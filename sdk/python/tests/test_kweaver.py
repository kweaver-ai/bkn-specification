"""Tests for the kweaver transformer."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
EXAMPLES_DIR = REPO_ROOT / "docs" / "examples"

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bkn.loader import load_network
from bkn.transformers.kweaver import (
    ImportResult,
    KweaverClient,
    KweaverImportError,
    KweaverTransformer,
    _map_type,
    _parse_index_config,
)


# ---------------------------------------------------------------------------
# Index Config parsing
# ---------------------------------------------------------------------------

class TestIndexConfigParsing:
    def test_empty(self):
        cfg = _parse_index_config("")
        assert cfg["keyword_config"]["enabled"] is False
        assert cfg["fulltext_config"]["enabled"] is False
        assert cfg["vector_config"]["enabled"] is False

    def test_keyword_only(self):
        cfg = _parse_index_config("keyword")
        assert cfg["keyword_config"]["enabled"] is True
        assert cfg["keyword_config"]["ignore_above_len"] == 1024

    def test_keyword_with_len(self):
        cfg = _parse_index_config("keyword(2048)")
        assert cfg["keyword_config"]["enabled"] is True
        assert cfg["keyword_config"]["ignore_above_len"] == 2048

    def test_fulltext_with_analyzer(self):
        cfg = _parse_index_config("fulltext(standard)")
        assert cfg["fulltext_config"]["enabled"] is True
        assert cfg["fulltext_config"]["analyzer"] == "standard"

    def test_vector_with_model(self):
        cfg = _parse_index_config("vector(1951511856216674304)")
        assert cfg["vector_config"]["enabled"] is True
        assert cfg["vector_config"]["model_id"] == "1951511856216674304"

    def test_combined(self):
        cfg = _parse_index_config(
            "keyword(1024) + fulltext(standard) + vector(1951511856216674304)"
        )
        assert cfg["keyword_config"]["enabled"] is True
        assert cfg["fulltext_config"]["enabled"] is True
        assert cfg["fulltext_config"]["analyzer"] == "standard"
        assert cfg["vector_config"]["enabled"] is True
        assert cfg["vector_config"]["model_id"] == "1951511856216674304"

    def test_fulltext_plus_vector(self):
        cfg = _parse_index_config("fulltext(standard) + vector(1951511856216674304)")
        assert cfg["keyword_config"]["enabled"] is False
        assert cfg["fulltext_config"]["enabled"] is True
        assert cfg["vector_config"]["enabled"] is True


# ---------------------------------------------------------------------------
# Type mapping
# ---------------------------------------------------------------------------

class TestTypeMapping:
    def test_varchar(self):
        assert _map_type("VARCHAR") == "string"

    def test_int64(self):
        assert _map_type("int64") == "integer"

    def test_float64(self):
        assert _map_type("float64") == "float"

    def test_decimal(self):
        assert _map_type("decimal") == "decimal"

    def test_decimal_with_precision(self):
        assert _map_type("decimal(10,2)") == "decimal"

    def test_date(self):
        assert _map_type("DATE") == "date"

    def test_timestamp(self):
        assert _map_type("TIMESTAMP") == "timestamp"

    def test_empty(self):
        assert _map_type("") == "string"


# ---------------------------------------------------------------------------
# Supplychain network transformation
# ---------------------------------------------------------------------------

class TestSupplychainTransform:
    """Test transforming the supplychain-hd network to kweaver JSON."""

    @pytest.fixture
    def network(self):
        root_path = EXAMPLES_DIR / "supplychain-hd" / "supplychain.bkn"
        if not root_path.exists():
            pytest.skip(f"Example file not found: {root_path}")
        return load_network(root_path)

    @pytest.fixture
    def transformer(self):
        return KweaverTransformer(
            branch="main",
            base_version="",
            id_prefix="supplychain_hd0202_",
        )

    @pytest.fixture
    def payload(self, network, transformer):
        return transformer.to_json(network)

    def test_knowledge_network(self, payload):
        kn = payload["knowledge_network"]
        assert kn["name"] == "HD供应链业务知识网络_v2"
        assert kn["branch"] == "main"
        assert "供应链" in kn.get("tags", [])

    def test_object_types_count(self, payload):
        assert len(payload["object_types"]) == 12

    def test_relation_types_count(self, payload):
        assert len(payload["relation_types"]) == 14

    def test_po_object_type(self, payload):
        po = next(
            (ot for ot in payload["object_types"] if ot.get("id", "").endswith("_po")),
            None,
        )
        assert po is not None
        assert po["name"] == "采购订单"
        assert "primary_keys" in po
        assert len(po["primary_keys"]) >= 1
        assert po["display_key"] != ""
        assert len(po["data_properties"]) > 0

    def test_po_data_property_types(self, payload):
        po = next(ot for ot in payload["object_types"] if ot.get("id", "").endswith("_po"))
        type_set = {dp["type"] for dp in po["data_properties"]}
        assert "string" in type_set

    def test_relation_has_source_target(self, payload):
        for rt in payload["relation_types"]:
            assert "source_object_type_id" in rt
            assert "target_object_type_id" in rt

    def test_relation_mapping_rules(self, payload):
        product2bom = next(
            (rt for rt in payload["relation_types"] if "product2bom" in rt.get("id", "")),
            None,
        )
        assert product2bom is not None
        assert len(product2bom.get("mapping_rules", [])) >= 1
        rule = product2bom["mapping_rules"][0]
        assert "source_property" in rule
        assert "name" in rule["source_property"]

    def test_id_prefix_applied(self, payload):
        for ot in payload["object_types"]:
            assert ot["id"].startswith("supplychain_hd0202_")

    def test_to_files(self, network, transformer):
        with tempfile.TemporaryDirectory() as tmpdir:
            files = transformer.to_files(network, tmpdir)
            assert len(files) == 3
            for f in files:
                assert f.exists()
                data = json.loads(f.read_text(encoding="utf-8"))
                assert data is not None


# ---------------------------------------------------------------------------
# KweaverClient import
# ---------------------------------------------------------------------------

class TestKweaverClient:
    """Test KweaverClient with mocked requests."""

    @pytest.fixture
    def network(self):
        root_path = EXAMPLES_DIR / "supplychain-hd" / "supplychain.bkn"
        if not root_path.exists():
            pytest.skip(f"Example file not found: {root_path}")
        return load_network(root_path)

    @pytest.fixture
    def client(self):
        return KweaverClient(
            base_url="http://ontology-manager-svc:13014",
            account_id="test_account",
            account_type="test_type",
            business_domain="test_domain",
            internal=True,
        )

    def test_dry_run_returns_empty_result(self, client, network):
        """dry_run=True should only transform, not call API."""
        result = client.import_network(network, dry_run=True)
        assert isinstance(result, ImportResult)
        assert result.knowledge_network_id == ""
        assert result.object_types_created == 0
        assert result.relation_types_created == 0
        assert result.success

    def test_import_network_success(self, client, network):
        """Mock successful import returns expected result."""
        mock_responses = [
            # createKnowledgeNetwork -> [{"id": "kn_123"}]
            [{"id": "kn_123"}],
            # createObjectTypes -> {created_count: 12, errors: []}
            {"created_count": 12, "errors": []},
            # createRelationTypes -> {created_count: 14, errors: []}
            {"created_count": 14, "errors": []},
        ]
        call_idx = [0]

        def mock_request(*_args, **_kwargs):
            idx = call_idx[0]
            call_idx[0] += 1
            data = mock_responses[idx]

            class MockResponse:
                status_code = 201
                content = json.dumps(data).encode()
                text = json.dumps(data)

                def json(self):
                    return data

            return MockResponse()

        with patch("requests.request", side_effect=mock_request):
            result = client.import_network(network)
        assert result.knowledge_network_id == "kn_123"
        assert result.object_types_created == 12
        assert result.relation_types_created == 14
        assert result.success
        assert len(result.errors) == 0

    def test_import_network_api_error(self, client, network):
        """Non-2xx response raises KweaverImportError."""
        class MockErrorResponse:
            status_code = 400
            content = b'{"error":"bad request"}'
            text = '{"error":"bad request"}'

            def json(self):
                return {"error": "bad request"}

        with patch("requests.request", return_value=MockErrorResponse()):
            with pytest.raises(KweaverImportError) as exc_info:
                client.import_network(network)
        assert exc_info.value.status_code == 400
        assert "bad request" in str(exc_info.value)

    def test_create_knowledge_network_extracts_id(self, client):
        """create_knowledge_network returns id from array response."""
        class MockResponse:
            status_code = 201
            content = b'[{"id":"kn_abc"}]'

            def json(self):
                return [{"id": "kn_abc"}]

        with patch("requests.request", return_value=MockResponse()):
            kn_id = client.create_knowledge_network({"name": "test", "branch": "main", "base_branch": ""})
        assert kn_id == "kn_abc"

    def test_create_object_types_returns_count_and_errors(self, client):
        """create_object_types returns (created_count, errors)."""
        class MockResponse:
            status_code = 201
            content = b'{"created_count":2,"errors":["dup id"]}'

            def json(self):
                return {"created_count": 2, "errors": ["dup id"]}

        with patch("requests.request", return_value=MockResponse()):
            count, errors = client.create_object_types("kn_1", [{"id": "a"}, {"id": "b"}])
        assert count == 2
        assert errors == ["dup id"]

    def test_create_relation_types_empty_list_skips_api(self, client):
        """create_relation_types with empty list does not call API."""
        with patch("requests.request") as m:
            count, errors = client.create_relation_types("kn_1", [])
        assert count == 0
        assert errors == []
        m.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
