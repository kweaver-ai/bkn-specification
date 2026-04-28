// Copyright The kweaver.ai Authors.
//
// Licensed under the Apache License, Version 2.0.
// See the LICENSE file in the project root for details.

/**
 * Validate .bknd DataTable rows against Object/Relation schema definitions,
 * and structural rules (IDs, cross-references, required sections).
 */

import type { BknDocument, BknNetwork, BknObject, DataProperty, DataTable } from "../models/index.js";
import {
  allActions,
  allConceptGroups,
  allConnections,
  allDataTables,
  allObjects,
  allRelations,
} from "../models/index.js";

/** IDs: aligned with adp bkn-backend RegexPattern_NonBuiltin_ID. */
const ID_PATTERN = /^[a-z0-9][a-z0-9_-]{0,39}$/;

export interface ValidationError {
  table: string;
  row: number | null;
  column: string;
  code: string;
  message: string;
}

export interface ValidationResult {
  errors: ValidationError[];
  get ok(): boolean;
}

function createResult(errors: ValidationError[]): ValidationResult {
  return {
    errors,
    get ok() {
      return this.errors.length === 0;
    },
  };
}

const CONSTRAINT_SPLIT_RE = /;\s*/;

function parseConstraints(raw: string): string[] {
  if (!raw?.trim()) return [];
  return raw
    .trim()
    .split(CONSTRAINT_SPLIT_RE)
    .map((c) => c.trim())
    .filter(Boolean);
}

function tryFloat(val: string): number | null {
  const n = parseFloat(val);
  return Number.isNaN(n) ? null : n;
}

function checkCell(
  value: string,
  prop: DataProperty,
  tableName: string,
  rowIdx: number,
  errors: ValidationError[]
): void {
  const constraints = parseConstraints(prop.constraint);
  const col = prop.property;

  for (const cst of constraints) {
    if (cst === "not_null") {
      if (!value.trim()) {
        errors.push({
          table: tableName,
          row: rowIdx,
          column: col,
          code: "not_null",
          message: "value must not be empty",
        });
      }
    } else if (cst.startsWith("regex:")) {
      const pattern = cst.slice(6);
      const re = new RegExp(`^${pattern}$`);
      if (value.trim() && !re.test(value.trim())) {
        errors.push({
          table: tableName,
          row: rowIdx,
          column: col,
          code: "regex",
          message: `'${value}' does not match /${pattern}/`,
        });
      }
    } else if (cst.startsWith("in(") && cst.endsWith(")")) {
      const allowed = cst
        .slice(3, -1)
        .split(",")
        .map((v) => v.trim());
      if (value.trim() && !allowed.includes(value.trim())) {
        errors.push({
          table: tableName,
          row: rowIdx,
          column: col,
          code: "in",
          message: `'${value}' not in ${JSON.stringify(allowed)}`,
        });
      }
    } else if (cst.startsWith("not_in(") && cst.endsWith(")")) {
      const forbidden = cst
        .slice(7, -1)
        .split(",")
        .map((v) => v.trim());
      if (value.trim() && forbidden.includes(value.trim())) {
        errors.push({
          table: tableName,
          row: rowIdx,
          column: col,
          code: "not_in",
          message: `'${value}' is forbidden (${JSON.stringify(forbidden)})`,
        });
      }
    } else if (cst.startsWith("range(") && cst.endsWith(")")) {
      const parts = cst.slice(6, -1).split(",");
      if (parts.length === 2 && value.trim()) {
        const lo = tryFloat(parts[0]);
        const hi = tryFloat(parts[1]);
        const v = tryFloat(value.trim());
        if (lo != null && hi != null && v != null && (v < lo || v > hi)) {
          errors.push({
            table: tableName,
            row: rowIdx,
            column: col,
            code: "range",
            message: `${v} not in [${lo}, ${hi}]`,
          });
        }
      }
    } else if (cst.startsWith(">=")) {
      const threshold = tryFloat(cst.slice(2).trim());
      const v = tryFloat(value.trim());
      if (threshold != null && v != null && v < threshold) {
        errors.push({
          table: tableName,
          row: rowIdx,
          column: col,
          code: ">=",
          message: `${v} < ${threshold}`,
        });
      }
    } else if (cst.startsWith("<=")) {
      const threshold = tryFloat(cst.slice(2).trim());
      const v = tryFloat(value.trim());
      if (threshold != null && v != null && v > threshold) {
        errors.push({
          table: tableName,
          row: rowIdx,
          column: col,
          code: "<=",
          message: `${v} > ${threshold}`,
        });
      }
    } else if (cst.startsWith(">") && !cst.startsWith(">=")) {
      const threshold = tryFloat(cst.slice(1).trim());
      const v = tryFloat(value.trim());
      if (threshold != null && v != null && v <= threshold) {
        errors.push({
          table: tableName,
          row: rowIdx,
          column: col,
          code: ">",
          message: `${v} <= ${threshold}`,
        });
      }
    } else if (cst.startsWith("<") && !cst.startsWith("<=")) {
      const threshold = tryFloat(cst.slice(1).trim());
      const v = tryFloat(value.trim());
      if (threshold != null && v != null && v >= threshold) {
        errors.push({
          table: tableName,
          row: rowIdx,
          column: col,
          code: "<",
          message: `${v} >= ${threshold}`,
        });
      }
    } else if (cst.startsWith("== ")) {
      const expected = cst.slice(3).trim();
      if (value.trim() && value.trim() !== expected) {
        errors.push({
          table: tableName,
          row: rowIdx,
          column: col,
          code: "==",
          message: `'${value}' != '${expected}'`,
        });
      }
    } else if (cst.startsWith("!= ")) {
      const forbiddenVal = cst.slice(3).trim();
      if (value.trim() === forbiddenVal) {
        errors.push({
          table: tableName,
          row: rowIdx,
          column: col,
          code: "!=",
          message: `value must not be '${forbiddenVal}'`,
        });
      }
    }
  }

  const propType = prop.type.trim().toLowerCase();
  if (value.trim()) {
    if (propType === "bool") {
      if (!["true", "false"].includes(value.trim().toLowerCase())) {
        errors.push({
          table: tableName,
          row: rowIdx,
          column: col,
          code: "type_bool",
          message: `'${value}' is not a valid bool`,
        });
      }
    } else if (
      ["int32", "int64", "integer", "float32", "float64", "float"].includes(
        propType
      )
    ) {
      if (tryFloat(value.trim()) === null) {
        errors.push({
          table: tableName,
          row: rowIdx,
          column: col,
          code: "type_numeric",
          message: `'${value}' is not a valid ${propType}`,
        });
      }
    } else if (propType.startsWith("decimal")) {
      if (tryFloat(value.trim()) === null) {
        errors.push({
          table: tableName,
          row: rowIdx,
          column: col,
          code: "type_numeric",
          message: `'${value}' is not a valid ${propType}`,
        });
      }
    }
  }
}

export interface ValidateOptions {
  mode?: "strict" | "compat";
}

function validateStructure(network: BknNetwork, errors: ValidationError[]): void {
  const objectIds = new Set(allObjects(network).map((o) => o.id));

  for (const doc of [network.root, ...network.includes]) {
    validateDocumentFrontmatter(doc, errors);
  }

  for (const obj of allObjects(network)) {
    const path = objectSourcePath(network, obj.id) ?? obj.id;
    if (obj.has_data_properties_section === false) {
      errors.push({
        table: path,
        row: null,
        column: "",
        code: "missing_section",
        message: "ObjectType must include a ### Data Properties section",
      });
    }
    if (obj.has_keys_section === false) {
      errors.push({
        table: path,
        row: null,
        column: "",
        code: "missing_section",
        message: "ObjectType must include a ### Keys section",
      });
    }
  }

  for (const rel of allRelations(network)) {
    const path = relationSourcePath(network, rel.id) ?? rel.id;
    if (rel.endpoints.length === 0) {
      errors.push({
        table: path,
        row: null,
        column: "",
        code: "empty_endpoint",
        message: "RelationType must have at least one endpoint row under ### Endpoint(s)",
      });
    }
    for (const ep of rel.endpoints) {
      const src = (ep.source ?? "").trim();
      const tgt = (ep.target ?? "").trim();
      if (src && !objectIds.has(src)) {
        errors.push({
          table: path,
          row: null,
          column: "Source",
          code: "invalid_endpoint_ref",
          message: `endpoint source '${src}' is not a defined object type id`,
        });
      }
      if (tgt && !objectIds.has(tgt)) {
        errors.push({
          table: path,
          row: null,
          column: "Target",
          code: "invalid_endpoint_ref",
          message: `endpoint target '${tgt}' is not a defined object type id`,
        });
      }
    }
  }

  for (const act of allActions(network)) {
    const path = actionSourcePath(network, act.id) ?? act.id;
    const refs =
      act.bound_object_refs && act.bound_object_refs.length > 0
        ? act.bound_object_refs
        : act.bound_object
          ? [act.bound_object]
          : [];
    for (const bid of refs) {
      const id = (bid ?? "").trim();
      if (!id) continue;
      if (!objectIds.has(id)) {
        errors.push({
          table: path,
          row: null,
          column: "Bound Object",
          code: "invalid_bound_object_ref",
          message: `bound object '${id}' is not a defined object type id`,
        });
      }
    }
  }

  for (const conn of allConnections(network)) {
    const path = connectionSourcePath(network, conn.id) ?? conn.id;
    if (conn.id && !ID_PATTERN.test(conn.id)) {
      errors.push({
        table: path,
        row: null,
        column: "id",
        code: "invalid_id",
        message: `connection id '${conn.id}' must match ${ID_PATTERN}`,
      });
    }
  }

  for (const cg of allConceptGroups(network)) {
    const path = conceptGroupSourcePath(network, cg.id) ?? cg.id;
    for (const oid of cg.object_type_ids) {
      if (!objectIds.has(oid)) {
        errors.push({
          table: path,
          row: null,
          column: "Object Types",
          code: "invalid_concept_group_ref",
          message: `concept group lists unknown object type id '${oid}'`,
        });
      }
    }
  }
}

function validateDocumentFrontmatter(doc: BknDocument, errors: ValidationError[]): void {
  const fm = doc.frontmatter;
  const t = (fm.type ?? "").trim();
  if (t === "data") return;

  const path = doc.source_path || "<document>";
  if (!t) {
    errors.push({
      table: path,
      row: null,
      column: "type",
      code: "missing_frontmatter_field",
      message: "frontmatter 'type' is required",
    });
    return;
  }
  const id = (fm.id ?? "").trim();
  const name = (fm.name ?? "").trim();
  if (!id) {
    errors.push({
      table: path,
      row: null,
      column: "id",
      code: "missing_frontmatter_field",
      message: "frontmatter 'id' is required",
    });
  }
  if (!name) {
    errors.push({
      table: path,
      row: null,
      column: "name",
      code: "missing_frontmatter_field",
      message: "frontmatter 'name' is required",
    });
  }
  if (id && !ID_PATTERN.test(id)) {
    errors.push({
      table: path,
      row: null,
      column: "id",
      code: "invalid_id",
      message: `frontmatter id '${id}' must match ${ID_PATTERN}`,
    });
  }
}

function objectSourcePath(network: BknNetwork, objectId: string): string | undefined {
  for (const doc of [network.root, ...network.includes]) {
    if (doc.objects.some((o) => o.id === objectId)) return doc.source_path;
  }
  return undefined;
}

function relationSourcePath(network: BknNetwork, relationId: string): string | undefined {
  for (const doc of [network.root, ...network.includes]) {
    if (doc.relations.some((r) => r.id === relationId)) return doc.source_path;
  }
  return undefined;
}

function actionSourcePath(network: BknNetwork, actionId: string): string | undefined {
  for (const doc of [network.root, ...network.includes]) {
    if (doc.actions.some((a) => a.id === actionId)) return doc.source_path;
  }
  return undefined;
}

function conceptGroupSourcePath(network: BknNetwork, cgId: string): string | undefined {
  for (const doc of [network.root, ...network.includes]) {
    if (doc.concept_groups.some((c) => c.id === cgId)) return doc.source_path;
  }
  return undefined;
}

function connectionSourcePath(network: BknNetwork, connId: string): string | undefined {
  for (const doc of [network.root, ...network.includes]) {
    if (doc.connections.some((c) => c.id === connId)) return doc.source_path;
  }
  return undefined;
}

export function validateDataTable(
  table: DataTable,
  schema?: BknObject | null,
  network?: BknNetwork | null
): ValidationResult {
  const result = createResult([]);
  const tableName = table.object_or_relation || table.source_path;

  if (table.is_relation) {
    return result;
  }

  if (!schema && network) {
    schema = allObjects(network).find((o) => o.id === table.object_or_relation) ?? undefined;
  }

  if (!schema) {
    result.errors.push({
      table: tableName,
      row: null,
      column: "",
      code: "no_schema",
      message: `no Object schema found for '${table.object_or_relation}'`,
    });
    return result;
  }

  if (schema.data_source) {
    const sourceType = schema.data_source.type.trim().toLowerCase();
    if (["data_view", "connection"].includes(sourceType)) {
      result.errors.push({
        table: tableName,
        row: null,
        column: "",
        code: "readonly_data_source",
        message: `object data source type '${schema.data_source.type}' cannot be materialized in .bknd`,
      });
      return result;
    }
  }

  const schemaProps = new Map(
    schema.data_properties.map((dp) => [dp.property, dp])
  );
  const schemaPropNames = new Set(schemaProps.keys());

  for (const col of table.columns) {
    if (!schemaPropNames.has(col)) {
      result.errors.push({
        table: tableName,
        row: null,
        column: col,
        code: "extra_column",
        message: `column '${col}' not defined in Object schema`,
      });
    }
  }

  for (const col of schemaPropNames) {
    if (!table.columns.includes(col)) {
      result.errors.push({
        table: tableName,
        row: null,
        column: col,
        code: "missing_column",
        message: `schema property '${col}' not present in data`,
      });
    }
  }

  const pkProps = schema.data_properties.filter((dp) => dp.primary_key);
  const pkSeen: Record<string, number[]> = {};

  table.rows.forEach((row, rowIdx) => {
    const idx = rowIdx + 1;
    for (const [colName, dp] of schemaProps) {
      if (!(colName in row)) continue;
      const value = row[colName] ?? "";
      checkCell(value, dp, tableName, idx, result.errors);
    }

    if (pkProps.length > 0) {
      const pkVal = pkProps.map((dp) => row[dp.property] ?? "").join("|");
      if (!pkSeen[pkVal]) pkSeen[pkVal] = [];
      pkSeen[pkVal].push(idx);
    }
  });

  for (const [pkKey, rows] of Object.entries(pkSeen)) {
    if (rows.length > 1) {
      const pkColNames = pkProps.map((dp) => dp.property).join(", ");
      result.errors.push({
        table: tableName,
        row: rows[0],
        column: pkColNames,
        code: "pk_duplicate",
        message: `duplicate primary key '${pkKey}' in rows ${JSON.stringify(rows)}`,
      });
    }
  }

  return result;
}

export function validateDocument(
  doc: BknDocument,
  _options?: ValidateOptions
): ValidationResult {
  const network: BknNetwork = { root: doc, includes: [] };
  const result = createResult([]);
  validateStructure(network, result.errors);
  for (const table of allDataTables(network)) {
    const tableResult = validateDataTable(table, undefined, network);
    result.errors.push(...tableResult.errors);
  }
  return result;
}

export function validateNetwork(
  network: BknNetwork,
  _options?: ValidateOptions
): ValidationResult {
  const result = createResult([]);
  validateStructure(network, result.errors);
  for (const table of allDataTables(network)) {
    const tableResult = validateDataTable(table, undefined, network);
    result.errors.push(...tableResult.errors);
  }
  return result;
}