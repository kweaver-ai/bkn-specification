# Copyright The kweaver.ai Authors.
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

"""Data models for BKN documents, aligned with SPECIFICATION.md sections and table columns."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Frontmatter:
    """YAML frontmatter metadata for a .bkn/.bknd file."""
    type: str = ""
    id: str = ""
    name: str = ""
    version: str = ""
    tags: list[str] = field(default_factory=list)
    description: str = ""
    includes: list[str] = field(default_factory=list)
    network: str = ""
    namespace: str = ""
    owner: str = ""
    spec_version: str = ""
    enabled: Optional[bool] = None
    risk_level: str = ""
    requires_approval: Optional[bool] = None
    object: str = ""
    relation: str = ""
    source: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class DataSource:
    """### Data Source table row."""
    type: str = ""
    id: str = ""
    name: str = ""


@dataclass
class ConnectionConfig:
    """### Connection table row (type: connection)."""
    conn_type: str = ""
    endpoint: str = ""
    secret_ref: str = ""


@dataclass
class Connection:
    """## Connection: {id} block (optional capability)."""
    id: str = ""
    name: str = ""
    description: str = ""
    config: Optional[ConnectionConfig] = None


@dataclass
class DataProperty:
    """### Data Properties table row."""
    property: str = ""
    display_name: str = ""
    type: str = ""
    constraint: str = ""
    description: str = ""
    primary_key: bool = False
    display_key: bool = False
    index: bool = False


@dataclass
class PropertyOverride:
    """### Property Override table row."""
    property: str = ""
    display_name: str = ""
    index_config: str = ""
    constraint: str = ""
    description: str = ""


@dataclass
class LogicPropertyParameter:
    """Parameter row inside a Logic Property sub-section."""
    parameter: str = ""
    type: str = ""
    source: str = ""
    binding: str = ""
    description: str = ""


@dataclass
class LogicProperty:
    """#### {property_name} under ### Logic Properties."""
    name: str = ""
    lp_type: str = ""          # metric | operator
    source: str = ""
    source_type: str = ""
    description: str = ""
    parameters: list[LogicPropertyParameter] = field(default_factory=list)


@dataclass
class Endpoint:
    """### Endpoints table row (relations)."""
    source: str = ""
    target: str = ""
    type: str = ""             # direct | data_view
    required: str = ""
    min: str = ""
    max: str = ""


@dataclass
class MappingRule:
    """### Mapping Rules table row."""
    source_property: str = ""
    target_property: str = ""


@dataclass
class ToolConfig:
    """### Tool Configuration table row."""
    type: str = ""             # tool | mcp
    tool_id: str = ""


@dataclass
class PreCondition:
    """### Pre-conditions table row."""
    object: str = ""
    check: str = ""
    condition: str = ""
    message: str = ""


@dataclass
class Schedule:
    """### Schedule table row."""
    type: str = ""             # FIX_RATE | CRON
    expression: str = ""


@dataclass
class BknObject:
    """## Object: {id} block."""
    id: str = ""
    name: str = ""
    description: str = ""
    tags: list[str] = field(default_factory=list)
    owner: str = ""
    data_source: Optional[DataSource] = None
    data_properties: list[DataProperty] = field(default_factory=list)
    property_overrides: list[PropertyOverride] = field(default_factory=list)
    logic_properties: list[LogicProperty] = field(default_factory=list)
    business_semantics: str = ""


@dataclass
class Relation:
    """## Relation: {id} block."""
    id: str = ""
    name: str = ""
    description: str = ""
    tags: list[str] = field(default_factory=list)
    owner: str = ""
    endpoints: list[Endpoint] = field(default_factory=list)
    mapping_rules: list[MappingRule] = field(default_factory=list)
    business_semantics: str = ""


@dataclass
class Action:
    """## Action: {id} block."""
    id: str = ""
    name: str = ""
    description: str = ""
    bound_object: str = ""
    action_type: str = ""
    trigger_condition: str = ""
    pre_conditions: list[PreCondition] = field(default_factory=list)
    tool_config: Optional[ToolConfig] = None
    parameter_binding: list[dict[str, str]] = field(default_factory=list)
    schedule: Optional[Schedule] = None
    scope_of_impact: list[dict[str, str]] = field(default_factory=list)
    execution_description: str = ""
    # Runtime/computed by risk assessment module: "allow" | "not_allow"; not read from BKN
    risk: str = ""


@dataclass
class RiskScope:
    """### Control Scope table row."""
    controlled_object: str = ""
    controlled_action: str = ""
    risk_level: str = ""


@dataclass
class RiskStrategy:
    """### Control Strategy table row."""
    condition: str = ""
    strategy: str = ""


@dataclass
class RiskPreCheck:
    """### Pre-checks table row."""
    check_item: str = ""
    type: str = ""
    description: str = ""


@dataclass
class Risk:
    """## Risk: {id} block."""
    id: str = ""
    name: str = ""
    description: str = ""
    control_scope: list[RiskScope] = field(default_factory=list)
    control_strategies: list[RiskStrategy] = field(default_factory=list)
    pre_checks: list[RiskPreCheck] = field(default_factory=list)
    rollback_plan: str = ""
    audit_requirements: str = ""


@dataclass
class DataTable:
    """A data table parsed from a .bknd (type: data) document."""

    object_or_relation: str = ""
    is_relation: bool = False
    columns: list[str] = field(default_factory=list)
    rows: list[dict[str, str]] = field(default_factory=list)
    source_path: str = ""
    network: str = ""

    def to_bknd(self, network: str | None = None, source: str | None = None) -> str:
        """Serialize this table to .bknd Markdown format."""
        from bkn.serializer import to_bknd_from_table
        return to_bknd_from_table(self, network=network, source=source)


@dataclass
class BknDocument:
    """A parsed .bkn/.bknd file: frontmatter + body definitions/data tables."""
    frontmatter: Frontmatter = field(default_factory=Frontmatter)
    objects: list[BknObject] = field(default_factory=list)
    relations: list[Relation] = field(default_factory=list)
    actions: list[Action] = field(default_factory=list)
    risks: list[Risk] = field(default_factory=list)
    connections: list[Connection] = field(default_factory=list)
    data_tables: list[DataTable] = field(default_factory=list)
    source_path: str = ""


@dataclass
class BknNetwork:
    """Aggregated network: root document + all included documents."""
    root: BknDocument = field(default_factory=BknDocument)
    includes: list[BknDocument] = field(default_factory=list)

    @property
    def all_objects(self) -> list[BknObject]:
        result = list(self.root.objects)
        for doc in self.includes:
            result.extend(doc.objects)
        return result

    @property
    def all_relations(self) -> list[Relation]:
        result = list(self.root.relations)
        for doc in self.includes:
            result.extend(doc.relations)
        return result

    @property
    def all_actions(self) -> list[Action]:
        result = list(self.root.actions)
        for doc in self.includes:
            result.extend(doc.actions)
        return result

    @property
    def all_risks(self) -> list[Risk]:
        result = list(self.root.risks)
        for doc in self.includes:
            result.extend(doc.risks)
        return result

    @property
    def all_data_tables(self) -> list[DataTable]:
        result = list(self.root.data_tables)
        for doc in self.includes:
            result.extend(doc.data_tables)
        return result

    @property
    def all_connections(self) -> list[Connection]:
        result = list(self.root.connections)
        for doc in self.includes:
            result.extend(doc.connections)
        return result

    def get_connection(self, connection_id: str) -> Connection | None:
        """Return connection by id, or None if not found."""
        for c in self.all_connections:
            if c.id == connection_id:
                return c
        return None