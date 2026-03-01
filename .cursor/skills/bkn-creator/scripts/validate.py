#!/usr/bin/env python3
"""Validate BKN file(s) - load and print summary. Run from repo root."""

import sys
from pathlib import Path

try:
    from bkn import load_network
except ImportError:
    print("bkn not installed. Run: pip install -e sdk/python", file=sys.stderr)
    sys.exit(1)


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python validate.py <path>", file=sys.stderr)
        print("  path: .bkn file or network index (e.g. examples/k8s-modular/index.bkn)", file=sys.stderr)
        return 1
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        return 1
    try:
        network = load_network(path)
        fm = network.root.frontmatter
        print(f"type: {fm.type} id: {fm.id} name: {fm.name}")
        print(f"entities: {len(network.all_entities)} relations: {len(network.all_relations)} actions: {len(network.all_actions)}")
        return 0
    except Exception as e:
        print(f"Validation failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
