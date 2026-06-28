"""CLI: python3 -m tfdiagram [TF_DIR] -o out.svg"""
import argparse
import pathlib
import sys

from . import generate
from .layout import build_dot
from .parser import scan


def parse_overrides(pairs):
    out = []
    for p in pairs or []:
        if "=" not in p:
            sys.exit(f"--color expects TYPE=HEX, got {p!r}")
        k, v = p.split("=", 1)
        out.append((k, v if v.startswith("#") else "#" + v))
    return out


def main():
    ap = argparse.ArgumentParser(
        prog="tfdiagram",
        description="Generate a styled SVG architecture diagram from Terraform.")
    ap.add_argument("dir", nargs="?", default=".", help="terraform directory")
    ap.add_argument("-o", "--out", default="infra.svg", help="output SVG path")
    ap.add_argument("--title", help="diagram title")
    ap.add_argument("--subtitle", help="subtitle line")
    ap.add_argument("--color", action="append", metavar="TYPE=HEX",
                    help="recolor cards whose type contains TYPE (repeatable)")
    ap.add_argument("--dot", action="store_true",
                    help="print the layout DOT and exit")
    args = ap.parse_args()

    if args.dot:
        print(build_dot(scan(args.dir)))
        return

    svg = generate(args.dir, args.title, args.subtitle,
                   parse_overrides(args.color))
    pathlib.Path(args.out).write_text(svg)
    n = svg.count('filter="url(#card)"')
    print(f"wrote {args.out}: {n} resource cards")


if __name__ == "__main__":
    main()
