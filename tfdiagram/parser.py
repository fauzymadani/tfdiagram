"""Scan *.tf files into a Graph. Regex-based, no HCL dependency.

ponytail: regex parse, not a real HCL parser. Handles resource/module blocks,
references, and top-level scalar attributes. If it ever mis-parses real
modules, feed it `terraform graph` output instead of source.
"""
import pathlib
import re

from .model import Graph, Resource
from .style import container_level

RESOURCE_RE = re.compile(r'\bresource\s+"([^"]+)"\s+"([^"]+)"\s*\{')
MODULE_RE = re.compile(r'\bmodule\s+"([^"]+)"\s*\{')
REF_RE = re.compile(r'\b((?:[a-z][a-z0-9_]*\.){1,2}[a-z][a-z0-9_]*)')
ATTR_RE = re.compile(r'^\s*([a-z][a-z0-9_]*)\s*=\s*(.+?)\s*$')


def _strip_comments(text):
    return re.sub(r'//.*', '', re.sub(r'#.*', '', text))


def _body(text, start):
    """Return the brace-matched block body starting after the opening '{'."""
    depth, i = 1, start
    while i < len(text) and depth:
        depth += {"{": 1, "}": -1}.get(text[i], 0)
        i += 1
    return text[start:i - 1]          # drop the matching '}'


def _scalar_attrs(body):
    """Top-level `key = "literal"` strings/numbers only (depth 0)."""
    attrs, depth = {}, 0
    for line in body.splitlines():
        if depth == 0:
            m = ATTR_RE.match(line)
            if m and "{" not in m.group(2):
                raw = m.group(2).strip()
                if raw.startswith('"') and raw.endswith('"'):     # string literal
                    val = raw[1:-1]
                elif re.fullmatch(r'[\w.\-/]+', raw) and not raw[0].isalpha():
                    val = raw                                     # number/bool/cidr
                else:
                    val = None                                    # reference/expr
                if val and len(val) < 40:
                    attrs.setdefault(m.group(1), val)
        depth += line.count("{") - line.count("}")
    return attrs


def find_tf_files(root):
    return [p for p in pathlib.Path(root).rglob("*.tf")
            if ".terraform" not in p.parts]


def scan(root) -> Graph:
    g = Graph()
    bodies = {}                                  # id -> raw body text
    for path in find_tf_files(root):
        text = _strip_comments(path.read_text(errors="replace"))
        for m in RESOURCE_RE.finditer(text):
            rtype, name = m.group(1), m.group(2)
            nid = f"{rtype}.{name}"
            body = _body(text, m.end())
            g.nodes[nid] = Resource(nid, rtype, name, _scalar_attrs(body))
            bodies[nid] = body
        for m in MODULE_RE.finditer(text):
            nid = f"module.{m.group(1)}"
            body = _body(text, m.end())
            g.nodes[nid] = Resource(nid, "module", m.group(1), _scalar_attrs(body))
            bodies[nid] = body

    # classify containers
    for r in g.nodes.values():
        r.level = container_level(r.rtype)
        r.is_container = r.level is not None

    # edges from references
    edges = set()
    for nid, body in bodies.items():
        for ref in REF_RE.findall(body):
            tgt = _resolve(ref, g.nodes)
            if tgt and tgt != nid:
                edges.add((tgt, nid))
    g.edges = sorted(edges)

    _assign_parents(g)
    return g


def _resolve(ref, nodes):
    p = ref.split(".")
    if p[0] == "module" and len(p) >= 2:
        return f"module.{p[1]}" if f"module.{p[1]}" in nodes else None
    if len(p) >= 2 and f"{p[0]}.{p[1]}" in nodes:
        return f"{p[0]}.{p[1]}"
    return None


def _assign_parents(g):
    deps = {n: [] for n in g.nodes}
    for src, dst in g.edges:
        deps[dst].append(src)
    for nid, r in g.nodes.items():
        subnets = [d for d in deps[nid] if g.nodes[d].level == 1]
        vpcs = [d for d in deps[nid] if g.nodes[d].level == 0]
        if r.level == 0:
            r.parent = None
        elif r.level == 1:
            r.parent = vpcs[0] if vpcs else None
        else:
            r.parent = subnets[0] if subnets else (vpcs[0] if vpcs else None)
