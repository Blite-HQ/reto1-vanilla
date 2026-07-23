"""Tests for the ICE-derived cr8/cr6 instances (real Costa Rican grid data)."""

import json
from pathlib import Path

from reto1.instances import load_instance
from reto1.maxcut import brute_force

DATA_DIR = Path(__file__).parent.parent / "data"


def test_cr_instances_exist_with_valid_digests() -> None:
    for name in ("cr8-uniforme", "cr8-voltaje", "cr6-uniforme", "cr6-voltaje"):
        inst = load_instance(DATA_DIR / f"{name}.json")  # digest verified inside
        assert inst.n_nodes in (6, 8)


def test_cr8_is_in_official_node_range() -> None:
    # Challenge statement: regional grid of 6-12 nodes.
    inst = load_instance(DATA_DIR / "cr8-uniforme.json")
    assert 6 <= inst.n_nodes <= 12


def test_cr_optima_reverify_by_brute_force() -> None:
    for name in ("cr8-uniforme", "cr8-voltaje", "cr6-uniforme", "cr6-voltaje"):
        inst = load_instance(DATA_DIR / f"{name}.json")
        best, assignment = brute_force(inst.n_nodes, inst.edges)
        assert best == inst.optimum
        assert list(assignment) == list(inst.canonical_assignment)


def test_cr_records_carry_provenance() -> None:
    record = json.loads((DATA_DIR / "cr8-uniforme.json").read_text())
    assert "fuente" in record and "descargado" in record
    assert len(record["nodos"]) == 8
    assert "criterio_corredor" in record and "definicion_peso" in record


def test_cr_maxcut_is_nontrivial() -> None:
    # A tree would have optimum == total weight (cut everything): boring and
    # suspicious. The corridor must contain cycles that make the problem real.
    for name in ("cr8-uniforme", "cr6-uniforme"):
        inst = load_instance(DATA_DIR / f"{name}.json")
        assert inst.optimum < inst.total_weight
        assert len(inst.edges) > inst.n_nodes - 1
