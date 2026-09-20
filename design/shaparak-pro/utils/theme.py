"""Brand constants, panel geometry and all copy used on the Shaparak Pro pouch.

Every measurement is expressed in millimetres, which is also the SVG user unit
used by the generator, so numbers here map 1:1 to the printed artwork.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

FONT_DIR = Path(__file__).resolve().parent.parent / "fonts"

LATIN = {
    "regular": FONT_DIR / "Montserrat-Regular.ttf",
    "medium": FONT_DIR / "Montserrat-Medium.ttf",
    "semibold": FONT_DIR / "Montserrat-SemiBold.ttf",
    "bold": FONT_DIR / "Montserrat-Bold.ttf",
}

PERSIAN = {
    "regular": FONT_DIR / "Vazirmatn-Regular.ttf",
    "medium": FONT_DIR / "Vazirmatn-Medium.ttf",
    "bold": FONT_DIR / "Vazirmatn-Bold.ttf",
}

LATIN_FAMILY = "Montserrat"
PERSIAN_FAMILY = "Vazirmatn"

# --- colours ---------------------------------------------------------------

NAVY_TEXT = "#16203F"
GOLD = "#BE8C3C"
GOLD_LIGHT = "#D9B978"
WHITE = "#FFFFFF"
PAPER = "#FDFDFC"
TOWEL = "#F7F7F5"
TOWEL_SHADE = "#E7E7E4"
INK_SOFT = "#3C4763"
BLACK = "#1A1A1A"


@dataclass(frozen=True)
class ColourWay:
    """One of the two requested pack versions."""

    key: str
    name_fa: str
    name_en: str
    primary: str  # main pouch colour
    primary_dark: str  # crimp / shadow tone
    primary_light: str  # crimp highlight tone
    accent: str  # headline colour on the white back panel
    badge: str  # "100% viscose" badge fill
    on_primary: str = WHITE


NAVY = ColourWay(
    key="navy",
    name_fa="سرمه‌ای",
    name_en="Navy",
    primary="#1F2C50",
    primary_dark="#16203F",
    primary_light="#40507B",
    accent="#1F2C50",
    badge="#22325A",
)

# Only the navy pack is produced. The generator still loops over this tuple, so
# a second colour way is one entry away.
COLOURWAYS = (NAVY,)

# --- pouch geometry --------------------------------------------------------

PANEL_W = 150.0
PANEL_H = 170.0
BLEED = 3.0
SAFE = 6.0

TOP_SEAL_H = 16.0  # crimped top seal band
BOTTOM_SEAL_H = 6.0  # crimped bottom seal band
CORNER_R = 4.0

HANG_HOLE_CY = 8.6  # centre of the euro hang slot

FRONT_WAVE_Y = 116.0  # mean height of the wavy colour break on the front
FRONT_WAVE_AMP = 4.2

# --- copy ------------------------------------------------------------------

BRAND = "SHAPARAK"
SUB_BRAND = "PRO"

TITLE_FA = "حوله یکبار مصرف بهداشتی"
TITLE_EN = "PROFESSIONAL DISPOSABLE TOWEL"
TITLE_AR = "منشفة للاستعمال الواحد"

VISCOSE_BADGE = ("100%", "VISCOSE")
EXTRA_SOFT = ("EXTRA SOFT", "NATURAL FIBER")

# icon key, English label. Every icon on the pack is labelled in English only.
USAGES = (
    ("scissors", "BARBERSHOP"),
    ("salon", "BEAUTY SALON"),
    ("paw", "PET SHOP"),
    ("dumbbell", "GYM"),
    ("pool", "POOL"),
    ("hotel", "HOTEL"),
    ("plane", "TRAVEL"),
)

SIZES_TITLE_FA = "سایزهای موجود"
SIZES = (
    ("۳۳ × ۶۰ سانتی‌متر", "سایز سالن"),
    ("۶۰ × ۶۰ سانتی‌متر", "سایز پریمیوم"),
)

BACK_PARAGRAPH = (
    "Shaparak Pro disposable towels are made",
    "from high quality material, soft and",
    "highly absorbent, ideal for professional",
    "and personal use.",
)

FEATURES_TITLE_EN = "FEATURES"

# icon key, English feature
FEATURES = (
    ("hygienic", "Hygienic & Clean"),
    ("soft", "Soft & Comfortable"),
    ("absorbent", "High Absorbency"),
    ("disposable", "Disposable"),
    ("professional", "Professional Use"),
)

SUITABLE_TITLE = "SUITABLE FOR"
VISCOSE_TITLE = "100% VISCOSE"
MATERIAL_ROWS = (
    ("leaf", "NATURAL FIBER"),
    ("cotton", "EXTRA SOFT"),
)
ORIGIN = "MADE IN IRAN"

FOLLOW_US = "Follow Us"
INSTAGRAM = "@shaparak.tissue"
WEBSITE = "www.shaparak-tissue.com"
WEBSITE_URL = "https://www.shaparak-tissue.com"

BARCODE_DIGITS = "626123456789"  # 12 digits, EAN-13 check digit is calculated
