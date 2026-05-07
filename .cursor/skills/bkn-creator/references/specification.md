# BKN 规范（LLM 生成用）

你负责生成符合 BKN 格式的 Markdown，供业务知识网络建模使用。

## 文件扩展名与载体

- `.bkn` / `.bknd`：推荐扩展名（schema 用 `.bkn`，实例数据用 `.bknd`）
- `.md`：兼容载体，可用 `.md` 保存；内容必须满足 BKN frontmatter、`type` 及结构约束，否则加载时报错

## 根文件与目录加载

- **根文件命名**：推荐 `network.bkn` 作为网络入口；`index.bkn` 兼容。发现顺序：`network.bkn` > `network.md` > `index.bkn` > `index.md`
- **目录输入**：`load_network(dir)` 支持传入目录，自动发现根文件
- **无 includes**：当根文件为 `type: knowledge_network` 且未声明 `includes` 时：
  - 同目录下所有 BKN 文件视为同一网络输入
  - **子目录隐式加载**：`object_types/`、`relation_types/`、`action_types/`、`risk_types/`、`concept_groups/`、`metrics/` 下的 `.bkn`/`.bknd`/`.md` 文件也会被自动加载
- **有 includes**：则仅按 `includes` 加载

## 文件结构

每个 BKN 文件（`.bkn` / `.bknd` / `.md`）由两部分组成：
1. **YAML Frontmatter**（元数据，以 `---` 包裹）
2. **Markdown Body**（定义内容）

## Frontmatter 类型

| type | 说明 |
|------|------|
| `knowledge_network` | 知识网络根文件 |
| `object_type` | 单个对象类型定义 |
| `relation_type` | 单个关系类型定义 |
| `action_type` | 单个行动类型定义 |
| `risk_type` | 单个风险类型定义 |
| `concept_group` | 概念分组 |
| `metric` | 网络级指标（推荐 `metrics/*.bkn`） |
| `fragment` | 混合片段（多定义合一） |
| `data` | 数据文件（建议 `.bknd`，承载对象/关系实例行） |

SDK 仍接受旧名 `object`、`relation`、`action`、`risk` 作为别名，但推荐使用 `*_type` 命名。

## `.bknd` 数据文件（type: data）

用于承载**知识原生**实例数据，不承载 schema 定义。仅当 Object 的 Data Source 为 `bknd` 或未指定 data_view 时，才使用 `.bknd` 维护数据；Data Source 为 `data_view` 的对象数据来自外部系统，不可用 `.bknd` 编辑。

Frontmatter 示例：

```yaml
---
type: data
network: recoverable-network
object: scenario   # 或 relation: rs_under_scenario（二选一）
source: PFMEA模板.xlsx   # 可选，数据来源
---
```

正文使用「一个标题 + 一个 Markdown 表格」，列名需与目标对象 Data Properties 的 `Name` 列（或 `Property` 列）一致。

## 对象类型 (ObjectType)

```yaml
---
type: object_type
id: {object_id}        # 小写+下划线
name: {显示名称}
tags: [tag1, tag2]     # 可选
---
```

正文结构：
- `## ObjectType: {显示名称}` + 简短描述
- `### Data Properties`（必须）：表格，列 Name | Display Name | Type | Description | Mapped Field
- `### Keys`（必须）：
  - `Primary Keys: {key_name}`（至少一个，逗号分隔多个）
  - `Display Key: {key_name}`（一个）
  - `Incremental Key: {key_name}`（可选，可为空）
- `### Logic Properties`（可选）：`#### {property_name}`，含 Display/Type/Source/Description，以及 Parameter 表
- `### Data Source`（可选）：表格，列 Type | ID | Name，行 `data_view | {view_id} | {view_name}`

### 数据类型

Type 列标准类型（大小写不敏感）：string, integer, float, decimal, boolean, date, time, datetime, text, json, binary；以及 int32, int64, float32, float64, VARCHAR, TEXT, DATE, TIME, TIMESTAMP 等。不在列表中的类型透传。

## 关系类型 (RelationType)

```yaml
---
type: relation_type
id: {relation_id}
name: {显示名称}
tags: [tag1, tag2]     # 可选
---
```

正文：
- `## RelationType: {显示名称}` + 简短描述
- `### Endpoint` 或 `### Endpoints`：表格 Source | Target | Type（`direct` 或 `data_view`）
- **direct 类型**时：`### Mapping Rules`：表格 Source Property | Target Property
- **data_view 类型**时：`### Mapping View`、`### Source Mapping`、`### Target Mapping`

## 行动类型 (ActionType)

```yaml
---
type: action_type
id: {action_id}
name: {显示名称}
tags: [tag1, tag2]     # 可选
enabled: false        # 是否启用，默认 false
risk_level: low | medium | high
requires_approval: true  # 是否需要审批
---
```

正文：
- `## ActionType: {显示名称}` + 简短描述
- `### Bound Object`（必须）：表格 Bound Object | Action Type（`add` / `modify` / `delete` / `query`）
- `### Affect Object`（可选）：表格 Affect Object
- `### Trigger Condition`（可选）：YAML 块，含 condition.object_type_id、field、operation、value
- `### Pre-conditions`（可选）：表格 Object | Check | Condition | Message
- `### Tool Configuration`（可选）：Type | Toolbox ID | Tool ID
- `### Parameter Binding`（可选）：Parameter | Type | Source | Binding | Description，Source 为 property/input/const
- `### Schedule`（可选）：表格 Type | Expression（`FIX_RATE` 或 `CRON`）
- `### Scope of Impact`（可选）：Impacted Object | Impact Description

## 风险类型 (RiskType)

```yaml
---
type: risk_type
id: {risk_id}
name: {显示名称}
tags: [tag1, tag2]     # 可选
---
```

正文：
- `## RiskType: {显示名称}` + 简短描述
- `### Control Scope`（必须）：管控范围描述
- `### Control Policy` 或 `### 管控策略`（必须）：策略要点
- `### Pre-checks`（可选）：表格 Object | Check | Condition | Message
- `### Rollback Plan`（可选）：回滚步骤
- `### Audit Requirements`（可选）：审计要求

## 概念分组 (ConceptGroup)

```yaml
---
type: concept_group
id: {group_id}
name: {显示名称}
tags: [tag1, tag2]     # 可选
---
```

正文：
- `## ConceptGroup: {显示名称}` + 简短描述
- `### Object Types`（必须）：表格 ID | Name | Description

## 网络级指标 (metric)

```yaml
---
type: metric
id: {metric_id}
name: {显示名称}
tags: [tag1, tag2]     # 可选
---
```

正文：
- `## Metric: {显示名称}` + 简短描述
- `### Metric attributes`：表格 Metric Type | Unit Type | Unit（单列数据行；对应 `metric_type`、`unit_type`、`unit`）；
- `### Scope`：表格 Scope Type | Scope Ref
- `### Calculation Formula`：围栏内 YAML，根级 **`kind`**（权威）；`atomic` / `derived` / `composite` 子树互斥
- `### Time Dimension`、`### Analysis Dimensions`（可选）

详见 `docs/DESIGN_BKN_METRIC.md` 与 `docs/templates/metric.bkn.template`。

## 更新与删除（无 patch 模型）

- 定义文件导入 = add/modify（upsert）；修改即编辑文件后重新导入
- 删除元素通过 SDK/CLI delete API 执行，不通过 BKN 文件；**不要生成 type: delete 或 type: patch 文件**

## 输出规则（必须遵守）

1. **仅输出 BKN Markdown**：含 frontmatter 和 body，无多余说明
2. **不要包裹代码块**：不要用 \`\`\`markdown 包裹整体输出
3. **引用已存在的 ID**：object/relation 引用时，使用项目中已有的 id
4. **表格格式**：按上述列名严格对齐
5. **命名**：ID 使用小写字母、数字、下划线；显示名和描述用中文（除非另有要求）
6. **必填字段**：
   - 所有类型：type、id、name
   - ObjectType：Data Properties、Keys（Primary Keys + Display Key）
   - RelationType：Endpoint(s)、Mapping Rules
   - ActionType：Bound Object、Parameter Binding（或 Tool Configuration）
   - RiskType：Control Scope、Control Policy
   - ConceptGroup：Object Types
   - Metric：Metric attributes（三列表）、`### Scope`、`### Calculation Formula`（Metric Type 列须与根级 `kind` 一致）
