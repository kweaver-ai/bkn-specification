#!/usr/bin/env python3
"""Transform BKN network to kweaver JSON files. Run from repo root."""

import argparse
import sys
from pathlib import Path

try:
    from bkn import load_network
    from bkn.transformers import KweaverTransformer
except ImportError:
    print("bkn not installed. Run: pip install -e sdk/python", file=sys.stderr)
    sys.exit(1)


def main() -> int:
    p = argparse.ArgumentParser(description="Transform BKN to kweaver JSON files")
    p.add_argument("path", help="Path to .bkn file or network index (e.g. examples/k8s-modular/index.bkn)")
    p.add_argument("-o", "--output", default="output", help="Output directory (default: output)")
    p.add_argument("--id-prefix", default="", help="ID prefix for entity/relation IDs")
    args = p.parse_args()
    path = Path(args.path)
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        return 1
    try:
        network = load_network(path)
        transformer = KweaverTransformer(id_prefix=args.id_prefix)
        created = transformer.to_files(network, args.output)
        for f in created:
            print(f"Written: {f}")
        return 0
    except Exception as e:
        print(f"Transform failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
