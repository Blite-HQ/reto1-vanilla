"""Tests for the national ladder (nested corridors cr8 ⊂ cr12 ⊂ … ⊂ cr68)."""

import json
from pathlib import Path

import networkx as nx
import numpy as np
import pytest

from reto1.instances import (
    canonical_digest,
    load_instance,
    load_open_instance,
)

DATA_DIR = Path(__file__).parent.parent / "data"
NACIONAL_DIR = DATA_DIR / "nacional"

PROVEN = ("cr12-uniforme", "cr16-uniforme", "cr20-uniforme")
OPEN = ("cr26-uniforme", "cr34-uniforme", "cr44-uniforme",
        "cr56-uniforme", "cr68-uniforme")
LADDER = ("cr8-uniforme", *PROVEN, *OPEN)


def _node_names(path: Path) -> dict[int, str]:
    record = json.loads(path.read_text())
    return {int(k): v for k, v in record["nodos"].items()}


def _path(name: str) -> Path:
    return (DATA_DIR if (DATA_DIR / f"{name}.json").exists()
            else NACIONAL_DIR) / f"{name}.json"


def test_proven_ladder_loads_with_valid_digests() -> None:
    for name in PROVEN:
        inst = load_instance(DATA_DIR / f"{name}.json")
        assert inst.optimum > 0
        assert inst.canonical_assignment[0] == 0


def test_open_ladder_loads_with_valid_digests() -> None:
    for name in OPEN:
        inst = load_open_instance(NACIONAL_DIR / f"{name}.json")
        assert inst.n_nodes >= 26
        assert all(w >= 1 for _, _, w in inst.edges)


def test_open_loader_rejects_proven_instances() -> None:
    with pytest.raises(ValueError, match="frozen optimum"):
        load_open_instance(DATA_DIR / "cr8-uniforme.json")


def test_ladder_is_nested() -> None:
    # Every corridor's node mapping must be a prefix-extension of the previous
    # one: same growth sequence, so cr8 ⊂ cr12 ⊂ … ⊂ cr68 node by node.
    names = [_node_names(_path(name)) for name in LADDER]
    for smaller, larger in zip(names, names[1:], strict=False):
        for index, substation in smaller.items():
            assert larger[index] == substation


def test_ladder_subgraphs_are_connected() -> None:
    for name in LADDER:
        record = json.loads(_path(name).read_text())
        graph = nx.Graph((i, j) for i, j, _ in record["aristas"])
        assert graph.number_of_nodes() == record["n_nodos"]
        assert nx.is_connected(graph)


def test_cr68_is_the_full_national_graph() -> None:
    inst = load_open_instance(NACIONAL_DIR / "cr68-uniforme.json")
    assert inst.n_nodes == 68
    assert len(inst.edges) == 90


def test_cr12_optimum_reverified_independently() -> None:
    # Independent third check (numpy bit-trick spectrum, code written here).
    inst = load_instance(DATA_DIR / "cr12-uniforme.json")
    indices = np.arange(2 ** inst.n_nodes, dtype=np.int64)
    cuts = np.zeros(2 ** inst.n_nodes, dtype=np.int64)
    for i, j, w in inst.edges:
        cuts += w * (((indices >> i) & 1) ^ ((indices >> j) & 1))
    assert int(cuts.max()) == inst.optimum


def test_open_records_carry_no_solution_claims() -> None:
    for name in OPEN:
        record = json.loads((NACIONAL_DIR / f"{name}.json").read_text())
        assert "optimo" not in record
        assert "asignacion_canonica" not in record
        assert canonical_digest(record) == record["digest"]
