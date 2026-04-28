# Copyright The kweaver.ai Authors.
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

"""Tests for BKN data validator."""

from __future__ import annotations

from pathlib import Path

import pytest

from bkn.models import BknObject, BknNetwork, DataProperty, DataSource, DataTable
from bkn.validator import validate_data_table, validate_network_data


def _object(props: list[DataProperty]) -> BknObject:
    return BknObject(id="test_object", data_properties=props)


def _table(columns: list[str], rows: list[dict[str, str]]) -> DataTable:
    return DataTable(
        object_or_relation="test_object",
        columns=columns,
        rows=rows,
    )


# ---------------------------------------------------------------------------
# Column matching
# ---------------------------------------------------------------------------


class TestColumnMatch:
    def test_exact_match_ok(self):
        schema = _object([
            DataProperty(property="id", primary_key=True),
            DataProperty(property="name", display_key=True),
        ])
        table = _table(["id", "name"], [{"id": "1", "name": "a"}])
        result = validate_data_table(table, schema=schema)
        assert result.ok

    def test_extra_column_reported(self):
        schema = _object([DataProperty(property="id", primary_key=True)])
        table = _table(["id", "bogus"], [{"id": "1", "bogus": "x"}])
        result = validate_data_table(table, schema=schema)
        codes = [e.code for e in result.errors]
        assert "extra_column" in codes

    def test_missing_column_reported(self):
        schema = _object([
            DataProperty(property="id", primary_key=True),
            DataProperty(property="name"),
        ])
        table = _table(["id"], [{"id": "1"}])
        result = validate_data_table(table, schema=schema)
        codes = [e.code for e in result.errors]
        assert "missing_column" in codes


# ---------------------------------------------------------------------------
# not_null constraint
# ---------------------------------------------------------------------------


class TestNotNull:
    def test_not_null_ok(self):
        schema = _object([
            DataProperty(property="id", constraint="not_null", primary_key=True),
        ])
        table = _table(["id"], [{"id": "abc"}])
        assert validate_data_table(table, schema=schema).ok

    def test_not_null_empty_fails(self):
        schema = _object([
            DataProperty(property="id", constraint="not_null", primary_key=True),
        ])
        table = _table(["id"], [{"id": ""}])
        result = validate_data_table(table, schema=schema)
        codes = [e.code for e in result.errors]
        assert "not_null" in codes

    def test_not_null_whitespace_fails(self):
        schema = _object([
            DataProperty(property="id", constraint="not_null", primary_key=True),
        ])
        table = _table(["id"], [{"id": "  "}])
        result = validate_data_table(table, schema=schema)
        codes = [e.code for e in result.errors]
        assert "not_null" in codes


# ---------------------------------------------------------------------------
# regex constraint
# ---------------------------------------------------------------------------


class TestRegex:
    def test_regex_match_ok(self):
        schema = _object([
            DataProperty(property="id", constraint="regex:^[a-z0-9_]+$", primary_key=True),
        ])
        table = _table(["id"], [{"id": "sec_t_01"}])
        assert validate_data_table(table, schema=schema).ok

    def test_regex_no_match_fails(self):
        schema = _object([
            DataProperty(property="id", constraint="regex:^[a-z0-9_]+$", primary_key=True),
        ])
        table = _table(["id"], [{"id": "SEC-T-01"}])
        result = validate_data_table(table, schema=schema)
        codes = [e.code for e in result.errors]
        assert "regex" in codes

    def test_regex_empty_value_skipped(self):
        schema = _object([
            DataProperty(property="id", constraint="regex:^[a-z]+$", primary_key=True),
        ])
        table = _table(["id"], [{"id": ""}])
        result = validate_data_table(table, schema=schema)
        regex_errors = [e for e in result.errors if e.code == "regex"]
        assert len(regex_errors) == 0


# ---------------------------------------------------------------------------
# in / not_in constraints
# ---------------------------------------------------------------------------


class TestEnum:
    def test_in_ok(self):
        schema = _object([
            DataProperty(property="category", constraint="in(a,b,c)"),
        ])
        table = _table(["category"], [{"category": "b"}])
        assert validate_data_table(table, schema=schema).ok

    def test_in_fails(self):
        schema = _object([
            DataProperty(property="category", constraint="in(a,b,c)"),
        ])
        table = _table(["category"], [{"category": "d"}])
        result = validate_data_table(table, schema=schema)
        codes = [e.code for e in result.errors]
        assert "in" in codes

    def test_not_in_ok(self):
        schema = _object([
            DataProperty(property="status", constraint="not_in(deleted)"),
        ])
        table = _table(["status"], [{"status": "active"}])
        assert validate_data_table(table, schema=schema).ok

    def test_not_in_fails(self):
        schema = _object([
            DataProperty(property="status", constraint="not_in(deleted)"),
        ])
        table = _table(["status"], [{"status": "deleted"}])
        result = validate_data_table(table, schema=schema)
        codes = [e.code for e in result.errors]
        assert "not_in" in codes


# ---------------------------------------------------------------------------
# Comparison constraints
# ---------------------------------------------------------------------------


class TestComparisons:
    def test_gte_ok(self):
        schema = _object([DataProperty(property="qty", type="int32", constraint=">= 0")])
        table = _table(["qty"], [{"qty": "5"}])
        assert validate_data_table(table, schema=schema).ok

    def test_gte_fails(self):
        schema = _object([DataProperty(property="qty", type="int32", constraint=">= 0")])
        table = _table(["qty"], [{"qty": "-1"}])
        result = validate_data_table(table, schema=schema)
        codes = [e.code for e in result.errors]
        assert ">=" in codes

    def test_lte_ok(self):
        schema = _object([DataProperty(property="score", type="float64", constraint="<= 100")])
        table = _table(["score"], [{"score": "99.5"}])
        assert validate_data_table(table, schema=schema).ok

    def test_lte_fails(self):
        schema = _object([DataProperty(property="score", type="float64", constraint="<= 100")])
        table = _table(["score"], [{"score": "101"}])
        result = validate_data_table(table, schema=schema)
        codes = [e.code for e in result.errors]
        assert "<=" in codes

    def test_range_ok(self):
        schema = _object([DataProperty(property="v", type="int32", constraint="range(1,5)")])
        table = _table(["v"], [{"v": "3"}])
        assert validate_data_table(table, schema=schema).ok

    def test_range_fails(self):
        schema = _object([DataProperty(property="v", type="int32", constraint="range(1,5)")])
        table = _table(["v"], [{"v": "6"}])
        result = validate_data_table(table, schema=schema)
        codes = [e.code for e in result.errors]
        assert "range" in codes


# ---------------------------------------------------------------------------
# Type checks
# ---------------------------------------------------------------------------


class TestTypeChecks:
    def test_bool_ok(self):
        schema = _object([DataProperty(property="flag", type="bool")])
        table = _table(["flag"], [{"flag": "true"}, {"flag": "false"}])
        assert validate_data_table(table, schema=schema).ok

    def test_bool_fails(self):
        schema = _object([DataProperty(property="flag", type="bool")])
        table = _table(["flag"], [{"flag": "yes"}])
        result = validate_data_table(table, schema=schema)
        codes = [e.code for e in result.errors]
        assert "type_bool" in codes

    def test_numeric_ok(self):
        schema = _object([DataProperty(property="count", type="int32")])
        table = _table(["count"], [{"count": "42"}])
        assert validate_data_table(table, schema=schema).ok

    def test_numeric_fails(self):
        schema = _object([DataProperty(property="count", type="int32")])
        table = _table(["count"], [{"count": "abc"}])
        result = validate_data_table(table, schema=schema)
        codes = [e.code for e in result.errors]
        assert "type_numeric" in codes


# ---------------------------------------------------------------------------
# Primary key uniqueness
# ---------------------------------------------------------------------------


class TestPrimaryKey:
    def test_unique_pk_ok(self):
        schema = _object([
            DataProperty(property="id", primary_key=True),
            DataProperty(property="name"),
        ])
        table = _table(
            ["id", "name"],
            [{"id": "a", "name": "A"}, {"id": "b", "name": "B"}],
        )
        assert validate_data_table(table, schema=schema).ok

    def test_duplicate_pk_fails(self):
        schema = _object([
            DataProperty(property="id", primary_key=True),
            DataProperty(property="name"),
        ])
        table = _table(
            ["id", "name"],
            [{"id": "a", "name": "A"}, {"id": "a", "name": "B"}],
        )
        result = validate_data_table(table, schema=schema)
        codes = [e.code for e in result.errors]
        assert "pk_duplicate" in codes


class TestReadOnlyDataSource:
    def test_data_view_object_rejects_bknd(self):
        schema = BknObject(
            id="test_object",
            data_source=DataSource(type="data_view", id="erp_view", name="ERP View"),
            data_properties=[DataProperty(property="id", primary_key=True)],
        )
        table = _table(["id"], [{"id": "1"}])
        result = validate_data_table(table, schema=schema)
        codes = [e.code for e in result.errors]
        assert "readonly_data_source" in codes

    def test_connection_object_rejects_bknd_via_network_lookup(self):
        schema = BknObject(
            id="test_object",
            data_source=DataSource(type="connection", id="erp_db", name="ERP DB"),
            data_properties=[DataProperty(property="id", primary_key=True)],
        )
        table = _table(["id"], [{"id": "1"}])
        network = BknNetwork()
        network.root.objects.append(schema)
        result = validate_data_table(table, network=network)
        codes = [e.code for e in result.errors]
        assert "readonly_data_source" in codes


# ---------------------------------------------------------------------------
# Combined constraints
# ---------------------------------------------------------------------------


class TestCombined:
    def test_combined_not_null_and_regex(self):
        schema = _object([
            DataProperty(
                property="code",
                constraint="not_null; regex:^[a-z0-9_]+$",
                primary_key=True,
            ),
        ])
        table = _table(["code"], [{"code": ""}])
        result = validate_data_table(table, schema=schema)
        codes = [e.code for e in result.errors]
        assert "not_null" in codes

    def test_combined_not_null_and_in(self):
        schema = _object([
            DataProperty(
                property="status",
                constraint="not_null; in(active,inactive)",
            ),
        ])
        table = _table(["status"], [{"status": "deleted"}])
        result = validate_data_table(table, schema=schema)
        codes = [e.code for e in result.errors]
        assert "in" in codes


# ---------------------------------------------------------------------------
# No schema found
# ---------------------------------------------------------------------------


class TestNoSchema:
    def test_no_schema_reports_error(self):
        table = _table(["id"], [{"id": "1"}])
        result = validate_data_table(table, schema=None, network=None)
        codes = [e.code for e in result.errors]
        assert "no_schema" in codes