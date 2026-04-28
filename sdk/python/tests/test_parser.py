# Copyright The kweaver.ai Authors.
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

"""Tests for BKN parser using real example files."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
EXAMPLES_DIR = REPO_ROOT / "examples"

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bkn.parser import parse, parse_frontmatter, parse_body, parse_data_tables
from bkn.loader import load, load_network
from bkn.models import BknDocument, BknNetwork


# ---------------------------------------------------------------------------
# supplychain-hd network (split by type)
# ---------------------------------------------------------------------------

class TestSupplychainNetwork:
    """Test parsing the supplychain-hd multi-file network."""

    @pytest.fixture
    def network(self) -> BknNetwork:
        root_path = EXAMPLES_DIR / "supplychain-hd"
        if not root_path.exists():
            pytest.skip(f"Example not found: {root_path}")
        return load_network(root_path)

    def test_root_frontmatter(self, network: BknNetwork):
        fm = network.root.frontmatter
        assert fm.type == "knowledge_network"
        assert fm.id == "supplychain-hd"
        assert fm.name == "HD供应链业务知识网络"
        assert "供应链" in fm.tags

    def test_object_count(self, network: BknNetwork):
        assert len(network.all_objects) == 12

    def test_relation_count(self, network: BknNetwork):
        assert len(network.all_relations) == 14

    def test_object_po_parsed(self, network: BknNetwork):
        po = next((e for e in network.all_objects if e.id == "po"), None)
        assert po is not None
        assert po.name == "采购订单"
        assert len(po.data_properties) > 0

        pk_props = [dp for dp in po.data_properties if dp.primary_key]
        assert len(pk_props) >= 1

        dk_props = [dp for dp in po.data_properties if dp.display_key]
        assert len(dk_props) >= 1

    def test_object_po_data_source(self, network: BknNetwork):
        po = next(e for e in network.all_objects if e.id == "po")
        assert po.data_source is not None
        assert po.data_source.type == "data_view"
        assert po.data_source.name == "erp_purchase_order"

    def test_object_tags(self, network: BknNetwork):
        po = next(e for e in network.all_objects if e.id == "po")
        assert "已审核" in po.tags

    def test_object_product_logic_properties(self, network: BknNetwork):
        product = next(
            (e for e in network.all_objects if e.id == "product"), None
        )
        if product is None:
            pytest.skip("product object not found")
        assert len(product.logic_properties) > 0

    def test_relation_product2bom(self, network: BknNetwork):
        rel = next(
            (r for r in network.all_relations if r.id == "product2bom"), None
        )
        assert rel is not None
        assert rel.name == "产品关联产品BOM"
        assert len(rel.endpoints) == 1
        ep = rel.endpoints[0]
        assert ep.source == "product"
        assert ep.target == "bom"
        assert ep.type == "direct"

    def test_relation_mapping_rules(self, network: BknNetwork):
        rel = next(r for r in network.all_relations if r.id == "product2bom")
        assert len(rel.mapping_rules) >= 1
        assert rel.mapping_rules[0].source_property == "material_number"


# ---------------------------------------------------------------------------
# k8s-network multi-file network
# ---------------------------------------------------------------------------

class TestK8sNetwork:
    """Test parsing the k8s-network multi-file example."""

    @pytest.fixture
    def network(self) -> BknNetwork:
        path = EXAMPLES_DIR / "k8s-network"
        if not path.exists():
            pytest.skip(f"Example not found: {path}")
        return load_network(path)

    def test_frontmatter(self, network: BknNetwork):
        fm = network.root.frontmatter
        assert fm.type == "knowledge_network"
        assert fm.id == "k8s-network"

    def test_has_objects(self, network: BknNetwork):
        assert len(network.all_objects) == 3
        object_ids = {e.id for e in network.all_objects}
        assert "pod" in object_ids
        assert "node" in object_ids
        assert "service" in object_ids

    def test_has_relations(self, network: BknNetwork):
        assert len(network.all_relations) == 2

    def test_has_actions(self, network: BknNetwork):
        assert len(network.all_actions) == 2

    def test_pod_object(self, network: BknNetwork):
        pod = next(e for e in network.all_objects if e.id == "pod")
        assert "Pod" in pod.name
        assert len(pod.data_properties) > 0

    def test_action_parsed(self, network: BknNetwork):
        action = next(a for a in network.all_actions if a.id == "restart_pod")
        assert action.bound_object == "pod"


# ---------------------------------------------------------------------------
# Parser unit tests
# ---------------------------------------------------------------------------

class TestParserUnits:
    """Unit tests for low-level parser functions."""

    def test_simple_frontmatter(self):
        text = "---\ntype: object\nid: test\nname: Test\n---\n\n## Object: test\n"
        fm = parse_frontmatter(text)
        assert fm.type == "object"
        assert fm.id == "test"
        assert fm.name == "Test"

    def test_no_frontmatter(self):
        text = "# Just markdown\n\nSome content.\n"
        fm = parse_frontmatter(text)
        assert fm.type == ""

    def test_frontmatter_with_tags(self):
        text = "---\ntype: network\nid: n1\ntags: [a, b, c]\n---\n"
        fm = parse_frontmatter(text)
        assert fm.tags == ["a", "b", "c"]

    def test_frontmatter_with_includes(self):
        text = "---\ntype: network\nid: n1\nincludes:\n  - objects.bkn\n  - relations.bkn\n---\n"
        fm = parse_frontmatter(text)
        assert fm.includes == ["objects.bkn", "relations.bkn"]

    def test_parse_object_block(self):
        text = """---
type: fragment
id: test
---

## Object: my_object

**My Object** - A test object

- **Tags**: tag1, tag2

### Data Source

| Type | ID | Name |
|------|-----|------|
| data_view | 123 | my_view |

### Data Properties

| Property | Display Name | Type | Constraint | Description | Primary Key | Display Key | Index |
|----------|--------------|------|------------|-------------|:-----------:|:-----------:|:-----:|
| id | ID | int64 | | Primary key | YES | | YES |
| name | Name | VARCHAR | not_null | Object name | | YES | YES |
"""
        objects, relations, actions, risks, connections = parse_body(text)
        assert len(objects) == 1
        assert len(risks) == 0
        e = objects[0]
        assert e.id == "my_object"
        assert e.name == "My Object"
        assert e.description == "A test object"
        assert e.tags == ["tag1", "tag2"]
        assert e.data_source is not None
        assert e.data_source.id == "123"
        assert len(e.data_properties) == 2
        assert e.data_properties[0].primary_key is True
        assert e.data_properties[1].display_key is True

    def test_parse_relation_block(self):
        text = """---
type: fragment
id: test
---

## Relation: a_to_b

**A relates to B** - Test relation

- **Tags**: tested

### Endpoints

| Source | Target | Type | Required | Min | Max |
|--------|--------|------|----------|-----|-----|
| object_a | object_b | direct | NO | 0 | - |

### Mapping Rules

| Source Property | Target Property |
|-----------------|-----------------|
| a_id | b_ref_id |
"""
        _, relations, _, _, _ = parse_body(text)
        assert len(relations) == 1
        r = relations[0]
        assert r.id == "a_to_b"
        assert r.name == "A relates to B"
        assert r.tags == ["tested"]
        assert len(r.endpoints) == 1
        assert r.endpoints[0].source == "object_a"
        assert len(r.mapping_rules) == 1
        assert r.mapping_rules[0].source_property == "a_id"

    def test_parse_data_file(self):
        text = """---
type: data
network: recoverable-network
object: scenario
source: PFMEA模板.xlsx
---

# scenario

| scenario_id | name | category |
|-------------|------|----------|
| s1 | 场景1 | integrity |
| s2 | 场景2 | availability |
"""
        fm = parse_frontmatter(text)
        assert fm.type == "data"
        assert fm.object == "scenario"
        assert fm.source == "PFMEA模板.xlsx"

        tables = parse_data_tables(text, frontmatter=fm)
        assert len(tables) == 1
        table = tables[0]
        assert table.object_or_relation == "scenario"
        assert table.is_relation is False
        assert table.columns == ["scenario_id", "name", "category"]
        assert len(table.rows) == 2
        assert table.rows[0]["scenario_id"] == "s1"

        doc = parse(text, source_path="/fake/scenario.bknd")
        assert len(doc.objects) == 0
        assert len(doc.relations) == 0
        assert len(doc.actions) == 0
        assert len(doc.data_tables) == 1
        table = doc.data_tables[0]
        assert table.source_path == "/fake/scenario.bknd"
        assert table.network == "recoverable-network"

    def test_parse_data_file_object_relation_both_raises(self):
        """type: data with both object and relation raises ValueError."""
        text = """---
type: data
object: scenario
relation: rs_under_scenario
network: n
---

# scenario
| col |
|-----|
| v   |
"""
        with pytest.raises(ValueError, match="exactly one of object or relation"):
            parse_data_tables(text)

    def test_parse_data_file_object_relation_neither_raises(self):
        """type: data with neither object nor relation raises ValueError."""
        text = """---
type: data
network: n
---

# scenario
| col |
|-----|
| v   |
"""
        with pytest.raises(ValueError, match="got neither"):
            parse_data_tables(text)

    def test_parse_data_file_no_heading_raises(self):
        """type: data with no heading raises ValueError."""
        text = """---
type: data
object: scenario
network: n
---

| col |
|-----|
| v   |
"""
        with pytest.raises(ValueError, match="must have a heading"):
            parse_data_tables(text)

    def test_parse_data_file_no_table_raises(self):
        """type: data with heading but no valid table raises ValueError."""
        text = """---
type: data
object: scenario
network: n
---

# scenario

Some text, no table.
"""
        with pytest.raises(ValueError, match="valid GFM table"):
            parse_data_tables(text)

    def test_parse_risk_block(self):
        text = """---
type: risk
id: pod_restart_risk
name: Pod Restart Risk
network: demo
---

## Risk: pod_restart_risk

**Pod Restart Risk** - Controls pod restart actions.

### Control Scope

| Controlled Object | Controlled Action | Risk Level |
|-------------------|-------------------|------------|
| pod | restart_pod | high |

### Control Strategy

| Condition | Strategy |
|-----------|----------|
| production | require approval |

### Pre-checks

| Check Item | Type | Description |
|------------|------|-------------|
| can_i_restart | permission | Verify restart permission |

### Rollback Plan

Scale workload back to original replicas.

### Audit Requirements

Record operator and scenario.
"""
        doc = parse(text)
        assert doc.frontmatter.type == "risk"
        assert len(doc.risks) == 1
        risk = doc.risks[0]
        assert risk.id == "pod_restart_risk"
        assert risk.control_scope[0].controlled_object == "pod"
        assert risk.control_scope[0].controlled_action == "restart_pod"
        assert risk.control_scope[0].risk_level == "high"
        assert risk.control_strategies[0].strategy == "require approval"
        assert risk.pre_checks[0].check_item == "can_i_restart"
        assert "original replicas" in risk.rollback_plan
        assert "operator" in risk.audit_requirements


if __name__ == "__main__":
    pytest.main([__file__, "-v"])