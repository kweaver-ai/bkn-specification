# BKN 指标（metric）设计文档

版本草案：与当前仓库 SPEC 2.0.1 对齐；**本文档描述拟定能力，实现以后续 PR 为准。**

---

## 1. Goal

在 bkn-specification 中，以与**对象类 / 关系类 / 行动类**相同的范式（独立 `.bkn` 文件、YAML frontmatter + Markdown 正文、推荐子目录组织），引入**网络级指标**的声明式定义。

约定要点：

- 文件类型名为 **`metric`**（**不使用** `metric_type` 作为文档 `type` 字段名）。
- **指标类别（atomic / derived / composite）** 以正文 **`### Calculation Formula` 根级 `kind`** 为**唯一权威**。
- **`frontmatter.metric_type` 规范保留**：与平台 **Metric API / DTO** 对齐的标准字段（非第二权威）；**推荐**在文件中长期保留并与 `kind` 同值，由**工具链或 SDK 序列化**据 `kind` 自动写入/回填；与 `kind` 冲突时**以 `kind` 为准**并规范化 frontmatter 或告警。
- 原子 / 衍生 / 复合指标 **共用同一 Metric API**；`kind` 仅区分计算公式子结构，**不因类别切换 HTTP 路由**。
- 指标（`kind: atomic`）**计算公式**中的 **`condition`** 与行动类**触发条件**写法同构，但**不包含 `object_type_id`**。
- 对象类 **Logic Properties** 仅保留 **`operator`**；**移除**逻辑属性类型 **`metric`**，网络级指标统一通过独立 `type: metric` 文件声明。

---

## 2. Background

### 2.1 当前 BKN 侧

- `docs/SPECIFICATION.md` 中对象类型可在 **Logic Properties** 下声明 **`metric | operator`**，与「对象上的派生字段」混在同一小节。
- 该形态与后端将 **Metric** 作为与 object-type **同级资源**管理（列表、批量创建、validation、override 检索等）在概念上重叠，易造成「指标到底挂在对象上还是网络上」的二义性。

### 2.2 后端与 API 参考

- OpenAPI：`kweaver-core/adp/docs/api/bkn/bkn-backend-api/bkn-metrics.yaml`（`MetricDefinition`、`CreateMetricRequest`、`MetricCalculationFormula` 等）。
- 实现参考：`kweaver-core/adp/bkn/bkn-backend/server`（如 `interfaces/metric.go`、`logics/metric/`）。

设计以该 API 的字段语义为准，BKN 文本层负责**可读、可版本化、可导入**的表达。

---

## 3. Scope

| In scope | Out scope（本文档不展开） |
|----------|---------------------------|
| 命名、目录与正文结构（范式） | 具体 PR 修改清单之外的实现细节 |
| `condition` 与 Action Trigger 的差异规则 | ontology-query `Condition` 的完整 JSON Schema _dup_ |
| 对象 Logic Properties 收敛为仅 `operator` 的规范含义 | 导入器、运行时查询引擎 |
| 与 `bkn-metrics.yaml` 的概念字段映射 | 与 kweaver 以外的第三方存储对齐 |

---

## 4. Design

### 4.1 文件类型与命名

| 项 | 约定 |
|----|------|
| `frontmatter.type` | **`metric`** |
| 正文二级标题 | 与 `## ObjectType:` 并列，建议 **`## Metric: {显示名称}`**（canonical 英文段为 `Metric`） |
| 推荐目录 | 与 `object_types/`、`action_types/` 同级：`metrics/*.bkn` |

### 4.2 Frontmatter（与 API 对齐）

建议字段（与创建/定义接口一致；`kn_id`、`branch` 由导入上下文注入，**不强制**写入文件）：

| 字段 | 说明 |
|------|------|
| `id`, `name`, `tags` | 与现有 BKN 类型惯例一致 |
| `metric_type` | **规范保留**，`atomic` \| `derived` \| `composite`，与平台 DTO 一致；**须与正文根级 `kind` 一致**。**推荐**由工具链/SDK 根据 `kind` 自动写入；手工维护时勿与 `kind` 矛盾。**校验与导入以正文 `kind` 为准**；不一致时以 `kind` **修正或覆盖** frontmatter 并告警。 |
| `scope_type` | `object_type` \| `subgraph` |
| `scope_ref` | `scope_type` 为 object_type 时为对象类型 id；为 subgraph 时为子图标识 |
| `unit_type`, `unit`, `comment` | 可选；枚举以后端为准 |

**API 与路由**：`atomic` / `derived` / `composite` **共用同一套 Metric 资源模型与 HTTP endpoint**（创建、查询、校验）；`kind` 仅影响**计算公式子结构的形态与校验**，**不因指标类别切换路由**。

### 4.3 正文结构（建议小节）

| 小节 | 用途 |
|------|------|
| `### Scope` | 表格复述 `scope_type` / `scope_ref`，便于人类阅读（实现时需定义与 frontmatter **冲突时的优先级**） |
| `### Calculation Formula` | YAML 代码块：根级 **`version`**（正文本范式版本）与 **`kind`**（`atomic` \| `derived` \| `composite`）；**仅此二者为指标类别的权威来源**。与 `kind` 对应的 **唯一**子键 **`atomic` / `derived` / `composite`** 承载具体公式（三者互斥）。 |
| `### Time Dimension` | 对应 `MetricTimeDimension`；**可整节省略**；若需表达「无时间过滤」可设策略为 **`none`**（见 §4.7） |
| `### Analysis Dimensions` | 对应 `MetricAnalysisDimension` 列表 |

**`kind` 与扩展**：新增形态时通过提高 `version`、扩展 `kind` 或子树字段演进；未知 `kind` 可由解析器拒绝或降级策略由实现约定。`derived` / `composite` 的字段级 schema 待与 `bkn-metrics.yaml` / `CreateMetricRequest` 对齐后写入 SPEC；`docs/templates/metric.bkn.template` 中已给占位结构。

嵌套 YAML 建议使用外层 ` ```markdown ` 与内层 ` ~~~yaml ` 等形式，避免破坏外层围栏（实现 SPEC 时注意排版一致性）。

### 4.4 `calculation_formula.condition`（`kind: atomic`）

以下针对 **原子指标**（`atomic` 子树）。衍生 / 复合指标的条件形态由各自子 schema 定义。

- **相同点**：与 **行动类型** `### Trigger Condition` 中的 `condition` **同一套结构与操作符**（见 SPEC 中触发条件 / Pre-conditions 所列操作符及组合习惯）。
- **不同点**：**禁止**出现 **`object_type_id`**。对象类范围已由指标的 **`scope_type` + `scope_ref`**（当为 `object_type` 时）限定；条件中的 `field` 在该作用域内解释。
- **可选**：不提供 `condition` 时表示无额外属性过滤，仅受聚合、时间窗等约束。

### 4.5 `aggregation` 与附属字段（`kind: atomic`）

- `aggregation`：**必填**（在 `atomic` 子树内）；`aggr` 枚举与后端一致（如 `count_distinct`、`sum`、`max`、`min`、`avg`、`count`）。
- `group_by`、`order_by`、`having`：可选，结构与 `bkn-metrics.yaml` 中 `MetricCalculationFormula` 一致。

### 4.6 公式中的属性名（须为 Data Properties 的 Name）

- `atomic` 子树中 **`condition.field`、`aggregation.property`、`group_by` / `order_by` 所涉 property**：**必须与** scope 所指 `object_type` 的 **Data Properties 表 → Name 列**一致。
- **Mapped Field** 仅表示对象到数据源视图的列映射；**不得在指标公式中用 Mapped Field 代替 Name**，以免 BKN 语义校验与运行时 **Name → 物理列** 的解析脱节。下推查询时由平台将 Name 解析为实际存储字段。

### 4.7 Time Dimension（可选与 `none`）

- **`### Time Dimension` 非必选**。当 scope 内对象无合适时间属性、或指标语义为**当前快照 / 全量视图**时，可**省略**该小节。
- 若保留表格且无需随时间窗过滤，可将 **Default Range Policy** 设为 **`none`**（与仅有状态类字段的对象类配合，如部分 `node` 指标示例）。

### 4.8 网络包与 CHECKSUM（`metrics/` 非必须）

- 知识网络目录下 **`metrics/` 为可选**：不含该目录的旧包、或未将 `metrics/*.bkn` 写入 CHECKSUM，**均非破坏性变更**；与 `risk_types/`、`data/` 等可选目录同级。
- 工具链若将 `metrics/` 纳入打包与校验键：**仅当目录存在时参与**；不得因缺少 `metrics/` 导致加载或校验失败。

### 4.9 对象类型 Logic Properties

- **允许**：**仅 `operator`**（及与现有 Parameter 表一致的 `property` / `input` / `const` 绑定）。
- **禁止**：逻辑属性声明为 **`metric`**；若历史文件存在，归入**迁移**（见 §7）。SDK 校验应对 `metric` **报错**。

### 4.10 术语对照（面向 SPEC 修订）

建议在术语表中明确区分：

- **逻辑属性（operator）**：挂在 **object_type** 上，描述算子派生。
- **指标（metric）**：**独立资源**，描述可聚合口径、时间维度、分析维度等，与后端 Metric API 一一对应。

---

## 5. Affected Areas（后续实现时）

| 区域 | 影响 |
|------|------|
| `docs/SPECIFICATION.md`（及 `.en.md`、`.llm.md`） | 新文件类型、`metric` 章节、原语表；对象 Logic 仅 operator |
| `docs/ARCHITECTURE.md` | 类型数量与数据流（Metric 独立；对象 → Operator） |
| `docs/templates/metric.bkn.template` | 新建；`object_type.bkn.template` 注释与示例收敛 |
| `examples/` | 含内联 logic metric 的示例需迁移或删除 |
| `sdk/golang`（`validator.go`、`parser`、模型） | 拒绝 logic `metric`；解析 `type: metric` 为独立工作项 |
| `sdk/python`、`sdk/typescript` | 与 Golang 行为对齐 |
| `.cursor/skills/bkn-creator` | `metrics/` 子目录、规范摘录 |

---

## 6. Alternatives Considered

| 方案 | 说明 | 结论 |
|------|------|------|
| 保留对象内 logic `metric` | 双轨并存 | **否**，与后端资源模型分裂 |
| 使用 `metric_type` 作为 `type` | 与「类型名叫 metric」冲突 | **否** |
| 在指标 condition 中保留 `object_type_id` | 与 `scope_ref` 重复，易不一致 | **否** |

---

## 7. Migration / Compatibility

- **规范升级**：建议在 SPEC 版本说明中注明：Logic Properties 的 `metric` **已废弃**，应迁至 `type: metric`。
- **历史文件**：需迁移脚本或人工拆分；**`ValidateNetwork`（Golang SDK）已对 object_type 上 Logic Property `type: metric` / `data_source.type: metric` 报错**。
- **解析器**：在未实现 `metric` 解析前，遇 `type: metric` 可 **fail-fast** 或 **跳过**（策略由 CLI/SDK 版本约定）。

---

## 8. Implementation Plan（建议分 PR）

1. **Spec + 模板 + 架构图**：不含 SDK 行为变更，或仅文档化 deprecation。
2. **SDK**：`BknMetric`（或等价结构）、目录加载、`ValidateNetwork` 扩展、单测。
3. **示例 + 与后端 validation 对照**：抽样请求体验证。

---

## 9. Verification

- 从范式 `metric` 文件生成 `CreateMetricRequest` JSON（或与 `MetricDefinition` 只读对照）字段完备。
- **`kind` 与 `metric_type` 一致**：正文 `Calculation Formula` 根级 `kind` 与 frontmatter `metric_type` 不一致时，**以 `kind` 为准**；合格流水线应在导出/导入时 **规范化 frontmatter** 或给出明确告警。
- 对象类型 Logic Property `Type: metric` → **校验失败**。
- 指标 YAML `condition`（原子子树内）含 `object_type_id` → **校验失败**（若实现显式规则）。
- 全量 `go test ./...` / 各语言 SDK 测试通过。

---

## 10. Open Questions

- **`scope_type: subgraph`** 时 `scope_ref` 在 BKN 中引用何种实体（是否需 subgraph 独立类型）？
- **正文 Scope 与 frontmatter 双写**：以谁为准，或禁止双写只保留一处。
- **`derived` / `composite` 的字段级 schema**：模板已预留子树及对其它 `metric.id` 的引用占位；与 OpenAPI / 持久化形态的 **一一映射** 待 API 稳定后写入 SPEC（本设计已假定 **同一 endpoint**，不因 kind 分路由）。

---

## References

- `docs/SPECIFICATION.md` — 行动类型触发条件、对象 Logic Properties（待修订）。
- `kweaver-core/.../bkn-metrics.yaml` — Metric 资源与计算公式结构。
- `kweaver-core/.../bkn-backend/server` — 校验与持久化行为。

---

**文档状态**：设计草案；**未随本文档自动修改运行时行为**。提交与否由维护者自行 `git add` / `commit`。
