"""Export the artwork as a genuinely layered Adobe Illustrator file.

Illustrator's modern ``.ai`` is a PDF with a private, undocumented blob, and a
plain PDF renamed to ``.ai`` opens as a single flat layer. The legacy
Illustrator 8 format, on the other hand, is documented PostScript with explicit
layer records (``%AI5_BeginLayer`` / ``Lb`` / ``Ln`` / ``LB``), and Illustrator
still opens it and rebuilds the Layers panel from those records.

This module walks the generated SVG of each layer and re-emits it with the
Illustrator operator set: ``m``/``l``/``c`` for geometry, ``Xa``/``XA`` for RGB
fill and stroke, ``f``/``s``/``b`` for painting and ``*u``/``*U`` around
compound paths so counters stay transparent.

The prolog defines the same operators as ordinary PostScript procedures, which
is what real Illustrator files do as well: Illustrator ignores the prolog and
reads the art natively, while Ghostscript and other PostScript consumers can
still render the file. That double life is what lets the build verify its own
output.
"""

from __future__ import annotations

import io
from datetime import UTC, datetime

from svgelements import SVG, Close, CubicBezier, Line, Move, Path, QuadraticBezier, Shape

from .svgdoc import Document, Node

MM = 72.0 / 25.4  # PostScript points per millimetre

_PROLOG = """%%BeginProlog
%%BeginResource: procset Shaparak_AI_compat 1.0 0
/_fr 0 def /_fg 0 def /_fb 0 def
/_sr 0 def /_sg 0 def /_sb 0 def
/Xa { /_fb exch def /_fg exch def /_fr exch def } def
/XA { /_sb exch def /_sg exch def /_sr exch def } def
/m { moveto } def
/l { lineto } def
/L { lineto } def
/c { curveto } def
/C { curveto } def
/v { currentpoint 6 2 roll curveto } def
/V { currentpoint 6 2 roll curveto } def
/y { 2 copy curveto } def
/Y { 2 copy curveto } def
/w { setlinewidth } def
/J { setlinecap } def
/j { setlinejoin } def
/M { setmiterlimit } def
/d { setdash } def
/F { _fr _fg _fb setrgbcolor fill } def
/f { closepath F } def
/S { _sr _sg _sb setrgbcolor stroke } def
/s { closepath S } def
/B { gsave F grestore S } def
/b { closepath B } def
/N { } def
/n { } def
/*u { } def
/*U { } def
/u { } def
/U { } def
/A { pop } def
/Lb { 10 { pop } repeat } def
/Ln { pop } def
/LB { } def
/annotatepage { } def
%%EndResource
%%EndProlog
"""


def _num(value: float) -> str:
    text = f"{value:.3f}".rstrip("0").rstrip(".")
    return "0" if text in ("", "-0") else text


def _colour(value) -> tuple[float, float, float] | None:
    """An svgelements colour as RGB in the 0-1 range, or None for no paint."""
    if value is None or getattr(value, "value", None) is None:
        return None
    return (value.red / 255.0, value.green / 255.0, value.blue / 255.0)


def _blend(rgb: tuple[float, float, float], alpha: float) -> tuple[float, float, float]:
    """Flatten transparency against white - AI 8 predates live transparency."""
    alpha = max(0.0, min(1.0, alpha))
    return tuple(channel * alpha + (1 - alpha) for channel in rgb)


def _alpha(shape: Shape) -> float:
    values = shape.values or {}
    alpha = 1.0
    for key in ("opacity", "fill-opacity"):
        raw = values.get(key)
        if raw is None:
            continue
        try:
            alpha *= float(raw)
        except (TypeError, ValueError):
            pass
    return alpha


def _subpaths(path: Path) -> list[list]:
    groups: list[list] = []
    for segment in path.segments():
        if isinstance(segment, Move) or not groups:
            groups.append([])
        groups[-1].append(segment)
    return [g for g in groups if len(g) > 1]


def _emit_subpath(segments, height: float, out: list[str]) -> bool:
    """Write one subpath; returns True when it ended with an explicit close."""
    closed = False
    for segment in segments:
        if isinstance(segment, Move):
            out.append(f"{_num(segment.end.x)} {_num(height - segment.end.y)} m")
        elif isinstance(segment, Line):
            out.append(f"{_num(segment.end.x)} {_num(height - segment.end.y)} L")
        elif isinstance(segment, Close):
            closed = True
        elif isinstance(segment, CubicBezier):
            out.append(
                f"{_num(segment.control1.x)} {_num(height - segment.control1.y)} "
                f"{_num(segment.control2.x)} {_num(height - segment.control2.y)} "
                f"{_num(segment.end.x)} {_num(height - segment.end.y)} C"
            )
        elif isinstance(segment, QuadraticBezier):
            start, control, end = segment.start, segment.control, segment.end
            c1 = (start.x + 2 / 3 * (control.x - start.x), start.y + 2 / 3 * (control.y - start.y))
            c2 = (end.x + 2 / 3 * (control.x - end.x), end.y + 2 / 3 * (control.y - end.y))
            out.append(
                f"{_num(c1[0])} {_num(height - c1[1])} {_num(c2[0])} {_num(height - c2[1])} "
                f"{_num(end.x)} {_num(height - end.y)} C"
            )
        else:  # arcs are flattened to cubics before we get here
            for cubic in segment.as_cubic_curves():
                out.append(
                    f"{_num(cubic.control1.x)} {_num(height - cubic.control1.y)} "
                    f"{_num(cubic.control2.x)} {_num(height - cubic.control2.y)} "
                    f"{_num(cubic.end.x)} {_num(height - cubic.end.y)} C"
                )
    return closed


def _shape_to_ai(shape: Shape, height: float) -> list[str]:
    try:
        path = abs(Path(shape))
    except Exception:  # noqa: BLE001 - unsupported element, skip it
        return []
    subpaths = _subpaths(path)
    if not subpaths:
        return []

    alpha = _alpha(shape)
    fill = _colour(shape.fill)
    stroke = _colour(shape.stroke)
    if fill is None and stroke is None:
        return []
    width = shape.implicit_stroke_width or 0.0
    if stroke is not None and width <= 0:
        stroke = None

    out: list[str] = []
    if fill is not None:
        r, g, b = _blend(fill, alpha)
        out.append(f"{_num(r)} {_num(g)} {_num(b)} Xa")
    if stroke is not None:
        r, g, b = _blend(stroke, alpha)
        out.append(f"{_num(r)} {_num(g)} {_num(b)} XA")
        out.append(f"{_num(width)} w")
        values = shape.values or {}
        caps = {"butt": 0, "round": 1, "square": 2}
        joins = {"miter": 0, "round": 1, "bevel": 2}
        out.append(f"{caps.get(values.get('stroke-linecap', 'butt'), 0)} J")
        out.append(f"{joins.get(values.get('stroke-linejoin', 'miter'), 0)} j")
        dashes = values.get("stroke-dasharray")
        if dashes and dashes != "none":
            try:
                declared = float(values.get("stroke-width", 1) or 1)
            except (TypeError, ValueError):
                declared = 1.0
            unit = width / declared if declared else MM
            pattern = " ".join(
                _num(float(part) * unit) for part in dashes.replace(",", " ").split()
            )
            out.append(f"[{pattern}] 0 d")
        else:
            out.append("[] 0 d")

    paint = {(True, True): "b", (True, False): "f", (False, True): "s"}[
        (fill is not None, stroke is not None)
    ]
    compound = len(subpaths) > 1
    if compound:
        out.append("*u")
    for index, segments in enumerate(subpaths):
        last = index == len(subpaths) - 1
        closed = _emit_subpath(segments, height, out)
        if not last:
            out.append("n")
        else:
            out.append(paint if closed or fill is not None else paint.upper())
    if compound:
        out.append("*U")
    return out


def _layer_art(svg_text: str, height: float) -> list[str]:
    svg = SVG.parse(io.StringIO(svg_text), ppi=72.0, reify=True)
    art: list[str] = []
    for element in svg.elements():
        if isinstance(element, Shape):
            art.extend(_shape_to_ai(element, height))
    return art


_LAYER_COLOURS = (4, 9, 10, 13, 16, 22, 25, 27, 3, 6, 19, 1)


def layered_ai(
    document: Document, layers: list[tuple[str, Node]], title: str, eps: bool = False
) -> str:
    """Render ``layers`` (name, node) into a layered Illustrator 8 document.

    With ``eps=True`` the identical artwork is wrapped in an EPS header, which
    every Illustrator version imports even if it dislikes the legacy ``.ai``
    extension.
    """
    width, height = document.width * MM, document.height * MM
    stamp = datetime.now(UTC).strftime("%m/%d/%Y %H:%M:%S")

    body: list[str] = []
    emitted = 0
    for index, (name, node) in enumerate(layers):
        if "display:none" in (node.attrs.get("style") or ""):
            continue  # guides stay in the SVG only, never in a print file
        single = Document(document.width, document.height)
        single.defs = document.defs
        single.add(node)
        art = _layer_art(single.render(), height)
        if not art:
            continue
        emitted += 1
        colour = _LAYER_COLOURS[index % len(_LAYER_COLOURS)]
        body.append("%AI5_BeginLayer")
        body.append(f"1 1 1 1 0 0 {colour} 0 0 0 Lb")
        body.append(f"({name}) Ln")
        body.extend(art)
        body.append("LB")
        body.append("%AI5_EndLayer--")

    out = [
        "%!PS-Adobe-3.0 EPSF-3.0" if eps else "%!PS-Adobe-3.0",
        "%%Creator: Adobe Illustrator(R) 8.0",
        "%%AI8_CreatorVersion: 8.0",
        "%%For: (Shaparak Pro) (shaparak-pro artwork generator)",
        f"%%Title: ({title})",
        f"%%CreationDate: {stamp}",
        f"%%BoundingBox: 0 0 {int(width + 0.999)} {int(height + 0.999)}",
        f"%%HiResBoundingBox: 0 0 {_num(width)} {_num(height)}",
        "%%DocumentProcessColors: Cyan Magenta Yellow Black",
        "%AI5_FileFormat 3",
        "%AI3_ColorUsage: Color",
        f"%AI5_ArtSize: {_num(width)} {_num(height)}",
        "%AI5_RulerUnits: 1",
        "%AI9_ColorModel: 1",
        f"%AI5_NumLayers: {emitted}",
        "%AI5_OpenToView: 0 0 1 1600 1200 18 0 0 -2 96 0 0 0 1 1 0 1 1 0 1",
        "%%EndComments",
        _PROLOG.rstrip("\n"),
        "%%BeginSetup",
        "%%EndSetup",
    ]
    out += body
    out += [
        "%%PageTrailer",
        "gsave annotatepage grestore showpage",
        "%%Trailer",
        "%%EOF",
        "",
    ]
    return "\n".join(out)
