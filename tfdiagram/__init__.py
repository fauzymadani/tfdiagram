"""tfdiagram — turn a Terraform codebase into a styled SVG architecture diagram."""
from .parser import scan
from .layout import run as layout
from .render import render

__all__ = ["scan", "layout", "render", "generate"]


def generate(tf_dir, title=None, subtitle=None, overrides=()):
    """Scan a dir and return SVG text."""
    g = scan(tf_dir)
    if not g.nodes:
        raise SystemExit(f"no terraform resources found under {tf_dir!r}")
    lay = layout(g)
    title = title or "Terraform Infrastructure"
    subtitle = subtitle or (
        f"{len([r for r in g.nodes.values() if not r.is_container])} resources, "
        f"{len(g.edges)} dependencies")
    return render(g, lay, title, subtitle, overrides)
