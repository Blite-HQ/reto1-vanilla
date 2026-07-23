"""Smoke tests: every report figure renders to disk without errors."""

import json
from pathlib import Path

from reto1.plots import (
    figure_noise_comparison,
    figure_partition,
    figure_ratio_vs_p,
    figure_ratio_vs_p_multi,
)

DATA_DIR = Path(__file__).parent.parent / "data"

SWEEP = {
    1: {"ratio_expected": {"mean": 0.83, "std": 0.01, "n": 5},
        "ratio_best": {"mean": 0.98, "std": 0.02, "n": 5}},
    2: {"ratio_expected": {"mean": 0.90, "std": 0.02, "n": 5},
        "ratio_best": {"mean": 1.0, "std": 0.0, "n": 5}},
}
CLASSICAL = {
    "gw": {"ratio_best": 1.0},
    "greedy": {"ratio": 0.95},
}


def test_ratio_vs_p_renders(tmp_path: Path) -> None:
    out = tmp_path / "r-vs-p"
    figure_ratio_vs_p("cr8-uniforme", SWEEP, CLASSICAL, out)
    assert out.with_suffix(".pdf").exists() and out.with_suffix(".png").exists()


def test_ratio_vs_p_multi_renders(tmp_path: Path) -> None:
    out = tmp_path / "multi"
    figure_ratio_vs_p_multi({"cr8-uniforme": SWEEP, "ieee9-uniforme": SWEEP}, out)
    assert out.with_suffix(".pdf").exists()


def test_partition_renders_with_real_names(tmp_path: Path) -> None:
    record = json.loads((DATA_DIR / "cr8-uniforme.json").read_text())
    out = tmp_path / "particion"
    figure_partition(DATA_DIR / "cr8-uniforme.json",
                     record["asignacion_canonica"], out)
    assert out.with_suffix(".png").exists()


def test_noise_comparison_renders(tmp_path: Path) -> None:
    records = [
        {"instance": "cr6-uniforme", "p": 1, "device": "H2-1LE",
         "stats": {"ratio_mean": 0.83}},
        {"instance": "cr6-uniforme", "p": 1, "device": "H2-Emulator",
         "stats": {"ratio_mean": 0.81}},
    ]
    out = tmp_path / "ruido"
    figure_noise_comparison(records, {"cr6-uniforme": SWEEP}, out)
    assert out.with_suffix(".pdf").exists()


def test_noise_comparison_skips_when_empty(tmp_path: Path) -> None:
    out = tmp_path / "vacio"
    figure_noise_comparison([], {}, out)
    assert not out.with_suffix(".pdf").exists()
