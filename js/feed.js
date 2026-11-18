/* Feed: Schalen aus data/schalen.json rendern, filtern, Bildfolge, Anfrage-Link, JSON-LD */
(function () {
  "use strict";

  var SITE = window.SITE || {};
  var BREITEN = [800, 1400, 2000];
  // Muss mit SIZES in scripts/feed-einbetten.py übereinstimmen
  var SIZES = "(min-width: 900px) 40vw, (min-width: 560px) and (min-aspect-ratio: 4/3) 40vw, 100vw";
  var STATUS = ["verfuegbar", "verkauft"];

  var feed = document.getElementById("feed");
  if (!feed) return;

  var filterLinks = document.querySelectorAll(".filter a");
  var statusZeile = document.getElementById("feed-status");
  var schalen = [];
  var ruhig = window.matchMedia("(prefers-reduced-motion: reduce)");

  /* ---------- Hilfen ---------- */

  function el(tag, klasse, text) {
    var knoten = document.createElement(tag);
    if (klasse) knoten.className = klasse;
    if (text !== undefined) knoten.textContent = text;
    return knoten;
  }

  function zwei(zahl) {
    return String(zahl).padStart(2, "0");
  }

  function zahl(wert) {
    return Number(wert).toLocaleString("de-CH");
  }

  function masse(schale) {
    return "Ø " + zahl(schale.durchmesser_cm) + " × H " + zahl(schale.hoehe_cm) + " cm";
  }

  function preis(schale) {
    return "CHF " + zahl(schale.preis_chf);
  }

  function bildPfad(schale, bild, breite) {
    var stamm = bild.datei.replace(/\.webp$/i, "");
    return "images/schalen/" + schale.id + "/" + stamm + "-" + breite + ".webp";
  }

  function setzeBild(img, schale, bild) {
    img.srcset = BREITEN.map(function (breite) {
      return bildPfad(schale, bild, breite) + " " + breite + "w";
    }).join(", ");
    img.src = bildPfad(schale, bild, BREITEN[0]);
    img.alt = bild.alt || "";
  }

  function statusAusUrl() {
    var wert = new URLSearchParams(window.location.search).get("status");
    return STATUS.indexOf(wert) !== -1 ? wert : "alle";
  }

  /* ---------- Anfrage per E-Mail ---------- */

  function mailtoLink(schale) {
    var betreff = "Anfrage " + schale.titel + " – " + schale.holzart;
    var text = [
      "Guten Tag",
      "",
      "Ich interessiere mich für die " + schale.titel +
        " (" + schale.holzart + ", " + masse(schale) + ", " + preis(schale) + ").",
      "",
      "Name:",
      "Lieferadresse:",
      "Abholung oder Versand:",
      "",
      "Freundliche Grüsse"
    ].join("\r\n");

    return "mailto:" + encodeURI(SITE.email || "") +
      "?subject=" + encodeURIComponent(betreff) +
      "&body=" + encodeURIComponent(text);
  }

  /* ---------- Ein Eintrag ---------- */

  function datenZeile(liste, begriff, wert) {
    var zeile = el("div");
    zeile.appendChild(el("dt", "", begriff));
    zeile.appendChild(el("dd", "", wert));
    liste.appendChild(zeile);
  }

  function baueEintrag(schale, istErster) {
    var bilder = schale.bilder || [];
    var verkauft = schale.status === "verkauft";
    var aktuell = 0;

    var artikel = el("article", "schale" + (verkauft ? " ist-verkauft" : ""));
    artikel.id = "schale-" + schale.id;

    var titel = el("h2", "", schale.titel);
    titel.id = "titel-" + schale.id;
    artikel.setAttribute("aria-labelledby", titel.id);

    var legende = el("p", "legende");

    /* Bildfolge */
    var folge = el("div", "bildfolge");
    if (bilder.length) {
      var img = document.createElement("img");
      img.sizes = SIZES;
      img.width = 800;
      img.height = 1000;
      img.decoding = "async";
      if (istErster) {
        img.loading = "eager";
        img.fetchPriority = "high";
      } else {
        img.loading = "lazy";
      }
      setzeBild(img, schale, bilder[0]);
      legende.textContent = bilder[0].legende || "";

      if (bilder.length > 1) {
        var knopf = el("button", "bild-knopf");
        knopf.type = "button";
        var hinweis = el("span", "vh");
        var zaehler = el("p", "zaehler");
        zaehler.setAttribute("aria-hidden", "true");
        legende.setAttribute("aria-live", "polite");

        var beschrifte = function () {
          zaehler.textContent = zwei(aktuell + 1) + " / " + zwei(bilder.length);
          hinweis.textContent = " – Bild " + (aktuell + 1) + " von " + bilder.length +
            ", weiter zum nächsten Bild";
          legende.textContent = bilder[aktuell].legende || "";
        };

        var zeige = function (index) {
          aktuell = (index + bilder.length) % bilder.length;
          beschrifte();
          if (ruhig.matches) {
            setzeBild(img, schale, bilder[aktuell]);
            return;
          }
          folge.classList.add("wechselt");
          var fertig = function () {
            folge.classList.remove("wechselt");
          };
          window.setTimeout(function () {
            img.addEventListener("load", fertig, { once: true });
            img.addEventListener("error", fertig, { once: true });
            setzeBild(img, schale, bilder[aktuell]);
            window.setTimeout(fertig, 1500);
          }, 120);
        };

        var gewischt = false;
        var startX = 0;
        var startY = 0;

        knopf.addEventListener("click", function () {
          if (gewischt) {
            gewischt = false;
            return;
          }
          zeige(aktuell + 1);
        });

        knopf.addEventListener("keydown", function (ereignis) {
          if (ereignis.key === "ArrowRight") {
            ereignis.preventDefault();
            zeige(aktuell + 1);
          } else if (ereignis.key === "ArrowLeft") {
            ereignis.preventDefault();
            zeige(aktuell - 1);
          }
        });

        knopf.addEventListener("touchstart", function (ereignis) {
          startX = ereignis.changedTouches[0].clientX;
          startY = ereignis.changedTouches[0].clientY;
          gewischt = false;
        }, { passive: true });

        knopf.addEventListener("touchend", function (ereignis) {
          var dx = ereignis.changedTouches[0].clientX - startX;
          var dy = ereignis.changedTouches[0].clientY - startY;
          if (Math.abs(dx) > 40 && Math.abs(dx) > Math.abs(dy)) {
            gewischt = true;
            zeige(dx < 0 ? aktuell + 1 : aktuell - 1);
            // Falls dem Wischen kein Klick folgt, die Sperre wieder lösen
            window.setTimeout(function () { gewischt = false; }, 400);
          }
        }, { passive: true });

        knopf.appendChild(img);
        knopf.appendChild(hinweis);
        folge.appendChild(knopf);
        folge.appendChild(zaehler);
        beschrifte();
      } else {
        folge.appendChild(img);
      }
    }
    artikel.appendChild(folge);

    /* Angaben */
    var angaben = el("div", "angaben");
    angaben.appendChild(titel);
    if (legende.textContent || bilder.length > 1) angaben.appendChild(legende);
    if (schale.beschrieb) angaben.appendChild(el("p", "beschrieb", schale.beschrieb));

    var liste = el("dl", "daten");
    datenZeile(liste, "Holz", schale.holzart);
    datenZeile(liste, "Herkunft", schale.herkunft);
    datenZeile(liste, "Masse", masse(schale));
    if (verkauft) {
      datenZeile(liste, "Preis", "verkauft");
    } else {
      datenZeile(liste, "Preis", preis(schale));
      datenZeile(liste, "Status", "verfügbar");
    }
    angaben.appendChild(liste);

    if (!verkauft) {
      var anfrage = el("a", "anfragen", "Anfragen +");
      anfrage.href = mailtoLink(schale);
      anfrage.setAttribute("aria-label", schale.titel + " per E-Mail anfragen");
      angaben.appendChild(anfrage);

      // Für alle ohne eingerichtetes Mailprogramm: Adresse zum Kopieren
      if (SITE.email) {
        var alternative = el("p", "anfrage-alternative", "Kein Mailprogramm? Adresse kopieren: ");
        var kopieren = el("button", "kopieren", SITE.email);
        kopieren.type = "button";
        kopieren.setAttribute("aria-label", "E-Mail-Adresse " + SITE.email + " kopieren");
        var rueckmeldung = el("span");
        rueckmeldung.setAttribute("role", "status");
        kopieren.addEventListener("click", function () {
          if (!navigator.clipboard) return;
          navigator.clipboard.writeText(SITE.email).then(function () {
            rueckmeldung.textContent = " – kopiert";
            window.setTimeout(function () { rueckmeldung.textContent = ""; }, 2500);
          });
        });
        alternative.appendChild(kopieren);
        alternative.appendChild(rueckmeldung);
        angaben.appendChild(alternative);
      }
    }

    artikel.appendChild(angaben);
    return artikel;
  }

  /* ---------- Feed und Filter ---------- */

  function rendere() {
    var status = statusAusUrl();

    filterLinks.forEach(function (link) {
      if (link.dataset.status === status) {
        link.setAttribute("aria-current", "true");
      } else {
        link.removeAttribute("aria-current");
      }
    });

    var auswahl = schalen.filter(function (schale) {
      return status === "alle" || schale.status === status;
    });

    var teil = document.createDocumentFragment();
    if (!auswahl.length) {
      teil.appendChild(el("p", "meldung", status === "verfuegbar"
        ? "Zurzeit sind alle Schalen verkauft. Neue Stücke folgen."
        : "Hier gibt es noch nichts zu sehen."));
    }
    auswahl.forEach(function (schale, index) {
      teil.appendChild(baueEintrag(schale, index === 0));
    });
    feed.replaceChildren(teil);

    // Für Screenreader ansagen, wie viele Schalen der Filter zeigt
    if (statusZeile) {
      statusZeile.textContent = auswahl.length === 1
        ? "1 Schale angezeigt"
        : auswahl.length + " Schalen angezeigt";
    }
  }

  filterLinks.forEach(function (link) {
    link.addEventListener("click", function (ereignis) {
      if (ereignis.metaKey || ereignis.ctrlKey || ereignis.shiftKey) return;
      ereignis.preventDefault();
      window.history.pushState(null, "", link.getAttribute("href"));
      rendere();
    });
  });

  window.addEventListener("popstate", rendere);

  /* ---------- Strukturierte Daten ---------- */

  function schreibeJsonLd() {
    // Fest eingebettete Daten (scripts/feed-einbetten.py) haben Vorrang
    if (document.getElementById("schalen-jsonld")) return;
    var basis = SITE.basisUrl || "";
    var produkte = schalen.filter(function (schale) {
      return schale.status === "verfuegbar";
    }).map(function (schale) {
      return {
        "@type": "Product",
        "@id": basis + "#schale-" + schale.id,
        "name": schale.titel + " – " + schale.holzart,
        "description": schale.beschrieb,
        "material": schale.holzart,
        "image": (schale.bilder || []).map(function (bild) {
          return basis + bildPfad(schale, bild, 1400);
        }),
        "brand": { "@type": "Brand", "name": SITE.name },
        "offers": {
          "@type": "Offer",
          "url": basis + "#schale-" + schale.id,
          "price": schale.preis_chf,
          "priceCurrency": "CHF",
          "availability": "https://schema.org/InStock",
          "itemCondition": "https://schema.org/NewCondition"
        }
      };
    });
    if (!produkte.length) return;

    var skript = document.createElement("script");
    skript.type = "application/ld+json";
    skript.textContent = JSON.stringify({ "@context": "https://schema.org", "@graph": produkte });
    document.head.appendChild(skript);
  }

  /* ---------- Start ---------- */

  fetch("data/schalen.json")
    .then(function (antwort) {
      if (!antwort.ok) throw new Error("HTTP " + antwort.status);
      return antwort.json();
    })
    .then(function (daten) {
      schalen = daten.slice().sort(function (a, b) {
        return String(b.datum).localeCompare(String(a.datum));
      });

      // Direktlink auf eine Schale (#schale-012): Ist sie ausgefiltert, den Filter aufheben
      var marke = window.location.hash.slice(1);
      var gemeint = schalen.filter(function (schale) {
        return "schale-" + schale.id === marke;
      })[0];
      var status = statusAusUrl();
      if (gemeint && status !== "alle" && gemeint.status !== status) {
        window.history.replaceState(null, "", window.location.pathname + window.location.hash);
      }

      rendere();
      schreibeJsonLd();

      if (marke) {
        var ziel = document.getElementById(marke);
        if (ziel) ziel.scrollIntoView();
      }
    }, function () {
      // Nur Ladefehler landen hier; Fehler beim Aufbau erscheinen in der Konsole
      feed.replaceChildren(el("p", "meldung",
        "Die Schalen konnten nicht geladen werden. Bitte die Seite neu laden."));
    });
})();
