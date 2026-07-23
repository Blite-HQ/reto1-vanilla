"""Decoding and statistics for Quantinuum emulator results (pytket bit order).

pytket's BackendResult.get_counts() keys are readout tuples ordered by qubit
register index: key[i] is qubit i, i.e. node i — the OPPOSITE end from
Qiskit's little-endian count strings. Both decoders canonicalize x0 = 0 and
every cut is recomputed classically from the bitstring with the original
integer weights (backend-agnostic verification).
"""

from collections.abc import Mapping, Sequence

from .instances import Instance
from .maxcut import Assignment, cut_value


def decode_pytket(key: Sequence[int], n_nodes: int) -> Assignment:
    """pytket readout tuple (index = qubit index) -> assignment with x0 = 0."""
    x = tuple(int(b) for b in key[:n_nodes])
    return tuple(1 - v for v in x) if x[0] == 1 else x


def counts_stats(counts: Mapping[tuple[int, ...], int], instance: Instance) -> dict:
    """Mean/best cut and approximation ratios from emulator counts."""
    total_shots, weighted, best_cut, best_x = 0, 0.0, -1, None
    for key, count in counts.items():
        x = decode_pytket(tuple(key), instance.n_nodes)
        value = cut_value(instance.edges, x)
        total_shots += count
        weighted += value * count
        if value > best_cut:
            best_cut, best_x = value, x
    if best_x is None:
        raise ValueError("empty counts")
    return {
        "shots": total_shots,
        "mean_cut": weighted / total_shots,
        "best_cut": best_cut,
        "best_assignment": list(best_x),
        "ratio_mean": (weighted / total_shots) / instance.optimum,
        "ratio_best": best_cut / instance.optimum,
    }
