#!/usr/bin/env python3
"""Build the Shaparak Pro packaging artwork.

Run ``python generate.py`` to write, into ``output/``:

* ``svg-outlined/``  four panels with every letter converted to curves - the
  files to hand to the printer or to open in any Illustrator version
* ``svg-live-text/`` the same four panels with editable ``<text>`` elements
* ``pdf/``           Illustrator-compatible PDFs of the outlined panels
* ``ai/`` and ``eps/`` layered Illustrator 8 files
* ``preview/``       PNG previews plus a presentation sheet that mirrors the
  original two-version mock-up
* ``assets/``        every item of the pack on its own artboard (logo, icons,
  barcode, headlines...) as SVG, AI and EPS, with a contact sheet index
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cairosvg

from utils import ai_export, assets, panels, theme
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

    written += asset_files()
    return written


def asset_files(png_dpi: int = 200) -> list[Path]:
    """Write every pack item on its own artboard, plus a contact sheet."""
    root = OUTPUT / "assets"
    written: list[Path] = []
    thumbs: list[tuple[assets.Asset, Document, str]] = []

    for asset in assets.catalogue():
        doc, layers = assets.document(asset)
        folder = root / asset.category
        svg = folder / f"{asset.name}.svg"
        svg.parent.mkdir(parents=True, exist_ok=True)
        doc.save(svg)
        written.append(svg)

        title = f"Shaparak Pro - {asset.en}"
        (folder / f"{asset.name}.ai").write_text(
            ai_export.layered_ai(doc, layers, title), encoding="utf-8"
        )
        (folder / f"{asset.name}.eps").write_text(
            ai_export.layered_ai(doc, layers, title, eps=True), encoding="utf-8"
        )

        png = root / "preview" / asset.category / f"{asset.name}.png"
        png.parent.mkdir(parents=True, exist_ok=True)
        cairosvg.svg2png(bytestring=svg.read_bytes(), write_to=str(png), dpi=png_dpi,
                         background_color=None)
        thumbs.append((asset, doc, f"{asset.category}/{asset.name}"))

    index = root / "00-INDEX.svg"
    index_document(thumbs).save(index)
    svg_bytes = index.read_bytes()
    cairosvg.svg2pdf(bytestring=svg_bytes, write_to=str(root / "00-INDEX.pdf"))
    cairosvg.svg2png(bytestring=svg_bytes, write_to=str(root / "00-INDEX.png"), dpi=110,
                     background_color="#FFFFFF")
    written.append(index)

    every = root / "00-ALL-ITEMS.svg"
    doc, layers = all_items_document(thumbs)
    doc.save(every)
    (root / "00-ALL-ITEMS.ai").write_text(
        ai_export.layered_ai(doc, layers, "Shaparak Pro - all items"), encoding="utf-8"
    )
    (root / "00-ALL-ITEMS.eps").write_text(
        ai_export.layered_ai(doc, layers, "Shaparak Pro - all items", eps=True), encoding="utf-8"
    )
    cairosvg.svg2pdf(bytestring=every.read_bytes(), write_to=str(root / "00-ALL-ITEMS.pdf"))
    written.append(every)
    return written


def all_items_document(
    thumbs: list[tuple[assets.Asset, Document, str]],
) -> tuple[Document, list[tuple[str, Node]]]:
    """One artboard holding every item at 1:1, each on its own named layer."""
    sheet_w, gap, label_h, margin, min_cell = 620.0, 8.0, 7.0, 14.0, 30.0
    cells = [(entry, max(entry[1].width, min_cell)) for entry in thumbs]
    rows: list[list[tuple[tuple, float]]] = [[]]
    x = margin
    for cell in cells:
        if rows[-1] and x + cell[1] > sheet_w - margin:
            rows.append([])
            x = margin
        rows[-1].append(cell)
        x += cell[1] + gap

    positions: list[tuple[assets.Asset, Document, str, float, float, float]] = []
    y = margin + 14.0
    for row in rows:
        x = margin
        height = max(item[0][1].height for item in row)
        for (asset, art_doc, relative), cell_w in row:
            positions.append((asset, art_doc, relative,
                              x + (cell_w - art_doc.width) / 2,
                              y + (height - art_doc.height) / 2,
                              cell_w))
            x += cell_w + gap
        y += height + label_h + gap
    height = y - gap + margin

    doc = Document(sheet_w, height, title="Shaparak Pro - all items at 1:1",
                   desc="Every separated item on one artboard, one layer each, real size.")
    doc.add(rect(0, 0, sheet_w, height, fill="#FFFFFF"))
    doc.add(
        group("00-SHEET-TITLE").add(
            tp.text("SHAPARAK PRO - ALL ARTWORK ITEMS, ACTUAL SIZE", margin, margin + 6,
                    tp.Style(size=5.0, weight="bold", fill=theme.NAVY_TEXT, tracking=0.5))
        )
    )

    labels = group("00-LABELS-delete-before-print")
    layers: list[tuple[str, Node]] = []
    for asset, art_doc, relative, ox, oy, cell_w in positions:
        layer = group(relative.upper(), transform=f"translate({ox:.3f} {oy:.3f})")
        layer.add(*art_doc.root_children)
        layers.append((relative.upper(), layer))
        centre = ox + art_doc.width / 2
        label_style = tp.Style(size=2.3, weight="medium", fill=theme.INK_SOFT, anchor="middle")
        labels.add(
            tp.text(relative, centre, oy + art_doc.height + 4.2,
                    tp.fit(relative, label_style, cell_w, min_size=1.9))
        )
    for _, layer in layers:
        doc.add(layer)
    doc.add(labels)
    layers.append(("00-LABELS-delete-before-print", labels))
    return doc, layers


def index_document(thumbs: list[tuple[assets.Asset, Document, str]]) -> Document:
    """A contact sheet: every item at a glance with the file name underneath."""
    columns, cell_w, cell_h, art_h = 6, 46.0, 44.0, 26.0
    margin, top = 12.0, 26.0
    rows = -(-len(thumbs) // columns)
    width = margin * 2 + columns * cell_w
    height = top + rows * cell_h + margin

    doc = Document(width, height, title="Shaparak Pro - asset index",
                   desc="Every separated item of the pack with its file name.")
    doc.add(rect(0, 0, width, height, fill="#FFFFFF"))
    header = group("HEADER")
    header.add(
        tp.text("SHAPARAK PRO - ARTWORK ITEMS", margin, 13,
                tp.Style(size=5.2, weight="bold", fill=theme.NAVY_TEXT, tracking=0.6)),
        tp.text("هر آیتم به صورت جداگانه در فرمت SVG / AI / EPS", width - margin, 19,
                tp.Style(size=3.4, script="persian", fill=theme.INK_SOFT, anchor="end")),
    )
    doc.add(header)

    sheet = group("ITEMS")
    label_style = tp.Style(size=1.85, weight="medium", fill=theme.INK_SOFT, anchor="middle")
    for index, (asset, art_doc, relative) in enumerate(thumbs):
        column, row = index % columns, index // columns
        x = margin + column * cell_w
        y = top + row * cell_h
        cell = group(None)
        cell.add(rect(x + 1.2, y, cell_w - 2.4, art_h + 3.4, rx=1.6, fill="#F4F5F7"))
        scale = min((cell_w - 8) / art_doc.width, art_h / art_doc.height)
        ox = x + cell_w / 2 - art_doc.width * scale / 2
        oy = y + 1.7 + (art_h - art_doc.height * scale) / 2
        art_group = group(None, transform=f"translate({ox:.3f} {oy:.3f}) scale({scale:.5f})")
        art_group.add(*art_doc.root_children)
        cell.add(art_group)
        cell.add(
            tp.text(relative, x + cell_w / 2, y + art_h + 7.4,
                    tp.fit(relative, label_style, cell_w - 3)),
            tp.text(asset.fa, x + cell_w / 2, y + art_h + 11.0,
                    tp.fit(asset.fa, tp.Style(size=2.0, script="persian", fill=theme.INK_SOFT,
                                              anchor="middle"), cell_w - 3)),
        )
        sheet.add(cell)
    doc.add(sheet)
    return doc


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dpi", type=int, default=150, help="preview PNG resolution")
    args = parser.parse_args()
    for path in build(args.dpi):
        print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
