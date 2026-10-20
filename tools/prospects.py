#!/usr/bin/env python3
"""Polyglotte : liste priorisée de TOUS les prospects (restaurants, cafés, bars) d'un territoire.

Par défaut, le territoire est le Grand Annecy (EPCI 200066793, 34 communes : voir
tools/grand_annecy_communes.json). Le script n'utilise que la bibliothèque standard
(Python 3.9 ou plus).

Sources (option --sources, chacune activable séparément) :
  sirene  API Recherche d'entreprises (gratuite, sans clé)
          https://recherche-entreprises.api.gouv.fr/search
  osm     OpenStreetMap via Overpass, en une seule requête
          https://overpass-api.de/api/interpreter
  google  Google Places API (New), facultative et payante, désactivée par défaut.
          Elle demande --google-key ou la variable GOOGLE_MAPS_API_KEY. Le script ne fait
          aucun scraping de Google Maps.

Sorties (dans --sortie) :
  prospects.csv           au format d'import de audit/ (« ; », UTF-8 avec BOM), trié par score
  prospects-complet.csv   toutes les colonnes (même format)

=====================================================================================
BARÈME DU SCORE DE PRIORITÉ (0 à 100). Plus le score est haut, plus il faut y aller tôt.
=====================================================================================
  Zone (25 max)            Vieille ville 25 · Bords du lac / Pâquier 25 · Talloires / rive est 18
                           · Sévrier / rive ouest 15 · Centre / gare 12 · Annecy-le-Vieux 8 · Autre 0
                           (poids_zones du fichier de territoire)
  Nombre d'avis Google     ≥ 500 : 15 · 200-499 : 12 · 50-199 : 8 · 10-49 : 4 · < 10 : 0
    (15 max)               · inconnu (Google non interrogé ou fiche non trouvée) : 5
  Note Google (15 max)     3,8 à 4,5 : 15 (bonne note, marge de progrès) · 3,5 à < 3,8 : 8
                           · > 4,5 à 4,7 : 6 · > 4,7 : 3 · < 3,5 : 4 · inconnue : 5
  Site web (10 max)        absent de Google : 10 · absent d'OSM (Google non consulté) : 6
                           · aucune information : 3 · site présent : 0
  Lien vers le menu        aucun lien menu dans OSM : 10 · pas d'information OSM : 5 · lien présent : 0
    (10 max)
  Création récente         établissement créé il y a moins de 18 mois : 15 (« prospect chaud »)
    (15 max)               · 18 à 36 mois : 5 · plus ancien ou date inconnue : 0
  Type (10 max)            restauration traditionnelle 10 · restaurant d'hôtel 8 · café / bar 6
                           · glacier 4 · restauration rapide 3 (les deux sources sont lues, la plus
                           favorable compte)
  Chaîne / franchise       exclue des sorties. Avec --inclure-chaines : −40 points (plancher 0).
=====================================================================================
Le détail du calcul est écrit pour chaque prospect (colonne score_detail et notes de audit/).

Le README (tools/README.md, section « Liste de prospects ») décrit l'usage, les coûts,
les limites et le RGPD.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import difflib
import hashlib
import io
import json
import math
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ICI = Path(__file__).resolve().parent
TERRITOIRE_DEFAUT = ICI / "grand_annecy_communes.json"
FIXTURES = ICI / "fixtures"

VERSION = "1.0"
USER_AGENT = ("Polyglotte-prospects/" + VERSION +
              " (outil interne de prospection locale ; Python urllib)")

URL_SIRENE = "https://recherche-entreprises.api.gouv.fr/search"
URL_OVERPASS = "https://overpass-api.de/api/interpreter"
URL_PLACES_TEXT = "https://places.googleapis.com/v1/places:searchText"
URL_PLACES_DETAILS = "https://places.googleapis.com/v1/places/"

# Documentation officielle de l'API Recherche d'entreprises (OpenAPI, octobre 2026) :
SIRENE_PER_PAGE_MAX = 25          # « Le nombre de résultats par page, limité à 25. »
SIRENE_RESULTATS_MAX = 10000      # page * per_page <= 10 000
SIRENE_MATCHING_MAX = 100         # limite_matching_etablissements : 1 à 100 (défaut 10)
SIRENE_DELAI = 0.2                # 5 req/s, sous la limite officielle de 7 req/s par IP

GOOGLE_TTL_JOURS = 30             # contenus Google : cache temporaire, purgé au-delà
GOOGLE_MAX_DEFAUT = 500
GOOGLE_PRIX_1000 = 35.0           # USD, Text Search Enterprise (à revérifier, voir README)
GOOGLE_GRATUIT_MOIS = 1000        # seuil gratuit mensuel du SKU Enterprise (à revérifier)
GOOGLE_FIELDMASK_TEXT = ",".join("places." + c for c in (
    "id", "displayName", "location", "rating", "userRatingCount", "websiteUri", "googleMapsUri"))
GOOGLE_FIELDMASK_DETAILS = "id,displayName,location,rating,userRatingCount,websiteUri,googleMapsUri"

NAF_DEFAUT = ["56.10A", "56.10C", "56.30Z"]
NAF_HOTEL = "55.10Z"
NAF_LIBELLES = {
    "56.10A": "Restauration traditionnelle",
    "56.10B": "Cafétérias et autres libres-services",
    "56.10C": "Restauration de type rapide",
    "56.30Z": "Débits de boissons",
    "55.10Z": "Hôtels et hébergement similaire",
}
AMENITIES_OSM = ["restaurant", "cafe", "bar", "fast_food", "pub", "ice_cream"]

# Colonnes du CSV d'import de audit/ (audit/audit.js, COLONNES). Ne pas modifier l'ordre.
COLONNES_AUDIT = ["id", "nom", "quartier", "note", "totalAvis", "sansReponse", "etrangers",
                  "etrangersSansReponse", "langues", "menu", "allergenes", "horaires", "photos",
                  "lienMenu", "site", "statut", "relance", "score", "notes", "creeLe", "majLe"]
QUARTIERS = ["Vieille ville", "Bords du lac / Pâquier", "Centre / gare", "Annecy-le-Vieux",
             "Sévrier / rive ouest", "Talloires / rive est", "Autre"]
STATUT_INITIAL = "À visiter"

COLONNES_COMPLET = [
    "id", "nom", "zone", "commune", "code_commune", "code_postal", "adresse", "lat", "lon",
    "siret", "siren", "naf", "naf_libelle", "type", "date_creation", "prospect_chaud",
    "tranche_effectif", "entreprise_individuelle", "denomination_sirene", "dirigeants",
    "site", "menu_en_ligne", "telephone", "cuisine", "horaires_osm", "osm_id", "place_id",
    "google_maps_uri", "note", "nb_avis", "chaine", "score", "score_detail", "sources",
    "ids_alternatifs", "deja_dans_crm", "donnees", "date_collecte",
]

# Chaînes et franchises. « exact » : nom trop courant pour une recherche par inclusion
# (« Chez Paul » n'est pas la boulangerie Paul).
CHAINES = [
    "McDonald's", "Burger King", "KFC", "Subway", "Domino's", "Pizza Hut", "Starbucks",
    "Brioche Dorée", "Flunch", "Buffalo Grill", "Del Arte", "Courtepaille", "Hippopotamus",
    "Léon de Bruxelles", "O'Tacos", "Five Guys", "Columbus Café", "Class'Croûte",
    "Pomme de Pain", "Bagelstein", "La Croissanterie", "Memphis Coffee", "Les 3 Brasseurs",
    "Trois Brasseurs", "Poivre Rouge", "Bistro Régent", "Big Fernand", "Sushi Shop",
    "Planet Sushi", "Cojean", "Mezzo di Pasta", "Pizza Cosy", "Le Kiosque à Pizzas",
    "Tim Hortons", "Popeyes", "Pitaya", "Tacos Avenue", "Black & White Burger",
    "Chicken Street", "Jour", "Le Pain Quotidien", "La Mie Câline", "Marie Blachère",
    "Ange", "Boulangerie Ange", "Crêpe Touch", "Pizza Hut Delivery", "Bistrot du Boucher",
    "Au Bureau", "La Boucherie", "Paul", "Quick", "Exki", "Wok Grill", "Big Mamma",
    "Signorizza", "Volfoni", "Les Burgers de Papa", "Holly's Diner", "Factory & Co",
    "Starbucks Coffee", "Dunkin", "Steak 'n Shake", "Crousty Burger", "Il Ristorante",
]
CHAINES_EXACTES = {"paul", "quick", "exki", "jour", "ange", "pitaya", "au bureau", "la boucherie",
                   "il ristorante", "volfoni"}

MOTS_VIDES = {"le", "la", "les", "l", "du", "de", "des", "d", "au", "aux", "chez", "et", "the",
              "a", "en", "sur"}
MOTS_GENERIQUES = {"restaurant", "resto", "restaurants", "bar", "cafe", "brasserie", "bistrot",
                   "bistro", "pizzeria", "creperie", "snack", "pub", "glacier", "traiteur",
                   "auberge", "hotel", "taverne", "cafeteria"}
FORMES_JURIDIQUES = {"sarl", "sas", "sasu", "eurl", "sa", "sci", "snc", "eirl", "ei", "ets",
                     "selarl", "scop", "earl", "sarlu"}
PETITS_MOTS = {"de", "du", "des", "la", "le", "les", "et", "à", "au", "aux", "d", "l", "en", "sur"}

MASQUE_ND = "[NON-DIFFUSIBLE]"

POINTS_TYPE = {"traditionnel": 10, "hotel": 8, "boissons": 6, "glacier": 4, "rapide": 3}
LIB_TYPE = {"traditionnel": "restauration traditionnelle", "hotel": "restaurant d'hôtel",
            "boissons": "café / bar", "glacier": "glacier", "rapide": "restauration rapide"}
TYPE_NAF = {"56.10A": "traditionnel", "56.10B": "rapide", "56.10C": "rapide",
            "56.30Z": "boissons", "55.10Z": "hotel"}
TYPE_OSM = {"restaurant": "traditionnel", "cafe": "boissons", "bar": "boissons", "pub": "boissons",
            "fast_food": "rapide", "ice_cream": "glacier"}
PENALITE_CHAINE = 40


class ErreurSource(Exception):
    """Une source est indisponible (réseau, quota, hors ligne sans cache)."""


class ErreurEntree(Exception):
    """Fichier ou option invalide."""


# ---------------------------------------------------------------------------
# Utilitaires
# ---------------------------------------------------------------------------
def sans_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def jetons(nom: str) -> list:
    s = sans_accents(str(nom or "")).lower().replace("&", " et ").replace("œ", "oe")
    s = re.sub(r"[’'`´]", " ", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return [t for t in s.split() if t]


def normaliser_nom(nom: str) -> str:
    """Nom comparable : sans accents, sans articles, sans « restaurant », sans forme juridique."""
    tout = jetons(nom)
    utiles = [t for t in tout if t not in MOTS_VIDES and t not in MOTS_GENERIQUES
              and t not in FORMES_JURIDIQUES]
    if not utiles:  # « Le Bistrot » -> « bistrot » plutôt qu'une chaîne vide
        utiles = ([t for t in tout if t not in MOTS_VIDES and t not in FORMES_JURIDIQUES]
                  or [t for t in tout if t not in FORMES_JURIDIQUES] or tout)
    return " ".join(utiles)


def similarite(a: str, b: str) -> float:
    """Similarité de 0 à 1 entre deux noms normalisés."""
    a, b = normaliser_nom(a), normaliser_nom(b)
    if not a or not b:
        return 0.0
    if a == b or a.replace(" ", "") == b.replace(" ", ""):
        return 1.0
    ta, tb = set(a.split()), set(b.split())
    inclusion = 0.85 if (ta <= tb or tb <= ta) else 0.0  # « Fictif » ⊂ « Fictif Thiou »
    jaccard = len(ta & tb) / len(ta | tb)
    ratio = difflib.SequenceMatcher(None, a, b).ratio()
    return max(inclusion, jaccard, ratio)


def meilleure_similarite(noms_a, noms_b) -> float:
    return max((similarite(x, y) for x in noms_a if x for y in noms_b if y), default=0.0)


def distance_m(lat1, lon1, lat2, lon2) -> float:
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def point_dans_polygone(lat, lon, polygone) -> bool:
    """Lancer de rayon ; polygone = [[lat, lon], ...]."""
    dedans = False
    n = len(polygone)
    for i in range(n):
        y1, x1 = polygone[i]
        y2, x2 = polygone[(i + 1) % n]
        if (y1 > lat) != (y2 > lat):
            x = x1 + (lat - y1) * (x2 - x1) / (y2 - y1)
            if lon < x:
                dedans = not dedans
    return dedans


def flottant(v):
    if v is None or v == "" or v == MASQUE_ND:
        return None
    try:
        f = float(str(v).replace(",", "."))
    except ValueError:
        return None
    return f if math.isfinite(f) else None


def propre(v):
    """Valeur exploitable ou None (champs masqués « [NON-DIFFUSIBLE] », vides)."""
    if v is None:
        return None
    s = str(v).strip()
    return None if not s or s == MASQUE_ND else s


def titre_propre(s: str) -> str:
    """« LE PETIT BISTROT » -> « Le Petit Bistrot » (seulement si tout est en capitales)."""
    s = re.sub(r"\s+", " ", str(s or "")).strip()
    if not s or s != s.upper():
        return s
    mots = s.lower().split(" ")
    out = []
    for i, m in enumerate(mots):
        if i and m in PETITS_MOTS:
            out.append(m)
            continue
        # d'arc, l'atelier, mc'donald : majuscule après l'apostrophe aussi
        out.append(re.sub(r"(^|[-'’])([a-zà-ÿ])", lambda x: x.group(1) + x.group(2).upper(), m))
    return " ".join(out)


def telephone_fr(tel):
    """« +33 4 50 12 34 56 » -> « 04 50 12 34 56 » (le premier numéro si plusieurs, séparés par « ; »)."""
    if not tel:
        return None
    premier = tel.split(";")[0].strip()
    chiffres = re.sub(r"[^\d+]", "", premier)
    if chiffres.startswith("+33") and len(chiffres) == 12:
        chiffres = "0" + chiffres[3:]
    elif chiffres.startswith("0033") and len(chiffres) == 13:
        chiffres = "0" + chiffres[4:]
    if re.fullmatch(r"0\d{9}", chiffres):
        return " ".join(chiffres[i:i + 2] for i in range(0, 10, 2))
    return premier


def mois_entre(debut: dt.date, fin: dt.date) -> float:
    return (fin - debut).days / 30.4375


def date_iso(v):
    try:
        return dt.date.fromisoformat(str(v)[:10])
    except (TypeError, ValueError):
        return None


def nombre_fr(x, dec=1):
    return ("{:.%df}" % dec).format(x).replace(".", ",")


def avertir(msg):
    print("Attention : " + msg, file=sys.stderr)


# ---------------------------------------------------------------------------
# Territoire
# ---------------------------------------------------------------------------
def charger_territoire(valeur=None, epci=None) -> dict:
    """Charge un fichier de territoire JSON, ou une liste de codes INSEE séparés par des virgules."""
    if valeur and re.fullmatch(r"\s*\d[\dAB]\d{3}(\s*,\s*\d[\dAB]\d{3})*\s*", str(valeur)):
        codes = [c.strip() for c in str(valeur).split(",")]
        brut = {"territoire": "Communes " + ", ".join(codes), "epci_siren": epci,
                "communes": [{"code_insee": c, "nom": c, "zone": "Autre"} for c in codes]}
    elif valeur is None and epci:
        brut = {"territoire": "EPCI " + epci, "epci_siren": epci, "communes": []}
    else:
        chemin = Path(valeur) if valeur else TERRITOIRE_DEFAUT
        try:
            brut = json.loads(chemin.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            raise ErreurEntree("fichier de communes illisible (%s) : %s" % (chemin, e))
        if epci:
            brut["epci_siren"] = epci
    communes, alias = {}, {}
    for c in brut.get("communes", []):
        code = str(c.get("code_insee", "")).strip()
        if not re.fullmatch(r"\d[\dAB]\d{3}", code):
            raise ErreurEntree("code INSEE invalide dans le fichier de communes : %r" % code)
        communes[code] = {"nom": c.get("nom") or code, "zone": c.get("zone") or "Autre",
                          "codes_postaux": list(c.get("codes_postaux") or [])}
        for ancien in (c.get("codes_anciens") or {}):
            alias[str(ancien)] = code
    for z in brut.get("regles_zones", []):
        if z.get("zone") not in QUARTIERS:
            raise ErreurEntree("zone inconnue de audit/ : %r" % z.get("zone"))
    poids = {q: 0 for q in QUARTIERS}
    poids.update({k: int(v) for k, v in (brut.get("poids_zones") or {}).items() if k in poids})
    if not brut.get("poids_zones"):
        poids.update({"Vieille ville": 25, "Bords du lac / Pâquier": 25, "Talloires / rive est": 18,
                      "Sévrier / rive ouest": 15, "Centre / gare": 12, "Annecy-le-Vieux": 8})
    return {
        "nom": brut.get("territoire", "?"), "epci": brut.get("epci_siren"),
        "communes": communes, "alias": alias, "regles_zones": brut.get("regles_zones", []),
        "poids_zones": poids, "bbox": brut.get("bbox"),
        "par_nom": {jetons_commune(v["nom"]): k for k, v in communes.items()},
    }


def jetons_commune(nom: str) -> str:
    return " ".join(jetons(nom))


def commune_canonique(code, territoire):
    """Code de commune du territoire (ou None si hors territoire). Gère les anciens codes."""
    code = propre(code)
    if not code:
        return None
    if code in territoire["communes"]:
        return code
    return territoire["alias"].get(code)


# ---------------------------------------------------------------------------
# HTTP : cache disque, hors ligne, débit, réessais
# ---------------------------------------------------------------------------
def transport_urllib(methode, url, entetes, corps, delai):
    req = urllib.request.Request(url, data=corps, headers=entetes, method=methode)
    try:
        with urllib.request.urlopen(req, timeout=delai) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers or {}), e.read() or b""


class Http:
    """Requêtes JSON avec cache disque des réponses brutes.

    - transport(methode, url, entetes, corps, delai) -> (statut, entetes, octets) : injectable (tests).
    - cache : dossier ; une réponse = un fichier <cache>/<source>/<sha1>.json.
    - hors_ligne : n'utilise que le cache, aucune requête.
    - La clé de cache n'inclut jamais la clé d'API Google (elle est dans un en-tête).
    """

    def __init__(self, transport=None, cache=None, hors_ligne=False, user_agent=USER_AGENT,
                 dormir=time.sleep, horloge=time.monotonic, maintenant=None, journal=None):
        self.transport = transport or transport_urllib
        self.cache = Path(cache) if cache else None
        self.hors_ligne = hors_ligne
        self.user_agent = user_agent
        self.dormir = dormir
        self.horloge = horloge
        self.maintenant = maintenant or (lambda: dt.datetime.now(dt.timezone.utc))
        self.derniere = {}
        self.compteur = {}
        self.journal = journal if journal is not None else []

    def _chemin(self, source, cle):
        return self.cache / source / (hashlib.sha1(cle.encode("utf-8")).hexdigest() + ".json")

    def lire_cache(self, source, cle, ttl_jours=None):
        if not self.cache:
            return None
        f = self._chemin(source, cle)
        if not f.exists():
            return None
        try:
            entree = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        if ttl_jours is not None:
            date = dt.datetime.fromisoformat(entree.get("date", "1970-01-01T00:00:00+00:00"))
            if self.maintenant() - date > dt.timedelta(days=ttl_jours):
                f.unlink()  # contenu périmé : supprimé, pas seulement ignoré
                return None
        return entree.get("reponse")

    def ecrire_cache(self, source, cle, url, reponse):
        if not self.cache:
            return
        f = self._chemin(source, cle)
        f.parent.mkdir(parents=True, exist_ok=True)
        entree = {"date": self.maintenant().isoformat(timespec="seconds"), "url": url,
                  "reponse": reponse}
        f.write_text(json.dumps(entree, ensure_ascii=False), encoding="utf-8")

    def json(self, source, methode, url, params=None, corps_json=None, corps_form=None,
             entetes=None, delai_min=0.0, delai_reseau=60, ttl_jours=None, essais=5):
        if params:
            url = url + "?" + urllib.parse.urlencode(params, safe=",")
        corps = None
        if corps_json is not None:
            corps = json.dumps(corps_json, ensure_ascii=False, sort_keys=True).encode("utf-8")
        elif corps_form is not None:
            corps = urllib.parse.urlencode(corps_form).encode("utf-8")
        masque = (entetes or {}).get("X-Goog-FieldMask", "")
        cle = "%s %s %s %s" % (methode, url, masque, corps.decode("utf-8") if corps else "")
        deja = self.lire_cache(source, cle, ttl_jours)
        if deja is not None:
            return deja
        if self.hors_ligne:
            raise ErreurSource("%s : réponse absente du cache en mode --hors-ligne (%s)" % (source, url))
        h = {"User-Agent": self.user_agent, "Accept": "application/json"}
        if corps_json is not None:
            h["Content-Type"] = "application/json"
        elif corps_form is not None:
            h["Content-Type"] = "application/x-www-form-urlencoded"
        h.update(entetes or {})
        attente = 2.0
        for essai in range(1, essais + 1):
            ecoule = self.horloge() - self.derniere.get(source, -1e9)
            if ecoule < delai_min:
                self.dormir(delai_min - ecoule)
            self.derniere[source] = self.horloge()
            self.compteur[source] = self.compteur.get(source, 0) + 1
            try:
                statut, ent, octets = self.transport(methode, url, h, corps, delai_reseau)
            except (urllib.error.URLError, OSError) as e:
                if essai == essais:
                    raise ErreurSource("%s : réseau indisponible (%s)" % (source, e))
                self.dormir(attente)
                attente *= 2
                continue
            if statut == 200:
                try:
                    reponse = json.loads(octets.decode("utf-8"))
                except (UnicodeDecodeError, ValueError):
                    raise ErreurSource("%s : réponse non JSON (%s)" % (source, octets[:200]))
                self.ecrire_cache(source, cle, url.split("key=")[0], reponse)
                return reponse
            if statut in (429, 500, 502, 503, 504) and essai < essais:
                ra = {k.lower(): v for k, v in (ent or {}).items()}.get("retry-after")
                pause = flottant(ra) if ra else None
                self.journal.append("%s : HTTP %s, nouvel essai dans %ss" % (source, statut, pause or attente))
                self.dormir(pause if pause is not None else attente)
                attente *= 2
                continue
            texte = octets[:300].decode("utf-8", "replace")
            raise ErreurSource("%s : HTTP %s %s" % (source, statut, texte))
        raise ErreurSource("%s : abandon après %d essais" % (source, essais))


def purger_cache_google(cache, maintenant=None):
    """Supprime les réponses Google de plus de GOOGLE_TTL_JOURS jours (seul l'index des place_id reste)."""
    if not cache:
        return 0
    dossier = Path(cache) / "google"
    if not dossier.is_dir():
        return 0
    maintenant = maintenant or dt.datetime.now(dt.timezone.utc)
    n = 0
    for f in dossier.glob("*.json"):
        try:
            date = dt.datetime.fromisoformat(json.loads(f.read_text(encoding="utf-8"))["date"])
        except (OSError, ValueError, KeyError):
            date = None
        if date is None or maintenant - date > dt.timedelta(days=GOOGLE_TTL_JOURS):
            f.unlink()
            n += 1
    return n


# ---------------------------------------------------------------------------
# Source 1 : API Recherche d'entreprises (Sirene)
# ---------------------------------------------------------------------------
def params_sirene(naf, territoire, page, codes=None, avec_dirigeants=False):
    include = ["matching_etablissements", "complements"] + (["dirigeants"] if avec_dirigeants else [])
    p = {
        "activite_principale": ",".join(naf),   # filtre sur l'unité légale (doc officielle)
        "etat_administratif": "A",              # unité légale active
        "per_page": SIRENE_PER_PAGE_MAX,
        "page": page,
        "limite_matching_etablissements": SIRENE_MATCHING_MAX,
        "minimal": "true",
        "include": ",".join(include),
    }
    if codes:
        p["code_commune"] = ",".join(codes)     # filtre sur les établissements
    elif territoire.get("epci"):
        p["epci"] = territoire["epci"]
    else:
        raise ErreurEntree("aucune commune ni EPCI pour interroger Sirene")
    return p


def pages_sirene(http, naf, territoire, codes, avec_dirigeants, stats):
    """Parcourt toutes les pages d'une requête ; renvoie la liste des unités légales."""
    resultats, page, total_pages = [], 1, 1
    while page <= total_pages:
        rep = http.json("sirene", "GET", URL_SIRENE,
                        params=params_sirene(naf, territoire, page, codes, avec_dirigeants),
                        delai_min=SIRENE_DELAI)
        if page == 1:
            total = int(rep.get("total_results") or 0)
            if total > SIRENE_RESULTATS_MAX:
                return None  # l'appelant découpe la requête
            total_pages = int(rep.get("total_pages") or 1)
            stats["sirene_unites_legales"] = stats.get("sirene_unites_legales", 0) + total
        lot = rep.get("results") or []
        resultats.extend(lot)
        stats["sirene_pages"] = stats.get("sirene_pages", 0) + 1
        if not lot:
            break
        page += 1
    return resultats


def collecter_sirene(http, territoire, naf, avec_dirigeants=False, stats=None):
    stats = stats if stats is not None else {}
    codes = sorted(territoire["communes"]) or None
    unites = pages_sirene(http, naf, territoire, codes, avec_dirigeants, stats)
    if unites is None:  # plus de 10 000 résultats : une requête par commune
        if not codes:
            raise ErreurSource("sirene : plus de 10 000 résultats pour l'EPCI ; passez --communes")
        unites = []
        for code in codes:
            lot = pages_sirene(http, naf, territoire, [code], avec_dirigeants, stats)
            if lot is None:
                raise ErreurSource("sirene : plus de 10 000 résultats pour la commune %s" % code)
            unites.extend(lot)
    vus, etabs = set(), []
    for ul in unites:
        for e in extraire_etablissements(ul, territoire, set(naf), stats, avec_dirigeants):
            if e["siret"] not in vus:
                vus.add(e["siret"])
                etabs.append(e)
    stats["sirene_etablissements"] = len(etabs)
    return etabs


def extraire_etablissements(ul, territoire, naf, stats, avec_dirigeants=False):
    """Établissements actifs, du territoire, de la bonne activité, diffusibles."""
    def compte(cle):
        stats[cle] = stats.get(cle, 0) + 1

    if ul.get("etat_administratif") not in (None, "A"):
        compte("sirene_exclus_unite_cessee")
        return
    comp = ul.get("complements") or {}
    ei = bool(comp.get("est_entrepreneur_individuel")) or str(ul.get("nature_juridique")) == "1000"
    matching = ul.get("matching_etablissements") or []
    if len(matching) >= SIRENE_MATCHING_MAX:
        avertir("sirene : %s a au moins %d établissements dans la zone ; seuls les %d premiers sont lus"
                % (ul.get("siren"), SIRENE_MATCHING_MAX, SIRENE_MATCHING_MAX))
    for et in matching:
        if et.get("etat_administratif") != "A":
            compte("sirene_exclus_etablissement_ferme")
            continue
        if et.get("statut_diffusion_etablissement") == "P" or ul.get("statut_diffusion") == "P":
            compte("sirene_exclus_non_diffusible")  # opposition à la diffusion : on respecte
            continue
        code = commune_canonique(et.get("commune"), territoire) if territoire["communes"] else None
        if territoire["communes"] and not code:
            compte("sirene_exclus_hors_territoire")
            continue
        if not territoire["communes"] and territoire.get("epci") and et.get("epci") not in (None, territoire["epci"]):
            compte("sirene_exclus_hors_territoire")
            continue
        code = code or propre(et.get("commune"))
        act = propre(et.get("activite_principale"))
        if act and act not in naf:
            compte("sirene_exclus_activite_etablissement")
            continue
        enseignes = [titre_propre(x) for x in (et.get("liste_enseignes") or []) if propre(x)]
        nom_com = titre_propre(propre(et.get("nom_commercial")) or "")
        raison = propre(ul.get("nom_raison_sociale"))
        nom_complet = propre(ul.get("nom_complet"))
        noms_publics = [n for n in enseignes + [nom_com] if n]
        if not ei and raison:
            noms_publics.append(titre_propre(raison))
        noms_matching = noms_publics + ([nom_complet] if ei and nom_complet else [])
        dirigeants = ""
        if avec_dirigeants:
            dirigeants = " | ".join(
                " ".join(x for x in (d.get("nom"), d.get("prenoms"), "(%s)" % d["qualite"] if d.get("qualite") else None) if x)
                if d.get("type_dirigeant") == "personne physique" else (d.get("denomination") or "")
                for d in (ul.get("dirigeants") or []) if d)
        yield {
            "source": "sirene",
            "siret": et.get("siret"), "siren": ul.get("siren"),
            "noms": noms_publics, "noms_matching": noms_matching,
            "denomination": (nom_complet if (avec_dirigeants or not ei) else ""),
            "ei": ei, "dirigeants": dirigeants,
            "naf": act or ul.get("activite_principale"),
            "date_creation": propre(et.get("date_creation")),
            "tranche_effectif": propre(et.get("tranche_effectif_salarie")),
            "adresse": propre(et.get("adresse")),
            "code_postal": propre(et.get("code_postal")),
            "commune": code,
            "lat": flottant(et.get("latitude")), "lon": flottant(et.get("longitude")),
        }


# ---------------------------------------------------------------------------
# Source 2 : OpenStreetMap (Overpass)
# ---------------------------------------------------------------------------
def requete_overpass(territoire, amenities=None, bbox=False, delai=180):
    filtre = '["amenity"~"^(%s)$"]' % "|".join(amenities or AMENITIES_OSM)
    if bbox:
        s, o, n, e = territoire["bbox"]
        return ("[out:json][timeout:%d];\nnwr%s(%s,%s,%s,%s);\nout center tags;\n"
                % (delai, filtre, s, o, n, e))
    codes = sorted(territoire["communes"])
    if codes:
        zone = ('area["boundary"="administrative"]["admin_level"="8"]["ref:INSEE"~"^(%s)$"]->.communes;'
                % "|".join(codes))
    elif territoire.get("epci"):
        zone = 'area["ref:FR:SIREN"="%s"]->.communes;' % territoire["epci"]
    else:
        raise ErreurEntree("aucune commune ni EPCI pour interroger Overpass")
    # Une seule requête : pour chaque commune, on écrit d'abord la zone (avec son ref:INSEE),
    # puis ses lieux. Le script sait ainsi dans quelle commune se trouve chaque lieu.
    return ("[out:json][timeout:%d];\n%s\nforeach.communes->.c(\n  .c out tags;\n"
            "  nwr%s(area.c);\n  out center tags;\n);\n" % (delai, zone, filtre))


def collecter_osm(http, territoire, amenities=None, bbox=False, stats=None):
    stats = stats if stats is not None else {}
    if bbox and not territoire.get("bbox"):
        raise ErreurEntree("--osm-bbox : le fichier de territoire n'a pas de « bbox »")
    q = requete_overpass(territoire, amenities, bbox)
    rep = http.json("osm", "POST", URL_OVERPASS, corps_form={"data": q}, delai_reseau=200, essais=3)
    if rep.get("remark") and "runtime error" in str(rep.get("remark")):
        raise ErreurSource("osm : " + str(rep["remark"]))
    return analyser_overpass(rep, territoire, bbox, stats)


def analyser_overpass(rep, territoire, bbox=False, stats=None):
    stats = stats if stats is not None else {}
    commune, vus, lieux = None, set(), []
    for el in rep.get("elements", []):
        tags = el.get("tags") or {}
        if el.get("type") == "area":
            commune = commune_canonique(tags.get("ref:INSEE"), territoire) or propre(tags.get("ref:INSEE"))
            continue
        cle = "%s/%s" % (el.get("type"), el.get("id"))
        if cle in vus:
            continue
        vus.add(cle)
        nom = propre(tags.get("name"))
        if not nom:
            stats["osm_exclus_sans_nom"] = stats.get("osm_exclus_sans_nom", 0) + 1
            continue
        lat = el.get("lat", (el.get("center") or {}).get("lat"))
        lon = el.get("lon", (el.get("center") or {}).get("lon"))
        code = commune
        if bbox or not code:
            code = commune_depuis_adresse(tags, territoire)
        if territoire["communes"] and code not in territoire["communes"]:
            stats["osm_exclus_hors_territoire"] = stats.get("osm_exclus_hors_territoire", 0) + 1
            continue
        site = propre(tags.get("website") or tags.get("contact:website") or tags.get("url"))
        menu = propre(tags.get("website:menu") or tags.get("menu:website") or tags.get("menu:url")
                      or tags.get("url:menu") or tags.get("contact:menu"))
        tel = telephone_fr(propre(tags.get("phone") or tags.get("contact:phone")))
        rue = " ".join(x for x in (tags.get("addr:housenumber"), tags.get("addr:street")) if x)
        ville = " ".join(x for x in (tags.get("addr:postcode"), tags.get("addr:city")) if x)
        lieux.append({
            "source": "osm", "osm_id": "%s/%s" % (el.get("type"), el.get("id")),
            "osm_cle": "%s-%s" % ({"node": "n", "way": "w", "relation": "r"}.get(el.get("type"), "x"), el.get("id")),
            "noms": [nom] + [propre(tags[k]) for k in ("alt_name", "official_name", "old_name") if propre(tags.get(k))],
            "amenity": tags.get("amenity"), "cuisine": propre(tags.get("cuisine")),
            "horaires": propre(tags.get("opening_hours")),
            "site": site, "menu": menu, "telephone": tel,
            "marque": propre(tags.get("brand") or tags.get("brand:wikidata")),
            "adresse": ", ".join(x for x in (rue, ville) if x) or None,
            "code_postal": propre(tags.get("addr:postcode")),
            "commune": code, "lat": flottant(lat), "lon": flottant(lon),
        })
    stats["osm_lieux"] = len(lieux)
    return lieux


def commune_depuis_adresse(tags, territoire):
    ville = jetons_commune(tags.get("addr:city") or "")
    if ville and ville in territoire["par_nom"]:
        return territoire["par_nom"][ville]
    cp = tags.get("addr:postcode")
    candidates = [k for k, v in territoire["communes"].items() if cp and cp in v["codes_postaux"]]
    return candidates[0] if len(candidates) == 1 else None


# ---------------------------------------------------------------------------
# Fusion Sirene <-> OSM
# ---------------------------------------------------------------------------
SEUIL_DISTANCE = 60.0      # mètres
SEUIL_NOM = 0.6
SEUIL_DISTANCE_LARGE = 150.0
SEUIL_NOM_FORT = 0.9


def score_appariement(a, b):
    """Renvoie (similarité, distance) si a et b sont le même établissement, sinon None.

    Règle : même commune, puis
      - distance < 60 m et similarité des noms >= 0,6 ;
      - ou distance < 150 m et similarité >= 0,9 (géocodage Sirene imprécis) ;
      - sans coordonnées d'un côté : similarité >= 0,95 et même code postal.
    """
    if a.get("commune") and b.get("commune") and a["commune"] != b["commune"]:
        return None
    sim = meilleure_similarite(a.get("noms_matching") or a["noms"], b.get("noms_matching") or b["noms"])
    if None in (a.get("lat"), a.get("lon"), b.get("lat"), b.get("lon")):
        if sim >= 0.95 and a.get("code_postal") and a.get("code_postal") == b.get("code_postal"):
            return sim, 9999.0
        return None
    d = distance_m(a["lat"], a["lon"], b["lat"], b["lon"])
    if (d < SEUIL_DISTANCE and sim >= SEUIL_NOM) or (d < SEUIL_DISTANCE_LARGE and sim >= SEUIL_NOM_FORT):
        return sim, d
    return None


def apparier(gauche, droite):
    """Appariement un-pour-un glouton : meilleures paires d'abord (similarité, puis distance)."""
    paires = []
    for i, a in enumerate(gauche):
        for j, b in enumerate(droite):
            if a is b:
                continue
            if a.get("lat") is not None and b.get("lat") is not None and abs(a["lat"] - b["lat"]) > 0.002:
                continue  # > ~220 m en latitude : inutile de comparer les noms (gros volumes)
            s = score_appariement(a, b)
            if s:
                paires.append((-s[0], s[1], i, j))
    paires.sort()
    pris_g, pris_d, res = set(), set(), []
    for _, _, i, j in paires:
        if i not in pris_g and j not in pris_d:
            pris_g.add(i)
            pris_d.add(j)
            res.append((i, j))
    return res


def dedoublonner_interne(liste, cle_recent=None):
    """Doublons au sein d'une même source (seuils stricts : < 30 m et nom >= 0,9)."""
    garde, retire = [], set()
    for i, a in enumerate(liste):
        if i in retire:
            continue
        for j in range(i + 1, len(liste)):
            if j in retire:
                continue
            b = liste[j]
            if None in (a.get("lat"), b.get("lat")) or a.get("commune") != b.get("commune"):
                continue
            if distance_m(a["lat"], a["lon"], b["lat"], b["lon"]) < 30 and \
                    meilleure_similarite(a["noms"], b["noms"]) >= 0.9:
                # Sirene : on garde l'établissement le plus récent (reprise de fonds)
                if cle_recent and (b.get(cle_recent) or "") > (a.get(cle_recent) or ""):
                    a, liste[i] = b, b
                retire.add(j)
        garde.append(a)
    return garde, len(retire)


def nom_affiche(s, o):
    """Nom à afficher : nom d'usage OSM > enseigne > nom commercial > raison sociale."""
    if o and o["noms"]:
        return o["noms"][0]
    if s and s["noms"]:
        return s["noms"][0]
    if s and s.get("denomination"):
        return titre_propre(s["denomination"])
    rue = (s or {}).get("adresse") or ""
    return "Établissement sans enseigne" + (" – " + titre_propre(rue) if rue else "")


def fusionner(sirene, osm, stats=None):
    stats = stats if stats is not None else {}
    sirene, n1 = dedoublonner_interne(list(sirene), "date_creation")
    osm, n2 = dedoublonner_interne(list(osm))
    stats["doublons_internes_sirene"], stats["doublons_internes_osm"] = n1, n2
    paires = apparier(sirene, osm)
    stats["fusions_sirene_osm"] = len(paires)
    lien_s = {i: j for i, j in paires}
    pris_o = set(lien_s.values())
    prospects = []
    for i, s in enumerate(sirene):
        o = osm[lien_s[i]] if i in lien_s else None
        prospects.append(construire(s, o))
    for j, o in enumerate(osm):
        if j not in pris_o:
            prospects.append(construire(None, o))
    return prospects


def construire(s, o):
    s, o = s or {}, o or {}
    sources = [x for x, v in (("sirene", s), ("osm", o)) if v]
    ids = []
    if s:
        ids.append("sirene-" + s["siret"])
    if o:
        ids.append("osm-" + o["osm_cle"])
    lat = o.get("lat") if o.get("lat") is not None else s.get("lat")
    lon = o.get("lon") if o.get("lon") is not None else s.get("lon")
    types = [t for t in (TYPE_NAF.get(s.get("naf")), TYPE_OSM.get(o.get("amenity"))) if t]
    return {
        "id": ids[0], "ids": ids, "sources": sources,
        "nom": nom_affiche(s or None, o or None),
        # noms publics seulement (le nom d'un entrepreneur individuel ne sert qu'à l'appariement)
        "noms": list(dict.fromkeys((o.get("noms") or []) + (s.get("noms") or []))),
        "siret": s.get("siret"), "siren": s.get("siren"), "naf": s.get("naf"),
        "date_creation": s.get("date_creation"), "tranche_effectif": s.get("tranche_effectif"),
        "ei": s.get("ei"), "denomination": s.get("denomination") or "", "dirigeants": s.get("dirigeants") or "",
        "adresse": s.get("adresse") or o.get("adresse"),
        "code_postal": s.get("code_postal") or o.get("code_postal"),
        "commune": s.get("commune") or o.get("commune"),
        "lat": lat, "lon": lon,
        "types": types,
        "osm_id": o.get("osm_id"), "amenity": o.get("amenity"), "cuisine": o.get("cuisine"),
        "horaires": o.get("horaires"), "telephone": o.get("telephone"), "marque": o.get("marque"),
        "site_osm": o.get("site"), "menu_osm": o.get("menu"), "a_osm": bool(o),
        "place_id": None, "note": None, "nb_avis": None, "site_google": None,
        "google_maps_uri": None, "google_consulte": False,
    }


# ---------------------------------------------------------------------------
# Source 3 (facultative) : Google Places API (New)
# ---------------------------------------------------------------------------
def charger_index_place_ids(cache):
    """Index persistant {id prospect: place_id}. Les place_id peuvent être conservés (CGU Google)."""
    if not cache:
        return {}
    f = Path(cache) / "google_place_ids.json"
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def sauver_index_place_ids(cache, index):
    if cache:
        Path(cache).mkdir(parents=True, exist_ok=True)
        (Path(cache) / "google_place_ids.json").write_text(
            json.dumps(index, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")


def choisir_place(p, places):
    """Meilleur candidat Google : même nom (>= 0,5) à moins de 150 m, ou nom >= 0,8 sans coordonnées."""
    meilleur = None
    for pl in places or []:
        nom = ((pl.get("displayName") or {}).get("text")) or ""
        sim = meilleure_similarite(p["noms"] or [p["nom"]], [nom])
        loc = pl.get("location") or {}
        if p.get("lat") is not None and loc.get("latitude") is not None:
            d = distance_m(p["lat"], p["lon"], loc["latitude"], loc["longitude"])
            ok = d < 150 and sim >= 0.5
        else:
            d, ok = 9999.0, sim >= 0.8
        if ok and (meilleur is None or (sim, -d) > meilleur[0]):
            meilleur = ((sim, -d), pl)
    return meilleur[1] if meilleur else None


def enrichir_google(http, prospects, cle, maximum=GOOGLE_MAX_DEFAUT, cache=None, stats=None):
    stats = stats if stats is not None else {}
    index = charger_index_place_ids(cache)
    entetes_base = {"X-Goog-Api-Key": cle}
    n = 0
    for p in prospects[:maximum]:
        place_id = next((index[i] for i in p["ids"] if i in index), None)
        place = None
        try:
            if place_id:
                place = http.json("google", "GET", URL_PLACES_DETAILS + urllib.parse.quote(place_id),
                                  entetes=dict(entetes_base, **{"X-Goog-FieldMask": GOOGLE_FIELDMASK_DETAILS}),
                                  delai_min=0.1, ttl_jours=GOOGLE_TTL_JOURS)
            else:
                corps = {"textQuery": " ".join(x for x in (p["nom"], p.get("adresse") or
                                                          p.get("commune_nom") or "") if x),
                         "languageCode": "fr", "regionCode": "FR", "pageSize": 3}
                if p.get("lat") is not None:
                    corps["locationBias"] = {"circle": {"center": {"latitude": p["lat"], "longitude": p["lon"]},
                                                        "radius": 200.0}}
                rep = http.json("google", "POST", URL_PLACES_TEXT, corps_json=corps,
                                entetes=dict(entetes_base, **{"X-Goog-FieldMask": GOOGLE_FIELDMASK_TEXT}),
                                delai_min=0.1, ttl_jours=GOOGLE_TTL_JOURS)
                place = choisir_place(p, rep.get("places"))
        except ErreurSource as e:
            if any(c in str(e) for c in ("HTTP 400", "HTTP 401", "HTTP 403")):
                raise  # clé invalide, API non activée, requête refusée : inutile d'insister
            avertir(str(e))
            continue
        n += 1
        p["google_consulte"] = True
        if place:
            p["place_id"] = place.get("id")
            p["note"] = place.get("rating")
            p["nb_avis"] = place.get("userRatingCount")
            p["site_google"] = place.get("websiteUri")
            p["google_maps_uri"] = place.get("googleMapsUri")
            index[p["id"]] = p["place_id"]
            if "google" not in p["sources"]:
                p["sources"].append("google")
            p["ids"].append("gplace-" + p["place_id"])
    sauver_index_place_ids(cache, index)
    stats["google_requetes"] = n
    stats["google_trouves"] = sum(1 for p in prospects if p.get("place_id"))
    # Deux prospects rattachés à la même fiche Google = doublon : on garde le plus complet.
    vus, garde, doublons = {}, [], 0   # vus : place_id -> position dans garde
    for p in prospects:
        pid = p.get("place_id")
        if pid and pid in vus:
            k = vus[pid]
            if len(p["sources"]) > len(garde[k]["sources"]):
                garde[k] = p
            doublons += 1
            continue
        if pid:
            vus[pid] = len(garde)
        garde.append(p)
    stats["doublons_google"] = doublons
    return garde


# ---------------------------------------------------------------------------
# Zones, chaînes, score
# ---------------------------------------------------------------------------
def zone_de(p, territoire):
    code = p.get("commune")
    for regle in territoire["regles_zones"]:
        if regle.get("communes") and code not in regle["communes"]:
            continue
        if regle.get("codes_postaux"):
            if p.get("code_postal") in regle["codes_postaux"] and not regle.get("polygone"):
                return regle["zone"]
            continue
        if regle.get("polygone") and p.get("lat") is not None and \
                point_dans_polygone(p["lat"], p["lon"], regle["polygone"]):
            return regle["zone"]
    zone = territoire["communes"].get(code, {}).get("zone", "Autre")
    return zone if zone in QUARTIERS else "Autre"


_CHAINES_NORM = None


def chaines_normalisees():
    global _CHAINES_NORM
    if _CHAINES_NORM is None:
        _CHAINES_NORM = [(" ".join(jetons(c)), "".join(jetons(c)), c) for c in CHAINES]
    return _CHAINES_NORM


def est_chaine(noms, marque=None):
    """Nom de la chaîne détectée, ou None. Une marque OSM (brand / brand:wikidata) suffit."""
    if marque:
        return marque
    for nom in noms or []:
        t = " ".join(j for j in jetons(nom) if j not in FORMES_JURIDIQUES)
        compact = t.replace(" ", "")
        for avec_espaces, compact_c, original in chaines_normalisees():
            if avec_espaces in CHAINES_EXACTES:
                if t == avec_espaces:
                    return original
            elif compact_c and (compact_c in compact or re.search(r"\b%s\b" % re.escape(avec_espaces), t)):
                return original
    return None


def calculer_score(p, territoire, aujourd_hui):
    d = []
    pts = territoire["poids_zones"].get(p["zone"], 0)
    d.append(("zone " + p["zone"], pts))

    n = p.get("nb_avis")
    if n is None:
        d.append(("nb d'avis inconnu", 5))
    else:
        v = 15 if n >= 500 else 12 if n >= 200 else 8 if n >= 50 else 4 if n >= 10 else 0
        d.append(("%d avis Google" % n, v))

    note = p.get("note")
    if note is None:
        d.append(("note inconnue", 5))
    else:
        v = 15 if 3.8 <= note <= 4.5 else 8 if 3.5 <= note < 3.8 else 6 if 4.5 < note <= 4.7 \
            else 3 if note > 4.7 else 4
        d.append(("note " + nombre_fr(note), v))

    if p.get("site_google") or p.get("site_osm"):
        d.append(("site web présent", 0))
    elif p.get("google_consulte") and p.get("place_id"):
        d.append(("pas de site sur Google", 10))
    elif p.get("a_osm"):
        d.append(("pas de site dans OSM", 6))
    else:
        d.append(("site web : aucune information", 3))

    if p.get("menu_osm"):
        d.append(("lien menu présent", 0))
    elif p.get("a_osm"):
        d.append(("pas de lien menu (OSM)", 10))
    else:
        d.append(("lien menu : aucune information", 5))

    creation = date_iso(p.get("date_creation"))
    p["prospect_chaud"] = False
    if creation:
        m = mois_entre(creation, aujourd_hui)
        if 0 <= m < 18:
            p["prospect_chaud"] = True
            d.append(("créé il y a %d mois (prospect chaud)" % int(m), 15))
        elif 0 <= m < 36:
            d.append(("créé il y a %d mois" % int(m), 5))
        else:
            d.append(("créé en %d" % creation.year, 0))
    else:
        d.append(("date de création inconnue", 0))

    types = p.get("types") or []
    if types:
        meilleur = max(types, key=lambda t: POINTS_TYPE[t])
        p["type"] = meilleur
        d.append((LIB_TYPE[meilleur], POINTS_TYPE[meilleur]))
    else:
        p["type"] = ""
        d.append(("type inconnu", 0))

    total = sum(v for _, v in d)
    if p.get("chaine"):
        d.append(("chaîne « %s »" % p["chaine"], -PENALITE_CHAINE))
        total -= PENALITE_CHAINE
    p["score"] = max(0, min(100, total))
    p["score_detail"] = " · ".join("%s %s%d" % (lib, "+" if v >= 0 else "", v) for lib, v in d)
    return p["score"]


# ---------------------------------------------------------------------------
# Pipeline existant (export CSV de audit/)
# ---------------------------------------------------------------------------
def lire_crm(chemin):
    """Lit un export CSV de audit/ et renvoie (ids, noms normalisés -> id)."""
    try:
        texte = Path(chemin).read_text(encoding="utf-8-sig")
    except OSError as e:
        raise ErreurEntree("export audit/ illisible : %s" % e)
    premiere = texte.split("\n", 1)[0]
    sep = ";" if premiere.count(";") >= premiere.count(",") else ","
    lecteur = csv.DictReader(io.StringIO(texte), delimiter=sep)
    if "nom" not in (lecteur.fieldnames or []):
        raise ErreurEntree("export audit/ sans colonne « nom » : %s" % chemin)
    ids, noms = set(), {}
    for ligne in lecteur:
        i = (ligne.get("id") or "").strip()
        nom = re.sub(r"^\[TEST\]\s*", "", (ligne.get("nom") or "").strip())
        if i:
            ids.add(i)
        if nom:
            noms.setdefault((normaliser_nom(nom), ligne.get("quartier") or ""), i)
    return ids, noms


def marquer_crm(prospects, crm):
    ids, noms = crm
    for p in prospects:
        deja = next((i for i in p["ids"] if i in ids), None)
        if not deja:
            deja = noms.get((normaliser_nom(p["nom"]), p["zone"]))
        p["deja_dans_crm"] = deja or ""


# ---------------------------------------------------------------------------
# Sorties CSV (règles de audit/audit.js : versCsv / csvCellule / depuisCsv)
# ---------------------------------------------------------------------------
def cellule(v):
    s = "" if v is None else str(v)
    if re.match(r"^[=+\-@]", s) and not re.match(r"^-?\d", s):
        s = "'" + s  # comme audit.js : évite l'injection de formules dans Excel
    return '"' + s.replace('"', '""') + '"' if re.search(r'[";\n\r]', s) else s


def ecrire_csv(chemin, colonnes, lignes):
    sortie = ["﻿" + ";".join(colonnes)]
    for l in lignes:
        sortie.append(";".join(cellule(l.get(c, "")) for c in colonnes))
    Path(chemin).write_text("\r\n".join(sortie) + "\r\n", encoding="utf-8", newline="")


def site_de(p):
    return p.get("site_google") or p.get("site_osm") or ""


def ligne_audit(p, rang, date_collecte, horodatage, test):
    morceaux = ["Priorité %d/100 : %s" % (p["score"], p["score_detail"])]
    if p.get("adresse"):
        morceaux.append("Adresse : " + p["adresse"])
    if p.get("telephone"):
        morceaux.append("Tél. (public) : " + p["telephone"])
    if site_de(p):
        morceaux.append("Site : " + site_de(p))
    if p.get("menu_osm"):
        morceaux.append("Menu : " + p["menu_osm"])
    if p.get("cuisine"):
        morceaux.append("Cuisine : " + p["cuisine"].replace(";", ", "))
    if p.get("siret"):
        morceaux.append("SIRET %s · NAF %s %s" % (p["siret"], p.get("naf") or "",
                                                 NAF_LIBELLES.get(p.get("naf"), "")))
    if p.get("date_creation"):
        morceaux.append("Créé le " + p["date_creation"])
    if p.get("chaine"):
        morceaux.append("CHAÎNE / FRANCHISE : " + p["chaine"])
    morceaux.append("Sources : " + "+".join(p["sources"]) + " · collecté le " + date_collecte +
                    (" · note/avis Google à rafraîchir sous 30 jours" if p.get("note") is not None else ""))
    if test:
        morceaux.insert(0, "DONNÉES DE TEST — établissement FICTIF")
    nom = ("[TEST] " if test else "") + p["nom"]
    # majLe décroissant = ordre d'affichage du pipeline de audit/ (relance vide pour tous)
    maj = (horodatage - dt.timedelta(seconds=rang)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    return {
        "id": p["id"], "nom": nom[:80], "quartier": p["zone"],
        "note": nombre_fr(p["note"]) if p.get("note") is not None else "",
        "totalAvis": p["nb_avis"] if p.get("nb_avis") is not None else "",
        "sansReponse": "", "etrangers": "", "etrangersSansReponse": "", "langues": "",
        "menu": "aucun", "allergenes": "non", "horaires": "non", "photos": "non",
        "lienMenu": "non", "site": "oui" if site_de(p) else "non",
        "statut": STATUT_INITIAL, "relance": "", "score": 0,
        "notes": " | ".join(morceaux)[:2000],
        "creeLe": horodatage.strftime("%Y-%m-%dT%H:%M:%S.000Z"), "majLe": maj,
        "date_collecte": date_collecte,
    }


def ligne_complete(p, territoire, date_collecte, test, avec_dirigeants):
    return {
        "id": p["id"], "nom": p["nom"], "zone": p["zone"],
        "commune": territoire["communes"].get(p.get("commune"), {}).get("nom", p.get("commune") or ""),
        "code_commune": p.get("commune") or "", "code_postal": p.get("code_postal") or "",
        "adresse": p.get("adresse") or "",
        "lat": "%.6f" % p["lat"] if p.get("lat") is not None else "",
        "lon": "%.6f" % p["lon"] if p.get("lon") is not None else "",
        "siret": p.get("siret") or "", "siren": p.get("siren") or "", "naf": p.get("naf") or "",
        "naf_libelle": NAF_LIBELLES.get(p.get("naf"), ""), "type": LIB_TYPE.get(p.get("type"), ""),
        "date_creation": p.get("date_creation") or "", "prospect_chaud": "oui" if p.get("prospect_chaud") else "",
        "tranche_effectif": p.get("tranche_effectif") or "",
        "entreprise_individuelle": "oui" if p.get("ei") else ("non" if p.get("siret") else ""),
        "denomination_sirene": p.get("denomination") or "",
        "dirigeants": p.get("dirigeants") if avec_dirigeants else "",
        "site": site_de(p), "menu_en_ligne": p.get("menu_osm") or "",
        "telephone": p.get("telephone") or "", "cuisine": p.get("cuisine") or "",
        "horaires_osm": p.get("horaires") or "", "osm_id": p.get("osm_id") or "",
        "place_id": p.get("place_id") or "", "google_maps_uri": p.get("google_maps_uri") or "",
        "note": nombre_fr(p["note"]) if p.get("note") is not None else "",
        "nb_avis": p["nb_avis"] if p.get("nb_avis") is not None else "",
        "chaine": p.get("chaine") or "", "score": p["score"], "score_detail": p["score_detail"],
        "sources": "+".join(p["sources"]), "ids_alternatifs": " ".join(p["ids"][1:]),
        "deja_dans_crm": p.get("deja_dans_crm") or "",
        "donnees": "TEST (établissement fictif)" if test else "réelles (sources publiques)",
        "date_collecte": date_collecte,
    }


def verifier_expiration(dossier, aujourd_hui):
    """Avertit si une ancienne sortie contient des contenus Google de plus de 30 jours."""
    f = Path(dossier) / "prospects-complet.csv"
    if not f.exists():
        return False
    try:
        lignes = list(csv.DictReader(io.StringIO(f.read_text(encoding="utf-8-sig")), delimiter=";"))
    except (OSError, csv.Error):
        return False
    for l in lignes:
        d = date_iso(l.get("date_collecte"))
        if (l.get("note") or l.get("nb_avis")) and d and (aujourd_hui - d).days > GOOGLE_TTL_JOURS:
            avertir("%s contient des notes/avis Google collectés le %s (plus de %d jours). Les CGU de "
                    "Google Maps Platform n'autorisent pas leur conservation durable : ce fichier va être "
                    "remplacé ; supprimez aussi vos anciennes copies." % (f, d, GOOGLE_TTL_JOURS))
            return True
    return False


# ---------------------------------------------------------------------------
# Résumé console
# ---------------------------------------------------------------------------
def compter(it):
    c = {}
    for x in it:
        c[x] = c.get(x, 0) + 1
    return sorted(c.items(), key=lambda kv: (-kv[1], str(kv[0])))


def resume(prospects, territoire, stats, test, sortie, exclus_chaines, deja_crm):
    o = []
    if test:
        o.append("=" * 72)
        o.append("  DONNÉES DE TEST : établissements FICTIFS (mode --fixtures). Rien n'est réel.")
        o.append("=" * 72)
    o.append("Territoire : %s (%d communes)" % (territoire["nom"], len(territoire["communes"])))
    o.append("Prospects retenus : %d  (chaînes exclues : %d, déjà dans le pipeline : %d)"
             % (len(prospects), exclus_chaines, deja_crm))
    o.append("Sources : " + ", ".join("%s %d" % kv for kv in compter("+".join(p["sources"]) for p in prospects)))
    detail = ["%s=%s" % (k, v) for k, v in sorted(stats.items())]
    o.append("Détail collecte : " + (", ".join(detail) if detail else "-"))
    o.append("")
    o.append("Par commune :")
    for k, v in compter(territoire["communes"].get(p.get("commune"), {}).get("nom", p.get("commune") or "?")
                        for p in prospects):
        o.append("  %-28s %4d" % (k, v))
    o.append("Par zone :")
    for k, v in compter(p["zone"] for p in prospects):
        o.append("  %-28s %4d" % (k, v))
    o.append("Par activité (NAF Sirene, sinon type OSM) :")
    for k, v in compter((p.get("naf") and "%s %s" % (p["naf"], NAF_LIBELLES.get(p["naf"], ""))) or
                        ("OSM " + (p.get("amenity") or "?")) for p in prospects):
        o.append("  %-40s %4d" % (k.strip(), v))
    o.append("")
    o.append("Top 20 :")
    for i, p in enumerate(prospects[:20], 1):
        o.append("  %2d. %3d  %-34s %-22s %s%s" % (i, p["score"], p["nom"][:34], p["zone"][:22],
                                                 "+".join(p["sources"]), "  [chaud]" if p.get("prospect_chaud") else ""))
    o.append("")
    o.append("Fichiers : %s/prospects.csv (à importer dans audit/) et %s/prospects-complet.csv" % (sortie, sortie))
    if any(p.get("note") is not None for p in prospects):
        o.append("Rappel : notes et nombres d'avis Google à usage ponctuel, à ne pas conserver plus de "
                 "%d jours (CGU Google Maps Platform)." % GOOGLE_TTL_JOURS)
    o.append("Données © contributeurs OpenStreetMap (ODbL) et base Sirene / INSEE (Licence Ouverte 2.0).")
    return "\n".join(o)


# ---------------------------------------------------------------------------
# Mode démonstration : transport qui lit tools/fixtures/exemple_*.json
# ---------------------------------------------------------------------------
class TransportFixtures:
    def __init__(self, dossier=FIXTURES):
        self.dossier = Path(dossier)
        self.appels = []

    def _lire(self, nom):
        return json.loads((self.dossier / nom).read_text(encoding="utf-8"))

    def __call__(self, methode, url, entetes, corps, delai):
        self.appels.append((methode, url, entetes, corps))
        if url.startswith(URL_SIRENE):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
            page = int(q.get("page", ["1"])[0])
            f = self.dossier / ("exemple_sirene_page%d.json" % page)
            rep = self._lire(f.name) if f.exists() else {"results": [], "total_results": 0,
                                                          "page": page, "per_page": 25, "total_pages": 0}
        elif url.startswith(URL_OVERPASS):
            rep = self._lire("exemple_overpass.json")
        elif url.startswith(URL_PLACES_TEXT):
            requete = json.loads(corps.decode("utf-8"))["textQuery"]
            rep = {}
            for r in self._lire("exemple_places.json")["reponses"]:
                if normaliser_nom(r["requete_contient"]) in normaliser_nom(requete):
                    rep = r["reponse"]
                    break
        elif url.startswith(URL_PLACES_DETAILS):
            pid = urllib.parse.unquote(url[len(URL_PLACES_DETAILS):])
            rep = next((pl for r in self._lire("exemple_places.json")["reponses"]
                        for pl in r["reponse"].get("places", []) if pl.get("id") == pid), None)
            if rep is None:
                return 404, {}, b'{"error":{"code":404,"status":"NOT_FOUND"}}'
        else:
            return 404, {}, b"{}"
        return 200, {}, json.dumps(rep).encode("utf-8")


# ---------------------------------------------------------------------------
# Programme principal
# ---------------------------------------------------------------------------
def analyser_arguments(argv):
    ap = argparse.ArgumentParser(
        prog="prospects.py",
        description="Liste priorisée des prospects (restaurants, cafés, bars) d'un territoire, "
                    "au format d'import de audit/.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Exemple : python3 tools/prospects.py --sortie prospects/\n"
               "Démo sans réseau : python3 tools/prospects.py --fixtures --sortie /tmp/demo")
    ap.add_argument("--sortie", default=None, help="dossier de sortie (défaut : prospects/, ou prospects/test/ avec --fixtures)")
    ap.add_argument("--sources", default=None,
                    help="sources séparées par des virgules : sirene,osm,google (défaut : sirene,osm ; "
                         "google ajouté automatiquement si une clé est fournie)")
    ap.add_argument("--naf", default=None, help="codes NAF (défaut : 56.10A,56.10C,56.30Z)")
    ap.add_argument("--avec-hotels", action="store_true", help="ajoute le NAF 55.10Z (hôtels)")
    ap.add_argument("--communes", default=None,
                    help="fichier JSON de territoire (défaut : tools/grand_annecy_communes.json) "
                         "ou liste de codes INSEE séparés par des virgules")
    ap.add_argument("--epci", default=None,
                    help="SIREN d'un EPCI : Sirene filtre sur l'EPCI (sans --communes : tout l'EPCI)")
    ap.add_argument("--osm-bbox", action="store_true",
                    help="OSM : interroger la bbox du territoire au lieu des zones communales")
    ap.add_argument("--cache", default=None, help="dossier de cache des réponses brutes (défaut : <sortie>/cache)")
    ap.add_argument("--sans-cache", action="store_true", help="n'écrit ni ne lit aucun cache")
    ap.add_argument("--hors-ligne", action="store_true", help="n'utilise que le cache, aucune requête réseau")
    ap.add_argument("--fixtures", action="store_true",
                    help="mode démo sur tools/fixtures/exemple_*.json (établissements fictifs, aucun réseau)")
    ap.add_argument("--google-key", default=None, help="clé Google Maps Platform (ou variable GOOGLE_MAPS_API_KEY)")
    ap.add_argument("--google-max", type=int, default=GOOGLE_MAX_DEFAUT,
                    help="nombre maximal de requêtes Google, par ordre de priorité (défaut : %d)" % GOOGLE_MAX_DEFAUT)
    ap.add_argument("--inclure-chaines", action="store_true",
                    help="garde les chaînes et franchises, avec une pénalité de %d points" % PENALITE_CHAINE)
    ap.add_argument("--avec-dirigeants", action="store_true",
                    help="exporte les noms des dirigeants (données personnelles : voir README)")
    ap.add_argument("--crm", default=None,
                    help="export CSV de votre pipeline audit/ : les prospects déjà présents sont retirés "
                         "de prospects.csv (évite d'écraser leur statut à la réimportation)")
    ap.add_argument("--contact", default=None,
                    help="adresse de contact ajoutée au User-Agent (recommandé par Overpass)")
    ap.add_argument("--date-ref", default=None, help=argparse.SUPPRESS)  # tests : date du jour imposée
    return ap.parse_args(argv)


def main(argv=None, transport=None, dormir=time.sleep):
    a = analyser_arguments(argv)
    try:
        aujourd_hui = dt.date.fromisoformat(a.date_ref) if a.date_ref else dt.date.today()
    except ValueError:
        print("Erreur : --date-ref attend AAAA-MM-JJ", file=sys.stderr)
        return 2
    test = a.fixtures
    sortie = Path(a.sortie or ("prospects/test" if test else "prospects"))
    cle_google = a.google_key or os.environ.get("GOOGLE_MAPS_API_KEY")
    if a.sources:
        sources = [s.strip() for s in a.sources.split(",") if s.strip()]
    else:
        sources = ["sirene", "osm"] + (["google"] if (cle_google or test) else [])
    inconnues = set(sources) - {"sirene", "osm", "google"}
    if inconnues or not sources:
        print("Erreur : --sources accepte sirene, osm, google (reçu : %s)" % a.sources, file=sys.stderr)
        return 2
    if "google" in sources and not cle_google and not test:
        print("Erreur : la source google demande --google-key ou la variable GOOGLE_MAPS_API_KEY.",
              file=sys.stderr)
        return 2
    naf = [c.strip().upper() for c in (a.naf.split(",") if a.naf else NAF_DEFAUT) if c.strip()]
    if a.avec_hotels and NAF_HOTEL not in naf:
        naf.append(NAF_HOTEL)
    if any(not re.fullmatch(r"\d\d\.\d\d[A-Z]", c) for c in naf):
        print("Erreur : codes NAF au format 56.10A attendus (reçu : %s)" % ",".join(naf), file=sys.stderr)
        return 2
    try:
        territoire = charger_territoire(a.communes, a.epci)
        crm = lire_crm(a.crm) if a.crm else None
    except ErreurEntree as e:
        print("Erreur : %s" % e, file=sys.stderr)
        return 2
    if a.avec_dirigeants:
        avertir("--avec-dirigeants : les noms des dirigeants (souvent ceux d'entrepreneurs individuels) "
                "sont des données personnelles. Base légale à documenter (intérêt légitime), information "
                "des personnes, conservation limitée à 3 ans. Ne les diffusez pas.")

    cache = None
    if not (a.sans_cache or test):
        cache = Path(a.cache) if a.cache else sortie / "cache"
    if test and a.hors_ligne:
        print("Erreur : --fixtures et --hors-ligne sont incompatibles.", file=sys.stderr)
        return 2
    if a.hors_ligne and not cache:
        print("Erreur : --hors-ligne demande un cache (--cache DIR).", file=sys.stderr)
        return 2
    purges = purger_cache_google(cache)
    if purges:
        print("Cache Google : %d réponse(s) de plus de %d jours supprimée(s)." % (purges, GOOGLE_TTL_JOURS))
    ua = USER_AGENT + ((" ; contact : " + a.contact) if a.contact else "")
    http = Http(transport=transport or (TransportFixtures() if test else None), cache=cache,
                hors_ligne=a.hors_ligne, user_agent=ua, dormir=dormir)

    stats, erreurs = {}, []
    sirene, osm = [], []
    if "sirene" in sources:
        try:
            print("Sirene : interrogation de l'API Recherche d'entreprises (NAF %s)…" % ",".join(naf), file=sys.stderr)
            sirene = collecter_sirene(http, territoire, naf, a.avec_dirigeants, stats)
        except ErreurSource as e:
            erreurs.append(str(e))
            avertir(str(e))
    if "osm" in sources:
        try:
            print("OSM : requête Overpass (une seule requête, jusqu'à 3 minutes)…", file=sys.stderr)
            osm = collecter_osm(http, territoire, bbox=a.osm_bbox, stats=stats)
        except ErreurSource as e:
            erreurs.append(str(e))
            avertir(str(e))
        except ErreurEntree as e:
            print("Erreur : %s" % e, file=sys.stderr)
            return 2
    if not sirene and not osm:
        print("Erreur : aucune donnée collectée (%s)." % ("; ".join(erreurs) or "sources vides"), file=sys.stderr)
        return 1

    prospects = fusionner(sirene, osm, stats)
    for p in prospects:
        p["commune_nom"] = territoire["communes"].get(p.get("commune"), {}).get("nom", "")
        p["zone"] = zone_de(p, territoire)
        p["chaine"] = est_chaine(p["noms"] + [p["nom"]], p.get("marque"))
        calculer_score(p, territoire, aujourd_hui)

    if "google" in sources:
        candidats = sorted((p for p in prospects if not p["chaine"] or a.inclure_chaines),
                           key=lambda p: (-p["score"], p["nom"]))
        n = min(len(candidats), max(0, a.google_max))
        payant = max(0, n - GOOGLE_GRATUIT_MOIS)
        print("Google Places : jusqu'à %d requête(s). Coût estimé : 0 $ dans le seuil gratuit mensuel "
              "(~%d), puis ~%.0f $ / 1 000 (ici ~%.2f $ au-delà du seuil)."
              % (n, GOOGLE_GRATUIT_MOIS, GOOGLE_PRIX_1000, payant * GOOGLE_PRIX_1000 / 1000), file=sys.stderr)
        try:
            garde = enrichir_google(http, candidats, cle_google or "fixtures", n, cache, stats)
        except ErreurSource as e:
            avertir("Google Places abandonné : %s" % e)
            garde = candidats
        ids_garde = {id(p) for p in garde}
        ids_cand = {id(p) for p in candidats}
        prospects = [p for p in prospects if id(p) not in ids_cand or id(p) in ids_garde]
        for p in prospects:
            calculer_score(p, territoire, aujourd_hui)

    exclus_chaines = sum(1 for p in prospects if p["chaine"])
    if not a.inclure_chaines:
        prospects = [p for p in prospects if not p["chaine"]]
        exclus_chaines_aff = exclus_chaines
    else:
        exclus_chaines_aff = 0
    if test:
        for p in prospects:
            p["ids"] = ["test-" + i for i in p["ids"]]
            p["id"] = p["ids"][0]
    deja = 0
    if crm:
        marquer_crm(prospects, crm)
        deja = sum(1 for p in prospects if p["deja_dans_crm"])
    prospects.sort(key=lambda p: (-p["score"], p["nom"].lower(), p["id"]))

    sortie.mkdir(parents=True, exist_ok=True)
    verifier_expiration(sortie, aujourd_hui)
    date_collecte = aujourd_hui.isoformat()
    horodatage = dt.datetime.combine(aujourd_hui, dt.time(12, 0))
    a_importer = [p for p in prospects if not p.get("deja_dans_crm")]
    ecrire_csv(sortie / "prospects.csv", COLONNES_AUDIT + ["date_collecte"],
               [ligne_audit(p, i, date_collecte, horodatage, test) for i, p in enumerate(a_importer)])
    ecrire_csv(sortie / "prospects-complet.csv", COLONNES_COMPLET,
               [ligne_complete(p, territoire, date_collecte, test, a.avec_dirigeants) for p in prospects])
    for ligne in http.journal:
        print(ligne, file=sys.stderr)
    print(resume(prospects, territoire, stats, test, sortie, exclus_chaines_aff, deja))
    if erreurs:
        print("\nSources en erreur (résultat partiel) : " + " ; ".join(erreurs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
