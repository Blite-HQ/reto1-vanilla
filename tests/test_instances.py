"""Tests for instance loading and digest verification."""

from pathlib import Path

import pytest

from reto1.instances import list_instances, load_instance

DATA_DIR = Path(__file__).parent.parent / "data"


def test_lists_all_bundled_instances() -> None:
    names = list_instances(DATA_DIR)
    assert "ieee9-uniforme" in names
    assert "ieee14-flujo" in names
    assert len(names) >= 6


def test_loads_ieee9_uniforme_with_verified_digest() -> None:
    inst = load_instance(DATA_DIR / "ieee9-uniforme.json")
    assert inst.name == "ieee9-uniforme"
    assert inst.n_nodes == 9
    assert len(inst.edges) == 9
    assert inst.optimum == 9  # bipartite graph: max cut = |E|
    assert inst.digest.startswith("dee38cdeea9b")


def test_rejects_tampered_instance(tmp_path: Path) -> None:
    original = (DATA_DIR / "ieee9-uniforme.json").read_text()
    tampered = original.replace('"optimo": 9', '"optimo": 10')
    bad = tmp_path / "ieee9-uniforme.json"
    bad.write_text(tampered)
    with pytest.raises(ValueError, match="digest"):
        load_instance(bad)


def test_instance_is_immutable() -> None:
    inst = load_instance(DATA_DIR / "ieee9-uniforme.json")
    with pytest.raises(AttributeError):
        inst.optimum = 0  # type: ignore[misc]


def test_total_weight_matches_documented_value() -> None:
    inst = load_instance(DATA_DIR / "ieee14-flujo.json")
    assert inst.total_weight == 66_263
    assert inst.optimum == 57_070
