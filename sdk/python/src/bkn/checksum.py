# Copyright The kweaver.ai Authors.
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

"""Checksum computation and CHECKSUM generation for BKN directories."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from datetime import datetime, timezone

from bkn.loader import discover_root_file, load, load_network
from bkn.parser import _split_frontmatter
from bkn.validator import validate_network_data


CHECKSUM_FILENAME = "CHECKSUM"
CHECKSUM_EXTENSIONS = {".bkn", ".bknd"}
CHECKSUM_FILES = {"SKILL.md"}


def _normalize_for_checksum(text: str) -> str:
    """
    Normalize text before hashing so that blank lines, CRLF/LF differences,
    trailing whitespace, and table-cell padding do not affect the checksum.
    Semantic content changes still change the checksum.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    out = [line.rstrip() for line in lines if line.rstrip()]
    return "\n".join(out)


def _body_checksum(body: str) -> str:
    """Compute sha256 of normalized body. Format: sha256:{64 hex}."""
    normalized = _normalize_for_checksum(body)
    h = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"sha256:{h}"


def compute_file_checksum(path: Path, root: Path) -> str | None:
    """
    Compute canonical checksum for a single file.

    For .bkn: uses Markdown body only (after frontmatter).
    For .bknd: parses table, sorts rows by all columns, re-serializes, hashes (order-insensitive).
    For SKILL.md: normalizes full content (LF, trim).

    Returns None if file type is not supported.
    """
    rel = path.relative_to(root).as_posix()
    suffix = path.suffix.lower()
    name = path.name

    if name == "SKILL.md":
        text = path.read_text(encoding="utf-8")
        normalized = _normalize_for_checksum(text)
        h = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        return f"sha256:{h}  {rel}"

    if suffix == ".bkn":
        text = path.read_text(encoding="utf-8")
        _, body = _split_frontmatter(text)
        h = _body_checksum(body)
        return f"{h}  {rel}"

    if suffix == ".bknd":
        text = path.read_text(encoding="utf-8")
        _, body = _split_frontmatter(text)
        # Parse table and sort rows for order-insensitive checksum
        lines = body.strip().split("\n")
        table_lines = []
        for line in lines:
            s = line.strip()
            if s.startswith("|"):
                table_lines.append(s)
            elif table_lines:
                break
        if len(table_lines) >= 2:
            # Parse header and rows
            def split_row(row: str) -> list[str]:
                r = row.strip()
                if r.startswith("|"):
                    r = r[1:]
                if r.endswith("|"):
                    r = r[:-1]
                return [c.strip() for c in r.split("|")]
            headers = split_row(table_lines[0])
            sorted_headers = sorted(headers)
            sep = table_lines[1]
            data_start = 2 if re.match(r"^\|?[\s:*-]+(\|[\s:*-]+)*\|?$", sep.strip()) else 1
            rows = []
            for line in table_lines[data_start:]:
                cells = split_row(line)
                row_dict = {h: cells[i] if i < len(cells) else "" for i, h in enumerate(headers)}
                rows.append(tuple(row_dict.get(h, "") for h in sorted_headers))
            rows.sort()
            # Serialize back using sorted header order so cells stay aligned.
            out_lines = [
                "| " + " | ".join(sorted_headers) + " |",
                "|" + "|".join(["---"] * len(sorted_headers)) + "|",
            ]
            for r in rows:
                out_lines.append("| " + " | ".join(str(v) for v in r) + " |")
            canonical = "\n".join(out_lines)
        else:
            canonical = body.strip()
        h = hashlib.sha256(_normalize_for_checksum(canonical).encode("utf-8")).hexdigest()
        return f"sha256:{h}  {rel}"

    return None


def collect_checksum_files(root: Path) -> list[Path]:
    """Collect .bkn, .bknd, and SKILL.md files under root, sorted by path."""
    paths: list[Path] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(root)
        if rel.name == CHECKSUM_FILENAME:
            continue
        if rel.name == "SKILL.md":
            paths.append(p)
        elif p.suffix.lower() in CHECKSUM_EXTENSIONS:
            paths.append(p)
    paths.sort(key=lambda x: x.relative_to(root).as_posix())
    return paths


def generate_checksum_file(root: str | Path) -> str:
    """
    Validate BKN inputs, then generate CHECKSUM in the given business directory.

    Covers .bkn, .bknd, and SKILL.md. Writes CHECKSUM at root.
    Returns the content written.
    """
    root = Path(root).resolve()
    if not root.is_dir():
        raise ValueError(f"Not a directory: {root}")
    _validate_checksum_inputs(root)

    entries: list[str] = []
    for p in collect_checksum_files(root):
        line = compute_file_checksum(p, root)
        if line:
            entries.append(line)

    # Aggregate checksum: hash of all entries concatenated
    concat = "\n".join(entries) + "\n" if entries else ""
    agg_hash = hashlib.sha256(concat.encode("utf-8")).hexdigest()
    agg_line = f"sha256:{agg_hash}  *"

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        "# BKN Directory Checksum",
        f"# generated: {now}",
        agg_line,
        "",
    ] + entries

    content = "\n".join(lines)
    out_path = root / CHECKSUM_FILENAME
    out_path.write_text(content, encoding="utf-8")
    return content


def _validate_checksum_inputs(root: Path) -> None:
    """Validate BKN inputs using root discovery to avoid double validation."""
    network_paths: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".bkn", ".bknd", ".md"}:
            continue
        try:
            doc = load(path)
        except Exception as exc:
            rel = path.relative_to(root).as_posix()
            raise ValueError(f"checksum validation failed for {rel}: {exc}") from exc
        if doc.frontmatter.type.strip().lower() in ("network", "knowledge_network"):
            network_paths.append(path)

    # Use root discovery per directory to avoid validating both network.bkn and
    # index.bkn when both exist (network.bkn takes priority).
    dirs_with_networks = {p.parent for p in network_paths}
    roots_to_validate: list[Path] = []
    for d in dirs_with_networks:
        try:
            root_path = discover_root_file(d)
            roots_to_validate.append(root_path)
        except ValueError as exc:
            raise ValueError(
                f"checksum validation failed: {exc}"
            ) from exc

    for root_path in roots_to_validate:
        rel = root_path.relative_to(root).as_posix()
        try:
            network = load_network(root_path)
        except Exception as exc:
            raise ValueError(
                f"checksum validation failed for network {rel}: {exc}"
            ) from exc
        result = validate_network_data(network)
        if not result.ok:
            raise ValueError(
                f"checksum validation failed for network {rel}: {result.errors[0]}"
            )


def verify_checksum_file(root: str | Path) -> tuple[bool, list[str]]:
    """
    Verify CHECKSUM against actual files.

    Returns (ok, list of error messages).
    """
    root = Path(root).resolve()
    ck_path = root / CHECKSUM_FILENAME
    if not ck_path.exists():
        return False, [f"{CHECKSUM_FILENAME} not found"]

    errors: list[str] = []
    content = ck_path.read_text(encoding="utf-8")
    declared: dict[str, str] = {}
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "  " in line:
            hash_part, path_part = line.split("  ", 1)
            path_part = path_part.strip()
            declared[path_part] = hash_part

    for p in collect_checksum_files(root):
        rel = p.relative_to(root).as_posix()
        line = compute_file_checksum(p, root)
        if not line:
            continue
        actual_hash = line.split("  ", 1)[0]
        if rel in declared:
            if declared[rel] != actual_hash:
                errors.append(f"Mismatch: {rel}")
            del declared[rel]
        else:
            errors.append(f"Unexpected file: {rel}")

    for rel in declared:
        if rel != "*":
            errors.append(f"Missing file: {rel}")

    # Verify aggregate: recompute from actual file hashes
    actual_entries = []
    for p in collect_checksum_files(root):
        rel = p.relative_to(root).as_posix()
        line = compute_file_checksum(p, root)
        if line:
            actual_entries.append(line)
    actual_entries.sort(key=lambda x: x.split("  ", 1)[1])
    concat = "\n".join(actual_entries) + "\n" if actual_entries else ""
    agg_hash = hashlib.sha256(concat.encode("utf-8")).hexdigest()
    expected_agg = f"sha256:{agg_hash}"
    if "*" in declared and declared["*"] != expected_agg:
        errors.append("Aggregate checksum mismatch")

    return len(errors) == 0, errors