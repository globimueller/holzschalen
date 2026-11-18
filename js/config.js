/* Zentrale Angaben zur Seite.
   Basis-URL ändern: python3 scripts/basis-url-setzen.py https://www.neue-domain.ch/
   (das Skript passt diese Datei, die HTML-Seiten, sitemap.xml und robots.txt an) */
document.documentElement.classList.add("js");

window.SITE = {
  basisUrl: "https://globimueller.github.io/holzschalen/",
  name: "Laurin",
  email: "[EMAIL]"
};
