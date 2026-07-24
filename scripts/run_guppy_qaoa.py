#!/usr/bin/env python3
"""QAOA Max-Cut written in Guppy, executed on the Selene emulator (Quest).

Parity port of the headline circuit (src/reto1/qaoa.py) to Quantinuum's
recommended SDK, under the exact same documented convention:

- initial H on every qubit;
- cost layer: RZZ(2·gamma·w_norm) per edge, decomposed exactly as CX·RZ·CX
  (CX(i,j)·RZ_j(θ)·CX(i,j) = exp(-iθ/2·Z_i Z_j), Guppy has no native RZZ);
- mixer layer: RX(2·beta) per qubit.

Guppy's angle type uses HALF-TURN semantics (tket convention, verified
empirically against RX(pi)): angle(x) rotates x·pi radians, so every radian
value below is divided by pi before entering the circuit.

Angles come from the committed runs/local record (optimized once on the exact
statevector — single source of truth, nothing re-optimized here). Parity
criterion: the Selene sampled mean cut must fall within 4σ of the exact
expectation ⟨C⟩, with σ = sqrt(Var[C]/shots) computed from the exact QAOA
distribution. Every cut is recomputed classically from the sampled bitstring
(same backend-agnostic verification as the Qiskit/Nexus paths).

Requires the `entregables` dependency group:  uv sync --all-groups

Examples:
    uv run python scripts/run_guppy_qaoa.py                    # cr8, p=1
    uv run python scripts/run_guppy_qaoa.py --p 2 --shots 8192
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from reto1.emulator import counts_stats  # noqa: E402
from reto1.instances import canonical_digest, load_instance  # noqa: E402
from reto1.qaoa import _cut_spectrum, _vector_probabilities  # noqa: E402

PARITY_SIGMAS = 4.0

# --- configuration must be resolved BEFORE the @guppy definition: the circuit
# below captures N/EDGES/LAYERS at compile time via comptime() ---------------
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--instance", default="cr8-uniforme")
parser.add_argument("--p", type=int, default=1)
parser.add_argument("--seed", type=int, default=0,
                    help="seed of the runs/local record providing the angles")
parser.add_argument("--shots", type=int, default=4096)
parser.add_argument("--selene-seed", type=int, default=7)
ARGS = parser.parse_args()

INST = load_instance(ROOT / "data" / f"{ARGS.instance}.json")
_record = json.loads((ROOT / "runs" / "local" / f"{ARGS.instance}.json").read_text())
_runs = _record["qaoa_local"][str(ARGS.p)]["runs"]
_run = next((r for r in _runs if r["seed"] == ARGS.seed), None)
if _run is None:
    raise SystemExit(f"no local run for {ARGS.instance} p={ARGS.p} "
                     f"seed={ARGS.seed}; run reproduce.py first")

N = INST.n_nodes
_MAX_W = max(abs(w) for _, _, w in INST.edges)
EDGES = [(i, j, w / _MAX_W) for i, j, w in INST.edges]
# Angles pre-converted to half-turns: rz gets 2·gamma·w_norm/pi, rx 2·beta/pi.
import math  # noqa: E402

LAYERS = [(2.0 * g / math.pi, 2.0 * b / math.pi)
          for g, b in zip(_run["gammas"], _run["betas"], strict=True)]

from guppylang import guppy  # noqa: E402
from guppylang.std.angles import angle  # noqa: E402
from guppylang.std.builtins import array, comptime, result  # noqa: E402
from guppylang.std.quantum import cx, h, measure_array, qubit, rx, rz  # noqa: E402


@guppy
def qaoa() -> None:
    qs = array(qubit() for _ in range(comptime(N)))
    for i in range(comptime(N)):
        h(qs[i])
    for layer in comptime(LAYERS):
        gamma_ht, beta_ht = layer  # already 2·angle/pi (half-turns)
        for edge in comptime(EDGES):
            i, j, w = edge
            cx(qs[i], qs[j])
            rz(qs[j], angle(gamma_ht * w))
            cx(qs[i], qs[j])
        for i in range(comptime(N)):
            rx(qs[i], angle(beta_ht))
    result("c", measure_array(qs))


def main() -> None:
    from selene_sim import Quest, build

    instance_sel = build(qaoa.compile())
    shots_iter = instance_sel.run_shots(
        Quest(random_seed=ARGS.selene_seed), n_qubits=N, n_shots=ARGS.shots)
    counts: dict[tuple[int, ...], int] = {}
    for shot in shots_iter:
        bits = tuple(int(b) for b in dict(shot)["c"])
        counts[bits] = counts.get(bits, 0) + 1

    stats = counts_stats(counts, INST)

    # Exact reference distribution (vector engine, parity-tested vs Qiskit).
    gammas = list(_run["gammas"])
    betas = list(_run["betas"])
    probabilities = _vector_probabilities(N, INST.edges, gammas, betas)
    spectrum = _cut_spectrum(N, INST.edges)
    expected = float(probabilities @ spectrum)
    variance = float(probabilities @ spectrum**2) - expected**2
    sigma = float(np.sqrt(max(variance, 0.0) / ARGS.shots))
    deviation = abs(stats["mean_cut"] - expected)
    parity_ok = deviation <= PARITY_SIGMAS * sigma

    record = {
        "instance": ARGS.instance, "p": ARGS.p, "seed": ARGS.seed,
        "sdk": "guppylang+selene-quest", "selene_seed": ARGS.selene_seed,
        "gammas": gammas, "betas": betas,
        "counts": {"".join(map(str, k)): v for k, v in sorted(counts.items())},
        "stats": stats,
        "parity": {
            "expected_cut_exact": expected,
            "sigma_of_mean": sigma,
            "deviation": deviation,
            "criterion": f"|mean - exact| <= {PARITY_SIGMAS}*sigma",
            "ok": parity_ok,
        },
    }
    record["digest"] = canonical_digest(record)
    out_dir = ROOT / "runs" / "guppy"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{ARGS.instance}-p{ARGS.p}-s{ARGS.seed}.json"
    out.write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")

    print(f"[guppy] {ARGS.instance} p={ARGS.p} shots={ARGS.shots}: "
          f"⟨cut⟩={stats['mean_cut']:.4f} (exacto {expected:.4f} ± {sigma:.4f}) "
          f"r_mean={stats['ratio_mean']:.4f} r_best={stats['ratio_best']:.4f}")
    print(f"[guppy] paridad {'OK' if parity_ok else 'FALLIDA'} "
          f"(desviación {deviation:.4f} <= {PARITY_SIGMAS}σ = "
          f"{PARITY_SIGMAS * sigma:.4f}) -> {out.name}")
    if not parity_ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
