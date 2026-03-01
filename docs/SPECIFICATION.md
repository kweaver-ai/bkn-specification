# BKN 语言规范

版本: 1.0.0
spec_version: 1.0.0

## 概述

BKN (Business Knowledge Network) 是一种基于 Markdown 的声明式建模语言，用于定义业务知识网络中的实体、关系和行动。BKN 只负责描述模型结构与语义，不包含执行逻辑——校验引擎、数据管道、工作流等运行时能力由消费 BKN 模型的平台实现。

本文档定义了 BKN 的完整语法规范。

### 术语表（Glossary）

**核心概念**

| 术语 | 含义 |
|------|------|
| BKN | Business Knowledge Network，业务知识网络 |
| knowledge_network | 一个业务知识网络的整体集合 |
| entity | 业务对象类型（例如 Pod/Node/Service） |
| relation | 连接两个 entity 的关系类型（例如 belongs_to/routes_to） |
| action | 对 entity 执行的操作定义（可绑定 tool 或 mcp） |

**实体结构**

| 术语 | 含义 |
|------|------|
| data_view | 数据视图，实体/关系可直接映射的数据来源 |
| data_properties | 实体的属性定义表，声明字段类型、主键、展示键等 |
| property_override | 属性覆盖，对继承属性的索引、约束等进行特殊配置 |
| logic_properties | 逻辑属性，基于其他数据源的派生字段（metric / operator） |
| primary_key | 主键字段，用于唯一定位实例（Data Properties 表中标记 YES） |
| display_key | 展示字段，用于 UI 显示和检索（Data Properties 表中标记 YES） |
| constraint | 属性值域约束，声明实例数据的合法范围（如 `>= 0`、`in(...)`） |
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
| network | 文件类型 `type: network`，完整知识网络的顶层容器 |
| fragment | 文件类型 `type: fragment`，可包含多个 entity/relation/action 的混合片段 |
| delete | 文件类型 `type: delete`，显式声明要删除的定义 |
| patch | 文件类型 `type: patch`，对已有文件的增量修改 |
| namespace | 命名空间，用于大规模组织与避免 ID 冲突 |
| spec_version | 规范版本号，标识文件遵循的 BKN 规范版本 |

### 标准原语表 (Primitives)

Section 标题和表格列名的规范形式，建议使用英文。解析器应同时支持英文与中文以便兼容。

下表按 **统一标题层级** 组织，适用于所有文件类型（network / fragment / entity / relation / action）。

| Level | English (canonical) | Definition | 中文 | Syntax |
|:-----:|---------------------|------------|------|--------|
| `#` | Entities | Section: all entity definitions in this file | 实体定义 | `# Entities` |
| `#` | Relations | Section: all relation definitions | 关系定义 | `# Relations` |
| `#` | Actions | Section: all action definitions | 行动定义 | `# Actions` |
| `##` | Entity | Individual entity definition | 实体 | `## Entity: {id}` |
| `##` | Relation | Individual relation definition | 关系 | `## Relation: {id}` |
| `##` | Action | Individual action definition | 行动 | `## Action: {id}` |
| `###` | Data Source | The data view this entity maps from | 数据来源 | `### Data Source` |
| `###` | Data Properties | Explicit list of fields (name, type, PK, index) | 数据属性 | `### Data Properties` |
| `###` | Property Override | Per-property overrides (e.g. index config) | 属性覆盖 | `### Property Override` |
| `###` | Logic Properties | Derived fields: metric, operator | 逻辑属性 | `### Logic Properties` |
| `###` | Business Semantics | Human-readable meaning of the entity/relation | 业务语义 | `### Business Semantics` |
| `###` | Endpoints | Relation endpoints: source, target, type | 关联定义 | `### Endpoints` |
| `###` | Mapping Rules | How source/target properties map | 映射规则 | `### Mapping Rules` |
| `###` | Mapping View | For data_view relations: the join view | 映射视图 | `### Mapping View` |
| `###` | Source Mapping | Map source entity props to view | 起点映射 | `### Source Mapping` |
| `###` | Target Mapping | Map view to target entity props | 终点映射 | `### Target Mapping` |
| `###` | Bound Entity | Entity this action operates on | 绑定实体 | `### Bound Entity` |
| `###` | Trigger Condition | When to run (YAML condition) | 触发条件 | `### Trigger Condition` |
| `###` | Pre-conditions | Data conditions required before action execution | 前置条件 | `### Pre-conditions` |
| `###` | Tool Configuration | tool or MCP binding | 工具配置 | `### Tool Configuration` |
| `###` | Parameter Binding | param name, source, binding | 参数绑定 | `### Parameter Binding` |
| `###` | Schedule | FIX_RATE or CRON | 调度配置 | `### Schedule` |
| `###` | Scope of Impact | What objects are affected | 影响范围 | `### Scope of Impact` |
| `####` | {property_name} | Individual logic property sub-section | — | `#### {name}` |
| — | Primary Key | Field that uniquely identifies an instance | 主键 | Data Properties table column |
| — | Display Key | Field used for UI label / search display | 显示属性 | Data Properties table column |
| — | Action Type | add \| modify \| delete | 行动类型 | table column |

表格列名（canonical）：Type, ID, Name, Property, Display Name, Type, Constraint, Primary Key, Display Key, Index, Index Config, Description; Source, Target, Required, Min, Max; Source Property, Target Property; Parameter, Type, Source, Binding, Description; Bound Entity, Action Type; Entity, Check, Condition, Message; Object, Impact Description。解析器同时接受中文列名。

## 文件格式

### 文件扩展名

- `.bkn` - BKN 文件

### 文件编码

- UTF-8

### 基本结构

每个 BKN 文件由两部分组成：

1. **YAML Frontmatter**: 文件元数据
2. **Markdown Body**: 知识网络定义内容

```markdown
---
type: network
id: example-network
name: Example Network
version: 1.0.0
---

# Network Title

Network description...

## Entity: entity_id

Entity definition...

## Relation: relation_id

Relation definition...

## Action: action_id

Action definition...
```

---

## Frontmatter 规范

### 工程可控性字段（推荐）

为支持规模化协作、审批与审计，建议在定义文件中使用以下字段：

| 字段 | 适用 type | 说明 |
|------|----------|------|
| `spec_version` | all | 该文件使用的规范版本（默认继承文档 spec_version） |
| `namespace` | entity/relation/action/fragment/delete | 命名空间/包名，用于大规模组织与避免冲突（例如 `platform.k8s`） |
| `owner` | entity/relation/action/fragment/delete | 负责人/团队（用于审计与审批路由） |
| `enabled` | action | 是否启用（建议默认 `false`，导入不等于启用） |
| `risk_level` | action | 风险等级（`low|medium|high`，用于审批与发布策略） |
| `requires_approval` | action | 是否需要审批才能启用/执行 |

### 文件类型 (type)

| type | 说明 | 用途 |
|------|------|------|
| `network` | 完整知识网络 | 包含多个定义的网络文件 |
| `entity` | 单个实体定义 | 独立的实体文件，可直接导入 |
| `relation` | 单个关系定义 | 独立的关系文件，可直接导入 |
| `action` | 单个行动定义 | 独立的行动文件，可直接导入 |
| `fragment` | 混合片段 | 包含多个类型的部分定义 |
| `delete` | 删除标记 | 标记要删除的定义 |

### 网络文件 (type: network)

```yaml
---
type: network                    # 完整知识网络
id: string                       # 网络ID，唯一标识
name: string                     # 网络显示名称
version: string                  # 版本号 (semver)
tags: [string]                   # 可选，标签列表
description: string              # 可选，网络描述
includes: [string]               # 可选，引用的其他文件
---
```

### 单实体文件 (type: entity)

```yaml
---
type: entity                     # 单个实体定义
id: string                       # 实体ID，唯一标识
name: string                     # 实体显示名称
version: string                  # 可选，版本号
network: string                  # 所属网络ID（建议必填，保证导入确定性）
namespace: string                # 可选，命名空间/包名
owner: string                    # 可选，负责人/团队
tags: [string]                   # 可选，标签列表
---
```

### 单关系文件 (type: relation)

```yaml
---
type: relation                   # 单个关系定义
id: string                       # 关系ID，唯一标识
name: string                     # 关系显示名称
version: string                  # 可选，版本号
network: string                  # 所属网络ID（建议必填，保证导入确定性）
namespace: string                # 可选，命名空间/包名
owner: string                    # 可选，负责人/团队
---
```

### 单行动文件 (type: action)

```yaml
---
type: action                     # 单个行动定义
id: string                       # 行动ID，唯一标识
name: string                     # 行动显示名称
action_type: add | modify | delete  # 行动类型
version: string                  # 可选，版本号
network: string                  # 所属网络ID（建议必填，保证导入确定性）
namespace: string                # 可选，命名空间/包名
owner: string                    # 可选，负责人/团队
enabled: boolean                 # 可选，是否启用（建议默认 false）
risk_level: low | medium | high  # 可选，静态风险等级
requires_approval: boolean       # 可选，是否需要审批
---
```

> **动态 risk 属性**：Action 的运行时属性 `risk`（取值 `allow` | `not_allow`）由 SDK 风险评估模块根据当前场景与带 `risk` tag 的知识计算，不在此 frontmatter 中声明。

### 混合片段 (type: fragment)

```yaml
---
type: fragment                   # 混合片段
id: string                       # 片段ID
name: string                     # 片段名称
version: string                  # 可选，版本号
network: string                  # 目标网络ID（建议必填，保证导入确定性）
namespace: string                # 可选，命名空间/包名
owner: string                    # 可选，负责人/团队
---
```

### 删除标记 (type: delete)

```yaml
---
type: delete                     # 删除标记
network: string                  # 目标网络ID（建议必填，保证导入确定性）
namespace: string                # 可选，命名空间/包名
owner: string                    # 可选，负责人/团队
targets:                         # 要删除的定义列表
  - entity: pod
  - relation: pod_belongs_node
  - action: restart_pod
---
```

---

## 实体定义规范

### 语法

```markdown
## Entity: {entity_id}

**{display_name}** - {brief_description}

- **Tags**: {tag1}, {tag2}     (可选，定义级标签)
- **Owner**: {owner}          (可选，负责人/团队)

### Data Source

| Type | ID | Name |
|------|-----|------|
| data_view | {view_id} | {view_name} |

### Data Properties

| Property | Display Name | Type | Constraint | Description | Primary Key | Display Key | Index |
|----------|--------------|------|------------|-------------|:-----------:|:-----------:|:-----:|
| {prop} | {name} | {type} | | {desc} | YES | | YES |
| {prop} | {name} | {type} | | {desc} | | YES | |

- `Primary Key`：标记为 `YES` 的属性用于唯一定位实例，至少一个
- `Display Key`：标记为 `YES` 的属性用于 UI 展示和检索显示，至少一个
- `Constraint` 列为可选，声明该属性在实例数据层面的合法值范围；留空表示无约束。语法见下文"Constraint 列语法"

### Property Override

(optional) Declare only properties needing special configuration

| Property | Display Name | Index Config | Constraint | Description |
|----------|--------------|--------------|------------|-------------|
| ... | ... | ... | ... | ... |

#### Index Config 语法

`Index Config` 列支持组合式语法，多个索引类型用 ` + ` 连接。可在括号内传递可选参数：

| 类型 | 语法 | 说明 |
|------|------|------|
| keyword | `keyword` | 基础关键字索引 |
| keyword | `keyword(max_len)` | 关键字索引，`max_len` 为 ignore_above_len |
| fulltext | `fulltext` | 全文索引，默认分析器 |
| fulltext | `fulltext(analyzer)` | 全文索引，指定分析器（如 standard、ik_max_word） |
| vector | `vector` | 向量索引，默认模型 |
| vector | `vector(model_id)` | 向量索引，指定 embedding 模型 ID |

示例：`keyword(1024) + fulltext(standard) + vector(1951511856216674304)`

### Logic Properties

#### {property_name}

- **Type**: metric | operator
- **Source**: {source_id} ({source_type})
- **Description**: {description}

| Parameter | Type | Source | Binding | Description |
|-----------|------|--------|---------|-------------|
| ... | string | property | {property_name} | 从实体属性绑定 |
| ... | array | input | - | 运行时用户输入 |
| ... | string | const | {value} | 常量值 |
```

- `Type`：参数数据类型，如 string、number、boolean、array
- `Source`：值来源，`property`（实体属性）/ `input`（用户输入）/ `const`（常量）
- `Binding`：当 Source 为 property 时为属性名，为 const 时为常量值，为 input 时为 `-`

### 定义级元数据

在 `## Entity:` 或 `## Relation:` 的定义头部（在 `### Data Source` 或 `### Endpoints` 之前），可使用可选的 inline 元数据行：

- **Tags**：该定义的标签列表（逗号分隔），用于分类、筛选和审计
- **Owner**：负责人或团队，用于审批路由和审计

在 fragment / network 文件中，多个实体或关系可各自拥有不同的 tags 和 owner。

### 风险相关定义

使用标签 **`risk`** 可标记“与风险相关的”实体与关系，供 AI 应用识别与筛选，并参与 Action 的**风险评估计算**：

- 在需要参与风险评估的实体、关系定义头部增加 `- **Tags**: risk`（或包含 `risk` 的标签列表）。
- AI 应用可通过 tags 筛选出所有 risk 相关定义，用于策略或决策。
- Action 拥有一个**运行时/计算属性** `risk`（见「行动定义规范」），取值 `allow` | `not_allow`，由风险评估模块根据当前场景与带 `risk` tag 的实体/关系数据计算得出，**不写入 BKN 文件**。

### 字段说明

| 字段 | 必须 | 说明 |
|------|:----:|------|
| {entity_id} | YES | 实体唯一标识，小写字母、数字、下划线 |
| {display_name} | YES | 人类可读名称 |
| Data Source | NO | 映射的数据视图，未设定时由平台自动管理 |
| Data Properties | YES | 属性定义，须标记 Primary Key 和 Display Key |
| Property Override | NO | 需要特殊配置的属性（索引、约束等） |
| Logic Properties | NO | 指标、算子等扩展属性 |

### 数据类型

Data Properties 表的 `Type` 列使用以下标准类型。类型名称大小写不敏感，推荐使用下表中的规范形式。

| 类型 | 说明 | JSON 对应 | SQL 对应 |
|------|------|-----------|----------|
| int32 | 32 位有符号整数 | number | INT / INTEGER |
| int64 | 64 位有符号整数 | number | BIGINT |
| integer | 泛型整数（精度未指定） | number | 平台相关（通常 int64） |
| float32 | 32 位浮点数 | number | FLOAT / REAL |
| float64 | 64 位浮点数 | number | DOUBLE / DOUBLE PRECISION |
| float | 泛型浮点数（精度未指定） | number | 平台相关（通常 float64） |
| decimal(p,s) | 精确十进制数，p 为精度，s 为小数位 | string / number | DECIMAL(p,s) / NUMERIC(p,s) |
| decimal | 泛型精确十进制（精度未指定） | string / number | 平台相关 |
| bool | 布尔值 | boolean | BOOLEAN |
| VARCHAR | 变长字符串 | string | VARCHAR / TEXT |
| TEXT | 长文本 | string | TEXT / CLOB |
| DATE | 日期（无时间） | string (ISO 8601) | DATE |
| TIME | 时间（无日期） | string (ISO 8601) | TIME |
| TIMESTAMP | 日期时间（含时区） | string (ISO 8601) | TIMESTAMP |
| JSON | JSON 结构数据 | object / array | JSON / JSONB |
| BINARY | 二进制数据 | string (base64) | BLOB / BYTEA |

> 当数据源使用的类型不在上表中时，可直接使用数据源原生类型名称（如 `ARRAY<VARCHAR>`），解析器应透传不识别的类型。

### 配置模式

#### 模式一：映射 + 最小属性声明

映射视图，仅声明主键和展示键：

```markdown
## Entity: node

**Node**

### Data Source

| Type | ID |
|------|-----|
| data_view | view_123 |

### Data Properties

| Property | Primary Key | Display Key |
|----------|:-----------:|:-----------:|
| id | YES | |
| node_name | | YES |
```

#### 模式二：映射 + 属性覆盖

映射视图，声明键并配置需要特殊处理的属性：

```markdown
## Entity: pod

**Pod Instance**

### Data Source

| Type | ID |
|------|-----|
| data_view | view_456 |

### Data Properties

| Property | Primary Key | Display Key |
|----------|:-----------:|:-----------:|
| id | YES | |
| pod_name | | YES |

### Property Override

| Property | Index Config | Constraint | Description |
|----------|--------------|------------|-------------|
| pod_status | fulltext(standard) + vector | in(Running,Pending,Failed,Unknown) | 支持全文和语义搜索 |
```

#### 模式三：完整定义

完整声明所有属性（含类型、约束、索引）：

```markdown
## Entity: service

**Service**

### Data Source

| Type | ID |
|------|-----|
| data_view | view_789 |

### Data Properties

| Property | Display Name | Type | Constraint | Description | Primary Key | Display Key | Index |
|----------|--------------|------|------------|-------------|:-----------:|:-----------:|:-----:|
| id | ID | int64 | | Primary key | YES | | YES |
| service_name | Name | VARCHAR | not_null | Service name | | YES | YES |
| service_type | Service Type | VARCHAR | in(ClusterIP,NodePort,LoadBalancer) | Service type | | | |
```

---

## 关系定义规范

### 语法

```markdown
## Relation: {relation_id}

**{display_name}** - {brief_description}

- **Tags**: {tag1}, {tag2}     (可选，定义级标签)
- **Owner**: {owner}          (可选，负责人/团队)

| Source | Target | Type | Required | Min | Max |
|--------|--------|------|----------|-----|-----|
| {source_entity} | {target_entity} | direct \| data_view | YES \| NO | 0 | - |

- `Required`: YES/NO，是否必须存在至少一条关系（从 Source 侧看）
- `Min`: 最小关系数，默认 0
- `Max`: 最大关系数，`-` 表示无限制
- Required / Min / Max 均为可选列，省略时不做约束

### Mapping Rules

| Source Property | Target Property |
|------------------|-----------------|
| {source_prop} | {target_prop} |

### Business Semantics

(optional) Human-readable meaning of the relation...
```

### 字段说明

| 字段 | 必须 | 说明 |
|------|:----:|------|
| {relation_id} | YES | 关系唯一标识 |
| Source | YES | 起点实体 ID |
| Target | YES | 终点实体 ID |
| Type | YES | `direct` (直接映射) 或 `data_view` (视图映射) |
| Mapping Rules | YES | 属性映射关系 |
| Required | NO | 是否必须存在至少一条关系（从 Source 侧看） |
| Min | NO | 最小关系数 |
| Max | NO | 最大关系数，`-` 表示无限制 |

### 关系类型

#### 直接映射 (direct)

通过属性值匹配建立关联：

```markdown
## Relation: pod_belongs_node

| Source | Target | Type | Required | Min | Max |
|--------|--------|------|----------|-----|-----|
| pod | node | direct | YES | 1 | 1 |

每个 Pod 必须属于且仅属于一个 Node。

### Mapping Rules

| Source Property | Target Property |
|------------------|-----------------|
| pod_node_name | node_name |
```

#### 视图映射 (data_view)

通过中间视图建立关联：

```markdown
## Relation: user_likes_post

| Source | Target | Type | Required | Min | Max |
|--------|--------|------|----------|-----|-----|
| user | post | data_view | NO | 0 | - |

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

## 行动定义规范

### 语法

```markdown
## Action: {action_id}

**{display_name}** - {brief_description}

| Bound Entity | Action Type |
|--------------|-------------|
| {entity_id} | add | modify | delete |

### Trigger Condition

```yaml
field: {property_name}
operation: == | != | > | < | >= | <= | in | not_in | exist | not_exist
value: {value}
```

### Pre-conditions

(optional) 执行前的数据前置条件，不满足则阻止行动执行

| Entity | Check | Condition | Message |
|--------|-------|-----------|---------|
| {entity_id} | relation:{relation_id} | exist | 违反时的说明 |
| {entity_id} | property:{property_name} | {op} {value} | 违反时的说明 |

- `Check`: `property:{name}` 或 `relation:{id}`，指明检查目标
- `Condition`: 复用 Trigger Condition 操作符语法
- Trigger 决定「何时触发」，Pre-conditions 决定「能否执行」

### Tool Configuration

| Type | Tool ID |
|------|---------|
| tool | {tool_id} |

or

| Type | MCP |
|------|-----|
| mcp | {mcp_id}/{tool_name} |

### Parameter Binding

| Parameter | Type | Source | Binding | Description |
|-----------|------|--------|---------|-------------|
| {param_name} | string | property | {property_name} | {说明} |
| {param_name} | string | input | - | {说明} |
| {param_name} | string | const | {value} | {说明} |

### Schedule

(optional)

| Type | Expression |
|------|------------|
| FIX_RATE | {interval} |
| CRON | {cron_expr} |

### Execution Description

(optional) Detailed execution flow...
```

### 治理要求（强烈建议）

行动定义连接执行面（tool/mcp），为了稳定性与安全性，建议在每个 Action 中**显式写清**以下四类信息，并在工程侧落地相应治理：

1. **触发**：何时触发（手动/定时/条件触发），触发条件是否可复现
2. **影响范围**：影响哪些对象、范围边界、预期副作用
3. **权限与前置条件**：谁可以导入/启用/执行，是否需要审批，依赖的权限/凭据
4. **回滚/失败策略**：失败处理、重试策略、熔断/限流、可撤销性

> 推荐实践：导入不等于启用；启用与执行需要独立的权限与审计日志，并能关联到对应的 BKN 定义版本。

### 字段说明

| 字段 | 必须 | 说明 |
|------|:----:|------|
| {action_id} | YES | 行动唯一标识 |
| Bound Entity | YES | 目标实体 ID |
| Action Type | YES | `add` / `modify` / `delete` |
| Trigger Condition | NO | 自动触发的条件 |
| Pre-conditions | NO | 执行前的数据前置条件 |
| Tool Configuration | YES | 执行的工具或 MCP |
| Parameter Binding | YES | 参数来源配置 |
| Schedule | NO | 定时执行配置 |
| risk（计算属性） | - | 运行时属性，取值 `allow` \| `not_allow`，由风险评估模块根据场景与带 `risk` tag 的实体/关系计算，不写入 BKN |

### 触发条件操作符

以下操作符适用于 Trigger Condition、Pre-conditions 以及 Data Properties / Property Override 表中的 Constraint 列：

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
| not_null | 不为空 | (无需 value，约束专用) |
| regex | 正则匹配 | `value: "^[a-z]+$"`（约束专用） |

### Constraint 列语法

`Constraint` 列出现在 Entity 的 **Data Properties** 和 **Property Override** 表格中，用于声明该属性在实例数据层面的合法值范围。该列为可选，留空表示无约束。

#### 语法格式

每条约束写在单个表格单元格内，格式为 **`operator`** 或 **`operator(args)`** 或 **`operator value`**。

| 类别 | 语法 | 含义 | 适用类型 | 示例 |
|------|------|------|----------|------|
| 比较 | `== value` | 等于固定值 | 数值、字符串 | `== 1` |
| 比较 | `!= value` | 不等于固定值 | 数值、字符串 | `!= 0` |
| 比较 | `> value` | 大于 | 数值 | `> 0` |
| 比较 | `< value` | 小于 | 数值 | `< 1000` |
| 比较 | `>= value` | 大于等于 | 数值 | `>= 0` |
| 比较 | `<= value` | 小于等于 | 数值 | `<= 100` |
| 范围 | `range(min,max)` | 闭区间 [min, max] | 数值 | `range(0,100)` |
| 枚举 | `in(v1,v2,…)` | 值必须为列表之一 | 字符串、数值 | `in(Running,Pending,Failed)` |
| 枚举 | `not_in(v1,v2,…)` | 值不能为列表之一 | 字符串、数值 | `not_in(Deleted,Archived)` |
| 存在性 | `not_null` | 值不能为空 | 任意 | `not_null` |
| 存在性 | `exist` | 属性必须存在 | 任意 | `exist` |
| 存在性 | `not_exist` | 属性不能存在 | 任意 | `not_exist` |
| 正则 | `regex:pattern` | 值须匹配正则表达式 | 字符串 | `regex:^[a-z0-9_]+$` |

#### 组合约束

当一个属性需要多条约束时，使用 `; ` （分号 + 空格）分隔：

```
not_null; >= 0
not_null; regex:^[a-z_]+$
>= 0; <= 100
not_null; in(ClusterIP,NodePort,LoadBalancer)
```

组合约束表示 **逻辑 AND**——所有约束必须同时满足。

#### 完整示例

| Property | Display Name | Type | Constraint | Description | Primary Key | Display Key | Index |
|----------|--------------|------|------------|-------------|:-----------:|:-----------:|:-----:|
| id | ID | int64 | not_null | 主键 | YES | | YES |
| name | 名称 | VARCHAR | not_null; regex:^[a-z0-9_]+$ | 唯一标识名 | | YES | YES |
| quantity | 数量 | int32 | >= 0 | 不允许负数 | | | |
| status | 状态 | VARCHAR | in(Active,Inactive,Archived) | 枚举值 | | | YES |
| score | 评分 | float64 | range(0,100) | 百分制 | | | |
| priority | 优先级 | int32 | not_null; range(1,5) | 1-5 级 | | | |

### 参数来源

| 来源 | 说明 |
|------|------|
| property | 从实体属性获取 |
| input | 运行时用户输入 |
| const | 常量值 |

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
> **注意**: 该实体变更需要审批流程
```

### 标题层级

标题层级在所有文件类型中保持一致：

- `#` - 文档/分组标题（例如网络标题，或 `# Entities` / `# Relations` / `# Actions`）
- `##` - 类型定义（`## Entity:` / `## Relation:` / `## Action:`）
- `###` - 定义内 section（Data Source, Data Properties, Mapping Rules, Trigger Condition 等）
- `####` - 子项（例如逻辑属性名）

> 规则：不再区分“单定义文件层级上移”；所有定义统一使用上述层级。

---

## 文件组织

### 模式一：单文件（小型网络）

所有定义在一个 `.bkn` 文件中：

```markdown
---
type: network
id: my-network
---

# My Network

## Entity: entity1
...

## Entity: entity2
...

## Relation: rel1
...

## Action: action1
...
```

### 模式二：按类型拆分（中型网络）

使用 `index.bkn` 引用其他文件：

```markdown
---
type: network
id: my-network
includes:
  - entities.bkn
  - relations.bkn
  - actions.bkn
---

# My Network

网络描述...
```

### 模式三：每定义一文件（大型网络，推荐）

每个实体/关系/行动独立一个文件：

```
k8s-network/
├── index.bkn                    # type: network
├── entities/
│   ├── pod.bkn                  # type: entity
│   ├── node.bkn                 # type: entity
│   └── service.bkn              # type: entity
├── relations/
│   ├── pod_belongs_node.bkn     # type: relation
│   └── service_routes_pod.bkn   # type: relation
└── actions/
    ├── restart_pod.bkn          # type: action
    └── cordon_node.bkn          # type: action
```

**单实体文件示例** (`pod.bkn`):

```markdown
---
type: entity
id: pod
name: Pod Instance
network: k8s-network
---

## Entity: pod

**Pod Instance**

Minimal deployable unit in Kubernetes.

## Data Source

| Type | ID |
|------|-----|
| data_view | view_123 |

## Data Properties

| Property | Primary Key | Display Key |
|----------|:-----------:|:-----------:|
| id | YES | |
| pod_name | | YES |
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

其中 `network_id` 取自：

- 优先使用 frontmatter `network`
- 若缺失，则由导入目标网络（导入命令参数或 `type: network` 的 `id`）补齐

### 更新语义（replace vs merge）

默认建议使用 **replace（整段覆盖）**：

- 当 `key` 已存在时，用导入文件中的定义整体替换旧定义
- **缺失字段不代表删除**：仅代表“该字段不在本次定义中”；删除必须显式声明（见 `type: delete`）

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
| 使用 `type: delete` | 删除指定定义 |

### 导入示例

**场景：向已有网络添加新实体**

创建 `deployment.bkn`:

```markdown
---
type: entity
id: deployment
name: Deployment
network: k8s-network
---

## Entity: deployment

**Deployment**

Kubernetes deployment controller.

## Data Source

| Type | ID |
|------|-----|
| data_view | deployment_view |

## Data Properties

| Property | Primary Key | Display Key |
|----------|:-----------:|:-----------:|
| id | YES | |
| deployment_name | | YES |
```

导入后，`k8s-network` 将包含新的 `deployment` 实体。

**场景：更新已有实体**

创建同 ID 的文件，导入后自动覆盖：

```markdown
---
type: entity
id: pod
name: Pod实例（更新版）
network: k8s-network
---

## Entity: pod

**Pod实例（更新版）**

更新后的定义...
```

**场景：删除定义**

```markdown
---
type: delete
network: k8s-network
targets:
  - entity: deprecated_entity
  - relation: old_relation
---

# 删除废弃定义

清理不再使用的定义。
```

**场景：批量导入（fragment）**

```markdown
---
type: fragment
id: monitoring-extension
name: 监控扩展
network: k8s-network
---

# 监控扩展

添加监控相关的实体和行动。

## Entity: alert

**Alert**

### Data Source

| Type | ID |
|------|-----|
| data_view | alert_view |

### Data Properties

| Property | Primary Key | Display Key |
|----------|:-----------:|:-----------:|
| id | YES | |
| alert_name | | YES |

---

## Action: send_alert

**Send Alert**

| Bound Entity | Action Type |
|--------------|-------------|
| alert | add |

### Tool Configuration

| Type | Tool ID |
|------|---------|
| tool | alert_sender |
```

---

## Patch 规范（文件级别）

### 添加操作

```markdown
---
type: patch
id: 2026-01-31-add-metric
target: k8s-topology.bkn
operation: add
---

# 添加CPU指标

在 `## Entity: pod` 的 `### Logic Properties` 后添加：

#### cpu_usage

- **Type**: metric
- **Source**: cpu_metric
```

### 修改操作

```markdown
---
type: patch
id: 2026-01-31-update-condition
target: k8s-topology.bkn
operation: modify
---

# 更新触发条件

将 `## Action: restart_pod` 的触发条件修改为：

```yaml
field: pod_status
operation: in
value: [Unknown, Failed, CrashLoopBackOff]
`` `
```

### 删除操作

```markdown
---
type: patch
id: 2026-01-31-remove-action
target: k8s-topology.bkn
operation: delete
---

# 删除废弃行动

删除 `## Action: deprecated_action`
```

---

## 最佳实践

### 命名规范

- **ID**: 小写字母、数字、下划线，如 `pod_belongs_node`
- **显示名称**: 简洁明确，如 "Pod属于节点"
- **标签**: 使用统一的标签体系

### 文档结构

1. 网络描述放在文件开头
2. 使用 mermaid 图展示整体拓扑
3. 实体定义在前，关系和行动在后
4. 相关定义放在一起

### 简洁原则

- 优先使用完全映射模式
- 只在需要时声明属性覆盖
- 避免重复信息

### 可读性

- 使用表格呈现结构化数据
- 添加业务语义说明
- 必要时使用 mermaid 图

---

## 参考

- [架构设计](./ARCHITECTURE.md)
- 样例：
  - [单文件模式](./examples/k8s-topology.bkn) - 所有定义在一个文件
  - [按类型拆分](./examples/k8s-network/) - 实体/关系/行动分文件
  - [每定义一文件](./examples/k8s-modular/) - 每个定义独立文件（推荐大规模场景）
