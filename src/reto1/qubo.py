"""Max-Cut -> QUBO formulation.

For x in {0,1}^n, cut(x) = sum_ij w_ij (x_i + x_j - 2 x_i x_j). Maximizing the
cut is minimizing E(x) = x^T Q x with the symmetric Q built here, so that
E(x) = -cut(x) exactly (no penalty terms needed: Max-Cut is unconstrained).
"""

from collections.abc import Sequence

import numpy as np

from .instances import Edge


def qubo_matrix(n_nodes: int, edges: Sequence[Edge]) -> np.ndarray:
    """Symmetric Q with x^T Q x = -cut(x) for binary column vector x."""
    q = np.zeros((n_nodes, n_nodes), dtype=np.int64)
    for i, j, w in edges:
        q[i, i] -= w
        q[j, j] -= w
        q[i, j] += w
        q[j, i] += w
    return q


def qubo_energy(q: np.ndarray, x: np.ndarray) -> int:
    """E(x) = x^T Q x (equals -cut(x) by construction)."""
    return int(x @ q @ x)
