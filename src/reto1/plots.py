"""Report figures (matplotlib, vector PDF + PNG).

Palette: Okabe-Ito subset, validated for CVD separation, lightness band,
chroma and contrast (dataviz six-checks validator, light surface):
QAOA #0072B2 / GW #D55E00 / greedy #009E73 / neutral #666666.
One axis per figure; direct labels instead of legend boxes where possible;
recessive grid.
"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import networkx as nx  # noqa: E402

COLOR_QAOA = "#0072B2"
COLOR_GW = "#D55E00"
COLOR_GREEDY = "#009E73"
COLOR_NEUTRAL = "#666666"
COLOR_INK = "#1a1a1a"
SIDE_FILLS = ("#a6cbe3", "#f4b988")  # light fills for the two partition sides

GW_GUARANTEE = 0.878
QAOA_P1_GUARANTEE = 0.6924


def _style(ax: plt.Axes) -> None:
    ax.grid(axis="y", color="#dddddd", linewidth=0.6)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


def figure_ratio_vs_p(instance_name: str, sweep: dict, classical: dict,
                      out_base: Path) -> None:
    """Headline figure: r vs p with error bars against the classical baselines."""
    p_values = sorted(sweep.keys())
    mean = [sweep[p]["ratio_expected"]["mean"] for p in p_values]
    std = [sweep[p]["ratio_expected"]["std"] for p in p_values]
    best = [sweep[p]["ratio_best"]["mean"] for p in p_values]
    best_std = [sweep[p]["ratio_best"]["std"] for p in p_values]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.errorbar(p_values, mean, yerr=std, color=COLOR_QAOA, linewidth=2,
                marker="o", markersize=7, capsize=4, label="QAOA ⟨cut⟩ / óptimo")
    ax.errorbar(p_values, best, yerr=best_std, color=COLOR_QAOA, linewidth=1.6,
                linestyle="--", marker="o", markersize=7, markerfacecolor="white",
                capsize=4, label="QAOA mejor muestra / óptimo")

    gw_ratio = classical["gw"]["ratio_best"]
    greedy_ratio = classical["greedy"]["ratio"]
    references = [
        (gw_ratio, f"GW logrado ({gw_ratio:.3f})", COLOR_GW, "-", 1.6),
        (greedy_ratio, f"greedy ({greedy_ratio:.3f})", COLOR_GREEDY, ":", 1.6),
        (GW_GUARANTEE, "garantía GW 0.878", COLOR_NEUTRAL, "--", 0.9),
    ]
    for value, _, color, style, width in references:
        ax.axhline(value, color=color, linewidth=width, linestyle=style)
    # Stagger the direct labels so coinciding reference lines stay readable.
    x_right = p_values[-1] + 0.08
    min_gap = 0.045
    placed: list[float] = []
    for value, text, color, _, _ in sorted(references, key=lambda r: -r[0]):
        y = value
        while any(abs(y - other) < min_gap for other in placed):
            y -= min_gap
        placed.append(y)
        ax.text(x_right, y, text, color=color, va="center", fontsize=8.5)

    ax.set_xlabel("profundidad p")
    ax.set_ylabel("razón de aproximación r")
    ax.set_xticks(p_values)
    ax.set_xlim(p_values[0] - 0.2, p_values[-1] + 1.15)
    ax.set_ylim(0.0, 1.08)
    ax.set_title(f"{instance_name}: QAOA vs líneas base clásicas "
                 f"(media ± σ, {sweep[p_values[0]]['ratio_expected']['n']} semillas)",
                 fontsize=11, color=COLOR_INK)
    ax.legend(loc="lower right", frameon=False, fontsize=9)
    _style(ax)
    fig.tight_layout()
    fig.savefig(out_base.with_suffix(".pdf"))
    fig.savefig(out_base.with_suffix(".png"), dpi=200)
    plt.close(fig)


def figure_ratio_vs_p_multi(sweeps: dict[str, dict], out_base: Path) -> None:
    """Scaling view: mean r vs p, one line per instance (fixed hue order)."""
    palette = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00"]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for color, (name, sweep) in zip(palette, sorted(sweeps.items()), strict=False):
        p_values = sorted(sweep.keys())
        mean = [sweep[p]["ratio_expected"]["mean"] for p in p_values]
        std = [sweep[p]["ratio_expected"]["std"] for p in p_values]
        ax.errorbar(p_values, mean, yerr=std, color=color, linewidth=2, marker="o",
                    markersize=6, capsize=3, label=name)
    ax.axhline(GW_GUARANTEE, color=COLOR_NEUTRAL, linewidth=0.9, linestyle="--")
    ax.text(0.99, GW_GUARANTEE + 0.012, "garantía GW 0.878", color=COLOR_NEUTRAL,
            transform=ax.get_yaxis_transform(), ha="right", fontsize=8)
    ax.set_xlabel("profundidad p")
    ax.set_ylabel("razón de aproximación r (media ± σ)")
    ax.set_ylim(0.0, 1.08)
    ax.set_xticks(sorted({p for sweep in sweeps.values() for p in sweep}))
    ax.set_title("Escalado: r vs p por instancia", fontsize=11, color=COLOR_INK)
    ax.legend(loc="lower right", frameon=False, fontsize=9)
    _style(ax)
    fig.tight_layout()
    fig.savefig(out_base.with_suffix(".pdf"))
    fig.savefig(out_base.with_suffix(".png"), dpi=200)
    plt.close(fig)


def figure_noise_comparison(records: list[dict], local_sweeps: dict[str, dict],
                            out_base: Path) -> None:
    """Noise analysis: r on the noisy H2 emulator vs the noiseless references.

    One point per (instance, p): noisy emulator sampled mean vs free noiseless
    emulator vs local exact expectation. Grouped dot plot, one axis.
    """
    ideal = {(r["instance"], r["p"]): r["stats"]["ratio_mean"]
             for r in records if r["device"] in ("H2-1LE", "H1-1LE")}
    noisy = {(r["instance"], r["p"]): r["stats"]["ratio_mean"]
             for r in records if r["device"] not in ("H2-1LE", "H1-1LE")}
    keys = sorted(set(ideal) | set(noisy))
    if not keys:
        return
    labels = [f"{name} p={p}" for name, p in keys]
    x = range(len(keys))

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    exact = [local_sweeps.get(name, {}).get(p, {})
             .get("ratio_expected", {}).get("mean") for name, p in keys]
    ax.scatter(x, exact, marker="_", s=520, color=COLOR_INK, linewidths=2,
               label="statevector local (exacto, sin ruido)")
    ax.scatter(x, [ideal.get(k) for k in keys], s=70, color=COLOR_QAOA,
               label="emulador H2-1LE (sin ruido, muestreado)")
    ax.scatter(x, [noisy.get(k) for k in keys], s=70, color=COLOR_GW,
               label="emulador H2 (modelo de ruido H-series)")
    ax.set_xticks(list(x), labels, fontsize=7.5, rotation=30, ha="right")
    ax.set_ylabel("razón de aproximación r (media de shots)")
    ax.set_ylim(0.0, 1.08)
    ax.set_title("Análisis de ruido: emulador H2 con ruido vs referencias ideales",
                 fontsize=11, color=COLOR_INK)
    ax.legend(loc="lower right", frameon=False, fontsize=8.5)
    _style(ax)
    fig.tight_layout()
    fig.savefig(out_base.with_suffix(".pdf"))
    fig.savefig(out_base.with_suffix(".png"), dpi=200)
    plt.close(fig)


def _substation_coordinates(raw_path: Path) -> dict[str, tuple[float, float]]:
    """Display name -> (lon, lat) from the raw ICE substations GeoJSON."""
    features = json.loads(raw_path.read_text())["features"]
    return {f["properties"]["Subestacio"]: tuple(f["geometry"]["coordinates"])
            for f in features}


def figure_national_map(instance_path: Path, assignment: list[int],
                        open_report: dict, raw_substations: Path,
                        highlight_names: set[str], out_base: Path) -> None:
    """The national grid on real WGS84 coordinates, colored by fault zone.

    Kept corridors solid, cut corridors dashed; the cr8 headline corridor is
    ring-highlighted. The title reports the honest interval: best classical
    cut found and the rigorous SDP upper bound.
    """
    record = json.loads(instance_path.read_text())
    names = {int(k): v for k, v in record["nodos"].items()}
    coords = _substation_coordinates(raw_substations)
    pos = {v: coords[names[v]] for v in range(record["n_nodos"])}

    graph = nx.Graph()
    graph.add_nodes_from(range(record["n_nodos"]))
    graph.add_weighted_edges_from((i, j, w) for i, j, w in record["aristas"])

    fig, ax = plt.subplots(figsize=(9, 6.5))
    kept = [(i, j) for i, j, _ in record["aristas"] if assignment[i] == assignment[j]]
    cut = [(i, j) for i, j, _ in record["aristas"] if assignment[i] != assignment[j]]
    nx.draw_networkx_edges(graph, pos, edgelist=kept, width=1.2,
                           edge_color=COLOR_NEUTRAL, ax=ax)
    nx.draw_networkx_edges(graph, pos, edgelist=cut, width=1.6, style="dashed",
                           edge_color=COLOR_GW, ax=ax)
    node_colors = [SIDE_FILLS[assignment[v]] for v in graph.nodes]
    rings = [2.0 if names[v] in highlight_names else 0.7 for v in graph.nodes]
    nx.draw_networkx_nodes(graph, pos, node_color=node_colors, node_size=110,
                           edgecolors=COLOR_INK, linewidths=rings, ax=ax)
    for v in graph.nodes:
        if names[v] in highlight_names:
            x, y = pos[v]
            ax.annotate(names[v], (x, y), textcoords="offset points",
                        xytext=(4, 4), fontsize=6.5, color=COLOR_INK)

    low, high = open_report["optimum_interval"]
    ax.set_title(f"Red de transmisión de Costa Rica ({record['n_nodos']} subestaciones, "
                 f"datos ICE): partición en zonas de falla\n"
                 f"mejor corte clásico = {low} ({open_report['best_method'].upper()}), "
                 f"cota superior SDP = {high:.1f} — corredor cr8 resaltado",
                 fontsize=10.5, color=COLOR_INK)
    ax.set_xlabel("longitud")
    ax.set_ylabel("latitud")
    ax.set_aspect("equal")
    _style(ax)
    fig.tight_layout()
    fig.savefig(out_base.with_suffix(".pdf"))
    fig.savefig(out_base.with_suffix(".png"), dpi=200)
    plt.close(fig)


def figure_national_scaling(quantum_points: list[tuple[int, float, float]],
                            open_points: list[tuple[int, float]],
                            out_base: Path) -> None:
    """Approximation quality vs instance size across the national ladder.

    Quantum points: QAOA mean r ± σ (deepest p) on corridors with a proven
    optimum. Open points: LOWER bounds (best classical / SDP bound) — the true
    r of the best classical cut is at least this. Vertical walls mark the
    documented limits: local statevector optimization (20 qubits) and the H2
    emulator ceiling (26 qubits); beyond them the honest answer is classical.
    """
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    q_n = [n for n, _, _ in quantum_points]
    q_mean = [m for _, m, _ in quantum_points]
    q_std = [s for _, _, s in quantum_points]
    ax.errorbar(q_n, q_mean, yerr=q_std, color=COLOR_QAOA, linewidth=2,
                marker="o", markersize=7, capsize=4,
                label="QAOA ⟨cut⟩/óptimo (óptimo probado)")
    o_n = [n for n, _ in open_points]
    o_r = [r for _, r in open_points]
    ax.plot(o_n, o_r, color=COLOR_GW, linewidth=0, marker="^", markersize=8,
            label="cota inferior: mejor clásico / cota SDP")
    ax.axhline(GW_GUARANTEE, color=COLOR_NEUTRAL, linewidth=0.9, linestyle="--")
    ax.text(0.02, GW_GUARANTEE + 0.012, "garantía GW 0.878", color=COLOR_NEUTRAL,
            transform=ax.get_yaxis_transform(), fontsize=8)

    top = max(o_n) + 3
    ax.axvline(20, color=COLOR_NEUTRAL, linewidth=0.9, linestyle=":")
    ax.axvline(26, color=COLOR_NEUTRAL, linewidth=0.9, linestyle=":")
    ax.axvspan(26, top, color="#f2f2f2", zorder=0)
    for x, text in ((20, "límite optimización local (20 qubits)"),
                    (26, "techo emulador H2 (26 qubits)")):
        ax.text(x, 0.06, text, rotation=90, fontsize=7.5, color=COLOR_NEUTRAL,
                ha="right", va="bottom")
    ax.text((26 + top) / 2, 0.06, "solo clásico +\nextrapolación honesta",
            fontsize=8, color=COLOR_NEUTRAL, ha="center", va="bottom")

    ax.set_xlabel("tamaño de instancia n (subestaciones)")
    ax.set_ylabel("razón de aproximación r")
    ax.set_xlim(4, top)
    ax.set_ylim(0.0, 1.08)
    ax.set_title("Escalado en la red nacional ICE: corredores anidados cr6 → cr68",
                 fontsize=11, color=COLOR_INK)
    ax.legend(loc="lower right", frameon=False, fontsize=8.5)
    _style(ax)
    fig.tight_layout()
    fig.savefig(out_base.with_suffix(".pdf"))
    fig.savefig(out_base.with_suffix(".png"), dpi=200)
    plt.close(fig)


def figure_partition(instance_path: Path, assignment: list[int],
                     out_base: Path) -> None:
    """Grid graph colored by fault zone; cut corridors dashed."""
    record = json.loads(instance_path.read_text())
    edges = record["aristas"]
    labels = {int(k): v for k, v in record.get("nodos", {}).items()}

    graph = nx.Graph()
    graph.add_nodes_from(range(record["n_nodos"]))
    graph.add_weighted_edges_from((i, j, w) for i, j, w in edges)
    pos = nx.kamada_kawai_layout(graph)

    fig, ax = plt.subplots(figsize=(7, 5.5))
    node_colors = [SIDE_FILLS[assignment[v]] for v in graph.nodes]
    nx.draw_networkx_nodes(graph, pos, node_color=node_colors, node_size=1100,
                           edgecolors=COLOR_INK, linewidths=1.2, ax=ax)
    kept = [(i, j) for i, j, _ in edges if assignment[i] == assignment[j]]
    cut = [(i, j) for i, j, _ in edges if assignment[i] != assignment[j]]
    nx.draw_networkx_edges(graph, pos, edgelist=kept, width=2,
                           edge_color=COLOR_NEUTRAL, ax=ax)
    nx.draw_networkx_edges(graph, pos, edgelist=cut, width=2, style="dashed",
                           edge_color=COLOR_GW, ax=ax)
    names = {v: labels.get(v, str(v)) for v in graph.nodes}
    nx.draw_networkx_labels(graph, pos, labels=names, font_size=8,
                            font_color=COLOR_INK, ax=ax)
    ax.set_title(f"{record['instancia']}-{record['convencion']}: zonas de falla "
                 f"óptimas (corte = {record['optimo']})", fontsize=11, color=COLOR_INK)
    ax.margins(0.12)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(out_base.with_suffix(".pdf"))
    fig.savefig(out_base.with_suffix(".png"), dpi=200)
    plt.close(fig)
