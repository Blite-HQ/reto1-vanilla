"""Tests for the QAOA implementation (local statevector + seeded Aer sampling)."""

from pathlib import Path

import numpy as np
from qiskit.quantum_info import Statevector

from reto1.instances import load_instance
from reto1.maxcut import cut_value
from reto1.qaoa import _vector_probabilities, build_qaoa_circuit, run_qaoa

DATA_DIR = Path(__file__).parent.parent / "data"

TRIANGLE = ((0, 1, 1), (0, 2, 1), (1, 2, 1))
TRIANGLE_OPTIMUM = 2
GOOD_ENOUGH_RATIO = 0.6  # official Challenge 1 threshold at p=1


def test_circuit_has_expected_gate_counts() -> None:
    circuit = build_qaoa_circuit(3, TRIANGLE, gammas=(0.4, 0.2), betas=(0.3, 0.1))
    ops = circuit.count_ops()
    assert ops["h"] == 3            # initial superposition
    assert ops["rzz"] == 2 * 3      # p layers x |E| edges
    assert ops["rx"] == 2 * 3       # p layers x n qubits
    assert "measure" not in ops     # measurement is added by the sampler


def test_p1_triangle_meets_good_enough_threshold() -> None:
    result = run_qaoa(3, TRIANGLE, optimum=TRIANGLE_OPTIMUM, p=1, seed=0)
    assert result.ratio_expected >= GOOD_ENOUGH_RATIO
    assert result.best_sampled_cut == TRIANGLE_OPTIMUM
    assert result.best_assignment[0] == 0  # canonical x0 = 0


def test_qaoa_is_deterministic_per_seed() -> None:
    a = run_qaoa(3, TRIANGLE, optimum=TRIANGLE_OPTIMUM, p=1, seed=11)
    b = run_qaoa(3, TRIANGLE, optimum=TRIANGLE_OPTIMUM, p=1, seed=11)
    assert a.gammas == b.gammas and a.betas == b.betas
    assert a.expected_cut == b.expected_cut
    assert a.best_sampled_cut == b.best_sampled_cut


def test_expectation_never_beats_the_optimum() -> None:
    inst = load_instance(DATA_DIR / "ieee9-uniforme.json")
    result = run_qaoa(inst.n_nodes, inst.edges, optimum=inst.optimum, p=1, seed=3)
    assert result.expected_cut <= inst.optimum + 1e-9
    assert result.ratio_expected <= 1.0 + 1e-12


def test_p1_ieee9_meets_good_enough_threshold() -> None:
    inst = load_instance(DATA_DIR / "ieee9-uniforme.json")
    result = run_qaoa(inst.n_nodes, inst.edges, optimum=inst.optimum, p=1, seed=0)
    assert result.ratio_expected >= GOOD_ENOUGH_RATIO


def test_deeper_p_does_not_degrade_ieee9() -> None:
    # Warm-started p=2 must be at least as good as p=1 (up to optimizer tolerance).
    inst = load_instance(DATA_DIR / "ieee9-uniforme.json")
    r1 = run_qaoa(inst.n_nodes, inst.edges, optimum=inst.optimum, p=1, seed=0)
    r2 = run_qaoa(inst.n_nodes, inst.edges, optimum=inst.optimum, p=2, seed=0)
    assert r2.ratio_expected >= r1.ratio_expected - 1e-6


def test_vector_engine_matches_qiskit_on_triangle() -> None:
    # The vectorized engine (cost layer as diagonal phases + per-axis RX mixer)
    # must produce the exact same distribution as the generic Qiskit path.
    gammas, betas = (0.37, -1.21), (0.85, 0.19)
    circuit = build_qaoa_circuit(3, TRIANGLE, gammas, betas)
    reference = Statevector.from_instruction(circuit).probabilities()
    fast = _vector_probabilities(3, TRIANGLE, gammas, betas)
    assert np.max(np.abs(fast - reference)) < 1e-12


def test_vector_engine_matches_qiskit_on_weighted_instances() -> None:
    rng = np.random.default_rng(7)
    for name in ("cr8-voltaje", "ieee9-uniforme"):
        inst = load_instance(DATA_DIR / f"{name}.json")
        for p in (1, 2):
            gammas = tuple(rng.uniform(0, np.pi, p))
            betas = tuple(rng.uniform(0, np.pi / 2, p))
            circuit = build_qaoa_circuit(inst.n_nodes, inst.edges, gammas, betas)
            reference = Statevector.from_instruction(circuit).probabilities()
            fast = _vector_probabilities(inst.n_nodes, inst.edges, gammas, betas)
            assert np.max(np.abs(fast - reference)) < 1e-12, f"{name} p={p}"


def test_best_assignment_cut_is_recomputed_classically() -> None:
    # The reported cut must equal a classical recomputation from the bitstring
    # (backend-agnostic verification: never trust the sampler's bookkeeping).
    inst = load_instance(DATA_DIR / "ieee9-uniforme.json")
    result = run_qaoa(inst.n_nodes, inst.edges, optimum=inst.optimum, p=1, seed=5)
    assert cut_value(inst.edges, result.best_assignment) == result.best_sampled_cut
