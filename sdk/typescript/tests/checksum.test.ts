// Copyright The kweaver.ai Authors.
//
// Licensed under the Apache License, Version 2.0.
// See the LICENSE file in the project root for details.

import { describe, it, expect } from "vitest";
import { generateChecksum, verifyChecksum } from "../src/checksum/index.js";
import { join } from "node:path";
import { mkdtempSync, writeFileSync, rmSync, mkdirSync } from "node:fs";
import { tmpdir } from "node:os";

describe("generateChecksum and verifyChecksum", () => {
  it("generates and verifies checksum for minimal network", async () => {
    const tmp = mkdtempSync(join(tmpdir(), "bkn-"));
    try {
      mkdirSync(join(tmp, "object_types"), { recursive: true });
      writeFileSync(
        join(tmp, "network.bkn"),
        `---
type: knowledge_network
id: test
name: Test
---

# Test Network
`,
        "utf-8"
      );
      writeFileSync(
        join(tmp, "object_types", "x.bkn"),
        `---
type: object_type
id: x
name: X
network: test
---

## Object: x

**X**

### Data Properties

| Property | Type |
|----------|------|
| id | string |

### Keys

Primary Key: id
Display Key: id
`,
        "utf-8"
      );

      const content = await generateChecksum(tmp);
      expect(content).toContain("# BKN Directory Checksum");
      expect(content).toContain("sha256:");
      expect(content).toContain("network");
      expect(content).toContain("object_type:x");

      const result = await verifyChecksum(tmp);
      expect(result.ok).toBe(true);
      expect(result.errors).toHaveLength(0);
    } finally {
      rmSync(tmp, { recursive: true });
    }
  });
});