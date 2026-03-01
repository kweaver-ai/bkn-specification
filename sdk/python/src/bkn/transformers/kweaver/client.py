"""Kweaver API client for importing BKN networks."""

from __future__ import annotations

import json
import os
from typing import Any, Optional

from bkn.models import BknNetwork

from bkn.transformers.kweaver.types import ImportResult, KweaverImportError
from bkn.transformers.kweaver.transformer import KweaverTransformer

_API_PREFIX_INTERNAL = "/api/ontology-manager/in/v1"
_API_PREFIX_EXTERNAL = "/api/ontology-manager/v1"

_ENV_BASE_URL = "KWEAVER_BASE_URL"
_ENV_TOKEN = "KWEAVER_TOKEN"


class KweaverClient:
    """Client for importing BKN models into kweaver via ontology-manager API.

    Requires the `requests` library. Install with: pip install bkn[api]

    Supports two API modes:
    - Internal (internal=True): /api/ontology-manager/in/v1, no Authorization,
      requires account_id + account_type headers.
    - External (internal=False): /api/ontology-manager/v1, Bearer token required.

    Args:
        base_url: Base URL (falls back to KWEAVER_BASE_URL env var).
        token: Bearer token for external API (falls back to KWEAVER_TOKEN env var).
        account_id: Value for x-account-id header (required for internal).
        account_type: Value for x-account-type header (required for internal).
        business_domain: Value for x-business-domain header.
        internal: If True, use internal API (no token); if False, use external (token required).
        timeout: Request timeout in seconds (default 30).
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
        account_id: str = "",
        account_type: str = "",
        business_domain: str = "",
        internal: bool = True,
        timeout: int = 30,
    ) -> None:
        resolved_base_url = base_url or os.environ.get(_ENV_BASE_URL, "")
        resolved_token = token or os.environ.get(_ENV_TOKEN, "")
        if not resolved_base_url:
            raise KweaverImportError(
                f"base_url is required (pass it directly or set {_ENV_BASE_URL})"
            )
        if internal:
            if not account_id or not account_type:
                raise KweaverImportError(
                    "account_id and account_type are required for internal API"
                )
            self._api_prefix = _API_PREFIX_INTERNAL
            headers = {
                "Content-Type": "application/json",
                "x-account-id": account_id,
                "x-account-type": account_type,
                "x-business-domain": business_domain,
            }
        else:
            if not resolved_token:
                raise KweaverImportError(
                    f"token is required for external API (pass it or set {_ENV_TOKEN})"
                )
            self._api_prefix = _API_PREFIX_EXTERNAL
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {resolved_token}",
                "x-account-id": account_id,
                "x-account-type": account_type,
                "x-business-domain": business_domain,
            }
        self.base_url = resolved_base_url.rstrip("/")
        self.timeout = timeout
        self._headers = headers

    def _request(self, method: str, path: str, json_body: Any = None) -> Any:
        """Send HTTP request and return JSON body. Raises KweaverImportError on failure."""
        try:
            import requests
        except ImportError as e:
            raise KweaverImportError(
                "requests library required for API calls. Install with: pip install bkn[api]"
            ) from e

        url = f"{self.base_url}{path}"
        resp = requests.request(
            method=method,
            url=url,
            headers=self._headers,
            json=json_body,
            timeout=self.timeout,
        )

        if not (200 <= resp.status_code < 300):
            try:
                err_body = resp.json()
                msg = err_body.get("error", resp.text) or resp.text
            except Exception:
                msg = resp.text
            raise KweaverImportError(
                f"kweaver API error: {msg}",
                status_code=resp.status_code,
                response_text=resp.text,
            )

        if not resp.content:
            return None
        return resp.json()

    def create_knowledge_network(self, payload: dict[str, Any]) -> str:
        """Create a knowledge network and return its ID."""
        path = f"{self._api_prefix}/knowledge-networks"
        data = self._request("POST", path, payload)
        if isinstance(data, list) and len(data) > 0 and "id" in data[0]:
            return str(data[0]["id"])
        if isinstance(data, dict) and "id" in data:
            return str(data["id"])
        raise KweaverImportError(
            "createKnowledgeNetwork response missing id",
            response_text=json.dumps(data) if data else "",
        )

    def create_object_types(
        self, knowledge_network_id: str, object_types: list[dict[str, Any]]
    ) -> tuple[int, list[str]]:
        """Create object types in the given knowledge network. Returns (created_count, errors)."""
        if not object_types:
            return 0, []
        path = f"{self._api_prefix}/knowledge-networks/{knowledge_network_id}/object-types"
        data = self._request("POST", path, object_types)
        if isinstance(data, dict):
            return data.get("created_count", 0), data.get("errors", [])
        return 0, []

    def create_relation_types(
        self,
        knowledge_network_id: str,
        relation_types: list[dict[str, Any]],
    ) -> tuple[int, list[str]]:
        """Create relation types in the given knowledge network. Returns (created_count, errors)."""
        if not relation_types:
            return 0, []
        path = f"{self._api_prefix}/knowledge-networks/{knowledge_network_id}/relation-types"
        data = self._request("POST", path, relation_types)
        if isinstance(data, dict):
            return data.get("created_count", 0), data.get("errors", [])
        return 0, []

    def import_network(
        self,
        network: BknNetwork,
        transformer: Optional[KweaverTransformer] = None,
        dry_run: bool = False,
    ) -> ImportResult:
        """Import a BKN network into kweaver.

        Args:
            network: The BKN network to import.
            transformer: Transformer to use. If None, creates a default KweaverTransformer.
            dry_run: If True, only transform to JSON without calling the API.

        Returns:
            ImportResult with knowledge_network_id, counts, and any errors.
        """
        t = transformer or KweaverTransformer()
        payload = t.to_json(network)

        result = ImportResult()
        if dry_run:
            return result

        kn_payload = payload["knowledge_network"]
        kn_id = self.create_knowledge_network(kn_payload)
        result.knowledge_network_id = kn_id

        ot_created, ot_errors = self.create_object_types(
            kn_id, payload["object_types"]
        )
        result.object_types_created = ot_created
        result.errors.extend(ot_errors)

        rt_created, rt_errors = self.create_relation_types(
            kn_id, payload["relation_types"]
        )
        result.relation_types_created = rt_created
        result.errors.extend(rt_errors)

        return result
