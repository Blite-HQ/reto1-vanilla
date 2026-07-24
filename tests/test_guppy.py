"""Parity test: the Guppy/Selene circuit convention matches the Qiskit one.

Self-contained (no dependency on runs/): a triangle QAOA p=1 with fixed
angles, sampled on Selene/Quest, must reproduce the exact expectation of the
same circuit computed by the parity-tested vector engine. This validates the
CX·RZ·CX decomposition of RZZ, the angle conventions (Guppy angles are in
HALF-TURNS — tket convention — so radians are divided by pi) and the bit
order of measure_array (index = qubit = node) in one shot.
"""

import math

import numpy as np
import pytest

pytest.importorskip("guppylang")

from guppylang import guppy  # noqa: E402
from guppylang.std.angles import angle  # noqa: E402
from guppylang.std.builtins import array, comptime, result  # noqa: E402
from guppylang.std.quantum import cx, h, measure_array, qubit, rx, rz  # noqa: E402

from reto1.maxcut import cut_value  # noqa: E402
from reto1.qaoa import _cut_spectrum, _vector_probabilities  # noqa: E402

N = 3
TRIANGLE = ((0, 1, 1), (0, 2, 1), (1, 2, 1))
NORM_EDGES = [(i, j, float(w)) for i, j, w in TRIANGLE]  # max|w| = 1 already
GAMMA, BETA = 0.6, 0.4
GAMMA_HT, BETA_HT = 2.0 * GAMMA / math.pi, 2.0 * BETA / math.pi  # half-turns
SHOTS = 2048
TOLERANCE_SIGMAS = 5.0


@guppy
def triangle_qaoa() -> None:
    qs = array(qubit() for _ in range(comptime(N)))
    for i in range(comptime(N)):
        h(qs[i])
    for edge in comptime(NORM_EDGES):
        i, j, w = edge
        cx(qs[i], qs[j])
        rz(qs[j], angle(comptime(GAMMA_HT) * w))
        cx(qs[i], qs[j])
    for i in range(comptime(N)):
        rx(qs[i], angle(comptime(BETA_HT)))
    result("c", measure_array(qs))


def _sample_counts(shots: int, seed: int) -> dict[tuple[int, ...], int]:
    from selene_sim import Quest, build

    instance = build(triangle_qaoa.compile())
    counts: dict[tuple[int, ...], int] = {}
    for shot in instance.run_shots(Quest(random_seed=seed), n_qubits=N,
                                   n_shots=shots):
        bits = tuple(int(b) for b in dict(shot)["c"])
        counts[bits] = counts.get(bits, 0) + 1
    return counts


def test_selene_sampling_matches_exact_expectation() -> None:
    counts = _sample_counts(SHOTS, seed=11)
    mean_cut = sum(cut_value(TRIANGLE, bits) * c for bits, c in counts.items()) / SHOTS

    probabilities = _vector_probabilities(N, TRIANGLE, (GAMMA,), (BETA,))
    spectrum = _cut_spectrum(N, TRIANGLE)
    expected = float(probabilities @ spectrum)
    variance = float(probabilities @ spectrum**2) - expected**2
    sigma = np.sqrt(variance / SHOTS)

    assert abs(mean_cut - expected) <= TOLERANCE_SIGMAS * sigma


def test_selene_bitstrings_are_per_node() -> None:
    counts = _sample_counts(256, seed=3)
    assert all(len(bits) == N for bits in counts)
    assert all(b in (0, 1) for bits in counts for b in bits)
    # The optimum cut (2) must appear among 256 shots of a 3-node QAOA state.
    assert max(cut_value(TRIANGLE, bits) for bits in counts) == 2
