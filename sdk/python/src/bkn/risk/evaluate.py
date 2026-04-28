# Copyright The kweaver.ai Authors.
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

"""Evaluate whether an action is allowed in a given scenario based on risk-tagged knowledge."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from bkn.models import BknNetwork


ALLOW = "allow"
NOT_ALLOW = "not_allow"
UNKNOWN = "unknown"


@dataclass
class RiskResult:
    """Structured output of risk evaluation."""

    decision: str  # "allow" | "not_allow" | "unknown"
    risk_level: int | None = None  # 0~5 recommended; None when unknown
    reason: str = ""

    def __str__(self) -> str:
        return self.decision  # backward compatibility: print/compare decision


class RiskEvaluator(Protocol):
    """Protocol for a risk evaluation function. Users may implement this for custom logic."""

    def __call__(
        self,
        network: BknNetwork,
        action_id: str,
        context: dict[str, Any],
        **kwargs: Any,
    ) -> RiskResult:
        """Return RiskResult with decision, risk_level, and reason."""
        ...


def _to_int(v: Any) -> int | None:
    """Convert value to int if possible; return None otherwise."""
    if v is None:
        return None
    if isinstance(v, int):
        return v
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def evaluate_risk(
    network: BknNetwork,
    action_id: str,
    context: dict[str, Any],
    risk_rules: list[dict[str, Any]] | None = None,
    evaluator: RiskEvaluator | None = None,
) -> RiskResult:
    """
    Compute whether the given action is allowed in the current context (e.g. scenario).

    Built-in implementation: uses instance data (risk_rules) only; definitions tagged
    with reserved `__risk__` in the network identify risk-related schema.

    Three-state result:
      - "not_allow": at least one matching rule has allowed=False → block.
      - "allow": at least one matching rule exists and all have allowed=True → permit.
      - "unknown": no risk_rules provided or no rule matches → insufficient info.

    Users may inject a custom evaluator for their own risk logic.

    Args:
        network: Loaded BKN network (reserved for API consistency / future use).
        action_id: Action ID to evaluate.
        context: Context for the evaluation, e.g. {"scenario_id": "sec_t_01"}.
        risk_rules: Optional list of rule dicts with keys scenario_id, action_id, allowed,
            risk_level, reason.
        evaluator: Optional custom evaluator. If provided, it is called instead of the
            built-in logic.

    Returns:
        RiskResult with decision, risk_level, and reason.
    """
    if evaluator is not None:
        return evaluator(network, action_id, context, risk_rules=risk_rules)

    if not risk_rules:
        return RiskResult(decision=UNKNOWN)

    scenario_id = (context or {}).get("scenario_id")
    matched_rules = []
    for rule in risk_rules:
        if rule.get("action_id") != action_id:
            continue
        if scenario_id is not None and rule.get("scenario_id") != scenario_id:
            continue
        matched_rules.append(rule)

    if not matched_rules:
        return RiskResult(decision=UNKNOWN)

    # not_allow priority: take first rule with allowed=False
    for rule in matched_rules:
        if rule.get("allowed") is False:
            return RiskResult(
                decision=NOT_ALLOW,
                risk_level=_to_int(rule.get("risk_level")),
                reason=rule.get("reason", ""),
            )

    # all allow: take highest risk_level
    best = max(matched_rules, key=lambda r: _to_int(r.get("risk_level")) or 0)
    return RiskResult(
        decision=ALLOW,
        risk_level=_to_int(best.get("risk_level")),
        reason=best.get("reason", ""),
    )