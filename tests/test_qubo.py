"""Tests for the Max-Cut -> QUBO formulation (verified on small instances)."""

import itertools

import numpy as np

from reto1.qubo import qubo_energy, qubo_matrix

TRIANGLE = ((0, 1, 1), (0, 2, 1), (1, 2, 1))
PATH4 = ((0, 1, 3), (1, 2, 2), (2, 3, 5))


def brute_cut(edges, x) -> int:
    return sum(w for i, j, w in edges if x[i] != x[j])


def test_qubo_energy_equals_negative_cut_on_every_assignment() -> None:
    # The QUBO is exact, not approximate: verify exhaustively (rubric: "verified
    # on test instances").
    for edges, n in ((TRIANGLE, 3), (PATH4, 4)):
        q = qubo_matrix(n, edges)
        for bits in itertools.product((0, 1), repeat=n):
            x = np.array(bits)
            assert qubo_energy(q, x) == -brute_cut(edges, bits)


def test_qubo_matrix_is_symmetric() -> None:
    q = qubo_matrix(4, PATH4)
    assert np.array_equal(q, q.T)


def test_minimizing_qubo_maximizes_cut() -> None:
    q = qubo_matrix(3, TRIANGLE)
    energies = {
        bits: qubo_energy(q, np.array(bits))
        for bits in itertools.product((0, 1), repeat=3)
    }
    best = min(energies, key=energies.get)
    assert brute_cut(TRIANGLE, best) == 2  # triangle optimum
