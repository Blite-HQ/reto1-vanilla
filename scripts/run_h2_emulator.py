#!/usr/bin/env python3
"""Run the locally-optimized QAOA circuits on Quantinuum devices via qnexus.

Reads the angle sets that reproduce.py optimized on the local statevector
(runs/local/<instance>.json), rebuilds each circuit, and submits it to the
requested device. Results are cached as runs/nexus/*.json so the report
reproduces offline without Nexus credentials.

Devices (Quantinuum naming): H2-1LE = noiseless emulator (free);
H2-Emulator = emulator with the realistic H2 noise model (spends HQC —
always estimate first with --dry-run).

Requires a Nexus session: run `qnx login` first.

Examples:
    uv run python scripts/run_h2_emulator.py --dry-run
    uv run python scripts/run_h2_emulator.py --device H2-1LE
    uv run python scripts/run_h2_emulator.py --device H2-Emulator \
        --instances cr8-uniforme --seeds 0 --shots 1024
"""

import argparse
import json
import sys
import time
from pathlib import Path

from pytket.extensions.qiskit import qiskit_to_tk

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from reto1.instances import canonical_digest, load_instance  # noqa: E402
from reto1.maxcut import cut_value  # noqa: E402
from reto1.qaoa import build_qaoa_circuit  # noqa: E402

PROJECT = "quantathon-reto1"
FREE_DEVICES = frozenset({"H2-1LE", "H1-1LE", "H2-1SC", "H1-1SC"})
DEFAULT_INSTANCES = ("cr6-uniforme", "cr8-uniforme", "ieee9-uniforme")
DEFAULT_P = (1, 2, 3)
DEFAULT_SEEDS = (0,)
DEFAULT_SHOTS = 1024
WAIT_TIMEOUT = 900.0


def load_angles(instance: str, p: int, seed: int) -> tuple[list[float], list[float]]:
    record = json.loads((ROOT / "runs" / "local" / f"{instance}.json").read_text())
    runs = record["qaoa_local"][str(p)]["runs"]
    for run in runs:
        if run["seed"] == seed:
            return run["gammas"], run["betas"]
    raise SystemExit(f"no local run for {instance} p={p} seed={seed}; "
                     "run reproduce.py first")


def tk_circuit(instance_name: str, p: int, seed: int):
    inst = load_instance(ROOT / "data" / f"{instance_name}.json")
    gammas, betas = load_angles(instance_name, p, seed)
    circuit = build_qaoa_circuit(inst.n_nodes, inst.edges, gammas, betas)
    circuit.measure_all()
    tkc = qiskit_to_tk(circuit)
    tkc.name = f"{instance_name}-p{p}-s{seed}"
    return inst, tkc, gammas, betas


def decode_pytket(key: tuple[int, ...], n_nodes: int) -> tuple[int, ...]:
    """pytket readout tuple (index = qubit index) -> assignment, canonical x0=0."""
    x = tuple(int(b) for b in key[:n_nodes])
    return tuple(1 - v for v in x) if x[0] == 1 else x


def counts_stats(counts: dict, inst) -> dict:
    total_shots, weighted, best_cut, best_x = 0, 0.0, -1, None
    for key, count in counts.items():
        x = decode_pytket(tuple(key), inst.n_nodes)
        value = cut_value(inst.edges, x)
        total_shots += count
        weighted += value * count
        if value > best_cut:
            best_cut, best_x = value, x
    return {
        "shots": total_shots,
        "mean_cut": weighted / total_shots,
        "best_cut": best_cut,
        "best_assignment": list(best_x or ()),
        "ratio_mean": (weighted / total_shots) / inst.optimum,
        "ratio_best": best_cut / inst.optimum,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instances", default=",".join(DEFAULT_INSTANCES))
    parser.add_argument("--p-values", default=",".join(map(str, DEFAULT_P)))
    parser.add_argument("--seeds", default=",".join(map(str, DEFAULT_SEEDS)))
    parser.add_argument("--shots", type=int, default=DEFAULT_SHOTS)
    parser.add_argument("--device", default="H2-1LE")
    parser.add_argument("--dry-run", action="store_true",
                        help="upload + cost estimate only, no execution")
    args = parser.parse_args()

    import qnexus as qnx

    if not qnx.auth.is_logged_in():
        raise SystemExit("no Nexus session: run `qnx login` first")

    instances = args.instances.split(",")
    p_values = [int(p) for p in args.p_values.split(",")]
    seeds = [int(s) for s in args.seeds.split(",")]
    config = qnx.QuantinuumConfig(device_name=args.device)
    project = qnx.projects.get_or_create(name=PROJECT)
    out_dir = ROOT / "runs" / "nexus"
    out_dir.mkdir(parents=True, exist_ok=True)

    total_cost = 0.0
    for name in instances:
        for p in p_values:
            for seed in seeds:
                inst, tkc, gammas, betas = tk_circuit(name, p, seed)
                tag = f"{name}-p{p}-s{seed}"
                ref = qnx.circuits.upload(circuit=tkc, name=tag, project=project)
                # The cost endpoint only exists for billable devices; free
                # emulators/syntax checkers cost 0 HQC by definition.
                cost = (0.0 if args.device in FREE_DEVICES
                        else qnx.circuits.cost(ref, args.shots, config))
                total_cost += float(cost or 0.0)
                print(f"[{tag}] n={inst.n_nodes} device={args.device} "
                      f"shots={args.shots} costo_estimado={cost}")
                if args.dry_run:
                    continue

                stamp = time.strftime("%Y%m%d-%H%M%S")
                compiled = qnx.compile(programs=[ref], backend_config=config,
                                       name=f"compile-{tag}-{stamp}", project=project)
                job = qnx.start_execute_job(
                    programs=[compiled[0]], n_shots=[args.shots],
                    backend_config=config, name=f"exec-{tag}-{stamp}",
                    project=project, valid_check=True,
                )
                qnx.jobs.wait_for(job, timeout=WAIT_TIMEOUT)
                result = qnx.jobs.results(job)[0].download_result()
                counts = {tuple(int(b) for b in k): int(v)
                          for k, v in result.get_counts().items()}
                record = {
                    "instance": name, "p": p, "seed": seed,
                    "device": args.device, "project": PROJECT,
                    "job_id": str(job.id), "hqc_cost_estimate": cost,
                    "gammas": gammas, "betas": betas,
                    "counts": {"".join(map(str, k)): v for k, v in counts.items()},
                    "stats": counts_stats(counts, inst),
                    "timestamp": stamp,
                }
                record["digest"] = canonical_digest(record)
                out = out_dir / f"{tag}-{args.device}.json"
                out.write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
                stats = record["stats"]
                print(f"    r_mean={stats['ratio_mean']:.4f} "
                      f"r_best={stats['ratio_best']:.4f} -> {out.name}")

    print(f"\ncosto total estimado ({args.device}): {total_cost} HQC"
          + (" [dry-run: nada ejecutado]" if args.dry_run else ""))


if __name__ == "__main__":
    main()
