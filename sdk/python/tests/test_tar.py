# Copyright The kweaver.ai Authors.
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

"""Tests for bkn.tar pack_to_tar."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import pytest


def test_pack_to_tar_k8s_network():
    from bkn import pack_to_tar

    with tempfile.TemporaryDirectory() as tmp:
        examples = Path(__file__).resolve().parent.parent.parent.parent / "examples"
        out_path = Path(tmp) / "k8s-network.tar"
        pack_to_tar(examples / "k8s-network", out_path)
        assert out_path.exists()
        assert out_path.stat().st_size > 0

        # List contents
        result = subprocess.run(
            ["tar", "-tf", str(out_path)],
            capture_output=True,
            text=True,
            check=True,
        )
        lines = result.stdout.strip().split("\n")
        assert any("network.bkn" in p for p in lines)
        assert any("object_types/" in p for p in lines)


def test_pack_to_tar_supplychain_hd():
    from bkn import pack_to_tar

    with tempfile.TemporaryDirectory() as tmp:
        examples = Path(__file__).resolve().parent.parent.parent.parent / "examples"
        out_path = Path(tmp) / "supplychain-hd.tar"
        pack_to_tar(examples / "supplychain-hd", out_path)
        assert out_path.exists()
        result = subprocess.run(
            ["tar", "-tf", str(out_path)],
            capture_output=True,
            text=True,
            check=True,
        )
        lines = result.stdout.strip().split("\n")
        assert any("network.bkn" in p for p in lines)


def test_pack_to_tar_no_apple_double_on_darwin():
    from bkn import pack_to_tar
    import sys

    if sys.platform != "darwin":
        pytest.skip("macOS only")

    with tempfile.TemporaryDirectory() as tmp:
        examples = Path(__file__).resolve().parent.parent.parent.parent / "examples"
        out_path = Path(tmp) / "out.tar"
        pack_to_tar(examples / "k8s-network", out_path)
        result = subprocess.run(
            ["tar", "-tf", str(out_path)],
            capture_output=True,
            text=True,
            check=True,
        )
        lines = result.stdout.strip().split("\n")
        apple_double = [p for p in lines if "/._" in p or p.startswith("._")]
        assert len(apple_double) == 0


def test_pack_to_tar_gzip():
    from bkn import pack_to_tar

    with tempfile.TemporaryDirectory() as tmp:
        examples = Path(__file__).resolve().parent.parent.parent.parent / "examples"
        out_path = Path(tmp) / "out.tar.gz"
        pack_to_tar(examples / "k8s-network", out_path, gzip=True)
        assert out_path.exists()
        data = out_path.read_bytes()
        assert data[0:2] == b"\x1f\x8b"


def test_pack_to_tar_source_not_found():
    from bkn import pack_to_tar

    with pytest.raises(ValueError, match="not found"):
        pack_to_tar("/nonexistent/dir", "/tmp/out.tar")


def test_pack_to_tar_source_not_directory():
    from bkn import pack_to_tar

    with tempfile.NamedTemporaryFile(suffix=".bkn", delete=False) as f:
        path = f.name
    try:
        with pytest.raises(ValueError, match="not a directory"):
            pack_to_tar(path, Path(path).parent / "out.tar")
    finally:
        Path(path).unlink(missing_ok=True)