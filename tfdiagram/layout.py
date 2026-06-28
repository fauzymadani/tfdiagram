"""Use graphviz `dot` purely as a layout engine.

We feed it sized boxes + edges, read back `-Tjson` coordinates, and flip to
SVG space (top-left origin). Rendering is done by render.py — dot never draws.
"""
import json
import subprocess
import sys
from dataclasses import dataclass, field

from .model import Graph
from .style import kind_label

CARD_W = 214        # px
CARD_H = 78


@dataclass
class Layout:
    width: float
    height: float
    nodes: dict = field(default_factory=dict)      # id -> (x, y, w, h) top-left
    clusters: list = field(default_factory=list)   # (id, x, y, w, h)
    edges: list = field(default_factory=list)      # list of [(x, y), ...]


def build_dot(g: Graph) -> str:
    parent = {n: r.parent for n, r in g.nodes.items()}
    lines = [
        "digraph infra {",
        'graph [rankdir=LR nodesep=0.55 ranksep=0.95 fontname="Helvetica" '
        "fontsize=14 margin=0];",
        f'node [shape=box fixedsize=true width={CARD_W / 72:.3f} '
        f'height={CARD_H / 72:.3f}];',
    ]

    def emit(nid, pad):
        r = g.nodes[nid]
        kids = g.children_of(nid)
        if r.is_container:
            lines.append(f'{pad}subgraph "cluster_{nid}" {{')
            lines.append(f'{pad}  label="{kind_label(r.rtype)}"; labelloc=t; '
                         f"labeljust=l; fontsize=14; margin=16; style=rounded;")
            for c in kids:
                emit(c, pad + "  ")
            if not kids:                         # keep empty container sized
                lines.append(f'{pad}  "{nid}::pad" [style=invis width=1.4 '
                             f'height=0.5];')
            lines.append(f"{pad}}}")
        else:
            lines.append(f'{pad}"{nid}";')

    for root in g.roots():
        emit(root, "  ")

    for src, dst in g.edges:
        if parent.get(dst) == src or parent.get(src) == dst:
            continue                             # containment, shown by nesting
        if g.nodes[src].is_container or g.nodes[dst].is_container:
            continue                             # ponytail: skip cluster edges
        lines.append(f'  "{src}" -> "{dst}";')
    lines.append("}")
    return "\n".join(lines)


def run(g: Graph) -> Layout:
    dot = build_dot(g)
    try:
        out = subprocess.run(["dot", "-Tjson"], input=dot, text=True,
                             capture_output=True, check=True).stdout
    except FileNotFoundError:
        sys.exit("error: graphviz `dot` not found. Install graphviz.")
    except subprocess.CalledProcessError as e:
        sys.exit(f"dot failed: {e.stderr}")

    data = json.loads(out)
    _, _, W, H = (float(v) for v in data["bb"].split(","))
    lay = Layout(width=W, height=H)

    for o in data.get("objects", []):
        name = o.get("name", "")
        if name.startswith("cluster_"):
            x1, y1, x2, y2 = (float(v) for v in o["bb"].split(","))
            lay.clusters.append((name[8:], x1, H - y2, x2 - x1, y2 - y1))
        elif "pos" in o and "::pad" not in name:
            px, py = (float(v) for v in o["pos"].split(","))
            w, h = float(o["width"]) * 72, float(o["height"]) * 72
            lay.nodes[name] = (px - w / 2, H - (py + h / 2), w, h)

    for e in data.get("edges", []):
        pts = next((op["points"] for op in e.get("_draw_", [])
                    if op.get("op") in ("b", "B") and "points" in op), None)
        if pts:
            lay.edges.append([(x, H - y) for x, y in pts])
    return lay
