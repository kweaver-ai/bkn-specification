// Copyright The kweaver.ai Authors.
//
// Licensed under the Apache License, Version 2.0.
// See the LICENSE file in the project root for details.

/**
 * Parse individual definition blocks (Object, Relation, Action, Risk, Connection).
 */

import type {
  Action,
  BknObject,
  ConceptGroup,
  Connection,
  ConnectionConfig,
  DataProperty,
  DataSource,
  Endpoint,
  LogicProperty,
  LogicPropertyParameter,
  MappingRule,
  PreCondition,
  PropertyOverride,
  Relation,
  Risk,
  RiskPreCheck,
  RiskScope,
  RiskStrategy,
  Schedule,
  ToolConfig,
} from "../models/index.js";
import { parseTable, extractSections, extractSubSections } from "./utils.js";
import { isYes } from "./aliases.js";

const INLINE_META_RE = /^-\s+\*\*(\w+)\*\*:\s*(.+)$/gm;
const DISPLAY_NAME_RE = /^\*\*(.+?)\*\*(?:\s*-\s*(.*))?$/m;

function parseInlineMeta(text: string): { tags: string[]; owner: string } {
  let tags: string[] = [];
  let owner = "";
  let m: RegExpExecArray | null;
  INLINE_META_RE.lastIndex = 0;
  while ((m = INLINE_META_RE.exec(text)) !== null) {
    const key = m[1].trim();
    const val = m[2].trim();
    if (key === "Tags") {
      tags = val.split(",").map((t) => t.trim()).filter(Boolean);
    } else if (key === "Owner") {
      owner = val;
    }
  }
  return { tags, owner };
}

function parseDisplayName(text: string): { name: string; desc: string } {
  const m = text.match(DISPLAY_NAME_RE);
  if (m) {
    return { name: m[1].trim(), desc: (m[2] ?? "").trim() };
  }
  return { name: "", desc: "" };
}

function parseDataSource(sectionText: string): DataSource | undefined {
  const rows = parseTable(sectionText.split("\n"));
  if (rows.length === 0) return undefined;
  const row = rows[0];
  return {
    type: row["Type"] ?? "",
    id: row["ID"] ?? "",
    name: row["Name"] ?? "",
  };
}

function parseDataProperties(sectionText: string): DataProperty[] {
  const rows = parseTable(sectionText.split("\n"));
  return rows.map((row) => ({
    property: row["Property"] || row["Name"] || "",
    display_name: row["Display Name"] ?? "",
    type: row["Type"] ?? "",
    constraint: row["Constraint"] ?? "",
    description: row["Description"] ?? "",
    primary_key: isYes(row["Primary Key"] ?? ""),
    display_key: isYes(row["Display Key"] ?? ""),
    index: isYes(row["Index"] ?? ""),
  }));
}

function parsePropertyOverrides(sectionText: string): PropertyOverride[] {
  const rows = parseTable(sectionText.split("\n"));
  return rows.map((row) => ({
    property: row["Property"] ?? "",
    display_name: row["Display Name"] ?? "",
    index_config: row["Index Config"] ?? "",
    constraint: row["Constraint"] ?? "",
    description: row["Description"] ?? "",
  }));
}

function parseLogicProperties(sectionText: string): LogicProperty[] {
  const subs = extractSubSections(sectionText);
  const props: LogicProperty[] = [];
  for (const [propName, content] of Object.entries(subs)) {
    const lp: LogicProperty = {
      name: propName,
      lp_type: "",
      source: "",
      source_type: "",
      description: "",
      parameters: [],
    };
    const typeM = content.match(/-\s+\*\*Type\*\*:\s*(\S+)/);
    if (typeM) lp.lp_type = typeM[1].trim();

    const sourceM = content.match(/-\s+\*\*Source\*\*:\s*(.+?)(?:\((.+?)\))?\s*$/m);
    if (sourceM) {
      lp.source = sourceM[1].trim();
      lp.source_type = (sourceM[2] ?? "").trim();
    }

    const descM = content.match(/-\s+\*\*Description\*\*:\s*(.+)$/m);
    if (descM) lp.description = descM[1].trim();

    const rows = parseTable(content.split("\n"));
    for (const row of rows) {
      lp.parameters.push({
        parameter: row["Parameter"] ?? "",
        type: row["Type"] ?? "",
        source: row["Source"] ?? "",
        binding: row["Binding"] ?? "",
        description: row["Description"] ?? "",
      });
    }
    props.push(lp);
  }
  return props;
}

function parseEndpoints(sectionText: string): Endpoint[] {
  const rows = parseTable(sectionText.split("\n"));
  return rows.map((row) => ({
    source: row["Source"] ?? "",
    target: row["Target"] ?? "",
    type: row["Type"] ?? "",
    required: row["Required"] ?? "",
    min: row["Min"] ?? "",
    max: row["Max"] ?? "",
  }));
}

function parseMappingRules(sectionText: string): MappingRule[] {
  const rows = parseTable(sectionText.split("\n"));
  return rows.map((row) => ({
    source_property: row["Source Property"] ?? "",
    target_property: row["Target Property"] ?? "",
  }));
}

function parseConnectionConfig(sectionText: string): ConnectionConfig | undefined {
  const rows = parseTable(sectionText.split("\n"));
  if (rows.length === 0) return undefined;
  const row = rows[0];
  return {
    conn_type: row["Type"] ?? "",
    endpoint: row["Endpoint"] ?? "",
    secret_ref: row["Secret Ref"] ?? "",
  };
}

export function parseObjectBlock(blockId: string, blockText: string): BknObject {
  const { name, desc } = parseDisplayName(blockText);
  const { tags, owner } = parseInlineMeta(blockText);
  const sections = extractSections(blockText);

  const obj: BknObject = {
    id: blockId,
    name,
    description: desc,
    tags,
    owner,
    data_properties: [],
    property_overrides: [],
    logic_properties: [],
    business_semantics: "",
  };

  if (sections["Data Source"]) {
    obj.data_source = parseDataSource(sections["Data Source"]);
  }
  if (sections["Data Properties"]) {
    obj.data_properties = parseDataProperties(sections["Data Properties"]);
  }
  if (sections["Property Override"]) {
    obj.property_overrides = parsePropertyOverrides(sections["Property Override"]);
  }
  if (sections["Logic Properties"]) {
    obj.logic_properties = parseLogicProperties(sections["Logic Properties"]);
  }
  if (sections["Keys"]) {
    const keysText = sections["Keys"];
    let pkNames: string[] = [];
    let dkName = "";
    for (const line of keysText.split("\n")) {
      const l = line.trim();
      if (l.toLowerCase().startsWith("primary key")) {
        const val = l.includes(":") ? l.split(":", 2)[1].trim() : "";
        pkNames = val.split(",").map((v) => v.trim()).filter(Boolean);
      } else if (l.toLowerCase().startsWith("display key")) {
        const val = l.includes(":") ? l.split(":", 2)[1].trim() : "";
        dkName = val.trim();
      }
    }
    for (const dp of obj.data_properties) {
      if (pkNames.includes(dp.property)) dp.primary_key = true;
      if (dp.property === dkName) dp.display_key = true;
    }
  }
  if (sections["Business Semantics"]) {
    obj.business_semantics = sections["Business Semantics"];
  }
  obj.has_data_properties_section = sections["Data Properties"] !== undefined;
  obj.has_keys_section = sections["Keys"] !== undefined;
  return obj;
}

export function parseRelationBlock(blockId: string, blockText: string): Relation {
  const { name, desc } = parseDisplayName(blockText);
  const { tags, owner } = parseInlineMeta(blockText);
  const sections = extractSections(blockText);

  const relation: Relation = {
    id: blockId,
    name,
    description: desc,
    tags,
    owner,
    endpoints: [],
    mapping_rules: [],
    business_semantics: "",
  };
  if (sections["Endpoints"]) {
    relation.endpoints = parseEndpoints(sections["Endpoints"]);
  }
  if (sections["Mapping Rules"]) {
    relation.mapping_rules = parseMappingRules(sections["Mapping Rules"]);
  }
  if (sections["Business Semantics"]) {
    relation.business_semantics = sections["Business Semantics"];
  }
  return relation;
}

export function parseConnectionBlock(blockId: string, blockText: string): Connection {
  const { name, desc } = parseDisplayName(blockText);
  const sections = extractSections(blockText);

  const conn: Connection = {
    id: blockId,
    name,
    description: desc,
  };
  if (sections["Connection"]) {
    conn.config = parseConnectionConfig(sections["Connection"]);
  }
  return conn;
}

export function parseActionBlock(blockId: string, blockText: string): Action {
  const { name, desc } = parseDisplayName(blockText);
  const sections = extractSections(blockText);

  const action: Action = {
    id: blockId,
    name,
    description: desc,
    bound_object: "",
    action_type: "",
    trigger_condition: "",
    pre_conditions: [],
    parameter_binding: [],
    scope_of_impact: [],
    execution_description: "",
    risk: "",
  };

  if (sections["Bound Object"]) {
    const boundRows = parseTable(sections["Bound Object"].split("\n"));
    action.bound_object_refs = boundRows
      .map((row) => (row["Bound Object"] ?? "").trim())
      .filter(Boolean);
    if (boundRows.length > 0) {
      action.bound_object = boundRows[0]["Bound Object"] ?? "";
      action.action_type = boundRows[0]["Action Type"] ?? "";
    }
  } else {
    const boundRows = parseTable(blockText.split("\n"));
    for (const row of boundRows) {
      if ("Bound Object" in row) {
        action.bound_object = row["Bound Object"] ?? "";
        action.action_type = row["Action Type"] ?? "";
        action.bound_object_refs = [action.bound_object].filter(Boolean);
        break;
      }
    }
  }

  if (sections["Trigger Condition"]) {
    const yamlM = sections["Trigger Condition"].match(/```yaml\s*\n([\s\S]+?)```/);
    action.trigger_condition = yamlM ? yamlM[1].trim() : sections["Trigger Condition"];
  }
  if (sections["Pre-conditions"]) {
    const rows = parseTable(sections["Pre-conditions"].split("\n"));
    action.pre_conditions = rows.map((row) => ({
      object: row["Object"] ?? "",
      check: row["Check"] ?? "",
      condition: row["Condition"] ?? "",
      message: row["Message"] ?? "",
    }));
  }
  if (sections["Tool Configuration"]) {
    const rows = parseTable(sections["Tool Configuration"].split("\n"));
    if (rows.length > 0) {
      const r = rows[0];
      const toolType = r["Type"] ?? "";
      const toolId = (r["Tool ID"] || r["MCP"]) || "";
      action.tool_config = { type: toolType, tool_id: toolId };
    }
  }
  if (sections["Parameter Binding"]) {
    action.parameter_binding = parseTable(sections["Parameter Binding"].split("\n"));
  }
  if (sections["Schedule"]) {
    const rows = parseTable(sections["Schedule"].split("\n"));
    if (rows.length > 0) {
      const r = rows[0];
      action.schedule = {
        type: r["Type"] ?? "",
        expression: r["Expression"] ?? "",
      };
    }
  }
  if (sections["Scope of Impact"]) {
    action.scope_of_impact = parseTable(sections["Scope of Impact"].split("\n"));
  }
  if (sections["Execution Description"]) {
    action.execution_description = sections["Execution Description"];
  }
  return action;
}

export function parseRiskBlock(blockId: string, blockText: string): Risk {
  const { name, desc } = parseDisplayName(blockText);
  const sections = extractSections(blockText);

  const risk: Risk = {
    id: blockId,
    name,
    description: desc,
    control_scope: [],
    control_strategies: [],
    pre_checks: [],
    rollback_plan: "",
    audit_requirements: "",
  };
  if (sections["Control Scope"]) {
    const rows = parseTable(sections["Control Scope"].split("\n"));
    risk.control_scope = rows.map((row) => ({
      controlled_object: row["Controlled Object"] ?? "",
      controlled_action: row["Controlled Action"] ?? "",
      risk_level: row["Risk Level"] ?? "",
    }));
  }
  if (sections["Control Strategy"]) {
    const rows = parseTable(sections["Control Strategy"].split("\n"));
    risk.control_strategies = rows.map((row) => ({
      condition: row["Condition"] ?? "",
      strategy: row["Strategy"] ?? "",
    }));
  }
  if (sections["Pre-checks"]) {
    const rows = parseTable(sections["Pre-checks"].split("\n"));
    risk.pre_checks = rows.map((row) => ({
      check_item: row["Check Item"] ?? "",
      type: row["Type"] ?? "",
      description: row["Description"] ?? "",
    }));
  }
  if (sections["Rollback Plan"]) {
    risk.rollback_plan = sections["Rollback Plan"];
  }
  if (sections["Audit Requirements"]) {
    risk.audit_requirements = sections["Audit Requirements"];
  }
  return risk;
}

export function parseConceptGroupBlock(blockId: string, blockText: string): ConceptGroup {
  const { name, desc } = parseDisplayName(blockText);
  const { tags, owner } = parseInlineMeta(blockText);
  const sections = extractSections(blockText);

  const cg: ConceptGroup = {
    id: blockId,
    name,
    description: desc,
    tags,
    owner,
    object_type_ids: [],
  };

  if (sections["Object Types"]) {
    const rows = parseTable(sections["Object Types"].split("\n"));
    for (const row of rows) {
      const id = (row["ID"] ?? row["Id"] ?? "").trim();
      if (id) cg.object_type_ids.push(id);
    }
  }

  return cg;
}