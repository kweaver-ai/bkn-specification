// Copyright The kweaver.ai Authors.
//
// Licensed under the Apache License, Version 2.0.
// See the LICENSE file in the project root for details.

/**
 * Load .bkn/.bknd/.md files from disk, resolving network includes.
 */

import { readFile } from "node:fs/promises";
import { resolve, dirname, join, relative } from "node:path";
import { existsSync, statSync } from "node:fs";
import type { BknDocument, BknNetwork } from "../models/index.js";
import { allObjects, getConnection } from "../models/index.js";
import { parseBkn } from "../parser/index.js";

export const BKN_SUPPORTED_EXTENSIONS = new Set([".bkn", ".bknd", ".md"]);
export const ROOT_CANDIDATE_NAMES = ["network.bkn", "network.md", "index.bkn", "index.md"];
export const KNOWN_SUBDIRS = [
  "object_types",
  "relation_types",
  "action_types",
  "risk_types",
  "concept_groups",
];

export interface LoadOptions {
  encoding?: "utf-8" | "utf16le" | "latin1" | "ascii" | "base64" | "hex";
}

function checkExtension(pathStr: string): void {
  const ext = pathStr.slice(pathStr.lastIndexOf(".")).toLowerCase();
  if (!BKN_SUPPORTED_EXTENSIONS.has(ext)) {
    throw new Error(
      `Unsupported file extension: ${JSON.stringify(ext)}. BKN supports: ${[...BKN_SUPPORTED_EXTENSIONS].sort().join(", ")}`
    );
  }
}

export async function discoverRootFile(directory: string): Promise<string> {
  const dir = resolve(directory);
  const stat = statSync(dir, { throwIfNoEntry: false });
  if (!stat?.isDirectory()) {
    throw new Error(`Not a directory: ${dir}`);
  }

  for (const name of ROOT_CANDIDATE_NAMES) {
    const candidate = join(dir, name);
    if (existsSync(candidate)) {
      const ext = name.slice(name.lastIndexOf(".")).toLowerCase();
      if (BKN_SUPPORTED_EXTENSIONS.has(ext)) {
        return candidate;
      }
    }
  }

  const networkFiles: string[] = [];
  const { readdir } = await import("node:fs/promises");
  const entries = await readdir(dir, { withFileTypes: true });
  for (const e of entries) {
    if (!e.isFile()) continue;
    const ext = e.name.slice(e.name.lastIndexOf(".")).toLowerCase();
    if (!BKN_SUPPORTED_EXTENSIONS.has(ext)) continue;
    try {
      const p = join(dir, e.name);
      const text = await readFile(p, "utf-8");
      const doc = parseBkn(text, { sourcePath: p });
      const t = (doc.frontmatter.type ?? "").trim().toLowerCase();
      if (t === "network" || t === "knowledge_network") {
        networkFiles.push(join(dir, e.name));
      }
    } catch {
      continue;
    }
  }

  if (networkFiles.length === 1) {
    return networkFiles[0];
  }
  if (networkFiles.length > 1) {
    throw new Error(
      `Multiple network roots in ${dir}: ${networkFiles.map((p) => p.split(/[/\\]/).pop()).join(", ")}. Use network.bkn or index.bkn as the single root.`
    );
  }
  throw new Error(
    `No root network file found in ${dir}. Expected one of: ${ROOT_CANDIDATE_NAMES.join(", ")} or a single type: network file.`
  );
}

async function collectSameDirBknFiles(
  directory: string,
  rootPath: string
): Promise<string[]> {
  const dir = resolve(directory);
  const root = resolve(rootPath);
  const rootName = root.split(/[/\\]/).pop() ?? "";

  const excludeNames = new Set([rootName]);
  for (const name of ROOT_CANDIDATE_NAMES) {
    if (existsSync(join(dir, name))) {
      excludeNames.add(name);
    }
  }

  const result: string[] = [];
  const { readdir } = await import("node:fs/promises");
  const entries = await readdir(dir, { withFileTypes: true });
  const sorted = entries.sort((a, b) => a.name.localeCompare(b.name));

  for (const e of sorted) {
    if (!e.isFile() || excludeNames.has(e.name)) continue;
    const ext = e.name.slice(e.name.lastIndexOf(".")).toLowerCase();
    if (!BKN_SUPPORTED_EXTENSIONS.has(ext)) continue;
    try {
      const p = join(dir, e.name);
      const text = await readFile(p, "utf-8");
      parseBkn(text, { sourcePath: p });
      result.push(p);
    } catch {
      continue;
    }
  }
  return result;
}

async function collectSubdirBknFiles(directory: string): Promise<string[]> {
  const result: string[] = [];
  const { readdir } = await import("node:fs/promises");

  for (const subdirName of KNOWN_SUBDIRS) {
    const subdir = join(directory, subdirName);
    if (!existsSync(subdir) || !statSync(subdir).isDirectory()) continue;
    const entries = await readdir(subdir, { withFileTypes: true });
    const sorted = entries.sort((a, b) => a.name.localeCompare(b.name));
    for (const e of sorted) {
      if (!e.isFile()) continue;
      const ext = e.name.slice(e.name.lastIndexOf(".")).toLowerCase();
      if (BKN_SUPPORTED_EXTENSIONS.has(ext)) {
        result.push(join(subdir, e.name));
      }
    }
  }
  return result;
}

export async function loadBknFile(
  path: string,
  options?: LoadOptions
): Promise<BknDocument> {
  const resolved = resolve(path);
  checkExtension(resolved);
  const text = await readFile(resolved, options?.encoding ?? "utf-8");
  return parseBkn(text, { sourcePath: resolved });
}

async function resolveIncludes(
  doc: BknDocument,
  baseDir: string,
  loadedPaths: Set<string>,
  recursionStack: Set<string>,
  result: BknDocument[]
): Promise<void> {
  for (const includeRel of doc.frontmatter.includes) {
    const includePath = resolve(baseDir, includeRel);
    const pathStr = resolve(includePath);

    if (loadedPaths.has(pathStr)) continue;
    if (recursionStack.has(pathStr)) {
      throw new Error(`Circular include detected: ${includeRel} (resolved to ${pathStr})`);
    }

    if (!existsSync(pathStr)) {
      throw new Error(`Include file not found: ${includeRel} (resolved to ${pathStr})`);
    }

    loadedPaths.add(pathStr);
    const incDoc = await loadBknFile(pathStr);
    result.push(incDoc);

    recursionStack.add(pathStr);
    try {
      await resolveIncludes(
        incDoc,
        dirname(pathStr),
        loadedPaths,
        recursionStack,
        result
      );
    } finally {
      recursionStack.delete(pathStr);
    }
  }
}

function validateNetworkReferences(network: BknNetwork): void {
  for (const obj of allObjects(network)) {
    if (!obj.data_source) continue;
    if (obj.data_source.type.trim().toLowerCase() !== "connection") continue;
    const connectionId = obj.data_source.id.trim();
    if (!connectionId || !getConnection(network, connectionId)) {
      throw new Error(
        `object ${JSON.stringify(obj.id)} references missing connection ${JSON.stringify(connectionId)}`
      );
    }
  }
}

export async function loadNetwork(
  rootPath: string,
  options?: LoadOptions
): Promise<BknNetwork> {
  let resolvedRoot = resolve(rootPath);
  const stat = statSync(resolvedRoot, { throwIfNoEntry: false });
  if (stat?.isDirectory()) {
    resolvedRoot = await discoverRootFile(resolvedRoot);
  }

  const rootDoc = await loadBknFile(resolvedRoot, options);
  const loadedPaths = new Set<string>([resolvedRoot]);
  const recursionStack = new Set<string>();
  const includes: BknDocument[] = [];

  if (rootDoc.frontmatter.includes.length > 0) {
    await resolveIncludes(
      rootDoc,
      dirname(resolvedRoot),
      loadedPaths,
      recursionStack,
      includes
    );
  } else {
    const docType = (rootDoc.frontmatter.type ?? "").trim().toLowerCase();
    if (docType === "network" || docType === "knowledge_network") {
      const implicitPaths = await collectSameDirBknFiles(
        dirname(resolvedRoot),
        resolvedRoot
      );
      implicitPaths.push(...(await collectSubdirBknFiles(dirname(resolvedRoot))));

      for (const incPath of implicitPaths) {
        const pathStr = resolve(incPath);
        if (loadedPaths.has(pathStr)) continue;
        if (recursionStack.has(pathStr)) {
          throw new Error(
            `Circular include detected: ${incPath.split(/[/\\]/).pop()} (resolved to ${pathStr})`
          );
        }
        loadedPaths.add(pathStr);
        const incDoc = await loadBknFile(incPath, options);
        includes.push(incDoc);
        recursionStack.add(pathStr);
        await resolveIncludes(
          incDoc,
          dirname(incPath),
          loadedPaths,
          recursionStack,
          includes
        );
        recursionStack.delete(pathStr);
      }
    }
  }

  const network: BknNetwork = { root: rootDoc, includes: includes };
  validateNetworkReferences(network);
  return network;
}