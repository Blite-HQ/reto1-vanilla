"""Loading and integrity-checking of Max-Cut benchmark instances.

Each instance is a JSON file with a known optimum and an embedded SHA-256
digest of its canonical form (sorted keys, no spaces, ensure_ascii, digest
field excluded). The digest is the identity of the instance: an edited file
fails loudly instead of silently benchmarking against a corrupted optimum.
"""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

Edge = tuple[int, int, int]


@dataclass(frozen=True)
class Instance:
    """A weighted Max-Cut instance with a proven optimum."""

    name: str
    convention: str
    n_nodes: int
    edges: tuple[Edge, ...]
    scale: int
    optimum: int
    canonical_assignment: tuple[int, ...]
    methods: tuple[str, ...]
    digest: str

    @property
    def total_weight(self) -> int:
        return sum(w for _, _, w in self.edges)


def canonical_digest(record: dict) -> str:
    """SHA-256 of the canonical JSON serialization, excluding the digest field."""
    body = {k: v for k, v in record.items() if k != "digest"}
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class OpenInstance:
    """A weighted Max-Cut instance with NO proven optimum (national ladder).

    The file carries only the graph and its provenance, never solution
    claims; benchmarks report the honest interval [best found, SDP bound].
    """

    name: str
    convention: str
    n_nodes: int
    edges: tuple[Edge, ...]
    digest: str

    @property
    def total_weight(self) -> int:
        return sum(w for _, _, w in self.edges)


def _verified_record(path: Path) -> dict:
    """Read an instance JSON and check its embedded canonical digest."""
    record = json.loads(path.read_text(encoding="utf-8"))
    embedded = record.get("digest")
    if not embedded:
        raise ValueError(f"{path.name}: missing digest field")
    computed = canonical_digest(record)
    if computed != embedded:
        raise ValueError(
            f"{path.name}: digest mismatch (embedded {embedded[:12]}…, "
            f"computed {computed[:12]}…) — file was modified after freezing"
        )
    return record


def load_instance(path: Path) -> Instance:
    """Load an instance JSON, verifying its embedded digest."""
    record = _verified_record(path)
    return Instance(
        name=f"{record['instancia']}-{record['convencion']}",
        convention=record["convencion"],
        n_nodes=int(record["n_nodos"]),
        edges=tuple((int(i), int(j), int(w)) for i, j, w in record["aristas"]),
        scale=int(record["escala"]),
        optimum=int(record["optimo"]),
        canonical_assignment=tuple(int(x) for x in record["asignacion_canonica"]),
        methods=tuple(record["metodos"]),
        digest=record["digest"],
    )


def load_open_instance(path: Path) -> OpenInstance:
    """Load an open (no proven optimum) instance JSON, verifying its digest."""
    record = _verified_record(path)
    if "optimo" in record:
        raise ValueError(f"{path.name}: carries a frozen optimum — use load_instance")
    return OpenInstance(
        name=f"{record['instancia']}-{record['convencion']}",
        convention=record["convencion"],
        n_nodes=int(record["n_nodos"]),
        edges=tuple((int(i), int(j), int(w)) for i, j, w in record["aristas"]),
        digest=record["digest"],
    )


def list_instances(data_dir: Path) -> list[str]:
    """Names (without extension) of every instance JSON in the data directory."""
    return sorted(p.stem for p in data_dir.glob("*.json"))
