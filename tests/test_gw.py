"""Tests for the Goemans-Williamson SDP-rounding baseline."""

from pathlib import Path

from reto1.gw import goemans_williamson
from reto1.instances import load_instance
from reto1.maxcut import cut_value

DATA_DIR = Path(__file__).parent.parent / "data"

TRIANGLE = ((0, 1, 1), (0, 2, 1), (1, 2, 1))
GW_RATIO = 0.878


def test_triangle_sdp_bound_and_rounded_cut() -> None:
    result = goemans_williamson(3, TRIANGLE, seed=0)
    # K3 SDP optimum is 9/4; the true max cut is 2.
    assert 2.24 <= result.sdp_bound <= 2.26
    assert result.value == 2
    assert result.assignment[0] == 0


def test_gw_meets_its_guarantee_on_ieee9() -> None:
    inst = load_instance(DATA_DIR / "ieee9-uniforme.json")
    result = goemans_williamson(inst.n_nodes, inst.edges, seed=1)
    assert result.value >= GW_RATIO * inst.optimum
    assert cut_value(inst.edges, result.assignment) == result.value


def test_sdp_bound_is_a_true_upper_bound() -> None:
    for name in ("ieee9-uniforme", "ieee14-uniforme", "ieee14-flujo"):
        inst = load_instance(DATA_DIR / f"{name}.json")
        result = goemans_williamson(inst.n_nodes, inst.edges, seed=2)
        assert result.sdp_bound >= inst.optimum - 1e-6
        assert result.value <= inst.optimum


def test_gw_is_deterministic_per_seed() -> None:
    inst = load_instance(DATA_DIR / "ieee14-flujo.json")
    r1 = goemans_williamson(inst.n_nodes, inst.edges, seed=5)
    r2 = goemans_williamson(inst.n_nodes, inst.edges, seed=5)
    assert r1.value == r2.value
    assert list(r1.assignment) == list(r2.assignment)
