# Copyright The kweaver.ai Authors.
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

"""Verify all examples/*.bkn files load successfully with the SDK."""

from __future__ import annotations

import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
EXAMPLES_DIR = REPO_ROOT / "examples"


def _get_all_bkn():
    """Collect all .bkn files under examples/."""
    return sorted(EXAMPLES_DIR.rglob("*.bkn"))


def _get_all_bknd():
    """Collect all .bknd files under examples/."""
    return sorted(EXAMPLES_DIR.rglob("*.bknd"))


class TestLoadSingleFiles:
    """Every .bkn file must parse with load()."""

    @pytest.mark.parametrize(
        "path",
        _get_all_bkn(),
        ids=lambda p: str(p.relative_to(EXAMPLES_DIR)),
    )
    def test_load_single_file(self, path: Path):
        from bkn import load
        doc = load(path)
        assert doc is not None
        assert doc.frontmatter is not None

    @pytest.mark.skipif(
        not _get_all_bknd(),
        reason="No .bknd files in examples (temporarily skipped)",
    )
    @pytest.mark.parametrize(
        "path",
        _get_all_bknd(),
        ids=lambda p: str(p.relative_to(EXAMPLES_DIR)),
    )
    def test_load_single_data_file(self, path: Path):
        from bkn import load
        doc = load(path)
        assert doc is not None
        assert doc.frontmatter.type == "data"
        assert len(doc.data_tables) >= 1


class TestLoadNetworks:
    """Network entry points must load with load_network()."""

    def test_supplychain_network(self):
        from bkn import load_network
        path = EXAMPLES_DIR / "supplychain-hd"
        if not path.exists():
            pytest.skip("supplychain-hd example not found")
        net = load_network(path)
        assert len(net.all_objects) == 12
        assert len(net.all_relations) == 14

    def test_k8s_network(self):
        from bkn import load_network
        path = EXAMPLES_DIR / "k8s-network"
        if not path.exists():
            pytest.skip("k8s-network example not found")
        net = load_network(path)
        assert len(net.all_objects) == 3
        assert len(net.all_relations) == 2
        assert len(net.all_actions) == 2