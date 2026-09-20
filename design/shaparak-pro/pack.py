#!/usr/bin/env python3
"""Bundle the artwork into one ZIP that can be sent to a designer.

``output/`` is organised for the build; this script re-organises the same
files for somebody who just received a link: the index and the all-in-one
file at the top, then the separated items, the finished panels and the
fonts.

The archive is written deterministically - entries sorted, one fixed
timestamp - so rebuilding it without changing the artwork produces a
byte-identical file and git sees no new blob.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "output"
ARCHIVE = ROOT / "shaparak-pro-artwork.zip"
TOP = "shaparak-pro-artwork"
STAMP = (2026, 1, 1, 0, 0, 0)  # fixed so identical artwork gives an identical zip

# (source, destination inside the archive); directories are copied recursively
PLAN: tuple[tuple[Path, str], ...] = (
    (ROOT / "HANDOVER.md", "00-START-HERE.md"),
    (ROOT / "README.md", "README-full.md"),
    (OUTPUT / "assets" / "00-INDEX.pdf", "00-INDEX.pdf"),
    (OUTPUT / "assets" / "00-INDEX.png", "00-INDEX.png"),
    (OUTPUT / "assets" / "00-ALL-ITEMS.ai", "00-ALL-ITEMS.ai"),
    (OUTPUT / "assets" / "00-ALL-ITEMS.eps", "00-ALL-ITEMS.eps"),
    (OUTPUT / "assets" / "00-ALL-ITEMS.pdf", "00-ALL-ITEMS.pdf"),
    (OUTPUT / "assets" / "preview", "items-preview"),
    (OUTPUT / "ai", "panels/ai"),
    (OUTPUT / "eps", "panels/eps"),
    (OUTPUT / "svg-outlined", "panels/svg-outlined"),
    (OUTPUT / "svg-live-text", "panels/svg-live-text"),
    (OUTPUT / "pdf", "panels/pdf"),
    (OUTPUT / "preview", "panels/preview"),
    (ROOT / "fonts", "fonts"),
)

ITEM_CATEGORIES = ("01-logo", "02-illustration", "03-front-blocks", "04-back-blocks",
                   "05-codes-and-marks", "06-icons", "07-type")


def entries() -> list[tuple[Path, str]]:
    """Every file to archive, as (source, name inside the archive)."""
    collected: list[tuple[Path, str]] = []
    for source, destination in PLAN:
        if source.is_dir():
            collected += [
                (path, f"{destination}/{path.relative_to(source).as_posix()}")
                for path in source.rglob("*")
                if path.is_file()
            ]
        elif source.is_file():
            collected.append((source, destination))
    for category in ITEM_CATEGORIES:
        folder = OUTPUT / "assets" / category
        collected += [
            (path, f"items/{category}/{path.name}")
            for path in folder.iterdir()
            if path.is_file()
        ]
    return sorted(collected, key=lambda pair: pair[1])


def build() -> Path:
    files = entries()
    missing = [str(path) for path, _ in files if not path.exists()]
    if missing:
        raise SystemExit("missing files, run generate.py first:\n  " + "\n  ".join(missing))

    with zipfile.ZipFile(ARCHIVE, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for source, name in files:
            info = zipfile.ZipInfo(f"{TOP}/{name}", date_time=STAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, source.read_bytes())
    return ARCHIVE


def main() -> None:
    archive = build()
    with zipfile.ZipFile(archive) as opened:
        count = len(opened.namelist())
    print(f"wrote {archive.relative_to(ROOT)} - {count} files, "
          f"{archive.stat().st_size / 1_048_576:.1f} MB")


if __name__ == "__main__":
    main()
