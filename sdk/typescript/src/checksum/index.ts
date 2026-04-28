// Copyright The kweaver.ai Authors.
//
// Licensed under the Apache License, Version 2.0.
// See the LICENSE file in the project root for details.

/**
 * Checksum computation and CHECKSUM generation for BKN directories.
 * Compatible with Go/examples format: {key}  sha256:{16hex}
 */

import { createHash } from "node:crypto";
import { readFile, readdir, writeFile } from "node:fs/promises";
import { resolve, join, relative } from "node:path";
import { existsSync, statSync } from "node:fs";
import { splitFrontmatter } from "../parser/utils.js";
import { parseFrontmatter } from "../parser/index.js";
import { loadNetwork } from "../loader/index.js";
import { validateNetwork } from "../validator/index.js";

export const CHECKSUM_FILENAME = "CHECKSUM";
export const CHECKSUM_EXTENSIONS = new Set([".bkn", ".bknd"]);
export const CHECKSUM_FILES = new Set(["SKILL.md"]);

function hashHex(data: string): string {
  const h = createHash("sha256").update(data, "utf-8").digest();
  return h.slice(0, 8).toString("hex");
}

function normalizeForChecksum(text: string): string {
  const normalized = text
    .replace(/\r\n/g, "\n")
    .replace(/\r/g, "\n");
  const lines = normalized.split("\n");
  const out = lines
    .map((l) => l.replace(/[ \t]+$/, ""))
    .filter((l) => l.length > 0);
  return out.join("\n");
}

async function computeSkillChecksum(path: string, root: string): Promise<string> {
  const data = await readFile(path, "utf-8");
  const norm = normalizeForChecksum(data);
  const rel = relative(root, path).replace(/\\/g, "/");
  return `${rel}  sha256:${hashHex(norm)}`;
}

async function computeBknChecksum(path: string, root: string): Promise<string[]> {
  const content = await readFile(path, "utf-8");
  let fm: Record<string, unknown>;
  try {
    fm = parseFrontmatter(content) as unknown as Record<string, unknown>;
  } catch {
    return [];
  }

  const typeVal = String(fm.type ?? "").trim();
  const id = String(fm.id ?? "").trim();

  const [, body] = splitFrontmatter(content);
  const norm = normalizeForChecksum(body);

  const results: string[] = [];

  if (typeVal === "network" || typeVal === "knowledge_network") {
    results.push(`network  sha256:${hashHex(norm)}`);
    return results;
  }

  switch (typeVal) {
    case "object_type":
      results.push(`object_type:${id}  sha256:${hashHex(norm)}`);
      break;
    case "relation_type":
      results.push(`relation_type:${id}  sha256:${hashHex(norm)}`);
      break;
    case "action_type":
      results.push(`action_type:${id}  sha256:${hashHex(norm)}`);
      break;
    case "risk_type":
      results.push(`risk_type:${id}  sha256:${hashHex(norm)}`);
      break;
    case "concept_group":
      results.push(`concept_group:${id}  sha256:${hashHex(norm)}`);
      break;
  }
  return results;
}

async function collectChecksumFiles(root: string): Promise<string[]> {
  const paths: string[] = [];

  async function walk(dir: string): Promise<void> {
    const entries = await readdir(dir, { withFileTypes: true });
    for (const e of entries) {
      const p = join(dir, e.name);
      const rel = relative(root, p).replace(/\\/g, "/");
      if (e.name === CHECKSUM_FILENAME) continue;
      if (e.isDirectory()) {
        await walk(p);
      } else if (e.isFile()) {
        if (e.name === "SKILL.md") {
          paths.push(p);
        } else if (CHECKSUM_EXTENSIONS.has(p.slice(p.lastIndexOf(".")).toLowerCase())) {
          paths.push(p);
        }
      }
    }
  }

  await walk(root);
  paths.sort((a, b) =>
    relative(root, a).localeCompare(relative(root, b))
  );
  return paths;
}

async function validateChecksumInputs(root: string): Promise<void> {
  try {
    const { discoverRootFile } = await import("../loader/index.js");
    const rootPath = await discoverRootFile(root);
    const network = await loadNetwork(rootPath);
    const result = validateNetwork(network);
    if (!result.ok) {
      const rel = relative(root, rootPath).replace(/\\/g, "/");
      throw new Error(
        `checksum validation failed for network ${rel}: ${result.errors[0]?.message ?? "validation error"}`
      );
    }
  } catch (err) {
    if (err instanceof Error) throw err;
    throw new Error(`checksum validation failed: ${err}`);
  }
}

export interface ChecksumOptions {
  filename?: string;
}

export interface VerifyResult {
  ok: boolean;
  errors: string[];
}

export async function generateChecksum(
  path: string,
  options?: ChecksumOptions
): Promise<string> {
  const root = resolve(path);
  const stat = statSync(root, { throwIfNoEntry: false });
  if (!stat?.isDirectory()) {
    throw new Error(`Not a directory: ${root}`);
  }

  await validateChecksumInputs(root);

  const entries: string[] = [];
  const files = await collectChecksumFiles(root);

  for (const p of files) {
    const rel = relative(root, p).replace(/\\/g, "/");
    const name = p.split(/[/\\]/).pop() ?? "";
    const ext = p.slice(p.lastIndexOf(".")).toLowerCase();

    if (name === "SKILL.md") {
      const line = await computeSkillChecksum(p, root);
      if (line) entries.push(line);
    } else if (CHECKSUM_EXTENSIONS.has(ext)) {
      const lines = await computeBknChecksum(p, root);
      entries.push(...lines);
    }
  }

  entries.sort();

  const now = new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
  const outLines = [
    "# BKN Directory Checksum",
    `# generated: ${now}`,
    "",
    ...entries,
  ];

  const content = outLines.join("\n") + "\n";
  const filename = options?.filename ?? "CHECKSUM";
  const outPath = join(root, filename);
  await writeFile(outPath, content, "utf-8");
  return content;
}

export async function verifyChecksum(
  path: string,
  options?: ChecksumOptions
): Promise<VerifyResult> {
  const root = resolve(path);
  const filename = options?.filename ?? CHECKSUM_FILENAME;
  const ckPath = join(root, filename);
  if (!existsSync(ckPath)) {
    return { ok: false, errors: [`${filename} not found`] };
  }

  const content = await readFile(ckPath, "utf-8");
  const declared: Record<string, string> = {};
  for (const line of content.split("\n")) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const idx = trimmed.indexOf("  ");
    if (idx >= 0) {
      const key = trimmed.slice(0, idx).trim();
      const val = trimmed.slice(idx + 2).trim();
      declared[key] = val;
    }
  }

  const errors: string[] = [];
  const files = await collectChecksumFiles(root);

  for (const p of files) {
    const rel = relative(root, p).replace(/\\/g, "/");
    const name = p.split(/[/\\]/).pop() ?? "";
    const ext = p.slice(p.lastIndexOf(".")).toLowerCase();

    let actualLines: string[] = [];
    if (name === "SKILL.md") {
      const line = await computeSkillChecksum(p, root);
      if (line) actualLines = [line];
    } else if (CHECKSUM_EXTENSIONS.has(ext)) {
      actualLines = await computeBknChecksum(p, root);
    }

    for (const line of actualLines) {
      const idx = line.indexOf("  ");
      if (idx < 0) continue;
      const defKey = line.slice(0, idx).trim();
      const actualHash = line.slice(idx + 2).trim();
      if (defKey in declared) {
        if (declared[defKey] !== actualHash) {
          errors.push(`Mismatch: ${defKey}`);
        }
        delete declared[defKey];
      } else {
        errors.push(`Unexpected definition: ${defKey}`);
      }
    }
  }

  for (const key of Object.keys(declared)) {
    if (key !== "*") {
      errors.push(`Missing definition: ${key}`);
    }
  }

  return {
    ok: errors.length === 0,
    errors,
  };
}