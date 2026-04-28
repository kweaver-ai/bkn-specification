# Copyright The kweaver.ai Authors.
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

"""Tests for bkn.checksum API."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest


def test_generate_and_verify_checksum():
    from bkn import generate_checksum_file, verify_checksum_file

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "objects").mkdir()
        (root / "objects" / "pod.bkn").write_text(
            "---\ntype: object\nid: pod\nname: Pod\nnetwork: k8s\n---\n\n## Object: pod\n**Pod**\n",
            encoding="utf-8",
        )
        content = generate_checksum_file(root)
        assert "sha256:" in content
        assert "objects/pod.bkn" in content
        assert "*" in content
        ok, errs = verify_checksum_file(root)
        assert ok, errs
        assert len(errs) == 0


def test_verify_fails_when_file_changed():
    from bkn import generate_checksum_file, verify_checksum_file

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "test.bkn").write_text(
            "---\ntype: object\nid: x\n---\n\n## Object: x\n",
            encoding="utf-8",
        )
        generate_checksum_file(root)
        (root / "test.bkn").write_text(
            "---\ntype: object\nid: x\n---\n\n## Object: x\nModified\n",
            encoding="utf-8",
        )
        ok, errs = verify_checksum_file(root)
        assert not ok
        assert any("Mismatch" in e for e in errs)


def test_checksum_normalization_blank_lines_and_whitespace():
    """Blank lines, CRLF, and trailing whitespace do not alter checksum."""
    from bkn import generate_checksum_file, verify_checksum_file

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        base_bkn = "---\ntype: object\nid: x\n---\n\n## Object: x\n**X**\n"
        (root / "test.bkn").write_text(base_bkn, encoding="utf-8")
        content = generate_checksum_file(root)
        base_hash = _extract_hash(content, "test.bkn")
        assert base_hash

        # Same semantic content with extra blank lines
        with_blank_lines = "---\ntype: object\nid: x\n---\n\n\n## Object: x\n\n**X**\n\n"
        (root / "test.bkn").write_text(with_blank_lines, encoding="utf-8")
        content2 = generate_checksum_file(root)
        hash2 = _extract_hash(content2, "test.bkn")
        assert base_hash == hash2, f"checksum changed with blank lines: {base_hash} vs {hash2}"

        # Same semantic content with CRLF and trailing spaces
        with_crlf = "---\r\ntype: object\r\nid: x\r\n---\r\n\r\n## Object: x\r\n**X**   \r\n"
        (root / "test.bkn").write_text(with_crlf, encoding="utf-8")
        content3 = generate_checksum_file(root)
        hash3 = _extract_hash(content3, "test.bkn")
        assert base_hash == hash3, f"checksum changed with CRLF/trailing space: {base_hash} vs {hash3}"

        # Restore and verify
        (root / "test.bkn").write_text(base_bkn, encoding="utf-8")
        generate_checksum_file(root)
        ok, errs = verify_checksum_file(root)
        assert ok, errs


def test_checksum_normalization_semantic_change_alters_checksum():
    """Semantic content changes do alter checksum."""
    from bkn import generate_checksum_file

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        base_bkn = "---\ntype: object\nid: x\n---\n\n## Object: x\n**X**\n"
        (root / "test.bkn").write_text(base_bkn, encoding="utf-8")
        content = generate_checksum_file(root)
        base_hash = _extract_hash(content, "test.bkn")

        modified_bkn = "---\ntype: object\nid: x\n---\n\n## Object: x\n**Y**\n"
        (root / "test.bkn").write_text(modified_bkn, encoding="utf-8")
        content2 = generate_checksum_file(root)
        hash2 = _extract_hash(content2, "test.bkn")
        assert base_hash != hash2, "checksum should change when semantic content changes"


def test_checksum_normalization_bknd_whitespace():
    """bknd whitespace-only changes do not alter checksum."""
    from bkn import generate_checksum_file

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        base_bknd = "---\ntype: data\nobject: x\n---\n\n## Data\n\n| a | b |\n|---|---|\n| 1 | 2 |\n"
        (root / "data.bknd").write_text(base_bknd, encoding="utf-8")
        content = generate_checksum_file(root)
        base_hash = _extract_hash(content, "data.bknd")

        with_whitespace = (
            "---\ntype: data\nobject: x\n---\n\n## Data\n\n\n|  a  |  b  |\n|-----|-----|\n|  1  |  2  |\n\n"
        )
        (root / "data.bknd").write_text(with_whitespace, encoding="utf-8")
        content2 = generate_checksum_file(root)
        hash2 = _extract_hash(content2, "data.bknd")
        assert base_hash == hash2, f"checksum changed with bknd whitespace: {base_hash} vs {hash2}"


def test_checksum_normalization_bknd_column_order():
    """Reordered bknd columns with matching values should produce the same checksum."""
    from bkn import generate_checksum_file

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        base_bknd = "---\ntype: data\nobject: x\n---\n\n## Data\n\n| a | b |\n|---|---|\n| 1 | 2 |\n"
        (root / "data.bknd").write_text(base_bknd, encoding="utf-8")
        content = generate_checksum_file(root)
        base_hash = _extract_hash(content, "data.bknd")

        reordered_bknd = (
            "---\ntype: data\nobject: x\n---\n\n## Data\n\n| b | a |\n|---|---|\n| 2 | 1 |\n"
        )
        (root / "data.bknd").write_text(reordered_bknd, encoding="utf-8")
        content2 = generate_checksum_file(root)
        hash2 = _extract_hash(content2, "data.bknd")

        assert base_hash == hash2, (
            f"checksum changed with bknd column reordering: {base_hash} vs {hash2}"
        )


def test_generate_checksum_fails_when_network_validation_fails():
    from bkn import generate_checksum_file

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "objects").mkdir()
        (root / "connections").mkdir()
        (root / "data").mkdir()
        (root / "index.bkn").write_text(
            "---\n"
            "type: network\n"
            "id: demo\n"
            "name: Demo\n"
            "includes:\n"
            "  - connections/erp.bkn\n"
            "  - objects/pod.bkn\n"
            "  - data/pod.bknd\n"
            "---\n\n"
            "# Demo\n",
            encoding="utf-8",
        )
        (root / "objects" / "pod.bkn").write_text(
            "---\n"
            "type: object\n"
            "id: pod\n"
            "network: demo\n"
            "---\n\n"
            "## Object: pod\n\n"
            "### Data Source\n\n"
            "| Type | ID | Name |\n"
            "|------|----|------|\n"
            "| connection | erp | ERP |\n\n"
            "### Data Properties\n\n"
            "| Property | Primary Key |\n"
            "|----------|-------------|\n"
            "| id | YES |\n",
            encoding="utf-8",
        )
        (root / "connections" / "erp.bkn").write_text(
            "---\n"
            "type: connection\n"
            "id: erp\n"
            "network: demo\n"
            "---\n\n"
            "## Connection: erp\n\n"
            "**ERP**\n",
            encoding="utf-8",
        )
        (root / "data" / "pod.bknd").write_text(
            "---\n"
            "type: data\n"
            "object: pod\n"
            "---\n\n"
            "## Data\n\n"
            "| id |\n"
            "|----|\n"
            "| pod-1 |\n",
            encoding="utf-8",
        )

        with pytest.raises(ValueError, match="checksum validation failed"):
            generate_checksum_file(root)
        assert not (root / "CHECKSUM").exists()


def _extract_hash(content: str, filename: str) -> str | None:
    for line in content.splitlines():
        if filename in line and "  " in line:
            hash_part = line.split("  ", 1)[0].strip()
            if hash_part.startswith("sha256:"):
                return hash_part
    return None