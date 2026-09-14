"""Text rendering for the pouch artwork.

Two output modes are supported for every string:

``live``      an SVG ``<text>`` element that stays editable in Illustrator
              (needs the bundled fonts installed, and the Middle-Eastern
              version of Illustrator for correct Persian/Arabic shaping)
``outlined``  the same string shaped with HarfBuzz and converted to a single
              ``<path>``, so the artwork looks identical everywhere and needs
              no fonts at all - this is what goes to the printer

Both modes share one measuring routine, so a layout built for one mode lines
up in the other.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from functools import cache
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

from . import theme
from .svgdoc import Node, fmt

ANCHORS = {"start", "middle", "end"}


class Face:
    """A font file plus the HarfBuzz and fontTools handles we need."""

    def __init__(self, path: Path, family: str, weight: str):
        self.path = path
        self.family = family
        self.weight = weight
        blob = hb.Blob.from_file_path(str(path))
        self.hb_face = hb.Face(blob)
        self.hb_font = hb.Font(self.hb_face)
        self.upem = self.hb_face.upem
        self.tt = TTFont(str(path), lazy=True)
        self.glyph_set = self.tt.getGlyphSet()
        self.glyph_order = self.tt.getGlyphOrder()

    def css_weight(self) -> int:
        return {"regular": 400, "medium": 500, "semibold": 600, "bold": 700}[self.weight]


@cache
def face(script: str, weight: str) -> Face:
    table = theme.LATIN if script == "latin" else theme.PERSIAN
    family = theme.LATIN_FAMILY if script == "latin" else theme.PERSIAN_FAMILY
    if weight not in table:  # Vazirmatn ships fewer weights than Montserrat
        weight = "bold" if weight in ("semibold", "bold") else "regular"
    return Face(table[weight], family, weight)


@dataclass(frozen=True)
class Style:
    size: float  # cap-to-cap type size in millimetres
    script: str = "latin"  # "latin" or "persian"
    weight: str = "regular"
    fill: str = theme.NAVY_TEXT
    tracking: float = 0.0  # extra letter spacing in millimetres
    anchor: str = "start"  # start | middle | end
    rtl: bool | None = None  # defaults to True for the Persian face
    opacity: float | None = None

    def with_(self, **kwargs) -> Style:
        return replace(self, **kwargs)

    @property
    def is_rtl(self) -> bool:
        return self.script == "persian" if self.rtl is None else self.rtl

    @property
    def face(self) -> Face:
        return face(self.script, self.weight)


ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹"
_RTL_BLOCKS = ((0x0591, 0x07FF), (0xFB1D, 0xFDFD), (0xFE70, 0xFEFC))


def _char_class(ch: str) -> str:
    """R (right to left), L (left to right), N (number) or W (neutral)."""
    if ch.isdigit() or ch in ARABIC_DIGITS:
        return "N"
    code = ord(ch)
    if any(lo <= code <= hi for lo, hi in _RTL_BLOCKS):
        return "R"
    if ch.isalpha():
        return "L"
    return "W"


def _logical_runs(text: str, base_rtl: bool) -> list[tuple[str, bool]]:
    """Split a mixed string into direction runs (a small subset of the Unicode
    bidirectional algorithm, enough for Persian copy with Latin and digits)."""
    classes = [_char_class(ch) for ch in text]
    resolved: list[str] = []
    for index, cls in enumerate(classes):
        if cls in ("R", "L"):
            resolved.append(cls)
            continue
        if cls == "N":
            resolved.append("L")  # numbers always read left to right
            continue
        previous = next((c for c in reversed(resolved) if c in ("R", "L")), None)
        following = next((c for c in classes[index + 1:] if c in ("R", "L", "N")), None)
        following = "L" if following == "N" else following
        if previous and previous == following:
            resolved.append(previous)
        else:
            resolved.append("R" if base_rtl else "L")

    runs: list[tuple[str, bool]] = []
    for ch, direction in zip(text, resolved, strict=True):
        rtl = direction == "R"
        if runs and runs[-1][1] == rtl:
            runs[-1] = (runs[-1][0] + ch, rtl)
        else:
            runs.append((ch, rtl))
    return runs


def _visual_runs(text: str, base_rtl: bool) -> list[tuple[str, bool]]:
    runs = _logical_runs(text, base_rtl)
    if base_rtl:
        runs.reverse()
        # trailing spaces of a run belong to its right hand neighbour visually
    return runs


def _shape_run(run: str, rtl: bool, style: Style):
    f = style.face
    buf = hb.Buffer()
    buf.add_str(run)
    arabic = any(_char_class(ch) == "R" or ch in ARABIC_DIGITS for ch in run)
    buf.direction = "rtl" if rtl else "ltr"
    buf.script = "Arab" if arabic else "Latn"
    buf.language = "fa" if arabic else "en"
    hb.shape(f.hb_font, buf, {"kern": True, "liga": True})
    return buf.glyph_infos, buf.glyph_positions


def _segments(text: str, style: Style):
    """Shaped runs in visual (left to right) order."""
    return [
        (*_shape_run(run, rtl, style), rtl)
        for run, rtl in _visual_runs(text, style.is_rtl)
        if run
    ]


def measure(text: str, style: Style) -> float:
    """Advance width of ``text`` in millimetres, tracking included."""
    if not text:
        return 0.0
    scale = style.size / style.face.upem
    width = 0.0
    glyphs = 0
    for infos, positions, _ in _segments(text, style):
        width += sum(p.x_advance for p in positions) * scale
        glyphs += len(infos)
    return width + style.tracking * max(glyphs - 1, 0)


def _origin(x: float, width: float, anchor: str) -> float:
    if anchor == "middle":
        return x - width / 2
    if anchor == "end":
        return x - width
    return x


def outlined(text: str, x: float, y: float, style: Style, **attrs) -> Node | None:
    """Shape ``text`` and return it as a single filled ``<path>``."""
    if not text.strip():
        return None
    f = style.face
    scale = style.size / f.upem
    pen = SVGPathPen(f.glyph_set, ntos=lambda v: fmt(round(v, 4)))
    cursor = _origin(x, measure(text, style), style.anchor)
    baseline = y
    for infos, positions, _ in _segments(text, style):
        for info, pos in zip(infos, positions, strict=True):
            name = f.glyph_order[info.codepoint]
            glyph = f.glyph_set[name]
            gx = cursor + pos.x_offset * scale
            gy = baseline - pos.y_offset * scale
            glyph.draw(TransformPen(pen, (scale, 0, 0, -scale, gx, gy)))
            cursor += pos.x_advance * scale + style.tracking
    commands = pen.getCommands()
    if not commands:
        return None
    node = Node("path", d=commands, fill=style.fill, **attrs)
    if style.opacity is not None:
        node.set(opacity=style.opacity)
    return node


def live(text: str, x: float, y: float, style: Style, **attrs) -> Node | None:
    """Return an editable ``<text>`` element for the same layout."""
    if not text.strip():
        return None
    f = style.face
    node = Node("text", text, x=x, y=y, fill=style.fill)
    node.set(
        font_family=f"{f.family}, sans-serif",
        font_size=style.size,
        font_weight=f.css_weight(),
    )
    if style.tracking:
        node.set(letter_spacing=style.tracking)
    if style.anchor != "start":
        node.set(text_anchor=style.anchor)
    if style.is_rtl:
        node.set(direction="rtl", unicode_bidi="embed")
    if style.opacity is not None:
        node.set(opacity=style.opacity)
    node.set(**attrs)
    return node


def text(text_: str, x: float, y: float, style: Style, outline: bool = True, **attrs) -> Node | None:
    return (outlined if outline else live)(text_, x, y, style, **attrs)


def fit(text_: str, style: Style, max_width: float, min_size: float = 1.4) -> Style:
    """Shrink ``style`` just enough for ``text_`` to fit ``max_width``."""
    width = measure(text_, style)
    if width <= max_width or width == 0:
        return style
    scaled = max(style.size * max_width / width, min_size)
    return style.with_(size=scaled, tracking=style.tracking * scaled / style.size)


def fit_lines(lines: tuple[str, ...] | list[str], style: Style, max_width: float) -> Style:
    """One common size that lets every line in a block fit the column."""
    for line_ in lines:
        style = fit(line_, style, max_width)
    return style


def paragraph(
    lines: tuple[str, ...] | list[str],
    x: float,
    y: float,
    style: Style,
    leading: float,
    outline: bool = True,
) -> list[Node]:
    nodes = []
    for index, line_ in enumerate(lines):
        node = text(line_, x, y + index * leading, style, outline=outline)
        if node is not None:
            nodes.append(node)
    return nodes
