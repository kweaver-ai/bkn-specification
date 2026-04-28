# Copyright The kweaver.ai Authors.
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

"""Tests for optional connection support."""

import pytest

from bkn import load, load_network
from bkn.models import Connection, ConnectionConfig, DataSource


def test_parse_connection_file():
    """Parse a type: connection file."""
    text = """---
type: connection
id: erp_db
name: ERP Database
network: demo
---

## Connection: erp_db

**ERP Database** - Shared ERP connection.

### Connection

| Type | Endpoint | Secret Ref |
|------|----------|------------|
| postgres | postgresql://erp.example.com:5432/erp | DB_PASSWORD |
"""
    from bkn.parser import parse
    doc = parse(text)
    assert doc.frontmatter.type == "connection"
    assert doc.frontmatter.id == "erp_db"
    assert len(doc.connections) == 1
    conn = doc.connections[0]
    assert conn.id == "erp_db"
    assert conn.name == "ERP Database"
    assert conn.config is not None
    assert conn.config.conn_type == "postgres"
    assert conn.config.endpoint == "postgresql://erp.example.com:5432/erp"
    assert conn.config.secret_ref == "DB_PASSWORD"


def test_parse_object_with_connection_data_source():
    """Object with connection Data Source parses correctly."""
    text = """---
type: object
id: material
name: Material
network: demo
---

## Object: material

**Material**

### Data Source

| Type | ID | Name |
|------|-----|------|
| connection | erp_db | ERP Database |

### Data Properties

| Property | Primary Key | Display Key |
|----------|:-----------:|:-----------:|
| id | YES | |
| name | | YES |
"""
    from bkn.parser import parse
    doc = parse(text)
    assert len(doc.objects) == 1
    obj = doc.objects[0]
    assert obj.data_source is not None
    assert obj.data_source.type == "connection"
    assert obj.data_source.id == "erp_db"


def test_load_network_missing_connection_fails(tmp_path):
    root = tmp_path / "index.bkn"
    obj = tmp_path / "material.bkn"

    root.write_text(
        """---
type: network
id: demo
name: Demo
includes:
  - material.bkn
---
""",
        encoding="utf-8",
    )
    obj.write_text(
        """---
type: object
id: material
name: Material
network: demo
---

## Object: material

**Material**

### Data Source

| Type | ID | Name |
|------|-----|------|
| connection | missing_conn | Missing Connection |

### Data Properties

| Property | Primary Key |
|----------|:-----------:|
| id | YES |
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="missing connection"):
        load_network(root)