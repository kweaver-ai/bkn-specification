# BKN Language Specification

Version: 2.0.1

## Overview

BKN (Business Knowledge Network) is a declarative modeling language based on Markdown for defining objects, relations, and actions in business knowledge networks. BKN describes model structure and semantics only — runtime capabilities such as validation engines, data pipelines, and workflows are provided by platforms that consume BKN models.

This document defines the complete syntax specification for BKN.

### Glossary

**Core Concepts**

| Term | Meaning |
|------|---------|
| BKN | Business Knowledge Network |
| knowledge_network | The overall collection of a business knowledge network |
| object_type | Business object type (e.g., Pod/Node/Service) |
| relation_type | Relationship type connecting two object_types (e.g., belongs_to/routes_to) |
| action_type | Operation definition on an object_type (can bind to tool or mcp) |
| risk_type | Risk type; structured modeling of execution risk for actions and objects |
| concept_group | Concept group; organizes related object types together |

**Object Structure**

| Term | Meaning |
|------|---------|
| data_view | Data view; the data source an object/relation maps to |
| data_properties | Object property definition table; declares field name, type, description |
| keys | Key definitions; declares primary key, display key, incremental key |
| logic_properties | Logic properties; derived fields from external sources (metric / operator) |
| primary_key | Primary key field; uniquely identifies an instance (declared in Keys section) |
| display_key | Display key field; used for UI display and search (declared in Keys section) |
| metric | Logic property type: metric; measurement value obtained from external data sources |
| operator | Logic property type: operator; computation logic based on input parameters |

**Action Structure**

| Term | Meaning |
|------|---------|
| trigger_condition | Trigger condition; defines when an action executes automatically |
| pre-conditions | Pre-conditions; data checks that must pass before execution (blocks execution if not met) |
| tool | External tool bound to an action |
| mcp | Model Context Protocol; MCP tool bound to an action |
| schedule | Schedule configuration (FIX_RATE or CRON) for periodic execution |
| scope_of_impact | Scope of impact; declares which objects are affected by the action |

**File Organization**

| Term | Meaning |
|------|---------|
| frontmatter | YAML metadata block (wrapped in `---`); header of each .bkn file |
| knowledge_network | File type `type: knowledge_network`; top-level container for a complete knowledge network |

### Primitives Table

Section titles and table column names should use English as the canonical form. Parsers should support both English and Chinese for compatibility.

The table below is organized by **unified heading level**, applicable to all BKN file types (knowledge_network / object_type / relation_type / action_type / risk_type / concept_group).

| Level | English (canonical) | Definition | Syntax |
|:-----:|---------------------|------------|--------|
| `#` | {Network Name} | Network title | `# {name}` |
| `##` | Network Overview | Network topology overview | `## Network Overview` |
| `##` | ObjectType | Individual object type definition | `## ObjectType: {name}` |
| `##` | RelationType | Individual relation type definition | `## RelationType: {name}` |
| `##` | ActionType | Individual action type definition | `## ActionType: {name}` |
| `##` | RiskType | Individual risk type definition | `## RiskType: {name}` |
| `##` | ConceptGroup | Concept group definition | `## ConceptGroup: {name}` |
| `###` | Data Source | The data view this object maps from | `### Data Source` |
| `###` | Data Properties | Explicit list of fields (name, type, description) | `### Data Properties` |
| `###` | Keys | Primary key, display key, incremental key | `### Keys` |
| `###` | Logic Properties | Derived fields: metric, operator | `### Logic Properties` |
| `###` | Endpoint | Relation endpoint: source, target, type | `### Endpoint` |
| `###` | Mapping Rules | How source/target properties map | `### Mapping Rules` |
| `###` | Mapping View | For data_view relations: the join view | `### Mapping View` |
| `###` | Source Mapping | Map source object props to view | `### Source Mapping` |
| `###` | Target Mapping | Map view to target object props | `### Target Mapping` |
| `###` | Bound Object | Object this action operates on | `### Bound Object` |
| `###` | Trigger Condition | When to run (YAML condition) | `### Trigger Condition` |
| `###` | Pre-conditions | Data conditions required before action execution | `### Pre-conditions` |
| `###` | Tool Configuration | tool or MCP binding | `### Tool Configuration` |
| `###` | Parameter Binding | param name, source, binding | `### Parameter Binding` |
| `###` | Schedule | FIX_RATE or CRON | `### Schedule` |
| `###` | Scope of Impact | What objects are affected | `### Scope of Impact` |
| `###` | Object Types | Object types in a concept group | `### Object Types` |
| `###` | Control Scope | Risk control scope | `### Control Scope` |
| `###` | Control Policy | Risk control policy | `### Control Policy` |
| `###` | Pre-checks | Risk pre-checks | `### Pre-checks` |
| `###` | Rollback Plan | Risk rollback plan | `### Rollback Plan` |
| `###` | Audit Requirements | Risk audit requirements | `### Audit Requirements` |
| `###` | Execution Description | Detailed execution flow for action | `### Execution Description` |
| `####` | {property_name} | Individual logic property sub-section | `#### {name}` |

Canonical table column names: Name, Display Name, Type, Description, Mapped Field; ID, Name; Source, Target; Source Property, Target Property, View Property; Parameter, Type, Source, Binding, Description; Bound Object, Action Type; Object, Check, Condition, Message; Object, Impact Description; Expression. Parsers should also accept Chinese column names.

## File Format

### File Extensions

- `.bkn` - BKN definition file (schema)
- `.csv` - Instance data file (not part of BKN schema, standard CSV format)

### File Encoding

- UTF-8

### Basic Structure

Each BKN file consists of two parts:

1. **YAML Frontmatter**: File metadata
2. **Markdown Body**: Knowledge network definition content

```markdown
---
type: knowledge_network
id: example-network
name: Example Network
tags: [example]
---

# Example Network

Network description...

## Network Overview

...
```

---

## Frontmatter Specification

### File Types (type)

| type | Description | Purpose |
|------|-------------|---------|
| `knowledge_network` | Complete knowledge network | Top-level network container file |
| `object_type` | Single object type definition | Standalone object type file, can be imported directly |
| `relation_type` | Single relation type definition | Standalone relation type file, can be imported directly |
| `action_type` | Single action type definition | Standalone action type file, can be imported directly |
| `risk_type` | Single risk type definition | Standalone risk type file, can be imported directly |
| `concept_group` | Concept group | Organizes related object types together |

### Network File (type: knowledge_network)

```yaml
---
type: knowledge_network          # Complete knowledge network
id: string                       # Network ID, unique identifier
name: string                     # Network display name
tags: [string]                   # Optional, tag list
business_domain: string          # Optional, business domain
---
```

Description is placed in the body, after the `# {name}` heading.

### Object Type File (type: object_type)

```yaml
---
type: object_type                # Object type definition
id: string                       # Object ID, unique identifier
name: string                     # Object display name
tags: [string]                   # Optional, tag list
---
```

### Relation Type File (type: relation_type)

```yaml
---
type: relation_type              # Relation type definition
id: string                       # Relation ID, unique identifier
name: string                     # Relation display name
tags: [string]                   # Optional, tag list
---
```

### Action Type File (type: action_type)

```yaml
---
type: action_type                # Action type definition
id: string                       # Action ID, unique identifier
name: string                     # Action display name
tags: [string]                   # Optional, tag list
enabled: boolean                 # Optional, whether enabled (default false recommended)
risk_level: low | medium | high  # Optional, static risk level
requires_approval: boolean       # Optional, whether approval is required
---
```

### Risk Type File (type: risk_type)

```yaml
---
type: risk_type                  # Risk type definition
id: string                       # Risk type ID, unique identifier
name: string                     # Risk type display name
tags: [string]                   # Optional, tag list
---
```

### Concept Group File (type: concept_group)

```yaml
---
type: concept_group              # Concept group
id: string                       # Group ID, unique identifier
name: string                     # Group display name
tags: [string]                   # Optional, tag list
---
```

---

## Object Type Definition

### Syntax

```markdown
## ObjectType: {name}

{description}

### Data Properties

| Name | Display Name | Type | Description | Mapped Field |
|------|--------------|------|-------------|--------------|
| {prop} | {display_name} | {type} | {desc} | {mapped_field} |

### Keys

Primary Keys: {key_name}
Display Key: {key_name}
Incremental Key: {key_name}

### Logic Properties

#### {property_name}

- **Display**: {display_name}
- **Type**: metric | operator
- **Source**: {source_id} ({source_type})
- **Description**: {description}

| Parameter | Type | Source | Binding | Description |
|-----------|------|--------|---------|-------------|
| ... | string | property | {property_name} | Bound from object property |
| ... | array | input | - | Runtime user input |
| ... | string | const | {value} | Constant value |

### Data Source

| Type | ID | Name |
|------|-----|------|
| data_view | {view_id} | {view_name} |
```

- `Type`: Parameter data type, e.g., string, number, boolean, array
- `Source`: Value source — `property` (object property) / `input` (user input) / `const` (constant)
- `Binding`: Property name when Source is property, constant value when const, `-` when input

### Field Reference

| Field | Required | Description |
|-------|:--------:|-------------|
| {name} | YES | Object type display name |
| Data Properties | YES | Property definition table |
| Keys | YES | Primary key, display key declaration |
| Logic Properties | NO | Metric, operator, and other extended properties |
| Data Source | NO | Mapped data view; managed by platform if not set |

### Data Types

The `Type` column in Data Properties uses the following standard types. Type names are case-insensitive; the canonical forms below are recommended.

| Type | Description | JSON Mapping | SQL Mapping |
|------|-------------|--------------|-------------|
| string | String | string | VARCHAR / TEXT |
| integer | Integer | number | INT / BIGINT |
| float | Floating point number | number | FLOAT / DOUBLE |
| decimal | Exact decimal number | string / number | DECIMAL / NUMERIC |
| boolean | Boolean | boolean | BOOLEAN |
| date | Date (no time) | string (ISO 8601) | DATE |
| time | Time (no date) | string (ISO 8601) | TIME |
| datetime | Date and time | string (ISO 8601) | TIMESTAMP |
| text | Long text | string | TEXT / CLOB |
| json | JSON structured data | object / array | JSON / JSONB |
| binary | Binary data | string (base64) | BLOB / BYTEA |

---

## Relation Type Definition

### Syntax

```markdown
## RelationType: {name}

{description}

### Endpoint

| Source | Target | Type |
|--------|--------|------|
| {source_object_type_id} | {target_object_type_id} | direct or data_view |

### Mapping Rules

(When Type is direct)

| Source Property | Target Property |
|------------------|-----------------|
| {source_prop} | {target_prop} |

### Mapping View

(When Type is data_view)

| Type | ID |
|------|-----|
| data_view | {view_id} |

### Source Mapping

| Source Property | View Property |
|-----------------|----------------|
| {source_prop} | {view_prop} |

### Target Mapping

| View Property | Target Property |
|---------------|-----------------|
| {view_prop} | {target_prop} |
```

### Field Reference

| Field | Required | Description |
|-------|:--------:|-------------|
| {name} | YES | Relation type display name |
| Endpoint | YES | Relation endpoint definition (Source, Target, Type) |
| Source | YES | Source object type ID |
| Target | YES | Target object type ID |
| Type | YES | `direct` (direct mapping) or `data_view` (view mapping) |
| Mapping Rules | YES | Property mapping relationships |

### Relation Types

#### Direct Mapping (direct)

Establishes relationships through property value matching:

```markdown
## RelationType: Pod belongs to Node

The ownership relationship between a Pod instance and its Node.

### Endpoint

| Source | Target | Type |
|--------|--------|------|
| pod | node | direct |

### Mapping Rules

| Source Property | Target Property |
|------------------|-----------------|
| pod_node_name | node_name |
```

#### View Mapping (data_view)

Establishes relationships through an intermediate view:

```markdown
## RelationType: User likes Post

The like relationship between users and posts.

### Endpoint

| Source | Target | Type |
|--------|--------|------|
| user | post | data_view |

### Mapping View

| Type | ID |
|------|-----|
| data_view | user_post_likes_view |

### Source Mapping

| Source Property | View Property |
|-----------------|----------------|
| user_id | uid |

### Target Mapping

| View Property | Target Property |
|---------------|-----------------|
| pid | post_id |
```

---

## Action Type Definition

### Syntax

```markdown
## ActionType: {name}

{description}

### Bound Object

| Bound Object | Action Type |
|--------------|-------------|
| {object_type_id} | add or modify or delete or query |

### Trigger Condition

```yaml
condition:
  object_type_id: {object_type_id}
  field: {property_name}
  operation: == | != | > | < | >= | <= | in | not_in | exist | not_exist
  value: {value}
```

### Pre-conditions

(optional) Data pre-conditions before execution; blocks action if not met

| Object | Check | Condition | Message |
|--------|-------|-----------|---------|
| {object_type_id} | relation:{relation_id} | exist | Violation message |
| {object_type_id} | property:{property_name} | {op} {value} | Violation message |

### Scope of Impact

| Object | Impact Description |
|--------|--------------------|
| {object_type_id} | {impact description} |

### Tool Configuration

| Type | Toolbox ID | Tool ID |
|------|------------|---------|
| tool | {toolbox_id} | {tool_id} |

or

| Type | MCP ID | Tool Name |
|------|--------|-----------|
| mcp | {mcp_id} | {tool_name} |

### Parameter Binding

| Parameter | Type | Source | Binding | Description |
|-----------|------|--------|---------|-------------|
| {param_name} | {type} | property | {property_name} | {description} |
| {param_name} | {type} | input | - | {description} |
| {param_name} | {type} | const | {value} | {description} |

### Schedule

(optional)

| Type | Expression |
|------|------------|
| FIX_RATE | {interval} |
| CRON | {cron_expr} |

### Execution Description

(optional) Detailed execution flow...
```

### Field Reference

| Field | Required | Description |
|-------|:--------:|-------------|
| {name} | YES | Action type display name |
| Bound Object | YES | Target object type ID |
| Action Type | YES | `add` / `modify` / `delete` / `query` |
| Trigger Condition | NO | Automatic trigger condition |
| Pre-conditions | NO | Data pre-conditions before execution |
| Scope of Impact | NO | Impact scope declaration |
| Tool Configuration | YES | Tool or MCP to execute |
| Parameter Binding | YES | Parameter source configuration |
| Schedule | NO | Scheduled execution configuration |

### Trigger Condition Operators

The following operators apply to Trigger Condition and Pre-conditions:

| Operator | Description | Example |
|----------|-------------|---------|
| == | Equal to | `value: Running` |
| != | Not equal to | `value: Running` |
| > | Greater than | `value: 100` |
| < | Less than | `value: 100` |
| >= | Greater than or equal to | `value: 100` |
| <= | Less than or equal to | `value: 100` |
| in | Contained in | `value: [A, B, C]` |
| not_in | Not contained in | `value: [A, B, C]` |
| exist | Exists | (no value needed) |
| not_exist | Does not exist | (no value needed) |
| range | Within range | `value: [0, 100]` |

### Parameter Sources

| Source | Description |
|--------|-------------|
| property | From object property |
| input | Runtime user input |
| const | Constant value |

---

## Risk Type Definition

Risk types (RiskType) provide structured modeling of execution risk for action types and object types. Risk types are independent types, not sub-fields of action types; ActionType's `risk_level` declares "how dangerous", while RiskType declares "how to manage".

### Syntax

```markdown
## RiskType: {name}

{description}

### Control Scope

{Description of control scope}

### Control Policy

- {Policy description 1}
- {Policy description 2}

### Pre-checks

(optional)

| Object | Check | Condition | Message |
|--------|-------|-----------|---------|
| {object_type_id} | {check_type} | {condition} | {message} |

### Rollback Plan

1. {Rollback step 1}
2. {Rollback step 2}

### Audit Requirements

- {Audit requirement 1}
- {Audit requirement 2}
```

### Field Reference

| Field | Required | Description |
|-------|:--------:|-------------|
| {name} | YES | Risk type display name |
| Control Scope | YES | Control scope description |
| Control Policy | YES | Control policies (at least one) |
| Pre-checks | NO | Pre-execution check items |
| Rollback Plan | NO | Failure recovery strategy |
| Audit Requirements | NO | Audit logging and alerting configuration |

---

## Concept Group Definition

Concept groups (ConceptGroup) organize related object types together for better understanding and management.

### Syntax

```markdown
## ConceptGroup: {name}

{description}

### Object Types

| ID | Name | Description |
|----|------|-------------|
| {object_type_id} | {name} | {description} |
```

### Field Reference

| Field | Required | Description |
|-------|:--------:|-------------|
| {name} | YES | Group display name |
| Object Types | YES | List of included object types |

---

## Common Syntax Elements

### Table Format

Use standard Markdown tables:

```markdown
| Col1 | Col2 | Col3 |
|------|------|------|
| Val1 | Val2 | Val3 |
```

Center alignment (for boolean values):

```markdown
| Col1 | Col2 |
|------|:----:|
| Val1 | YES |
```

### YAML Code Blocks

Used for complex structures (e.g., condition expressions):

```markdown
```yaml
condition:
  operation: and
  sub_conditions:
    - field: status
      operation: ==
      value: Failed
    - field: retry_count
      operation: <
      value: 3
`` `
```

### Mermaid Diagrams

Used for visualizing relationships:

```markdown
```mermaid
graph LR
    A --> B
    B --> C
`` `
```

### Block Quotes

Used for highlighting key information:

```markdown
> **Note**: This object change requires an approval workflow
```

### Heading Levels

Heading levels are consistent across all file types:

- `#` - Network title (`# {Network Name}`)
- `##` - Type definition (`## ObjectType:` / `## RelationType:` / `## ActionType:` / `## RiskType:` / `## ConceptGroup:`) or network overview (`## Network Overview`)
- `###` - Sections within definitions (Data Properties, Keys, Endpoint, Mapping Rules, Trigger Condition, etc.)
- `####` - Sub-items (e.g., logic property names)

---

## File Organization

### Root File Discovery and Directory Loading

When a **directory** is passed as the network entry point (e.g., `validate network <dir>`, `load_network(dir)`), the SDK/CLI discovers the root file as follows:

1. `network.bkn`
2. If not found, report error "root file does not exist"

### Directory Structure

Each object/relation/action/risk is defined in its own file.

```
{business_dir}/
├── SKILL.md                     # agentskills.io standard entry point, contains network topology, index, usage guide
├── network.bkn                  # Network root file
├── CHECKSUM                     # Optional, directory-level consistency check (generated by SDK generate_checksum_file)
├── object_types/
│   ├── material.bkn             # type: object_type
│   └── inventory.bkn            # type: object_type
├── relation_types/
│   └── material_to_inventory.bkn # type: relation_type
├── action_types/
│   ├── check_inventory.bkn      # type: action_type
│   └── adjust_inventory.bkn     # type: action_type
├── risk_types/
│   └── inventory_adjustment_risk.bkn  # type: risk_type
├── concept_groups/
│   └── supply_chain.bkn         # type: concept_group
├── metrics/                     # Optional network-level metrics; omitting is not an error and is not a breaking change for legacy CHECKSUM layouts
│   └── example_count.bkn        # type: metric
└── data/                        # Optional, .csv instance data
    └── scenario.csv
```

- **`metrics/` is optional**: Networks without this subdirectory or without metric files in `CHECKSUM` remain valid; metrics are not required to define a knowledge network.
- **Files with `type: metric`** (`metrics/*.bkn`): besides `type`, `id`, `name`, and `tags`, the spec **reserves `metric_type`** in YAML frontmatter (`atomic` | `derived` | `composite`), aligned with the platform Metric DTO. It **must match** the root-level `kind` inside the `### Calculation Formula` fenced block; **`kind` is authoritative**. See `docs/DESIGN_BKN_METRIC.md`. Optional: `unit_type`, `unit`, etc.

### Data Files (CSV)

Instance data uses standard CSV format, not part of the BKN schema definition, and does not contain YAML frontmatter.

- File extension: `.csv`
- Encoding: UTF-8 (BOM recommended for Excel compatibility)
- Column names should match the `Name` column of the target object_type's Data Properties
- Each CSV file should contain data for only one object type, for easier versioning and auditing
- CSV files are placed in the `data/` directory

### SKILL.md and BKN Compatibility

`SKILL.md` is the Agent Skill entry file defined by agentskills.io, used complementarily with BKN's directory organization:

- **SKILL.md manages responsibilities**: Describes the Skill's capabilities, script entry points, workflows, templates, and output rules for AI Agent interpretation.
- **network.bkn manages structure**: Declares network metadata via frontmatter `type: knowledge_network`; SDK/CLI automatically discovers BKN files in the same directory.
- **Not interchangeable**: SKILL.md is not a BKN root file. SDK/CLI's `load_network` and `validate network` read `network.bkn`, not `SKILL.md`.
- **Co-existence recommended**: Place both `SKILL.md` (Agent entry) and `network.bkn` (SDK/CLI entry) in the directory, each serving its own purpose.
- **Checksum inclusion**: `SKILL.md` is included in `checksum generate` hash computation (normalized full text hash), ensuring Skill description changes are auditable.
- **Directory validation compatibility**: `validate network <dir>` and `load_network(dir)` work normally in Skill directories — automatically discovering `network.bkn`. SKILL.md does not affect network loading.

**Object Type File Example** (`pod.bkn`):

```markdown
---
type: object_type
id: pod
name: Pod Instance
tags: [topology, container, Kubernetes]
---

## ObjectType: Pod Instance

The smallest deployable unit in Kubernetes, a collection of one or more containers.

### Data Properties

| Name | Display Name | Type | Description | Mapped Field |
|------|--------------|------|-------------|--------------|
| id | ID | integer | Primary key ID | id |
| pod_name | Pod Name | string | Pod name | pod_name |
| pod_status | Pod Status | string | Pod status (Running/Pending/Failed) | pod_status |
| pod_node_name | Node | string | Node name where Pod resides | pod_node_name |
| pod_namespace | Namespace | string | Pod namespace | pod_namespace |
| pod_ip | Pod IP | string | Pod IP address | pod_ip |
| pod_created_at | Created At | datetime | Pod creation time | pod_created_at |

### Keys

Primary Keys: id
Display Key: pod_name
Incremental Key:

### Logic Properties


### Data Source

| Type | ID | Name |
|------|-----|------|
| data_view | d2mio43q6gt6p380dis0 | pod_info_view |
```

---

## Incremental Import Specification

BKN supports dynamically importing any `.bkn` file into an existing knowledge network.

### Importer Capability Requirements

It is recommended to implement a **BKN Importer** that converts BKN files into system changes, providing the following capabilities (all required):

| Capability | Description | Purpose |
|------------|-------------|---------|
| `validate` | Structure/table/YAML block validation, referential integrity check, parameter binding validation | Prevent errors from entering the system |
| `diff` | Compute change set (add/update/delete) and impact scope | Make changes explainable and auditable |
| `dry_run` | Execute validate + diff without persisting | Pre-deployment rehearsal |
| `apply` | Persist changes (with deterministic semantics and conflict strategy) | Controlled execution |
| `export` | Export live knowledge network state as BKN (round-trip capable) | Prevent drift, enable rollback and reproducibility |

> Requirement: All import operations must record audit information (operator, timestamp, input file fingerprint, change set, result).

### Import Determinism (Must Be Guaranteed)

To ensure multi-user collaboration and replayability, import semantics must be **deterministic**:

- Same set of input files (regardless of filesystem order) produce the same result
- Repeated import of the same file produces the same result (idempotent)
- Conflicts are explainable: either fail-fast explicitly, or follow clear rules (e.g., last-wins); no "implicit merging"

### Unique Key and Scope

The suggested unique key for each definition:

- `key = (network_id, type, id)`

Where `network_id` is determined by the import target network (import command parameter or the network root file's `type: knowledge_network` and `id`).

### Update Semantics (replace vs merge)

Default recommendation is **replace (whole-section overwrite)**:

- When a `key` already exists, the definition in the import file entirely replaces the old definition
- **Missing fields do not mean deletion**: They only mean "this field is not in the current definition"; deleting elements should be done via SDK/CLI's explicit delete API, not through BKN files

If needed, controlled **merge-by-section** can be supported, but must satisfy:

- Only allow merging for a few "additive sections" (e.g., `property overrides`, `logic properties`)
- Conflicts must be controllable: same-name logic properties/field configurations should fail-fast or last-wins (configurable)
- Merge strategy must be explicitly configured in the importer and recorded in the import audit log

### Conflict and Priority

When the same `key` is declared by multiple files in a single import batch:

- Default: **fail-fast** (recommended, ensures stability)
- Optional: Sort by explicit priority (e.g., command-line order or `priority` field), otherwise not recommended

### Import Behavior

| Scenario | Behavior |
|----------|----------|
| ID does not exist | Create new definition |
| ID already exists | Update definition (overwrite) |
| Delete element | Execute explicitly via SDK/CLI delete API, not through BKN files |

### Import Examples

**Scenario: Adding a new object type to an existing network**

Create `deployment.bkn`:

```markdown
---
type: object_type
id: deployment
name: Deployment
tags: [k8s]
---

## ObjectType: Deployment

Kubernetes deployment controller.

### Data Properties

| Name | Display Name | Type | Description | Mapped Field |
|------|--------------|------|-------------|--------------|
| id | ID | integer | Unique identifier | id |
| deployment_name | Deployment Name | string | Deployment name | deployment_name |

### Keys

Primary Keys: id
Display Key: deployment_name
Incremental Key:

### Logic Properties


### Data Source

| Type | ID | Name |
|------|-----|------|
| data_view | deployment_view | Deployment View |
```

After import, the network will contain the new `deployment` object type.

**Scenario: Updating an existing object type**

Create a file with the same ID; import will automatically overwrite:

```markdown
---
type: object_type
id: pod
name: Pod Instance (Updated)
tags: [topology, container, Kubernetes]
---

## ObjectType: Pod Instance (Updated)

Updated definition...
```

---

## No-Patch Update Model

BKN uses a **no-patch update model**: definition files are used only for adding and modifying; deletion is performed explicitly via SDK/CLI API.

### Definition File Import (add/modify)

- When importing a single `.bkn` file, **upsert** (create or overwrite) is performed by `(network, type, id)`
- Modify: Edit the corresponding definition file and re-import to overwrite
- Missing fields do not mean deletion: They only mean "this field is not in the current definition"

### Deleting Elements

- Deletion should be performed explicitly via **SDK/CLI's delete API**, not through BKN files
- Delete operations require: explicit parameters, auditability, support for dry-run and batch deletion

### Editing Workflow

1. **Add**: Create a `.bkn` file, import
2. **Modify**: Edit the `.bkn` file, re-import
3. **Delete**: Call SDK/CLI's delete interface

---

## Best Practices

### Naming Conventions

- **ID**: Lowercase letters, numbers, underscores, e.g., `pod_belongs_node`
- **Display Name**: Concise and clear, e.g., "Pod belongs to Node"
- **Tags**: Use a unified tagging system

### Document Structure

1. Place network description at the beginning of the file
2. Use mermaid diagrams to show overall topology
3. Object definitions first, then relations and actions
4. Keep related definitions together

### Business Rule Placement

Business rules should be placed according to their scope. Do not add extra information beyond the standard BKN structure:

1. **Network-level rules** — Write in the description area of `network.bkn` (free text after the `# {name}` heading), for top-level business constraints of the entire knowledge network
2. **Type-level rules** — Write in the body description of the corresponding type file (`object_type.bkn`, `relation_type.bkn`, `action_type.bkn`) — the free text between the `## ObjectType: {name}` heading and the first `###` section. Do not put business rules in frontmatter
3. **Property-level rules** — Write directly in the `Description` column of the Data Properties table

> **Note**: BKN files have strict format constraints (frontmatter + standard sections). Content outside the specification may not be preserved during SDK parsing and platform import. Place business rules in the three levels above; do not add custom sections or non-standard structures.

### Simplicity Principle

- Avoid duplicate information
- Each definition file should have a single responsibility

### Readability

- Use tables for structured data
- Add business semantic descriptions
- Use mermaid diagrams when necessary

---

## References

- [Architecture](./ARCHITECTURE.md)
- Examples:
  - [K8s Network](../examples/k8s-network/) - Kubernetes topology knowledge network
  - [Supply Chain Network](../examples/supplychain-hd/) - Supply chain business knowledge network
