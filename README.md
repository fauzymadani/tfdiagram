# tfdiagram

Scan a Terraform codebase and generate a styled SVG architecture diagram.
Graphviz computes the layout; the SVG is hand-rendered for a clean,
card-based look (no ugly default `dot` output).

![example](example/example.svg)

## Requires

- Python 3.10+
- [Graphviz](https://graphviz.org) (`dot` on PATH) — layout only

## Use

```bash
python3 -m tfdiagram path/to/terraform -o infra.svg
python3 -m tfdiagram example --title "AWS Web App"
python3 -m tfdiagram example --color database=#c62828   # recolor by type
python3 -m tfdiagram example --dot                       # dump layout DOT
```

## How it works

```
tfdiagram/
  parser.py    scan *.tf -> resources, attrs, edges, VPC/subnet nesting
  model.py     Resource / Graph dataclasses
  style.py     category colors, pretty labels, container tints
  layout.py    feed sized boxes to `dot -Tjson`, read back coordinates
  render.py    emit the styled SVG (cards, groups, arrows, legend)
  __main__.py  CLI
```

Resources are colored by category (compute / database / storage / network /
serverless / dns). Anything referencing a subnet/VPC is nested inside it.

## Test

```bash
python3 -m tests.test_parser
python3 -m tests.test_render   # needs graphviz
```

## Limitations

Regex HCL parse (not a real parser), no `count`/`for_each` fan-out, geometric
cards rather than vendor icons. Containment covers AWS/GCP/Azure VPC+subnet —
extend `CONTAINERS` in `style.py` for more.
# tfdiagram
