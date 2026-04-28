# Copyright The kweaver.ai Authors.
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

"""Tests for .bknd serialization (to_bknd, to_bknd_from_table)."""

from __future__ import annotations

import pytest

from bkn import load, parse, to_bknd, to_bknd_from_table


class TestToBknd:
    """Test to_bknd() serialization."""

    def test_to_bknd_object(self):
        """Serialize object data to .bknd format."""
        md = to_bknd(
            object_id="scenario",
            rows=[
                {"scenario_id": "s1", "name": "场景1", "category": "integrity"},
                {"scenario_id": "s2", "name": "场景2", "category": "availability"},
            ],
            network="recoverable-network",
            source="PFMEA模板.xlsx",
        )
        assert "type: data" in md
        assert "object: scenario" in md
        assert "network: recoverable-network" in md
        assert "source: PFMEA模板.xlsx" in md
        assert "# scenario" in md
        assert "| scenario_id | name | category |" in md
        assert "| s1 | 场景1 | integrity |" in md

    def test_to_bknd_relation(self):
        """Serialize relation data to .bknd format."""
        md = to_bknd(
            relation_id="rs_under_scenario",
            rows=[
                {"rs_id": "r1", "scenario_id": "s1"},
            ],
            network="recoverable-network",
        )
        assert "relation: rs_under_scenario" in md
        assert "object:" not in md or "object: rs_under_scenario" not in md
        assert "# rs_under_scenario" in md
        assert "| rs_id | scenario_id |" in md

    def test_to_bknd_empty_rows(self):
        """Empty rows produce valid .bknd with header only."""
        md = to_bknd(
            object_id="scenario",
            rows=[],
            network="test",
            columns=["id", "name"],
        )
        assert "type: data" in md
        assert "object: scenario" in md
        assert "# scenario" in md

    def test_to_bknd_requires_object_or_relation(self):
        """Must specify either object_id or relation_id."""
        with pytest.raises(ValueError, match="Specify either"):
            to_bknd(rows=[], network="test")
        with pytest.raises(ValueError, match="not both"):
            to_bknd(
                object_id="e",
                relation_id="r",
                rows=[],
                network="test",
            )


class TestToBkndFromTable:
    """Test to_bknd_from_table() and DataTable.to_bknd()."""

    def test_round_trip_object(self):
        """Parse .bknd -> serialize -> parse yields same data."""
        text = """---
type: data
object: scenario
network: recoverable-network
source: PFMEA模板.xlsx
---

# scenario

| scenario_id | name | category |
|-------------|------|----------|
| s1 | 场景1 | integrity |
| s2 | 场景2 | availability |
"""
        doc = parse(text, source_path="/fake/scenario.bknd")
        table = doc.data_tables[0]
        serialized = to_bknd_from_table(table)
        doc2 = parse(serialized)
        t2 = doc2.data_tables[0]
        assert t2.object_or_relation == table.object_or_relation
        assert t2.columns == table.columns
        assert t2.rows == table.rows
        assert t2.network == table.network

    def test_round_trip_via_instance_method(self):
        """DataTable.to_bknd() produces parseable output."""
        text = """---
type: data
relation: rs_under_scenario
network: recoverable-network
---

# rs_under_scenario

| rs_id | scenario_id |
|-------|-------------|
| r1 | s1 |
"""
        doc = parse(text)
        table = doc.data_tables[0]
        serialized = table.to_bknd()
        doc2 = parse(serialized)
        t2 = doc2.data_tables[0]
        assert t2.object_or_relation == "rs_under_scenario"
        assert t2.is_relation is True
        assert t2.rows == [{"rs_id": "r1", "scenario_id": "s1"}]