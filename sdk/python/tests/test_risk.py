# Copyright The kweaver.ai Authors.
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

"""Tests for the risk assessment module."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
EXAMPLES_DIR = REPO_ROOT / "examples"


@pytest.fixture
def network():
    """Load k8s-network as the test network for risk evaluation."""
    path = EXAMPLES_DIR / "k8s-network"
    if not path.exists():
        pytest.skip("examples/k8s-network not found")
    from bkn.loader import load_network
    return load_network(path)


def test_evaluate_risk_no_rules_returns_unknown(network):
    """With no risk_rules, result is unknown (insufficient info)."""
    from bkn.risk import evaluate_risk
    result = evaluate_risk(network, "any_action", {"scenario_id": "any"})
    assert result.decision == "unknown"
    assert result.risk_level is None
    assert result.reason == ""
    result2 = evaluate_risk(network, "restart_erp", {})
    assert result2.decision == "unknown"


def test_evaluate_risk_not_allow_when_rule_forbids(network):
    """When a rule has allowed=False for the given scenario+action, return not_allow."""
    from bkn.risk import evaluate_risk
    rules = [
        {"scenario_id": "sec_t_01", "action_id": "restart_erp", "allowed": False, "risk_level": 5, "reason": "blocked"},
    ]
    result = evaluate_risk(
        network, "restart_erp", {"scenario_id": "sec_t_01"}, risk_rules=rules
    )
    assert result.decision == "not_allow"
    assert result.risk_level == 5
    assert "blocked" in result.reason


def test_evaluate_risk_allow_when_rule_allows(network):
    """When a rule has allowed=True, return allow."""
    from bkn.risk import evaluate_risk
    rules = [
        {"scenario_id": "sec_c_02", "action_id": "batch_restart_nodes", "allowed": True, "risk_level": 2, "reason": "throttle"},
    ]
    result = evaluate_risk(
        network, "batch_restart_nodes", {"scenario_id": "sec_c_02"}, risk_rules=rules
    )
    assert result.decision == "allow"
    assert result.risk_level == 2
    assert "throttle" in result.reason


def test_evaluate_risk_no_match_returns_unknown(network):
    """When no rule matches the scenario+action, return unknown."""
    from bkn.risk import evaluate_risk
    rules = [
        {"scenario_id": "other_scenario", "action_id": "other_action", "allowed": False},
    ]
    result = evaluate_risk(
        network, "restart_erp", {"scenario_id": "sec_t_01"}, risk_rules=rules
    )
    assert result.decision == "unknown"


def test_evaluate_risk_no_scenario_matches_by_action_only(network):
    """Without scenario_id in context, rules match by action_id alone."""
    from bkn.risk import evaluate_risk
    rules = [
        {"action_id": "grant_root_admin", "allowed": False, "risk_level": 5},
    ]
    result = evaluate_risk(network, "grant_root_admin", {}, risk_rules=rules)
    assert result.decision == "not_allow"
    assert result.risk_level == 5
    result2 = evaluate_risk(network, "grant_root_admin", None, risk_rules=rules)
    assert result2.decision == "not_allow"


def test_evaluate_risk_no_scenario_allow(network):
    """Global rule with allowed=True, no scenario filtering."""
    from bkn.risk import evaluate_risk
    rules = [
        {"action_id": "query_sensitive_data", "allowed": True, "risk_level": 2},
    ]
    result = evaluate_risk(network, "query_sensitive_data", {}, risk_rules=rules)
    assert result.decision == "allow"
    assert result.risk_level == 2


def test_evaluate_risk_scenario_filters_rules(network):
    """With scenario_id in context, only matching rules participate."""
    from bkn.risk import evaluate_risk
    rules = [
        {"scenario_id": "sec_t_01", "action_id": "restart_erp", "allowed": False},
    ]
    result = evaluate_risk(
        network, "restart_erp", {"scenario_id": "sec_c_02"}, risk_rules=rules
    )
    assert result.decision == "unknown"


def test_evaluate_risk_custom_evaluator(network):
    """Custom evaluator is called when provided."""
    from bkn.risk import RiskResult, evaluate_risk

    def my_evaluator(network, action_id, context, risk_rules=None, **kwargs):
        if action_id == "grant_root_admin":
            return RiskResult(decision="not_allow", risk_level=5, reason="全局禁止提权")
        return RiskResult(decision="unknown")

    result = evaluate_risk(network, "grant_root_admin", {}, evaluator=my_evaluator)
    assert result.decision == "not_allow"
    assert result.risk_level == 5
    assert "全局禁止提权" in result.reason

    result2 = evaluate_risk(network, "other_action", {}, evaluator=my_evaluator)
    assert result2.decision == "unknown"


def test_risk_result_str_backward_compat(network):
    """RiskResult.__str__ returns decision for backward compatibility."""
    from bkn.risk import RiskResult
    r = RiskResult(decision="allow", risk_level=2, reason="ok")
    assert str(r) == "allow"


def test_risk_result_fields():
    """RiskResult has expected fields."""
    from bkn.risk import RiskResult
    r = RiskResult(decision="allow", risk_level=3, reason="ok")
    assert r.decision == "allow"
    assert r.risk_level == 3
    assert r.reason == "ok"