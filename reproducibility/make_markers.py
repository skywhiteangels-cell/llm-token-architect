# -*- coding: utf-8 -*-
"""Создаёт markers.txt из фактических строк и проверяет round-trip.

Файл нужен, чтобы утверждение в статье было проверяемым: pdfLaTeX заменяет
эти глифы типографическими фолбэками, а здесь лежат исходные байты.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "markers.txt")

MARKERS = [
    ("A_korean", "점점점◁", "v16 arm A: Hangul marker, 4 characters"),
    ("B_geometry", "▤▤▤▤", "v16 arm B: geometric block, 4 characters"),
]

lines = [
    "# Exact v16 markers, byte for byte.",
    "#",
    "# The PDF renders these glyphs through typographic fallbacks",
    "# (jeom for U+C810, boxminus for U+25A4, triangleleft for U+25C1),",
    "# so the printed page does not show the bytes used in the experiment.",
    "# This file is the reference: the strings below are the ones sent in the",
    "# prompt field of the raw telemetry archives.",
    "#",
    "# Format: name <TAB> string <TAB> hex bytes <TAB> bytes <TAB> chars",
    "",
]

for name, s, note in MARKERS:
    raw = s.encode("utf-8")
    hexs = " ".join("%02X" % b for b in raw)
    assert raw.decode("utf-8") == s, "round-trip failed for %s" % name
    assert len(raw) == 12, (name, len(raw))
    lines.append("%s\t%s\t%s\t%d\t%d\t# %s" % (name, s, hexs, len(raw), len(s), note))

with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(lines) + "\n")

print("записано: %s (%d байт)" % (OUT, os.path.getsize(OUT)))
for name, s, _ in MARKERS:
    print("  %-11s %d байт, %d символов" % (name, len(s.encode('utf-8')), len(s)))
