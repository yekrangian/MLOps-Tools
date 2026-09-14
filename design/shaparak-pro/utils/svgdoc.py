"""A tiny SVG writer tuned for artwork that has to survive a round trip
through Adobe Illustrator.

The output keeps real millimetre dimensions, named top level groups (which
Illustrator turns into named layers on import) and plain, indented markup so
the files stay diffable in git.
"""

from __future__ import annotations

from typing import Iterable
from xml.sax.saxutils import escape

Number = float | int


def fmt(value: Number) -> str:
    """Format a coordinate with enough precision for print, without noise."""
    if isinstance(value, int):
        return str(value)
    text = f"{value:.4f}".rstrip("0").rstrip(".")
    return text if text not in ("", "-0") else "0"


def _attr_name(name: str) -> str:
    if name.endswith("_"):
        name = name[:-1]
    return name.replace("__", ":").replace("_", "-")


class Node:
    def __init__(self, tag: str, *children: "Node | str", **attrs):
        self.tag = tag
        self.attrs: dict[str, str] = {}
        self.children: list[Node | str] = [c for c in children if c is not None]
        self.set(**attrs)

    def set(self, **attrs) -> "Node":
        for key, value in attrs.items():
            if value is None:
                continue
            if isinstance(value, float | int) and not isinstance(value, bool):
                value = fmt(value)
            self.attrs[_attr_name(key)] = str(value)
        return self

    def add(self, *children: "Node | str | Iterable[Node]") -> "Node":
        for child in children:
            if child is None:
                continue
            if isinstance(child, Node | str):
                self.children.append(child)
            else:
                self.children.extend(c for c in child if c is not None)
        return self

    def render(self, indent: int = 0) -> str:
        pad = "  " * indent
        attrs = "".join(f' {k}="{escape(v, {chr(34): "&quot;"})}"' for k, v in self.attrs.items())
        if not self.children:
            return f"{pad}<{self.tag}{attrs}/>"
        if len(self.children) == 1 and isinstance(self.children[0], str):
            return f"{pad}<{self.tag}{attrs}>{escape(self.children[0])}</{self.tag}>"
        inner = "\n".join(
            escape(c) if isinstance(c, str) else c.render(indent + 1) for c in self.children
        )
        return f"{pad}<{self.tag}{attrs}>\n{inner}\n{pad}</{self.tag}>"


def el(tag: str, *children, **attrs) -> Node:
    return Node(tag, *children, **attrs)


def group(id_: str | None = None, **attrs) -> Node:
    node = Node("g", **attrs)
    if id_:
        node.set(id=id_, data_name=id_)
    return node


def path(d: str, **attrs) -> Node:
    return Node("path", d=d, **attrs)


def rect(x: Number, y: Number, w: Number, h: Number, **attrs) -> Node:
    return Node("rect", x=x, y=y, width=w, height=h, **attrs)


def circle(cx: Number, cy: Number, r: Number, **attrs) -> Node:
    return Node("circle", cx=cx, cy=cy, r=r, **attrs)


def line(x1: Number, y1: Number, x2: Number, y2: Number, **attrs) -> Node:
    return Node("line", x1=x1, y1=y1, x2=x2, y2=y2, **attrs)


class Document:
    """An SVG artboard measured in millimetres."""

    def __init__(self, width: float, height: float, title: str = "", desc: str = ""):
        self.width = width
        self.height = height
        self.title = title
        self.desc = desc
        self.defs = Node("defs")
        self.root_children: list[Node] = []

    def add(self, *nodes: Node) -> "Document":
        self.root_children.extend(n for n in nodes if n is not None)
        return self

    def define(self, *nodes: Node) -> "Document":
        self.defs.add(*nodes)
        return self

    def render(self) -> str:
        svg = Node(
            "svg",
            xmlns="http://www.w3.org/2000/svg",
            xmlns__xlink="http://www.w3.org/1999/xlink",
            version="1.1",
            width=f"{fmt(self.width)}mm",
            height=f"{fmt(self.height)}mm",
            viewBox=f"0 0 {fmt(self.width)} {fmt(self.height)}",
        )
        if self.title:
            svg.add(Node("title", self.title))
        if self.desc:
            svg.add(Node("desc", self.desc))
        if self.defs.children:
            svg.add(self.defs)
        svg.add(*self.root_children)
        return '<?xml version="1.0" encoding="UTF-8"?>\n' + svg.render() + "\n"

    def save(self, destination) -> None:
        destination.write_text(self.render(), encoding="utf-8")
