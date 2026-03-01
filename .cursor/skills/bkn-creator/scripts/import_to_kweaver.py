#!/usr/bin/env python3
"""Import BKN network to kweaver via API. Run from repo root. Requires pip install -e 'sdk/python[api]'."""

import argparse
import os
import sys
from pathlib import Path

try:
    from bkn import load_network
    from bkn.transformers import KweaverClient, KweaverTransformer
except ImportError:
    print("bkn[api] not installed. Run: pip install -e 'sdk/python[api]'", file=sys.stderr)
    sys.exit(1)


def main() -> int:
    p = argparse.ArgumentParser(description="Import BKN network to kweaver API")
    p.add_argument("path", help="Path to .bkn file or network index")
    p.add_argument("--external", action="store_true", help="External API (Bearer token); default is internal (account headers)")
    p.add_argument("--base-url", help="Base URL (or set KWEAVER_BASE_URL)")
    p.add_argument("--token", help="Bearer token for external mode (or set KWEAVER_TOKEN)")
    p.add_argument("--account-id", default="", help="Required for internal mode")
    p.add_argument("--account-type", default="", help="Required for internal mode")
    p.add_argument("--business-domain", default="", help="Business domain header")
    p.add_argument("--id-prefix", default="", help="ID prefix for entity/relation IDs")
    p.add_argument("--dry-run", action="store_true", help="Transform only, do not call API")
    args = p.parse_args()

    internal = not args.external
    base_url = args.base_url or os.environ.get("KWEAVER_BASE_URL")
    token = args.token or os.environ.get("KWEAVER_TOKEN")

    path = Path(args.path)
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        return 1

    try:
        network = load_network(path)
        transformer = KweaverTransformer(id_prefix=args.id_prefix)
        client = KweaverClient(
            base_url=base_url or "http://ontology-manager-svc:13014",
            token=token,
            account_id=args.account_id,
            account_type=args.account_type,
            business_domain=args.business_domain,
            internal=internal,
        )
        result = client.import_network(network, transformer, dry_run=args.dry_run)
        if args.dry_run:
            print("Dry-run OK (no API calls)")
        else:
            print(f"kn_id: {result.knowledge_network_id}")
            print(f"object_types_created: {result.object_types_created}")
            print(f"relation_types_created: {result.relation_types_created}")
            if result.errors:
                for e in result.errors:
                    print(f"error: {e}")
        return 0 if result.success else 1
    except Exception as e:
        print(f"Import failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
