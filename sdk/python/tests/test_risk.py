"""Tests for the risk assessment module."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
RISK_FRAGMENT = REPO_ROOT / "examples" / "risk" / "risk-fragment.bkn"


@pytest.fixture
def network():
    """Load the risk-tagged fragment as a network (single doc, no includes)."""
    from bkn.loader import load_network
    return load_network(str(RISK_FRAGMENT))


def test_evaluate_risk_default_allow(network):
    """With no risk_rules, result is allow (permissive default)."""
    from bkn.risk import evaluate_risk
    assert evaluate_risk(network, "any_action", {"scenario_id": "any"}) == "allow"
    assert evaluate_risk(network, "restore_from_backup", {}) == "allow"


def test_evaluate_risk_not_allow_when_rule_forbids(network):
    """When a rule has allowed=False for the given scenario+action, return not_allow."""
    from bkn.risk import evaluate_risk
    rules = [
        {"scenario_id": "prod_db", "action_id": "restore_from_backup", "allowed": False},
    ]
    assert evaluate_risk(
        network, "restore_from_backup", {"scenario_id": "prod_db"}, risk_rules=rules
    ) == "not_allow"


def test_evaluate_risk_allow_when_rule_allows(network):
    """When a rule has allowed=True, return allow."""
    from bkn.risk import evaluate_risk
    rules = [
        {"scenario_id": "prod_db", "action_id": "restore_from_backup", "allowed": True},
    ]
    assert evaluate_risk(
        network, "restore_from_backup", {"scenario_id": "prod_db"}, risk_rules=rules
    ) == "allow"


def test_evaluate_risk_no_match_returns_allow(network):
    """When no rule matches the scenario+action, return allow."""
    from bkn.risk import evaluate_risk
    rules = [
        {"scenario_id": "other_scenario", "action_id": "other_action", "allowed": False},
    ]
    assert evaluate_risk(
        network, "restore_from_backup", {"scenario_id": "prod_db"}, risk_rules=rules
    ) == "allow"


def test_network_has_risk_tagged_entities(network):
    """The risk fragment defines entities with Tags: risk."""
    risk_entities = [e for e in network.all_entities if "risk" in (e.tags or [])]
    assert len(risk_entities) >= 1
    ids = [e.id for e in risk_entities]
    assert "risk_scenario" in ids or "risk_rule" in ids
