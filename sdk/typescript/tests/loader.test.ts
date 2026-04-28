// Copyright The kweaver.ai Authors.
//
// Licensed under the Apache License, Version 2.0.
// See the LICENSE file in the project root for details.

import { describe, it, expect } from "vitest";
import { loadBknFile, loadNetwork, discoverRootFile } from "../src/loader/index.js";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const EXAMPLES_ROOT = join(__dirname, "../../../examples");

describe("loadBknFile", () => {
  it("loads a single .bkn file", async () => {
    const path = join(EXAMPLES_ROOT, "k8s-network/object_types/pod.bkn");
    const doc = await loadBknFile(path);
    expect(doc.frontmatter.type).toBe("object_type");
    expect(doc.objects).toHaveLength(1);
    expect(doc.objects[0].id).toBe("pod");
  });
});

describe("discoverRootFile", () => {
  it("finds network.bkn in k8s-network", async () => {
    const dir = join(EXAMPLES_ROOT, "k8s-network");
    const root = await discoverRootFile(dir);
    expect(root).toContain("network.bkn");
  });

  it("finds network.bkn in supplychain-hd", async () => {
    const dir = join(EXAMPLES_ROOT, "supplychain-hd");
    const root = await discoverRootFile(dir);
    expect(root).toContain("network.bkn");
  });
});

describe("loadNetwork", () => {
  it("loads k8s-network", async () => {
    const path = join(EXAMPLES_ROOT, "k8s-network");
    const network = await loadNetwork(path);
    expect(network.root.frontmatter.type).toBe("knowledge_network");
    expect(network.root.frontmatter.id).toBe("k8s-network");
    expect(network.includes.length).toBeGreaterThan(0);
    const { allObjects, allRelations, allActions, allRisks } = await import("../src/models/index.js");
    expect(allObjects(network).length).toBeGreaterThan(0);
    expect(allRelations(network).length).toBeGreaterThan(0);
    expect(allActions(network).length).toBeGreaterThan(0);
    expect(allRisks(network).length).toBe(0);
  });

  it("loads supplychain-hd", async () => {
    const path = join(EXAMPLES_ROOT, "supplychain-hd");
    const network = await loadNetwork(path);
    expect(network.root.frontmatter.id).toBe("supplychain-hd");
    const { allObjects, allRelations } = await import("../src/models/index.js");
    expect(allObjects(network).length).toBeGreaterThan(0);
    expect(allRelations(network).length).toBeGreaterThan(0);
  });
});