#!/usr/bin/env python3
"""Build the Shaparak Pro packaging artwork.

Run ``python generate.py`` to write, into ``output/``:

* ``svg-outlined/``  four panels with every letter converted to curves - the
  files to hand to the printer or to open in any Illustrator version
* ``svg-live-text/`` the same four panels with editable ``<text>`` elements
* ``pdf/``           Illustrator-compatible PDFs of the outlined panels
* ``preview/``       PNG previews plus a presentation sheet that mirrors the
  original two-version mock-up
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cairosvg

from utils import ai_export, panels, theme
from utils import artwork as art
from utils import typography as tp
from utils.svgdoc import Document, Node, el, group, rect

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "output"

PANEL_BUILDERS = {"front": panels.front_panel, "back": panels.back_panel}


def panel_document(
    colourway: theme.ColourWay, side: str, outline: bool
) -> tuple[Document, Node]:
    mode = "outlined" if outline else "live text"
    doc = Document(
        theme.PANEL_W,
        theme.PANEL_H,
        title=f"Shaparak Pro - {colourway.name_en} - {side} panel",
        desc=f"Flow pack {side} panel, {theme.PANEL_W:.0f} x {theme.PANEL_H:.0f} mm, {mode}.",
    )
    uid = f"{side}-{colourway.key}-{'o' if outline else 'l'}"
    panel = PANEL_BUILDERS[side](colourway, outline=outline, mockup=False, uid=uid)
    doc.add(panel)
    return doc, panel


def _pouch(colourway: theme.ColourWay, side: str, x: float, y: float, index: int) -> Node:
    """One rounded, shaded pouch for the presentation sheet."""
    uid = f"sheet-{index}"
    clip_id = f"{uid}-round"
    node = group(f"pouch-{colourway.key}-{side}", transform=f"translate({x} {y})")
    node.add(
        el(
            "defs",
            el(
                "clipPath",
                rect(0, 0, theme.PANEL_W, theme.PANEL_H, rx=theme.CORNER_R, ry=theme.CORNER_R),
                id=clip_id,
            ),
            el(
                "filter",
                el("feDropShadow", dx="0", dy="1.6", stdDeviation="2.2",
                   flood_color="#1B2540", flood_opacity="0.22"),
                id=f"{uid}-shadow",
                x="-10%",
                y="-10%",
                width="120%",
                height="120%",
            ),
        )
    )
    body = group(None, clip_path=f"url(#{clip_id})", filter=f"url(#{uid}-shadow)")
    body.add(PANEL_BUILDERS[side](colourway, outline=True, mockup=True, uid=uid))
    node.add(body)
    return node


def sheet_document() -> Document:
    margin, chip_w, gap_x, gap_y = 10.0, 30.0, 9.0, 12.0
    width = margin + chip_w + 6 + theme.PANEL_W * 2 + gap_x + margin
    height = margin + theme.PANEL_H * 2 + gap_y + margin
    doc = Document(width, height, title="Shaparak Pro - two colour ways",
                   desc="Presentation sheet: turquoise and navy, front and back.")
    doc.add(rect(0, 0, width, height, fill="#FFFFFF"))

    for row, colourway in enumerate(theme.COLOURWAYS):
        y = margin + row * (theme.PANEL_H + gap_y)
        chip = group(f"label-{colourway.key}")
        chip.add(rect(margin, y + 52, chip_w, 26, rx=3, fill=colourway.primary))
        label_style = tp.Style(size=4.0, script="persian", weight="medium",
                               fill=colourway.on_primary, anchor="middle")
        chip.add(
            tp.text(colourway.name_fa.split("–")[0].strip(), margin + chip_w / 2, y + 62,
                    label_style),
            tp.text(colourway.name_fa.split("–")[1].strip(), margin + chip_w / 2, y + 71,
                    label_style),
        )
        doc.add(chip)
        for column, side in enumerate(("front", "back")):
            x = margin + chip_w + 6 + column * (theme.PANEL_W + gap_x)
            doc.add(_pouch(colourway, side, x, y, row * 2 + column))
    return doc


def logo_document() -> Document:
    doc = Document(80, 46, title="Shaparak Pro - logo", desc="Brand butterfly lock-up.")
    doc.add(rect(0, 0, 80, 46, fill="#FFFFFF"))
    logo = group("LOGO")
    logo.add(art.butterfly_logo(40, 15, 30, theme.GOLD, stroke=1.0))
    logo.add(
        tp.text(theme.BRAND, 40, 34,
                tp.Style(size=9.6, weight="bold", fill=theme.NAVY_TEXT, anchor="middle",
                         tracking=1.1))
    )
    logo.add(
        art.heading_with_rules(
            theme.SUB_BRAND, 40, 41, 19,
            tp.Style(size=5.0, weight="medium", fill=theme.GOLD, anchor="middle", tracking=1.7),
            theme.GOLD, True, gap=2.8)
    )
    doc.add(logo)
    return doc


def layer_nodes(panel: Node) -> list[tuple[str, Node]]:
    """The named layer groups of a panel, in stacking order."""
    return [
        (child.attrs.get("id", f"layer-{index}"), child)
        for index, child in enumerate(panel.children)
        if isinstance(child, Node) and child.tag == "g"
    ]


def write_ai(doc: Document, panel: Node, destination: Path, title: str) -> Path:
    """Write a layered legacy Illustrator file plus an EPS fallback."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    layers = layer_nodes(panel)
    destination.write_text(ai_export.layered_ai(doc, layers, title), encoding="utf-8")
    eps = OUTPUT / "eps" / f"{destination.stem}.eps"
    eps.parent.mkdir(parents=True, exist_ok=True)
    eps.write_text(ai_export.layered_ai(doc, layers, title, eps=True), encoding="utf-8")
    return eps


def write(doc: Document, destination: Path, png_dpi: int | None = None,
          pdf: Path | None = None) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    doc.save(destination)
    svg_bytes = destination.read_bytes()
    if pdf is not None:
        pdf.parent.mkdir(parents=True, exist_ok=True)
        cairosvg.svg2pdf(bytestring=svg_bytes, write_to=str(pdf))
    if png_dpi:
        png = OUTPUT / "preview" / f"{destination.stem}.png"
        png.parent.mkdir(parents=True, exist_ok=True)
        cairosvg.svg2png(bytestring=svg_bytes, write_to=str(png), dpi=png_dpi,
                         output_width=None, background_color="#FFFFFF")


def build(png_dpi: int = 150) -> list[Path]:
    written: list[Path] = []
    for colourway in theme.COLOURWAYS:
        for side in PANEL_BUILDERS:
            stem = f"shaparak-pro-{colourway.key}-{side}"
            doc, panel = panel_document(colourway, side, outline=True)
            outlined = OUTPUT / "svg-outlined" / f"{stem}.svg"
            write(doc, outlined, png_dpi=png_dpi, pdf=OUTPUT / "pdf" / f"{stem}.pdf")
            written.append(outlined)

            ai = OUTPUT / "ai" / f"{stem}.ai"
            write_ai(doc, panel, ai, f"Shaparak Pro {colourway.name_en} {side}")
            written.append(ai)

            live, _ = panel_document(colourway, side, outline=False)
            live_path = OUTPUT / "svg-live-text" / f"{stem}-live-text.svg"
            write(live, live_path)
            written.append(live_path)

    sheet = OUTPUT / "shaparak-pro-presentation-sheet.svg"
    write(sheet_document(), sheet, png_dpi=110, pdf=OUTPUT / "pdf" / sheet.with_suffix(".pdf").name)
    written.append(sheet)

    logo = OUTPUT / "shaparak-pro-logo.svg"
    write(logo_document(), logo, png_dpi=300, pdf=OUTPUT / "pdf" / "shaparak-pro-logo.pdf")
    written.append(logo)
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dpi", type=int, default=150, help="preview PNG resolution")
    args = parser.parse_args()
    for path in build(args.dpi):
        print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
