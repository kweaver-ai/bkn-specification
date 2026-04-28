// Copyright The kweaver.ai Authors.
//
// Licensed under the Apache License, Version 2.0.
// See the LICENSE file in the project root for details.

import { describe, it, expect } from "vitest";
import { validateDataTable, validateNetwork } from "../src/validator/index.js";
import type { DataTable, BknObject, BknNetwork, BknDocument } from "../src/models/index.js";
import { emptyFrontmatter } from "../src/models/index.js";
import { loadNetwork } from "../src/loader/index.js";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const EXAMPLES_ROOT = join(__dirname, "../../../examples");

describe("validateDataTable", () => {
  it("returns ok for valid table", () => {
    const table: DataTable = {
      object_or_relation: "pod",
      is_relation: false,
      columns: ["id", "name"],
      rows: [{ id: "p1", name: "pod-1" }],
      source_path: "",
      network: "",
    };
    const schema: BknObject = {
      id: "pod",
      name: "Pod",
      description: "",
      tags: [],
      owner: "",
      data_properties: [
        { property: "id", display_name: "ID", type: "string", constraint: "not_null", description: "", primary_key: true, display_key: false, index: false },
        { property: "name", display_name: "Name", type: "string", constraint: "", description: "", primary_key: false, display_key: false, index: false },
      ],
      property_overrides: [],
      logic_properties: [],
      business_semantics: "",
    };
    const result = validateDataTable(table, schema);
    expect(result.ok).toBe(true);
    expect(result.errors).toHaveLength(0);
  });

  it("reports missing column", () => {
    const table: DataTable = {
      object_or_relation: "pod",
      is_relation: false,
      columns: ["id"],
      rows: [{ id: "p1" }],
      source_path: "",
      network: "",
    };
    const schema: BknObject = {
      id: "pod",
      name: "Pod",
      description: "",
      tags: [],
      owner: "",
      data_properties: [
        { property: "id", display_name: "ID", type: "string", constraint: "", description: "", primary_key: true, display_key: false, index: false },
        { property: "name", display_name: "Name", type: "string", constraint: "not_null", description: "", primary_key: false, display_key: false, index: false },
      ],
      property_overrides: [],
      logic_properties: [],
      business_semantics: "",
    };
    const result = validateDataTable(table, schema);
    expect(result.ok).toBe(false);
    expect(result.errors.some((e) => e.code === "missing_column")).toBe(true);
  });

  it("reports not_null violation", () => {
    const table: DataTable = {
      object_or_relation: "pod",
      is_relation: false,
      columns: ["id"],
      rows: [{ id: "" }],
      source_path: "",
      network: "",
    };
    const schema: BknObject = {
      id: "pod",
      name: "Pod",
      description: "",
      tags: [],
      owner: "",
      data_properties: [
        { property: "id", display_name: "ID", type: "string", constraint: "not_null", description: "", primary_key: true, display_key: false, index: false },
      ],
      property_overrides: [],
      logic_properties: [],
      business_semantics: "",
    };
    const result = validateDataTable(table, schema);
    expect(result.ok).toBe(false);
    expect(result.errors.some((e) => e.code === "not_null")).toBe(true);
  });
});

describe("validateNetwork — structural", () => {
  it("passes for examples/k8s-network", async () => {
    const path = join(EXAMPLES_ROOT, "k8s-network");
    const network = await loadNetwork(path);
    const result = validateNetwork(network);
    expect(result.ok).toBe(true);
    expect(result.errors).toHaveLength(0);
  });

  it("reports missing_frontmatter_field when id is empty on a definition doc", () => {
    const fm = emptyFrontmatter();
    fm.type = "object_type";
    fm.name = "X";
    fm.id = "";
    const doc: BknDocument = {
      frontmatter: fm,
      objects: [],
      relations: [],
      actions: [],
      risks: [],
      connections: [],
      concept_groups: [],
      data_tables: [],
      source_path: "test.bkn",
    };
    const network: BknNetwork = { root: doc, includes: [] };
    const result = validateNetwork(network);
    expect(result.ok).toBe(false);
    expect(result.errors.some((e) => e.code === "missing_frontmatter_field")).toBe(true);
  });

  it("reports invalid_id when id does not match pattern", () => {
    const fm = emptyFrontmatter();
    fm.type = "object_type";
    fm.id = "Bad_Upper";
    fm.name = "Bad";
    const doc: BknDocument = {
      frontmatter: fm,
      objects: [],
      relations: [],
      actions: [],
      risks: [],
      connections: [],
      concept_groups: [],
      data_tables: [],
      source_path: "test.bkn",
    };
    const network: BknNetwork = { root: doc, includes: [] };
    const result = validateNetwork(network);
    expect(result.ok).toBe(false);
    expect(result.errors.some((e) => e.code === "invalid_id")).toBe(true);
  });

  it("reports invalid_endpoint_ref when relation endpoint references unknown object", () => {
    const fm = emptyFrontmatter();
    fm.type = "relation_type";
    fm.id = "r1";
    fm.name = "R";
    const obj = makeMinimalObject("a");
    const docObj: BknDocument = {
      frontmatter: { ...emptyFrontmatter(), type: "object_type", id: "a", name: "A" },
      objects: [obj],
      relations: [],
      actions: [],
      risks: [],
      connections: [],
      concept_groups: [],
      data_tables: [],
      source_path: "a.bkn",
    };
    const docRel: BknDocument = {
      frontmatter: fm,
      objects: [],
      relations: [
        {
          id: "r1",
          name: "R",
          description: "",
          tags: [],
          owner: "",
          endpoints: [{ source: "a", target: "missing_obj", type: "direct", required: "", min: "", max: "" }],
          mapping_rules: [],
          business_semantics: "",
        },
      ],
      actions: [],
      risks: [],
      connections: [],
      concept_groups: [],
      data_tables: [],
      source_path: "r.bkn",
    };
    const network: BknNetwork = { root: docObj, includes: [docRel] };
    const result = validateNetwork(network);
    expect(result.ok).toBe(false);
    expect(result.errors.some((e) => e.code === "invalid_endpoint_ref")).toBe(true);
  });

  it("reports invalid_bound_object_ref when action references unknown object", () => {
    const fm = emptyFrontmatter();
    fm.type = "action_type";
    fm.id = "act1";
    fm.name = "Act";
    const obj = makeMinimalObject("only_one");
    const docObj: BknDocument = {
      frontmatter: { ...emptyFrontmatter(), type: "object_type", id: "only_one", name: "O" },
      objects: [obj],
      relations: [],
      actions: [],
      risks: [],
      connections: [],
      concept_groups: [],
      data_tables: [],
      source_path: "o.bkn",
    };
    const docAct: BknDocument = {
      frontmatter: fm,
      objects: [],
      relations: [],
      actions: [
        {
          id: "act1",
          name: "Act",
          description: "",
          bound_object: "ghost",
          action_type: "query",
          trigger_condition: "",
          pre_conditions: [],
          parameter_binding: [],
          scope_of_impact: [],
          execution_description: "",
          risk: "",
          bound_object_refs: ["ghost"],
        },
      ],
      risks: [],
      connections: [],
      concept_groups: [],
      data_tables: [],
      source_path: "act.bkn",
    };
    const network: BknNetwork = { root: docObj, includes: [docAct] };
    const result = validateNetwork(network);
    expect(result.ok).toBe(false);
    expect(result.errors.some((e) => e.code === "invalid_bound_object_ref")).toBe(true);
  });
});

function makeMinimalObject(id: string): BknObject {
  return {
    id,
    name: "N",
    description: "",
    tags: [],
    owner: "",
    data_properties: [{ property: "x", display_name: "", type: "string", constraint: "", description: "", primary_key: true, display_key: false, index: false }],
    property_overrides: [],
    logic_properties: [],
    business_semantics: "",
    has_data_properties_section: true,
    has_keys_section: true,
  };
}