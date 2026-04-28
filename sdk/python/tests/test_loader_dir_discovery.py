# Copyright The kweaver.ai Authors.
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

"""Tests for directory input, root file discovery, and implicit same-dir loading."""

from __future__ import annotations

import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
EXAMPLES_DIR = REPO_ROOT / "examples"


class TestDiscoverRootFile:
    """Root file discovery order: network.bkn > network.md > index.bkn > index.md."""

    def test_network_bkn_priority_over_index_bkn(self, tmp_path):
        """When both network.bkn and index.bkn exist, network.bkn is used."""
        from bkn import load_network, discover_root_file
        (tmp_path / "network.bkn").write_text("""---
type: network
id: net-priority
name: Network priority
---
# Root from network.bkn
""")
        (tmp_path / "index.bkn").write_text("""---
type: network
id: index-priority
name: Index (should not be used)
---
# Wrong root
""")
        (tmp_path / "objects.bkn").write_text("""---
type: fragment
id: obj1
---
## Object: obj1
""")
        net = load_network(tmp_path)
        assert net.root.frontmatter.id == "net-priority"
        root = discover_root_file(tmp_path)
        assert root.name == "network.bkn"

    def test_load_network_dir_k8s(self):
        """load_network(examples/k8s-network) discovers network.bkn."""
        from bkn import load_network
        path = EXAMPLES_DIR / "k8s-network"
        if not path.exists():
            pytest.skip("k8s-network example not found")
        net = load_network(path)
        assert net.root.frontmatter.id == "k8s-network"
        assert len(net.all_objects) >= 3



class TestImplicitSameDirLoading:
    """When root has no includes and type: network, same-dir files are loaded implicitly."""

    def test_no_includes_implicit_same_dir(self, tmp_path):
        """type: network with empty includes loads same-dir BKN files."""
        from bkn import load_network
        (tmp_path / "network.bkn").write_text("""---
type: network
id: implicit-demo
---
# Root
""")
        (tmp_path / "objects.bkn").write_text("""---
type: fragment
id: obj1
---
## Object: obj1
""")
        (tmp_path / "relations.bkn").write_text("""---
type: fragment
id: rel1
---
## Relation: rel1
""")
        net = load_network(tmp_path)
        assert len(net.all_objects) == 1
        assert len(net.all_relations) == 1
        assert net.root.frontmatter.id == "implicit-demo"

    def test_explicit_includes_no_implicit(self, tmp_path):
        """When includes is non-empty, no implicit same-dir scanning."""
        from bkn import load_network
        (tmp_path / "network.bkn").write_text("""---
type: network
id: explicit-demo
includes:
  - objects.bkn
---
# Root
""")
        (tmp_path / "objects.bkn").write_text("""---
type: fragment
id: obj1
---
## Object: obj1
""")
        (tmp_path / "relations.bkn").write_text("""---
type: fragment
id: rel1
---
## Relation: rel1
""")
        net = load_network(tmp_path)
        assert len(net.all_objects) == 1
        assert len(net.all_relations) == 0  # relations.bkn not in includes

    def test_fragment_root_no_implicit(self, tmp_path):
        """Fragment root does not trigger implicit directory absorption."""
        from bkn import load_network
        (tmp_path / "fragment.bkn").write_text("""---
type: fragment
id: frag1
---
## Object: obj1
""")
        (tmp_path / "other.bkn").write_text("""---
type: fragment
id: other
---
## Object: obj2
""")
        # No named root; discover_root_file would need exactly one type: network
        # Here we have no network, so load_network(fragment.bkn) as file
        net = load_network(tmp_path / "fragment.bkn")
        assert len(net.all_objects) == 1
        assert len(net.includes) == 0  # fragment has no includes, no implicit

    def test_dedup_no_false_circular(self, tmp_path):
        """Same file via multiple paths: deduplicate, don't report circular."""
        from bkn import load_network
        (tmp_path / "network.bkn").write_text("""---
type: network
id: dedup-demo
includes:
  - a.bkn
  - b.bkn
---
""")
        (tmp_path / "a.bkn").write_text("""---
type: fragment
id: a
includes:
  - shared.bkn
---
## Object: obj_a
""")
        (tmp_path / "b.bkn").write_text("""---
type: fragment
id: b
includes:
  - shared.bkn
---
## Object: obj_b
""")
        (tmp_path / "shared.bkn").write_text("""---
type: fragment
id: shared
---
## Object: obj_shared
""")
        net = load_network(tmp_path)
        # shared.bkn loaded once (dedup), no circular error
        objs = [o.id for o in net.all_objects]
        assert "obj_shared" in objs
        assert objs.count("obj_shared") == 1


class TestDiscoverRootErrors:
    """Error cases for root discovery."""

    def test_multiple_networks_no_named_root(self, tmp_path):
        """Multiple type: network files without named root raises."""
        from bkn import discover_root_file
        (tmp_path / "a.bkn").write_text("---\ntype: network\nid: a\n---\n")
        (tmp_path / "b.bkn").write_text("---\ntype: network\nid: b\n---\n")
        with pytest.raises(ValueError, match="Multiple network roots"):
            discover_root_file(tmp_path)

    def test_no_root_in_empty_dir(self, tmp_path):
        """Empty directory raises."""
        from bkn import discover_root_file
        with pytest.raises(ValueError, match="No root network file"):
            discover_root_file(tmp_path)