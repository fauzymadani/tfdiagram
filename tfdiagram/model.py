"""Core data model for the parsed Terraform graph."""
from dataclasses import dataclass, field


@dataclass
class Resource:
    id: str                       # "aws_instance.web" or "module.vpc"
    rtype: str                    # "aws_instance" / "module"
    name: str                     # "web"
    attrs: dict = field(default_factory=dict)
    parent: str | None = None     # id of the container it nests in
    is_container: bool = False    # vpc / subnet
    level: int | None = None      # 0 = vpc, 1 = subnet, None = leaf

    @property
    def provider(self) -> str:
        return self.rtype.split("_")[0].split("-")[0]


@dataclass
class Graph:
    nodes: dict[str, Resource] = field(default_factory=dict)
    edges: list[tuple[str, str]] = field(default_factory=list)  # (dep, dependent)

    def children_of(self, nid: str) -> list[str]:
        return [n for n, r in self.nodes.items() if r.parent == nid]

    def roots(self) -> list[str]:
        return [n for n, r in self.nodes.items() if r.parent is None]
