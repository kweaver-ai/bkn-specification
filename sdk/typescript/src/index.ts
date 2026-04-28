// Copyright The kweaver.ai Authors.
//
// Licensed under the Apache License, Version 2.0.
// See the LICENSE file in the project root for details.

/**
 * BKN SDK - Parse, validate, and transform Business Knowledge Network files.
 * @packageDocumentation
 */

export * from "./models/index.js";
export {
  parseBkn,
  parseFrontmatter,
  parseBody,
} from "./parser/index.js";
export {
  loadBknFile,
  loadNetwork,
  discoverRootFile,
} from "./loader/index.js";
export {
  validateDocument,
  validateNetwork,
  validateDataTable,
  type ValidationResult,
  type ValidationError,
} from "./validator/index.js";
export {
  generateChecksum,
  verifyChecksum,
  type VerifyResult,
  CHECKSUM_FILENAME,
} from "./checksum/index.js";
export {
  packToTar,
  type PackToTarOptions,
} from "./tar/index.js";

export const VERSION = "0.1.0";