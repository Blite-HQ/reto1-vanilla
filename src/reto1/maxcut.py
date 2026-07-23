"""Cut evaluation and classical Max-Cut solvers: exact, greedy, simulated annealing.

Conventions (shared with the instance corpus):
- assignments are tuples of 0/1 per node with x[0] = 0 (complement symmetry broken);
- the problem is MAXIMIZATION of the cut weight, consistently everywhere.
"""

import itertools
import math
import random
from collections.abc import Sequence

from .instances import Edge

Assignment = tuple[int, ...]

SA_DEFAULT_SWEEPS = 200
SA_INITIAL_TEMP_FACTOR = 1.0
SA_FINAL_TEMP_FACTOR = 1e-3


def cut_value(edges: Sequence[Edge], assignment: Sequence[int]) -> int:
    """Total weight of edges crossing the partition."""
    return sum(w for i, j, w in edges if assignment[i] != assignment[j])


def _canonical(assignment: Sequence[int]) -> Assignment:
    """Fix x0 = 0 by taking the complement if needed (same cut value)."""
    if assignment[0] == 1:
        return tuple(1 - x for x in assignment)
    return tuple(assignment)


def brute_force(n_nodes: int, edges: Sequence[Edge]) -> tuple[int, Assignment]:
    """Exact optimum by full enumeration of the 2^(n-1) assignments with x0 = 0.

    Returns the optimum value and the lexicographically smallest optimal
    assignment (deterministic witness). Only meant for n <= ~20.
    """
    if n_nodes < 2:
        raise ValueError(f"need at least 2 nodes, got {n_nodes}")
    best, best_x = -1, None
    for bits in itertools.product((0, 1), repeat=n_nodes - 1):
        x = (0, *bits)
        v = cut_value(edges, x)
        if v > best:  # strict: keeps the lexicographically smallest witness
            best, best_x = v, x
    assert best_x is not None
    return best, best_x


def greedy_cut(n_nodes: int, edges: Sequence[Edge]) -> tuple[int, Assignment]:
    """Deterministic greedy: place each node on the side that cuts more weight.

    Locally optimal single-flip solution; classical guarantee >= W/2 (ratio ~0.5).
    """
    assignment = [0] * n_nodes
    incident: list[list[tuple[int, int]]] = [[] for _ in range(n_nodes)]
    for i, j, w in edges:
        incident[i].append((j, w))
        incident[j].append((i, w))
    improved = True
    while improved:
        improved = False
        for node in range(1, n_nodes):  # node 0 stays fixed at side 0
            gain = sum(w if assignment[other] == assignment[node] else -w
                       for other, w in incident[node])
            if gain > 0:
                assignment[node] = 1 - assignment[node]
                improved = True
    final = _canonical(assignment)
    return cut_value(edges, final), final


def simulated_annealing(
    n_nodes: int,
    edges: Sequence[Edge],
    seed: int,
    sweeps: int = SA_DEFAULT_SWEEPS,
) -> tuple[int, Assignment]:
    """Seeded simulated annealing over single-node flips (geometric cooling).

    Deterministic for a given seed; returns the best assignment ever visited.
    """
    rng = random.Random(seed)
    total_weight = sum(w for _, _, w in edges)
    assignment = [0] + [rng.randint(0, 1) for _ in range(n_nodes - 1)]
    current = cut_value(edges, assignment)
    best, best_x = current, tuple(assignment)

    incident: list[list[tuple[int, int]]] = [[] for _ in range(n_nodes)]
    for i, j, w in edges:
        incident[i].append((j, w))
        incident[j].append((i, w))

    t_start = SA_INITIAL_TEMP_FACTOR * max(total_weight, 1)
    t_end = SA_FINAL_TEMP_FACTOR * max(total_weight, 1)
    steps = sweeps * n_nodes
    for step in range(steps):
        temp = t_start * (t_end / t_start) ** (step / max(steps - 1, 1))
        node = rng.randrange(1, n_nodes)
        gain = sum(w if assignment[other] == assignment[node] else -w
                   for other, w in incident[node])
        if gain >= 0 or rng.random() < math.exp(gain / temp):
            assignment[node] = 1 - assignment[node]
            current += gain
            if current > best:
                best, best_x = current, tuple(assignment)
    final = _canonical(best_x)
    return best, final
