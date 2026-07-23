"""Goemans-Williamson SDP relaxation + random-hyperplane rounding.

Reference: Goemans & Williamson (1995), JACM 42(6), 1115-1145 — approximation
ratio >= 0.87856 for Max-Cut. The SDP optimum is also a rigorous UPPER bound on
the true max cut, reported here as `sdp_bound` (sanity anchor: no solver may
exceed it).
"""

from collections.abc import Sequence
from dataclasses import dataclass

import cvxpy as cp
import numpy as np

from .instances import Edge
from .maxcut import Assignment, cut_value

DEFAULT_ROUNDINGS = 200
EIGENVALUE_FLOOR = 1e-9


@dataclass(frozen=True)
class GWResult:
    value: int
    assignment: Assignment
    sdp_bound: float
    roundings: int


def _solve_sdp(n_nodes: int, edges: Sequence[Edge]) -> tuple[np.ndarray, float]:
    """Solve the Max-Cut SDP relaxation; return (Gram matrix, SDP optimum)."""
    x = cp.Variable((n_nodes, n_nodes), PSD=True)
    objective = cp.Maximize(
        sum(0.5 * w * (1 - x[i, j]) for i, j, w in edges)
    )
    problem = cp.Problem(objective, [cp.diag(x) == 1])
    problem.solve(solver=cp.SCS, verbose=False)
    if x.value is None:
        raise RuntimeError("SDP solver failed to produce a solution")
    return x.value, float(problem.value)


def _embedding(gram: np.ndarray) -> np.ndarray:
    """Vectors v_i with v_i . v_j ~= gram[i, j], via eigendecomposition."""
    eigenvalues, eigenvectors = np.linalg.eigh(gram)
    eigenvalues = np.clip(eigenvalues, EIGENVALUE_FLOOR, None)
    return eigenvectors * np.sqrt(eigenvalues)


def goemans_williamson(
    n_nodes: int,
    edges: Sequence[Edge],
    seed: int,
    roundings: int = DEFAULT_ROUNDINGS,
) -> GWResult:
    """Best cut over `roundings` seeded random hyperplanes on the SDP embedding."""
    gram, sdp_bound = _solve_sdp(n_nodes, edges)
    vectors = _embedding(gram)
    rng = np.random.default_rng(seed)

    best_value, best_assignment = -1, None
    for _ in range(roundings):
        hyperplane = rng.standard_normal(vectors.shape[1])
        sides = (vectors @ hyperplane >= 0).astype(int)
        if sides[0] == 1:
            sides = 1 - sides  # canonical x0 = 0
        value = cut_value(edges, sides)
        if value > best_value:
            best_value, best_assignment = value, tuple(int(s) for s in sides)
    assert best_assignment is not None
    return GWResult(
        value=best_value,
        assignment=best_assignment,
        sdp_bound=sdp_bound,
        roundings=roundings,
    )
