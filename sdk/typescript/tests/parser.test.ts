// Copyright The kweaver.ai Authors.
//
// Licensed under the Apache License, Version 2.0.
// See the LICENSE file in the project root for details.

import { describe, it, expect } from "vitest";
import { parseBkn, parseFrontmatter, parseBody } from "../src/parser/index.js";

describe("parseFrontmatter", () => {
  it("parses YAML frontmatter", () => {
    const text = `---
type: object_type
id: pod
name: Pod
network: k8s
---
# Body`;
    const fm = parseFrontmatter(text);
    expect(fm.type).toBe("object_type");
    expect(fm.id).toBe("pod");
    expect(fm.name).toBe("Pod");
    expect(fm.network).toBe("k8s");
  });

  it("returns empty frontmatter when no frontmatter", () => {
    const fm = parseFrontmatter("# No frontmatter");
    expect(fm.type).toBe("");
    expect(fm.id).toBe("");
  });
});

describe("parseBkn", () => {
  it("parses object_type document", () => {
    const text = `---
type: object_type
id: pod
name: Pod
network: k8s
---

## Object: pod

**Pod** - A Kubernetes pod

- **Tags**: k8s, workload
- **Owner**: platform

### Data Properties

| Property | Display Name | Type | Constraint | Description |
|----------|--------------|------|------------|-------------|
| id | ID | string | not_null | Pod identifier |
`;
    const doc = parseBkn(text);
    expect(doc.frontmatter.type).toBe("object_type");
    expect(doc.objects).toHaveLength(1);
    expect(doc.objects[0].id).toBe("pod");
    expect(doc.objects[0].name).toBe("Pod");
    expect(doc.objects[0].data_properties).toHaveLength(1);
    expect(doc.objects[0].data_properties[0].property).toBe("id");
  });

  it("parses network document with type knowledge_network", () => {
    const text = `---
type: knowledge_network
id: k8s-network
name: Kubernetes网络
---

# Kubernetes网络

## Network Overview

- **ObjectTypes**: pod, node, service
`;
    const doc = parseBkn(text);
    expect(doc.frontmatter.type).toBe("knowledge_network");
    expect(doc.frontmatter.id).toBe("k8s-network");
  });

  it("throws on missing frontmatter", () => {
    expect(() => parseBkn("# No frontmatter")).toThrow("YAML frontmatter");
  });

  it("throws on invalid type", () => {
    const text = `---
type: invalid_type
id: x
---
# Body`;
    expect(() => parseBkn(text)).toThrow("Invalid BKN type");
  });
});