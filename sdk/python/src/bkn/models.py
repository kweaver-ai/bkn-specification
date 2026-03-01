"""Data models for BKN documents, aligned with SPECIFICATION.md sections and table columns."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Frontmatter:
    """YAML frontmatter metadata for a .bkn file."""
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
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class DataSource:
    """### Data Source table row."""
    type: str = ""
    id: str = ""
    name: str = ""


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
    entity: str = ""
    check: str = ""
    condition: str = ""
    message: str = ""


@dataclass
class Schedule:
    """### Schedule table row."""
    type: str = ""             # FIX_RATE | CRON
    expression: str = ""


@dataclass
class Entity:
    """## Entity: {id} block."""
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
    bound_entity: str = ""
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
class BknDocument:
    """A parsed .bkn file: frontmatter + body definitions."""
    frontmatter: Frontmatter = field(default_factory=Frontmatter)
    entities: list[Entity] = field(default_factory=list)
    relations: list[Relation] = field(default_factory=list)
    actions: list[Action] = field(default_factory=list)
    source_path: str = ""


@dataclass
class BknNetwork:
    """Aggregated network: root document + all included documents."""
    root: BknDocument = field(default_factory=BknDocument)
    includes: list[BknDocument] = field(default_factory=list)

    @property
    def all_entities(self) -> list[Entity]:
        result = list(self.root.entities)
        for doc in self.includes:
            result.extend(doc.entities)
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
