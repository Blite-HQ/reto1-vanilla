#!/usr/bin/env python3
"""Extend the ICE-derived corridor family to the whole national grid.

The same deterministic growth criterion as build_cr_instances.py (greedy
densest corridor from the highest-degree substation, La Caja, alphabetical
tie-break) produces a NESTED family:

    cr8 ⊂ cr12 ⊂ cr16 ⊂ cr20 ⊂ cr26 ⊂ cr34 ⊂ cr44 ⊂ cr56 ⊂ cr68

where cr68 is the full connected national transmission graph (68 substations,
90 aggregated corridors from 94 circuits).

- Proven sizes (12, 16, 20): same JSON schema and double optimum anchor as
  cr8 (itertools brute force + vectorized numpy spectrum) -> data/.
- Open sizes (26, 34, 44, 56, 68): NO optimum is claimed — the file carries
  only the graph + provenance + digest -> data/nacional/. Benchmarks report
  the honest interval [best classical found, SDP upper bound].
- Convention: uniforme only (assumption-free: w = parallel circuit count);
  `voltaje` stays a documented proxy on the cr8/cr6 headline instances.

Frozen-file rule: an existing file whose digest differs is reported and the
script aborts — it never overwrites (same policy as build_cr_instances.py).

Run from the repo root:  uv run python scripts/build_cr_ladder.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from build_cr_instances import (  # noqa: E402
    RETRIEVED,
    SOURCES,
    build_instance,
    grow_corridor,
    load_national_graph,
)

from reto1.instances import canonical_digest  # noqa: E402

PROVEN_SIZES = (12, 16, 20)   # double-anchored optimum, quantum-reachable
OPEN_SIZES = (26, 34, 44, 56, 68)  # classical-only, no optimum claimed
CONVENTION = "uniforme"
OUT_PROVEN = Path("data")
OUT_OPEN = Path("data/nacional")
CORRIDOR_CRITERION = ("greedy densest desde la subestacion de mayor grado, "
                      "desempate alfabetico (ver scripts/build_cr_instances.py)")


def build_open_record(name: str, corridor: list[str], graph,
                      substations: dict[str, dict]) -> dict:
    """Open-instance record: the graph and its provenance, no solution claims."""
    index = {node: k for k, node in enumerate(corridor)}
    edges = []
    for a, b, data in graph.subgraph(corridor).edges(data=True):
        i, j = sorted((index[a], index[b]))
        edges.append([i, j, int(data["circuits"])])
    edges.sort()
    record = {
        "instancia": name,
        "convencion": CONVENTION,
        "n_nodos": len(corridor),
        "aristas": edges,
        "escala": 1,
        "nodos": {str(index[node]): substations[node]["Subestacio"] for node in corridor},
        "fuente": SOURCES,
        "descargado": RETRIEVED,
        "criterio_corredor": CORRIDOR_CRITERION,
        "definicion_peso": "1 por circuito paralelo",
    }
    return {**record, "digest": canonical_digest(record)}


def write_frozen(path: Path, record: dict) -> str:
    """Write a frozen instance; never overwrite different content."""
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing.get("digest") == record["digest"]:
            return "sin cambios"
        raise SystemExit(f"{path.name}: existe con digest distinto — "
                         "se reporta, no se sobreescribe")
    path.write_text(json.dumps(record, sort_keys=True, indent=2,
                               ensure_ascii=True) + "\n", encoding="utf-8")
    return "escrito"


def main() -> None:
    graph, substations = load_national_graph()
    full_corridor = grow_corridor(graph, graph.number_of_nodes())
    print(f"\ngrafo nacional: {graph.number_of_nodes()} subestaciones, "
          f"{graph.number_of_edges()} corredores agregados")

    OUT_OPEN.mkdir(parents=True, exist_ok=True)
    rows = []
    for size in PROVEN_SIZES:
        record = build_instance(f"cr{size}", full_corridor[:size], graph,
                                substations, CONVENTION)
        status = write_frozen(OUT_PROVEN / f"cr{size}-{CONVENTION}.json", record)
        rows.append((record["instancia"], record["n_nodos"], len(record["aristas"]),
                     str(record["optimo"]), record["digest"][:12], status))
    for size in OPEN_SIZES:
        record = build_open_record(f"cr{size}", full_corridor[:size], graph, substations)
        status = write_frozen(OUT_OPEN / f"cr{size}-{CONVENTION}.json", record)
        rows.append((record["instancia"], record["n_nodos"], len(record["aristas"]),
                     "abierta", record["digest"][:12], status))

    print(f"\n{'instancia':10} {'n':>3} {'|E|':>4} {'optimo':>8} {'digest':12} estado")
    for name, n, m, opt, digest, status in rows:
        print(f"{name:10} {n:>3} {m:>4} {opt:>8} {digest:12} {status}")


if __name__ == "__main__":
    main()
