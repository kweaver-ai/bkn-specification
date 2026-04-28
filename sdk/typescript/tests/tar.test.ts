// Copyright The kweaver.ai Authors.
//
// Licensed under the Apache License, Version 2.0.
// See the LICENSE file in the project root for details.

import { describe, it, expect } from "vitest";
import { packToTar } from "../src/tar/index.js";
import { loadNetwork } from "../src/loader/index.js";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import {
  mkdtempSync,
  existsSync,
  rmSync,
  readFileSync,
  mkdirSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { spawnSync } from "node:child_process";

const __dirname = dirname(fileURLToPath(import.meta.url));
const EXAMPLES_ROOT = join(__dirname, "../../../examples");

function listTarContents(tarPath: string, gzip = false): string[] {
  const args = gzip ? ["-tzf", tarPath] : ["-tf", tarPath];
  const r = spawnSync("tar", args, { encoding: "utf-8" });
  if (r.status !== 0) return [];
  return r.stdout
    .trim()
    .split("\n")
    .filter(Boolean)
    .map((p) => p.replace(/^\.\//, ""));
}

describe("packToTar", () => {
  it("packs k8s-network directory to tar", async () => {
    const tmp = mkdtempSync(join(tmpdir(), "bkn-tar-"));
    const outPath = join(tmp, "k8s-network.tar");
    try {
      await packToTar(join(EXAMPLES_ROOT, "k8s-network"), outPath);
      expect(existsSync(outPath)).toBe(true);
      const buf = readFileSync(outPath);
      expect(buf.length).toBeGreaterThan(0);
      expect(buf.subarray(0, 5).toString()).toMatch(/^.{5}/);
    } finally {
      rmSync(tmp, { recursive: true });
    }
  });

  it("packs supplychain-hd directory to tar", async () => {
    const tmp = mkdtempSync(join(tmpdir(), "bkn-tar-"));
    const outPath = join(tmp, "supplychain-hd.tar");
    try {
      await packToTar(join(EXAMPLES_ROOT, "supplychain-hd"), outPath);
      expect(existsSync(outPath)).toBe(true);
      const contents = listTarContents(outPath);
      expect(contents.some((c) => c.endsWith("network.bkn"))).toBe(true);
      expect(contents.some((c) => c.includes("object_types/"))).toBe(true);
      expect(contents.some((c) => c.includes("relation_types/"))).toBe(true);
    } finally {
      rmSync(tmp, { recursive: true });
    }
  });

  it("tar contains expected BKN structure", async () => {
    const tmp = mkdtempSync(join(tmpdir(), "bkn-tar-"));
    const outPath = join(tmp, "out.tar");
    try {
      await packToTar(join(EXAMPLES_ROOT, "k8s-network"), outPath);
      const contents = listTarContents(outPath);
      expect(contents.some((c) => c.endsWith("network.bkn"))).toBe(true);
      expect(contents.some((c) => c.endsWith("object_types/pod.bkn"))).toBe(true);
      expect(contents.some((c) => c.endsWith("relation_types/pod_belongs_node.bkn"))).toBe(true);
      expect(contents.some((c) => c.endsWith("action_types/restart_pod.bkn"))).toBe(true);
      expect(contents.some((c) => c.endsWith("concept_groups/k8s.bkn"))).toBe(true);
    } finally {
      rmSync(tmp, { recursive: true });
    }
  });

  it("no AppleDouble (._*) entries on darwin", async () => {
    const tmp = mkdtempSync(join(tmpdir(), "bkn-tar-"));
    const outPath = join(tmp, "out.tar");
    try {
      await packToTar(join(EXAMPLES_ROOT, "k8s-network"), outPath);
      const contents = listTarContents(outPath);
      const appleDouble = contents.filter(
        (c) => c.includes("/._") || c.startsWith("._")
      );
      if (process.platform === "darwin") {
        expect(appleDouble).toHaveLength(0);
      }
    } finally {
      rmSync(tmp, { recursive: true });
    }
  });

  it("pack then extract and loadNetwork succeeds", async () => {
    const tmp = mkdtempSync(join(tmpdir(), "bkn-tar-"));
    const outPath = join(tmp, "out.tar");
    const extractDir = join(tmp, "extracted");
    try {
      await packToTar(join(EXAMPLES_ROOT, "k8s-network"), outPath);
      mkdirSync(extractDir, { recursive: true });
      const r = spawnSync("tar", ["-xf", outPath, "-C", extractDir], {
        encoding: "utf-8",
      });
      expect(r.status).toBe(0);
      const network = await loadNetwork(extractDir);
      expect(network.root.frontmatter.id).toBe("k8s-network");
      const { allObjects, allRelations } = await import("../src/models/index.js");
      expect(allObjects(network).length).toBeGreaterThan(0);
      expect(allRelations(network).length).toBeGreaterThan(0);
    } finally {
      rmSync(tmp, { recursive: true });
    }
  });

  it("throws when source does not exist", async () => {
    await expect(
      packToTar("/nonexistent/dir", "/tmp/out.tar")
    ).rejects.toThrow("not found");
  });

  it("throws when source is not a directory", async () => {
    await expect(
      packToTar(join(EXAMPLES_ROOT, "k8s-network/network.bkn"), "/tmp/out.tar")
    ).rejects.toThrow("not a directory");
  });

  it("supports gzip option", async () => {
    const tmp = mkdtempSync(join(tmpdir(), "bkn-tar-"));
    const outPath = join(tmp, "out.tar.gz");
    try {
      await packToTar(join(EXAMPLES_ROOT, "k8s-network"), outPath, {
        gzip: true,
      });
      expect(existsSync(outPath)).toBe(true);
      const buf = readFileSync(outPath);
      expect(buf[0]).toBe(0x1f);
      expect(buf[1]).toBe(0x8b);
      const contents = listTarContents(outPath, true);
      expect(contents.some((c) => c.endsWith("network.bkn"))).toBe(true);
    } finally {
      rmSync(tmp, { recursive: true });
    }
  });
});