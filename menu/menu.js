// Menu QR multilingue Polyglotte : lit menu/restaurants/<slug>.json et l'affiche
// dans la langue du visiteur, avec filtres allergènes et régimes.
(function () {
  "use strict";

  var I18N = window.POLY_I18N;
  var LOCALES = { fr: "fr-FR", en: "en-GB", de: "de-DE", it: "it-IT", es: "es-ES", nl: "nl-NL" };
  var REGIMES = ["vegetarien", "vegan", "sans-gluten"];
  var CLE_STOCKAGE = "polyglotte-menu";

  var params = new URLSearchParams(location.search);
  var slug = (params.get("r") || "demo").toLowerCase();
  var menu = null;
  var langue = "fr";
  var filtres = { allergenes: [], regimes: [] };

  var $ = function (id) { return document.getElementById(id); };

  function lire() {
    try { return JSON.parse(localStorage.getItem(CLE_STOCKAGE)) || {}; } catch (e) { return {}; }
  }
  function ecrire(donnees) {
    try { localStorage.setItem(CLE_STOCKAGE, JSON.stringify(donnees)); } catch (e) { /* stockage indisponible */ }
  }

  function ui(cle) {
    return (I18N.ui[langue] && I18N.ui[langue][cle]) || I18N.ui.fr[cle] || cle;
  }

  // Renvoie le texte dans la langue courante, sinon le français, en signalant le repli.
  function tr(objet) {
    if (!objet) return { texte: "", repli: false };
    if (typeof objet === "string") return { texte: objet, repli: false };
    if (objet[langue]) return { texte: objet[langue], repli: false };
    var texte = objet.fr || Object.keys(objet).map(function (k) { return objet[k]; }).filter(Boolean)[0] || "";
    return { texte: texte, repli: langue !== "fr" && texte !== "" };
  }

  function el(tag, classe, texte) {
    var n = document.createElement(tag);
    if (classe) n.className = classe;
    if (texte != null) n.textContent = texte;
    return n;
  }

  function choisirLangue(disponibles) {
    var demandee = params.get("l");
    if (demandee && disponibles.indexOf(demandee) >= 0) return demandee;
    var memo = lire().langue;
    if (memo && disponibles.indexOf(memo) >= 0) return memo;
    var navigateur = navigator.languages || [navigator.language || "fr"];
    for (var i = 0; i < navigateur.length; i++) {
      var code = String(navigateur[i]).slice(0, 2).toLowerCase();
      if (disponibles.indexOf(code) >= 0) return code;
    }
    return disponibles[0] || "fr";
  }

  function formatPrix(prix) {
    if (typeof prix !== "number") return "";
    try {
      return new Intl.NumberFormat(LOCALES[langue] || "fr-FR", {
        style: "currency", currency: menu.devise || "EUR",
        minimumFractionDigits: prix % 1 === 0 ? 0 : 2
      }).format(prix);
    } catch (e) { return prix + " €"; }
  }

  function formatDate(iso) {
    var d = new Date(iso + "T12:00:00");
    if (isNaN(d)) return iso;
    return d.toLocaleDateString(LOCALES[langue] || "fr-FR", { day: "numeric", month: "long", year: "numeric" });
  }

  function platVisible(plat) {
    var allergenes = plat.allergenes || [];
    for (var i = 0; i < filtres.allergenes.length; i++) {
      if (allergenes.indexOf(filtres.allergenes[i]) >= 0) return false;
    }
    var tags = plat.tags || [];
    for (var j = 0; j < filtres.regimes.length; j++) {
      var r = filtres.regimes[j];
      var ok = tags.indexOf(r) >= 0 || (r === "vegetarien" && tags.indexOf("vegan") >= 0);
      if (!ok) return false;
    }
    return true;
  }

  function nbFiltres() { return filtres.allergenes.length + filtres.regimes.length; }

  // ---------- Rendu ----------

  function rendreEntete() {
    document.documentElement.lang = langue;
    document.title = menu.nom + " — " + ui("menu");
    $("nom").textContent = menu.nom;
    $("sous-titre").textContent = tr(menu.sousTitre).texte;
    $("lbl-langue").textContent = "Langue / Language";

    var select = $("langue");
    select.textContent = "";
    menu.langues.forEach(function (code) {
      var opt = el("option", null, I18N.langues[code] || code.toUpperCase());
      opt.value = code;
      opt.selected = code === langue;
      select.appendChild(opt);
    });

    var onglets = $("onglets");
    onglets.textContent = "";
    menu.sections.forEach(function (s) {
      var a = el("a", null, tr(s.titre).texte);
      a.href = "#s-" + s.id;
      onglets.appendChild(a);
    });
  }

  function rendreFiltres(conteneur) {
    var frag = $("tpl-filtres").content.cloneNode(true);
    frag.querySelectorAll("[data-t]").forEach(function (n) { n.textContent = ui(n.getAttribute("data-t")); });

    var presents = {};
    var tagsPresents = {};
    menu.sections.forEach(function (s) {
      s.plats.forEach(function (p) {
        (p.allergenes || []).forEach(function (a) { presents[a] = true; });
        (p.tags || []).forEach(function (t) { tagsPresents[t] = true; });
      });
    });
    if (tagsPresents.vegan) tagsPresents.vegetarien = true;

    var groupeA = frag.querySelector('[data-groupe="allergenes"]');
    Object.keys(I18N.allergenes).filter(function (a) { return presents[a]; }).forEach(function (a) {
      groupeA.appendChild(puce("allergenes", a, I18N.allergenes[a]));
    });
    var groupeR = frag.querySelector('[data-groupe="regimes"]');
    REGIMES.filter(function (r) { return tagsPresents[r]; }).forEach(function (r) {
      groupeR.appendChild(puce("regimes", r, I18N.tags[r]));
    });
    if (!groupeR.children.length) groupeR.closest("fieldset").remove();

    var details = frag.querySelector("details");
    if (nbFiltres()) details.open = true;
    var compteur = frag.querySelector(".compteur");
    if (nbFiltres()) { compteur.hidden = false; compteur.textContent = nbFiltres(); }

    frag.querySelector('[data-action="effacer"]').addEventListener("click", function () {
      filtres = { allergenes: [], regimes: [] };
      sauver();
      rendre();
    });
    conteneur.appendChild(frag);
  }

  function puce(groupe, id, libelles) {
    var label = el("label", "puce");
    var input = el("input");
    input.type = "checkbox";
    input.checked = filtres[groupe].indexOf(id) >= 0;
    input.addEventListener("change", function () {
      var liste = filtres[groupe];
      var i = liste.indexOf(id);
      if (input.checked && i < 0) liste.push(id);
      if (!input.checked && i >= 0) liste.splice(i, 1);
      sauver();
      rendreSections();
      var compteur = document.querySelector(".filtres .compteur");
      compteur.hidden = !nbFiltres();
      compteur.textContent = nbFiltres();
    });
    label.appendChild(input);
    label.appendChild(el("span", null, libelles[langue] || libelles.fr));
    return label;
  }

  function rendrePlat(plat) {
    var art = el("article", "plat" + (plat.dispo === false ? " indispo" : ""));
    var ligne = el("div", "plat-ligne");
    var nom = tr(plat.nom);
    var h = el("h3", "plat-nom", nom.texte);
    if (nom.repli) h.lang = "fr";
    ligne.appendChild(h);
    ligne.appendChild(el("span", "plat-pointilles"));
    ligne.appendChild(el("span", "plat-prix", formatPrix(plat.prix)));
    art.appendChild(ligne);

    if (plat.dispo === false) art.appendChild(el("p", "badge-indispo", ui("indispo")));

    var desc = tr(plat.description);
    if (desc.texte) {
      var p = el("p", "plat-desc", desc.texte);
      if (desc.repli) { p.lang = "fr"; p.title = ui("traduit"); }
      art.appendChild(p);
    }

    var tags = (plat.tags || []).filter(function (t) { return I18N.tags[t]; });
    if (tags.length) {
      var ul = el("ul", "tags");
      tags.forEach(function (t) { ul.appendChild(el("li", "tag tag-" + t, I18N.tags[t][langue] || I18N.tags[t].fr)); });
      art.appendChild(ul);
    }

    var allergenes = plat.allergenes;
    if (Array.isArray(allergenes)) {
      var pa = el("p", "allergenes");
      if (allergenes.length) {
        pa.appendChild(el("strong", null, ui("contient") + (langue === "fr" ? "\u00a0: " : ": ")));
        pa.appendChild(document.createTextNode(allergenes.map(function (a) {
          var l = I18N.allergenes[a];
          return l ? (l[langue] || l.fr) : a;
        }).join(", ")));
      } else {
        pa.textContent = ui("sansAllergene");
        pa.classList.add("aucun");
      }
      art.appendChild(pa);
    }
    return art;
  }

  function rendreSections() {
    var zone = $("sections");
    zone.textContent = "";
    var totalMasques = 0;

    menu.sections.forEach(function (s) {
      var section = el("section", "section");
      section.id = "s-" + s.id;
      section.appendChild(el("h2", "section-titre", tr(s.titre).texte));
      var masques = 0;
      s.plats.forEach(function (plat) {
        if (platVisible(plat)) section.appendChild(rendrePlat(plat));
        else masques++;
      });
      if (masques) {
        totalMasques += masques;
        section.appendChild(el("p", "masques", masques + " " + ui("masque")));
      }
      zone.appendChild(section);
    });

    if (totalMasques) {
      var b = el("button", "lien afficher-tout", ui("afficher"));
      b.type = "button";
      b.addEventListener("click", function () {
        filtres = { allergenes: [], regimes: [] };
        sauver();
        rendre();
      });
      zone.appendChild(b);
    }
    observerSections();
  }

  function rendrePied() {
    var pied = $("pied");
    pied.textContent = "";

    var note = el("section", "note-allergenes");
    note.appendChild(el("h2", null, ui("allergenesTitre")));
    note.appendChild(el("p", null, tr(menu.noteAllergenes).texte || ui("allergenesDefaut")));
    pied.appendChild(note);

    var infos = menu.infos || {};
    var dl = el("dl", "infos");
    function ajouter(cle, contenu) {
      if (!contenu) return;
      dl.appendChild(el("dt", null, ui(cle)));
      var dd = el("dd");
      if (typeof contenu === "string") dd.textContent = contenu; else dd.appendChild(contenu);
      dl.appendChild(dd);
    }
    ajouter("horaires", tr(infos.horaires).texte);
    ajouter("adresse", infos.adresse);
    if (infos.telephone) {
      var tel = el("a", null, infos.telephone);
      tel.href = "tel:" + infos.telephone.replace(/[^\d+]/g, "");
      ajouter("telephone", tel);
    }
    if (dl.children.length) {
      var bloc = el("section", "bloc-infos");
      bloc.appendChild(el("h2", null, ui("infos")));
      bloc.appendChild(dl);
      pied.appendChild(bloc);
    }

    if (infos.avisUrl && /^https:\/\//.test(infos.avisUrl)) {
      var avis = el("section", "bloc-avis");
      avis.appendChild(el("p", null, ui("avis")));
      var a = el("a", "bouton", ui("avisBtn"));
      a.href = infos.avisUrl;
      a.rel = "noopener";
      a.target = "_blank";
      avis.appendChild(a);
      pied.appendChild(avis);
    }

    var bas = el("p", "signature");
    if (menu.maj) bas.appendChild(document.createTextNode(ui("maj") + " " + formatDate(menu.maj) + " · "));
    var lien = el("a", null, ui("propulse"));
    lien.href = "../";
    bas.appendChild(lien);
    pied.appendChild(bas);
  }

  function rendre() {
    rendreEntete();
    var contenu = $("contenu");
    contenu.textContent = "";
    var msg = tr(menu.message).texte;
    if (msg) contenu.appendChild(el("p", "bienvenue", msg));
    rendreFiltres(contenu);
    var zone = el("div");
    zone.id = "sections";
    contenu.appendChild(zone);
    rendreSections();
    rendrePied();
  }

  // ---------- Navigation : onglet actif selon la section visible ----------

  var observateur = null;
  function observerSections() {
    if (!("IntersectionObserver" in window)) return;
    if (observateur) observateur.disconnect();
    var liens = document.querySelectorAll("#onglets a");
    observateur = new IntersectionObserver(function (entrees) {
      entrees.forEach(function (e) {
        if (!e.isIntersecting) return;
        liens.forEach(function (l) {
          var actif = l.getAttribute("href") === "#" + e.target.id;
          l.classList.toggle("actif", actif);
          if (actif) l.scrollIntoView({ block: "nearest", inline: "nearest" });
        });
      });
    }, { rootMargin: "-45% 0px -50% 0px" });
    document.querySelectorAll(".section").forEach(function (s) { observateur.observe(s); });
  }

  function sauver() {
    ecrire({ langue: langue, filtres: filtres });
  }

  function erreur() {
    var contenu = $("contenu");
    contenu.textContent = "";
    contenu.appendChild(el("p", "etat", ui("introuvable")));
    if (slug !== "demo") {
      var a = el("a", "bouton", ui("demo"));
      a.href = "?r=demo";
      contenu.appendChild(a);
    }
    $("nom").textContent = "Polyglotte";
  }

  $("langue").addEventListener("change", function (e) {
    langue = e.target.value;
    sauver();
    rendre();
  });

  if (!/^[a-z0-9-]{1,60}$/.test(slug)) { erreur(); return; }

  fetch("restaurants/" + slug + ".json", { cache: "no-cache" })
    .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(function (donnees) {
      menu = donnees;
      if (!Array.isArray(menu.langues) || !menu.langues.length) menu.langues = ["fr"];
      langue = choisirLangue(menu.langues);
      var memo = lire().filtres;
      if (memo && Array.isArray(memo.allergenes) && Array.isArray(memo.regimes)) filtres = memo;
      rendre();
      if (location.hash) {
        var cible = document.querySelector(location.hash);
        if (cible) cible.scrollIntoView();
      }
    })
    .catch(erreur);
})();
