# Copyright The kweaver.ai Authors.
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

"""Pack BKN directory into tar archive.

macOS: Sets COPYFILE_DISABLE=1 when spawning tar to prevent AppleDouble
(._*.bkn) extended-attribute files. Without this, Go SDK parsing the same
tar would treat ._*.bkn as valid BKN files, producing empty ObjectTypes
and validation errors like "对象类名称为空".
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def pack_to_tar(
    source_dir: str | Path,
    output_path: str | Path,
    *,
    gzip: bool = False,
) -> None:
    """Pack a BKN directory into a tar archive.

    Uses the system `tar` command. On macOS, sets COPYFILE_DISABLE=1 to avoid
    AppleDouble (._*) files that would cause parsing/validation errors in Go SDK.

    Args:
        source_dir: Path to the BKN network directory (e.g. examples/k8s-network).
        output_path: Path for the output .tar (or .tar.gz if gzip=True).
        gzip: If True, compress with gzip (uses tar -czf).

    Raises:
        ValueError: If source_dir is not a directory or tar command fails.
    """
    source = Path(source_dir).resolve()
    output = Path(output_path).resolve()

    if not source.exists():
        raise ValueError(f"Source directory not found: {source}")
    if not source.is_dir():
        raise ValueError(f"Source is not a directory: {source}")

    args = ["-czf", str(output), "."] if gzip else ["-cf", str(output), "."]

    env = os.environ.copy()
    if sys.platform == "darwin":
        env["COPYFILE_DISABLE"] = "1"

    result = subprocess.run(
        ["tar"] + args,
        cwd=source,
        env=env,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        err = (result.stderr or result.stdout or "unknown error").strip()
        raise ValueError(f"tar failed (exit {result.returncode}): {err}")