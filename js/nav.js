/* Navigation (Overlay auf kleinen Bildschirmen) und E-Mail-Links */
(function () {
  "use strict";

  var SITE = window.SITE || {};

  // E-Mail-Adresse aus config.js in alle Links mit data-email eintragen
  document.querySelectorAll("a[data-email]").forEach(function (link) {
    if (!SITE.email) return;
    link.href = "mailto:" + encodeURI(SITE.email);
    link.textContent = SITE.email;
  });

  var knopf = document.querySelector(".menue-knopf");
  var menue = document.getElementById("menue");
  if (!knopf || !menue) return;

  var schmal = window.matchMedia("(max-width: 699px)");

  function istOffen() {
    return menue.classList.contains("ist-offen");
  }

  function setze(offen) {
    menue.classList.toggle("ist-offen", offen);
    knopf.setAttribute("aria-expanded", String(offen));
    knopf.textContent = offen ? "Schliessen" : "Menü";
    document.body.classList.toggle("menue-offen", offen);
    // Inhalt hinter dem offenen Menü für Tastatur und Screenreader sperren
    document.querySelectorAll("main, .fuss").forEach(function (teil) {
      teil.inert = offen;
    });
  }

  knopf.addEventListener("click", function () {
    setze(!istOffen());
  });

  menue.addEventListener("click", function (ereignis) {
    if (ereignis.target.closest("a")) setze(false);
  });

  document.addEventListener("keydown", function (ereignis) {
    if (!istOffen()) return;

    if (ereignis.key === "Escape") {
      setze(false);
      knopf.focus();
      return;
    }

    // Fokus bleibt im offenen Menü: Knopf und Menüpunkte im Kreis
    if (ereignis.key === "Tab") {
      var ziele = [knopf].concat(Array.prototype.slice.call(menue.querySelectorAll("a")));
      var erstes = ziele[0];
      var letztes = ziele[ziele.length - 1];
      if (ziele.indexOf(document.activeElement) === -1) {
        ereignis.preventDefault();
        erstes.focus();
      } else if (ereignis.shiftKey && document.activeElement === erstes) {
        ereignis.preventDefault();
        letztes.focus();
      } else if (!ereignis.shiftKey && document.activeElement === letztes) {
        ereignis.preventDefault();
        erstes.focus();
      }
    }
  });

  // Beim Wechsel auf die breite Ansicht das Overlay schliessen
  schmal.addEventListener("change", function (ereignis) {
    if (!ereignis.matches && istOffen()) setze(false);
  });
})();
