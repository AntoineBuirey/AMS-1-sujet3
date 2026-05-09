"""Utilities for cleaning OCR-like text extracted from the sample novels."""

from __future__ import annotations

import re

from .standardizer import normalize_apostrophes


_PAGE_MARKER_RE = re.compile(r"^\s*-\s*\d+\s*-\s*$")


def clean_text(text: str) -> str:
    """Clean raw book text and return a normalized version.

    The cleaning is intentionally conservative:
    - normalize apostrophe variants
    - remove simple page-number markers such as "- 12 -"
    - repair OCR line breaks inside paragraphs
    - preserve paragraph breaks
    - collapse repeated whitespace
    """
    text = normalize_apostrophes(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    cleaned_lines: list[str] = []
    for raw_line in text.split("\n"):
        line = raw_line.strip()
        if not line:
            cleaned_lines.append("")
            continue
        if _PAGE_MARKER_RE.match(line):
            continue
        cleaned_lines.append(line)

    text = "\n".join(cleaned_lines)

    # Join line wraps within paragraphs while keeping blank lines as separators.
    paragraphs = [paragraph for paragraph in re.split(r"\n\s*\n", text) if paragraph.strip()]
    normalized_paragraphs: list[str] = []
    for paragraph in paragraphs:
        paragraph = re.sub(r"(\w)-\n(\w)", r"\1\2", paragraph)
        paragraph = re.sub(r"\n(?=\S)", " ", paragraph)
        paragraph = re.sub(r"\s+", " ", paragraph).strip()
        if paragraph:
            normalized_paragraphs.append(paragraph)

    return "\n\n".join(normalized_paragraphs)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Clean raw book text.")
    parser.add_argument("input_file", help="Path to the input text file.")
    parser.add_argument("output_file", help="Path to the output cleaned text file.")
    args = parser.parse_args()

    with open(args.input_file, "r", encoding="utf-8") as f:
        raw_text = f.read()

    cleaned_text = clean_text(raw_text)

    with open(args.output_file, "w", encoding="utf-8") as f:
        f.write(cleaned_text)
        
if __name__ == "__main__":
    main()