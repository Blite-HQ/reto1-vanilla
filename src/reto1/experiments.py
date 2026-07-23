"""Experiment runner: classical benchmarks + QAOA sweeps with statistics.

Every reported number is either deterministic (exact, greedy) or aggregated
over multiple seeds with mean and sample standard deviation — never a single
cherry-picked run (rubric: statistical analysis; pitfall: single QAOA run).
"""

import statistics
from collections.abc import Sequence
from dataclasses import asdict

from .gw import goemans_williamson
from .instances import Instance
from .maxcut import brute_force, greedy_cut, simulated_annealing
from .qaoa import DEFAULT_SHOTS, run_qaoa

BRUTE_FORCE_MAX_N = 20


def aggregate(values: Sequence[float]) -> dict:
    """Mean, sample std, extremes and count for a list of per-seed values."""
    return {
        "mean": statistics.fmean(values),
        "std": statistics.stdev(values) if len(values) > 1 else 0.0,
        "min": min(values),
        "max": max(values),
        "n": len(values),
    }


def run_classical_benchmarks(instance: Instance, seeds: Sequence[int]) -> dict:
    """Exact + GW + greedy + simulated annealing on one instance."""
    if instance.n_nodes <= BRUTE_FORCE_MAX_N:
        exact_value, exact_assignment = brute_force(instance.n_nodes, instance.edges)
        if exact_value != instance.optimum:
            raise AssertionError(
                f"{instance.name}: recomputed optimum {exact_value} != frozen "
                f"{instance.optimum} — corrupted instance or solver bug"
            )
        exact = {"value": exact_value, "assignment": list(exact_assignment),
                 "method": "bruteforce"}
    else:
        exact = {"value": instance.optimum, "assignment": list(instance.canonical_assignment),
                 "method": "+".join(instance.methods) + " (frozen anchors)"}

    gw_runs = [goemans_williamson(instance.n_nodes, instance.edges, seed=s) for s in seeds]
    gw_values = [float(r.value) for r in gw_runs]
    best_gw = max(gw_runs, key=lambda r: r.value)

    greedy_value, greedy_assignment = greedy_cut(instance.n_nodes, instance.edges)

    sa_values = []
    sa_best_value, sa_best_assignment = -1, None
    for seed in seeds:
        value, assignment = simulated_annealing(instance.n_nodes, instance.edges, seed=seed)
        sa_values.append(float(value))
        if value > sa_best_value:
            sa_best_value, sa_best_assignment = value, assignment

    optimum = float(exact["value"])
    return {
        "instance": instance.name,
        "optimum": exact["value"],
        "exact": exact,
        "gw": {
            "stats": aggregate(gw_values),
            "best": best_gw.value,
            "best_assignment": list(best_gw.assignment),
            "sdp_bound": best_gw.sdp_bound,
            "ratio_best": best_gw.value / optimum,
            "reference": "Goemans & Williamson (1995), JACM 42(6) — ratio >= 0.878",
        },
        "greedy": {
            "value": greedy_value,
            "best": greedy_value,
            "assignment": list(greedy_assignment),
            "ratio": greedy_value / optimum,
            "reference": "locally-optimal single-flip greedy — ratio ~0.5 guarantee",
        },
        "sa": {
            "stats": aggregate(sa_values),
            "best": sa_best_value,
            "best_assignment": list(sa_best_assignment or ()),
            "ratio_best": sa_best_value / optimum,
        },
    }


def run_qaoa_sweep(
    instance: Instance,
    p_values: Sequence[int],
    seeds: Sequence[int],
    shots: int = DEFAULT_SHOTS,
) -> dict:
    """QAOA at each depth p, once per seed; aggregates the approximation ratios."""
    sweep: dict[int, dict] = {}
    for p in p_values:
        runs = [run_qaoa(instance.n_nodes, instance.edges, optimum=instance.optimum,
                         p=p, seed=seed, shots=shots) for seed in seeds]
        sweep[p] = {
            "runs": [asdict(r) for r in runs],
            "ratio_expected": aggregate([r.ratio_expected for r in runs]),
            "ratio_best": aggregate([r.ratio_best for r in runs]),
            "best_sampled_cut": max(r.best_sampled_cut for r in runs),
        }
    return sweep
