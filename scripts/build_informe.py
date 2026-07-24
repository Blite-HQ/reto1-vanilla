#!/usr/bin/env python3
"""Compile the Typst deliverables to PDF (requires the `entregables` group).

    uv run python scripts/build_informe.py            # informe/informe.pdf
    uv run python scripts/build_informe.py --slides   # + informe/slides.pdf
    uv run python scripts/build_informe.py --pitch    # + informe/pitch.pdf
"""

import argparse
from pathlib import Path

import typst

ROOT = Path(__file__).parent.parent
DOCUMENTS = {"informe": ROOT / "informe" / "informe.typ",
             "slides": ROOT / "informe" / "slides.typ",
             "pitch": ROOT / "informe" / "pitch.typ"}


def compile_document(source: Path) -> None:
    output = source.with_suffix(".pdf")
    typst.compile(str(source), output=str(output), root=str(ROOT))
    print(f"[ok] {output.relative_to(ROOT)} ({output.stat().st_size // 1024} KiB)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slides", action="store_true",
                        help="also compile the 5-minute slide deck")
    parser.add_argument("--pitch", action="store_true",
                        help="also compile the 14-slide pitch deck")
    args = parser.parse_args()
    compile_document(DOCUMENTS["informe"])
    if args.slides:
        compile_document(DOCUMENTS["slides"])
    if args.pitch:
        compile_document(DOCUMENTS["pitch"])


if __name__ == "__main__":
    main()
