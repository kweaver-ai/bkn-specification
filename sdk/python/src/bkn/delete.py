# Copyright The kweaver.ai Authors.
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

"""Delete API for BKN networks. Supports planning and in-memory simulation of deletions."""

from __future__ import annotations

from dataclasses import dataclass, field

from bkn.models import BknNetwork

_DELETE_TYPE_ALIASES: dict[str, str] = {
    "object_type": "object",
    "relation_type": "relation",
    "action_type": "action",
}


@dataclass
class DeleteTarget:
    """A single deletion target: type and id."""

    type: str  # "object" | "relation" | "action"
    id: str

    def __post_init__(self) -> None:
        self.type = self.type.strip().lower()
        self.type = _DELETE_TYPE_ALIASES.get(self.type, self.type)
        if self.type not in ("object", "relation", "action"):
            raise ValueError(f"Invalid delete type: {self.type!r}; must be object, relation, or action")


@dataclass
class DeletePlan:
    """Result of planning a delete operation."""

    targets: list[DeleteTarget] = field(default_factory=list)
    not_found: list[DeleteTarget] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """True if all targets exist in the network."""
        return len(self.not_found) == 0


def plan_delete(
    network: BknNetwork,
    targets: list[DeleteTarget] | DeleteTarget,
    *,
    dry_run: bool = True,
) -> DeletePlan:
    """
    Plan a delete operation: validate that targets exist in the network.

    Args:
        network: Loaded BknNetwork.
        targets: Single DeleteTarget or list of DeleteTargets.
        dry_run: If True (default), only validate; no side effects. The SDK does not
            persist changes; actual deletion is performed by the consumer (e.g. backend API).

    Returns:
        DeletePlan with .targets (validated, found) and .not_found (targets not in network).
    """
    if isinstance(targets, DeleteTarget):
        targets = [targets]

    found: list[DeleteTarget] = []
    not_found: list[DeleteTarget] = []

    for t in targets:
        exists = False
        if t.type == "object":
            exists = any(o.id == t.id for o in network.all_objects)
        elif t.type == "relation":
            exists = any(r.id == t.id for r in network.all_relations)
        elif t.type == "action":
            exists = any(a.id == t.id for a in network.all_actions)
        if exists:
            found.append(t)
        else:
            not_found.append(t)

    return DeletePlan(targets=found, not_found=not_found)


def network_without(network: BknNetwork, targets: list[DeleteTarget]) -> BknNetwork:
    """
    Return a new BknNetwork with the given targets removed (in-memory simulation).

    Targets that do not exist in the network are ignored.

    Args:
        network: Source BknNetwork.
        targets: List of DeleteTargets to remove.

    Returns:
        New BknNetwork with those definitions excluded.
    """
    from copy import deepcopy

    target_set = {(t.type.strip().lower(), t.id) for t in targets}
    out = deepcopy(network)

    def filter_objects(doc):
        doc.objects = [o for o in doc.objects if ("object", o.id) not in target_set]

    def filter_relations(doc):
        doc.relations = [r for r in doc.relations if ("relation", r.id) not in target_set]

    def filter_actions(doc):
        doc.actions = [a for a in doc.actions if ("action", a.id) not in target_set]

    filter_objects(out.root)
    filter_relations(out.root)
    filter_actions(out.root)
    for doc in out.includes:
        filter_objects(doc)
        filter_relations(doc)
        filter_actions(doc)

    return out