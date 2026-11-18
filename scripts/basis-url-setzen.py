#!/usr/bin/env python3
"""Trägt eine neue Basis-URL in alle Dateien ein, die sie als festen Text brauchen.

Aufruf (aus dem Projektordner):

    python3 scripts/basis-url-setzen.py https://www.meine-domain.ch/

Die bisherige Basis-URL wird aus js/config.js gelesen und in den HTML-Seiten,
in sitemap.xml, robots.txt und js/config.js durch die neue ersetzt.
"""

import re
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
CONFIG = WURZEL / "js" / "config.js"
DATEIEN = [
    "index.html",
    "werkstatt.html",
    "kontakt.html",
    "404.html",
    "sitemap.xml",
    "robots.txt",
    "js/config.js",
]


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 1

    neu = sys.argv[1].strip()
    if not re.match(r"^https?://[^\s/]+", neu):
        print("Die Basis-URL muss mit https:// beginnen, z. B. https://www.meine-domain.ch/")
        return 1
    if not neu.endswith("/"):
        neu += "/"

    treffer = re.search(r'basisUrl:\s*"([^"]+)"', CONFIG.read_text(encoding="utf-8"))
    if not treffer:
        print(f"In {CONFIG} wurde kein Eintrag basisUrl gefunden.")
        return 1
    alt = treffer.group(1)

    if alt == neu:
        print(f"Die Basis-URL lautet bereits {neu}. Nichts zu tun.")
        return 0

    print(f"Alt: {alt}\nNeu: {neu}\n")
    for name in DATEIEN:
        pfad = WURZEL / name
        if not pfad.exists():
            print(f"  übersprungen (fehlt): {name}")
            continue
        text = pfad.read_text(encoding="utf-8")
        anzahl = text.count(alt)
        if anzahl:
            pfad.write_text(text.replace(alt, neu), encoding="utf-8")
        print(f"  {anzahl:2d} Stelle(n) ersetzt: {name}")

    print("\nFertig. Änderungen prüfen (git diff), dann committen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
