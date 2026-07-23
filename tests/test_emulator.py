"""Tests for emulator count decoding (pytket bit order) and statistics."""

from pathlib import Path

import pytest

from reto1.emulator import counts_stats, decode_pytket
from reto1.instances import load_instance

DATA_DIR = Path(__file__).parent.parent / "data"


def test_decode_pytket_index_is_qubit_index() -> None:
    # key[i] = qubit i = node i (NOT Qiskit's little-endian string order).
    assert decode_pytket((0, 1, 1, 0), 4) == (0, 1, 1, 0)


def test_decode_pytket_canonicalizes_x0() -> None:
    assert decode_pytket((1, 0, 1), 3) == (0, 1, 0)


def test_counts_stats_recomputes_cuts_classically() -> None:
    inst = load_instance(DATA_DIR / "cr6-uniforme.json")
    optimal = tuple(inst.canonical_assignment)
    trivial = tuple([0] * inst.n_nodes)
    stats = counts_stats({optimal: 3, trivial: 1}, inst)
    assert stats["shots"] == 4
    assert stats["best_cut"] == inst.optimum
    assert stats["mean_cut"] == pytest.approx(3 * inst.optimum / 4)
    assert stats["ratio_best"] == 1.0


def test_counts_stats_rejects_empty() -> None:
    inst = load_instance(DATA_DIR / "cr6-uniforme.json")
    with pytest.raises(ValueError):
        counts_stats({}, inst)
