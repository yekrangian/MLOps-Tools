"""Vector icon library for the Shaparak Pro pouch.

Every icon is drawn inside a 24 x 24 box with the origin at the top left, then
placed with :func:`icon`, which scales and centres it. Icons are stroke based
so a single set works both as white marks on the coloured strip and as tinted
marks on the white back panel.
"""

from __future__ import annotations

import math
from collections.abc import Callable

from .svgdoc import Node, circle, group, line, path, rect

GRID = 24.0

Builder = Callable[[], list[Node]]
_REGISTRY: dict[str, Builder] = {}


def register(name: str) -> Callable[[Builder], Builder]:
    def wrap(fn: Builder) -> Builder:
        _REGISTRY[name] = fn
        return fn

    return wrap


def solid(node: Node) -> Node:
    """Mark a node as filled with the icon colour instead of stroked."""
    return node.set(fill="currentColor", stroke="none")


# --- usage icons -----------------------------------------------------------


@register("scissors")
def _scissors() -> list[Node]:
    return [
        line(9.4, 18.4, 16.6, 4.2),
        line(14.6, 18.4, 7.4, 4.2),
        circle(8.6, 20.0, 2.1),
        circle(15.4, 20.0, 2.1),
        solid(circle(12.0, 12.3, 0.9)),
    ]


@register("salon")
def _salon() -> list[Node]:
    return [
        circle(12, 10.6, 5.4),
        path("M6.4,9.8 C6.4,5.2 8.8,2.8 12,2.8 C15.2,2.8 17.6,5.2 17.6,9.8"),
        path("M6.5,9.0 C5.3,12.8 5.0,17.4 5.6,20.8"),
        path("M17.5,9.0 C18.7,12.8 19.0,17.4 18.4,20.8"),
        solid(circle(10.2, 10.2, 0.8)),
        solid(circle(13.8, 10.2, 0.8)),
        path("M10.6,13.0 C11.4,13.8 12.6,13.8 13.4,13.0"),
    ]


@register("paw")
def _paw() -> list[Node]:
    return [
        solid(Node("ellipse", cx=7.3, cy=9.9, rx=2.3, ry=2.9)),
        solid(Node("ellipse", cx=11.5, cy=7.6, rx=2.4, ry=3.1)),
        solid(Node("ellipse", cx=15.9, cy=8.8, rx=2.3, ry=2.9)),
        solid(Node("ellipse", cx=19.2, cy=12.6, rx=2.0, ry=2.5)),
        solid(
            path(
                "M12.1,12.2 C15.0,12.2 17.6,14.5 17.6,17.1 C17.6,19.4 15.8,20.8 13.6,20.4 "
                "C12.6,20.2 11.6,20.2 10.6,20.4 C8.4,20.8 6.6,19.4 6.6,17.1 "
                "C6.6,14.5 9.2,12.2 12.1,12.2 Z"
            )
        ),
    ]


@register("dumbbell")
def _dumbbell() -> list[Node]:
    return [
        line(8.4, 12.0, 15.6, 12.0),
        line(6.2, 8.6, 6.2, 15.4),
        line(17.8, 8.6, 17.8, 15.4),
        line(3.4, 10.1, 3.4, 13.9),
        line(20.6, 10.1, 20.6, 13.9),
        line(8.6, 9.6, 8.6, 14.4),
        line(15.4, 9.6, 15.4, 14.4),
    ]


@register("pool")
def _pool() -> list[Node]:
    return [
        solid(circle(9.6, 7.4, 1.9)),
        path("M12.4, 6.2 L17.6,9.0"),
        path("M3.4,12.4 C6.0,10.6 8.8,10.8 11.6,11.8 C14.2,12.7 16.6,12.6 18.8,11.2"),
        path("M2.2,16.4 C4.1,14.7 6.0,14.7 7.9,16.4 C9.8,18.1 11.7,18.1 13.6,16.4 "
             "C15.5,14.7 17.4,14.7 19.3,16.4 C20.2,17.2 21.0,17.5 21.8,17.4"),
        path("M2.2,20.2 C4.1,18.5 6.0,18.5 7.9,20.2 C9.8,21.9 11.7,21.9 13.6,20.2 "
             "C15.5,18.5 17.4,18.5 19.3,20.2 C20.2,21.0 21.0,21.3 21.8,21.2"),
    ]


@register("hotel")
def _hotel() -> list[Node]:
    windows = [
        solid(rect(7.4 + col * 2.6, 8.2 + row * 2.8, 1.6, 1.9))
        for row in range(3)
        for col in range(3)
    ]
    return [
        path("M5.6,21.0 L5.6,5.2 C5.6,4.5 6.1,4.0 6.8,4.0 L14.2,4.0 "
             "C14.9,4.0 15.4,4.5 15.4,5.2 L15.4,21.0"),
        path("M15.4,21.0 L15.4,10.6 L18.6,10.6 C19.2,10.6 19.6,11.0 19.6,11.6 L19.6,21.0"),
        line(3.6, 21.0, 21.0, 21.0),
        *windows,
        solid(rect(16.6, 13.0, 1.5, 1.8)),
        solid(rect(16.6, 16.2, 1.5, 1.8)),
        path("M10.0,21.0 L10.0,17.4 C10.0,16.8 10.5,16.3 11.1,16.3 "
             "C11.7,16.3 12.2,16.8 12.2,17.4 L12.2,21.0"),
    ]


@register("plane")
def _plane() -> list[Node]:
    body = solid(
        path(
            "M12,2.2 C13.1,2.2 14,3.3 14,4.7 L14,9.4 L21.6,13.9 L21.6,16.1 L14,13.8 "
            "L14,18.3 L16.7,20.2 L16.7,21.8 L12,20.5 L7.3,21.8 L7.3,20.2 L10,18.3 "
            "L10,13.8 L2.4,16.1 L2.4,13.9 L10,9.4 L10,4.7 C10,3.3 10.9,2.2 12,2.2 Z"
        )
    )
    return [Node("g", body, transform="rotate(42 12 12)")]


# --- feature and material icons -------------------------------------------


@register("hygienic")
def _hygienic() -> list[Node]:
    return [
        path("M12,2.8 L19.6,5.8 L19.6,11.6 C19.6,16.2 16.5,20.1 12,21.4 "
             "C7.5,20.1 4.4,16.2 4.4,11.6 L4.4,5.8 Z"),
        path("M8.6,12.0 L11.0,14.5 L15.5,9.7"),
    ]


@register("leaf")
def _leaf() -> list[Node]:
    return [
        path("M20.4,3.8 C20.4,12.4 14.6,18.6 5.4,19.4 C3.8,11.2 9.6,4.2 20.4,3.8 Z"),
        path("M4.0,21.0 C6.6,16.0 10.8,11.4 16.4,8.2"),
    ]


@register("soft")
def _soft() -> list[Node]:
    return [
        path("M12,21.2 C12,14.4 15.6,9.0 21.2,7.0 C21.2,14.0 17.6,19.2 12,21.2 Z"),
        path("M12,21.2 C12,14.4 8.4,9.0 2.8,7.0 C2.8,14.0 6.4,19.2 12,21.2 Z"),
        line(12, 21.2, 12, 10.6),
    ]


@register("absorbent")
def _absorbent() -> list[Node]:
    return [
        path("M12,2.6 C12,2.6 5.4,10.2 5.4,14.4 C5.4,18.1 8.4,21.2 12,21.2 "
             "C15.6,21.2 18.6,18.1 18.6,14.4 C18.6,10.2 12,2.6 12,2.6 Z"),
        path("M9.0,15.2 C9.0,17.0 10.2,18.2 11.8,18.4"),
    ]


@register("disposable")
def _disposable() -> list[Node]:
    return [
        rect(3.6, 3.6, 16.8, 16.8, rx=3.2),
        path("M9.0,9.0 C10.6,7.4 13.4,7.4 15.0,9.0 C16.6,10.6 16.6,13.4 15.0,15.0 "
             "C13.4,16.6 10.6,16.6 9.0,15.0"),
        path("M9.0,6.4 L9.0,9.4 L12.0,9.4"),
    ]


@register("professional")
def _professional() -> list[Node]:
    return [
        circle(12, 7.6, 3.4),
        path("M5.4,20.6 C5.4,16.4 8.4,13.6 12,13.6 C15.6,13.6 18.6,16.4 18.6,20.6"),
    ]


@register("cotton")
def _cotton() -> list[Node]:
    return [
        path("M12,6.2 C9.6,6.2 8.0,8.0 8.0,10.2 C6.0,10.2 4.4,11.5 4.4,13.3 "
             "C4.4,15.2 6.2,16.4 8.2,16.4 L15.8,16.4 C17.8,16.4 19.6,15.2 19.6,13.3 "
             "C19.6,11.5 18.0,10.2 16.0,10.2 C16.0,8.0 14.4,6.2 12,6.2 Z"),
        line(12, 16.4, 12, 21.0),
        path("M12,19.4 C10.6,19.4 9.2,18.6 8.4,17.2"),
        path("M12,19.4 C13.4,19.4 14.8,18.6 15.6,17.2"),
    ]


@register("instagram")
def _instagram() -> list[Node]:
    return [
        rect(3.4, 3.4, 17.2, 17.2, rx=5.0),
        circle(12, 12, 4.1),
        solid(circle(17.0, 7.1, 1.15)),
    ]


@register("recycle")
def _recycle() -> list[Node]:
    """Three chasing arrows: an arc plus a tangential head, repeated at 120 deg."""
    cx = cy = 12.0
    radius, head = 7.0, 2.7
    nodes: list[Node] = []
    for step in range(3):
        base = -90 + step * 120
        start, end = math.radians(base + 16), math.radians(base + 82)
        tip = math.radians(base + 104)
        p0 = (cx + radius * math.cos(start), cy + radius * math.sin(start))
        p1 = (cx + radius * math.cos(end), cy + radius * math.sin(end))
        nodes.append(
            path(f"M{p0[0]:.2f},{p0[1]:.2f} A{radius},{radius} 0 0 1 {p1[0]:.2f},{p1[1]:.2f}")
        )
        corners = [
            (cx + radius * math.cos(tip), cy + radius * math.sin(tip)),
            (cx + (radius + head) * math.cos(end), cy + (radius + head) * math.sin(end)),
            (cx + (radius - head) * math.cos(end), cy + (radius - head) * math.sin(end)),
        ]
        nodes.append(
            solid(path("M" + " L".join(f"{px:.2f},{py:.2f}" for px, py in corners) + " Z"))
        )
    return nodes


def available() -> tuple[str, ...]:
    return tuple(sorted(_REGISTRY))


def icon(
    name: str,
    cx: float,
    cy: float,
    size: float,
    colour: str,
    stroke_width: float = 1.7,
    opacity: float | None = None,
) -> Node:
    """Place icon ``name`` centred on ``(cx, cy)`` at ``size`` millimetres."""
    if name not in _REGISTRY:
        raise KeyError(f"unknown icon {name!r}; available: {', '.join(available())}")
    scale = size / GRID
    node = group(
        f"icon-{name}",
        transform=f"translate({cx - size / 2:.4f} {cy - size / 2:.4f}) scale({scale:.6f})",
        fill="none",
        stroke=colour,
        stroke_width=stroke_width,
        stroke_linecap="round",
        stroke_linejoin="round",
    )
    if opacity is not None:
        node.set(opacity=opacity)
    parts = _REGISTRY[name]()
    for part in parts:
        _resolve_colour(part, colour)
    node.add(*parts)
    return node


def _resolve_colour(node: Node, colour: str) -> None:
    """Replace the ``currentColor`` placeholder so every renderer agrees."""
    for key, value in node.attrs.items():
        if value == "currentColor":
            node.attrs[key] = colour
    for child in node.children:
        if isinstance(child, Node):
            _resolve_colour(child, colour)
