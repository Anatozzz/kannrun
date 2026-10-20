/*
 * Polyglotte — outil d'audit terrain + mini-CRM de prospection.
 * Aucune dépendance. Données stockées uniquement dans le navigateur (localStorage).
 */
(function () {
  "use strict";

  // ------------------------------------------------------------------
  // Constantes
  // ------------------------------------------------------------------
  var CLE_PROSPECTS = "polyglotte.audit.prospects.v1";
  var CLE_BROUILLON = "polyglotte.audit.brouillon.v1";
  var CLE_FILTRE = "polyglotte.audit.filtre.v1";

  var STATUTS = ["À visiter", "Audit remis", "Démo", "Signé Pack", "Abonné", "Perdu"];
  var STATUTS_CLOS = ["Abonné", "Perdu"];
  var QUARTIERS = ["Vieille ville", "Bords du lac / Pâquier", "Centre / gare", "Annecy-le-Vieux",
    "Sévrier / rive ouest", "Talloires / rive est", "Autre"];
  var LANGUES = ["EN", "DE", "IT", "ES", "NL", "autre"];
  var PUBLIC_LANGUE = {
    EN: "anglophones", DE: "germanophones", IT: "italophones",
    ES: "hispanophones", NL: "néerlandophones"
  };
  var MENU_LIB = { aucun: "Aucun", fr: "FR seulement", "fr-en": "FR + EN", multi: "Multilingue" };
  var ALLERG_LIB = { non: "Non indiqués", partiel: "Partiellement", oui: "Indiqués" };
  var PRIX_ABONNEMENT = 59;

  // Barème (total 100). Affiché tel quel sur l'audit imprimé.
  var BAREME = {
    reponses: 30, etrangers: 20, menu: 20, allergenes: 15, fiche: 15
  };
  var POINTS_MENU = { aucun: 0, fr: 5, "fr-en": 12, multi: 20 };
  var POINTS_ALLERG = { non: 0, partiel: 7, oui: 15 };
  var POINTS_FICHE = { horaires: 4, photos: 4, lienMenu: 4, site: 3 };

  // Seule statistique citée (voir docs/recherche.md).
  var STAT_44 = "44 % de clientèle étrangère à Annecy à l'été 2025 (source : Sources du Lac, synthèse été 2025).";
  var MENTION_ALLERGENES = "Information obligatoire sur les 14 allergènes, y compris en restauration : " +
    "règlement (UE) n° 1169/2011 « INCO » (art. 44, annexe II) et décret n° 2015-447 du 17 avril 2015.";

  // ------------------------------------------------------------------
  // Stockage (try/catch partout)
  // ------------------------------------------------------------------
  var stockageOk = (function () {
    try {
      var k = "__polyglotte_test__";
      window.localStorage.setItem(k, "1");
      window.localStorage.removeItem(k);
      return true;
    } catch (e) { return false; }
  })();
  var memoire = {}; // repli si localStorage indisponible

  function lire(cle, defaut) {
    try {
      var brut = stockageOk ? window.localStorage.getItem(cle) : memoire[cle];
      if (brut == null) return defaut;
      return JSON.parse(brut);
    } catch (e) { return defaut; }
  }
  function ecrire(cle, valeur) {
    var brut;
    try { brut = JSON.stringify(valeur); } catch (e) { return false; }
    memoire[cle] = brut;
    if (!stockageOk) return false;
    try { window.localStorage.setItem(cle, brut); return true; } catch (e) { return false; }
  }
  function supprimer(cle) {
    delete memoire[cle];
    try { if (stockageOk) window.localStorage.removeItem(cle); } catch (e) { /* rien */ }
  }

  function chargerProspects() {
    var l = lire(CLE_PROSPECTS, []);
    return Array.isArray(l) ? l.filter(function (p) { return p && typeof p === "object" && p.id; }) : [];
  }
  function sauverProspects(liste) { return ecrire(CLE_PROSPECTS, liste); }

  // ------------------------------------------------------------------
  // Utilitaires
  // ------------------------------------------------------------------
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function entier(v) {
    if (v === "" || v == null) return null;
    var n = Number(String(v).replace(",", "."));
    if (!isFinite(n)) return null;
    return Math.max(0, Math.round(n));
  }
  function decimal(v) {
    if (v === "" || v == null) return null;
    var n = Number(String(v).trim().replace(",", "."));
    return isFinite(n) ? n : null;
  }
  function aujourdhui() {
    var d = new Date();
    return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate());
  }
  function pad(n) { return (n < 10 ? "0" : "") + n; }
  function dateFr(iso) {
    if (!iso || !/^\d{4}-\d{2}-\d{2}/.test(iso)) return "";
    var p = iso.slice(0, 10).split("-");
    return p[2] + "/" + p[1] + "/" + p[0];
  }
  function dateLongue(iso) {
    var mois = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
      "septembre", "octobre", "novembre", "décembre"];
    if (!iso || !/^\d{4}-\d{2}-\d{2}/.test(iso)) return "";
    var p = iso.slice(0, 10).split("-");
    return Number(p[2]) + (p[2] === "01" ? "er" : "") + " " + mois[Number(p[1]) - 1] + " " + p[0];
  }
  function nouvelId() {
    return "p-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 7);
  }
  function pluriel(n, sing, plur) { return n > 1 ? plur : sing; }
  function nombreFr(n, dec) {
    return Number(n).toLocaleString("fr-FR", { maximumFractionDigits: dec || 0, minimumFractionDigits: dec || 0 });
  }
  function listeFr(arr) {
    if (arr.length <= 1) return arr.join("");
    return arr.slice(0, -1).join(", ") + " et " + arr[arr.length - 1];
  }

  // ------------------------------------------------------------------
  // Modèle et calcul du score
  // ------------------------------------------------------------------
  function prospectVide() {
    return {
      id: "", nom: "", quartier: QUARTIERS[0], note: "", totalAvis: "",
      sansReponse: "", etrangers: "", etrangersSansReponse: "", langues: [],
      menu: "aucun", allergenes: "non",
      horaires: false, photos: false, lienMenu: false, site: false,
      statut: STATUTS[0], relance: "", notes: "", creeLe: "", majLe: "", score: 0
    };
  }

  /** Normalise un prospect (données importées ou saisies). */
  function normaliser(p) {
    var v = prospectVide();
    p = p || {};
    Object.keys(v).forEach(function (k) { if (p[k] !== undefined && p[k] !== null) v[k] = p[k]; });
    v.nom = String(v.nom).trim().slice(0, 80);
    if (QUARTIERS.indexOf(v.quartier) < 0) v.quartier = "Autre";
    if (!Array.isArray(v.langues)) v.langues = String(v.langues || "").split(/[|,\s]+/);
    v.langues = LANGUES.filter(function (l) {
      return v.langues.map(function (x) { return String(x).trim().toLowerCase(); }).indexOf(l.toLowerCase()) >= 0;
    });
    if (!MENU_LIB[v.menu]) v.menu = "aucun";
    if (!ALLERG_LIB[v.allergenes]) v.allergenes = "non";
    ["horaires", "photos", "lienMenu", "site"].forEach(function (k) { v[k] = booleen(v[k]); });
    if (STATUTS.indexOf(v.statut) < 0) v.statut = STATUTS[0];
    if (v.relance && !/^\d{4}-\d{2}-\d{2}$/.test(v.relance)) v.relance = "";
    v.notes = String(v.notes || "").slice(0, 2000);
    return v;
  }
  function booleen(x) {
    if (typeof x === "boolean") return x;
    var s = String(x || "").trim().toLowerCase();
    return s === "oui" || s === "true" || s === "1" || s === "on" || s === "x";
  }

  /**
   * Calcule le score et les chiffres de l'audit.
   * Échantillon = 30 derniers avis, ou le total s'il est inférieur.
   */
  function calculer(p) {
    var total = entier(p.totalAvis);
    var ech = total != null && total > 0 ? Math.min(30, total) : 30;
    var sr = Math.min(entier(p.sansReponse) || 0, ech);
    var etr = Math.min(entier(p.etrangers) || 0, ech);
    var etrSr = Math.min(entier(p.etrangersSansReponse) || 0, etr, sr || etr);
    var aucunAvis = total === 0;

    var ptsRep = aucunAvis ? 0 : Math.round(BAREME.reponses * (ech - sr) / ech);
    var ptsEtr = aucunAvis ? 0 : (etr === 0 ? BAREME.etrangers : Math.round(BAREME.etrangers * (etr - etrSr) / etr));
    var ptsMenu = POINTS_MENU[p.menu] || 0;
    var ptsAll = POINTS_ALLERG[p.allergenes] || 0;
    var ptsFiche = 0;
    Object.keys(POINTS_FICHE).forEach(function (k) { if (p[k]) ptsFiche += POINTS_FICHE[k]; });

    var details = [
      { id: "reponses", titre: "Réponses aux avis", pts: ptsRep, max: BAREME.reponses,
        regle: "30 × part des " + ech + " derniers avis ayant une réponse" },
      { id: "etrangers", titre: "Avis en langue étrangère", pts: ptsEtr, max: BAREME.etrangers,
        regle: "20 × part des avis étrangers ayant une réponse (20 si aucun)" },
      { id: "menu", titre: "Menu en ligne", pts: ptsMenu, max: BAREME.menu,
        regle: "aucun 0 · FR 5 · FR+EN 12 · multilingue 20" },
      { id: "allergenes", titre: "Allergènes", pts: ptsAll, max: BAREME.allergenes,
        regle: "non 0 · partiellement 7 · oui 15" },
      { id: "fiche", titre: "Fiche Google", pts: ptsFiche, max: BAREME.fiche,
        regle: "horaires 4 · photos récentes 4 · lien menu 4 · site 3" }
    ];
    var score = details.reduce(function (s, d) { return s + d.pts; }, 0);

    return {
      score: score, details: details, echantillon: ech, sansReponse: sr,
      etrangers: etr, etrangersSansReponse: etrSr, total: total, aucunAvis: aucunAvis,
      tauxReponse: aucunAvis ? null : Math.round(100 * (ech - sr) / ech),
      priorites: priorites(p, { ech: ech, sr: sr, etr: etr, etrSr: etrSr, aucunAvis: aucunAvis, details: details })
    };
  }

  function publicLangues(langues) {
    var pub = (langues || []).filter(function (l) { return PUBLIC_LANGUE[l]; })
      .map(function (l) { return PUBLIC_LANGUE[l]; });
    return pub.length ? listeFr(pub) : "étrangers";
  }
  function perdu(details, id) {
    var d = details.filter(function (x) { return x.id === id; })[0];
    return d ? d.max - d.pts : 0;
  }

  /** Règles des 3 priorités : chaque règle a un poids = points perdus (+ bonus métier). */
  function priorites(p, c) {
    var r = [];
    var pub = publicLangues(p.langues);

    if (c.aucunAvis) {
      r.push({ poids: 40,
        titre: "Aucun avis Google pour l'instant : les premiers avis comptent beaucoup pour être choisi.",
        action: "Nous préparons un carton QR « Laissez-nous un avis » et répondons à chacun." });
    }
    if (c.etrSr > 0) {
      r.push({ poids: perdu(c.details, "etrangers") + 8,
        titre: c.etrSr + " " + pluriel(c.etrSr, "avis", "avis") + " en langue étrangère sans réponse : vos futurs clients " +
          pub + " les lisent avant de réserver.",
        action: "Nous rédigeons chaque réponse dans la langue du client ; vous validez avant publication." });
    }
    var srFr = c.sr - c.etrSr;
    if (c.sr > 0 && (srFr > 0 || c.etrSr === 0)) {
      r.push({ poids: perdu(c.details, "reponses"),
        titre: c.sr + " des " + c.ech + " derniers avis " + pluriel(c.sr, "est resté", "sont restés") +
          " sans réponse : une réponse courte et personnalisée montre aux prochains clients que vous êtes à l'écoute.",
        action: "Réponses rédigées pour vous chaque semaine, signées à votre nom." });
    }
    if (p.menu !== "multi") {
      var t = {
        aucun: "Aucun menu consultable en ligne : les visiteurs ne peuvent pas découvrir votre carte avant de venir.",
        fr: "Menu en français uniquement : les visiteurs " + pub + " ne peuvent pas choisir leurs plats avant de venir.",
        "fr-en": "Menu en français et en anglais : il manque l'allemand, l'italien et l'espagnol."
      }[p.menu];
      r.push({ poids: perdu(c.details, "menu"), titre: t,
        action: "Menu QR en 5 langues (FR, EN, DE, IT, ES), spécialités savoyardes gardées sous leur nom." });
    }
    if (p.allergenes !== "oui") {
      r.push({ poids: perdu(c.details, "allergenes") + 4,
        titre: p.allergenes === "non"
          ? "Allergènes non indiqués : l'information sur les 14 allergènes réglementaires est obligatoire."
          : "Allergènes indiqués en partie : l'information doit couvrir les 14 allergènes réglementaires.",
        action: "Chaque plat affiche ses allergènes, traduits, exactement tels que vous les déclarez." });
    }
    var manque = [];
    if (!p.horaires) manque.push("horaires à vérifier");
    if (!p.photos) manque.push("photos de plus de 6 mois");
    if (!p.lienMenu) manque.push("pas de lien vers le menu");
    if (!p.site) manque.push("pas de site web");
    if (manque.length) {
      r.push({ poids: perdu(c.details, "fiche"),
        titre: "Fiche Google à compléter : " + listeFr(manque) + ".",
        action: "Mise à jour de la fiche incluse dans le Pack Démarrage." });
    }

    r.sort(function (a, b) { return b.poids - a.poids; });
    r = r.filter(function (x) { return x.poids > 0; }).slice(0, 3);

    var complements = [
      { titre: "Votre présence en ligne est solide : l'enjeu est de garder ce rythme toute la saison.",
        action: "Nous prenons le relais des réponses quand le service vous laisse moins de temps." },
      { titre: "Pensez à mettre à jour photos et menu à chaque changement de carte.",
        action: "Mises à jour du menu QR incluses dans l'abonnement." },
      { titre: "Un carton QR en salle peut inviter les clients satisfaits à laisser un avis.",
        action: "Carton fourni avec le Pack Démarrage." }
    ];
    var i = 0;
    while (r.length < 3 && i < complements.length) { r.push(complements[i]); i++; }
    return r;
  }

  function niveau(score) {
    if (score >= 80) return "Très bonne base";
    if (score >= 60) return "Bonne base, à consolider";
    if (score >= 40) return "Marge de progrès nette";
    return "Fort potentiel de progrès";
  }

  // ------------------------------------------------------------------
  // Configuration contact (../assets/js/config.js, facultatif)
  // ------------------------------------------------------------------
  function config() {
    var c = window.POLYGLOTTE;
    if (!c || typeof c !== "object") return {};
    var out = {};
    ["email", "telephone", "whatsapp", "lienRdv", "nomResponsable", "adresse", "site"].forEach(function (k) {
      if (typeof c[k] === "string" && c[k].trim()) out[k] = c[k].trim();
    });
    return out;
  }
  function blocContact() {
    var c = config();
    var lignes = [];
    if (c.nomResponsable) lignes.push("<strong>" + esc(c.nomResponsable) + "</strong>");
    if (c.telephone) lignes.push("Tél. " + esc(c.telephone));
    if (c.whatsapp && !c.telephone) lignes.push("WhatsApp +" + esc(c.whatsapp.replace(/\D/g, "")));
    if (c.email) lignes.push(esc(c.email));
    if (c.lienRdv) lignes.push("RDV : " + esc(c.lienRdv.replace(/^https?:\/\//, "")));
    if (!c.telephone && !c.email && !c.whatsapp) {
      return { vide: true, html:
        '<span class="f-ligne-main">Votre interlocuteur :</span><span class="f-ligne-main">Tél. :</span>' };
    }
    return { vide: false, html: lignes.map(function (l) { return "<span>" + l + "</span>"; }).join("") };
  }

  // ------------------------------------------------------------------
  // Rendu de la feuille A4
  // ------------------------------------------------------------------
  function rendreFeuille(p, c) {
    var el = document.getElementById("feuille");
    var date = (p.creeLe || aujourdhui()).slice(0, 10);
    var nom = p.nom || "Votre restaurant";
    var note = decimal(p.note);
    var langues = (p.langues || []).map(function (l) { return l === "autre" ? "autres" : l; });
    var contact = blocContact();
    var angle = Math.round(3.6 * c.score);

    var faits = [
      { k: "Note Google", v: note != null ? nombreFr(note, 1) + "<small>/5</small>" : "–",
        s: c.total != null ? nombreFr(c.total) + " " + pluriel(c.total, "avis", "avis") : "" },
      { k: "Avis avec réponse", v: c.tauxReponse != null ? c.tauxReponse + "<small> %</small>" : "–",
        s: "sur les " + c.echantillon + " derniers" },
      { k: "Avis en langue étrangère", v: String(c.etrangers),
        s: c.etrangers ? c.etrangersSansReponse + " sans réponse" : "dans l'échantillon" },
      { k: "Langues vues", v: langues.length ? esc(langues.join(" · ")) : "–", s: "", petit: true },
      { k: "Menu en ligne", v: esc(MENU_LIB[p.menu]), s: "", petit: true },
      { k: "Allergènes", v: esc(ALLERG_LIB[p.allergenes]), s: "", petit: true }
    ];

    el.innerHTML =
      '<header class="f-tete">' +
        '<div><p class="f-marque">Polyglotte</p>' +
        '<p class="f-baseline">Avis, menus et fiche Google dans la langue de vos clients · Annecy</p></div>' +
        '<p class="f-date">Audit offert<br><span>' + esc(dateLongue(date)) + "</span></p>" +
      "</header>" +

      '<section class="f-titre">' +
        '<p class="f-surtitre">Audit de présence en ligne</p>' +
        "<h2 class=\"f-nom\">" + esc(nom) + "</h2>" +
        '<p class="f-lieu">' + esc(p.quartier) + (p.quartier === "Autre" ? "" : " · Annecy") + "</p>" +
      "</section>" +

      '<section class="f-synthese">' +
        '<div class="f-score" style="--angle:' + angle + 'deg" role="img" aria-label="Score Polyglotte ' + c.score + ' sur 100">' +
          '<div class="f-score__anneau"><p class="f-score__val">' + c.score + "<small>/100</small></p></div>" +
          '<p class="f-score__lib">Score Polyglotte</p>' +
          '<p class="f-score__niv">' + esc(niveau(c.score)) + "</p>" +
        "</div>" +
        '<dl class="f-faits">' + faits.map(function (f) {
          return '<div class="f-fait' + (f.petit ? " f-fait--texte" : "") + '"><dt>' + esc(f.k) + "</dt><dd>" + f.v +
            (f.s ? "<span>" + esc(f.s) + "</span>" : "") + "</dd></div>";
        }).join("") + "</dl>" +
      "</section>" +

      '<section class="f-prio">' +
        '<h3 class="f-h3">Vos 3 priorités</h3>' +
        "<ol>" + c.priorites.map(function (x) {
          return "<li><p class=\"f-prio__titre\">" + esc(x.titre) + "</p><p class=\"f-prio__action\">" + esc(x.action) + "</p></li>";
        }).join("") + "</ol>" +
        '<p class="f-stat">' + esc(STAT_44) + "</p>" +
      "</section>" +

      '<section class="f-offre">' +
        '<div class="f-offre__pack">' +
          '<p class="f-offre__nom">Pack Démarrage</p>' +
          '<p class="f-offre__prix"><s>290 €</s> <strong>145 €</strong></p>' +
          '<p class="f-offre__fond">Offre fondateurs : −50 % pour les 10 premiers restaurants</p>' +
          '<p class="f-offre__desc">Menu QR en 5 langues avec les 14 allergènes, fiche Google optimisée, mise en route des réponses aux avis.</p>' +
        "</div>" +
        '<div class="f-offre__abo">' +
          '<p class="f-offre__nom">Puis abonnement</p>' +
          '<p class="f-offre__prix"><strong>59 €</strong><small>/mois</small></p>' +
          '<p class="f-offre__desc">Réponses aux avis dans la langue du client, validées par vous. Mises à jour du menu.</p>' +
        "</div>" +
        '<div class="f-offre__contact' + (contact.vide ? " f-offre__contact--vide" : "") + '">' +
          '<p class="f-offre__nom">Contact</p>' + contact.html +
        "</div>" +
      "</section>" +

      '<footer class="f-pied">' +
        '<div class="f-bareme"><p class="f-bareme__titre">Barème du score (sur 100)</p><ul>' +
          c.details.map(function (d) {
            return "<li><span>" + esc(d.titre) + " <b>" + d.pts + "/" + d.max + "</b></span><em>" + esc(d.regle) + "</em></li>";
          }).join("") +
        "</ul></div>" +
        '<p class="f-legal">' + esc(MENTION_ALLERGENES) + "</p>" +
        '<p class="f-legal">Audit établi le ' + esc(dateFr(date)) +
          " à partir des informations publiques de la fiche Google de l'établissement (30 derniers avis examinés à la main). " +
          "Note Google indiquée pour information, non comptée dans le score.</p>" +
      "</footer>";

    var live = document.getElementById("score-live");
    if (live) live.textContent = c.score;
  }

  // ------------------------------------------------------------------
  // Formulaire
  // ------------------------------------------------------------------
  var form, courant = prospectVide();

  function lireFormulaire() {
    var f = form.elements;
    var p = normaliser({
      id: f.id.value, nom: f.nom.value, quartier: f.quartier.value, note: f.note.value.trim(),
      totalAvis: f.totalAvis.value, sansReponse: f.sansReponse.value, etrangers: f.etrangers.value,
      etrangersSansReponse: f.etrangersSansReponse.value,
      langues: Array.prototype.filter.call(form.querySelectorAll('input[name="langues"]'), function (i) { return i.checked; })
        .map(function (i) { return i.value; }),
      menu: (form.querySelector('input[name="menu"]:checked') || {}).value,
      allergenes: (form.querySelector('input[name="allergenes"]:checked') || {}).value,
      horaires: f.horaires.checked, photos: f.photos.checked, lienMenu: f.lienMenu.checked, site: f.site.checked,
      statut: f.statut.value, relance: f.relance.value, notes: f.notes.value
    });
    p.creeLe = courant.creeLe || "";
    p.majLe = courant.majLe || "";
    return p;
  }

  function remplirFormulaire(p) {
    p = normaliser(p);
    courant = p;
    var f = form.elements;
    f.id.value = p.id; f.nom.value = p.nom; f.quartier.value = p.quartier;
    f.note.value = p.note === "" || p.note == null ? "" : String(p.note).replace(".", ",");
    f.totalAvis.value = p.totalAvis; f.sansReponse.value = p.sansReponse;
    f.etrangers.value = p.etrangers; f.etrangersSansReponse.value = p.etrangersSansReponse;
    form.querySelectorAll('input[name="langues"]').forEach(function (i) { i.checked = p.langues.indexOf(i.value) >= 0; });
    form.querySelectorAll('input[name="menu"]').forEach(function (i) { i.checked = i.value === p.menu; });
    form.querySelectorAll('input[name="allergenes"]').forEach(function (i) { i.checked = i.value === p.allergenes; });
    f.horaires.checked = p.horaires; f.photos.checked = p.photos; f.lienMenu.checked = p.lienMenu; f.site.checked = p.site;
    f.statut.value = p.statut; f.relance.value = p.relance; f.notes.value = p.notes;
    document.getElementById("titre-audit").textContent = p.id ? "Modifier l'audit" : "Nouvel audit";
    rafraichir(false);
  }

  /** Valide et renvoie la liste des erreurs { champ, message }. */
  function valider(p) {
    var e = [];
    var note = decimal(p.note);
    var total = entier(p.totalAvis);
    var ech = total != null && total > 0 ? Math.min(30, total) : 30;
    var sr = entier(p.sansReponse), etr = entier(p.etrangers), etrSr = entier(p.etrangersSansReponse);
    if (!p.nom) e.push({ champ: "nom", id: "err-nom", msg: "Indiquez le nom du restaurant." });
    if (p.note !== "" && (note == null || note < 1 || note > 5)) e.push({ champ: "note", id: "err-note", msg: "Note entre 1 et 5." });
    if (p.totalAvis !== "" && (Number(p.totalAvis) < 0 || !/^\d+$/.test(String(p.totalAvis)))) e.push({ champ: "totalAvis", id: "err-total", msg: "Nombre entier positif." });
    if (sr != null && sr > ech) e.push({ champ: "sansReponse", id: "err-sansrep", msg: "Maximum " + ech + "." });
    if (etr != null && etr > ech) e.push({ champ: "etrangers", id: "err-etr", msg: "Maximum " + ech + "." });
    if (etrSr != null && etrSr > (etr || 0)) e.push({ champ: "etrangersSansReponse", id: "err-etrsr", msg: "Pas plus que les avis étrangers." });
    else if (etrSr != null && sr != null && etrSr > sr) e.push({ champ: "etrangersSansReponse", id: "err-etrsr", msg: "Pas plus que le total sans réponse." });
    return e;
  }

  function afficherErreurs(erreurs, toutes) {
    ["nom", "note", "totalAvis", "sansReponse", "etrangers", "etrangersSansReponse"].forEach(function (n) {
      var champ = form.elements[n];
      var err = erreurs.filter(function (x) { return x.champ === n; })[0];
      var montrer = err && (toutes || n !== "nom");
      champ.setAttribute("aria-invalid", montrer ? "true" : "false");
      var zone = document.getElementById(champ.getAttribute("aria-describedby").split(" ").pop());
      if (zone) zone.textContent = montrer ? err.msg : "";
    });
  }

  var minuterie = null;
  function rafraichir(sauverBrouillon) {
    var p = lireFormulaire();
    afficherErreurs(valider(p), false);
    var c = calculer(p);
    rendreFeuille(p, c);
    ajusterApercu();
    if (sauverBrouillon !== false) {
      clearTimeout(minuterie);
      minuterie = setTimeout(function () { ecrire(CLE_BROUILLON, p); }, 300);
    }
    return { p: p, c: c };
  }

  function message(id, texte) {
    var el = document.getElementById(id);
    if (!el) return;
    el.textContent = texte;
    clearTimeout(el._t);
    el._t = setTimeout(function () { el.textContent = ""; }, 5000);
  }

  function enregistrer() {
    var p = lireFormulaire();
    var erreurs = valider(p);
    afficherErreurs(erreurs, true);
    if (erreurs.length) {
      var premier = form.elements[erreurs[0].champ];
      if (premier) premier.focus();
      message("message-action", "Corrigez les champs signalés avant d'enregistrer.");
      return null;
    }
    var liste = chargerProspects();
    var maintenant = new Date().toISOString();
    if (!p.id) { p.id = nouvelId(); p.creeLe = maintenant; }
    p.creeLe = p.creeLe || maintenant;
    p.majLe = maintenant;
    p.score = calculer(p).score;
    var idx = -1;
    liste.forEach(function (x, i) { if (x.id === p.id) idx = i; });
    if (idx >= 0) liste[idx] = p; else liste.unshift(p);
    var ok = sauverProspects(liste);
    courant = p;
    form.elements.id.value = p.id;
    document.getElementById("titre-audit").textContent = "Modifier l'audit";
    supprimer(CLE_BROUILLON);
    rendrePipeline();
    message("message-action", ok ? "« " + p.nom + " » enregistré dans le pipeline." :
      "Enregistré pour cette session seulement (stockage indisponible) : pensez à exporter en CSV.");
    return p;
  }

  function imprimer() {
    rafraichir(false);
    var go = function () { try { window.print(); } catch (e) { /* rien */ } };
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(go, go); else go();
  }

  // Mise à l'échelle de l'aperçu A4 dans son cadre
  function ajusterApercu() {
    var cadre = document.getElementById("apercu-cadre");
    var feuille = document.getElementById("feuille");
    if (!cadre || !feuille) return;
    var largeur = cadre.clientWidth;
    var base = feuille.offsetWidth || 794;
    var echelle = Math.min(1, largeur / base);
    feuille.style.transform = "scale(" + echelle + ")";
    cadre.style.height = Math.ceil(feuille.offsetHeight * echelle) + "px";
  }

  // ------------------------------------------------------------------
  // Pipeline
  // ------------------------------------------------------------------
  var filtre = lire(CLE_FILTRE, "tous");

  function stats(liste) {
    var visites = liste.filter(function (p) { return p.statut !== "À visiter"; }).length;
    var signes = liste.filter(function (p) { return p.statut === "Signé Pack" || p.statut === "Abonné"; }).length;
    var abonnes = liste.filter(function (p) { return p.statut === "Abonné"; }).length;
    return {
      visites: visites, signes: signes, abonnes: abonnes,
      conversion: visites ? Math.round(1000 * signes / visites) / 10 : null,
      mrr: abonnes * PRIX_ABONNEMENT
    };
  }
  function aRelancer(p) {
    return p.relance && p.relance <= aujourdhui() && STATUTS_CLOS.indexOf(p.statut) < 0;
  }

  function rendreFiltres(liste) {
    var zone = document.getElementById("filtres");
    var options = [{ v: "tous", lib: "Tous", n: liste.length },
      { v: "relancer", lib: "À relancer", n: liste.filter(aRelancer).length }]
      .concat(STATUTS.map(function (s) {
        return { v: s, lib: s, n: liste.filter(function (p) { return p.statut === s; }).length };
      }));
    zone.innerHTML = options.map(function (o) {
      return '<button type="button" class="filtre" data-filtre="' + esc(o.v) + '" aria-pressed="' + (filtre === o.v) + '">' +
        esc(o.lib) + ' <span class="filtre__n">' + o.n + "</span></button>";
    }).join("");
  }

  function rendrePipeline() {
    var liste = chargerProspects().map(normaliserStocke);
    var s = stats(liste);
    document.getElementById("c-visites").textContent = s.visites;
    document.getElementById("c-signes").textContent = s.signes;
    document.getElementById("c-conversion").textContent = s.conversion == null ? "–" : nombreFr(s.conversion, s.conversion % 1 ? 1 : 0) + " %";
    document.getElementById("c-mrr").textContent = nombreFr(s.mrr) + " €";
    document.getElementById("compte-pipeline").textContent = liste.length;
    rendreFiltres(liste);

    var visibles = liste.filter(function (p) {
      if (filtre === "tous") return true;
      if (filtre === "relancer") return aRelancer(p);
      return p.statut === filtre;
    }).sort(function (a, b) {
      var ra = a.relance || "9999", rb = b.relance || "9999";
      if (ra !== rb) return ra < rb ? -1 : 1;
      return (b.majLe || "").localeCompare(a.majLe || "");
    });

    var zone = document.getElementById("liste-prospects");
    document.getElementById("liste-vide").hidden = visibles.length > 0;
    if (!visibles.length) { zone.innerHTML = ""; return; }

    zone.innerHTML =
      '<table class="table"><caption class="visually-hidden">Prospects</caption><thead><tr>' +
      '<th scope="col">Restaurant</th><th scope="col">Score</th><th scope="col">Statut</th>' +
      '<th scope="col">Relance</th><th scope="col"><span class="visually-hidden">Actions</span></th></tr></thead><tbody>' +
      visibles.map(function (p) {
        var retard = aRelancer(p);
        return '<tr data-id="' + esc(p.id) + '">' +
          '<th scope="row" data-label="Restaurant"><span class="t-nom">' + esc(p.nom) + '</span><span class="t-sous">' + esc(p.quartier) +
            (p.note !== "" ? " · " + esc(String(p.note).replace(".", ",")) + "/5" : "") + "</span></th>" +
          '<td data-label="Score"><span class="t-score" style="--s:' + p.score + '">' + p.score + "</span></td>" +
          '<td data-label="Statut"><label class="visually-hidden" for="st-' + esc(p.id) + '">Statut de ' + esc(p.nom) + "</label>" +
            '<select id="st-' + esc(p.id) + '" class="t-statut" data-action="statut">' +
            STATUTS.map(function (st) { return "<option" + (st === p.statut ? " selected" : "") + ">" + esc(st) + "</option>"; }).join("") +
            "</select></td>" +
          '<td data-label="Relance"><label class="visually-hidden" for="rl-' + esc(p.id) + '">Date de relance de ' + esc(p.nom) + "</label>" +
            '<input id="rl-' + esc(p.id) + '" type="date" class="t-relance' + (retard ? " t-relance--retard" : "") + '" data-action="relance" value="' + esc(p.relance) + '">' +
            (retard ? '<span class="t-badge">à relancer</span>' : "") + "</td>" +
          '<td class="t-actions"><button type="button" class="btn btn--petit" data-action="ouvrir">Ouvrir</button>' +
            '<button type="button" class="btn btn--petit btn--danger" data-action="supprimer" aria-label="Supprimer ' + esc(p.nom) + '">Supprimer</button></td>' +
          "</tr>";
      }).join("") + "</tbody></table>";
  }
  function normaliserStocke(p) {
    var n = normaliser(p);
    n.id = p.id; n.creeLe = p.creeLe || ""; n.majLe = p.majLe || "";
    n.score = calculer(n).score;
    return n;
  }

  function majProspect(id, champs) {
    var liste = chargerProspects();
    liste.forEach(function (p) {
      if (p.id === id) {
        Object.keys(champs).forEach(function (k) { p[k] = champs[k]; });
        p.majLe = new Date().toISOString();
      }
    });
    sauverProspects(liste);
    if (courant.id === id) {
      Object.keys(champs).forEach(function (k) { if (form.elements[k]) form.elements[k].value = champs[k]; });
      courant = Object.assign({}, courant, champs);
    }
  }

  // ------------------------------------------------------------------
  // CSV (séparateur « ; », UTF-8 avec BOM pour Excel)
  // ------------------------------------------------------------------
  var COLONNES = ["id", "nom", "quartier", "note", "totalAvis", "sansReponse", "etrangers", "etrangersSansReponse",
    "langues", "menu", "allergenes", "horaires", "photos", "lienMenu", "site", "statut", "relance", "score",
    "notes", "creeLe", "majLe"];

  function csvCellule(v) {
    var s = v == null ? "" : String(v);
    if (/^[=+\-@]/.test(s) && !/^-?\d/.test(s)) s = "'" + s; // évite l'injection de formules
    return /[";\n\r]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
  }
  function versCsv(liste) {
    var lignes = [COLONNES.join(";")];
    liste.forEach(function (p) {
      lignes.push(COLONNES.map(function (k) {
        var v = p[k];
        if (k === "langues") v = (p.langues || []).join("|");
        else if (typeof v === "boolean") v = v ? "oui" : "non";
        else if (k === "note" && v !== "" && v != null) v = String(v).replace(".", ",");
        return csvCellule(v);
      }).join(";"));
    });
    return "﻿" + lignes.join("\r\n") + "\r\n";
  }
  function analyserCsv(texte) {
    texte = String(texte || "").replace(/^﻿/, "");
    var premiere = texte.split(/\r?\n/)[0] || "";
    var sep = (premiere.split(";").length >= premiere.split(",").length) ? ";" : ",";
    var lignes = [], ligne = [], cell = "", guill = false;
    for (var i = 0; i < texte.length; i++) {
      var ch = texte[i];
      if (guill) {
        if (ch === '"') { if (texte[i + 1] === '"') { cell += '"'; i++; } else guill = false; }
        else cell += ch;
      } else if (ch === '"') guill = true;
      else if (ch === sep) { ligne.push(cell); cell = ""; }
      else if (ch === "\n" || ch === "\r") {
        if (ch === "\r" && texte[i + 1] === "\n") i++;
        ligne.push(cell); cell = "";
        if (ligne.some(function (x) { return x !== ""; })) lignes.push(ligne);
        ligne = [];
      } else cell += ch;
    }
    ligne.push(cell);
    if (ligne.some(function (x) { return x !== ""; })) lignes.push(ligne);
    return lignes;
  }
  function depuisCsv(texte) {
    var lignes = analyserCsv(texte);
    if (!lignes.length) throw new Error("Fichier vide.");
    var tete = lignes[0].map(function (h) { return h.trim(); });
    if (tete.indexOf("nom") < 0) throw new Error("Colonne « nom » introuvable : utilisez un fichier exporté par cet outil.");
    var res = [], ignores = 0;
    lignes.slice(1).forEach(function (l) {
      var o = {};
      tete.forEach(function (h, i) {
        var v = l[i] == null ? "" : l[i];
        if (/^'[=+\-@]/.test(v)) v = v.slice(1);
        o[h] = v;
      });
      if (!String(o.nom || "").trim()) { ignores++; return; }
      var p = normaliser(o);
      p.id = String(o.id || "").trim() || nouvelId();
      p.creeLe = o.creeLe || new Date().toISOString();
      p.majLe = o.majLe || p.creeLe;
      if (p.note !== "" && decimal(p.note) == null) p.note = "";
      p.score = calculer(p).score;
      res.push(p);
    });
    return { prospects: res, ignores: ignores };
  }

  function exporter() {
    var liste = chargerProspects();
    if (!liste.length) { message("message-pipeline", "Rien à exporter pour l'instant."); return; }
    var blob = new Blob([versCsv(liste)], { type: "text/csv;charset=utf-8" });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url; a.download = "polyglotte-prospects-" + aujourdhui() + ".csv";
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    message("message-pipeline", liste.length + " prospect(s) exporté(s).");
  }
  function importer(fichier) {
    var lecteur = new FileReader();
    lecteur.onload = function () {
      try {
        var r = depuisCsv(lecteur.result);
        var liste = chargerProspects();
        var ajout = 0, maj = 0;
        r.prospects.forEach(function (p) {
          var idx = -1;
          liste.forEach(function (x, i) { if (x.id === p.id) idx = i; });
          if (idx >= 0) { liste[idx] = p; maj++; } else { liste.push(p); ajout++; }
        });
        sauverProspects(liste);
        rendrePipeline();
        message("message-pipeline", ajout + " ajouté(s), " + maj + " mis à jour" + (r.ignores ? ", " + r.ignores + " ligne(s) ignorée(s)" : "") + ".");
      } catch (e) {
        message("message-pipeline", "Import impossible : " + e.message);
      }
    };
    lecteur.onerror = function () { message("message-pipeline", "Lecture du fichier impossible."); };
    lecteur.readAsText(fichier, "utf-8");
  }

  // ------------------------------------------------------------------
  // Navigation
  // ------------------------------------------------------------------
  function montrerVue(v, focus) {
    if (v !== "pipeline") v = "audit";
    document.getElementById("vue-audit").hidden = v !== "audit";
    document.getElementById("vue-pipeline").hidden = v !== "pipeline";
    document.querySelectorAll(".onglet").forEach(function (b) {
      if (b.getAttribute("data-vue") === v) b.setAttribute("aria-current", "page"); else b.removeAttribute("aria-current");
    });
    if (v === "pipeline") rendrePipeline(); else ajusterApercu();
    if (focus) {
      var h = document.getElementById(v === "pipeline" ? "titre-pipeline" : "titre-audit");
      h.setAttribute("tabindex", "-1"); h.focus();
    }
    try { if (location.hash !== "#" + v) history.replaceState(null, "", "#" + v); } catch (e) { /* rien */ }
  }

  // ------------------------------------------------------------------
  // Initialisation
  // ------------------------------------------------------------------
  function init() {
    form = document.getElementById("form-audit");
    var sel = form.elements.statut;
    sel.innerHTML = STATUTS.map(function (s) { return "<option>" + esc(s) + "</option>"; }).join("");

    if (!stockageOk) document.getElementById("alerte-stockage").hidden = false;
    var c = config();
    if (!c.telephone && !c.email && !c.whatsapp) document.getElementById("alerte-config").hidden = false;

    var brouillon = lire(CLE_BROUILLON, null);
    remplirFormulaire(brouillon && typeof brouillon === "object" ? brouillon : prospectVide());

    form.addEventListener("input", function () { rafraichir(); });
    form.addEventListener("change", function () { rafraichir(); });
    form.addEventListener("submit", function (e) { e.preventDefault(); enregistrer(); });
    document.getElementById("btn-imprimer").addEventListener("click", imprimer);
    document.getElementById("btn-nouveau").addEventListener("click", function () {
      supprimer(CLE_BROUILLON);
      remplirFormulaire(prospectVide());
      afficherErreurs([], false);
      form.elements.nom.focus();
    });

    document.querySelectorAll(".onglet").forEach(function (b) {
      b.addEventListener("click", function () { montrerVue(b.getAttribute("data-vue"), true); });
    });

    document.getElementById("filtres").addEventListener("click", function (e) {
      var b = e.target.closest("[data-filtre]");
      if (!b) return;
      filtre = b.getAttribute("data-filtre");
      ecrire(CLE_FILTRE, filtre);
      rendrePipeline();
      var nb = document.querySelector('[data-filtre="' + filtre.replace(/"/g, '\\"') + '"]');
      if (nb) nb.focus();
    });

    var liste = document.getElementById("liste-prospects");
    liste.addEventListener("change", function (e) {
      var tr = e.target.closest("tr[data-id]");
      if (!tr) return;
      var a = e.target.getAttribute("data-action");
      if (a === "statut") { majProspect(tr.getAttribute("data-id"), { statut: e.target.value }); }
      else if (a === "relance") { majProspect(tr.getAttribute("data-id"), { relance: e.target.value }); }
      else return;
      rendrePipeline();
      var cible = document.getElementById((a === "statut" ? "st-" : "rl-") + tr.getAttribute("data-id"));
      if (cible) cible.focus();
      message("message-pipeline", "Mis à jour.");
    });
    liste.addEventListener("click", function (e) {
      var b = e.target.closest("button[data-action]");
      if (!b) return;
      var id = b.closest("tr").getAttribute("data-id");
      var p = chargerProspects().filter(function (x) { return x.id === id; })[0];
      if (!p) return;
      if (b.getAttribute("data-action") === "ouvrir") {
        remplirFormulaire(p);
        montrerVue("audit", true);
      } else if (b.getAttribute("data-action") === "supprimer") {
        if (!window.confirm("Supprimer « " + p.nom + " » du pipeline ?")) return;
        sauverProspects(chargerProspects().filter(function (x) { return x.id !== id; }));
        if (courant.id === id) { form.elements.id.value = ""; courant.id = ""; }
        rendrePipeline();
        message("message-pipeline", "« " + p.nom + " » supprimé.");
      }
    });

    document.getElementById("btn-export").addEventListener("click", exporter);
    document.getElementById("input-import").addEventListener("change", function (e) {
      var f = e.target.files && e.target.files[0];
      if (f) importer(f);
      e.target.value = "";
    });

    window.addEventListener("resize", ajusterApercu);
    window.addEventListener("beforeprint", function () { rafraichir(false); });
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(ajusterApercu, function () {});

    rendrePipeline();
    montrerVue((location.hash || "").replace("#", ""), false);
  }

  // API exposée pour les tests et la console
  window.PolyglotteAudit = {
    calculer: calculer, normaliser: normaliser, versCsv: versCsv, depuisCsv: depuisCsv,
    stats: stats, STATUTS: STATUTS, BAREME: BAREME
  };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init); else init();
})();
