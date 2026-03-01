# BKN Python SDK

Parse, validate, and transform [BKN (Business Knowledge Network)](../../docs/SPECIFICATION.md) files.

- **中文** [README.zh.md](README.zh.md)

## Install

```bash
# From repo root
cd sdk/python
pip install -e .

# Or with path
pip install -e path/to/bkn-specification/sdk/python

# With kweaver API support
pip install -e ".[api]"
```

Requires Python 3.9+.

## Usage

### 1. Parse a single file

```python
from bkn import load

doc = load("examples/supplychain-hd/entities.bkn")
print(doc.frontmatter.type)   # fragment
print(len(doc.entities))      # 12
for e in doc.entities:
    print(e.id, e.name, len(e.data_properties), "properties")
```

### 2. Load a network (with includes)

The root file references sub-files via `includes`; `load_network` resolves them recursively:

```python
from bkn import load_network

network = load_network("examples/supplychain-hd/supplychain.bkn")

print(network.root.frontmatter.name)   # HD供应链业务知识网络_v2
print(len(network.all_entities))      # 12
print(len(network.all_relations))     # 14
print(len(network.all_actions))       # 0
```

### 3. Transform to kweaver JSON

Convert BKN models to JSON for ontology-manager API (see `ref/ontology_import_openapi_v2.json`):

```python
from bkn import load_network
from bkn.transformers import KweaverTransformer

network = load_network("examples/supplychain-hd/supplychain.bkn")

transformer = KweaverTransformer(
    branch="main",
    base_version="",
    id_prefix="supplychain_",   # Entity/relation ID prefix, e.g. po -> supplychain_po
)

# Get JSON dict
payload = transformer.to_json(network)
# payload["knowledge_network"]  - Create knowledge network request body
# payload["object_types"]      - Object types (entities) list
# payload["relation_types"]    - Relation types list

# Or write to files
transformer.to_files(network, "output/")
# Creates: output/knowledge_network.json, object_types.json, relation_types.json
```

### 4. Import to kweaver via API

Import a BKN network directly to kweaver ontology-manager. Requires `pip install -e ".[api]"`.

Two API modes: **internal** (default, no token) and **external** (Bearer token).

**Internal API** (inside cluster, account headers only):
```python
from bkn import load_network
from bkn.transformers import KweaverClient, KweaverTransformer

network = load_network("examples/supplychain-hd/supplychain.bkn")
client = KweaverClient(
    base_url="http://ontology-manager-svc:13014",  # or KWEAVER_BASE_URL
    account_id="your_account_id",
    account_type="your_account_type",
    business_domain="your_domain_id",
    internal=True,  # default
)
transformer = KweaverTransformer(id_prefix="supplychain_")
result = client.import_network(network, transformer)
```

**External API** (Bearer token):
```python
client = KweaverClient(
    base_url="https://your-gateway/api",
    token="your_bearer_token",  # or KWEAVER_TOKEN
    account_id="your_account_id",
    account_type="your_account_type",
    business_domain="your_domain_id",
    internal=False,
)
result = client.import_network(network, transformer)
# result.knowledge_network_id   -> created knowledge network ID
# result.object_types_created   -> number of object types created
# result.relation_types_created -> number of relation types created
# result.errors                 -> list of errors (if any)
# result.success                -> True if no errors
```

Dry-run mode (transform only, no API calls):

```python
result = client.import_network(network, transformer, dry_run=True)
```

### 5. Parse from string

```python
from bkn import parse, parse_frontmatter, parse_body

text = """
---
type: entity
id: my_entity
name: My Entity
---

## Entity: my_entity
**My Entity** - Example entity

### Data Source
| Type | ID | Name |
|------|-----|------|
| data_view | 123 | my_view |

### Data Properties
| Property | Display Name | Type | Primary Key | Display Key |
|----------|--------------|------|:-----------:|:-----------:|
| id | ID | int64 | YES | |
| name | Name | VARCHAR | | YES |
"""
doc = parse(text)
```

### 6. Access entity and relation structure

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

### 7. Risk assessment

Entities and relations tagged with **`risk`** in BKN participate in risk evaluation. The Action model has a runtime/computed property **`risk`** (values `allow` | `not_allow`), filled by the risk assessment module based on the current scenario and risk-tagged knowledge.

```python
from bkn import load_network, evaluate_risk

network = load_network("examples/risk/risk-fragment.bkn")
# With no rule data, result is allow (permissive default)
result = evaluate_risk(network, "restore_from_backup", {"scenario_id": "prod_db"})
# result == "allow"

# Pass risk_rules when you have instance data (e.g. from a graph or API)
rules = [
    {"scenario_id": "prod_db", "action_id": "restore_from_backup", "allowed": False},
]
result = evaluate_risk(network, "restore_from_backup", {"scenario_id": "prod_db"}, risk_rules=rules)
# result == "not_allow"
```

- **Tagging**: In BKN, add `- **Tags**: risk` to entity/relation definitions that are risk-related; AI applications can filter by this tag.
- **Action.risk**: The `Action` dataclass has a `risk` field (empty by default); call `evaluate_risk()` and assign the result when you need the computed value.
- **Full evaluation**: When the SDK has no instance data, `evaluate_risk` returns `"allow"` by default; pass `risk_rules` (list of dicts with `scenario_id`, `action_id`, `allowed`) to get allow/not_allow from your data source.

## Modules

| Module | Description |
|--------|-------------|
| `bkn.models` | Dataclass models: BknDocument, Entity, Relation, Action, DataProperty, PropertyOverride, etc. |
| `bkn.parser` | Parsing: parse(), parse_frontmatter(), parse_body(); supports EN/CN table headers |
| `bkn.loader` | Loading: load(path), load_network(root_path); auto-resolves includes |
| `bkn.risk` | Risk assessment: evaluate_risk(network, action_id, context, risk_rules?) -> "allow" \| "not_allow" |
| `bkn.transformers.base` | Abstract `Transformer` base class with `to_json()` and `to_files()` interface |
| `bkn.transformers.kweaver` | KweaverTransformer, KweaverClient; outputs kweaver import JSON |

## KweaverTransformer parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `branch` | Branch name | `"main"` |
| `base_version` | Base version string | `""` |
| `id_prefix` | Entity/relation ID prefix (e.g. `supplychain_` makes `po` -> `supplychain_po`) | `""` |

## Testing

```bash
cd sdk/python
pip install -e ".[dev]"
python -m pytest tests/ -v
```
