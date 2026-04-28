# Copyright The kweaver.ai Authors.
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

"""Tests for BKN .md carrier compatibility."""

from __future__ import annotations

from pathlib import Path

import pytest


class TestMdCompatNegative:
    """Negative: invalid content fails with clear errors."""

    def test_no_frontmatter_raises(self):
        """Plain .md without frontmatter raises."""
        from bkn.parser import parse

        with pytest.raises(ValueError, match="YAML frontmatter"):
            parse("# Plain doc\n\nNo frontmatter here.")

    def test_no_type_raises(self):
        """Frontmatter without type raises."""
        from bkn.parser import parse

        text = "---\nid: x\nname: 测试\n---\n## Object: x"
        with pytest.raises(ValueError, match="valid 'type' field"):
            parse(text)

    def test_invalid_type_raises(self):
        """Invalid type value raises."""
        from bkn.parser import parse

        text = "---\ntype: foo\nid: x\n---\n"
        with pytest.raises(ValueError, match="Invalid BKN type"):
            parse(text)

    def test_unsupported_extension_raises(self):
        """Unsupported file extension raises."""
        import tempfile

        from bkn.loader import load

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"---\ntype: network\nid: x\n---\n")
            p = Path(f.name)
        try:
            with pytest.raises(ValueError, match="Unsupported file extension"):
                load(p)
        finally:
            p.unlink(missing_ok=True)