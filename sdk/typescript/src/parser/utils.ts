// Copyright The kweaver.ai Authors.
//
// Licensed under the Apache License, Version 2.0.
// See the LICENSE file in the project root for details.

/**
 * Low-level parsing utilities.
 */

import { normalizeColumn, normalizeSection } from "./aliases.js";

export function splitFrontmatter(text: string): [string, string] {
  const stripped = text.replace(/^\uFEFF/, "");
  if (!stripped.startsWith("---")) {
    return ["", stripped];
  }
  const end = stripped.indexOf("\n---", 3);
  if (end === -1) {
    return ["", stripped];
  }
  const newlineAfter = stripped.indexOf("\n", end + 3);
  if (newlineAfter === -1) {
    const fm = stripped.slice(3, end).trim();
    return [fm, ""];
  }
  const fm = stripped.slice(3, end).trim();
  const body = stripped.slice(newlineAfter + 1);
  return [fm, body];
}

function splitRow(row: string): string[] {
  let r = row.trim();
  if (r.startsWith("|")) r = r.slice(1);
  if (r.endsWith("|")) r = r.slice(0, -1);
  return r.split("|").map((c) => c.trim());
}

export function parseTable(lines: string[]): Record<string, string>[] {
  const tableLines: string[] = [];
  for (const line of lines) {
    const stripped = line.trim();
    if (stripped.startsWith("|")) {
      tableLines.push(stripped);
    } else if (tableLines.length > 0) {
      break;
    }
  }
  if (tableLines.length < 2) return [];

  const headers = splitRow(tableLines[0]).map(normalizeColumn);
  const sepLine = tableLines[1].trim();
  const isSep = /^\|?[\s:*-]+(\|[\s:*-]+)*\|?$/.test(sepLine);
  const dataStart = isSep ? 2 : 1;

  const rows: Record<string, string>[] = [];
  for (const line of tableLines.slice(dataStart)) {
    const cells = splitRow(line);
    const row: Record<string, string> = {};
    for (let i = 0; i < headers.length; i++) {
      row[headers[i]] = cells[i] ?? "";
    }
    rows.push(row);
  }
  return rows;
}

export function extractSections(body: string, level = "###"): Record<string, string> {
  const escaped = level.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const pattern = new RegExp(`^${escaped}\\s+(.+)$`, "gm");
  const matches = [...body.matchAll(pattern)];
  const sections: Record<string, string> = {};
  for (let i = 0; i < matches.length; i++) {
    const title = normalizeSection(matches[i][1].trim());
    const start = matches[i].index! + matches[i][0].length;
    const end = i + 1 < matches.length ? matches[i + 1].index! : body.length;
    sections[title] = body.slice(start, end).trim();
  }
  return sections;
}

export function extractSubSections(text: string): Record<string, string> {
  return extractSections(text, "####");
}

export function extractFirstTableLines(text: string): string[] {
  const lines = text.split("\n");
  const tableLines: string[] = [];
  let started = false;
  for (const line of lines) {
    const stripped = line.trim();
    if (stripped.startsWith("|")) {
      tableLines.push(stripped);
      started = true;
    } else if (started) {
      break;
    }
  }
  return tableLines;
}

export function parseTableColumns(tableLines: string[]): string[] {
  if (tableLines.length === 0) return [];
  let header = tableLines[0].trim();
  if (header.startsWith("|")) header = header.slice(1);
  if (header.endsWith("|")) header = header.slice(0, -1);
  return header.split("|").map((c) => normalizeColumn(c.trim()));
}