"""QAOA for Max-Cut (Farhi, Goldstone & Gutmann 2014, arXiv:1411.4028).

Circuit convention (documented, consistent everywhere):
- initial layer of H on every qubit;
- cost layer l: RZZ(2 * gamma_l * w_norm) per edge, with weights normalized to
  max |w| = 1 so angles stay in a sane range on heavily weighted instances;
- mixer layer l: RX(2 * beta_l) on every qubit.

Angles are optimized classically on the EXACT statevector expectation (grid
warm start for p=1 + seeded multi-start COBYLA; deeper p warm-starts from the
p-1 solution, so quality is monotonic in p up to optimizer tolerance). Sampling
runs on seeded Aer; every reported cut is recomputed classically from the
bitstring with the ORIGINAL integer weights.
"""

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator
from scipy.optimize import minimize

from .instances import Edge
from .maxcut import Assignment, cut_value

DEFAULT_SHOTS = 4096
GRID_POINTS = 16
RANDOM_RESTARTS = 6
COBYLA_MAXITER = 250
# Instances up to 14 nodes (every originally published run, ieee14 included)
# keep the generic Qiskit statevector path so frozen artifacts reproduce
# bit-for-bit. Larger corridors switch to the vectorized engine below, which
# computes the SAME distribution (parity-tested to ~1e-12): the generic path
# costs ~2.8 s/evaluation at 20 qubits — infeasible inside the optimizer.
VECTOR_ENGINE_MIN_N = 15
# Reduced, documented optimization budget for those larger corridors (an
# evaluation still costs ~0.5 s at n=20). The warm-start chain p -> p+1 plus
# QAOA angle concentration (Zhou et al. 2020, arXiv:1812.01041, INTERP) make
# the dense multistart redundant there; small instances keep the full budget.
GRID_POINTS_LARGE = 8
RANDOM_RESTARTS_LARGE = 2
COBYLA_MAXITER_LARGE = 100


@dataclass(frozen=True)
class QAOAResult:
    p: int
    seed: int
    gammas: tuple[float, ...]
    betas: tuple[float, ...]
    expected_cut: float
    sampled_mean_cut: float
    best_sampled_cut: int
    best_assignment: Assignment
    ratio_expected: float
    ratio_best: float
    shots: int


def _normalized(edges: Sequence[Edge]) -> tuple[tuple[int, int, float], ...]:
    max_w = max(abs(w) for _, _, w in edges)
    return tuple((i, j, w / max_w) for i, j, w in edges)


def build_qaoa_circuit(
    n_nodes: int,
    edges: Sequence[Edge],
    gammas: Sequence[float],
    betas: Sequence[float],
) -> QuantumCircuit:
    """p-layer QAOA circuit (no measurements) under the documented convention."""
    if len(gammas) != len(betas):
        raise ValueError("gammas and betas must have the same length p")
    norm_edges = _normalized(edges)
    circuit = QuantumCircuit(n_nodes)
    circuit.h(range(n_nodes))
    for gamma, beta in zip(gammas, betas, strict=True):
        for i, j, w in norm_edges:
            circuit.rzz(2.0 * gamma * w, i, j)
        for q in range(n_nodes):
            circuit.rx(2.0 * beta, q)
    return circuit


def _cut_spectrum(n_nodes: int, edges: Sequence[Edge]) -> np.ndarray:
    """cut(x) for every basis index; bit i of the index is node i's side."""
    indices = np.arange(2**n_nodes, dtype=np.int64)
    cuts = np.zeros(2**n_nodes, dtype=np.float64)
    for i, j, w in edges:
        cuts += w * (((indices >> i) & 1) ^ ((indices >> j) & 1))
    return cuts


def _vector_probabilities(
    n_nodes: int,
    edges: Sequence[Edge],
    gammas: Sequence[float],
    betas: Sequence[float],
    norm_spectrum: np.ndarray | None = None,
) -> np.ndarray:
    """Probabilities of the QAOA state via dense vector simulation.

    Same circuit convention as build_qaoa_circuit, exploiting that the cost
    layer is diagonal — its phases are exp(2i*gamma*cut_norm(x)) up to a global
    phase, with cut_norm the cut spectrum of the max|w|-normalized weights —
    and that the mixer layer is a tensor product of RX(2*beta) rotations,
    applied axis by axis. Bit i of the basis index is node i, identical to
    _cut_spectrum and to Qiskit's little-endian probabilities(). Parity with
    the Qiskit statevector path is asserted in tests.
    """
    if norm_spectrum is None:
        norm_spectrum = _cut_spectrum(n_nodes, _normalized(edges))
    dim = 1 << n_nodes
    psi = np.full(dim, 1.0 / np.sqrt(dim), dtype=np.complex128)
    for gamma, beta in zip(gammas, betas, strict=True):
        psi *= np.exp(2j * gamma * norm_spectrum)
        cos_b, sin_b = np.cos(beta), -1j * np.sin(beta)
        for q in range(n_nodes):
            psi = psi.reshape(-1, 2, 1 << q)
            top = psi[:, 0, :].copy()
            psi[:, 0, :] = cos_b * top + sin_b * psi[:, 1, :]
            psi[:, 1, :] = sin_b * top + cos_b * psi[:, 1, :]
        psi = psi.reshape(dim)
    return np.abs(psi) ** 2


def _expected_cut(params: np.ndarray, n_nodes: int, edges: Sequence[Edge],
                  spectrum: np.ndarray,
                  norm_spectrum: np.ndarray | None = None) -> float:
    p = len(params) // 2
    if norm_spectrum is not None:
        probabilities = _vector_probabilities(n_nodes, edges, params[:p],
                                              params[p:], norm_spectrum)
    else:
        circuit = build_qaoa_circuit(n_nodes, edges, params[:p], params[p:])
        probabilities = Statevector.from_instruction(circuit).probabilities()
    return float(probabilities @ spectrum)


def _optimize_angles(
    n_nodes: int,
    edges: Sequence[Edge],
    p: int,
    seed: int,
    warm_start: np.ndarray | None,
) -> tuple[np.ndarray, float]:
    """Maximize the exact expectation; returns (params, expected_cut).

    Instances below VECTOR_ENGINE_MIN_N keep the original full budget (16x8
    grid, 6 random restarts, 250 COBYLA iters) so the published runs reproduce
    bit-for-bit; larger corridors use the reduced budget documented above.
    """
    spectrum = _cut_spectrum(n_nodes, edges)
    large = n_nodes >= VECTOR_ENGINE_MIN_N
    norm_spectrum = _cut_spectrum(n_nodes, _normalized(edges)) if large else None
    grid_points = GRID_POINTS_LARGE if large else GRID_POINTS
    restarts = RANDOM_RESTARTS_LARGE if large else RANDOM_RESTARTS
    maxiter = COBYLA_MAXITER_LARGE if large else COBYLA_MAXITER
    objective = lambda t: -_expected_cut(t, n_nodes, edges, spectrum,  # noqa: E731
                                         norm_spectrum)
    rng = np.random.default_rng(seed)

    starts: list[np.ndarray] = []
    if p == 1:
        grid_gamma = np.linspace(0.05, np.pi, grid_points)
        grid_beta = np.linspace(0.05, np.pi / 2, grid_points // 2)
        best_grid = max(
            (np.array([g, b]) for g in grid_gamma for b in grid_beta),
            key=lambda t: -objective(t),
        )
        starts.append(best_grid)
    if warm_start is not None:
        padded = np.concatenate([warm_start[: p - 1], [0.0],
                                 warm_start[p - 1:], [0.0]])
        starts.append(padded)
    for _ in range(restarts):
        starts.append(np.concatenate([rng.uniform(0, np.pi, p),
                                      rng.uniform(0, np.pi / 2, p)]))

    best_params, best_value = None, -np.inf
    for start in starts:
        result = minimize(objective, start, method="COBYLA",
                          options={"maxiter": maxiter, "rhobeg": 0.3})
        value = -result.fun
        if value > best_value:
            best_params, best_value = np.asarray(result.x), value
    assert best_params is not None
    return best_params, best_value


def _decode(bitstring: str, n_nodes: int) -> Assignment:
    """Qiskit counts key (qubit 0 rightmost) -> assignment with canonical x0=0."""
    x = tuple(int(bitstring[-(i + 1)]) for i in range(n_nodes))
    return tuple(1 - v for v in x) if x[0] == 1 else x


def _sample(circuit: QuantumCircuit, edges: Sequence[Edge], n_nodes: int,
            seed: int, shots: int) -> tuple[float, int, Assignment]:
    """Seeded Aer sampling -> (mean cut, best cut, best assignment), all cuts
    recomputed classically from bitstrings with the original weights."""
    measured = circuit.copy()
    measured.measure_all()
    backend = AerSimulator(seed_simulator=seed)
    counts = backend.run(measured, shots=shots).result().get_counts()

    total, best_cut, best_x = 0.0, -1, None
    for bitstring, count in counts.items():
        x = _decode(bitstring, n_nodes)
        value = cut_value(edges, x)
        total += value * count
        if value > best_cut:
            best_cut, best_x = value, x
    assert best_x is not None
    return total / shots, best_cut, best_x


def run_qaoa(
    n_nodes: int,
    edges: Sequence[Edge],
    optimum: int,
    p: int,
    seed: int,
    shots: int = DEFAULT_SHOTS,
) -> QAOAResult:
    """Optimize angles at depth p (warm-starting from p-1) and sample the result."""
    warm: np.ndarray | None = None
    params, expected = np.array([]), 0.0
    for depth in range(1, p + 1):
        params, expected = _optimize_angles(n_nodes, edges, depth, seed, warm)
        warm = params
    mean_cut, best_cut, best_x = _sample(
        build_qaoa_circuit(n_nodes, edges, params[:p], params[p:]),
        edges, n_nodes, seed, shots,
    )
    return QAOAResult(
        p=p,
        seed=seed,
        gammas=tuple(float(g) for g in params[:p]),
        betas=tuple(float(b) for b in params[p:]),
        expected_cut=expected,
        sampled_mean_cut=mean_cut,
        best_sampled_cut=best_cut,
        best_assignment=best_x,
        ratio_expected=expected / optimum,
        ratio_best=best_cut / optimum,
        shots=shots,
    )
