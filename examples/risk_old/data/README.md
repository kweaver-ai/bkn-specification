# Risk Data Extraction

本目录包含从 `examples/risk/cases/` 下案例文件中抽取的结构化数据，按 [risk-fragment.bkn](../risk-fragment.bkn) 定义的实体和关系拆分。

## 数据文件

| 文件 | 说明 | BKN 映射 |
|------|------|----------|
| `scenario.csv` | 风险发生的场景 | Entity: scenario |
| `action_option.csv` | 风险发生后可执行的动作选项 | Entity: action_option |
| `risk.csv` | 静态风险类型定义 | Entity: risk |
| `risk_statement.csv` | 风险断言（场景 × 动作 × 风险） | Entity: risk_statement |
| `rs_under_scenario.csv` | risk_statement → scenario | Relation: rs_under_scenario |
| `rs_about_action.csv` | risk_statement → action_option | Relation: rs_about_action |
| `rs_asserts_risk.csv` | risk_statement → risk | Relation: rs_asserts_risk |

## 抽取来源

| 来源文件 | 抽取内容 |
|----------|----------|
| `风险表.xlsx` | 程序运行类、系统运维类的命令风险（允许/禁止操作及风险说明） |
| `PFMEA模板.xlsx` | 定时备份、云备份、磁带备份、公共管理类、其他模块的 FMEA 条目；实时&容灾仅 1 条 |
| `DFMEA模板.xlsx` | KVM数据备份评审、数据恢复评审、容灾接管评审 |
| `AnyBackup 7.0.1.0 风险声明文档.docx` | 各模块风险声明的段落文本 |

## 映射逻辑

### scenario (场景)

- **PFMEA/DFMEA**：从「模块」列 + 「风险检查点/潜在问题」生成场景，`primary_object` 为模块名，`category` 由文本语义推断
- **风险表**：从「类别」+「命令/操作范围」生成场景，`primary_object` 固定为 `backup_system`
- **docx**：从 Heading3 标题作为 `primary_object`，段落内容作为 `description`
- **category**：根据关键词映射到 `availability` / `integrity` / `security` / `performance` / `dependency` / `operator`

### action_option (动作选项)

- **PFMEA/DFMEA**：从「改善措施」/「设计改进」提取动作，空则用「应对{失效模式}」
- **风险表**：从「命令/操作范围」作为动作（触发风险的操作）
- **docx**：统一为「遵循产品说明操作」
- **action_type**：由文本推断 `failover` / `wait` / `restore` / `rollback` / `degrade` / `isolate` / `rebuild`
- **reversibility**：由操作性质推断 `reversible` / `partially_reversible` / `irreversible`

### risk (风险类型)

- **PFMEA/DFMEA**：从「潜在失效模式」+「潜在故障影响」
- **风险表**：从「风险说明」
- **docx**：从段落描述
- **risk_type**：由语义映射到 `data_loss` / `inconsistency` / `availability` / `security` / `compliance` / `financial` / `reputation`

### risk_statement (风险断言)

- 每行有效数据生成一条 risk_statement，通过 `scenario_id` / `action_id` / `risk_id` 关联三者
- **business_impact**：风险表用「风险等级」(极高→5, 高→4, 中→3, 低→2)；PFMEA/DFMEA 用「严重程度」1–9 映射到 1–5
- **likelihood_level**：PFMEA/DFMEA 的「出现频率/出现概率」映射到 1–5
- **status**：全部为 `active`
- **notes**：RPN、现有控制、起因等辅助信息

### ID 命名规则

- 风险表：`ops-{类别}-{行号}` / `ops-cmd-{行号}` / `ops-risk-{类型}-{行号}`
- PFMEA：`pfmea-{模块}-{行号}`，实时&容灾为 `pfmea-realtime-1`
- DFMEA：`dfmea-{功能}-{行号}`
- docx：`decl-{模块}-{序号}`

## 重新抽取

```bash
python examples/risk/scripts/extract_risk_data.py
```

依赖：`openpyxl`（xlsx）、`python-docx`（docx）。
