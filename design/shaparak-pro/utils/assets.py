"""Every item on the pack as a separate, tightly cropped artwork.

The panels are useful for printing, but a designer who wants to rebuild the
pack in Illustrator needs the parts: the butterfly on its own, one icon per
file, the barcode, each Persian headline. This module lists those parts and
crops each one to its own artboard, so the exported file contains nothing but
the item plus a small margin.

Every entry reuses the exact drawing code of the panels, so a part and the
place it comes from can never drift apart.
"""

from __future__ import annotations

import io
from collections.abc import Callable
from dataclasses import dataclass

from svgelements import SVG, Shape

from . import artwork as art
from . import icons, panels, theme
from . import typography as tp
from .svgdoc import Document, Node, group, path, rect

OUTLINE = True  # asset text is always converted to curves


@dataclass(frozen=True)
class Asset:
    """One item, its crop settings and a bilingual caption for the index."""

    category: str
    name: str
    build: Callable[[], Node]
    en: str
    fa: str
    backdrop: str | None = None
    margin: float = 2.0
    canvas: tuple[float, float] | None = None


# --- cropping --------------------------------------------------------------


def _bbox(node: Node) -> tuple[float, float, float, float]:
    """Millimetre bounding box of a node, stroke width included."""
    scratch = Document(600, 600)
    scratch.add(node)
    svg = SVG.parse(io.StringIO(scratch.render()), ppi=25.4, reify=True)
    box: list[float] | None = None
    for element in svg.elements():
        if not isinstance(element, Shape):
            continue
        try:
            bounds = element.bbox()
        except Exception:  # noqa: BLE001 - unsupported element, ignore it
            bounds = None
        if bounds is None:
            continue
        pad = (element.implicit_stroke_width or 0.0) / 2 if element.stroke is not None else 0.0
        x0, y0, x1, y1 = bounds
        candidate = [x0 - pad, y0 - pad, x1 + pad, y1 + pad]
        if box is None:
            box = candidate
        else:
            box = [
                min(box[0], candidate[0]),
                min(box[1], candidate[1]),
                max(box[2], candidate[2]),
                max(box[3], candidate[3]),
            ]
    if box is None:
        raise ValueError("asset draws nothing")
    return tuple(box)  # type: ignore[return-value]


def document(asset: Asset) -> tuple[Document, list[tuple[str, Node]]]:
    """Artboard and layer list for one asset, cropped around its artwork."""
    node = asset.build()
    x0, y0, x1, y1 = _bbox(node)
    if asset.canvas:
        width, height = asset.canvas
        dx = width / 2 - (x0 + x1) / 2
        dy = height / 2 - (y0 + y1) / 2
    else:
        width = x1 - x0 + 2 * asset.margin
        height = y1 - y0 + 2 * asset.margin
        dx, dy = asset.margin - x0, asset.margin - y0

    doc = Document(
        round(width, 3),
        round(height, 3),
        title=f"Shaparak Pro - {asset.en}",
        desc=f"{asset.fa} - {width:.1f} x {height:.1f} mm, text converted to curves.",
    )
    layers: list[tuple[str, Node]] = []
    if asset.backdrop:
        back = group("00-BACKDROP-reference")
        back.add(rect(0, 0, round(width, 3), round(height, 3), fill=asset.backdrop))
        layers.append(("00-BACKDROP-reference", back))
    placed = group(asset.name.upper(), transform=f"translate({dx:.4f} {dy:.4f})")
    placed.add(node)
    layers.append((asset.name.upper(), placed))
    for _, layer in layers:
        doc.add(layer)
    return doc, layers


# --- catalogue -------------------------------------------------------------


def _wordmark() -> Node:
    node = group("wordmark-shaparak")
    node.add(
        tp.text(theme.BRAND, 0, 0,
                tp.Style(size=13.4, weight="bold", fill=theme.NAVY_TEXT, tracking=1.5), OUTLINE)
    )
    return node


def _lockup(tagline: bool) -> Node:
    node = group("logo-lockup")
    node.add(art.butterfly_logo(40, 15, 30, theme.GOLD, stroke=1.0))
    node.add(
        tp.text(theme.BRAND, 40, 34,
                tp.Style(size=9.6, weight="bold", fill=theme.NAVY_TEXT, anchor="middle",
                         tracking=1.1), OUTLINE)
    )
    node.add(
        art.heading_with_rules(
            theme.SUB_BRAND, 40, 41, 19,
            tp.Style(size=5.0, weight="medium", fill=theme.GOLD, anchor="middle", tracking=1.7),
            theme.GOLD, OUTLINE, gap=2.8)
    )
    if tagline:
        node.add(
            tp.text(theme.TITLE_EN, 40, 47.6,
                    tp.fit(theme.TITLE_EN,
                           tp.Style(size=3.2, weight="medium", fill=theme.NAVY_TEXT,
                                    anchor="middle", tracking=0.4), 62), OUTLINE)
        )
    return node


def _pro_mark() -> Node:
    return group("pro-mark").add(
        art.heading_with_rules(
            theme.SUB_BRAND, 30, 10, 19,
            tp.Style(size=7.0, weight="medium", fill=theme.GOLD, anchor="middle", tracking=2.2),
            theme.GOLD, OUTLINE, gap=3.4)
    )


def _wave(colourway: theme.ColourWay) -> Node:
    node = group("wave-divider")
    node.add(
        path(art.wave_path(14.0, theme.FRONT_WAVE_AMP, theme.PANEL_W, close_to=30.0),
             fill=colourway.primary),
        path(art.wave_path(13.45, theme.FRONT_WAVE_AMP, theme.PANEL_W), fill="none",
             stroke=theme.GOLD, stroke_width=1.0, stroke_linecap="round"),
    )
    return node


def _seal_band(colourway: theme.ColourWay, slot: bool) -> Node:
    node = group("seal-band")
    node.add(rect(0, 0, theme.PANEL_W, theme.TOP_SEAL_H, fill=colourway.primary))
    node.add(art.crimp_lines(0, 0, theme.PANEL_W, theme.TOP_SEAL_H, colourway.primary_light,
                             spacing=0.95, width=0.3, opacity=0.5))
    if slot:
        node.add(art.hang_slot(theme.PANEL_W / 2, theme.HANG_HOLE_CY, theme.PAPER))
    return node


def _marks_row() -> Node:
    return panels.certification_marks(OUTLINE)


def _icon_asset(key: str) -> Callable[[], Node]:
    def build() -> Node:
        return group(f"icon-{key}").add(
            icons.icon(key, 10, 10, 15, theme.NAVY_TEXT, stroke_width=1.55)
        )

    return build


def _text_asset(text: str, style: tp.Style, name: str) -> Callable[[], Node]:
    def build() -> Node:
        return group(name).add(tp.text(text, 0, 0, style, OUTLINE))

    return build


_FA_TITLE = tp.Style(size=6.4, script="persian", weight="medium", fill=theme.NAVY_TEXT)
_FA_LABEL = tp.Style(size=4.4, script="persian", weight="medium", fill=theme.NAVY_TEXT)
_EN_LABEL = tp.Style(size=4.0, weight="semibold", fill=theme.NAVY_TEXT, tracking=0.4)


def _slug(text: str) -> str:
    keep = [c.lower() if c.isalnum() else "-" for c in text]
    return "".join(keep).strip("-").replace("--", "-")


def _colourway_suffix(colourway: theme.ColourWay) -> str:
    """Omit the colour key when only one colourway is produced."""
    return "" if len(theme.COLOURWAYS) == 1 else f"-{colourway.key}"


def catalogue() -> list[Asset]:
    items: list[Asset] = []

    def add(category, name, build, en, fa, **kwargs) -> None:
        items.append(Asset(category, name, build, en, fa, **kwargs))

    # --- logo ---------------------------------------------------------------
    add("01-logo", "butterfly-symbol",
        lambda: group("butterfly").add(art.butterfly_logo(30, 20, 50, theme.GOLD, stroke=1.2)),
        "Butterfly symbol", "نماد پروانه")
    add("01-logo", "logo-lockup", lambda: _lockup(False),
        "Logo lock-up (butterfly + SHAPARAK PRO)", "لوگوی کامل")
    add("01-logo", "logo-lockup-with-tagline", lambda: _lockup(True),
        "Logo lock-up with English tagline", "لوگو با شعار انگلیسی")
    add("01-logo", "wordmark-shaparak", _wordmark, "SHAPARAK wordmark", "لوگوتایپ شاپرک")
    add("01-logo", "pro-mark", _pro_mark, "PRO with gold rules", "نشان PRO با خطوط طلایی")

    # --- illustration -------------------------------------------------------
    add("02-illustration", "towel-butterfly",
        lambda: group("towel-butterfly").add(
            art.towel_butterfly(60, 55, 110, outline=theme.GOLD, uid="asset-towel")),
        "Folded towel butterfly", "پروانه حوله تاشده")
    for cw in theme.COLOURWAYS:
        suffix = _colourway_suffix(cw)
        add("02-illustration", f"wave-divider{suffix}", (lambda c=cw: _wave(c)),
            f"Wave divider, {cw.name_en}", f"موج تفکیک‌کننده – {cw.name_fa}")
        add("02-illustration", f"seal-band{suffix}", (lambda c=cw: _seal_band(c, slot=False)),
            f"Crimped seal band, {cw.name_en}", f"نوار دوخت – {cw.name_fa}")
        add("02-illustration", f"hang-slot{suffix}", (lambda c=cw: _seal_band(c, slot=True)),
            f"Seal band with euro hang slot, {cw.name_en}",
            f"نوار دوخت با جای آویز – {cw.name_fa}")

    # --- front blocks -------------------------------------------------------
    for cw in theme.COLOURWAYS:
        suffix = _colourway_suffix(cw)
        add("03-front-blocks", f"viscose-badge{suffix}",
            (lambda c=cw: panels.viscose_badge(c, OUTLINE)),
            f"100% VISCOSE badge, {cw.name_en}", f"مهر ۱۰۰٪ ویسکوز – {cw.name_fa}")
        add("03-front-blocks", f"usage-strip{suffix}",
            (lambda c=cw: panels.usage_strip(c, OUTLINE)),
            f"Usage icon strip, {cw.name_en}", f"نوار کاربردها – {cw.name_fa}",
            backdrop=cw.primary, margin=4.0)
        add("03-front-blocks", f"size-box{suffix}",
            (lambda c=cw: panels.size_box(c, OUTLINE)),
            f"Size options box, {cw.name_en}", f"کادر سایزها – {cw.name_fa}",
            backdrop=cw.primary, margin=4.0)
        add("03-front-blocks", f"front-lockup{suffix}",
            (lambda c=cw: panels.front_lockup(c, OUTLINE)),
            f"Front lock-up with all three titles, {cw.name_en}",
            f"لوگو و عناوین روی پنل جلو – {cw.name_fa}")
    add("03-front-blocks", "extra-soft-claim", lambda: panels.extra_soft_claim(OUTLINE),
        "EXTRA SOFT / NATURAL FIBER claim", "نشان نرمی و الیاف طبیعی")

    # --- back blocks --------------------------------------------------------
    for cw in theme.COLOURWAYS:
        suffix = _colourway_suffix(cw)
        add("04-back-blocks", f"back-lockup{suffix}",
            (lambda c=cw: panels.back_lockup(c, OUTLINE)),
            f"Back panel lock-up, {cw.name_en}", f"لوگوی پنل پشت – {cw.name_fa}")
        add("04-back-blocks", f"features-list-en{suffix}",
            (lambda c=cw: panels.features_list(c, OUTLINE)),
            f"FEATURES list, {cw.name_en}", f"فهرست ویژگی‌ها – {cw.name_fa}")
        add("04-back-blocks", f"suitable-for{suffix}",
            (lambda c=cw: panels.suitable_for(c, OUTLINE)),
            f"SUITABLE FOR list, {cw.name_en}", f"فهرست موارد استفاده – {cw.name_fa}")
        add("04-back-blocks", f"viscose-block{suffix}",
            (lambda c=cw: panels.viscose_block(c, OUTLINE)),
            f"100% VISCOSE block, {cw.name_en}", f"بلوک ویسکوز – {cw.name_fa}")
    add("04-back-blocks", "intro-paragraph", lambda: panels.back_paragraph(OUTLINE),
        "English intro paragraph", "متن معرفی انگلیسی")
    add("04-back-blocks", "made-in-iran", lambda: panels.origin_block(OUTLINE),
        "MADE IN IRAN with rule", "نشان ساخت ایران")
    add("04-back-blocks", "follow-us", lambda: panels.follow_us(OUTLINE),
        "Follow Us block with QR code", "بلوک شبکه‌های اجتماعی با کیوآر")

    # --- codes and marks ----------------------------------------------------
    add("05-codes-and-marks", "barcode-ean13", lambda: panels.barcode_block(OUTLINE),
        "EAN-13 barcode", "بارکد EAN-13")
    add("05-codes-and-marks", "qr-code",
        lambda: group("qr").add(art.qr_code(theme.WEBSITE_URL, 0, 0, 26, theme.BLACK)),
        "Website QR code", "کیوآرکد وب‌سایت")
    add("05-codes-and-marks", "marks-row", _marks_row,
        "Certification marks row", "ردیف نشان‌های استاندارد")
    add("05-codes-and-marks", "mark-iran-standard",
        lambda: group("mark").add(art.iran_standard_mark(15, 15, 12, theme.NAVY_TEXT, OUTLINE)),
        "Iran national standard mark (placeholder)", "نشان استاندارد ایران (جایگزین)")
    add("05-codes-and-marks", "mark-iso-9001",
        lambda: group("mark").add(art.iso_mark(15, 15, 12, theme.NAVY_TEXT, OUTLINE)),
        "ISO 9001 mark", "نشان ایزو ۹۰۰۱")
    add("05-codes-and-marks", "mark-recycle",
        lambda: group("mark").add(icons.icon("recycle", 15, 15, 26, theme.BLACK,
                                             stroke_width=1.9)),
        "Recycling mark", "نشان بازیافت")

    # --- icons --------------------------------------------------------------
    for key in icons.available():
        add("06-icons", f"icon-{key}", _icon_asset(key), f"{key} icon", f"آیکن {key}",
            canvas=(20.0, 20.0))

    # --- type ---------------------------------------------------------------
    add("07-type", "title-fa", _text_asset(theme.TITLE_FA, _FA_TITLE, "title-fa"),
        "Persian product title", "عنوان فارسی محصول")
    add("07-type", "title-ar",
        _text_asset(theme.TITLE_AR,
                    tp.Style(size=5.6, script="persian", fill=theme.NAVY_TEXT), "title-ar"),
        "Arabic product title", "عنوان عربی محصول")
    add("07-type", "title-en",
        _text_asset(theme.TITLE_EN,
                    tp.Style(size=4.4, weight="medium", fill=theme.NAVY_TEXT, tracking=0.55),
                    "title-en"),
        "English product title", "عنوان انگلیسی محصول")
    add("07-type", "sizes-title-fa", _text_asset(theme.SIZES_TITLE_FA, _FA_LABEL,
                                                 "sizes-title-fa"),
        "Available sizes heading", "عنوان سایزهای موجود")
    for index, (size_text, note) in enumerate(theme.SIZES, start=1):
        add("07-type", f"size-{index}-fa",
            _text_asset(f"{size_text} – {note}", _FA_LABEL, f"size-{index}"),
            f"Size option {index}", f"سایز {index}")
    for key, label_en in theme.USAGES:
        add("07-type", f"label-usage-{key}-en", _text_asset(label_en, _EN_LABEL, key),
            f"Usage label: {label_en}", f"برچسب کاربرد: {label_en}")
    for key, label_en in theme.FEATURES:
        add("07-type", f"label-feature-{key}-en", _text_asset(label_en, _EN_LABEL, key),
            f"Feature label: {label_en}", f"برچسب ویژگی: {label_en}")
    for text in (theme.SUITABLE_TITLE, theme.VISCOSE_TITLE, theme.ORIGIN, theme.FEATURES_TITLE_EN):
        add("07-type", f"heading-{_slug(text)}", _text_asset(text, _EN_LABEL, _slug(text)),
            f"Heading: {text}", f"عنوان: {text}")
    add("07-type", "handle-instagram",
        _text_asset(theme.INSTAGRAM,
                    tp.Style(size=4.0, weight="medium", fill=theme.INK_SOFT), "instagram"),
        "Instagram handle", "آیدی اینستاگرام")
    add("07-type", "website-address",
        _text_asset(theme.WEBSITE,
                    tp.Style(size=4.0, weight="medium", fill=theme.INK_SOFT), "website"),
        "Website address", "آدرس وب‌سایت")
    return items
