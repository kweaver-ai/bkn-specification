# BKN 语言规范

版本: 2.0.1

## 概述

BKN (Business Knowledge Network) 是一种基于 Markdown 的声明式建模语言，用于定义业务知识网络中的对象、关系和行动。BKN 只负责描述模型结构与语义，不包含执行逻辑——校验引擎、数据管道、工作流等运行时能力由消费 BKN 模型的平台实现。

本文档定义了 BKN 的完整语法规范。

### 术语表（Glossary）

**核心概念**

| 术语 | 含义 |
|------|------|
| BKN | Business Knowledge Network，业务知识网络 |
| knowledge_network | 一个业务知识网络的整体集合 |
| object_type | 业务对象类型（例如 Pod/Node/Service） |
| relation_type | 连接两个 object_type 的关系类型（例如 belongs_to/routes_to） |
| action_type | 对 object_type 执行的操作定义（可绑定 tool 或 mcp） |
| risk_type | 风险类，对行动类和对象类的执行风险进行结构化建模 |
| concept_group | 概念分组，用于将相关对象类型组织在一起 |

**对象结构**

| 术语 | 含义 |
|------|------|
| data_view | 数据视图，对象/关系可直接映射的数据来源 |
| data_properties | 对象的属性定义表，声明字段名称、类型、描述 |
| keys | 键定义，声明主键、展示键、增量键 |
| logic_properties | 逻辑属性，基于其他数据源的派生字段（metric / operator） |
| primary_key | 主键字段，用于唯一定位实例（Keys 小节中声明） |
| display_key | 展示字段，用于 UI 显示和检索（Keys 小节中声明） |
| metric | 逻辑属性类型：指标，从外部数据源获取的度量值 |
| operator | 逻辑属性类型：算子，基于输入参数的计算逻辑 |

**行动结构**

| 术语 | 含义 |
|------|------|
| trigger_condition | 触发条件，定义 action 自动执行的条件 |
| pre-conditions | 前置条件，执行前必须满足的数据检查（不满足则阻止执行） |
| tool | 行动绑定的外部工具 |
| mcp | Model Context Protocol，行动绑定的 MCP 工具 |
| schedule | 定时配置（FIX_RATE 或 CRON），用于周期性执行 |
| scope_of_impact | 影响范围，声明行动影响的对象 |

**文件组织**

| 术语 | 含义 |
|------|------|
| frontmatter | YAML 元数据区（`---` 包裹），每个 .bkn 文件的头部 |
| knowledge_network | 文件类型 `type: knowledge_network`，完整知识网络的顶层容器 |

### 标准原语表 (Primitives)

Section 标题和表格列名的规范形式，建议使用英文。解析器应同时支持英文与中文以便兼容。

下表按 **统一标题层级** 组织，适用于所有 BKN 文件类型（knowledge_network / object_type / relation_type / action_type / risk_type / concept_group）。

| Level | English (canonical) | Definition | 中文 | Syntax |
|:-----:|---------------------|------------|------|--------|
| `#` | {Network Name} | Network title | 网络标题 | `# {name}` |
| `##` | Network Overview | Network topology overview | 网络概览 | `## Network Overview` |
| `##` | ObjectType | Individual object type definition | 对象类型 | `## ObjectType: {name}` |
| `##` | RelationType | Individual relation type definition | 关系类型 | `## RelationType: {name}` |
| `##` | ActionType | Individual action type definition | 行动类型 | `## ActionType: {name}` |
| `##` | RiskType | Individual risk type definition | 风险类型 | `## RiskType: {name}` |
| `##` | ConceptGroup | Concept group definition | 概念分组 | `## ConceptGroup: {name}` |
| `###` | Data Source | The data view this object maps from | 数据来源 | `### Data Source` |
| `###` | Data Properties | Explicit list of fields (name, type, description) | 数据属性 | `### Data Properties` |
| `###` | Keys | Primary key, display key, incremental key | 键定义 | `### Keys` |
| `###` | Logic Properties | Derived fields: metric, operator | 逻辑属性 | `### Logic Properties` |
| `###` | Endpoint | Relation endpoint: source, target, type | 关联定义 | `### Endpoint` |
| `###` | Mapping Rules | How source/target properties map | 映射规则 | `### Mapping Rules` |
| `###` | Mapping View | For data_view relations: the join view | 映射视图 | `### Mapping View` |
| `###` | Source Mapping | Map source object props to view | 起点映射 | `### Source Mapping` |
| `###` | Target Mapping | Map view to target object props | 终点映射 | `### Target Mapping` |
| `###` | Bound Object | Object this action operates on | 绑定对象 | `### Bound Object` |
| `###` | Trigger Condition | When to run (YAML condition) | 触发条件 | `### Trigger Condition` |
| `###` | Pre-conditions | Data conditions required before action execution | 前置条件 | `### Pre-conditions` |
| `###` | Tool Configuration | tool or MCP binding | 工具配置 | `### Tool Configuration` |
| `###` | Parameter Binding | param name, source, binding | 参数绑定 | `### Parameter Binding` |
| `###` | Schedule | FIX_RATE or CRON | 调度配置 | `### Schedule` |
| `###` | Scope of Impact | What objects are affected | 影响范围 | `### Scope of Impact` |
| `###` | Object Types | Object types in a concept group | 对象类型列表 | `### Object Types` |
| `###` | Control Scope | Risk control scope | 管控范围 | `### Control Scope` |
| `###` | Control Policy | Risk control policy | 管控策略 | `### Control Policy` |
| `###` | Pre-checks | Risk pre-checks | 前置检查 | `### Pre-checks` |
| `###` | Rollback Plan | Risk rollback plan | 回滚方案 | `### Rollback Plan` |
| `###` | Audit Requirements | Risk audit requirements | 审计要求 | `### Audit Requirements` |
| `###` | Execution Description | Detailed execution flow for action | 执行说明 | `### Execution Description` |
| `####` | {property_name} | Individual logic property sub-section | — | `#### {name}` |

表格列名（canonical）：Name, Display Name, Type, Description, Mapped Field; ID, Name; Source, Target; Source Property, Target Property, View Property; Parameter, Type, Source, Binding, Description; Bound Object, Action Type; Object, Check, Condition, Message; Object, Impact Description; Expression。解析器同时接受中文列名。

## 文件格式

### 文件扩展名

- `.bkn` - BKN 定义文件（schema）
- `.csv` - 实例数据文件（不属于 BKN schema，标准 CSV 格式）

### 文件编码

- UTF-8

### 基本结构

每个 BKN 文件由两部分组成：

1. **YAML Frontmatter**: 文件元数据
2. **Markdown Body**: 知识网络定义内容

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

## Frontmatter 规范

### 文件类型 (type)

| type | 说明 | 用途 |
|------|------|------|
| `knowledge_network` | 完整知识网络 | 网络顶层容器文件 |
| `object_type` | 单个对象类型定义 | 独立的对象类型文件，可直接导入 |
| `relation_type` | 单个关系类型定义 | 独立的关系类型文件，可直接导入 |
| `action_type` | 单个行动类型定义 | 独立的行动类型文件，可直接导入 |
| `risk_type` | 单个风险类型定义 | 独立的风险类文件，可直接导入 |
| `concept_group` | 概念分组 | 将相关对象类型组织在一起 |

### 网络文件 (type: knowledge_network)

```yaml
---
type: knowledge_network          # 完整知识网络
id: string                       # 网络ID，唯一标识
name: string                     # 网络显示名称
tags: [string]                   # 可选，标签列表
business_domain: string          # 可选，业务领域
---
```

描述放在 body 中，`# {name}` 标题之后。

### 对象类型文件 (type: object_type)

```yaml
---
type: object_type                # 对象类型定义
id: string                       # 对象ID，唯一标识
name: string                     # 对象显示名称
tags: [string]                   # 可选，标签列表
---
```

### 关系类型文件 (type: relation_type)

```yaml
---
type: relation_type              # 关系类型定义
id: string                       # 关系ID，唯一标识
name: string                     # 关系显示名称
tags: [string]                   # 可选，标签列表
---
```

### 行动类型文件 (type: action_type)

```yaml
---
type: action_type                # 行动类型定义
id: string                       # 行动ID，唯一标识
name: string                     # 行动显示名称
tags: [string]                   # 可选，标签列表
enabled: boolean                 # 可选，是否启用（建议默认 false）
risk_level: low | medium | high  # 可选，静态风险等级
requires_approval: boolean       # 可选，是否需要审批
---
```

### 风险类型文件 (type: risk_type)

```yaml
---
type: risk_type                  # 风险类型定义
id: string                       # 风险类ID，唯一标识
name: string                     # 风险类显示名称
tags: [string]                   # 可选，标签列表
---
```

### 概念分组文件 (type: concept_group)

```yaml
---
type: concept_group              # 概念分组
id: string                       # 分组ID，唯一标识
name: string                     # 分组显示名称
tags: [string]                   # 可选，标签列表
---
```

---

## 对象类型定义规范

### 语法

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
| ... | string | property | {property_name} | 从对象属性绑定 |
| ... | array | input | - | 运行时用户输入 |
| ... | string | const | {value} | 常量值 |

### Data Source

| Type | ID | Name |
|------|-----|------|
| data_view | {view_id} | {view_name} |
```

- `Type`：参数数据类型，如 string、number、boolean、array
- `Source`：值来源，`property`（对象属性）/ `input`（用户输入）/ `const`（常量）
- `Binding`：当 Source 为 property 时为属性名，为 const 时为常量值，为 input 时为 `-`

### 字段说明

| 字段 | 必须 | 说明 |
|------|:----:|------|
| {name} | YES | 对象类型显示名称 |
| Data Properties | YES | 属性定义表 |
| Keys | YES | 主键、展示键声明 |
| Logic Properties | NO | 指标、算子等扩展属性 |
| Data Source | NO | 映射的数据视图，未设定时由平台自动管理 |

### 数据类型

Data Properties 表的 `Type` 列使用以下标准类型。类型名称大小写不敏感，推荐使用下表中的规范形式。

| 类型 | 说明 | JSON 对应 | SQL 对应 |
|------|------|-----------|----------|
| string | 字符串 | string | VARCHAR / TEXT |
| integer | 整数 | number | INT / BIGINT |
| float | 浮点数 | number | FLOAT / DOUBLE |
| decimal | 精确十进制数 | string / number | DECIMAL / NUMERIC |
| boolean | 布尔值 | boolean | BOOLEAN |
| date | 日期（无时间） | string (ISO 8601) | DATE |
| time | 时间（无日期） | string (ISO 8601) | TIME |
| datetime | 日期时间 | string (ISO 8601) | TIMESTAMP |
| text | 长文本 | string | TEXT / CLOB |
| json | JSON 结构数据 | object / array | JSON / JSONB |
| binary | 二进制数据 | string (base64) | BLOB / BYTEA |

---

## 关系类型定义规范

### 语法

```markdown
## RelationType: {name}

{description}

### Endpoint

| Source | Target | Type |
|--------|--------|------|
| {source_object_type_id} | {target_object_type_id} | direct 或 data_view |

### Mapping Rules

（当 Type 为 direct 时）

| Source Property | Target Property |
|------------------|-----------------|
| {source_prop} | {target_prop} |

### Mapping View

（当 Type 为 data_view 时）

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

### 字段说明

| 字段 | 必须 | 说明 |
|------|:----:|------|
| {name} | YES | 关系类型显示名称 |
| Endpoint | YES | 关系端点定义（Source、Target、Type） |
| Source | YES | 起点对象类型 ID |
| Target | YES | 终点对象类型 ID |
| Type | YES | `direct` (直接映射) 或 `data_view` (视图映射) |
| Mapping Rules | YES | 属性映射关系 |

### 关系类型

#### 直接映射 (direct)

通过属性值匹配建立关联：

```markdown
## RelationType: Pod属于Node

Pod 实例与其所属 Node 的归属关系。

### Endpoint

| Source | Target | Type |
|--------|--------|------|
| pod | node | direct |

### Mapping Rules

| Source Property | Target Property |
|------------------|-----------------|
| pod_node_name | node_name |
```

#### 视图映射 (data_view)

通过中间视图建立关联：

```markdown
## RelationType: 用户点赞帖子

用户与帖子之间的点赞关系。

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

## 行动类型定义规范

### 语法

```markdown
## ActionType: {name}

{description}

### Bound Object

| Bound Object | Action Type |
|--------------|-------------|
| {object_type_id} | add 或 modify 或 delete 或 query |

### Affect Object

(optional) 影响的对象类型 ID，用于声明行动对哪些对象有影响。

| Affect Object |
|---------------|
| {affect_type_id} |

### Trigger Condition

```yaml
condition:
  object_type_id: {object_type_id}
  field: {property_name}
  operation: == | != | > | < | >= | <= | in | not_in | exist | not_exist
  value: {value}
```

### Pre-conditions

(optional) 执行前的数据前置条件，不满足则阻止行动执行

| Object | Check | Condition | Message |
|--------|-------|-----------|---------|
| {object_type_id} | relation:{relation_id} | exist | 违反时的说明 |
| {object_type_id} | property:{property_name} | {op} {value} | 违反时的说明 |

### Scope of Impact

| Object | Impact Description |
|--------|--------------------|
| {object_type_id} | {影响说明} |

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
| {param_name} | {type} | property | {property_name} | {说明} |
| {param_name} | {type} | input | - | {说明} |
| {param_name} | {type} | const | {value} | {说明} |

### Schedule

(optional)

| Type | Expression |
|------|------------|
| FIX_RATE | {interval} |
| CRON | {cron_expr} |

### Execution Description

(optional) Detailed execution flow...
```

### 字段说明

| 字段 | 必须 | 说明 |
|------|:----:|------|
| {name} | YES | 行动类型显示名称 |
| Bound Object | YES | 目标对象类型 ID |
| Action Type | YES | `add` / `modify` / `delete` / `query` |
| Trigger Condition | NO | 自动触发的条件 |
| Pre-conditions | NO | 执行前的数据前置条件 |
| Scope of Impact | NO | 影响范围声明 |
| Tool Configuration | YES | 执行的工具或 MCP |
| Parameter Binding | YES | 参数来源配置 |
| Schedule | NO | 定时执行配置 |

### 触发条件操作符

以下操作符适用于 Trigger Condition 和 Pre-conditions：

| 操作符 | 说明 | 示例 |
|--------|------|------|
| == | 等于 | `value: Running` |
| != | 不等于 | `value: Running` |
| > | 大于 | `value: 100` |
| < | 小于 | `value: 100` |
| >= | 大于等于 | `value: 100` |
| <= | 小于等于 | `value: 100` |
| in | 包含于 | `value: [A, B, C]` |
| not_in | 不包含于 | `value: [A, B, C]` |
| exist | 存在 | (无需 value) |
| not_exist | 不存在 | (无需 value) |
| range | 范围内 | `value: [0, 100]` |

### 参数来源

| 来源 | 说明 |
|------|------|
| property | 从对象属性获取 |
| input | 运行时用户输入 |
| const | 常量值 |

---

## 风险类型定义规范

风险类型（RiskType）用于对行动类型和对象类型的执行风险进行结构化建模。风险类型是独立类型，不是行动类型的附属字段；ActionType 的 `risk_level` 声明「多危险」，RiskType 声明「如何管控」。

### 语法

```markdown
## RiskType: {name}

{description}

### Control Scope

{管控范围的描述文字}

### Control Policy

- {策略描述1}
- {策略描述2}

### Pre-checks

(optional)

| Object | Check | Condition | Message |
|--------|-------|-----------|---------|
| {object_type_id} | {check_type} | {condition} | {message} |

### Rollback Plan

1. {回滚步骤1}
2. {回滚步骤2}

### Audit Requirements

- {审计要求1}
- {审计要求2}
```

### 字段说明

| 字段 | 必须 | 说明 |
|------|:----:|------|
| {name} | YES | 风险类型显示名称 |
| Control Scope | YES | 管控范围描述 |
| Control Policy | YES | 管控策略（至少一条） |
| Pre-checks | NO | 执行前检查项列表 |
| Rollback Plan | NO | 失败恢复策略 |
| Audit Requirements | NO | 审计日志与告警配置 |

---

## 概念分组定义规范

概念分组（ConceptGroup）用于将相关的对象类型组织在一起，便于理解和管理。

### 语法

```markdown
## ConceptGroup: {name}

{description}

### Object Types

| ID | Name | Description |
|----|------|-------------|
| {object_type_id} | {name} | {description} |
```

### 字段说明

| 字段 | 必须 | 说明 |
|------|:----:|------|
| {name} | YES | 分组显示名称 |
| Object Types | YES | 包含的对象类型列表 |

---

## 通用语法元素

### 表格格式

使用标准 Markdown 表格：

```markdown
| 列1 | 列2 | 列3 |
|-----|-----|-----|
| 值1 | 值2 | 值3 |
```

居中对齐（用于布尔值）：

```markdown
| 列1 | 列2 |
|-----|:---:|
| 值1 | YES |
```

### YAML 代码块

用于复杂结构（如条件表达式）：

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

### Mermaid 图表

用于可视化关系：

```markdown
```mermaid
graph LR
    A --> B
    B --> C
`` `
```

### 引用块

用于关键信息高亮：

```markdown
> **注意**: 该对象变更需要审批流程
```

### 标题层级

标题层级在所有文件类型中保持一致：

- `#` - 网络标题（`# {Network Name}`）
- `##` - 类型定义（`## ObjectType:` / `## RelationType:` / `## ActionType:` / `## RiskType:` / `## ConceptGroup:`）或网络概览（`## Network Overview`）
- `###` - 定义内 section（Data Properties, Keys, Endpoint, Mapping Rules, Trigger Condition 等）
- `####` - 子项（例如逻辑属性名）

---

## 文件组织

### 根文件发现与目录加载

当传入**目录**作为网络入口时（如 `validate network <dir>`、`load_network(dir)`），SDK/CLI 按以下顺序自动发现根文件：

1. `network.bkn`
2. 若不存在，报错「根文件不存在」

### 目录结构

每个对象/关系/行动/风险独立一个文件。

```
{business_dir}/
├── SKILL.md                     # agentskills.io 标准入口，含网络拓扑、索引、使用指南
├── network.bkn                  # 网络根文件
├── CHECKSUM                     # 可选，目录级一致性校验（SDK generate_checksum_file 生成）
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
├── metrics/                     # 可选，网络级指标；缺省不视为错误，亦非对旧 CHECKSUM 的破坏性变更
│   └── example_count.bkn        # type: metric
└── data/                        # 可选，.csv 实例数据
    └── scenario.csv
```

- **`metrics/` 可选**：未包含该子目录或未将其中文件纳入 `CHECKSUM` 的历史网络包仍有效；指标非定义知识网络的必要条件。
- **`type: metric` 文件**（`metrics/*.bkn`）：YAML frontmatter 除 `type`、`id`、`name`、`tags` 外，**规范保留 `metric_type`**（`atomic` \| `derived` \| `composite`），与平台 Metric DTO 对齐；**须与正文 `### Calculation Formula` 代码块根级 `kind` 一致**，权威来源为 `kind`，详见 `docs/DESIGN_BKN_METRIC.md`。另可选用 `unit_type`、`unit` 等。

### 数据文件（CSV）

实例数据使用标准 CSV 格式，不属于 BKN schema 定义，不含 YAML frontmatter。

- 文件扩展名：`.csv`
- 编码：UTF-8（建议带 BOM 以兼容 Excel）
- 列名应与目标 object_type 的 Data Properties `Name` 列一致
- 每个 CSV 文件建议只包含一个对象类型的数据，便于版本化和审计
- CSV 文件放置在 `data/` 目录下

### SKILL.md 与 BKN 兼容性

`SKILL.md` 是 agentskills.io 定义的 Agent Skill 入口文件，与 BKN 的目录组织互补使用：

- **SKILL.md 管职责**：描述 Skill 的能力、脚本入口、工作流、模板和输出规则，供 AI Agent 解读。
- **network.bkn 管结构**：通过 frontmatter `type: knowledge_network` 声明网络元数据，SDK/CLI 自动发现同目录下的 BKN 文件。
- **互不替代**：SKILL.md 不是 BKN 根文件，SDK/CLI 的 `load_network` 和 `validate network` 读取的是 `network.bkn`，而非 `SKILL.md`。
- **共存推荐**：在目录中同时放置 `SKILL.md`（Agent 入口）和 `network.bkn`（SDK/CLI 入口），两者各司其职。
- **checksum 纳入**：`SKILL.md` 被 `checksum generate` 纳入校验和计算（按 `SKILL.md` 全文 normalize 后哈希），确保 Skill 描述变更可被审计追踪。
- **目录校验兼容**：`validate network <dir>` 和 `load_network(dir)` 在 Skill 目录下正常工作——自动发现 `network.bkn`，SKILL.md 不影响网络加载。

**对象类型文件示例** (`pod.bkn`):

```markdown
---
type: object_type
id: pod
name: Pod实例
tags: [拓扑架构, 容器, Kubernetes]
---

## ObjectType: Pod实例

Kubernetes 中的最小部署单元，一个或多个容器的集合。

### Data Properties

| Name | Display Name | Type | Description | Mapped Field |
|------|--------------|------|-------------|--------------|
| id | ID | integer | 主键ID | id |
| pod_name | Pod名称 | string | Pod名称 | pod_name |
| pod_status | Pod状态 | string | Pod状态 (Running/Pending/Failed) | pod_status |
| pod_node_name | 所在节点 | string | Pod所在节点名称 | pod_node_name |
| pod_namespace | 命名空间 | string | Pod所属命名空间 | pod_namespace |
| pod_ip | Pod IP | string | Pod IP地址 | pod_ip |
| pod_created_at | 创建时间 | datetime | Pod创建时间 | pod_created_at |

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

## 增量导入规范

BKN 支持将任何 `.bkn` 文件动态导入到已有的知识网络。

### 导入器能力要求（工程可控性 9+ 的前提）

建议实现一个 **BKN Importer**，将 BKN 文件转换为系统变更，并提供以下能力（缺一不可）：

| 能力 | 说明 | 目的 |
|------|------|------|
| `validate` | 结构/表格/YAML block 校验，引用完整性校验，参数绑定校验 | 阻止错误进入系统 |
| `diff` | 计算变更集（新增/更新/删除）与影响范围 | 让变更可解释、可审计 |
| `dry_run` | 在不落地的情况下执行 validate + diff | 上线前预演 |
| `apply` | 执行落地（按确定性语义与冲突策略） | 可控执行 |
| `export` | 将线上知识网络状态导出为 BKN（可 round-trip） | 防漂移、可回滚、可复现 |

> 要求：所有导入操作必须记录审计信息（操作者、时间、输入文件指纹、变更集、结果）。

### 导入的确定性（必须保证）

为保证多人协作与可回放性，导入语义必须是**确定性的（deterministic）**：

- 对同一组输入文件（不考虑文件系统顺序）导入结果一致
- 同一文件重复导入结果一致（幂等）
- 冲突可解释：要么明确失败（fail-fast），要么有明确规则（例如 last-wins），不得“隐式合并”

### 唯一键与作用域

每个定义的唯一键建议为：

- `key = (network_id, type, id)`

其中 `network_id` 由导入目标网络（导入命令参数或 `type: knowledge_network` 的 `id`）确定。

### 更新语义（replace vs merge）

默认建议使用 **replace（整段覆盖）**：

- 当 `key` 已存在时，用导入文件中的定义整体替换旧定义
- **缺失字段不代表删除**：仅代表“该字段不在本次定义中”；删除元素应通过 SDK/CLI 的显式删除 API 执行，而非 BKN 文件

如确有需要，可支持受控的 **merge-by-section（按章节合并）**，但必须满足：

- 仅允许合并少数“附加型章节”（例如 `属性覆盖`、`逻辑属性`）
- 冲突必须可控：同名逻辑属性/同名字段配置冲突时 fail-fast 或 last-wins（需配置）
- 合并策略必须在导入器中显式配置并记录到导入审计日志

### 冲突与优先级

当同一个 `key` 在一次导入批次中被多个文件重复声明：

- 默认：**fail-fast**（推荐，保证稳定性）
- 可选：按显式优先级排序（例如命令行顺序或 `priority` 字段），否则不建议支持

### 导入行为

| 场景 | 行为 |
|------|------|
| ID 不存在 | 创建新定义 |
| ID 已存在 | 更新定义（覆盖） |
| 删除元素 | 通过 SDK/CLI 的 delete API 显式执行，不通过 BKN 文件 |

### 导入示例

**场景：向已有网络添加新对象类型**

创建 `deployment.bkn`:

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
| id | ID | integer | 唯一标识 | id |
| deployment_name | Deployment名称 | string | Deployment 名称 | deployment_name |

### Logic Properties


### Keys

Primary Keys: id
Display Key: deployment_name
Incremental Key:

### Data Source

| Type | ID | Name |
|------|-----|------|
| data_view | deployment_view | Deployment视图 |
```

导入后，网络将包含新的 `deployment` 对象类型。

**场景：更新已有对象类型**

创建同 ID 的文件，导入后自动覆盖：

```markdown
---
type: object_type
id: pod
name: Pod实例（更新版）
tags: [拓扑架构, 容器, Kubernetes]
---

## ObjectType: Pod实例（更新版）

更新后的定义...
```

---

## 无 patch 更新模型

BKN 采用**无 patch 的更新模型**：定义文件仅用于新增与修改，删除通过 SDK/CLI API 显式执行。

### 定义文件导入（add/modify）

- 单个 `.bkn` 文件导入时，按 `(network, type, id)` 执行 **upsert**（新增或覆盖）
- 修改：直接编辑对应定义文件，重新导入即可覆盖
- 缺失字段不代表删除：仅表示该字段不在本次定义中

### 删除元素

- 删除应通过 **SDK/CLI 的 delete API** 显式执行，不通过 BKN 文件
- 删除操作要求：显式参数、可审计、支持 dry-run 与批量删除

### 编辑流程

1. **新增**：创建 `.bkn` 文件，导入
2. **修改**：编辑 `.bkn` 文件，重新导入
3. **删除**：调用 SDK/CLI 的 delete 接口

---

## 最佳实践

### 命名规范

- **ID**: 小写字母、数字、下划线，如 `pod_belongs_node`
- **显示名称**: 简洁明确，如 "Pod属于节点"
- **标签**: 使用统一的标签体系

### 文档结构

1. 网络描述放在文件开头
2. 使用 mermaid 图展示整体拓扑
3. 对象定义在前，关系和行动在后
4. 相关定义放在一起

### 业务规则放置

业务规则应按作用域分层放置，不要在 BKN 文件中添加规范外的额外信息：

1. **网络级规则** — 写在 `network.bkn` 的 `# {name}` 标题之后的描述区，用于声明整个知识网络的顶层业务约束
2. **类型级规则** — 写在对应类型文件（`object_type.bkn`、`relation_type.bkn`、`action_type.bkn`）的 body 描述段（`## ObjectType: {name}` 标题之后、第一个 `###` 之前的自由文本），不要放在 frontmatter 中
3. **属性级规则** — 直接写在 Data Properties 表的 `Description` 列中

> **注意**：BKN 文件有严格的格式约束（frontmatter + 标准 section），超出规范定义的内容在 SDK 解析和平台导入时可能不会被保存。请将业务规则放在上述三个层级中，不要添加自定义 section 或非标准结构。

### 简洁原则

- 避免重复信息
- 每个定义文件职责单一

### 可读性

- 使用表格呈现结构化数据
- 添加业务语义说明
- 必要时使用 mermaid 图

---

## 参考

- [架构设计](./ARCHITECTURE.md)
- 样例：
  - [K8s 网络](../examples/k8s-network/) - K8s 拓扑知识网络
  - [供应链网络](../examples/supplychain-hd/) - 供应链业务知识网络
