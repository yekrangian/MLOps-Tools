"""Drawing primitives specific to the Shaparak Pro pouch: the pouch die line,
the crimped seals, the butterfly logo and towel, the trim marks, the barcode
and the QR code.
"""

from __future__ import annotations

import re

import qrcode

from . import theme
from . import typography as tp
from .svgdoc import Node, circle, el, fmt, group, line, path, rect

# --- pouch body ------------------------------------------------------------


def pouch_shape(w: float, h: float, r: float = theme.CORNER_R, **attrs) -> Node:
    """Rounded rectangle used as pouch die line and clipping shape."""
    return rect(0, 0, w, h, rx=r, ry=r, **attrs)


def wave_path(y: float, amp: float, w: float, close_to: float | None = None) -> str:
    """A soft two-crest wave across the panel, optionally closed downwards."""
    seg = w / 4
    d = (
        f"M0,{fmt(y + amp * 0.55)} "
        f"C{fmt(seg * 0.7)},{fmt(y - amp)} {fmt(seg * 1.5)},{fmt(y - amp * 1.05)} "
        f"{fmt(seg * 2)},{fmt(y - amp * 0.1)} "
        f"C{fmt(seg * 2.5)},{fmt(y + amp * 0.9)} {fmt(seg * 3.3)},{fmt(y + amp * 1.0)} "
        f"{fmt(w)},{fmt(y - amp * 0.35)}"
    )
    if close_to is not None:
        d += f" L{fmt(w)},{fmt(close_to)} L0,{fmt(close_to)} Z"
    return d


def crimp_lines(
    x: float,
    y: float,
    w: float,
    h: float,
    colour: str,
    spacing: float = 0.9,
    width: float = 0.35,
    opacity: float = 0.55,
) -> Node:
    """The fine horizontal ribbing left by the sealing jaws."""
    band = group("crimp-ribbing", opacity=opacity)
    count = int(h // spacing)
    for i in range(1, count):
        band.add(line(x, y + i * spacing, x + w, y + i * spacing, stroke=colour, stroke_width=width))
    return band


def hang_slot(cx: float, cy: float, colour: str = theme.WHITE) -> Node:
    """Euro hang slot knocked out of the top seal."""
    slot = group("hang-slot")
    slot.add(
        path(
            f"M{fmt(cx - 9.5)},{fmt(cy + 1.0)} "
            f"a1.4,1.4 0 0 1 1.4,-1.4 h3.6 "
            f"a4.6,4.6 0 0 1 9.0,0 h3.6 "
            f"a1.4,1.4 0 0 1 1.4,1.4 v1.9 "
            f"a1.4,1.4 0 0 1 -1.4,1.4 h-16.2 "
            f"a1.4,1.4 0 0 1 -1.4,-1.4 Z",
            fill=colour,
        )
    )
    return slot


# --- butterflies -----------------------------------------------------------

_LOGO_WINGS = (
    # (cx, cy, rx, ry, rotation) for the right hand side, mirrored for the left
    (16.8, -8.6, 16.2, 8.8, -21.0),
    (10.6, 6.4, 9.8, 5.8, 30.0),
)


def butterfly_logo(cx: float, cy: float, width: float, colour: str, stroke: float = 1.05) -> Node:
    """The outlined brand butterfly (four looping wings, body and antennae)."""
    scale = width / 72.0
    node = group(
        "butterfly-logo",
        transform=f"translate({fmt(cx)} {fmt(cy)}) scale({fmt(scale)})",
        fill="none",
        stroke=colour,
        stroke_width=stroke / scale,
        stroke_linecap="round",
        stroke_linejoin="round",
    )
    for sign in (1, -1):
        for wx, wy, rx, ry, rot in _LOGO_WINGS:
            node.add(
                el(
                    "ellipse",
                    cx=0,
                    cy=0,
                    rx=rx,
                    ry=ry,
                    transform=f"translate({fmt(sign * wx)} {fmt(wy)}) rotate({fmt(sign * rot)})",
                )
            )
        node.add(
            path(
                f"M0,-6.8 C{fmt(sign * 2.6)},-11.4 {fmt(sign * 5.6)},-14.6 "
                f"{fmt(sign * 9.2)},-16.4"
            ),
            circle(sign * 10.2, -16.8, 1.3, fill=colour, stroke="none"),
        )
    node.add(
        path(
            "M0,-8.0 C2.0,-4.8 2.3,0.2 1.0,5.4 C0.6,6.9 -0.6,6.9 -1.0,5.4 "
            "C-2.3,0.2 -2.0,-4.8 0,-8.0 Z",
            fill=colour,
            stroke="none",
        )
    )
    return node


_TOWEL_UPPER = (
    "M2.5,-1.5 C4.0,-11.0 10.0,-20.0 20.0,-23.0 "
    "C32.0,-26.5 45.0,-21.0 46.0,-10.5 "
    "C46.8,-2.0 38.0,4.2 26.0,4.6 "
    "C14.0,5.2 5.0,4.8 2.5,-1.5 Z"
)
_TOWEL_LOWER = (
    "M3.0,3.4 C11.0,2.2 23.0,4.6 29.5,10.4 "
    "C36.5,17.2 33.0,27.4 22.5,27.8 "
    "C12.0,28.2 4.4,18.0 3.0,3.4 Z"
)
_TOWEL_BODY_TOP = "M0,-6.2 C2.7,-3.2 2.7,0.6 0,3.2 C-2.7,0.6 -2.7,-3.2 0,-6.2 Z"
_TOWEL_BODY_BOTTOM = "M0,4.2 C3.1,8.4 3.1,16.4 0,22.4 C-3.1,16.4 -3.1,8.4 0,4.2 Z"


def _flatten(d: str, steps: int = 28) -> list[tuple[float, float]]:
    """Flatten a simple ``M``/``C``/``Z`` path into a polygon.

    Only the subset used by the butterfly shapes is supported, which keeps the
    towel texture free of clipping paths - legacy Illustrator files and some
    RIPs handle plain geometry far more predictably than clip groups.
    """
    numbers = [float(n) for n in re.findall(r"-?\d+(?:\.\d+)?", d)]
    commands = re.findall(r"[MCLZmclz]", d)
    points: list[tuple[float, float]] = []
    cursor = 0
    current = (0.0, 0.0)
    for command in commands:
        if command in "Mm" or command in "Ll":
            current = (numbers[cursor], numbers[cursor + 1])
            cursor += 2
            points.append(current)
        elif command in "Cc":
            p1 = (numbers[cursor], numbers[cursor + 1])
            p2 = (numbers[cursor + 2], numbers[cursor + 3])
            p3 = (numbers[cursor + 4], numbers[cursor + 5])
            cursor += 6
            p0 = current
            for step in range(1, steps + 1):
                t = step / steps
                u = 1 - t
                points.append(
                    (
                        u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
                        u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1],
                    )
                )
            current = p3
    return points


def _scanline(polygon: list[tuple[float, float]], y: float) -> list[tuple[float, float]]:
    """Spans where the horizontal line at ``y`` runs inside ``polygon``."""
    crossings: list[float] = []
    for (x1, y1), (x2, y2) in zip(polygon, polygon[1:] + polygon[:1], strict=True):
        if (y1 <= y < y2) or (y2 <= y < y1):
            crossings.append(x1 + (y - y1) / (y2 - y1) * (x2 - x1))
    crossings.sort()
    return list(zip(crossings[0::2], crossings[1::2], strict=False))


def towel_butterfly(
    cx: float,
    cy: float,
    width: float,
    outline: str = theme.GOLD,
    fill: str = theme.TOWEL,
    stroke: float = 1.35,
    uid: str = "towel",
) -> Node:
    """The folded towel, die-cut into a butterfly, as shown on the front."""
    scale = width / 91.0
    node = group("towel-butterfly", transform=f"translate({fmt(cx)} {fmt(cy)}) scale({fmt(scale)})")

    wings = group(f"{uid}-wings", fill=fill, stroke=outline, stroke_width=stroke / scale,
                  stroke_linejoin="round")
    polygons: list[list[tuple[float, float]]] = []
    for sign in (1, -1):
        transform = None if sign == 1 else "scale(-1 1)"
        for d in (_TOWEL_UPPER, _TOWEL_LOWER):
            wings.add(path(d, transform=transform) if transform else path(d))
            polygons.append([(sign * px, py) for px, py in _flatten(d)])

    # the woven look of the towel: horizontal ridges trimmed to each wing
    texture = group(f"{uid}-texture", opacity=0.5)
    inset, spacing = 1.1, 2.1
    y = -26.0
    while y < 28.0:
        for polygon in polygons:
            for x1, x2 in _scanline(polygon, y):
                if x2 - x1 > 2 * inset + 1.0:
                    texture.add(
                        line(
                            x1 + inset,
                            y,
                            x2 - inset,
                            y,
                            stroke=theme.TOWEL_SHADE,
                            stroke_width=0.44 / scale,
                            stroke_linecap="round",
                        )
                    )
        y += spacing

    body = group(
        f"{uid}-body",
        fill=fill,
        stroke=outline,
        stroke_width=stroke / scale,
        stroke_linejoin="round",
    )
    body.add(path(_TOWEL_BODY_TOP), path(_TOWEL_BODY_BOTTOM))

    antennae = group(
        f"{uid}-antennae",
        fill="none",
        stroke=outline,
        stroke_width=(stroke * 0.62) / scale,
        stroke_linecap="round",
    )
    for sign in (1, -1):
        antennae.add(
            path(
                f"M0,-5.2 C{fmt(sign * 1.8)},-11.0 {fmt(sign * 4.2)},-16.0 "
                f"{fmt(sign * 7.6)},-19.2"
            ),
            circle(sign * 8.6, -19.9, 1.5, fill=outline, stroke="none"),
        )

    node.add(wings, texture, body, antennae)
    return node


# --- small furniture -------------------------------------------------------


def rule(x1: float, y: float, x2: float, colour: str, width: float = 0.3) -> Node:
    return line(x1, y, x2, y, stroke=colour, stroke_width=width, stroke_linecap="round")


def heading_with_rules(
    text: str,
    cx: float,
    y: float,
    half_width: float,
    style: tp.Style,
    rule_colour: str,
    outline: bool,
    gap: float = 2.4,
) -> Node:
    """A centred heading flanked by two thin rules, as used for FEATURES."""
    node = group(None)
    width = tp.measure(text, style)
    node.add(
        tp.text(text, cx, y, style.with_(anchor="middle"), outline=outline),
        rule(cx - half_width, y - style.size * 0.34, cx - width / 2 - gap, rule_colour),
        rule(cx + width / 2 + gap, y - style.size * 0.34, cx + half_width, rule_colour),
    )
    return node


def checkbox(x: float, y: float, size: float, colour: str, width: float = 0.32) -> Node:
    return rect(x, y, size, size, rx=size * 0.16, fill="none", stroke=colour, stroke_width=width)


def rounded_panel(
    x: float, y: float, w: float, h: float, colour: str, width: float = 0.35, radius: float = 2.4
) -> Node:
    return rect(x, y, w, h, rx=radius, fill="none", stroke=colour, stroke_width=width)


# --- codes -----------------------------------------------------------------

_EAN_L = ("0001101", "0011001", "0010011", "0111101", "0100011",
          "0110001", "0101111", "0111011", "0110111", "0001011")
_EAN_G = ("0100111", "0110011", "0011011", "0100001", "0011101",
          "0111001", "0000101", "0010001", "0001001", "0010111")
_EAN_R = ("1110010", "1100110", "1101100", "1000010", "1011100",
          "1001110", "1010000", "1000100", "1001000", "1110100")
_EAN_PARITY = ("LLLLLL", "LLGLGG", "LLGGLG", "LLGGGL", "LGLLGG",
               "LGGLLG", "LGGGLL", "LGLGLG", "LGLGGL", "LGGLGL")


def ean13_check_digit(digits: str) -> int:
    total = sum(int(d) * (3 if i % 2 else 1) for i, d in enumerate(digits[:12]))
    return (10 - total % 10) % 10


def ean13(
    digits12: str,
    x: float,
    y: float,
    w: float,
    h: float,
    outline: bool = True,
    colour: str = theme.BLACK,
) -> Node:
    """A specification-correct EAN-13 symbol with human readable digits."""
    digits12 = "".join(ch for ch in digits12 if ch.isdigit())[:12].rjust(12, "0")
    full = digits12 + str(ean13_check_digit(digits12))
    first, left, right = int(full[0]), full[1:7], full[7:13]

    modules: list[str] = ["101"]
    for parity, digit in zip(_EAN_PARITY[first], left, strict=True):
        modules.append((_EAN_L if parity == "L" else _EAN_G)[int(digit)])
    modules.append("01010")
    modules.extend(_EAN_R[int(d)] for d in right)
    modules.append("101")
    pattern = "".join(modules)

    unit = w / len(pattern)
    text_size = min(h * 0.22, unit * 7.2)
    bar_h = h - text_size * 1.25
    guard_extra = text_size * 0.62
    guards = set(range(3)) | set(range(45, 50)) | set(range(92, 95))

    node = group("barcode-ean13")
    node.add(rect(x - unit * 2, y - unit, w + unit * 11, h + unit * 2, fill=theme.WHITE))
    bars = group("barcode-bars", fill=colour)
    for index, module in enumerate(pattern):
        if module != "1":
            continue
        height = bar_h + (guard_extra if index in guards else 0)
        bars.add(rect(x + index * unit, y, unit, height))
    node.add(bars)

    style = tp.Style(size=text_size, weight="medium", fill=colour, script="latin")
    baseline = y + bar_h + guard_extra + text_size * 0.1
    node.add(tp.text(full[0], x - unit * 1.4, baseline, style, outline=outline))
    for group_index, chunk in ((1, full[1:7]), (2, full[7:13])):
        start = 3 if group_index == 1 else 50
        centre = x + (start + 21) * unit
        node.add(
            tp.text(
                " ".join(chunk),
                centre,
                baseline,
                style.with_(anchor="middle", tracking=unit * 0.2),
                outline=outline,
            )
        )
    return node


def qr_code(data: str, x: float, y: float, size: float, colour: str = theme.BLACK) -> Node:
    """A real, scannable QR code drawn as one vector path."""
    code = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, border=0)
    code.add_data(data)
    code.make(fit=True)
    matrix = code.get_matrix()
    n = len(matrix)
    unit = size / n
    commands: list[str] = []
    for row, cells in enumerate(matrix):
        col = 0
        while col < n:
            if not cells[col]:
                col += 1
                continue
            run = col
            while run < n and cells[run]:
                run += 1
            cx, cy = x + col * unit, y + row * unit
            commands.append(
                f"M{fmt(cx)},{fmt(cy)} h{fmt((run - col) * unit)} v{fmt(unit)} "
                f"h{fmt(-(run - col) * unit)} Z"
            )
            col = run
    return group("qr-code").add(path(" ".join(commands), fill=colour, shape_rendering="crispEdges"))


# --- certification marks ---------------------------------------------------


def iso_mark(cx: float, cy: float, r: float, colour: str, outline: bool = True) -> Node:
    node = group("mark-iso")
    node.add(
        el("ellipse", cx=cx, cy=cy, rx=r * 1.12, ry=r, fill="none", stroke=colour,
           stroke_width=r * 0.11),
        tp.text("ISO", cx, cy - r * 0.04, tp.Style(size=r * 0.72, weight="bold", fill=colour,
                                                   anchor="middle"), outline=outline),
        tp.text("9001", cx, cy + r * 0.62, tp.Style(size=r * 0.62, weight="medium", fill=colour,
                                                    anchor="middle"), outline=outline),
    )
    return node


def iran_standard_mark(cx: float, cy: float, r: float, colour: str, outline: bool = True) -> Node:
    """Placeholder for the Iranian national standard mark.

    Drawn as a close approximation so the layout is final; swap in the official
    artwork supplied by INSO before going to print.
    """
    node = group("mark-iran-standard")
    node.add(
        circle(cx, cy, r, fill="none", stroke=colour, stroke_width=r * 0.11),
        circle(cx, cy, r * 0.82, fill="none", stroke=colour, stroke_width=r * 0.05),
        tp.text(
            "استاندارد",
            cx,
            cy + r * 0.02,
            tp.Style(size=r * 0.36, script="persian", weight="bold", fill=colour,
                     anchor="middle"),
            outline=outline,
        ),
        tp.text(
            "ایران",
            cx,
            cy + r * 0.5,
            tp.Style(size=r * 0.32, script="persian", fill=colour, anchor="middle"),
            outline=outline,
        ),
    )
    return node
