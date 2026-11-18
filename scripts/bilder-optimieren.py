#!/usr/bin/env python3
"""Macht aus Originalfotos Web-Bilder für die Schalen.

Aufruf (aus dem Projektordner):

    python3 scripts/bilder-optimieren.py          alle Ordner in originale/
    python3 scripts/bilder-optimieren.py 015      nur die Schale 015
    python3 scripts/bilder-optimieren.py 015 016  mehrere Schalen

Liest die Originale aus originale/<id>/ (in alphabetischer Reihenfolge) und
schreibt pro Bild drei WebP-Dateien nach images/schalen/<id>/:

    01-800.webp, 01-1400.webp, 01-2000.webp, 02-800.webp, ...

Metadaten (EXIF, GPS, XMP) werden nicht übernommen. Am Schluss gibt das Skript
aus, was in data/schalen.json einzutragen ist.

Voraussetzung: Pillow (python3 -m pip install Pillow)
"""

import json
import sys
from pathlib import Path

try:
    from PIL import Image, ImageOps
except ImportError:
    sys.exit("Pillow fehlt. Installation: python3 -m pip install Pillow")

WURZEL = Path(__file__).resolve().parent.parent
ORIGINALE = WURZEL / "originale"
ZIEL = WURZEL / "images" / "schalen"
DATEN = WURZEL / "data" / "schalen.json"

BREITEN = (800, 1400, 2000)
QUALITAET = 80
ENDUNGEN = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}


def optimiere(schalen_id: str) -> list[str]:
    """Wandelt alle Originale einer Schale um und gibt die Dateinamen für schalen.json zurück."""
    quelle = ORIGINALE / schalen_id
    if not quelle.is_dir():
        print(f"  Ordner fehlt: {quelle}")
        return []

    originale = sorted(
        pfad for pfad in quelle.iterdir()
        if pfad.suffix.lower() in ENDUNGEN and not pfad.name.startswith(".")
    )
    if not originale:
        print(f"  Keine Bilder gefunden in {quelle}")
        return []

    ziel = ZIEL / schalen_id
    ziel.mkdir(parents=True, exist_ok=True)
    namen = []

    for nummer, pfad in enumerate(originale, start=1):
        stamm = f"{nummer:02d}"
        with Image.open(pfad) as original:
            # Drehung aus den EXIF-Daten anwenden, bevor die Metadaten wegfallen
            bild = ImageOps.exif_transpose(original)
            farbprofil = bild.info.get("icc_profile")
            bild = bild.convert("RGB")

        if bild.width < BREITEN[-1]:
            print(f"  Hinweis: {pfad.name} ist nur {bild.width} px breit, "
                  f"grössere Stufen werden nicht hochgerechnet.")

        for breite in BREITEN:
            if bild.width > breite:
                hoehe = round(bild.height * breite / bild.width)
                stufe = bild.resize((breite, hoehe), Image.Resampling.LANCZOS)
            else:
                stufe = bild
            # Nur Bildpunkte und Farbprofil speichern: kein EXIF, kein GPS, kein XMP
            stufe.save(
                ziel / f"{stamm}-{breite}.webp",
                "WEBP",
                quality=QUALITAET,
                method=6,
                icc_profile=farbprofil,
                exif=b"",
                xmp=b"",
            )

        print(f"  {pfad.name} → {stamm}-{{{', '.join(str(b) for b in BREITEN)}}}.webp")
        namen.append(f"{stamm}.webp")

    return namen


def main() -> int:
    if not ORIGINALE.is_dir():
        print(f"Ordner fehlt: {ORIGINALE}")
        return 1

    ids = sys.argv[1:] or sorted(
        pfad.name for pfad in ORIGINALE.iterdir()
        if pfad.is_dir() and not pfad.name.startswith(".")
    )
    if not ids:
        print("Keine Unterordner in originale/ gefunden. Erwartet wird z. B. originale/015/")
        return 1

    vorhanden = set()
    if DATEN.exists():
        vorhanden = {eintrag["id"] for eintrag in json.loads(DATEN.read_text(encoding="utf-8"))}

    for schalen_id in ids:
        print(f"\nSchale {schalen_id}")
        namen = optimiere(schalen_id)
        if not namen:
            continue

        bilder = [{"datei": name, "alt": "", "legende": ""} for name in namen]
        if schalen_id in vorhanden:
            print(f"\n  Eintrag {schalen_id} besteht bereits in data/schalen.json. "
                  f"Dort «bilder» ersetzen durch:")
        else:
            print(f"\n  Eintrag {schalen_id} fehlt noch in data/schalen.json. "
                  f"Neuen Eintrag anlegen mit:")
        print('  "bilder": ' + json.dumps(bilder, ensure_ascii=False, indent=2).replace("\n", "\n  "))
        print("  Bitte «alt» (Bildbeschreibung) und «legende» ausfüllen.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
