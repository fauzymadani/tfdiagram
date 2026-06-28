"""Render a laid-out Graph as a hand-styled SVG (cards, tinted groups, arrows)."""
from xml.sax.saxutils import escape

from .layout import Layout
from .model import Graph
from .style import (CATEGORY_COLOR, FAINT, INK, MUTE, accent_for, category_of,
                    container_style, kind_label, key_attr)

PAD = 24
HEADER_H = 100
FOOTER_H = 34
FONT = "Segoe UI, Roboto, Helvetica, Arial, sans-serif"


def _t(x, y, s, size, fill, weight="400", anchor="start", italic=False):
    style = ' font-style="italic"' if italic else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"'
            f'{style}>{escape(str(s))}</text>')


def _path(points):
    """Cubic-bezier path through graphviz spline control points."""
    if not points:
        return ""
    d = [f"M{points[0][0]:.1f},{points[0][1]:.1f}"]
    i = 1
    while i + 2 < len(points):
        (a, b, c) = points[i:i + 3]
        d.append(f"C{a[0]:.1f},{a[1]:.1f} {b[0]:.1f},{b[1]:.1f} "
                 f"{c[0]:.1f},{c[1]:.1f}")
        i += 3
    while i < len(points):                      # leftover -> straight
        d.append(f"L{points[i][0]:.1f},{points[i][1]:.1f}")
        i += 1
    return " ".join(d)


def render(g: Graph, lay: Layout, title: str, subtitle: str,
           overrides=()) -> str:
    width = max(lay.width + 2 * PAD, 780)
    height = HEADER_H + lay.height + FOOTER_H
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" '
        f'height="{height:.0f}" viewBox="0 0 {width:.0f} {height:.0f}" '
        f'font-family="{FONT}">',
        '<defs>',
        '<marker id="arrow" markerWidth="10" markerHeight="10" refX="8" '
        'refY="3" orient="auto" markerUnits="strokeWidth">'
        f'<path d="M0,0 L8,3 L0,6 Z" fill="{MUTE}"/></marker>',
        '<filter id="card" x="-20%" y="-20%" width="140%" height="140%">'
        '<feDropShadow dx="0" dy="1" stdDeviation="2.2" flood-color="#000" '
        'flood-opacity="0.14"/></filter>',
        '</defs>',
        f'<rect width="{width:.0f}" height="{height:.0f}" fill="#ffffff"/>',
    ]

    # --- header ---
    out.append(_t(PAD + 16, 42, title, 22, INK, "600"))
    out.append(_t(PAD + 16, 66, subtitle, 13, MUTE))
    cats = sorted({category_of(r.rtype) for r in g.nodes.values()
                   if not r.is_container})
    lx = PAD + 16
    for cat in cats:
        out.append(f'<circle cx="{lx + 6:.0f}" cy="84" r="6" '
                   f'fill="{CATEGORY_COLOR[cat]}"/>')
        out.append(_t(lx + 18, 88, cat, 11.5, MUTE))
        lx += 28 + len(cat) * 7

    out.append(f'<g transform="translate({PAD},{HEADER_H})">')

    # --- containers (outermost first so children paint on top) ---
    levels = {r.id: r.level for r in g.nodes.values()}
    for cid, x, y, w, h in sorted(lay.clusters,
                                  key=lambda c: levels.get(c[0], 0)):
        level = levels.get(cid, 0)
        accent, fill = container_style(level)
        out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" '
                   f'height="{h:.1f}" rx="12" fill="{fill}" stroke="{accent}" '
                   f'stroke-width="2"/>')
        out.append(_t(x + 16, y + 24, kind_label(g.nodes[cid].rtype),
                      14, accent, "600"))
        out.append(_t(x + 16, y + 40, g.nodes[cid].name, 11.5, MUTE))

    # --- edges (on top so arrowheads always read) ---
    for pts in lay.edges:
        out.append(f'<path d="{_path(pts)}" fill="none" stroke="{MUTE}" '
                   f'stroke-width="1.5" marker-end="url(#arrow)" '
                   f'opacity="0.85"/>')

    # --- resource cards ---
    for nid, (x, y, w, h) in lay.nodes.items():
        r = g.nodes[nid]
        accent = accent_for(r.rtype, overrides)
        cx = x + w / 2
        out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" '
                   f'height="{h:.1f}" rx="9" fill="#ffffff" stroke="{accent}" '
                   f'stroke-width="1.6" filter="url(#card)"/>')
        out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="5" height="{h:.1f}" '
                   f'rx="2.5" fill="{accent}"/>')
        out.append(_t(cx + 2, y + 27, kind_label(r.rtype), 13, INK, "600", "middle"))
        out.append(_t(cx + 2, y + 45, r.name, 11.5, MUTE, "400", "middle", italic=True))
        attr = key_attr(r.attrs)
        if attr:
            out.append(_t(cx + 2, y + 62, attr, 10.5, FAINT, "400", "middle"))

    out.append('</g>')
    out.append(_t(PAD + 16, height - 12,
                  "Generated from Terraform by tfdiagram — not authoritative; "
                  "verify against plan.", 11, FAINT))
    out.append('</svg>')
    return "\n".join(out)
