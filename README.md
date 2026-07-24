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

The comparison then scales to **the whole country**: the same deterministic
corridor-growth criterion yields a nested family cr8 ⊂ cr12 ⊂ cr16 ⊂ cr20 ⊂
cr26 ⊂ … ⊂ **cr68 = the full national transmission graph** (68 substations).
Up to 20 nodes the optimum is proven (double anchor) and QAOA runs with full
statistics; beyond the documented quantum walls (20 qubits for local angle
optimization, 26 for the H2 emulator) instances are **classical-only** and
reported with the honest interval **[best cut found, SDP upper bound]** — no
faked optima (`data/nacional/`, `scripts/build_cr_ladder.py`).

## Dashboard

A single-file, no-build visual summary — the partitioned cr8 corridor, the
full national grid map, r vs p, classical baselines and the honest
limitations — lives at `docs/index.html`. Open it directly or serve
`docs/` with GitHub Pages.

## Reproduce everything

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python reproduce.py            # every figure and number of the report
python reproduce.py --quick    # fast smoke pass (skips the national ladder)
```

The full run takes a while (~1 h, dominated by angle optimization on the
20-qubit corridor); `--quick` finishes in minutes.

Developed with [uv](https://docs.astral.sh/uv/) (`uv sync --all-groups`);
`requirements.txt` is exported from the lock file, so both paths give the same
environment. Tests: `pytest` (41 tests).

Outputs: `figures/*.{pdf,png}`, `runs/local/*.json` (raw records with SHA-256
digests), `RESULTS.md` (summary tables).

## Guppy parity port (Selene emulator)

The headline circuit is also written in **Guppy** (Quantinuum's recommended
SDK) and executed on the Selene/Quest emulator, reusing the same optimized
angles — RZZ decomposed exactly as CX·RZ·CX, angles in half-turns (tket
convention). Parity criterion: sampled mean cut within 4σ of the exact
expectation (it lands within 1σ; see `runs/guppy/` and `tests/test_guppy.py`).

```bash
uv sync --all-groups                        # `entregables` dependency group
uv run python scripts/run_guppy_qaoa.py     # cr8, p=1 — prints the verdict
```

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
| `data/` | Frozen Max-Cut instances with proven optima (two independent anchors) + SHA-256 canonical digests: IEEE 9/14/30 (pandapower) and cr6…cr20 (real ICE data, raw snapshots in `data/raw/`) |
| `data/nacional/` | Open instances cr26…cr68 (no optimum claimed — graph + provenance + digest only) |
| `src/reto1/` | `instances` (digest-verified loading) · `qubo` (exact QUBO, exhaustively verified) · `maxcut` (brute force, greedy, SA) · `gw` (CVXPY SDP + rounding, with SDP upper bound) · `qaoa` (Qiskit circuits, seeded optimization + sampling; vectorized ⟨C⟩ engine for n ≥ 15, parity-tested) · `emulator` (pytket decoding) · `experiments` (multi-seed statistics + open-instance benchmarks) · `plots` |
| `scripts/` | `build_cr_instances.py` (ICE data → cr8/cr6) · `build_cr_ladder.py` (national ladder) · `run_h2_emulator.py` (Nexus) · `run_guppy_qaoa.py` (Guppy/Selene parity port) |
| `notebooks/` | `reto1.ipynb` — the narrative walkthrough, end to end (executed) |
| `reproduce.py` | Single entry point |
| `STATEMENT-SDK.md` | ≤200-word SDK statement (deliverable) |

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
- The national ladder has no quantum leg beyond 20 nodes (local angle
  optimization on the dense statevector) and none is possible beyond 26 (H2
  emulator ceiling); those instances are reported as [best classical cut,
  SDP upper bound] intervals with no optimum claimed.
- Physical islanding feasibility (generator/load balance per zone, N-1) is NOT
  encoded in plain Max-Cut; it is discussed in the report and maps to the
  official "constraint mixers" extension.

## License

MIT
