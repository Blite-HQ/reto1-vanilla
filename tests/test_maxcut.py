"""Tests for cut evaluation and classical solvers (exact, greedy, simulated annealing)."""

from pathlib import Path

import pytest

from reto1.instances import load_instance
from reto1.maxcut import (
    brute_force,
    cut_value,
    greedy_cut,
    simulated_annealing,
)

DATA_DIR = Path(__file__).parent.parent / "data"

# K3 triangle: any 2-1 split cuts 2 of the 3 unit edges.
TRIANGLE = ((0, 1, 1), (0, 2, 1), (1, 2, 1))


def test_cut_value_counts_crossing_edges() -> None:
    assert cut_value(TRIANGLE, (0, 1, 1)) == 2
    assert cut_value(TRIANGLE, (0, 0, 0)) == 0
    assert cut_value(TRIANGLE, (0, 1, 0)) == 2


def test_brute_force_triangle_optimum_is_two() -> None:
    best, assignment = brute_force(3, TRIANGLE)
    assert best == 2
    assert assignment[0] == 0  # canonical x0 = 0


def test_brute_force_reproduces_corpus_optimum_ieee9() -> None:
    inst = load_instance(DATA_DIR / "ieee9-uniforme.json")
    best, assignment = brute_force(inst.n_nodes, inst.edges)
    assert best == inst.optimum
    assert list(assignment) == list(inst.canonical_assignment)


def test_brute_force_reproduces_corpus_optimum_ieee14_flujo() -> None:
    inst = load_instance(DATA_DIR / "ieee14-flujo.json")
    best, _ = brute_force(inst.n_nodes, inst.edges)
    assert best == inst.optimum == 57_070


def test_greedy_reaches_at_least_half_the_total_weight() -> None:
    # Classical guarantee: greedy locally-optimal cut >= W/2.
    for name in ("ieee9-uniforme", "ieee14-flujo", "ieee30-flujo"):
        inst = load_instance(DATA_DIR / f"{name}.json")
        value, assignment = greedy_cut(inst.n_nodes, inst.edges)
        assert value >= inst.total_weight / 2
        assert cut_value(inst.edges, assignment) == value
        assert assignment[0] == 0


def test_simulated_annealing_is_deterministic_per_seed() -> None:
    inst = load_instance(DATA_DIR / "ieee14-uniforme.json")
    v1, a1 = simulated_annealing(inst.n_nodes, inst.edges, seed=7)
    v2, a2 = simulated_annealing(inst.n_nodes, inst.edges, seed=7)
    assert (v1, list(a1)) == (v2, list(a2))


def test_simulated_annealing_finds_optimum_on_small_instance() -> None:
    inst = load_instance(DATA_DIR / "ieee9-uniforme.json")
    value, assignment = simulated_annealing(inst.n_nodes, inst.edges, seed=1)
    assert value == inst.optimum
    assert cut_value(inst.edges, assignment) == value


def test_solvers_never_beat_the_exact_optimum() -> None:
    # "Better than optimal" would mean a bug, not a discovery.
    inst = load_instance(DATA_DIR / "ieee14-flujo.json")
    for value, _ in (
        greedy_cut(inst.n_nodes, inst.edges),
        simulated_annealing(inst.n_nodes, inst.edges, seed=3),
    ):
        assert value <= inst.optimum


@pytest.mark.parametrize("n", [0, 1])
def test_brute_force_rejects_degenerate_sizes(n: int) -> None:
    with pytest.raises(ValueError):
        brute_force(n, ())
