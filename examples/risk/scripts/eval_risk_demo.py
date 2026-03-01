#!/usr/bin/env python3
"""
Demo: call SDK risk assessment to get allow/not_allow for an action in a given context.
Usage (from repo root):
  python examples/risk/scripts/eval_risk_demo.py
  python examples/risk/scripts/eval_risk_demo.py --action restore_from_backup --scenario prod_db
"""
from __future__ import annotations

import argparse
from pathlib import Path

# Fragment path: examples/risk/risk-fragment.bkn (relative to repo root)
REPO_ROOT = Path(__file__).resolve().parents[3]
FRAGMENT_PATH = REPO_ROOT / "examples" / "risk" / "risk-fragment.bkn"


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate risk for an action in a scenario")
    parser.add_argument("--action", default="restore_from_backup", help="Action ID")
    parser.add_argument("--scenario", default="prod_db", help="Scenario ID (context)")
    parser.add_argument("--bkn", type=Path, default=FRAGMENT_PATH, help="Path to BKN fragment/network")
    args = parser.parse_args()

    from bkn.loader import load_network
    from bkn.risk import evaluate_risk

    network = load_network(str(args.bkn))
    context = {"scenario_id": args.scenario}
    result = evaluate_risk(network, args.action, context)
    print(f"action={args.action} scenario={args.scenario} -> risk={result}")


if __name__ == "__main__":
    main()
