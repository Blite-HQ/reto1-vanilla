#!/usr/bin/env python3
"""Single entry point: reproduces every figure and number of the report.

    python reproduce.py            # full run (classical + QAOA sweeps + figures)
    python reproduce.py --quick    # reduced seeds/depths for a fast smoke pass

Outputs:
    runs/local/<instance>.json     raw run records (with canonical digests)
    figures/*.pdf|png              report figures
    RESULTS.md                     summary tables

Quantinuum H2 emulator runs are produced separately (scripts/run_h2_emulator.py,
requires Nexus credentials) and cached under runs/nexus/; this entry point
consumes the cached records if present, so the full report reproduces offline.
"""

import argparse
import json
import platform
from datetime import UTC, datetime
from importlib import metadata
from pathlib import Path

from reto1.experiments import run_classical_benchmarks, run_qaoa_sweep
from reto1.instances import canonical_digest, load_instance
from reto1.plots import figure_partition, figure_ratio_vs_p, figure_ratio_vs_p_multi

ROOT = Path(__file__).parent
DATA, RUNS, FIGURES = ROOT / "data", ROOT / "runs", ROOT / "figures"

CLASSICAL_INSTANCES = ("cr6-uniforme", "cr8-uniforme", "cr8-voltaje",
                       "ieee9-uniforme", "ieee14-flujo", "ieee30-flujo")
QUANTUM_INSTANCES = ("cr6-uniforme", "cr8-uniforme", "cr8-voltaje",
                     "ieee9-uniforme", "ieee14-flujo")
FULL = {"seeds": (0, 1, 2, 3, 4), "p_values": (1, 2, 3), "shots": 4096}
QUICK = {"seeds": (0, 1), "p_values": (1, 2), "shots": 1024}
HEADLINE = "cr8-uniforme"


def environment() -> dict:
    packages = ("qiskit", "qiskit-aer", "cvxpy", "networkx", "numpy", "scipy")
    return {
        "python": platform.python_version(),
        "packages": {p: metadata.version(p) for p in packages},
        "timestamp_utc": datetime.now(UTC).isoformat(timespec="seconds"),
    }


def verify_all_digests() -> None:
    for path in sorted(DATA.glob("*.json")):
        load_instance(path)  # raises on digest mismatch
    print(f"[ok] {len(list(DATA.glob('*.json')))} instancias con digest verificado")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true", help="reduced smoke run")
    args = parser.parse_args()
    cfg = QUICK if args.quick else FULL

    verify_all_digests()
    (RUNS / "local").mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(exist_ok=True)

    classical, sweeps = {}, {}
    for name in CLASSICAL_INSTANCES:
        inst = load_instance(DATA / f"{name}.json")
        classical[name] = run_classical_benchmarks(inst, seeds=cfg["seeds"] or (1,))
        print(f"[clásico] {name}: óptimo={classical[name]['optimum']} "
              f"GW={classical[name]['gw']['best']} "
              f"greedy={classical[name]['greedy']['value']} "
              f"SA_best={classical[name]['sa']['best']}")

    for name in QUANTUM_INSTANCES:
        inst = load_instance(DATA / f"{name}.json")
        sweeps[name] = run_qaoa_sweep(inst, p_values=cfg["p_values"],
                                      seeds=cfg["seeds"], shots=cfg["shots"])
        for p in cfg["p_values"]:
            stats = sweeps[name][p]["ratio_expected"]
            print(f"[QAOA]   {name} p={p}: r = {stats['mean']:.4f} ± {stats['std']:.4f}")

    env = environment()
    for name in set(CLASSICAL_INSTANCES) | set(sweeps):
        record = {
            "instance": name,
            "environment": env,
            "config": {k: list(v) if isinstance(v, tuple) else v for k, v in cfg.items()},
            "classical": classical.get(name),
            "qaoa_local": sweeps.get(name),
        }
        record["digest"] = canonical_digest(record)
        out = RUNS / "local" / f"{name}.json"
        out.write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")

    figure_ratio_vs_p(HEADLINE, sweeps[HEADLINE], classical[HEADLINE],
                      FIGURES / "r-vs-p-cr8")
    figure_ratio_vs_p_multi(sweeps, FIGURES / "r-vs-p-escalado")
    figure_partition(DATA / f"{HEADLINE}.json",
                     classical[HEADLINE]["exact"]["assignment"],
                     FIGURES / "particion-cr8")
    write_results_md(classical, sweeps, env)
    print(f"[ok] figuras en {FIGURES}/ · registros en {RUNS}/local/ · RESULTS.md")


def write_results_md(classical: dict, sweeps: dict, env: dict) -> None:
    lines = ["# Resultados (generado por reproduce.py — no editar a mano)", ""]
    lines += [f"Entorno: Python {env['python']}, " +
              ", ".join(f"{k} {v}" for k, v in env["packages"].items()), ""]
    lines += ["## Líneas base clásicas", "",
              "| instancia | óptimo | GW (mejor) | cota SDP | greedy | SA (mejor) |",
              "|---|---|---|---|---|---|"]
    for name, rep in sorted(classical.items()):
        lines.append(f"| {name} | {rep['optimum']} | {rep['gw']['best']} "
                     f"| {rep['gw']['sdp_bound']:.1f} | {rep['greedy']['value']} "
                     f"| {rep['sa']['best']} |")
    lines += ["", "## QAOA local (statevector exacto + muestreo Aer)", "",
              "| instancia | p | r = ⟨cut⟩/óptimo (media ± σ) | r mejor muestra |",
              "|---|---|---|---|"]
    for name, sweep in sorted(sweeps.items()):
        for p in sorted(sweep):
            re_, rb = sweep[p]["ratio_expected"], sweep[p]["ratio_best"]
            lines.append(f"| {name} | {p} | {re_['mean']:.4f} ± {re_['std']:.4f} "
                         f"| {rb['mean']:.4f} |")
    lines += ["", "Limitación honesta: QAOA no supera a Goemans-Williamson en Max-Cut "
              "en ninguna instancia; la garantía p=1 (0.6924) es estrictamente menor "
              "que la de GW (0.878). Ver el informe para la discusión completa.", ""]
    (ROOT / "RESULTS.md").write_text("\n".join(lines))


if __name__ == "__main__":
    main()
