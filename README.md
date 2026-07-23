# Quantathon CR 2026 — Challenge 1: Fault-Zone Partitioning as Max-Cut

Partition a real power grid into fault-isolation zones by modeling the problem as
**Max-Cut**, casting it as a **QUBO**, solving it with **QAOA** on Quantinuum's
**H2 emulators**, and benchmarking honestly against the strongest classical
baselines: exact solvers, **Goemans-Williamson** (SDP rounding, ratio ≥ 0.878),
greedy (≈ 0.5) and simulated annealing.

The headline instance (**cr8**) is derived from **real open data of the Costa
Rican transmission grid** (Grupo ICE): an 8-substation corridor in the greater
metropolitan area — La Caja, Alajuelita, Anonos, Belén, Ribera, Colima, Heredia,
Cóncavas. See `data/README.md` for the full, auditable derivation.

## Reproduce everything

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python reproduce.py            # every figure and number of the report
python reproduce.py --quick    # fast smoke pass (reduced seeds/depths)
```

Developed with [uv](https://docs.astral.sh/uv/) (`uv sync --all-groups`);
`requirements.txt` is exported from the lock file, so both paths give the same
environment. Tests: `pytest` (41 tests).

Outputs: `figures/*.{pdf,png}`, `runs/local/*.json` (raw records with SHA-256
digests), `RESULTS.md` (summary tables).

## Quantinuum emulator runs (via Nexus)

```bash
qnx login                                     # Nexus credentials (event-provided)
uv run python scripts/run_h2_emulator.py --device H2-1LE       # noiseless, free
uv run python scripts/run_h2_emulator.py --device H2-Emulator \
    --instances cr8-uniforme --seeds 0 --shots 1024            # H2 noise model
```

The script reuses the angles optimized locally (hybrid split: classical
optimization on exact statevector, quantum sampling on the emulator), submits
through [qnexus](https://pypi.org/project/qnexus/), and caches results under
`runs/nexus/` — so `reproduce.py` regenerates the noise-analysis figure
**offline**, without credentials. Every reported cut is recomputed classically
from the sampled bitstrings (backend-agnostic verification).

## What is in the box

| Path | What |
| --- | --- |
| `data/` | Frozen Max-Cut instances with proven optima (two independent anchors) + SHA-256 canonical digests: IEEE 9/14/30 (pandapower) and cr8/cr6 (real ICE data, raw snapshots in `data/raw/`) |
| `src/reto1/` | `instances` (digest-verified loading) · `qubo` (exact QUBO, exhaustively verified) · `maxcut` (brute force, greedy, SA) · `gw` (CVXPY SDP + rounding, with SDP upper bound) · `qaoa` (Qiskit circuits, seeded optimization + sampling) · `emulator` (pytket decoding) · `experiments` (multi-seed statistics) · `plots` |
| `scripts/` | `build_cr_instances.py` (ICE data → cr8/cr6, deterministic) · `run_h2_emulator.py` |
| `reproduce.py` | Single entry point |

## Honest limitations

- **QAOA does not beat Goemans-Williamson on any Max-Cut instance today.** At
  p=1 the guaranteed ratio (0.6924) is strictly below GW's (0.878); on our
  instances GW additionally *finds the exact optimum*. At these sizes (6–30
  nodes) exact classical solvers answer in milliseconds — the value of the
  exercise is the verified hybrid workflow, not a quantum speedup.
- QAOA angle optimization runs on the exact local statevector; the emulator is
  used for sampling and noise analysis, not for in-the-loop optimization
  (documented hybrid split — standard practice at NISQ scale).
- The remote H-series emulator does not expose a shot-level seed, so emulator
  statistics are sampling statistics, not exact replicas.
- `cr8`'s `voltaje` weights are a documented proxy (sum of kV levels per
  corridor); the open data carries no MVA capacity or load-flow case. The
  `uniforme` convention is topology-only and assumption-free.
- Physical islanding feasibility (generator/load balance per zone, N-1) is NOT
  encoded in plain Max-Cut; it is discussed in the report and maps to the
  official "constraint mixers" extension.

## License

MIT
