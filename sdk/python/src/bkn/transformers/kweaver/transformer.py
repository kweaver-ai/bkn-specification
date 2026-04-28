# Copyright The kweaver.ai Authors.
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

"""Transform BKN models to kweaver ontology-manager API JSON.

Based on ref/ontology_import_openapi_v2.json which defines three endpoints:
  - POST /knowledge-networks               (CreateKnowledgeNetwork)
  - POST /knowledge-networks/{id}/object-types   (CreateObjectTypes)
  - POST /knowledge-networks/{id}/relation-types (CreateRelationTypes)
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from bkn.models import (
    Action,
    BknNetwork,
    BknObject,
    Frontmatter,
    PropertyOverride,
    Relation,
)

from bkn.transformers.base import Transformer

# ---------------------------------------------------------------------------
# BKN type -> kweaver type mapping (reverse of what gen_objects_bkn.js did)
# ---------------------------------------------------------------------------
_TYPE_TO_KWEAVER: dict[str, str] = {
    "VARCHAR": "string",
    "varchar": "string",
    "TEXT": "text",
    "text": "text",
    "int32": "integer",
    "int64": "integer",
    "integer": "integer",
    "float32": "float",
    "float64": "float",
    "float": "float",
    "bool": "boolean",
    "DATE": "date",
    "date": "date",
    "TIME": "time",
    "TIMESTAMP": "timestamp",
    "timestamp": "timestamp",
    "JSON": "json",
    "BINARY": "binary",
}

_DECIMAL_RE = re.compile(r"^decimal(?:\((\d+),\s*(\d+)\))?$", re.IGNORECASE)

# ---------------------------------------------------------------------------
# Index Config parsing: "keyword(1024) + fulltext(standard) + vector(model_id)"
# -> { keyword_config: {...}, fulltext_config: {...}, vector_config: {...} }
# ---------------------------------------------------------------------------
_INDEX_PART_RE = re.compile(r"(keyword|fulltext|vector)(?:\(([^)]*)\))?")


def _parse_index_config(config_str: str) -> dict[str, Any]:
    """Parse a BKN Index Config string into kweaver index config dicts."""
    result: dict[str, Any] = {
        "keyword_config": {"enabled": False, "ignore_above_len": 1024},
        "fulltext_config": {"enabled": False, "analyzer": "standard"},
        "vector_config": {"enabled": False, "model_id": ""},
    }

    if not config_str or not config_str.strip():
        return result

    for m in _INDEX_PART_RE.finditer(config_str):
        idx_type = m.group(1)
        param = (m.group(2) or "").strip()

        if idx_type == "keyword":
            result["keyword_config"]["enabled"] = True
            if param:
                try:
                    result["keyword_config"]["ignore_above_len"] = int(param)
                except ValueError:
                    pass
        elif idx_type == "fulltext":
            result["fulltext_config"]["enabled"] = True
            if param:
                result["fulltext_config"]["analyzer"] = param
        elif idx_type == "vector":
            result["vector_config"]["enabled"] = True
            if param:
                result["vector_config"]["model_id"] = param

    return result


def _map_type(bkn_type: str) -> str:
    """Map a BKN data type to a kweaver type string."""
    if not bkn_type:
        return "string"

    dm = _DECIMAL_RE.match(bkn_type)
    if dm:
        return "decimal"

    return _TYPE_TO_KWEAVER.get(bkn_type, bkn_type.lower())


class KweaverTransformer(Transformer):
    """Convert BKN models to kweaver API-compatible JSON payloads.

    Args:
        branch: Target branch name (default "main").
        base_version: Base version string for object/relation types.
        id_prefix: Prefix to prepend to BKN short IDs to form full kweaver IDs.
                   For example "supplychain_hd0202_" turns "po" into
                   "supplychain_hd0202_po".
    """

    def __init__(
        self,
        branch: str = "main",
        base_version: str = "",
        id_prefix: str = "",
    ) -> None:
        self.branch = branch
        self.base_version = base_version
        self.id_prefix = id_prefix

    def _full_id(self, short_id: str) -> str:
        """Prepend id_prefix to a short BKN ID."""
        if self.id_prefix and not short_id.startswith(self.id_prefix):
            return f"{self.id_prefix}{short_id}"
        return short_id

    # -- Knowledge Network --------------------------------------------------

    def transform_network(self, fm: Frontmatter) -> dict[str, Any]:
        """Transform network frontmatter to CreateKnowledgeNetwork request body."""
        payload: dict[str, Any] = {
            "name": fm.name or fm.id,
            "branch": self.branch,
            "base_branch": "",
        }
        if fm.description:
            payload["comment"] = fm.description
        if fm.tags:
            payload["tags"] = fm.tags
        return payload

    # -- Object Types --------------------------------------------------------

    def _build_override_map(self, obj: BknObject) -> dict[str, PropertyOverride]:
        """Index property overrides by property name for fast lookup."""
        return {po.property: po for po in obj.property_overrides}

    def transform_object(self, obj: BknObject) -> dict[str, Any]:
        """Transform a BknObject to a kweaver CreateObjectTypes item."""
        override_map = self._build_override_map(obj)

        primary_keys = [
            dp.property for dp in obj.data_properties if dp.primary_key
        ]
        display_keys = [
            dp.property for dp in obj.data_properties if dp.display_key
        ]
        display_key = display_keys[0] if display_keys else ""

        data_props: list[dict[str, Any]] = []
        for dp in obj.data_properties:
            kweaver_type = _map_type(dp.type)
            prop_dict: dict[str, Any] = {
                "name": dp.property,
                "display_name": dp.display_name or dp.property,
                "type": kweaver_type,
                "comment": dp.description or "",
                "mapped_field": {
                    "name": dp.property,
                    "type": kweaver_type,
                    "display_name": dp.display_name or dp.property,
                },
            }

            override = override_map.get(dp.property)
            if override and override.index_config:
                prop_dict["index_config"] = _parse_index_config(override.index_config)
            elif dp.index:
                prop_dict["index_config"] = _parse_index_config("keyword")

            data_props.append(prop_dict)

        result: dict[str, Any] = {
            "name": obj.name or obj.id,
            "branch": self.branch,
            "base_version": self.base_version,
            "primary_keys": primary_keys,
            "display_key": display_key,
            "data_properties": data_props,
        }

        full_id = self._full_id(obj.id)
        if full_id:
            result["id"] = full_id

        if obj.tags:
            result["tags"] = obj.tags
        if obj.description:
            result["comment"] = obj.description

        if obj.data_source:
            ds = obj.data_source
            result["data_source"] = {
                "type": ds.type,
                "id": ds.id,
                "name": ds.name or obj.name or obj.id,
            }

        return result

    # -- Relation Types ------------------------------------------------------

    def transform_relation(self, relation: Relation) -> dict[str, Any]:
        """Transform a BKN Relation to a kweaver CreateRelationTypes item."""
        result: dict[str, Any] = {
            "name": relation.name or relation.id,
            "branch": self.branch,
            "base_version": self.base_version,
        }

        full_id = self._full_id(relation.id)
        if full_id:
            result["id"] = full_id

        if relation.tags:
            result["tags"] = relation.tags
        if relation.description:
            result["comment"] = relation.description

        if relation.endpoints:
            ep = relation.endpoints[0]
            result["source_object_type_id"] = self._full_id(ep.source)
            result["target_object_type_id"] = self._full_id(ep.target)
            result["type"] = ep.type or "direct"

        if relation.mapping_rules:
            # OpenAPI import spec accepts a flat array of {source_property, target_property}.
            # Kweaver export format uses nested source_mapping_rules/target_mapping_rules;
            # the import API accepts this flat format for direct relations.
            result["mapping_rules"] = [
                {
                    "source_property": {"name": mr.source_property},
                    "target_property": {"name": mr.target_property},
                }
                for mr in relation.mapping_rules
            ]

        return result

    # -- Action Types --------------------------------------------------------

    def transform_action(self, action: Action) -> dict[str, Any]:
        """Transform a BKN Action to a kweaver action_type item."""
        result: dict[str, Any] = {
            "name": action.name or action.id,
            "branch": self.branch,
            "base_version": self.base_version,
            "action_type": action.action_type or "add",
            "object_type_id": self._full_id(action.bound_object) if action.bound_object else "",
            "schedule": {"type": "", "expression": ""},
        }

        full_id = self._full_id(action.id)
        if full_id:
            result["id"] = full_id
        if action.description:
            result["comment"] = action.description

        if action.tool_config:
            result["action_source"] = {
                "type": action.tool_config.type or "tool",
                "box_id": "",
                "tool_id": action.tool_config.tool_id,
            }
        else:
            result["action_source"] = {"type": "tool", "box_id": "", "tool_id": ""}

        parameters: list[dict[str, Any]] = []
        for pb in action.parameter_binding:
            source = (pb.get("Source") or "input").strip()
            value_from = "const" if source.lower() == "const" else "input"
            value = pb.get("Binding") if value_from == "const" else None
            parameters.append({
                "name": pb.get("Parameter", ""),
                "type": (pb.get("Type") or "string").lower(),
                "source": source if source else "Body",
                "operation": "",
                "value_from": value_from,
                "value": value,
            })
        result["parameters"] = parameters

        if action.schedule:
            result["schedule"] = {
                "type": action.schedule.type or "",
                "expression": action.schedule.expression or "",
            }

        return result

    # -- Transformer interface -----------------------------------------------

    def to_json(self, network: BknNetwork) -> dict[str, Any]:
        """Transform a full BKN network into kweaver-compatible JSON payload.

        Returns a dict with four keys:
            - knowledge_network: CreateKnowledgeNetwork request body
            - object_types: list of CreateObjectTypes items
            - relation_types: list of CreateRelationTypes items
            - action_types: list of action_type items
        """
        return {
            "knowledge_network": self.transform_network(network.root.frontmatter),
            "object_types": [
                self.transform_object(e) for e in network.all_objects
            ],
            "relation_types": [
                self.transform_relation(r) for r in network.all_relations
            ],
            "action_types": [
                self.transform_action(a) for a in network.all_actions
            ],
        }

    def to_files(
        self,
        network: BknNetwork,
        output_dir: str | Path,
        indent: int = 2,
    ) -> list[Path]:
        """Write kweaver JSON payloads to separate files.

        Creates four files in output_dir:
            - knowledge_network.json
            - object_types.json
            - relation_types.json
            - action_types.json

        Returns list of created file paths.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        payload = self.to_json(network)
        created: list[Path] = []

        for key in (
            "knowledge_network",
            "object_types",
            "relation_types",
            "action_types",
        ):
            file_path = output_dir / f"{key}.json"
            file_path.write_text(
                json.dumps(payload[key], ensure_ascii=False, indent=indent),
                encoding="utf-8",
            )
            created.append(file_path)

        return created