// Copyright The kweaver.ai Authors.
//
// Licensed under the Apache License, Version 2.0.
// See the LICENSE file in the project root for details.

/**
 * Parse .bkn/.bknd files: YAML frontmatter + Markdown body sections and tables.
 */

import yaml from "js-yaml";
import type {
  Action,
  BknDocument,
  BknObject,
  ConceptGroup,
  Connection,
  DataTable,
  Frontmatter,
  Relation,
  Risk,
} from "../models/index.js";
import { emptyFrontmatter } from "../models/index.js";
import { splitFrontmatter, parseTable, extractSections, extractFirstTableLines, parseTableColumns } from "./utils.js";
import {
  parseObjectBlock,
  parseRelationBlock,
  parseActionBlock,
  parseRiskBlock,
  parseConnectionBlock,
  parseConceptGroupBlock,
} from "./blocks.js";

const VALID_BKN_TYPES = new Set([
  "network",
  "knowledge_network",
  "object",
  "object_type",
  "relation",
  "relation_type",
  "action",
  "action_type",
  "risk",
  "risk_type",
  "concept_group",
  "fragment",
  "data",
  "connection",
]);

const DEFINITION_RE =
  /^##\s+(Object(?:Type)?|Relation(?:Type)?|Action(?:Type)?|Risk(?:Type)?|Connection|ConceptGroup):\s*(.+?)\s*$/gm;

const HEADING_CATEGORY: Record<string, string> = {
  Object: "Object",
  ObjectType: "Object",
  Relation: "Relation",
  RelationType: "Relation",
  Action: "Action",
  ActionType: "Action",
  Risk: "Risk",
  RiskType: "Risk",
  Connection: "Connection",
  ConceptGroup: "ConceptGroup",
};

export interface ParseOptions {
  sourcePath?: string;
}

export function parseFrontmatter(text: string): Frontmatter {
  const [fmStr] = splitFrontmatter(text);
  if (!fmStr) return emptyFrontmatter();

  const data = (yaml.load(fmStr) as Record<string, unknown>) ?? {};

  const fm = emptyFrontmatter();
  fm.type = String(data.type ?? "");
  fm.id = String(data.id ?? "");
  fm.name = String(data.name ?? "");
  fm.version = String(data.version ?? "");
  fm.description = String(data.description ?? "");
  fm.network = String(data.network ?? "");
  fm.namespace = String(data.namespace ?? "");
  fm.owner = String(data.owner ?? "");
  fm.spec_version = String(data.spec_version ?? "");
  fm.risk_level = String(data.risk_level ?? "");
  fm.object = String(data.object ?? "");
  fm.relation = String(data.relation ?? "");
  fm.source = String(data.source ?? "");

  if (Array.isArray(data.tags)) {
    fm.tags = (data.tags as unknown[]).map(String);
  }
  if (Array.isArray(data.includes)) {
    fm.includes = (data.includes as unknown[]).map(String);
  }
  if (data.enabled !== undefined) {
    fm.enabled = Boolean(data.enabled);
  }
  if (data.requires_approval !== undefined) {
    fm.requires_approval = Boolean(data.requires_approval);
  }

  const knownKeys = new Set([
    "type", "id", "name", "version", "tags", "description",
    "includes", "network", "namespace", "owner", "spec_version",
    "enabled", "risk_level", "requires_approval",
    "object", "relation", "source",
  ]);
  fm.extra = {};
  for (const [k, v] of Object.entries(data)) {
    if (!knownKeys.has(k)) fm.extra[k] = v;
  }
  return fm;
}

export function parseBody(text: string): {
  objects: BknObject[];
  relations: Relation[];
  actions: Action[];
  risks: Risk[];
  connections: Connection[];
  concept_groups: ConceptGroup[];
} {
  const [, body] = splitFrontmatter(text);
  const matches = [...body.matchAll(DEFINITION_RE)];

  const objects: BknObject[] = [];
  const relations: Relation[] = [];
  const actions: Action[] = [];
  const risks: Risk[] = [];
  const connections: Connection[] = [];
  const concept_groups: ConceptGroup[] = [];

  for (let i = 0; i < matches.length; i++) {
    const m = matches[i];
    const defType = HEADING_CATEGORY[m[1]] ?? m[1];
    const defId = m[2].trim();
    const start = m.index! + m[0].length;
    const end = i + 1 < matches.length ? matches[i + 1].index! : body.length;
    let blockText = body.slice(start, end);

    const hrSplit = blockText.split(/^\s*---\s*$/m);
    blockText = hrSplit[0];

    if (defType === "Object") {
      objects.push(parseObjectBlock(defId, blockText));
    } else if (defType === "Relation") {
      relations.push(parseRelationBlock(defId, blockText));
    } else if (defType === "Action") {
      actions.push(parseActionBlock(defId, blockText));
    } else if (defType === "Risk") {
      risks.push(parseRiskBlock(defId, blockText));
    } else if (defType === "Connection") {
      connections.push(parseConnectionBlock(defId, blockText));
    } else if (defType === "ConceptGroup") {
      concept_groups.push(parseConceptGroupBlock(defId, blockText));
    }
  }

  return { objects, relations, actions, risks, connections, concept_groups };
}

export function parseDataTables(
  text: string,
  frontmatter?: Frontmatter | null,
  sourcePath = ""
): DataTable[] {
  const fm = frontmatter ?? parseFrontmatter(text);
  const [, body] = splitFrontmatter(text);

  const hasObject = Boolean(fm.object.trim());
  const hasRelation = Boolean(fm.relation.trim());
  if (hasObject && hasRelation) {
    throw new Error(
      `type: data frontmatter must have exactly one of object or relation, got both: object=${JSON.stringify(fm.object)}, relation=${JSON.stringify(fm.relation)}`
    );
  }
  if (!hasObject && !hasRelation) {
    throw new Error("type: data frontmatter must have exactly one of object or relation, got neither");
  }

  const headingMatch = body.match(/^#{1,2}\s+(.+)$/m);
  if (!headingMatch) {
    throw new Error("type: data body must have a heading (# or ##) followed by a table");
  }

  const tableText = body.slice(headingMatch.index! + headingMatch[0].length);
  const rawTableLines = extractFirstTableLines(tableText);
  const rows = parseTable(rawTableLines);
  const columns = parseTableColumns(rawTableLines);

  if (rawTableLines.length < 2 || columns.length === 0) {
    throw new Error("type: data body must have a valid GFM table (header + separator + rows)");
  }

  const isRelation = hasRelation;
  const objectOrRelation = isRelation ? fm.relation : fm.object;

  return [
    {
      object_or_relation: objectOrRelation,
      is_relation: isRelation,
      columns,
      rows,
      source_path: sourcePath,
      network: fm.network,
    },
  ];
}

export function parseBkn(text: string, options?: ParseOptions): BknDocument {
  const sourcePath = options?.sourcePath ?? "";
  const frontmatter = parseFrontmatter(text);
  const [fmStr] = splitFrontmatter(text);

  if (!fmStr.trim()) {
    throw new Error(
      `BKN file must have YAML frontmatter with a valid type.${sourcePath.toLowerCase().endsWith(".md") ? " .md files used as BKN must start with YAML frontmatter (--- ... ---)." : ""}`
    );
  }

  const typeVal = (frontmatter.type ?? "").trim();
  if (!typeVal) {
    throw new Error(
      "BKN frontmatter must include a valid 'type' field (network, object, relation, action, fragment, data, risk, connection, knowledge_network, object_type, relation_type, action_type, risk_type, concept_group)."
    );
  }
  if (!VALID_BKN_TYPES.has(typeVal)) {
    throw new Error(
      `Invalid BKN type: ${JSON.stringify(typeVal)}. Valid types: ${[...VALID_BKN_TYPES].sort().join(", ")}`
    );
  }

  let objects: BknObject[] = [];
  let relations: Relation[] = [];
  let actions: Action[] = [];
  let risks: Risk[] = [];
  let connections: Connection[] = [];
  let concept_groups: ConceptGroup[] = [];
  let dataTables: DataTable[] = [];

  if (frontmatter.type === "data") {
    dataTables = parseDataTables(text, frontmatter, sourcePath);
  } else {
    const parsed = parseBody(text);
    objects = parsed.objects;
    relations = parsed.relations;
    actions = parsed.actions;
    risks = parsed.risks;
    connections = parsed.connections;
    concept_groups = parsed.concept_groups;
  }

  const SINGLE_DEF_MAP: Record<string, unknown[]> = {
    object_type: objects,
    relation_type: relations,
    action_type: actions,
    risk_type: risks,
    concept_group: concept_groups,
  };
  const items = SINGLE_DEF_MAP[typeVal];
  if (items && items.length === 1) {
    const item = items[0] as BknObject | Relation | Action | Risk | ConceptGroup;
    if (frontmatter.id) item.id = frontmatter.id;
    if (!item.name && frontmatter.name) item.name = frontmatter.name;
    if ("tags" in item && !item.tags?.length && frontmatter.tags?.length) {
      item.tags = frontmatter.tags;
    }
  }

  return {
    frontmatter,
    objects,
    relations,
    actions,
    risks,
    connections,
    concept_groups,
    data_tables: dataTables,
    source_path: sourcePath,
  };
}