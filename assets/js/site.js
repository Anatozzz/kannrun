/* Polyglotte : comportements du site (JavaScript sans dépendance).
 *  1. Remplissage des coordonnées depuis window.POLYGLOTTE (config.js)
 *  2. Menu mobile
 *  3. Démo du menu multilingue
 *  4. Formulaire de demande d'audit
 */
(function () {
  "use strict";

  document.documentElement.classList.add("js");

  /* ------------------------------------------------------------------
   * 1. Coordonnées
   * ------------------------------------------------------------------ */
  var CONFIG = window.POLYGLOTTE || {};

  function brut(cle) {
    var v = CONFIG[cle];
    return typeof v === "string" ? v.trim() : "";
  }

  // Renvoie le lien utilisable pour une clé, ou "" si la valeur est vide
  // ou mal formée (on préfère ne rien afficher plutôt qu'un lien cassé).
  function lienPour(cle) {
    var v = brut(cle);
    if (!v) return "";
    switch (cle) {
      case "email":
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v) ? "mailto:" + v : "";
      case "telephone": {
        var tel = v.replace(/[^\d+]/g, "");
        return tel.replace(/\D/g, "").length >= 6 ? "tel:" + tel : "";
      }
      case "whatsapp": {
        var wa = v.replace(/\D/g, "");
        return wa.length >= 8 ? "https://wa.me/" + wa : "";
      }
      case "lienRdv":
      case "lienFormulaire":
        return /^https:\/\/[^\s]+$/i.test(v) ? v : "";
      default:
        return "";
    }
  }

  var CLES_LIENS = ["email", "telephone", "whatsapp", "lienRdv", "lienFormulaire"];
  function dispo(cle) {
    return CLES_LIENS.indexOf(cle) !== -1 ? lienPour(cle) !== "" : brut(cle) !== "";
  }
  function listeCles(attr) {
    return (attr || "").split(/\s+/).filter(Boolean);
  }

  function appliquerConfig() {
    // Liens : <a data-config="email" [data-config-show] [data-fallback="#audit" data-fallback-label="…"]>
    document.querySelectorAll("a[data-config]").forEach(function (a) {
      var cle = a.getAttribute("data-config");
      var href = lienPour(cle);
      if (href) {
        a.setAttribute("href", href);
        if (a.hasAttribute("data-config-show")) a.textContent = brut(cle);
        if (/^https:/.test(href)) a.setAttribute("rel", "noopener");
      } else if (a.hasAttribute("data-fallback")) {
        a.setAttribute("href", a.getAttribute("data-fallback"));
        if (a.hasAttribute("data-fallback-label")) a.textContent = a.getAttribute("data-fallback-label");
      } else {
        a.hidden = true;
      }
    });

    // Texte : <span data-config-text="siret" data-empty="…">
    document.querySelectorAll("[data-config-text]").forEach(function (el) {
      var v = brut(el.getAttribute("data-config-text"));
      if (v) {
        el.textContent = v;
        el.classList.remove("a-completer");
      } else if (el.hasAttribute("data-empty")) {
        el.textContent = el.getAttribute("data-empty");
        el.classList.add("a-completer");
      } else {
        el.textContent = "";
      }
    });

    // Affichage conditionnel
    document.querySelectorAll("[data-config-if]").forEach(function (el) {
      el.hidden = !dispo(el.getAttribute("data-config-if"));
    });
    document.querySelectorAll("[data-config-any]").forEach(function (el) {
      el.hidden = !listeCles(el.getAttribute("data-config-any")).some(dispo);
    });
    document.querySelectorAll("[data-config-none]").forEach(function (el) {
      el.hidden = listeCles(el.getAttribute("data-config-none")).some(dispo);
    });

    document.querySelectorAll("[data-annee]").forEach(function (el) {
      el.textContent = String(new Date().getFullYear());
    });
  }

  /* ------------------------------------------------------------------
   * 2. Menu mobile
   * ------------------------------------------------------------------ */
  function initNav() {
    var bouton = document.querySelector(".nav-toggle");
    var nav = document.getElementById("nav-principale");
    if (!bouton || !nav) return;

    function fermer(rendreFocus) {
      bouton.setAttribute("aria-expanded", "false");
      nav.classList.remove("is-open");
      if (rendreFocus) bouton.focus();
    }
    function ouvrir() {
      bouton.setAttribute("aria-expanded", "true");
      nav.classList.add("is-open");
    }

    bouton.addEventListener("click", function () {
      if (bouton.getAttribute("aria-expanded") === "true") fermer(false);
      else ouvrir();
    });
    nav.addEventListener("click", function (e) {
      if (e.target.closest("a")) fermer(false);
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && nav.classList.contains("is-open")) fermer(true);
    });
    document.addEventListener("click", function (e) {
      if (nav.classList.contains("is-open") && !nav.contains(e.target) && !bouton.contains(e.target)) fermer(false);
    });
    window.matchMedia("(min-width: 960px)").addEventListener("change", function (mq) {
      if (mq.matches) fermer(false);
    });
  }

  /* ------------------------------------------------------------------
   * 3. Démo du menu multilingue (restaurant fictif)
   * ------------------------------------------------------------------ */
  var DEMO = {
    fr: {
      sub: "Annecy · La carte", title: "Nos plats", all: "Allergènes :",
      note: "En cas d'allergie, demandez conseil à notre équipe.",
      plats: [
        ["Tartiflette au reblochon", "Pommes de terre, lardons, oignons et reblochon de Savoie fondu.", ["Lait"]],
        ["Filets de perche, sauce meunière", "Filets de perche poêlés au beurre, pommes vapeur.", ["Poisson", "Lait", "Gluten"]],
        ["Tarte aux myrtilles", "Pâte sablée maison et myrtilles de montagne.", ["Gluten", "Œufs", "Lait"]]
      ]
    },
    en: {
      sub: "Annecy · Menu", title: "Our dishes", all: "Allergens:",
      note: "If you have an allergy, please ask our staff.",
      plats: [
        ["Tartiflette with Reblochon cheese", "Potatoes, bacon lardons, onions and melted Reblochon from Savoie.", ["Milk"]],
        ["Perch fillets, meunière sauce", "Pan-fried perch fillets in butter, steamed potatoes.", ["Fish", "Milk", "Gluten"]],
        ["Blueberry tart", "Homemade shortcrust pastry and mountain blueberries.", ["Gluten", "Eggs", "Milk"]]
      ]
    },
    de: {
      sub: "Annecy · Speisekarte", title: "Unsere Gerichte", all: "Allergene:",
      note: "Bei Allergien fragen Sie bitte unser Personal.",
      plats: [
        ["Tartiflette mit Reblochon", "Kartoffeln, Speckwürfel, Zwiebeln und geschmolzener Reblochon aus Savoyen.", ["Milch"]],
        ["Barschfilets nach Müllerin-Art", "In Butter gebratene Barschfilets, Salzkartoffeln.", ["Fisch", "Milch", "Gluten"]],
        ["Heidelbeertarte", "Hausgemachter Mürbeteig und Bergheidelbeeren.", ["Gluten", "Eier", "Milch"]]
      ]
    },
    it: {
      sub: "Annecy · Il menù", title: "I nostri piatti", all: "Allergeni:",
      note: "In caso di allergie, chiedete al nostro personale.",
      plats: [
        ["Tartiflette al Reblochon", "Patate, pancetta a cubetti, cipolle e Reblochon della Savoia fuso.", ["Latte"]],
        ["Filetti di persico alla mugnaia", "Filetti di persico saltati nel burro, patate al vapore.", ["Pesce", "Latte", "Glutine"]],
        ["Crostata ai mirtilli", "Pasta frolla fatta in casa e mirtilli di montagna.", ["Glutine", "Uova", "Latte"]]
      ]
    },
    es: {
      sub: "Annecy · La carta", title: "Nuestros platos", all: "Alérgenos:",
      note: "En caso de alergia, consulte a nuestro personal.",
      plats: [
        ["Tartiflette con queso Reblochon", "Patatas, tocino en dados, cebolla y queso Reblochon de Saboya fundido.", ["Leche"]],
        ["Filetes de perca a la meunière", "Filetes de perca a la plancha con mantequilla, patatas al vapor.", ["Pescado", "Leche", "Gluten"]],
        ["Tarta de arándanos", "Masa quebrada casera y arándanos de montaña.", ["Gluten", "Huevos", "Leche"]]
      ]
    }
  };
  var PRIX = ["19,50 €", "24 €", "8,50 €"];

  function el(tag, cls, texte) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (texte != null) n.textContent = texte;
    return n;
  }

  function rendreDemo(langue) {
    var d = DEMO[langue];
    var ecran = document.getElementById("demo-menu");
    var liste = document.getElementById("demo-plats");
    if (!d || !ecran || !liste) return;

    ecran.setAttribute("lang", langue);
    ecran.querySelectorAll("[data-i18n]").forEach(function (n) {
      var cle = n.getAttribute("data-i18n");
      if (d[cle]) n.textContent = d[cle];
    });

    var frag = document.createDocumentFragment();
    d.plats.forEach(function (p, i) {
      var li = el("li", "pm-plat");
      var l1 = el("div", "pm-plat__l1");
      l1.appendChild(el("span", "pm-plat__nom", p[0]));
      l1.appendChild(el("span", "pm-plat__prix", PRIX[i]));
      li.appendChild(l1);
      li.appendChild(el("p", "pm-plat__desc", p[1]));
      var all = el("p", "pm-all");
      all.appendChild(el("span", "pm-all__lib", d.all));
      p[2].forEach(function (a) {
        all.appendChild(document.createTextNode(" "));
        all.appendChild(el("span", "pm-chip", a));
      });
      li.appendChild(all);
      frag.appendChild(li);
    });
    liste.replaceChildren(frag);
  }

  function initDemo() {
    var boutons = document.querySelectorAll(".pm-lang");
    var liste = document.getElementById("demo-plats");
    if (!boutons.length || !liste) return;
    var reduit = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    boutons.forEach(function (b) {
      b.addEventListener("click", function () {
        var langue = b.getAttribute("data-lang");
        boutons.forEach(function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
        if (reduit) { rendreDemo(langue); return; }
        liste.classList.add("is-switching");
        window.setTimeout(function () {
          rendreDemo(langue);
          liste.classList.remove("is-switching");
        }, 160);
      });
    });
  }

  /* ------------------------------------------------------------------
   * 4. Formulaire de demande d'audit
   * ------------------------------------------------------------------ */
  function initFormulaire() {
    var form = document.getElementById("form-audit");
    var msg = document.getElementById("form-msg");
    if (!form || !msg) return;

    var champs = {
      restaurant: form.elements.restaurant,
      prenom: form.elements.prenom,
      telephone: form.elements.telephone,
      email: form.elements.email,
      quartier: form.elements.quartier
    };

    function erreur(input, texte) {
      var p = document.getElementById("e-" + input.name);
      input.setAttribute("aria-invalid", texte ? "true" : "false");
      if (p) {
        p.textContent = texte || "";
        p.hidden = !texte;
      }
    }

    ["restaurant", "prenom", "telephone", "email"].forEach(function (nom) {
      champs[nom].addEventListener("input", function () {
        if (champs[nom].getAttribute("aria-invalid") === "true") erreur(champs[nom], "");
        if ((nom === "telephone" || nom === "email") && champs[nom].value.trim()) {
          var autre = nom === "telephone" ? champs.email : champs.telephone;
          if (!autre.value.trim()) erreur(autre, "");
        }
      });
    });

    function valider() {
      var v = {};
      Object.keys(champs).forEach(function (k) { v[k] = champs[k].value.trim(); });
      var premier = null;
      function ko(input, texte) { erreur(input, texte); if (!premier) premier = input; }

      ["restaurant", "prenom", "telephone", "email"].forEach(function (k) { erreur(champs[k], ""); });

      if (v.restaurant.length < 2) ko(champs.restaurant, "Indiquez le nom de votre restaurant.");
      if (!v.prenom) ko(champs.prenom, "Indiquez votre prénom.");

      if (!v.telephone && !v.email) {
        ko(champs.telephone, "Indiquez un téléphone ou un e-mail pour qu'on puisse vous recontacter.");
        erreur(champs.email, "Ou bien un e-mail.");
      } else {
        if (v.telephone) {
          var chiffres = v.telephone.replace(/\D/g, "");
          if (!/^[\d\s.+()-]+$/.test(v.telephone) || chiffres.length < 9 || chiffres.length > 15) {
            ko(champs.telephone, "Ce numéro semble incomplet. Exemple : 06 12 34 56 78.");
          }
        }
        if (v.email && !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v.email)) {
          ko(champs.email, "Cette adresse e-mail semble incorrecte. Exemple : nom@exemple.fr.");
        }
      }

      if (premier) { premier.focus(); return null; }
      return v;
    }

    function afficher(paragraphes, alerte) {
      msg.replaceChildren();
      paragraphes.forEach(function (contenu) {
        var p = document.createElement("p");
        contenu.forEach(function (morceau) {
          if (typeof morceau === "string") p.appendChild(document.createTextNode(morceau));
          else p.appendChild(morceau);
        });
        msg.appendChild(p);
      });
      msg.classList.toggle("form__msg--alerte", !!alerte);
      msg.hidden = false;
      msg.focus();
    }

    function lien(href, texte) {
      var a = document.createElement("a");
      a.href = href;
      a.textContent = texte;
      return a;
    }

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var v = valider();
      if (!v) { msg.hidden = true; return; }

      var lienForm = lienPour("lienFormulaire");
      var mail = lienPour("email");

      // a) Formulaire externe (Tally…) : on redirige avec les champs en paramètres.
      if (lienForm) {
        var url;
        try {
          url = new URL(lienForm);
          Object.keys(v).forEach(function (k) { if (v[k]) url.searchParams.set(k, v[k]); });
          url = url.toString();
        } catch (err) {
          url = lienForm;
        }
        afficher([["Merci " + v.prenom + " ! Nous vous redirigeons vers notre formulaire pour finaliser votre demande…"]]);
        window.setTimeout(function () { window.location.href = url; }, 600);
        return;
      }

      // b) E-mail prérempli vers l'adresse de contact.
      if (mail) {
        var nl = "\r\n";
        var sujet = "Demande d'audit gratuit : " + v.restaurant;
        var corps = [
          "Bonjour,",
          "",
          "Je souhaite recevoir l'audit gratuit Polyglotte.",
          "",
          "Restaurant : " + v.restaurant,
          "Prénom : " + v.prenom,
          "Téléphone : " + (v.telephone || "non renseigné"),
          "E-mail : " + (v.email || "non renseigné"),
          "Quartier : " + (v.quartier || "non renseigné"),
          "",
          "Merci !"
        ].join(nl);
        var mailto = mail + "?subject=" + encodeURIComponent(sujet) + "&body=" + encodeURIComponent(corps);
        afficher([
          ["Merci " + v.prenom + " ! Votre messagerie s'ouvre avec la demande déjà rédigée : il ne vous reste qu'à l'envoyer."],
          ["Rien ne s'ouvre ? Écrivez-nous directement à ", lien(mail, brut("email")), "."]
        ]);
        window.location.href = mailto;
        return;
      }

      // c) Aucun canal configuré : on le dit honnêtement, avec une alternative si possible.
      var alternatives = [];
      if (lienPour("telephone")) alternatives.push(["Appelez-nous au ", lien(lienPour("telephone"), brut("telephone")), "."]);
      if (lienPour("whatsapp")) alternatives.push(["Ou écrivez-nous sur ", lien(lienPour("whatsapp"), "WhatsApp"), "."]);
      if (lienPour("lienRdv")) alternatives.push(["Vous pouvez aussi ", lien(lienPour("lienRdv"), "prendre rendez-vous en ligne"), "."]);
      if (window.console) console.warn("Polyglotte : renseignez `email` ou `lienFormulaire` dans assets/js/config.js pour activer le formulaire.");
      afficher(
        [["Merci " + v.prenom + ". L'envoi en ligne n'est pas encore activé, votre demande n'a donc pas été transmise."]]
          .concat(alternatives.length ? alternatives : [["Revenez très bientôt : cette page est en cours de mise en service."]]),
        true
      );
    });
  }

  /* ------------------------------------------------------------------ */
  function demarrer() {
    appliquerConfig();
    initNav();
    initDemo();
    initFormulaire();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", demarrer);
  else demarrer();
})();
