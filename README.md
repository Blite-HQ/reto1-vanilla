# Quantathon CR 2026 — Challenge 1: Fault-Zone Partitioning as Max-Cut

Partition a real power grid into fault-isolation zones by modeling the problem as
**Max-Cut**, casting it as a **QUBO**, solving it with **QAOA** on Quantinuum's **H2
emulator**, and benchmarking the result honestly against the strongest classical
baselines: exact solvers, **Goemans-Williamson** (SDP rounding, ratio ≥ 0.878),
greedy (≈ 0.5) and simulated annealing.

> Status: under construction during the hackathon. Every figure and number in the
> report is reproduced by a single entry point (see below).

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python reproduce.py            # regenerates every figure and number of the report
```

Developed with [uv](https://docs.astral.sh/uv/) (`uv sync --all-groups`); the
`requirements.txt` is exported from the lock file, so both paths give the same
environment.

## Instances

`data/` ships weighted Max-Cut instances derived from standard IEEE power-system
test cases (via `pandapower`) and — where noted — from open data of the Costa Rican
Electricity Institute (ICE). Each JSON embeds a SHA-256 digest of its canonical
form and the **known optimum**, proven by two independent anchors (CP-SAT with
optimality proof + exhaustive enumeration). See `data/README.md`.

## Honest limitations

QAOA does not currently outperform Goemans-Williamson for Max-Cut on any graph
instance: at p=1 the guaranteed approximation ratio (0.6924) is strictly below
GW's (0.878). This project reports that gap explicitly, with error bars across
seeds — see the report's Limitations section.

## License

MIT
