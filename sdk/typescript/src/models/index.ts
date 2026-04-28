// Copyright The kweaver.ai Authors.
//
// Licensed under the Apache License, Version 2.0.
// See the LICENSE file in the project root for details.

/**
 * Data models for BKN documents, aligned with SPECIFICATION.md sections.
 */

export interface Frontmatter {
  type: string;
  id: string;
  name: string;
  version: string;
  tags: string[];
  description: string;
  includes: string[];
  network: string;
  namespace: string;
  owner: string;
  spec_version: string;
  enabled?: boolean;
  risk_level: string;
  requires_approval?: boolean;
  object: string;
  relation: string;
  source: string;
  extra: Record<string, unknown>;
}

export interface DataSource {
  type: string;
  id: string;
  name: string;
}

export interface ConnectionConfig {
  conn_type: string;
  endpoint: string;
  secret_ref: string;
}

export interface Connection {
  id: string;
  name: string;
  description: string;
  config?: ConnectionConfig;
}

export interface DataProperty {
  property: string;
  display_name: string;
  type: string;
  constraint: string;
  description: string;
  primary_key: boolean;
  display_key: boolean;
  index: boolean;
}

export interface PropertyOverride {
  property: string;
  display_name: string;
  index_config: string;
  constraint: string;
  description: string;
}

export interface LogicPropertyParameter {
  parameter: string;
  type: string;
  source: string;
  binding: string;
  description: string;
}

export interface LogicProperty {
  name: string;
  lp_type: string;
  source: string;
  source_type: string;
  description: string;
  parameters: LogicPropertyParameter[];
}

export interface Endpoint {
  source: string;
  target: string;
  type: string;
  required: string;
  min: string;
  max: string;
}

export interface MappingRule {
  source_property: string;
  target_property: string;
}

export interface ToolConfig {
  type: string;
  tool_id: string;
}

export interface PreCondition {
  object: string;
  check: string;
  condition: string;
  message: string;
}

export interface Schedule {
  type: string;
  expression: string;
}

export interface BknObject {
  id: string;
  name: string;
  description: string;
  tags: string[];
  owner: string;
  data_source?: DataSource;
  data_properties: DataProperty[];
  property_overrides: PropertyOverride[];
  logic_properties: LogicProperty[];
  business_semantics: string;
  /** Set when parsing; used by structural validation */
  has_data_properties_section?: boolean;
  /** Set when parsing; used by structural validation */
  has_keys_section?: boolean;
}

export interface Relation {
  id: string;
  name: string;
  description: string;
  tags: string[];
  owner: string;
  endpoints: Endpoint[];
  mapping_rules: MappingRule[];
  business_semantics: string;
}

export interface RiskScope {
  controlled_object: string;
  controlled_action: string;
  risk_level: string;
}

export interface RiskStrategy {
  condition: string;
  strategy: string;
}

export interface RiskPreCheck {
  check_item: string;
  type: string;
  description: string;
}

export interface Risk {
  id: string;
  name: string;
  description: string;
  control_scope: RiskScope[];
  control_strategies: RiskStrategy[];
  pre_checks: RiskPreCheck[];
  rollback_plan: string;
  audit_requirements: string;
}

export interface Action {
  id: string;
  name: string;
  description: string;
  bound_object: string;
  action_type: string;
  /** All object type IDs from the Bound Object table (multi-row actions) */
  bound_object_refs?: string[];
  trigger_condition: string;
  pre_conditions: PreCondition[];
  tool_config?: ToolConfig;
  parameter_binding: Record<string, string>[];
  schedule?: Schedule;
  scope_of_impact: Record<string, string>[];
  execution_description: string;
  risk: string;
}

/** Concept group definition (concept_group files). */
export interface ConceptGroup {
  id: string;
  name: string;
  description: string;
  tags: string[];
  owner: string;
  /** Object type IDs listed under ### Object Types */
  object_type_ids: string[];
}

export interface DataTable {
  object_or_relation: string;
  is_relation: boolean;
  columns: string[];
  rows: Record<string, string>[];
  source_path: string;
  network: string;
}

export interface BknDocument {
  frontmatter: Frontmatter;
  objects: BknObject[];
  relations: Relation[];
  actions: Action[];
  risks: Risk[];
  connections: Connection[];
  concept_groups: ConceptGroup[];
  data_tables: DataTable[];
  source_path: string;
}

export interface BknNetwork {
  root: BknDocument;
  includes: BknDocument[];
}

export function emptyFrontmatter(): Frontmatter {
  return {
    type: "",
    id: "",
    name: "",
    version: "",
    tags: [],
    description: "",
    includes: [],
    network: "",
    namespace: "",
    owner: "",
    spec_version: "",
    risk_level: "",
    object: "",
    relation: "",
    source: "",
    extra: {},
  };
}

export function allObjects(network: BknNetwork): BknObject[] {
  const result = [...network.root.objects];
  for (const doc of network.includes) {
    result.push(...doc.objects);
  }
  return result;
}

export function allRelations(network: BknNetwork): Relation[] {
  const result = [...network.root.relations];
  for (const doc of network.includes) {
    result.push(...doc.relations);
  }
  return result;
}

export function allActions(network: BknNetwork): Action[] {
  const result = [...network.root.actions];
  for (const doc of network.includes) {
    result.push(...doc.actions);
  }
  return result;
}

export function allRisks(network: BknNetwork): Risk[] {
  const result = [...network.root.risks];
  for (const doc of network.includes) {
    result.push(...doc.risks);
  }
  return result;
}

export function allDataTables(network: BknNetwork): DataTable[] {
  const result = [...network.root.data_tables];
  for (const doc of network.includes) {
    result.push(...doc.data_tables);
  }
  return result;
}

export function allConnections(network: BknNetwork): Connection[] {
  const result = [...network.root.connections];
  for (const doc of network.includes) {
    result.push(...doc.connections);
  }
  return result;
}

export function allConceptGroups(network: BknNetwork): ConceptGroup[] {
  const result = [...network.root.concept_groups];
  for (const doc of network.includes) {
    result.push(...doc.concept_groups);
  }
  return result;
}

export function getConnection(network: BknNetwork, connectionId: string): Connection | undefined {
  for (const c of allConnections(network)) {
    if (c.id === connectionId) return c;
  }
  return undefined;
}