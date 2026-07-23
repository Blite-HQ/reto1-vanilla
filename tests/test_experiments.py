"""Tests for the experiment runner and its statistics."""

from pathlib import Path

from reto1.experiments import (
    aggregate,
    run_classical_benchmarks,
    run_qaoa_sweep,
)
from reto1.instances import load_instance

DATA_DIR = Path(__file__).parent.parent / "data"


def test_aggregate_mean_std() -> None:
    stats = aggregate([1.0, 2.0, 3.0])
    assert stats["mean"] == 2.0
    assert 0.99 < stats["std"] < 1.01  # sample std (ddof=1)
    assert stats["n"] == 3
    assert stats["min"] == 1.0 and stats["max"] == 3.0


def test_classical_benchmarks_cr6() -> None:
    inst = load_instance(DATA_DIR / "cr6-uniforme.json")
    report = run_classical_benchmarks(inst, seeds=(1, 2, 3))
    assert report["exact"]["value"] == inst.optimum
    assert report["gw"]["best"] >= 0.878 * inst.optimum
    assert report["gw"]["sdp_bound"] >= inst.optimum - 1e-6
    assert report["greedy"]["value"] >= inst.total_weight / 2
    assert report["sa"]["stats"]["n"] == 3
    for solver in ("gw", "greedy", "sa"):
        assert report[solver]["best"] <= inst.optimum


def test_qaoa_sweep_shapes_and_threshold() -> None:
    inst = load_instance(DATA_DIR / "cr6-uniforme.json")
    sweep = run_qaoa_sweep(inst, p_values=(1,), seeds=(0, 1, 2), shots=1024)
    assert set(sweep.keys()) == {1}
    per_seed = sweep[1]["runs"]
    assert len(per_seed) == 3
    # Official good-enough: r >= 0.6 at p=1 on a 6-node instance.
    assert sweep[1]["ratio_expected"]["mean"] >= 0.6
    for run in per_seed:
        assert run["ratio_expected"] <= 1.0 + 1e-12
