# BKN Python SDK

解析、校验与转换 [BKN 业务知识网络](../../docs/SPECIFICATION.md) 文件。

- **English** [README.md](README.md)

## 安装

```bash
# 从仓库根目录
cd sdk/python
pip install -e .

# 或指定路径
pip install -e path/to/bkn-specification/sdk/python

# 含 kweaver API 调用支持
pip install -e ".[api]"
```

要求 Python 3.9+。

## 用法

### 1. 解析单个文件

```python
from bkn import load

doc = load("examples/supplychain-hd/entities.bkn")
print(doc.frontmatter.type)   # fragment
print(len(doc.entities))      # 12
for e in doc.entities:
    print(e.id, e.name, len(e.data_properties), "个属性")
```

### 2. 加载网络（含 includes）

根文件通过 `includes` 引用子文件，`load_network` 会递归解析：

```python
from bkn import load_network

network = load_network("examples/supplychain-hd/supplychain.bkn")

print(network.root.frontmatter.name)   # HD供应链业务知识网络_v2
print(len(network.all_entities))      # 12
print(len(network.all_relations))     # 14
print(len(network.all_actions))       # 0
```

### 3. 转换到 kweaver JSON

将 BKN 模型转为 ontology-manager API（见 `ref/ontology_import_openapi_v2.json`）所需 JSON：

```python
from bkn import load_network
from bkn.transformers import KweaverTransformer

network = load_network("examples/supplychain-hd/supplychain.bkn")

transformer = KweaverTransformer(
    branch="main",
    base_version="",
    id_prefix="supplychain_",   # 实体/关系 ID 前缀，如 po -> supplychain_po
)

# 获取 JSON 字典
payload = transformer.to_json(network)
# payload["knowledge_network"]  - 创建知识网络请求体
# payload["object_types"]       - 对象类（实体）列表
# payload["relation_types"]    - 关系类列表

# 或写入文件
transformer.to_files(network, "output/")
# 生成: output/knowledge_network.json, object_types.json, relation_types.json
```

### 4. 通过 API 导入到 kweaver

将 BKN 网络直接导入到 kweaver ontology-manager。需要 `pip install -e ".[api]"`。

两种 API 模式：**内部**（默认，无 token）和**外部**（Bearer token）。

**内部 API**（集群内，仅 account headers）：
```python
from bkn import load_network
from bkn.transformers import KweaverClient, KweaverTransformer

network = load_network("examples/supplychain-hd/supplychain.bkn")
client = KweaverClient(
    base_url="http://ontology-manager-svc:13014",  # 或 KWEAVER_BASE_URL
    account_id="your_account_id",
    account_type="your_account_type",
    business_domain="your_domain_id",
    internal=True,  # 默认
)
transformer = KweaverTransformer(id_prefix="supplychain_")
result = client.import_network(network, transformer)
```

**外部 API**（Bearer token）：
```python
client = KweaverClient(
    base_url="https://your-gateway/api",
    token="your_bearer_token",  # 或 KWEAVER_TOKEN
    account_id="your_account_id",
    account_type="your_account_type",
    business_domain="your_domain_id",
    internal=False,
)
result = client.import_network(network, transformer)
# result.knowledge_network_id   -> 创建的知识网络 ID
# result.object_types_created   -> 创建的对象类数量
# result.relation_types_created -> 创建的关系类数量
# result.errors                 -> 错误列表（如有）
# result.success                 -> 无错误时为 True
```

仅转换不调 API 的 dry_run 模式：

```python
result = client.import_network(network, transformer, dry_run=True)
```

### 5. 从字符串解析

```python
from bkn import parse, parse_frontmatter, parse_body

text = """
---
type: entity
id: my_entity
name: My Entity
---

## Entity: my_entity
**My Entity** - 示例实体

### Data Source
| Type | ID | Name |
|------|-----|------|
| data_view | 123 | my_view |

### Data Properties
| Property | Display Name | Type | Primary Key | Display Key |
|----------|--------------|------|:-----------:|:-----------:|
| id | ID | int64 | YES | |
| name | 名称 | VARCHAR | | YES |
"""
doc = parse(text)
```

### 6. 访问实体与关系结构

```python
entity = network.all_entities[0]
print(entity.data_source.type, entity.data_source.id)
for dp in entity.data_properties:
    print(dp.property, dp.type, dp.primary_key)
for po in entity.property_overrides:
    print(po.property, po.index_config)   # fulltext(standard) + vector(id)

relation = network.all_relations[0]
ep = relation.endpoints[0]
print(ep.source, "->", ep.target, ep.type)
for mr in relation.mapping_rules:
    print(mr.source_property, "->", mr.target_property)
```

### 7. 风险评估

在 BKN 中带 **`risk`** 标签的实体与关系参与风险计算。Action 模型拥有运行时/计算属性 **`risk`**（取值 `allow` | `not_allow`），由风险评估模块根据当前场景与带 risk 标签的知识计算得出。

```python
from bkn import load_network, evaluate_risk

network = load_network("examples/risk/risk-fragment.bkn")
# 无规则数据时默认返回 allow（宽松）
result = evaluate_risk(network, "restore_from_backup", {"scenario_id": "prod_db"})
# result == "allow"

# 有实例数据（如图库或 API）时传入 risk_rules
rules = [
    {"scenario_id": "prod_db", "action_id": "restore_from_backup", "allowed": False},
]
result = evaluate_risk(network, "restore_from_backup", {"scenario_id": "prod_db"}, risk_rules=rules)
# result == "not_allow"
```

- **标签**：在 BKN 中为风险相关的实体/关系定义增加 `- **Tags**: risk`，AI 应用可按该标签筛选。
- **Action.risk**：`Action` 数据类有 `risk` 字段（默认空）；需要计算值时调用 `evaluate_risk()` 并赋给该字段。
- **完整评估**：SDK 无实例数据时 `evaluate_risk` 默认返回 `"allow"`；可传入 `risk_rules`（含 `scenario_id`、`action_id`、`allowed` 的字典列表）以根据数据源得到 allow/not_allow。

## 模块说明

| 模块 | 说明 |
|------|------|
| `bkn.models` | 数据模型：BknDocument、Entity、Relation、Action、DataProperty、PropertyOverride 等 |
| `bkn.parser` | 解析：parse()、parse_frontmatter()、parse_body()，支持中英文表头 |
| `bkn.loader` | 加载：load(path)、load_network(root_path)，自动解析 includes |
| `bkn.risk` | 风险评估：evaluate_risk(network, action_id, context, risk_rules?) -> "allow" \| "not_allow" |
| `bkn.transformers.base` | 抽象基类 `Transformer`，定义 `to_json()` 和 `to_files()` 接口 |
| `bkn.transformers.kweaver` | KweaverTransformer、KweaverClient；输出 kweaver 导入 JSON |

## KweaverTransformer 参数

| 参数 | 说明 | 默认 |
|------|------|------|
| `branch` | 分支名 | `"main"` |
| `base_version` | 基础版本 | `""` |
| `id_prefix` | 实体/关系 ID 前缀（如 `supplychain_` 使 `po` 变为 `supplychain_po`） | `""` |

## 测试

```bash
cd sdk/python
pip install -e ".[dev]"
python -m pytest tests/ -v
```
