# Copyright The kweaver.ai Authors.
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

"""Validate .bknd DataTable rows against Object/Relation schema definitions.

Checks performed:
  1. Column match   — .bknd columns vs Data Properties names
  2. not_null       — required fields must have non-empty values
  3. regex          — string values must match declared pattern
  4. in / not_in    — enum membership
  5. Comparisons    — ==, !=, >, <, >=, <=
  6. range          — closed interval [min, max]
  7. Type checks    — bool literal ("true"/"false"), numeric parsability
  8. Primary key    — uniqueness across rows
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from bkn.models import BknNetwork, BknObject, DataProperty, DataTable


@dataclass
class ValidationError:
    """A single validation problem."""

    table: str
    row: int | None
    column: str
    code: str
    message: str

    def __str__(self) -> str:
        loc = self.table
        if self.row is not None:
            loc += f" row {self.row}"
        if self.column:
            loc += f" [{self.column}]"
        return f"{loc}: {self.code} - {self.message}"


@dataclass
class ValidationResult:
    """Aggregated validation outcome."""

    errors: list[ValidationError] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0

    def __str__(self) -> str:
        if self.ok:
            return "OK (no errors)"
        lines = [f"{len(self.errors)} error(s):"]
        for e in self.errors:
            lines.append(f"  - {e}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Constraint parsing
# ---------------------------------------------------------------------------

_CONSTRAINT_SPLIT_RE = re.compile(r";\s*")


def _parse_constraints(raw: str) -> list[str]:
    """Split a combined constraint string like 'not_null; regex:^[a-z]+$'."""
    if not raw or not raw.strip():
        return []
    return [c.strip() for c in _CONSTRAINT_SPLIT_RE.split(raw.strip()) if c.strip()]


def _try_float(val: str) -> float | None:
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Per-cell constraint checks
# ---------------------------------------------------------------------------

def _check_cell(
    value: str,
    prop: DataProperty,
    table_name: str,
    row_idx: int,
    errors: list[ValidationError],
) -> None:
    """Validate a single cell value against its DataProperty constraints."""
    constraints = _parse_constraints(prop.constraint)
    col = prop.property

    for cst in constraints:
        if cst == "not_null":
            if not value.strip():
                errors.append(ValidationError(
                    table=table_name, row=row_idx, column=col,
                    code="not_null", message="value must not be empty",
                ))

        elif cst.startswith("regex:"):
            pattern = cst[len("regex:"):]
            if value.strip() and not re.fullmatch(pattern, value.strip()):
                errors.append(ValidationError(
                    table=table_name, row=row_idx, column=col,
                    code="regex", message=f"'{value}' does not match /{pattern}/",
                ))

        elif cst.startswith("in(") and cst.endswith(")"):
            allowed = [v.strip() for v in cst[3:-1].split(",")]
            if value.strip() and value.strip() not in allowed:
                errors.append(ValidationError(
                    table=table_name, row=row_idx, column=col,
                    code="in", message=f"'{value}' not in {allowed}",
                ))

        elif cst.startswith("not_in(") and cst.endswith(")"):
            forbidden = [v.strip() for v in cst[7:-1].split(",")]
            if value.strip() and value.strip() in forbidden:
                errors.append(ValidationError(
                    table=table_name, row=row_idx, column=col,
                    code="not_in", message=f"'{value}' is forbidden ({forbidden})",
                ))

        elif cst.startswith("range(") and cst.endswith(")"):
            parts = cst[6:-1].split(",")
            if len(parts) == 2 and value.strip():
                lo, hi = _try_float(parts[0]), _try_float(parts[1])
                v = _try_float(value.strip())
                if lo is not None and hi is not None and v is not None:
                    if not (lo <= v <= hi):
                        errors.append(ValidationError(
                            table=table_name, row=row_idx, column=col,
                            code="range",
                            message=f"{v} not in [{lo}, {hi}]",
                        ))

        elif cst.startswith(">="):
            threshold = _try_float(cst[2:].strip())
            v = _try_float(value.strip())
            if threshold is not None and v is not None and v < threshold:
                errors.append(ValidationError(
                    table=table_name, row=row_idx, column=col,
                    code=">=", message=f"{v} < {threshold}",
                ))

        elif cst.startswith("<="):
            threshold = _try_float(cst[2:].strip())
            v = _try_float(value.strip())
            if threshold is not None and v is not None and v > threshold:
                errors.append(ValidationError(
                    table=table_name, row=row_idx, column=col,
                    code="<=", message=f"{v} > {threshold}",
                ))

        elif cst.startswith(">") and not cst.startswith(">="):
            threshold = _try_float(cst[1:].strip())
            v = _try_float(value.strip())
            if threshold is not None and v is not None and v <= threshold:
                errors.append(ValidationError(
                    table=table_name, row=row_idx, column=col,
                    code=">", message=f"{v} <= {threshold}",
                ))

        elif cst.startswith("<") and not cst.startswith("<="):
            threshold = _try_float(cst[1:].strip())
            v = _try_float(value.strip())
            if threshold is not None and v is not None and v >= threshold:
                errors.append(ValidationError(
                    table=table_name, row=row_idx, column=col,
                    code="<", message=f"{v} >= {threshold}",
                ))

        elif cst.startswith("== "):
            expected = cst[3:].strip()
            if value.strip() and value.strip() != expected:
                errors.append(ValidationError(
                    table=table_name, row=row_idx, column=col,
                    code="==", message=f"'{value}' != '{expected}'",
                ))

        elif cst.startswith("!= "):
            forbidden_val = cst[3:].strip()
            if value.strip() == forbidden_val:
                errors.append(ValidationError(
                    table=table_name, row=row_idx, column=col,
                    code="!=", message=f"value must not be '{forbidden_val}'",
                ))

    prop_type = prop.type.strip().lower()
    if value.strip():
        if prop_type == "bool":
            if value.strip().lower() not in ("true", "false"):
                errors.append(ValidationError(
                    table=table_name, row=row_idx, column=col,
                    code="type_bool", message=f"'{value}' is not a valid bool",
                ))
        elif prop_type in (
            "int32", "int64", "integer",
            "float32", "float64", "float",
        ):
            if _try_float(value.strip()) is None:
                errors.append(ValidationError(
                    table=table_name, row=row_idx, column=col,
                    code="type_numeric",
                    message=f"'{value}' is not a valid {prop_type}",
                ))
        elif prop_type.startswith("decimal"):
            if _try_float(value.strip()) is None:
                errors.append(ValidationError(
                    table=table_name, row=row_idx, column=col,
                    code="type_numeric",
                    message=f"'{value}' is not a valid {prop_type}",
                ))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate_data_table(
    table: DataTable,
    schema: BknObject | None = None,
    network: BknNetwork | None = None,
) -> ValidationResult:
    """Validate a DataTable against its Object schema.

    Args:
        table: Parsed DataTable from a .bknd file.
        schema: Object definition to validate against. If not provided,
            will be looked up from *network* by table.object_or_relation.
        network: BknNetwork to look up schema from (used when schema is None).

    Returns:
        ValidationResult with any errors found.
    """
    result = ValidationResult()
    table_name = table.object_or_relation or table.source_path

    if table.is_relation:
        return result

    if schema is None and network is not None:
        schema = next(
            (e for e in network.all_objects if e.id == table.object_or_relation),
            None,
        )

    if schema is None:
        result.errors.append(ValidationError(
            table=table_name, row=None, column="",
            code="no_schema",
            message=f"no Object schema found for '{table.object_or_relation}'",
        ))
        return result
    if schema.data_source is not None:
        source_type = schema.data_source.type.strip().lower()
        if source_type in {"data_view", "connection"}:
            result.errors.append(ValidationError(
                table=table_name, row=None, column="",
                code="readonly_data_source",
                message=f"object data source type '{schema.data_source.type}' cannot be materialized in .bknd",
            ))
            return result

    schema_props = {dp.property: dp for dp in schema.data_properties}
    schema_prop_names = set(schema_props.keys())

    extra_cols = [c for c in table.columns if c not in schema_prop_names]
    for col in extra_cols:
        result.errors.append(ValidationError(
            table=table_name, row=None, column=col,
            code="extra_column",
            message=f"column '{col}' not defined in Object schema",
        ))

    missing_cols = [p for p in schema_prop_names if p not in table.columns]
    for col in missing_cols:
        result.errors.append(ValidationError(
            table=table_name, row=None, column=col,
            code="missing_column",
            message=f"schema property '{col}' not present in data",
        ))

    pk_props = [dp for dp in schema.data_properties if dp.primary_key]
    pk_seen: dict[str, list[int]] = {}

    for row_idx, row in enumerate(table.rows, start=1):
        for col_name, dp in schema_props.items():
            if col_name not in row:
                continue
            value = row[col_name]
            _check_cell(value, dp, table_name, row_idx, result.errors)

        if pk_props:
            pk_val = tuple(row.get(dp.property, "") for dp in pk_props)
            pk_key = "|".join(pk_val)
            pk_seen.setdefault(pk_key, []).append(row_idx)

    for pk_key, rows in pk_seen.items():
        if len(rows) > 1:
            pk_col_names = ", ".join(dp.property for dp in pk_props)
            result.errors.append(ValidationError(
                table=table_name, row=rows[0], column=pk_col_names,
                code="pk_duplicate",
                message=f"duplicate primary key '{pk_key}' in rows {rows}",
            ))

    return result


def validate_network_data(network: BknNetwork) -> ValidationResult:
    """Validate all DataTables in a network against their Object schemas.

    Args:
        network: Loaded BknNetwork with schema definitions and data tables.

    Returns:
        Aggregated ValidationResult.
    """
    result = ValidationResult()
    for table in network.all_data_tables:
        table_result = validate_data_table(table, network=network)
        result.errors.extend(table_result.errors)
    return result