// Copyright The kweaver.ai Authors.
//
// Licensed under the Apache License, Version 2.0.
// See the LICENSE file in the project root for details.

/**
 * Pack BKN directory into tar archive.
 *
 * macOS: Sets COPYFILE_DISABLE=1 when spawning tar to prevent AppleDouble
 * (._*.bkn) extended-attribute files. Without this, Go SDK parsing the same
 * tar would treat ._*.bkn as valid BKN files, producing empty ObjectTypes
 * and validation errors like "对象类名称为空".
 */

import { spawnSync } from "node:child_process";
import { resolve } from "node:path";
import { existsSync, statSync } from "node:fs";

export interface PackToTarOptions {
  /** Gzip compress the output (adds .gz, uses tar -czf). Default: false. */
  gzip?: boolean;
}

/**
 * Pack a BKN directory into a tar archive.
 *
 * Uses the system `tar` command. On macOS, sets COPYFILE_DISABLE=1 to avoid
 * AppleDouble (._*) files that would cause parsing/validation errors in Go SDK.
 *
 * @param sourceDir - Path to the BKN network directory (e.g. examples/k8s-network)
 * @param outputPath - Path for the output .tar (or .tar.gz if gzip: true)
 * @throws Error if sourceDir is not a directory or tar command fails
 */
export async function packToTar(
  sourceDir: string,
  outputPath: string,
  options?: PackToTarOptions
): Promise<void> {
  const absSource = resolve(sourceDir);
  const absOutput = resolve(outputPath);

  if (!existsSync(absSource)) {
    throw new Error(`Source directory not found: ${absSource}`);
  }
  const stat = statSync(absSource, { throwIfNoEntry: false });
  if (!stat?.isDirectory()) {
    throw new Error(`Source is not a directory: ${absSource}`);
  }

  const gzip = options?.gzip ?? false;
  const args = gzip ? ["-czf", absOutput, "."] : ["-cf", absOutput, "."];

  const env = { ...process.env };
  if (process.platform === "darwin") {
    env.COPYFILE_DISABLE = "1";
  }

  const result = spawnSync("tar", args, {
    cwd: absSource,
    env,
    stdio: ["ignore", "pipe", "pipe"],
  });

  if (result.status !== 0) {
    const stderr = (result.stderr?.toString() || "").trim();
    const stdout = (result.stdout?.toString() || "").trim();
    throw new Error(
      `tar failed (exit ${result.status}): ${stderr || stdout || "unknown error"}`
    );
  }
}