"""Layout of the two pouch panels.

``front_panel`` and ``back_panel`` return one ``<g>`` holding a complete
150 x 170 mm panel, built out of named layers so Illustrator shows a tidy
layer list. Both take a colour way (turquoise or navy), a text mode
(outlined or live) and a ``mockup`` flag that adds the pouch rounding, the
film sheen and the centre fin seam used for the presentation sheet.
"""

from __future__ import annotations

from . import artwork as art
from . import icons, theme
from . import typography as tp
from .svgdoc import Node, circle, el, group, line, path, rect

W = theme.PANEL_W
H = theme.PANEL_H


def _sheen(uid: str, colourway: theme.ColourWay, seam: bool) -> tuple[Node, Node]:
    """Gradients plus the soft highlights that make a flat panel read as film."""
    defs = el("defs")
    defs.add(
        el(
            "linearGradient",
            el("stop", offset="0%", stop_color="#000000", stop_opacity="0.10"),
            el("stop", offset="16%", stop_color="#FFFFFF", stop_opacity="0.18"),
            el("stop", offset="50%", stop_color="#FFFFFF", stop_opacity="0.02"),
            el("stop", offset="84%", stop_color="#FFFFFF", stop_opacity="0.16"),
            el("stop", offset="100%", stop_color="#000000", stop_opacity="0.12"),
            id=f"{uid}-sheen",
            x1="0",
            y1="0",
            x2="1",
            y2="0",
        ),
        el(
            "linearGradient",
            el("stop", offset="0%", stop_color="#B9BCC0", stop_opacity="0.45"),
            el("stop", offset="35%", stop_color="#FFFFFF", stop_opacity="0.0"),
            el("stop", offset="65%", stop_color="#FFFFFF", stop_opacity="0.0"),
            el("stop", offset="100%", stop_color="#B9BCC0", stop_opacity="0.45"),
            id=f"{uid}-seam",
            x1="0",
            y1="0",
            x2="1",
            y2="0",
        ),
        el(
            "linearGradient",
            el("stop", offset="0%", stop_color=theme.GOLD_LIGHT),
            el("stop", offset="45%", stop_color=theme.GOLD),
            el("stop", offset="100%", stop_color="#9C6F27"),
            id=f"{uid}-gold",
            x1="0",
            y1="0",
            x2="1",
            y2="1",
        ),
    )
    layer = group("ZZ-MOCKUP-SHADING", opacity=0.9)
    layer.add(rect(0, 0, W, H, fill=f"url(#{uid}-sheen)"))
    if seam:
        layer.add(rect(W / 2 - 6.0, 0, 12, H, fill=f"url(#{uid}-seam)", opacity=0.55))
        layer.add(
            line(W / 2, 0, W / 2, H, stroke="#C9CCD1", stroke_width=0.25, opacity=0.7),
            line(W / 2 - 3.2, 0, W / 2 - 3.2, H, stroke="#DDE0E3", stroke_width=0.2, opacity=0.6),
            line(W / 2 + 3.2, 0, W / 2 + 3.2, H, stroke="#DDE0E3", stroke_width=0.2, opacity=0.6),
        )
    layer.add(
        rect(0, 0, W, theme.TOP_SEAL_H, fill="#000000", opacity=0.05),
    )
    del colourway
    return defs, layer


def _guides() -> Node:
    layer = group("ZZ-GUIDES-do-not-print", style="display:none")
    layer.add(
        rect(0, 0, W, H, fill="none", stroke="#FF00FF", stroke_width=0.25,
             stroke_dasharray="2 1.5"),
        rect(theme.SAFE, theme.SAFE, W - 2 * theme.SAFE, H - 2 * theme.SAFE, fill="none",
             stroke="#00A0FF", stroke_width=0.25, stroke_dasharray="2 1.5"),
        rect(-theme.BLEED, -theme.BLEED, W + 2 * theme.BLEED, H + 2 * theme.BLEED, fill="none",
             stroke="#FF7A00", stroke_width=0.25, stroke_dasharray="3 2"),
    )
    return layer


def _seal(uid: str, colourway: theme.ColourWay, y: float, height: float, name: str) -> Node:
    layer = group(name)
    layer.add(rect(0, y, W, height, fill=colourway.primary))
    layer.add(art.crimp_lines(0, y, W, height, colourway.primary_light, spacing=0.95,
                              width=0.3, opacity=0.5))
    return layer


# --- front -----------------------------------------------------------------


def front_panel(
    colourway: theme.ColourWay,
    outline: bool = True,
    mockup: bool = False,
    uid: str | None = None,
) -> Node:
    uid = uid or f"front-{colourway.key}"
    gold = f"url(#{uid}-gold)" if mockup else theme.GOLD
    panel = group(f"PANEL-FRONT-{colourway.key}")

    defs, sheen = _sheen(uid, colourway, seam=False)
    panel.add(defs)

    background = group("01-BACKGROUND")
    background.add(rect(0, 0, W, H, fill=theme.PAPER))
    background.add(
        path(art.wave_path(theme.FRONT_WAVE_Y, theme.FRONT_WAVE_AMP, W, close_to=H),
                      fill=colourway.primary)
    )
    background.add(
        path(
            art.wave_path(theme.FRONT_WAVE_Y - 0.55, theme.FRONT_WAVE_AMP, W),
            fill="none",
            stroke=gold,
            stroke_width=1.0,
            stroke_linecap="round",
        )
    )
    panel.add(background)

    panel.add(_seal(uid, colourway, 0, theme.TOP_SEAL_H, "02-TOP-SEAL"))
    bottom = group("03-BOTTOM-SEAL")
    bottom.add(art.crimp_lines(0, H - theme.BOTTOM_SEAL_H, W, theme.BOTTOM_SEAL_H,
                               colourway.primary_dark, spacing=0.95, width=0.3, opacity=0.45))
    panel.add(bottom)
    panel.add(group("04-HANG-SLOT").add(art.hang_slot(W / 2, theme.HANG_HOLE_CY, theme.PAPER)))

    panel.add(viscose_badge(colourway, outline))
    panel.add(front_lockup(colourway, outline, gold))
    panel.add(group("07-TOWEL-BUTTERFLY").add(
        art.towel_butterfly(W / 2, 113, 76, outline=gold, uid=uid)
    ))
    panel.add(extra_soft_claim(outline))
    panel.add(usage_strip(colourway, outline))
    panel.add(size_box(colourway, outline))

    if mockup:
        panel.add(sheen)
    panel.add(_guides())
    return panel


def viscose_badge(colourway: theme.ColourWay, outline: bool) -> Node:
    """The round 100% VISCOSE seal from the top left of the front."""
    badge = group("05-VISCOSE-BADGE")
    badge.add(circle(24.5, 36.5, 11.2, fill=colourway.badge))
    badge.add(icons.icon("leaf", 24.5, 32.2, 7.0, theme.WHITE, stroke_width=1.5))
    badge.add(
        tp.text(theme.VISCOSE_BADGE[0], 24.5, 39.2,
                tp.Style(size=4.4, weight="bold", fill=theme.WHITE, anchor="middle"), outline),
        tp.text(theme.VISCOSE_BADGE[1], 24.5, 43.0,
                tp.Style(size=2.9, weight="medium", fill=theme.WHITE, anchor="middle",
                         tracking=0.22), outline),
    )
    return badge


def front_lockup(colourway: theme.ColourWay, outline: bool, gold: str = theme.GOLD) -> Node:
    """Butterfly, SHAPARAK, PRO and the three language titles."""
    del colourway
    lockup = group("06-LOGO-AND-TITLES")
    lockup.add(art.butterfly_logo(W / 2, 34.5, 28, gold, stroke=1.0))
    lockup.add(
        tp.text(theme.BRAND, W / 2, 55.5,
                tp.Style(size=13.4, weight="bold", fill=theme.NAVY_TEXT, anchor="middle",
                         tracking=1.5), outline)
    )
    pro_style = tp.Style(size=7.0, weight="medium", fill=theme.GOLD, anchor="middle", tracking=2.2)
    lockup.add(art.heading_with_rules(theme.SUB_BRAND, W / 2, 64.6, 26, pro_style, theme.GOLD,
                                      outline, gap=3.4))
    lockup.add(
        tp.text(theme.TITLE_FA, W / 2, 74.6,
                tp.fit(theme.TITLE_FA,
                       tp.Style(size=6.4, script="persian", weight="medium",
                                fill=theme.NAVY_TEXT, anchor="middle"), 104), outline),
        tp.text(theme.TITLE_EN, W / 2, 81.6,
                tp.fit(theme.TITLE_EN,
                       tp.Style(size=4.1, weight="medium", fill=theme.NAVY_TEXT, anchor="middle",
                                tracking=0.55), 104), outline),
        tp.text(theme.TITLE_AR, W / 2, 88.4,
                tp.fit(theme.TITLE_AR,
                       tp.Style(size=4.8, script="persian", fill=theme.NAVY_TEXT,
                                anchor="middle"), 92), outline),
    )
    return lockup


def extra_soft_claim(outline: bool) -> Node:
    """Leaf icon over the EXTRA SOFT / NATURAL FIBER wording."""
    claim = group("08-EXTRA-SOFT-CLAIM")
    claim.add(icons.icon("leaf", 130.5, 97.6, 8.6, theme.NAVY_TEXT, stroke_width=1.3))
    claim.add(
        tp.text(theme.EXTRA_SOFT[0], 130.5, 105.6,
                tp.Style(size=2.9, weight="semibold", fill=theme.NAVY_TEXT, anchor="middle",
                         tracking=0.24), outline),
        tp.text(theme.EXTRA_SOFT[1], 130.5, 109.4,
                tp.Style(size=2.9, weight="semibold", fill=theme.NAVY_TEXT, anchor="middle",
                         tracking=0.24), outline),
    )
    return claim


def usage_strip(colourway: theme.ColourWay, outline: bool) -> Node:
    """Seven usage icons with their Persian labels, drawn in the knock-out colour."""
    layer = group("09-USAGE-STRIP")
    left, right = 17.0, 133.0
    step = (right - left) / (len(theme.USAGES) - 1)
    label_style = tp.Style(size=3.4, script="persian", weight="medium", fill=colourway.on_primary,
                           anchor="middle")
    for index, (key, label_fa, _) in enumerate(theme.USAGES):
        cx = left + index * step
        layer.add(icons.icon(key, cx, 142.0, 8.0, colourway.on_primary, stroke_width=1.65))
        layer.add(tp.text(label_fa, cx, 149.3, tp.fit(label_fa, label_style, step - 1.2), outline))
    return layer


def size_box(colourway: theme.ColourWay, outline: bool) -> Node:
    """Rounded size panel with its legend and the two size options."""
    layer = group("10-SIZE-OPTIONS")
    box_x, box_y, box_w, box_h = 20.0, 153.6, 110.0, 10.2
    layer.add(art.rounded_panel(box_x, box_y, box_w, box_h, colourway.on_primary, width=0.32,
                                radius=2.2))

    title_style = tp.Style(size=3.4, script="persian", weight="medium",
                           fill=colourway.on_primary, anchor="middle")
    title_w = tp.measure(theme.SIZES_TITLE_FA, title_style)
    layer.add(rect(W / 2 - title_w / 2 - 2.2, box_y - 1.7, title_w + 4.4, 3.2,
                   fill=colourway.primary))
    layer.add(tp.text(theme.SIZES_TITLE_FA, W / 2, box_y + 1.2, title_style, outline))

    size_style = tp.Style(size=3.3, script="persian", weight="medium",
                          fill=colourway.on_primary, anchor="end")
    note_style = tp.Style(size=2.7, script="persian", fill=colourway.on_primary, anchor="end",
                          opacity=0.9)
    for index, (size_text, note) in enumerate(theme.SIZES):
        group_right = box_x + 52.0 + index * 54.0
        size_style_fitted = tp.fit(size_text, size_style, 40)
        note_style_fitted = tp.fit(note, note_style, 40)
        text_width = max(tp.measure(size_text, size_style_fitted),
                         tp.measure(note, note_style_fitted))
        layer.add(
            art.checkbox(group_right - text_width - 6.4, box_y + 3.2, 3.6, colourway.on_primary)
        )
        layer.add(
            tp.text(size_text, group_right, box_y + 5.4, size_style_fitted, outline),
            tp.text(note, group_right, box_y + 9.0, note_style_fitted, outline),
        )
    return layer


# --- back ------------------------------------------------------------------


def back_panel(
    colourway: theme.ColourWay,
    outline: bool = True,
    mockup: bool = False,
    uid: str | None = None,
) -> Node:
    uid = uid or f"back-{colourway.key}"
    gold = f"url(#{uid}-gold)" if mockup else theme.GOLD
    panel = group(f"PANEL-BACK-{colourway.key}")

    defs, sheen = _sheen(uid, colourway, seam=True)
    panel.add(defs)

    background = group("01-BACKGROUND")
    background.add(rect(0, 0, W, H, fill=theme.PAPER))
    background.add(
        rect(0, theme.TOP_SEAL_H, 2.2, H - theme.TOP_SEAL_H, fill=colourway.primary),
        rect(W - 2.2, theme.TOP_SEAL_H, 2.2, H - theme.TOP_SEAL_H, fill=colourway.primary),
        rect(0, H - 3.4, W, 3.4, fill=colourway.primary),
    )
    panel.add(background)
    panel.add(_seal(uid, colourway, 0, theme.TOP_SEAL_H, "02-TOP-SEAL"))
    panel.add(*_back_left_column(colourway, outline, gold))
    panel.add(*_back_right_column(colourway, outline))

    if mockup:
        panel.add(sheen)
    panel.add(_guides())
    return panel


BACK_CENTRE, BACK_LEFT, BACK_RIGHT = 38.0, 10.0, 67.0


def back_lockup(colourway: theme.ColourWay, outline: bool, gold: str = theme.GOLD) -> Node:
    """Butterfly, wordmark, PRO and the English tagline, as used on the back."""
    block = group("brand-lockup")
    block.add(art.butterfly_logo(BACK_CENTRE, 28.0, 21, gold, stroke=0.8))
    block.add(
        tp.text(theme.BRAND, BACK_CENTRE, 41.0,
                tp.Style(size=8.6, weight="bold", fill=theme.NAVY_TEXT, anchor="middle",
                         tracking=0.95), outline)
    )
    block.add(
        art.heading_with_rules(
            theme.SUB_BRAND, BACK_CENTRE, 46.8, 17.0,
            tp.Style(size=4.6, weight="medium", fill=theme.GOLD, anchor="middle", tracking=1.5),
            theme.GOLD, outline, gap=2.6)
    )
    block.add(
        tp.text(theme.TITLE_EN, BACK_CENTRE, 52.6,
                tp.fit(theme.TITLE_EN,
                       tp.Style(size=3.1, weight="semibold", fill=colourway.accent,
                                anchor="middle", tracking=0.3), 57), outline)
    )
    return block


def back_paragraph(outline: bool) -> Node:
    style = tp.fit_lines(
        theme.BACK_PARAGRAPH,
        tp.Style(size=3.0, weight="regular", fill=theme.INK_SOFT),
        BACK_RIGHT - BACK_LEFT,
    )
    return group("intro-paragraph").add(
        tp.paragraph(theme.BACK_PARAGRAPH, BACK_LEFT, 59.6, style, 4.3, outline)
    )


def features_list(colourway: theme.ColourWay, outline: bool, persian: bool) -> Node:
    """The FEATURES / ویژگی‌ها list with its gold-ruled heading."""
    block = group("features-fa" if persian else "features-en")
    top = 118.6 if persian else 81.0
    title = theme.FEATURES_TITLE_FA if persian else theme.FEATURES_TITLE_EN
    title_style = (
        tp.Style(size=4.4, script="persian", weight="medium", fill=colourway.accent,
                 anchor="middle")
        if persian
        else tp.Style(size=4.2, weight="semibold", fill=colourway.accent, anchor="middle",
                      tracking=0.5)
    )
    block.add(
        art.heading_with_rules(title, BACK_CENTRE, top, 28.5, title_style, theme.GOLD, outline)
    )
    row_style = (
        tp.Style(size=3.2, script="persian", fill=theme.INK_SOFT, anchor="end")
        if persian
        else tp.Style(size=3.0, weight="medium", fill=theme.INK_SOFT)
    )
    for index, (key, label_en, label_fa) in enumerate(theme.FEATURES):
        y = (125.6 if persian else 88.4) + index * 5.7
        label = label_fa if persian else label_en
        block.add(icons.icon(key, BACK_LEFT + 2.2, y - 1.0, 5.4, colourway.accent,
                             stroke_width=1.5))
        block.add(
            tp.text(
                label,
                BACK_RIGHT if persian else BACK_LEFT + 6.4,
                y,
                tp.fit(label, row_style, 46 if persian else 48),
                outline,
            )
        )
    return block


def follow_us(outline: bool) -> Node:
    """QR code, Instagram handle and web address."""
    block = group("04-FOLLOW-US")
    block.add(art.qr_code(theme.WEBSITE_URL, BACK_LEFT, 152.0, 12.4, theme.NAVY_TEXT))
    block.add(
        tp.text(theme.FOLLOW_US, BACK_LEFT + 15.6, 155.4,
                tp.Style(size=3.1, weight="semibold", fill=theme.INK_SOFT), outline)
    )
    block.add(
        icons.icon("instagram", BACK_LEFT + 17.0, 159.4, 4.2, theme.INK_SOFT, stroke_width=1.6)
    )
    block.add(
        tp.text(theme.INSTAGRAM, BACK_LEFT + 20.0, 160.5,
                tp.Style(size=3.0, weight="medium", fill=theme.INK_SOFT), outline),
        tp.text(theme.WEBSITE, BACK_LEFT + 15.6, 165.0,
                tp.Style(size=3.0, weight="medium", fill=theme.INK_SOFT), outline),
    )
    return block


def _back_left_column(colourway: theme.ColourWay, outline: bool, gold: str) -> list[Node]:
    layer = group("03-BRAND-AND-FEATURES")
    layer.add(
        back_lockup(colourway, outline, gold),
        back_paragraph(outline),
        features_list(colourway, outline, persian=False),
        features_list(colourway, outline, persian=True),
    )
    return [layer, follow_us(outline)]


RIGHT_CENTRE, RIGHT_LEFT, RIGHT_RIGHT = 112.0, 84.0, 141.0
_RIGHT_LABEL = tp.Style(size=3.2, weight="medium", fill=theme.INK_SOFT, tracking=0.22)


def suitable_for(colourway: theme.ColourWay, outline: bool) -> Node:
    """SUITABLE FOR heading with the seven usage rows."""
    block = group("suitable-for")
    block.add(
        art.heading_with_rules(
            theme.SUITABLE_TITLE, RIGHT_CENTRE, 26.0, 28.5,
            tp.Style(size=4.2, weight="semibold", fill=colourway.accent, anchor="middle",
                     tracking=0.5),
            theme.GOLD, outline)
    )
    for index, (key, _, label_en) in enumerate(theme.USAGES):
        y = 35.4 + index * 8.1
        block.add(
            icons.icon(key, RIGHT_LEFT + 3.6, y - 1.1, 7.0, colourway.accent, stroke_width=1.55)
        )
        block.add(
            tp.text(label_en, RIGHT_LEFT + 13.0, y, tp.fit(label_en, _RIGHT_LABEL, 44), outline)
        )
    return block


def viscose_block(colourway: theme.ColourWay, outline: bool) -> Node:
    """100% VISCOSE panel with the natural fibre and extra soft rows."""
    block = group("viscose")
    block.add(art.rule(RIGHT_LEFT, 95.4, RIGHT_RIGHT, theme.GOLD, 0.32))
    block.add(
        tp.text(theme.VISCOSE_TITLE, RIGHT_CENTRE, 101.6,
                tp.Style(size=4.2, weight="semibold", fill=colourway.accent, anchor="middle",
                         tracking=0.5), outline)
    )
    block.add(art.rule(RIGHT_LEFT, 105.0, RIGHT_RIGHT, theme.GOLD, 0.32))
    for index, (key, label) in enumerate(theme.MATERIAL_ROWS):
        y = 113.4 + index * 9.4
        block.add(
            icons.icon(key, RIGHT_LEFT + 3.6, y - 1.2, 7.4, colourway.accent, stroke_width=1.5)
        )
        block.add(tp.text(label, RIGHT_LEFT + 13.0, y, tp.fit(label, _RIGHT_LABEL, 44), outline))
    return block


def origin_block(outline: bool) -> Node:
    block = group("made-in-iran")
    block.add(art.rule(RIGHT_LEFT, 128.6, RIGHT_RIGHT, theme.GOLD, 0.32))
    block.add(
        tp.text(theme.ORIGIN, RIGHT_CENTRE, 134.4,
                tp.Style(size=3.6, weight="semibold", fill=theme.NAVY_TEXT, anchor="middle",
                         tracking=0.55), outline)
    )
    return block


def certification_marks(outline: bool) -> Node:
    block = group("06-CERTIFICATION-MARKS")
    block.add(art.iran_standard_mark(93.0, 142.4, 4.1, theme.NAVY_TEXT, outline))
    block.add(art.iso_mark(111.0, 143.0, 4.0, theme.NAVY_TEXT, outline))
    block.add(icons.icon("recycle", 130.0, 143.0, 10.6, theme.BLACK, stroke_width=1.9))
    return block


def barcode_block(outline: bool) -> Node:
    return group("07-BARCODE").add(
        art.ean13(theme.BARCODE_DIGITS, 100.0, 150.0, 40.0, 14.4, outline=outline)
    )


def _back_right_column(colourway: theme.ColourWay, outline: bool) -> list[Node]:
    layer = group("05-SUITABLE-FOR")
    layer.add(
        suitable_for(colourway, outline),
        viscose_block(colourway, outline),
        origin_block(outline),
    )
    return [layer, certification_marks(outline), barcode_block(outline)]
