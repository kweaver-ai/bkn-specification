# Copyright The kweaver.ai Authors.
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

"""Parse .bkn/.bknd files: YAML frontmatter + Markdown body sections and tables."""

from __future__ import annotations

import re
from typing import Any

import yaml

from bkn.models import (
    Action,
    BknDocument,
    BknObject,
    Connection,
    ConnectionConfig,
    DataTable,
    DataProperty,
    DataSource,
    Endpoint,
    Frontmatter,
    LogicProperty,
    LogicPropertyParameter,
    MappingRule,
    PreCondition,
    PropertyOverride,
    Relation,
    Risk,
    RiskPreCheck,
    RiskScope,
    RiskStrategy,
    Schedule,
    ToolConfig,
)

# ---------------------------------------------------------------------------
# Column name aliases (English canonical <-> Chinese)
# ---------------------------------------------------------------------------
_COLUMN_ALIASES: dict[str, str] = {
    # Data Properties
    "属性": "Property",
    "显示名": "Display Name",
    "显示名称": "Display Name",
    "类型": "Type",
    "约束": "Constraint",
    "描述": "Description",
    "说明": "Description",
    "主键": "Primary Key",
    "显示属性": "Display Key",
    "索引": "Index",
    # Data Source
    "数据来源": "Data Source",
    "名称": "Name",
    # Endpoints
    "起点": "Source",
    "终点": "Target",
    "必须": "Required",
    # Mapping Rules
    "起点属性": "Source Property",
    "终点属性": "Target Property",
    # Logic Properties parameters
    "参数": "Parameter",
    "来源": "Source",
    "绑定": "Binding",
    # Tool Configuration
    "工具": "Tool ID",
    # Action
    "绑定对象": "Bound Object",
    "行动类型": "Action Type",
    # Pre-conditions
    "对象": "Object",
    "检查": "Check",
    "条件": "Condition",
    "消息": "Message",
    # Schedule
    "表达式": "Expression",
    # Property Override
    "索引配置": "Index Config",
    # Scope of Impact
    "对象": "Object",
    "影响说明": "Impact Description",
    # Connection
    "端点": "Endpoint",
    "凭据引用": "Secret Ref",
    # Risk
    "管控对象": "Controlled Object",
    "管控行动": "Controlled Action",
    "风险等级": "Risk Level",
    "策略": "Strategy",
    "检查项": "Check Item",
}

# Section name aliases
_SECTION_ALIASES: dict[str, str] = {
    "连接定义": "Connection",
    "数据来源": "Data Source",
    "数据属性": "Data Properties",
    "属性覆盖": "Property Override",
    "逻辑属性": "Logic Properties",
    "业务语义": "Business Semantics",
    "关联定义": "Endpoints",
    "映射规则": "Mapping Rules",
    "映射视图": "Mapping View",
    "起点映射": "Source Mapping",
    "终点映射": "Target Mapping",
    "绑定对象": "Bound Object",
    "触发条件": "Trigger Condition",
    "前置条件": "Pre-conditions",
    "工具配置": "Tool Configuration",
    "参数绑定": "Parameter Binding",
    "调度配置": "Schedule",
    "影响范围": "Scope of Impact",
    "执行说明": "Execution Description",
    "管控范围": "Control Scope",
    "管控策略": "Control Strategy",
    "前置检查": "Pre-checks",
    "回滚方案": "Rollback Plan",
    "审计要求": "Audit Requirements",
    "Endpoint": "Endpoints",
    "管控策略": "Control Policy",
}


def _normalize_column(name: str) -> str:
    """Normalize a column header to its canonical English form."""
    name = name.strip()
    return _COLUMN_ALIASES.get(name, name)


def _normalize_section(name: str) -> str:
    """Normalize a section title to its canonical English form."""
    name = name.strip()
    return _SECTION_ALIASES.get(name, name)


def _is_yes(val: str) -> bool:
    return val.strip().upper() == "YES"


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def _split_frontmatter(text: str) -> tuple[str, str]:
    """Split a .bkn file into (frontmatter_yaml, body_markdown).

    Returns ("", text) if no frontmatter is found.
    """
    stripped = text.lstrip("\ufeff")  # BOM
    if not stripped.startswith("---"):
        return "", stripped

    end = stripped.find("\n---", 3)
    if end == -1:
        return "", stripped

    newline_after = stripped.find("\n", end + 3)
    if newline_after == -1:
        fm = stripped[3:end].strip()
        return fm, ""

    fm = stripped[3:end].strip()
    body = stripped[newline_after + 1:]
    return fm, body


def _parse_table(lines: list[str]) -> list[dict[str, str]]:
    """Parse a GFM Markdown table into a list of row dicts.

    Handles alignment rows (`:---:`, `---`, etc.) and normalizes column names.
    """
    if not lines:
        return []

    table_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|"):
            table_lines.append(stripped)
        elif table_lines:
            break

    if len(table_lines) < 2:
        return []

    def _split_row(row: str) -> list[str]:
        row = row.strip()
        if row.startswith("|"):
            row = row[1:]
        if row.endswith("|"):
            row = row[:-1]
        return [cell.strip() for cell in row.split("|")]

    headers = [_normalize_column(h) for h in _split_row(table_lines[0])]

    sep_line = table_lines[1].strip()
    if re.match(r"^\|?[\s:*-]+(\|[\s:*-]+)*\|?$", sep_line):
        data_start = 2
    else:
        data_start = 1

    rows: list[dict[str, str]] = []
    for line in table_lines[data_start:]:
        cells = _split_row(line)
        row: dict[str, str] = {}
        for i, header in enumerate(headers):
            row[header] = cells[i] if i < len(cells) else ""
        rows.append(row)

    return rows


def _extract_sections(body: str, level: str = "###") -> dict[str, str]:
    """Split body text by markdown headings of the given level.

    Returns {section_title: content_text}.
    """
    pattern = re.compile(rf"^{re.escape(level)}\s+(.+)$", re.MULTILINE)
    matches = list(pattern.finditer(body))
    sections: dict[str, str] = {}

    for i, m in enumerate(matches):
        title = _normalize_section(m.group(1).strip())
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        sections[title] = body[start:end].strip()

    return sections


def _extract_sub_sections(text: str) -> dict[str, str]:
    """Extract #### sub-sections (used for Logic Properties)."""
    return _extract_sections(text, level="####")


def _extract_first_table_lines(text: str) -> list[str]:
    """Extract the first contiguous markdown table block from text."""
    lines = text.splitlines()
    table_lines: list[str] = []
    started = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|"):
            table_lines.append(stripped)
            started = True
        elif started:
            break
    return table_lines


def _parse_table_columns(table_lines: list[str]) -> list[str]:
    """Parse table header columns from raw markdown table lines."""
    if not table_lines:
        return []
    header = table_lines[0].strip()
    if header.startswith("|"):
        header = header[1:]
    if header.endswith("|"):
        header = header[:-1]
    return [_normalize_column(c.strip()) for c in header.split("|")]


# ---------------------------------------------------------------------------
# Parsing individual definition blocks
# ---------------------------------------------------------------------------

_INLINE_META_RE = re.compile(r"^-\s+\*\*(\w+)\*\*:\s*(.+)$", re.MULTILINE)
_DISPLAY_NAME_RE = re.compile(r"^\*\*(.+?)\*\*(?:\s*-\s*(.*))?$", re.MULTILINE)


def _parse_inline_meta(text: str) -> tuple[list[str], str]:
    """Extract Tags and Owner from inline metadata lines."""
    tags: list[str] = []
    owner = ""
    for m in _INLINE_META_RE.finditer(text):
        key = m.group(1).strip()
        val = m.group(2).strip()
        if key == "Tags":
            tags = [t.strip() for t in val.split(",") if t.strip()]
        elif key == "Owner":
            owner = val
    return tags, owner


def _parse_display_name(text: str) -> tuple[str, str]:
    """Extract display name and brief description from **Name** - desc line."""
    m = _DISPLAY_NAME_RE.search(text)
    if m:
        name = m.group(1).strip()
        desc = (m.group(2) or "").strip()
        return name, desc
    return "", ""


def _parse_data_source(section_text: str) -> DataSource | None:
    """Parse ### Data Source section."""
    rows = _parse_table(section_text.splitlines())
    if not rows:
        return None
    row = rows[0]
    return DataSource(
        type=row.get("Type", ""),
        id=row.get("ID", ""),
        name=row.get("Name", ""),
    )


def _parse_data_properties(section_text: str) -> list[DataProperty]:
    """Parse ### Data Properties table."""
    rows = _parse_table(section_text.splitlines())
    props: list[DataProperty] = []
    for row in rows:
        props.append(DataProperty(
            property=row.get("Property", "") or row.get("Name", ""),
            display_name=row.get("Display Name", ""),
            type=row.get("Type", ""),
            constraint=row.get("Constraint", ""),
            description=row.get("Description", ""),
            primary_key=_is_yes(row.get("Primary Key", "")),
            display_key=_is_yes(row.get("Display Key", "")),
            index=_is_yes(row.get("Index", "")),
        ))
    return props


def _parse_property_overrides(section_text: str) -> list[PropertyOverride]:
    """Parse ### Property Override table."""
    rows = _parse_table(section_text.splitlines())
    overrides: list[PropertyOverride] = []
    for row in rows:
        overrides.append(PropertyOverride(
            property=row.get("Property", ""),
            display_name=row.get("Display Name", ""),
            index_config=row.get("Index Config", ""),
            constraint=row.get("Constraint", ""),
            description=row.get("Description", ""),
        ))
    return overrides


def _parse_logic_properties(section_text: str) -> list[LogicProperty]:
    """Parse ### Logic Properties with #### sub-sections."""
    subs = _extract_sub_sections(section_text)
    props: list[LogicProperty] = []

    for prop_name, content in subs.items():
        lp = LogicProperty(name=prop_name)

        type_m = re.search(r"-\s+\*\*Type\*\*:\s*(\S+)", content)
        if type_m:
            lp.lp_type = type_m.group(1).strip()

        source_m = re.search(r"-\s+\*\*Source\*\*:\s*(.+?)(?:\((.+?)\))?\s*$", content, re.MULTILINE)
        if source_m:
            lp.source = source_m.group(1).strip()
            lp.source_type = (source_m.group(2) or "").strip()

        desc_m = re.search(r"-\s+\*\*Description\*\*:\s*(.+)$", content, re.MULTILINE)
        if desc_m:
            lp.description = desc_m.group(1).strip()

        rows = _parse_table(content.splitlines())
        for row in rows:
            lp.parameters.append(LogicPropertyParameter(
                parameter=row.get("Parameter", ""),
                type=row.get("Type", ""),
                source=row.get("Source", ""),
                binding=row.get("Binding", ""),
                description=row.get("Description", ""),
            ))

        props.append(lp)

    return props


def _parse_endpoints(section_text: str) -> list[Endpoint]:
    """Parse ### Endpoints table."""
    rows = _parse_table(section_text.splitlines())
    endpoints: list[Endpoint] = []
    for row in rows:
        endpoints.append(Endpoint(
            source=row.get("Source", ""),
            target=row.get("Target", ""),
            type=row.get("Type", ""),
            required=row.get("Required", ""),
            min=row.get("Min", ""),
            max=row.get("Max", ""),
        ))
    return endpoints


def _parse_mapping_rules(section_text: str) -> list[MappingRule]:
    """Parse ### Mapping Rules table."""
    rows = _parse_table(section_text.splitlines())
    rules: list[MappingRule] = []
    for row in rows:
        rules.append(MappingRule(
            source_property=row.get("Source Property", ""),
            target_property=row.get("Target Property", ""),
        ))
    return rules


def _parse_object_block(block_id: str, block_text: str) -> BknObject:
    """Parse a ## Object: {id} block into a BknObject model."""
    name, desc = _parse_display_name(block_text)
    tags, owner = _parse_inline_meta(block_text)
    sections = _extract_sections(block_text)

    obj = BknObject(id=block_id, name=name, description=desc, tags=tags, owner=owner)

    if "Data Source" in sections:
        obj.data_source = _parse_data_source(sections["Data Source"])

    if "Data Properties" in sections:
        obj.data_properties = _parse_data_properties(sections["Data Properties"])

    if "Property Override" in sections:
        obj.property_overrides = _parse_property_overrides(sections["Property Override"])

    if "Logic Properties" in sections:
        obj.logic_properties = _parse_logic_properties(sections["Logic Properties"])

    if "Keys" in sections:
        keys_text = sections["Keys"]
        pk_names: list[str] = []
        dk_name = ""
        for line in keys_text.splitlines():
            line = line.strip()
            if line.lower().startswith("primary key"):
                val = line.split(":", 1)[1].strip() if ":" in line else ""
                pk_names = [v.strip() for v in val.split(",") if v.strip()]
            elif line.lower().startswith("display key"):
                val = line.split(":", 1)[1].strip() if ":" in line else ""
                dk_name = val.strip()
        for dp in obj.data_properties:
            if dp.property in pk_names:
                dp.primary_key = True
            if dp.property == dk_name:
                dp.display_key = True

    if "Business Semantics" in sections:
        obj.business_semantics = sections["Business Semantics"]

    return obj


def _parse_relation_block(block_id: str, block_text: str) -> Relation:
    """Parse a ## Relation: {id} block into a Relation model."""
    name, desc = _parse_display_name(block_text)
    tags, owner = _parse_inline_meta(block_text)
    sections = _extract_sections(block_text)

    relation = Relation(id=block_id, name=name, description=desc, tags=tags, owner=owner)

    if "Endpoints" in sections:
        relation.endpoints = _parse_endpoints(sections["Endpoints"])

    if "Mapping Rules" in sections:
        relation.mapping_rules = _parse_mapping_rules(sections["Mapping Rules"])

    if "Business Semantics" in sections:
        relation.business_semantics = sections["Business Semantics"]

    return relation


def _parse_connection_config(section_text: str) -> ConnectionConfig | None:
    """Parse ### Connection section table."""
    rows = _parse_table(section_text.splitlines())
    if not rows:
        return None
    row = rows[0]
    return ConnectionConfig(
        conn_type=row.get("Type", ""),
        endpoint=row.get("Endpoint", ""),
        secret_ref=row.get("Secret Ref", ""),
    )


def _parse_connection_block(block_id: str, block_text: str) -> Connection:
    """Parse a ## Connection: {id} block into a Connection model."""
    name, desc = _parse_display_name(block_text)
    sections = _extract_sections(block_text)

    conn = Connection(id=block_id, name=name, description=desc)
    if "Connection" in sections:
        conn.config = _parse_connection_config(sections["Connection"])
    return conn


def _parse_action_block(block_id: str, block_text: str) -> Action:
    """Parse a ## Action: {id} block into an Action model."""
    name, desc = _parse_display_name(block_text)
    sections = _extract_sections(block_text)

    action = Action(id=block_id, name=name, description=desc)

    bound_rows = _parse_table(block_text.splitlines())
    for row in bound_rows:
        if "Bound Object" in row:
            action.bound_object = row["Bound Object"]
            action.action_type = row.get("Action Type", "")
            break

    if "Trigger Condition" in sections:
        yaml_m = re.search(r"```yaml\s*\n(.+?)```", sections["Trigger Condition"], re.DOTALL)
        action.trigger_condition = yaml_m.group(1).strip() if yaml_m else sections["Trigger Condition"]

    if "Pre-conditions" in sections:
        rows = _parse_table(sections["Pre-conditions"].splitlines())
        for row in rows:
            action.pre_conditions.append(PreCondition(
                object=row.get("Object", ""),
                check=row.get("Check", ""),
                condition=row.get("Condition", ""),
                message=row.get("Message", ""),
            ))

    if "Tool Configuration" in sections:
        rows = _parse_table(sections["Tool Configuration"].splitlines())
        if rows:
            r = rows[0]
            tool_type = r.get("Type", "")
            tool_id = r.get("Tool ID", "") or r.get("MCP", "")
            action.tool_config = ToolConfig(type=tool_type, tool_id=tool_id)

    if "Parameter Binding" in sections:
        rows = _parse_table(sections["Parameter Binding"].splitlines())
        action.parameter_binding = rows

    if "Schedule" in sections:
        rows = _parse_table(sections["Schedule"].splitlines())
        if rows:
            r = rows[0]
            action.schedule = Schedule(
                type=r.get("Type", ""),
                expression=r.get("Expression", ""),
            )

    if "Scope of Impact" in sections:
        rows = _parse_table(sections["Scope of Impact"].splitlines())
        action.scope_of_impact = rows

    if "Execution Description" in sections:
        action.execution_description = sections["Execution Description"]

    return action


def _parse_risk_block(block_id: str, block_text: str) -> Risk:
    """Parse a ## Risk: {id} block into a Risk model."""
    name, desc = _parse_display_name(block_text)
    sections = _extract_sections(block_text)

    risk = Risk(id=block_id, name=name, description=desc)
    if "Control Scope" in sections:
        rows = _parse_table(sections["Control Scope"].splitlines())
        risk.control_scope = [
            RiskScope(
                controlled_object=row.get("Controlled Object", ""),
                controlled_action=row.get("Controlled Action", ""),
                risk_level=row.get("Risk Level", ""),
            )
            for row in rows
        ]
    if "Control Strategy" in sections:
        rows = _parse_table(sections["Control Strategy"].splitlines())
        risk.control_strategies = [
            RiskStrategy(
                condition=row.get("Condition", ""),
                strategy=row.get("Strategy", ""),
            )
            for row in rows
        ]
    if "Pre-checks" in sections:
        rows = _parse_table(sections["Pre-checks"].splitlines())
        risk.pre_checks = [
            RiskPreCheck(
                check_item=row.get("Check Item", ""),
                type=row.get("Type", ""),
                description=row.get("Description", ""),
            )
            for row in rows
        ]
    if "Rollback Plan" in sections:
        risk.rollback_plan = sections["Rollback Plan"]
    if "Audit Requirements" in sections:
        risk.audit_requirements = sections["Audit Requirements"]
    return risk


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_DEFINITION_RE = re.compile(
    r"^##\s+(Object(?:Type)?|Relation(?:Type)?|Action(?:Type)?|Risk(?:Type)?|Connection|ConceptGroup):\s*(.+?)\s*$",
    re.MULTILINE,
)

_VALID_BKN_TYPES = frozenset({
    "network", "knowledge_network",
    "object", "object_type",
    "relation", "relation_type",
    "action", "action_type",
    "risk", "risk_type",
    "concept_group",
    "fragment", "data", "connection",
})

_NETWORK_TYPES = frozenset({"network", "knowledge_network"})

_HEADING_CATEGORY: dict[str, str] = {
    "Object": "Object",
    "ObjectType": "Object",
    "Relation": "Relation",
    "RelationType": "Relation",
    "Action": "Action",
    "ActionType": "Action",
    "Risk": "Risk",
    "RiskType": "Risk",
    "Connection": "Connection",
    "ConceptGroup": "ConceptGroup",
}


def parse_frontmatter(text: str) -> Frontmatter:
    """Parse the YAML frontmatter of a .bkn file."""
    fm_str, _ = _split_frontmatter(text)
    if not fm_str:
        return Frontmatter()

    data: dict[str, Any] = yaml.safe_load(fm_str) or {}

    fm = Frontmatter(
        type=str(data.get("type", "")),
        id=str(data.get("id", "")),
        name=str(data.get("name", "")),
        version=str(data.get("version", "")),
        description=str(data.get("description", "")),
        network=str(data.get("network", "")),
        namespace=str(data.get("namespace", "")),
        owner=str(data.get("owner", "")),
        spec_version=str(data.get("spec_version", "")),
        risk_level=str(data.get("risk_level", "")),
        object=str(data.get("object", "")),
        relation=str(data.get("relation", "")),
        source=str(data.get("source", "")),
    )

    if "tags" in data and isinstance(data["tags"], list):
        fm.tags = [str(t) for t in data["tags"]]
    if "includes" in data and isinstance(data["includes"], list):
        fm.includes = [str(i) for i in data["includes"]]
    if "enabled" in data:
        fm.enabled = bool(data["enabled"])
    if "requires_approval" in data:
        fm.requires_approval = bool(data["requires_approval"])

    known_keys = {
        "type", "id", "name", "version", "tags", "description",
        "includes", "network", "namespace", "owner", "spec_version",
        "enabled", "risk_level", "requires_approval",
        "object", "relation", "source",
    }
    fm.extra = {k: v for k, v in data.items() if k not in known_keys}

    return fm


def parse_body(text: str) -> tuple[list[BknObject], list[Relation], list[Action], list[Risk], list[Connection]]:
    """Parse the Markdown body of a .bkn file into lists of definitions."""
    _, body = _split_frontmatter(text)

    matches = list(_DEFINITION_RE.finditer(body))
    objects: list[BknObject] = []
    relations: list[Relation] = []
    actions: list[Action] = []
    risks: list[Risk] = []
    connections: list[Connection] = []

    for i, m in enumerate(matches):
        def_type = _HEADING_CATEGORY.get(m.group(1), m.group(1))
        def_id = m.group(2).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        block_text = body[start:end]

        hr_split = re.split(r"^\s*---\s*$", block_text, flags=re.MULTILINE)
        block_text = hr_split[0]

        if def_type == "Object":
            objects.append(_parse_object_block(def_id, block_text))
        elif def_type == "Relation":
            relations.append(_parse_relation_block(def_id, block_text))
        elif def_type == "Action":
            actions.append(_parse_action_block(def_id, block_text))
        elif def_type == "Risk":
            risks.append(_parse_risk_block(def_id, block_text))
        elif def_type == "Connection":
            connections.append(_parse_connection_block(def_id, block_text))

    return objects, relations, actions, risks, connections


def parse_data_tables(
    text: str,
    frontmatter: Frontmatter | None = None,
    source_path: str = "",
) -> list[DataTable]:
    """Parse .bknd body into DataTable list.

    Raises:
        ValueError: If object and relation are both set or both empty (must be
            mutually exclusive). If no valid table header or table is found.
    """
    fm = frontmatter or parse_frontmatter(text)
    _, body = _split_frontmatter(text)

    has_object = bool(fm.object.strip())
    has_relation = bool(fm.relation.strip())
    if has_object and has_relation:
        raise ValueError(
            "type: data frontmatter must have exactly one of object or relation, "
            f"got both: object={fm.object!r}, relation={fm.relation!r}"
        )
    if not has_object and not has_relation:
        raise ValueError(
            "type: data frontmatter must have exactly one of object or relation, "
            "got neither"
        )

    heading_match = re.search(r"^#{1,2}\s+(.+)$", body, re.MULTILINE)
    if not heading_match:
        raise ValueError("type: data body must have a heading (# or ##) followed by a table")

    heading_name = heading_match.group(1).strip()
    table_text = body[heading_match.end():]
    raw_table_lines = _extract_first_table_lines(table_text)
    rows = _parse_table(raw_table_lines)
    columns = _parse_table_columns(raw_table_lines)

    if len(raw_table_lines) < 2 or not columns:
        raise ValueError(
            "type: data body must have a valid GFM table (header + separator + rows)"
        )

    is_relation = has_relation
    object_or_relation = fm.relation if is_relation else fm.object

    return [
        DataTable(
            object_or_relation=object_or_relation,
            is_relation=is_relation,
            columns=columns,
            rows=rows,
            source_path=source_path,
            network=fm.network,
        )
    ]


def parse(text: str, source_path: str = "") -> BknDocument:
    """Parse a complete .bkn/.bknd/.md file into a BknDocument.

    Content must have YAML frontmatter with a valid `type` field.
    Raises ValueError if frontmatter or type is missing/invalid.
    """
    frontmatter = parse_frontmatter(text)
    fm_str, _ = _split_frontmatter(text)

    if not fm_str.strip():
        hint = ""
        if source_path and source_path.lower().endswith(".md"):
            hint = " .md files used as BKN must start with YAML frontmatter (--- ... ---)."
        raise ValueError(
            f"BKN file must have YAML frontmatter with a valid type.{hint}"
        )

    type_val = (frontmatter.type or "").strip()
    if not type_val:
        raise ValueError(
            "BKN frontmatter must include a valid 'type' field "
            "(network, object, relation, action, fragment, data, risk, connection, "
            "knowledge_network, object_type, relation_type, action_type, risk_type, concept_group)."
        )
    if type_val not in _VALID_BKN_TYPES:
        raise ValueError(
            f"Invalid BKN type: {type_val!r}. "
            f"Valid types: {', '.join(sorted(_VALID_BKN_TYPES))}"
        )

    objects: list[BknObject] = []
    relations: list[Relation] = []
    actions: list[Action] = []
    risks: list[Risk] = []
    connections: list[Connection] = []
    data_tables: list[DataTable] = []
    if frontmatter.type == "data":
        data_tables = parse_data_tables(text, frontmatter=frontmatter, source_path=source_path)
    else:
        objects, relations, actions, risks, connections = parse_body(text)

    # For single-definition types, override ID/name/tags from frontmatter
    _SINGLE_DEF_MAP = {
        "object_type": objects,
        "relation_type": relations,
        "action_type": actions,
        "risk_type": risks,
    }
    if type_val in _SINGLE_DEF_MAP:
        items = _SINGLE_DEF_MAP[type_val]
        if len(items) == 1:
            item = items[0]
            if frontmatter.id:
                item.id = frontmatter.id
            if not item.name and frontmatter.name:
                item.name = frontmatter.name
            if hasattr(item, "tags") and not item.tags and frontmatter.tags:
                item.tags = frontmatter.tags

    return BknDocument(
        frontmatter=frontmatter,
        objects=objects,
        relations=relations,
        actions=actions,
        risks=risks,
        connections=connections,
        data_tables=data_tables,
        source_path=source_path,
    )