#!/usr/bin/env python3
"""Build the cr8/cr6 Max-Cut instances from ICE open data (Costa Rican grid).

Sources (retrieved 2026-07-23, public open data portal of Grupo ICE):
- https://services1.arcgis.com/cW2GfO4rBCLoFwgj/arcgis/rest/services/LineasDeTransmision/FeatureServer
- https://services1.arcgis.com/cW2GfO4rBCLoFwgj/arcgis/rest/services/Subestaciones/FeatureServer
Raw snapshots are committed under data/raw/ so this script is reproducible
offline and the derivation is auditable end to end.

Derivation, fully deterministic:
1. Parse each line's `Circuito` field ("A-B", optionally suffixed with a
   circuit number, e.g. "San Miguel-Lindora2") into two endpoints; normalize
   accents/case; strip trailing circuit digits; try the "La <name>" variant
   when the bare name is not a substation.
2. Build the national graph over endpoints that are known substations
   (edges between them; parallel circuits aggregated).
3. Corridor selection (cr8): start at the highest-degree substation and
   greedily add the neighboring substation that maximizes induced edge count
   (ties broken alphabetically) until 8 nodes. cr6 = first 6 nodes of the
   same growth sequence. This yields the densest (cycle-rich) corridor of the
   network under a criterion a reader can re-run by hand.
4. Weights: `uniforme` -> w = number of parallel circuits between the pair
   (cutting the pair opens all of them); `voltaje` -> w = sum of the
   circuits' voltage levels in kV (documented proxy for the cost of opening
   the corridor; the open data has no MVA capacity).
5. Optimum proven by two independent anchors (itertools enumeration +
   numpy bit-trick spectrum); the script aborts without writing if they
   disagree. Same JSON schema + canonical SHA-256 digest as the IEEE
   instances in data/.

Run from the repo root:  uv run python scripts/build_cr_instances.py
"""

import json
import sys
import unicodedata
from pathlib import Path

import networkx as nx
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from reto1.instances import canonical_digest  # noqa: E402
from reto1.maxcut import brute_force  # noqa: E402

RAW_DIR = Path("data/raw")
OUT_DIR = Path("data")
RETRIEVED = "2026-07-23"
SOURCES = {
    "lineas": "https://services1.arcgis.com/cW2GfO4rBCLoFwgj/arcgis/rest/services/LineasDeTransmision/FeatureServer",
    "subestaciones": "https://services1.arcgis.com/cW2GfO4rBCLoFwgj/arcgis/rest/services/Subestaciones/FeatureServer",
    "portal": "https://datos-ice-se.opendata.arcgis.com",
}
CORRIDOR_SIZES = {"cr8": 8, "cr6": 6}
CONVENTIONS = ("uniforme", "voltaje")


def norm(name: str) -> str:
    flat = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode()
    return flat.lower().strip()


def parse_endpoint(token: str, substations: dict[str, str]) -> str | None:
    """Normalized circuit endpoint -> substation key, or None if unknown."""
    candidate = norm(token).rstrip("0123456789").strip()
    if candidate in substations:
        return candidate
    if f"la {candidate}" in substations:
        return f"la {candidate}"
    return None


def load_national_graph() -> tuple[nx.Graph, dict[str, dict]]:
    lines = json.loads((RAW_DIR / "ice-lineas-transmision.geojson").read_text())["features"]
    subs = json.loads((RAW_DIR / "ice-subestaciones.geojson").read_text())["features"]
    substations = {norm(f["properties"]["Subestacio"]): f["properties"] for f in subs}

    graph = nx.Graph()
    skipped = []
    for feature in lines:
        props = feature["properties"]
        parts = (props["Circuito"] or "").split("-")
        endpoints = [parse_endpoint(t, substations) for t in parts] if len(parts) == 2 else []
        if len(endpoints) == 2 and all(endpoints) and endpoints[0] != endpoints[1]:
            a, b = sorted(endpoints)  # type: ignore[type-var]
            if graph.has_edge(a, b):
                graph[a][b]["circuits"] += 1
                graph[a][b]["voltage_sum"] += int(props["Voltaje"])
            else:
                graph.add_edge(a, b, circuits=1, voltage_sum=int(props["Voltaje"]))
        else:
            skipped.append(props["Circuito"])
    print(f"lineas usadas: {sum(d['circuits'] for _, _, d in graph.edges(data=True))}"
          f" / {len(lines)}  (descartadas por endpoint desconocido: {len(skipped)})")
    for circ in skipped:
        print(f"  descartada: {circ}")
    return graph, substations


def grow_corridor(graph: nx.Graph, size: int) -> list[str]:
    """Deterministic greedy densest corridor from the highest-degree node."""
    seed = min(sorted(graph.nodes), key=lambda v: (-graph.degree(v), v))
    corridor = [seed]
    while len(corridor) < size:
        frontier = sorted({n for v in corridor for n in graph.neighbors(v)} - set(corridor))
        best = max(frontier,
                   key=lambda c: (sum(graph.has_edge(c, v) for v in corridor), ), default=None)
        # max() with alphabetical tie-break: frontier is sorted, max keeps the
        # FIRST occurrence of the top key, i.e. the alphabetically smallest.
        if best is None:
            raise AssertionError("corridor cannot grow: disconnected frontier")
        corridor.append(best)
    return corridor


def spectrum_optimum(n: int, edges: list[list[int]]) -> int:
    """Second anchor: vectorized enumeration via bit tricks (independent code)."""
    indices = np.arange(2**n, dtype=np.int64)
    cuts = np.zeros(2**n, dtype=np.int64)
    for i, j, w in edges:
        cuts += w * (((indices >> i) & 1) ^ ((indices >> j) & 1))
    return int(cuts.max())


def build_instance(name: str, corridor: list[str], graph: nx.Graph,
                   substations: dict[str, dict], convention: str) -> dict:
    index = {node: k for k, node in enumerate(corridor)}
    edges = []
    for a, b, data in graph.subgraph(corridor).edges(data=True):
        i, j = sorted((index[a], index[b]))
        w = data["circuits"] if convention == "uniforme" else data["voltage_sum"]
        edges.append([i, j, int(w)])
    edges.sort()

    sub = nx.Graph((i, j) for i, j, _ in edges)
    if not nx.is_connected(sub) or sub.number_of_nodes() != len(corridor):
        raise AssertionError(f"{name}: corridor subgraph not connected")

    optimum, assignment = brute_force(len(corridor), [tuple(e) for e in edges])
    anchor2 = spectrum_optimum(len(corridor), edges)
    if anchor2 != optimum:
        raise AssertionError(f"{name}/{convention}: anchors disagree "
                             f"(bruteforce={optimum}, spectrum={anchor2})")

    record = {
        "instancia": name,
        "convencion": convention,
        "n_nodos": len(corridor),
        "aristas": edges,
        "escala": 1,
        "optimo": optimum,
        "asignacion_canonica": list(assignment),
        "metodos": ["bruteforce", "spectrum"],
        "solver_status": "OPTIMAL",
        "nodos": {str(index[node]): substations[node]["Subestacio"] for node in corridor},
        "fuente": SOURCES,
        "descargado": RETRIEVED,
        "criterio_corredor": "greedy densest desde la subestacion de mayor grado, "
                             "desempate alfabetico (ver scripts/build_cr_instances.py)",
        "definicion_peso": ("1 por circuito paralelo" if convention == "uniforme"
                            else "suma de niveles de tension (kV) de los circuitos paralelos"),
    }
    return {**record, "digest": canonical_digest(record)}


def main() -> None:
    graph, substations = load_national_graph()
    corridor8 = grow_corridor(graph, CORRIDOR_SIZES["cr8"])
    corridors = {"cr8": corridor8, "cr6": corridor8[: CORRIDOR_SIZES["cr6"]]}
    print(f"\ncorredor cr8: {corridors['cr8']}")

    rows = []
    for name, corridor in corridors.items():
        for convention in CONVENTIONS:
            record = build_instance(name, corridor, graph, substations, convention)
            path = OUT_DIR / f"{name}-{convention}.json"
            path.write_text(json.dumps(record, sort_keys=True, indent=2,
                                       ensure_ascii=True) + "\n", encoding="utf-8")
            rows.append((record["instancia"], convention, record["n_nodos"],
                         len(record["aristas"]), record["optimo"], record["digest"][:12]))
    print(f"\n{'instancia':10} {'convencion':10} {'n':>3} {'|E|':>4} {'optimo':>7} digest")
    for row in rows:
        print(f"{row[0]:10} {row[1]:10} {row[2]:>3} {row[3]:>4} {row[4]:>7} {row[5]}")


if __name__ == "__main__":
    main()
