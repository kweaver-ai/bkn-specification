# Copyright The kweaver.ai Authors.
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

"""Load .bkn/.bknd/.md files from disk, resolving network includes."""

from __future__ import annotations

from pathlib import Path

from bkn.models import BknDocument, BknNetwork
from bkn.parser import parse

# Supported file extensions for BKN content. .md is allowed as a carrier;
# content must still satisfy BKN frontmatter/type/structure requirements.
BKN_SUPPORTED_EXTENSIONS = frozenset({".bkn", ".bknd", ".md"})

# Root file discovery order: network.bkn > network.md > index.bkn > index.md
ROOT_CANDIDATE_NAMES = ("network.bkn", "network.md", "index.bkn", "index.md")

KNOWN_SUBDIRS = (
    "object_types", "relation_types", "action_types",
    "risk_types", "concept_groups",
)


def _check_extension(path: Path) -> None:
    """Raise ValueError if path extension is not supported."""
    ext = path.suffix.lower()
    if ext not in BKN_SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file extension: {ext!r}. "
            f"BKN supports: {', '.join(sorted(BKN_SUPPORTED_EXTENSIONS))}"
        )


def discover_root_file(directory: Path) -> Path:
    """Discover the root network file in a directory.

    Order: network.bkn > network.md > index.bkn > index.md.
    If none exist, and exactly one file in the directory has type: network,
    use that file. Otherwise raise ValueError.

    Args:
        directory: Path to the directory to scan.

    Returns:
        Path to the root file.

    Raises:
        ValueError: If no root can be determined or multiple roots exist.
    """
    directory = Path(directory).resolve()
    if not directory.is_dir():
        raise ValueError(f"Not a directory: {directory}")

    # 1. Check named candidates in order
    for name in ROOT_CANDIDATE_NAMES:
        candidate = directory / name
        if candidate.is_file():
            ext = candidate.suffix.lower()
            if ext in BKN_SUPPORTED_EXTENSIONS:
                return candidate

    # 2. Scan same directory for type: network files
    network_files: list[Path] = []
    for p in directory.iterdir():
        if not p.is_file():
            continue
        ext = p.suffix.lower()
        if ext not in BKN_SUPPORTED_EXTENSIONS:
            continue
        try:
            doc = parse(p.read_text(encoding="utf-8"), source_path=str(p))
            if (doc.frontmatter.type or "").strip().lower() in ("network", "knowledge_network"):
                network_files.append(p)
        except Exception:
            continue

    if len(network_files) == 1:
        return network_files[0]
    if len(network_files) > 1:
        raise ValueError(
            f"Multiple network roots in {directory}: "
            f"{[p.name for p in network_files]}. "
            f"Use network.bkn or index.bkn as the single root."
        )
    raise ValueError(
        f"No root network file found in {directory}. "
        f"Expected one of: {', '.join(ROOT_CANDIDATE_NAMES)} "
        f"or a single type: network file."
    )


def _collect_same_dir_bkn_files(
    directory: Path,
    root_path: Path,
) -> list[Path]:
    """Collect BKN files in the same directory for implicit loading.

    Excludes the root file and other root candidates. Only includes files
    that can be parsed as valid BKN (.bkn, .bknd, .md).
    """
    directory = Path(directory).resolve()
    root_path = Path(root_path).resolve()
    root_name = root_path.name

    # Exclude root and other root candidates
    exclude_names = {root_name}
    for name in ROOT_CANDIDATE_NAMES:
        if (directory / name).exists():
            exclude_names.add(name)

    result: list[Path] = []
    for p in sorted(directory.iterdir()):
        if not p.is_file():
            continue
        if p.name in exclude_names:
            continue
        ext = p.suffix.lower()
        if ext not in BKN_SUPPORTED_EXTENSIONS:
            continue
        try:
            parse(p.read_text(encoding="utf-8"), source_path=str(p))
        except Exception:
            continue
        result.append(p)
    return result


def _collect_subdir_bkn_files(directory: Path) -> list[Path]:
    """Collect BKN files from known subdirectories (Go SDK compatible).

    Scans object_types/, relation_types/, action_types/, risk_types/,
    concept_groups/ for .bkn/.bknd/.md files.
    """
    result: list[Path] = []
    for subdir_name in KNOWN_SUBDIRS:
        subdir = directory / subdir_name
        if not subdir.is_dir():
            continue
        for p in sorted(subdir.iterdir()):
            if not p.is_file():
                continue
            ext = p.suffix.lower()
            if ext not in BKN_SUPPORTED_EXTENSIONS:
                continue
            result.append(p)
    return result


def load(path: str | Path) -> BknDocument:
    """Load and parse a single .bkn/.bknd/.md file.

    Supported extensions: .bkn, .bknd, .md. Content must satisfy BKN
    frontmatter, type, and structure requirements regardless of extension.

    Args:
        path: Path to the .bkn, .bknd, or .md file.

    Returns:
        Parsed BknDocument.

    Raises:
        ValueError: If extension is unsupported or content is not valid BKN.
    """
    path = Path(path).resolve()
    _check_extension(path)
    text = path.read_text(encoding="utf-8")
    return parse(text, source_path=str(path))


def load_network(root_path: str | Path) -> BknNetwork:
    """Load a network file and recursively resolve its includes.

    Supported extensions: .bkn, .bknd, .md. Root file should be type: network.
    When root_path is a directory, the root file is discovered automatically
    (network.bkn > network.md > index.bkn > index.md).
    If the root has no `includes`, same-directory BKN files are loaded implicitly.
    Otherwise only files listed in frontmatter `includes` are loaded.

    Args:
        root_path: Path to the root file or directory containing the network.

    Returns:
        BknNetwork containing the root document and all included documents.

    Raises:
        ValueError: If extension is unsupported, content is not valid BKN,
            or a circular include is detected.
    """
    root_path = Path(root_path).resolve()
    if root_path.is_dir():
        root_path = discover_root_file(root_path)

    root_doc = load(root_path)

    loaded_paths: set[str] = {str(root_path)}
    recursion_stack: set[str] = set()
    includes: list[BknDocument] = []

    if root_doc.frontmatter.includes:
        _resolve_includes(
            root_doc,
            root_path.parent,
            loaded_paths,
            recursion_stack,
            includes,
        )
    else:
        # No includes: for network types only, implicitly load same-dir
        # files and files from known subdirectories (Go SDK compatible).
        doc_type = (root_doc.frontmatter.type or "").strip().lower()
        if doc_type in ("network", "knowledge_network"):
            implicit_paths = _collect_same_dir_bkn_files(
                root_path.parent,
                root_path,
            )
            implicit_paths.extend(_collect_subdir_bkn_files(root_path.parent))
            for inc_path in implicit_paths:
                path_str = str(inc_path.resolve())
                if path_str in loaded_paths:
                    continue
                if path_str in recursion_stack:
                    raise ValueError(
                        f"Circular include detected: {inc_path.name} "
                        f"(resolved to {path_str})"
                    )
                loaded_paths.add(path_str)
                inc_doc = load(inc_path)
                includes.append(inc_doc)
                recursion_stack.add(path_str)
                _resolve_includes(
                    inc_doc,
                    inc_path.parent,
                    loaded_paths,
                    recursion_stack,
                    includes,
                )
                recursion_stack.discard(path_str)

    network = BknNetwork(root=root_doc, includes=includes)
    _validate_network_references(network)
    return network


def _resolve_includes(
    doc: BknDocument,
    base_dir: Path,
    loaded_paths: set[str],
    recursion_stack: set[str],
    result: list[BknDocument],
) -> None:
    """Recursively resolve includes from a document's frontmatter.

    Deduplication: paths in loaded_paths are skipped (already loaded).
    Circular: only when path is in recursion_stack (back to self in chain).
    """
    for include_rel in doc.frontmatter.includes:
        include_path = (base_dir / include_rel).resolve()
        path_str = str(include_path)

        if path_str in loaded_paths:
            continue  # Deduplication: already loaded via another path

        if path_str in recursion_stack:
            raise ValueError(
                f"Circular include detected: {include_rel} "
                f"(resolved to {path_str})"
            )

        if not include_path.exists():
            raise FileNotFoundError(
                f"Include file not found: {include_rel} "
                f"(resolved to {path_str})"
            )

        loaded_paths.add(path_str)
        inc_doc = load(include_path)
        result.append(inc_doc)

        recursion_stack.add(path_str)
        try:
            _resolve_includes(
                inc_doc,
                include_path.parent,
                loaded_paths,
                recursion_stack,
                result,
            )
        finally:
            recursion_stack.discard(path_str)


def _validate_network_references(network: BknNetwork) -> None:
    for obj in network.all_objects:
        if obj.data_source is None:
            continue
        if obj.data_source.type.strip().lower() != "connection":
            continue
        connection_id = obj.data_source.id.strip()
        if not connection_id or network.get_connection(connection_id) is None:
            raise ValueError(
                f"object {obj.id!r} references missing connection {connection_id!r}"
            )