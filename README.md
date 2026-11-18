# Webseite gedrechselte Holzschalen

Statische Webseite ohne Webshop: Die Schalen stehen in einem Feed, bestellt wird per E-Mail.
Reines HTML, CSS und JavaScript, kein Build-Schritt, keine externen Abhängigkeiten.

## Aufbau

| Datei / Ordner | Inhalt |
| --- | --- |
| `index.html` | Feed mit allen Schalen und Filter |
| `werkstatt.html` | Person, Arbeitsweise, Pflege |
| `kontakt.html` | Kontakt, Impressum, Datenschutz |
| `data/schalen.json` | Alle Schalen (Texte, Masse, Preis, Status, Bilder) |
| `images/schalen/<id>/` | Bilder je Schale in drei Breiten |
| `css/style.css` | Gestaltung; Farben und Schriften als Variablen ganz oben |
| `js/config.js` | Basis-URL, Name und E-Mail-Adresse |
| `fonts/` | Selbst gehostete Schriften mit Lizenztexten |
| `scripts/` | Hilfsskripte für Bilder, Feed-Einbettung und Domainwechsel |
| `originale/` | Originalfotos, werden nicht veröffentlicht (`.gitignore`) |

## Vor der Veröffentlichung: Platzhalter ersetzen

Im ganzen Projekt suchen und ersetzen (z. B. im Editor mit «In Dateien suchen»):

- `[NAME]` – voller Name für Impressum und Datenschutz in `kontakt.html` (die Seite selbst heisst «Laurin», festgelegt in `js/config.js` und in den Seitentiteln)
- `[EMAIL]` – E-Mail-Adresse für Anfragen
- `[ADRESSE]` – Postadresse für Impressum und Datenschutz
- `https://BENUTZERNAME.github.io/REPO/` – siehe «Basis-URL» unten

Danach einmal `python3 scripts/feed-einbetten.py` ausführen, damit auch der fest eingebettete Feed die neuen Angaben erhält.

Alle Textentwürfe sind im Code mit `<!-- ENTWURF -->` markiert. Impressum und Datenschutzerklärung sind Entwürfe und sollten vor der Veröffentlichung geprüft werden. Die Beispiel-Schalen und ihre Bilder sind Platzhalter.

## Seite lokal ansehen

Im Projektordner:

```bash
python3 -m http.server 8000
```

Dann im Browser `http://localhost:8000/` öffnen. Ein Doppelklick auf `index.html` genügt nicht, weil der Browser die Datei `schalen.json` nur über einen Server laden darf.

## Neue Schale hinzufügen

1. **Nummer festlegen**, z. B. `015`.
2. **Fotos ablegen** in `originale/015/`. Die Reihenfolge der Dateinamen bestimmt die Reihenfolge im Feed (z. B. `1-aussen.jpg`, `2-innen.jpg`). Hochformat 4:5 passt am besten; andere Formate werden mittig beschnitten.
3. **Bilder optimieren** (siehe unten):
   ```bash
   python3 scripts/bilder-optimieren.py 015
   ```
4. **Eintrag in `data/schalen.json`** ergänzen. Die Reihenfolge in der Datei spielt keine Rolle, der Feed sortiert nach `datum` (neueste oben):
   ```json
   {
     "id": "015",
     "titel": "Schale Nr. 015",
     "holzart": "Kirsche",
     "herkunft": "Ort, Region",
     "durchmesser_cm": 24,
     "hoehe_cm": 8,
     "preis_chf": 190,
     "status": "verfuegbar",
     "beschrieb": "Ein bis zwei Sätze.",
     "bilder": [
       { "datei": "01.webp", "alt": "Was auf dem Bild zu sehen ist", "legende": "Kurze Bildunterschrift" }
     ],
     "datum": "2026-12-01"
   }
   ```
   - `id` muss dem Ordnernamen in `images/schalen/` entsprechen.
   - `datei` nennt nur die Bildnummer: Aus `01.webp` werden automatisch `01-800.webp`, `01-1400.webp` und `01-2000.webp` geladen.
   - `alt` beschreibt das Bild für Menschen, die es nicht sehen. `legende` erscheint kursiv unter dem Titel.
   - Zwischen den Einträgen steht ein Komma, nach dem letzten keines.
5. **Prüfen und einbetten:**
   ```bash
   python3 scripts/feed-einbetten.py
   ```
   Das Skript meldet Tippfehler und fehlende Bilder und schreibt den Feed fest in `index.html` (siehe «Feed einbetten»).
6. **Lokal ansehen**, dann committen und pushen.

## Schale als verkauft markieren

In `data/schalen.json` beim Eintrag `"status": "verfuegbar"` auf `"status": "verkauft"` ändern, `python3 scripts/feed-einbetten.py` ausführen, committen, pushen. Die Schale bleibt im Feed sichtbar, der Preis wird durch «verkauft» ersetzt, der Anfrage-Link verschwindet.

## Feed einbetten

Nach jeder Änderung an `data/schalen.json`:

```bash
python3 scripts/feed-einbetten.py
```

Das Skript braucht nur Python 3 und macht vier Dinge:

- Es prüft `schalen.json` auf fehlende Felder, Tippfehler beim Status, doppelte Nummern und fehlende Bilddateien.
- Es schreibt alle Schalen als festes HTML in `index.html`. Besucher ohne JavaScript und Suchmaschinen sehen so den ganzen Feed (ohne Filter und Bildfolge).
- Es schreibt die strukturierten Daten der verfügbaren Schalen fest in `index.html`.
- Es trägt das Datum der neuesten Schale in `sitemap.xml` ein.

Mit `--pruefen` wird nur geprüft und nichts geschrieben. Geht das Skript einmal vergessen, funktioniert die Seite trotzdem: Im Browser wird der Feed weiterhin aus `schalen.json` aufgebaut, veraltet sind dann nur die Ansicht ohne JavaScript und die strukturierten Daten.

## Bilder optimieren

Das Skript braucht Python 3 und Pillow. Einmalig einrichten:

```bash
python3 -m venv .venv
```

```bash
.venv/bin/pip install Pillow
```

Danach:

```bash
.venv/bin/python scripts/bilder-optimieren.py
```

- Ohne Angabe werden alle Ordner in `originale/` verarbeitet, mit Nummer nur diese Schale (`… bilder-optimieren.py 015`).
- Pro Foto entstehen drei WebP-Dateien (800, 1400 und 2000 px breit, Qualität 80) in `images/schalen/<id>/`.
- Metadaten wie Aufnahmeort (GPS) und Kameradaten werden entfernt.
- Am Schluss zeigt das Skript, was in `schalen.json` einzutragen ist.
- Unterstützt werden JPG, PNG, TIFF und WebP. HEIC-Fotos vom iPhone vorher als JPG exportieren.

## GitHub Pages aktivieren

1. Auf GitHub ein neues, öffentliches Repository anlegen und dieses Projekt hochladen:
   ```bash
   git remote add origin https://github.com/BENUTZERNAME/REPO.git
   ```
   ```bash
   git push -u origin main
   ```
2. Im Repository unter **Settings → Pages** bei «Build and deployment» die Quelle **Deploy from a branch** wählen, Branch **main**, Ordner **/ (root)**, speichern.
3. Nach ein bis zwei Minuten ist die Seite unter `https://BENUTZERNAME.github.io/REPO/` erreichbar.
4. Die Basis-URL eintragen (siehe unten), committen, pushen.

Die Datei `.nojekyll` sorgt dafür, dass GitHub die Dateien unverändert ausliefert.

## Basis-URL

Vorschaubilder für soziale Medien, `sitemap.xml` und `robots.txt` brauchen die vollständige Adresse der Seite als festen Text. Sie wird mit einem Befehl überall eingetragen:

```bash
python3 scripts/basis-url-setzen.py https://BENUTZERNAME.github.io/REPO/
```

Das Skript liest die bisherige Adresse aus `js/config.js` und ersetzt sie in den HTML-Seiten, in `sitemap.xml`, `robots.txt` und `js/config.js`. Alle Links innerhalb der Seite sind relativ und brauchen keine Anpassung.

## Eigene Domain verbinden

1. **Domain bei GitHub eintragen:** Im Repository unter **Settings → Pages → Custom domain** die Domain eingeben, z. B. `www.meine-domain.ch`. GitHub legt dabei eine Datei `CNAME` im Repository an. Danach lokal `git pull` ausführen.
2. **DNS-Einträge beim Domain-Anbieter setzen:**
   - Für `www.meine-domain.ch`: ein **CNAME**-Eintrag auf `BENUTZERNAME.github.io`
   - Für `meine-domain.ch` (ohne www): vier **A**-Einträge auf
     `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - Die aktuell gültigen Adressen stehen in der GitHub-Dokumentation unter «Managing a custom domain for your GitHub Pages site». Bitte dort gegenprüfen.
3. **Warten**, bis die DNS-Änderung wirkt (meist unter einer Stunde, höchstens ein Tag).
4. **HTTPS erzwingen:** Unter **Settings → Pages** das Häkchen **Enforce HTTPS** setzen, sobald es anwählbar ist.
5. **Basis-URL anpassen:**
   ```bash
   python3 scripts/basis-url-setzen.py https://www.meine-domain.ch/
   ```
   Committen und pushen.

Hinweis: Suchmaschinen lesen `robots.txt` nur im Wurzelverzeichnis einer Domain. Unter `BENUTZERNAME.github.io/REPO/` wird sie deshalb nicht beachtet, mit eigener Domain schon.

## Gestaltung anpassen

Farben, Schriften und Abstände stehen als CSS-Variablen am Anfang von `css/style.css`. Die Schriften Source Serif 4 (Titel) und Public Sans (Text) liegen als WOFF2-Dateien in `fonts/` und werden vom eigenen Server geladen, nichts kommt von fremden Servern. Beide stehen unter der SIL Open Font License, die Lizenztexte liegen daneben.
