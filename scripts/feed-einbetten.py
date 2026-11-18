#!/usr/bin/env python3
"""Prüft data/schalen.json und bettet den Feed fest in index.html ein.

Aufruf (aus dem Projektordner), nach jeder Änderung an data/schalen.json:

    python3 scripts/feed-einbetten.py            prüfen und einbetten
    python3 scripts/feed-einbetten.py --pruefen  nur prüfen, nichts schreiben

Was das Skript macht:

1. Es prüft jeden Eintrag in data/schalen.json (Pflichtfelder, Status, Datum,
   doppelte Nummern, fehlende Bilddateien).
2. Es schreibt die Schalen als festes HTML in index.html. Besucher ohne
   JavaScript und Suchmaschinen sehen so alle Schalen.
3. Es schreibt die strukturierten Daten (JSON-LD) der verfügbaren Schalen fest
   in den Kopf von index.html.
4. Es trägt das Datum der neuesten Schale in sitemap.xml ein.

Die Seite funktioniert auch, wenn das Skript einmal vergessen geht: Der Feed
wird im Browser weiterhin aus schalen.json aufgebaut. Veraltet sind dann nur
die Ansicht ohne JavaScript und die strukturierten Daten.

Braucht nur Python 3, keine zusätzlichen Pakete.
"""

import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote

WURZEL = Path(__file__).resolve().parent.parent
DATEN = WURZEL / "data" / "schalen.json"
CONFIG = WURZEL / "js" / "config.js"
INDEX = WURZEL / "index.html"
SITEMAP = WURZEL / "sitemap.xml"
BILDER = WURZEL / "images" / "schalen"

BREITEN = (800, 1400, 2000)
# Muss mit SIZES in js/feed.js übereinstimmen
SIZES = "(min-width: 900px) 40vw, (min-width: 560px) and (min-aspect-ratio: 4/3) 40vw, 100vw"
STATUS = ("verfuegbar", "verkauft")
ZAHL = (int, float)
PFLICHT = {
    "id": str, "titel": str, "holzart": str, "herkunft": str,
    "durchmesser_cm": ZAHL, "hoehe_cm": ZAHL, "preis_chf": ZAHL,
    "status": str, "beschrieb": str, "bilder": list, "datum": str,
}


# ---------- Prüfung ----------

def pruefe(schalen) -> list[str]:
    fehler = []
    if not isinstance(schalen, list):
        return ["schalen.json muss eine Liste von Einträgen sein."]

    gesehen = set()
    for nummer, schale in enumerate(schalen, start=1):
        wer = f"Eintrag {nummer}"
        if not isinstance(schale, dict):
            fehler.append(f"{wer}: ist kein Objekt in geschweiften Klammern.")
            continue
        if isinstance(schale.get("id"), str):
            wer = f"Schale {schale['id']}"

        for feld, typ in PFLICHT.items():
            if feld not in schale:
                fehler.append(f"{wer}: Feld «{feld}» fehlt.")
            elif not isinstance(schale[feld], typ) or isinstance(schale[feld], bool):
                fehler.append(f"{wer}: Feld «{feld}» hat den falschen Typ.")
        if any(f"{wer}:" in zeile for zeile in fehler):
            continue

        if schale["id"] in gesehen:
            fehler.append(f"{wer}: Die Nummer kommt mehrfach vor.")
        gesehen.add(schale["id"])
        if not re.fullmatch(r"[A-Za-z0-9_-]+", schale["id"]):
            fehler.append(f"{wer}: «id» darf nur Buchstaben, Ziffern, - und _ enthalten.")
        if schale["status"] not in STATUS:
            fehler.append(f"{wer}: «status» muss «verfuegbar» oder «verkauft» sein.")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", schale["datum"]):
            fehler.append(f"{wer}: «datum» muss die Form JJJJ-MM-TT haben, z. B. 2026-12-01.")
        if not schale["bilder"]:
            fehler.append(f"{wer}: Es ist kein Bild eingetragen.")

        for position, bild in enumerate(schale["bilder"], start=1):
            if not isinstance(bild, dict) or not isinstance(bild.get("datei"), str):
                fehler.append(f"{wer}, Bild {position}: «datei» fehlt.")
                continue
            if not bild.get("alt"):
                fehler.append(f"{wer}, Bild {position}: Die Bildbeschreibung «alt» fehlt.")
            for breite in BREITEN:
                pfad = BILDER / schale["id"] / f"{stamm(bild)}-{breite}.webp"
                if not pfad.is_file():
                    fehler.append(f"{wer}, Bild {position}: Datei fehlt: {pfad.relative_to(WURZEL)}")
    return fehler


# ---------- Darstellung (gleich wie in js/feed.js) ----------

def stamm(bild) -> str:
    return re.sub(r"\.webp$", "", bild["datei"], flags=re.IGNORECASE)


def zahl(wert) -> str:
    if float(wert).is_integer():
        return f"{int(wert):,}".replace(",", "’")
    return str(wert)


def masse(schale) -> str:
    return f"Ø {zahl(schale['durchmesser_cm'])} × H {zahl(schale['hoehe_cm'])} cm"


def preis(schale) -> str:
    return f"CHF {zahl(schale['preis_chf'])}"


def bild_pfad(schale, bild, breite) -> str:
    return f"images/schalen/{schale['id']}/{stamm(bild)}-{breite}.webp"


def mailto(schale, email) -> str:
    betreff = f"Anfrage {schale['titel']} – {schale['holzart']}"
    text = "\r\n".join([
        "Guten Tag",
        "",
        f"Ich interessiere mich für die {schale['titel']} "
        f"({schale['holzart']}, {masse(schale)}, {preis(schale)}).",
        "",
        "Name:",
        "Lieferadresse:",
        "Abholung oder Versand:",
        "",
        "Freundliche Grüsse",
    ])
    return (f"mailto:{quote(email, safe='@.-_+')}"
            f"?subject={quote(betreff, safe='')}&body={quote(text, safe='')}")


def eintrag_html(schale, email) -> str:
    e = html.escape
    verkauft = schale["status"] == "verkauft"
    bild = schale["bilder"][0]
    srcset = ", ".join(f"{bild_pfad(schale, bild, b)} {b}w" for b in BREITEN)

    zeilen = [
        ("Holz", schale["holzart"]),
        ("Herkunft", schale["herkunft"]),
        ("Masse", masse(schale)),
        ("Preis", "verkauft" if verkauft else preis(schale)),
    ]
    if not verkauft:
        zeilen.append(("Status", "verfügbar"))
    daten = "".join(f"<div><dt>{e(a)}</dt><dd>{e(b)}</dd></div>" for a, b in zeilen)

    teile = [
        f'<article class="schale{" ist-verkauft" if verkauft else ""}">',
        f'<div class="bildfolge"><img src="{e(bild_pfad(schale, bild, BREITEN[0]))}" '
        f'srcset="{e(srcset)}" sizes="{e(SIZES)}" width="800" height="1000" '
        f'loading="lazy" alt="{e(bild.get("alt", ""))}"></div>',
        '<div class="angaben">',
        f'<h2>{e(schale["titel"])}</h2>',
    ]
    if bild.get("legende"):
        teile.append(f'<p class="legende">{e(bild["legende"])}</p>')
    teile.append(f'<p class="beschrieb">{e(schale["beschrieb"])}</p>')
    teile.append(f'<dl class="daten">{daten}</dl>')
    if not verkauft:
        teile.append(f'<a class="anfragen" href="{e(mailto(schale, email))}">Anfragen +</a>')
    teile.append("</div>")
    teile.append("</article>")
    return "\n".join("        " + teil for teil in teile)


def feed_html(schalen, email) -> str:
    eintraege = "\n".join(eintrag_html(schale, email) for schale in schalen)
    return f'      <div class="feed">\n{eintraege}\n      </div>'


def jsonld_html(schalen, basis, name) -> str:
    produkte = []
    for schale in schalen:
        if schale["status"] != "verfuegbar":
            continue
        adresse = f"{basis}#schale-{schale['id']}"
        produkte.append({
            "@type": "Product",
            "@id": adresse,
            "name": f"{schale['titel']} – {schale['holzart']}",
            "description": schale["beschrieb"],
            "material": schale["holzart"],
            "image": [basis + bild_pfad(schale, bild, 1400) for bild in schale["bilder"]],
            "brand": {"@type": "Brand", "name": name},
            "offers": {
                "@type": "Offer",
                "url": adresse,
                "price": schale["preis_chf"],
                "priceCurrency": "CHF",
                "availability": "https://schema.org/InStock",
                "itemCondition": "https://schema.org/NewCondition",
            },
        })
    if not produkte:
        return ""
    daten = json.dumps({"@context": "https://schema.org", "@graph": produkte},
                       ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return f'  <script type="application/ld+json" id="schalen-jsonld">{daten}</script>'


# ---------- Dateien ----------

def aus_config(schluessel) -> str:
    treffer = re.search(rf'{schluessel}:\s*"([^"]*)"', CONFIG.read_text(encoding="utf-8"))
    if not treffer:
        sys.exit(f"In {CONFIG.relative_to(WURZEL)} fehlt der Eintrag «{schluessel}».")
    return treffer.group(1)


def zwischen(text, marke, inhalt) -> str:
    muster = re.compile(rf"(<!-- {marke}:START[^>]*-->\n).*?([ \t]*<!-- {marke}:ENDE -->)", re.DOTALL)
    if not muster.search(text):
        sys.exit(f"In index.html fehlen die Marken <!-- {marke}:START --> und <!-- {marke}:ENDE -->.")
    return muster.sub(lambda m: m.group(1) + (inhalt + "\n" if inhalt else "") + m.group(2), text, count=1)


def sitemap_mit_datum(text, datum) -> str:
    muster = re.compile(r"(<url><loc>[^<]*/</loc>)(?:<lastmod>[^<]*</lastmod>)?(</url>)")
    return muster.sub(lambda m: f"{m.group(1)}<lastmod>{datum}</lastmod>{m.group(2)}", text, count=1)


def main() -> int:
    nur_pruefen = "--pruefen" in sys.argv[1:]

    try:
        schalen = json.loads(DATEN.read_text(encoding="utf-8"))
    except json.JSONDecodeError as fehler:
        print(f"data/schalen.json ist kein gültiges JSON: Zeile {fehler.lineno}, {fehler.msg}.")
        print("Häufige Ursache: ein fehlendes oder überzähliges Komma.")
        return 1

    fehler = pruefe(schalen)
    if fehler:
        print(f"{len(fehler)} Problem(e) in data/schalen.json:\n")
        for zeile in fehler:
            print(f"  - {zeile}")
        return 1

    schalen.sort(key=lambda schale: schale["datum"], reverse=True)
    verfuegbar = sum(schale["status"] == "verfuegbar" for schale in schalen)
    print(f"data/schalen.json in Ordnung: {len(schalen)} Schalen, {verfuegbar} verfügbar.")

    index_alt = INDEX.read_text(encoding="utf-8")
    index_neu = zwischen(index_alt, "FEED", feed_html(schalen, aus_config("email")))
    index_neu = zwischen(index_neu, "JSONLD", jsonld_html(schalen, aus_config("basisUrl"), aus_config("name")))

    sitemap_alt = SITEMAP.read_text(encoding="utf-8")
    sitemap_neu = sitemap_mit_datum(sitemap_alt, schalen[0]["datum"]) if schalen else sitemap_alt

    aktuell = index_alt == index_neu and sitemap_alt == sitemap_neu
    if nur_pruefen:
        if aktuell:
            print("index.html und sitemap.xml sind aktuell.")
            return 0
        print("index.html oder sitemap.xml ist veraltet. Bitte ausführen: python3 scripts/feed-einbetten.py")
        return 1

    if aktuell:
        print("index.html und sitemap.xml sind bereits aktuell. Nichts zu tun.")
        return 0
    INDEX.write_text(index_neu, encoding="utf-8")
    SITEMAP.write_text(sitemap_neu, encoding="utf-8")
    print("index.html und sitemap.xml aktualisiert. Änderungen prüfen (git diff), dann committen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
