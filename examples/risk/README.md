# Risk Design (Tag-Based)

本示例展示基于 **tag** 的风险相关定义与 Action 的 **动态 risk 属性**（allow / not_allow）。

## 设计要点

1. **Risk 作为类别**：通过 `- **Tags**: risk` 标记与风险相关的实体与关系，供 AI 应用识别与筛选。不单独定义 risk 实体类型，而是用 tag 指定“风险相关”的定义。
2. **Action 的 risk 属性**：Action 拥有运行时/计算属性 `risk`，取值仅 `allow` | `not_allow`，由 **SDK 风险评估模块** 根据当前场景与带 `risk` tag 的实体/关系数据计算得出，不写入 BKN 文件。
3. **风险评估模块**：SDK 提供 `bkn.risk.evaluate_risk(network, action_id, context)`，在给定场景（context）下判断某 action 是否允许执行。

## 目录结构

```
examples/risk/
├── README.md           # 本说明
├── risk-fragment.bkn   # 带 Tags: risk 的实体/关系示例
└── scripts/            # 可选：演示调用 SDK 风险评估接口
    └── eval_risk_demo.py
```

## 使用 SDK 风险评估

```python
from bkn.loader import load_network
from bkn.risk import evaluate_risk

network = load_network("examples/risk/risk-fragment.bkn")
result = evaluate_risk(network, action_id="restore_from_backup", context={"scenario_id": "prod_db"})
# result == "allow" or "not_allow"
```

## 与旧版示例的关系

旧版静态风险知识（scenario / action_option / risk_statement 等）已移至 `examples/risk_old/`，可作为历史参考。新设计用 tag 标记风险相关定义，由 SDK 统一计算 Action 的 risk 属性。
