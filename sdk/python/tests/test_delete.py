# Copyright The kweaver.ai Authors.
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

"""Tests for bkn.delete API."""

from __future__ import annotations

import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
EXAMPLES_DIR = REPO_ROOT / "examples"


def test_plan_delete_single():
    from bkn import load_network, plan_delete, DeleteTarget

    path = EXAMPLES_DIR / "k8s-network"
    if not path.exists():
        pytest.skip("k8s-network example not found")
    net = load_network(path)
    plan = plan_delete(net, DeleteTarget(type="object", id="pod"), dry_run=True)
    assert plan.ok
    assert len(plan.targets) == 1
    assert plan.targets[0].id == "pod"
    assert len(plan.not_found) == 0


def test_plan_delete_not_found():
    from bkn import load_network, plan_delete, DeleteTarget

    path = EXAMPLES_DIR / "k8s-network"
    if not path.exists():
        pytest.skip("k8s-network example not found")
    net = load_network(path)
    plan = plan_delete(net, DeleteTarget(type="object", id="nonexistent"), dry_run=True)
    assert not plan.ok
    assert len(plan.not_found) == 1
    assert plan.not_found[0].id == "nonexistent"


def test_plan_delete_batch():
    from bkn import load_network, plan_delete, DeleteTarget

    path = EXAMPLES_DIR / "k8s-network"
    if not path.exists():
        pytest.skip("k8s-network example not found")
    net = load_network(path)
    targets = [
        DeleteTarget(type="object", id="pod"),
        DeleteTarget(type="relation", id="pod_belongs_node"),
        DeleteTarget(type="object", id="nonexistent"),
    ]
    plan = plan_delete(net, targets, dry_run=True)
    assert len(plan.targets) == 2
    assert len(plan.not_found) == 1


def test_network_without():
    from bkn import load_network, network_without, DeleteTarget

    path = EXAMPLES_DIR / "k8s-network"
    if not path.exists():
        pytest.skip("k8s-network example not found")
    net = load_network(path)
    orig_count = len(net.all_objects)
    out = network_without(net, [DeleteTarget(type="object", id="pod")])
    assert len(out.all_objects) == orig_count - 1
    assert not any(o.id == "pod" for o in out.all_objects)