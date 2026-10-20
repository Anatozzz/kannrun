"""Tests de tools/prospects.py, sans aucun accès réseau (transports simulés, fixtures fictives).

Lancement :  python3 -m unittest tools/test_prospects.py

Le format d'import de audit/ est vérifié en important RÉELLEMENT le CSV généré avec le code de
audit/audit.js (via node, s'il est installé). Sans node, une reproduction Python des règles du
parseur de audit.js prend le relais.
"""

from __future__ import annotations

import copy
import datetime as dt
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import urllib.parse
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent
sys.path.insert(0, str(ICI))

import prospects as P  # noqa: E402

FIX = ICI / "fixtures"
AUDIT_JS = RACINE / "audit" / "audit.js"
DATE_REF = "2026-10-20"
AUJ = dt.date(2026, 10, 20)
TERR = P.charger_territoire()


def fixture(nom):
    return json.loads((FIX / nom).read_text(encoding="utf-8"))


def silencieux(f, *a, **kw):
    with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()) as err:
        r = f(*a, **kw)
    return r, out.getvalue(), err.getvalue()


class FauxTransport:
    """Rejoue des réponses (statut, entêtes, corps) et note les requêtes."""

    def __init__(self, reponses):
        self.reponses = list(reponses)
        self.appels = []

    def __call__(self, methode, url, entetes, corps, delai):
        self.appels.append({"methode": methode, "url": url, "entetes": entetes, "corps": corps})
        if not self.reponses:
            raise AssertionError("requête inattendue : " + url)
        r = self.reponses.pop(0)
        if callable(r):
            r = r(methode, url, entetes, corps)
        statut, ent, corps_rep = r
        if not isinstance(corps_rep, bytes):
            corps_rep = json.dumps(corps_rep).encode("utf-8")
        return statut, ent, corps_rep


def http(transport, **kw):
    kw.setdefault("dormir", lambda s: None)
    return P.Http(transport=transport, **kw)


def lancer(*args, transport=None):
    return silencieux(P.main, list(args) + ["--date-ref", DATE_REF], transport=transport, dormir=lambda s: None)


# ---------------------------------------------------------------------------
class TestTerritoire(unittest.TestCase):
    def test_34_communes_grand_annecy(self):
        brut = json.loads((ICI / "grand_annecy_communes.json").read_text(encoding="utf-8"))
        self.assertEqual(brut["epci_siren"], "200066793")
        self.assertEqual(len(TERR["communes"]), 34)
        self.assertEqual(len({c["code_insee"] for c in brut["communes"]}), 34)
        self.assertIn("74010", TERR["communes"])
        self.assertTrue(brut["notes"], "le champ notes signale les incertitudes")
        for code in TERR["communes"]:
            self.assertRegex(code, r"^74\d{3}$")

    def test_anciens_codes_rattaches(self):
        self.assertEqual(P.commune_canonique("74011", TERR), "74010")  # Annecy-le-Vieux
        self.assertEqual(P.commune_canonique("74010", TERR), "74010")
        self.assertIsNone(P.commune_canonique("74225", TERR))          # Rumilly : hors territoire
        self.assertIsNone(P.commune_canonique("[NON-DIFFUSIBLE]", TERR))

    def test_communes_en_ligne_de_commande(self):
        t = P.charger_territoire("74010,74267")
        self.assertEqual(sorted(t["communes"]), ["74010", "74267"])
        with self.assertRaises(P.ErreurEntree):
            P.charger_territoire("/nexiste/pas.json")

    def test_zones_reconnues_par_audit(self):
        js = AUDIT_JS.read_text(encoding="utf-8")
        quartiers = re.findall(r'"([^"]+)"', re.search(r"var QUARTIERS = \[(.*?)\];", js, re.S).group(1))
        self.assertEqual(quartiers, P.QUARTIERS)
        for z in TERR["poids_zones"]:
            self.assertIn(z, quartiers)


# ---------------------------------------------------------------------------
class TestSirene(unittest.TestCase):
    def setUp(self):
        self.t = FauxTransport([(200, {}, fixture("exemple_sirene_page1.json")),
                                (200, {}, fixture("exemple_sirene_page2.json"))])
        self.stats = {}
        self.etabs = P.collecter_sirene(http(self.t), TERR, P.NAF_DEFAUT, stats=self.stats)
        self.par_siret = {e["siret"]: e for e in self.etabs}

    def test_parametres_conformes_a_la_doc(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.t.appels[0]["url"]).query)
        self.assertEqual(q["activite_principale"], ["56.10A,56.10C,56.30Z"])
        self.assertEqual(q["etat_administratif"], ["A"])
        self.assertEqual(q["per_page"], ["25"])
        self.assertEqual(q["limite_matching_etablissements"], ["100"])
        self.assertEqual(q["minimal"], ["true"])
        self.assertEqual(q["include"], ["matching_etablissements,complements"])
        self.assertEqual(len(q["code_commune"][0].split(",")), 34)
        self.assertEqual(self.t.appels[0]["entetes"]["User-Agent"], P.USER_AGENT)

    def test_pagination(self):
        pages = [urllib.parse.parse_qs(urllib.parse.urlparse(a["url"]).query)["page"][0] for a in self.t.appels]
        self.assertEqual(pages, ["1", "2"])
        self.assertEqual(self.stats["sirene_pages"], 2)
        self.assertIn("99000027600017", self.par_siret)  # résultat de la page 2

    def test_filtres_etat_activite_diffusion(self):
        self.assertNotIn("99000006000025", self.par_siret)        # établissement fermé (F)
        self.assertIn("99000006000017", self.par_siret)
        self.assertNotIn("99000007800012", self.par_siret)        # non diffusible
        self.assertNotIn("99000008600029", self.par_siret)        # activité 47.24Z
        self.assertEqual(self.stats["sirene_exclus_etablissement_ferme"], 1)
        self.assertEqual(self.stats["sirene_exclus_non_diffusible"], 1)
        self.assertEqual(self.stats["sirene_exclus_activite_etablissement"], 1)

    def test_filtre_communes(self):
        ul = copy.deepcopy(fixture("exemple_sirene_page1.json")["results"][0])
        ul["matching_etablissements"][0]["commune"] = "74225"   # Rumilly
        stats = {}
        self.assertEqual(list(P.extraire_etablissements(ul, TERR, set(P.NAF_DEFAUT), stats)), [])
        self.assertEqual(stats["sirene_exclus_hors_territoire"], 1)
        ul["matching_etablissements"][0]["commune"] = "74011"   # ancien code d'Annecy-le-Vieux
        self.assertEqual(list(P.extraire_etablissements(ul, TERR, set(P.NAF_DEFAUT), {}))[0]["commune"], "74010")

    def test_coordonnees_chaines_converties(self):
        e = self.par_siret["99000001100017"]
        self.assertAlmostEqual(e["lat"], 45.89851)
        self.assertEqual(e["noms"][0], "Le Fictif du Thiou")

    def test_entrepreneur_individuel_sans_nom_de_personne(self):
        e = self.par_siret["99000003700017"]
        self.assertTrue(e["ei"])
        self.assertEqual(e["noms"], ["Chez Jeannot Fictif"])
        self.assertEqual(e["denomination"], "")
        self.assertEqual(e["dirigeants"], "")

    def test_decoupage_au_dela_de_10000(self):
        trop = {"results": [], "total_results": 12000, "page": 1, "per_page": 25, "total_pages": 480}
        vide = {"results": [], "total_results": 0, "page": 1, "per_page": 25, "total_pages": 0}
        t = FauxTransport([(200, {}, trop)] + [(200, {}, vide)] * 2)
        terr = P.charger_territoire("74010,74267")
        P.collecter_sirene(http(t), terr, ["56.10A"])
        codes = [urllib.parse.parse_qs(urllib.parse.urlparse(a["url"]).query)["code_commune"][0] for a in t.appels]
        self.assertEqual(codes, ["74010,74267", "74010", "74267"])

    def test_epci(self):
        terr = P.charger_territoire(None, epci="200066793")
        vide = {"results": [], "total_results": 0, "page": 1, "per_page": 25, "total_pages": 0}
        t = FauxTransport([(200, {}, vide)])
        P.collecter_sirene(http(t), terr, ["56.10A"])
        q = urllib.parse.parse_qs(urllib.parse.urlparse(t.appels[0]["url"]).query)
        self.assertEqual(q["epci"], ["200066793"])
        self.assertNotIn("code_commune", q)


class TestHttp(unittest.TestCase):
    def test_429_retry_after_et_debit(self):
        pauses = []
        t = FauxTransport([(429, {"Retry-After": "3"}, b"{}"), (200, {}, {"ok": 1})])
        h = P.Http(transport=t, dormir=pauses.append)
        self.assertEqual(h.json("sirene", "GET", "https://x.test/a"), {"ok": 1})
        self.assertIn(3.0, pauses)

    def test_delai_minimal_entre_requetes(self):
        pauses, temps = [], [0.0]
        t = FauxTransport([(200, {}, {"n": 1}), (200, {}, {"n": 2})])
        h = P.Http(transport=t, dormir=pauses.append, horloge=lambda: temps[0])
        h.json("sirene", "GET", "https://x.test/1", delai_min=0.2)
        h.json("sirene", "GET", "https://x.test/2", delai_min=0.2)
        self.assertAlmostEqual(pauses[-1], 0.2)

    def test_erreur_definitive(self):
        t = FauxTransport([(400, {}, b'{"erreur":"Veuillez indiquer au moins un param\xc3\xa8tre"}')])
        with self.assertRaises(P.ErreurSource):
            http(t).json("sirene", "GET", "https://x.test/a")

    def test_cache_puis_hors_ligne(self):
        with tempfile.TemporaryDirectory() as d:
            t = FauxTransport([(200, {}, {"v": 1})])
            http(t, cache=d).json("osm", "POST", "https://x.test/i", corps_form={"data": "q"})
            h2 = http(FauxTransport([]), cache=d, hors_ligne=True)
            self.assertEqual(h2.json("osm", "POST", "https://x.test/i", corps_form={"data": "q"}), {"v": 1})
            with self.assertRaises(P.ErreurSource):
                h2.json("osm", "POST", "https://x.test/i", corps_form={"data": "autre"})


# ---------------------------------------------------------------------------
class TestOsm(unittest.TestCase):
    def setUp(self):
        self.stats = {}
        self.lieux = P.analyser_overpass(fixture("exemple_overpass.json"), TERR, stats=self.stats)
        self.par_nom = {l["noms"][0]: l for l in self.lieux}

    def test_requete_unique_par_communes(self):
        q = P.requete_overpass(TERR)
        self.assertIn('["ref:INSEE"~"^(', q)
        self.assertIn("74010", q)
        self.assertIn("foreach.communes->.c(", q)
        self.assertIn("restaurant|cafe|bar|fast_food|pub|ice_cream", q)
        self.assertIn("out center tags;", q)
        self.assertIn("[timeout:180]", q)
        t = FauxTransport([(200, {}, fixture("exemple_overpass.json"))])
        P.collecter_osm(http(t), TERR)
        self.assertEqual(len(t.appels), 1)
        self.assertEqual(t.appels[0]["methode"], "POST")
        self.assertTrue(t.appels[0]["corps"].startswith(b"data="))

    def test_bbox(self):
        q = P.requete_overpass(TERR, bbox=True)
        self.assertIn("(45.7,5.97,46.06,6.33)", q)

    def test_communes_et_champs(self):
        self.assertEqual(self.par_nom["Le Fictif du Thiou"]["commune"], "74010")
        self.assertEqual(self.par_nom["L'Auberge du Lac Fictif"]["commune"], "74275")
        self.assertEqual(self.par_nom["Le Café des Fixtures"]["telephone"], "04 00 00 00 09")
        self.assertEqual(P.telephone_fr("+41 22 000 00 00"), "+41 22 000 00 00")
        self.assertEqual(P.telephone_fr("0033450000000;+33 6 00 00 00 00"), "04 50 00 00 00")
        self.assertEqual(self.par_nom["Crêperie Test"]["menu"], "https://exemple.invalid/creperie/menu")
        self.assertIsNone(self.par_nom["Le Fictif du Thiou"]["site"])
        self.assertAlmostEqual(self.par_nom["Glaces Imaginaires"]["lat"], 45.9027)  # way : centre
        self.assertEqual(self.par_nom["Brioche Dorée"]["marque"], "Brioche Dorée")

    def test_sans_nom_et_doublon_de_limite(self):
        self.assertEqual(self.stats["osm_exclus_sans_nom"], 1)
        self.assertEqual(sum(1 for l in self.lieux if l["noms"][0] == "Le Petit Fictif"), 1)


# ---------------------------------------------------------------------------
class TestFusion(unittest.TestCase):
    def test_normalisation(self):
        self.assertEqual(P.normaliser_nom("SARL Restaurant Le Fictif du Thiou"), "fictif thiou")
        self.assertEqual(P.normaliser_nom("Pizzeria Démo"), P.normaliser_nom("PIZZERIA DEMO"))
        self.assertEqual(P.normaliser_nom("Le Bistrot"), "bistrot")  # jamais vide
        self.assertGreaterEqual(P.similarite("L'Auberge du Lac Fictif", "AUBERGE DU LAC FICTIF"), 0.99)
        self.assertLess(P.similarite("Bar Voisin Exemple", "Le Fictif du Thiou"), 0.6)

    def lieu(self, nom, lat, lon, commune="74010", **kw):
        return dict({"noms": [nom], "lat": lat, "lon": lon, "commune": commune}, **kw)

    def test_regles_distance_nom(self):
        a = self.lieu("Le Fictif du Thiou", 45.89851, 6.12552)
        self.assertIsNotNone(P.score_appariement(a, self.lieu("Fictif du Thiou", 45.89860, 6.12560)))  # 12 m
        self.assertIsNone(P.score_appariement(a, self.lieu("Bar Voisin Exemple", 45.89860, 6.12560)))
        self.assertIsNone(P.score_appariement(a, self.lieu("Fictif Thiou Autre", 45.8995, 6.1255)))  # 110 m, nom moyen
        self.assertIsNotNone(P.score_appariement(a, self.lieu("Le Fictif du Thiou", 45.8995, 6.1255)))  # 110 m, même nom
        self.assertIsNone(P.score_appariement(a, self.lieu("Le Fictif du Thiou", 45.89851, 6.12552, "74267")))

    def test_un_pour_un(self):
        s = [self.lieu("La Table", 45.9, 6.13), self.lieu("La Table", 45.9003, 6.13)]
        o = [self.lieu("La Table", 45.90001, 6.13)]
        self.assertEqual(len(P.apparier(s, o)), 1)

    def test_fusion_fixtures(self):
        sirene = P.collecter_sirene(http(FauxTransport([(200, {}, fixture("exemple_sirene_page1.json")),
                                                        (200, {}, fixture("exemple_sirene_page2.json"))])),
                                    TERR, P.NAF_DEFAUT)
        osm = P.analyser_overpass(fixture("exemple_overpass.json"), TERR)
        stats = {}
        pr = P.fusionner(sirene, osm, stats)
        par_nom = {p["nom"]: p for p in pr}
        self.assertEqual(par_nom["Le Fictif du Thiou"]["sources"], ["sirene", "osm"])
        self.assertEqual(par_nom["Le Fictif du Thiou"]["id"], "sirene-99000001100017")
        self.assertEqual(par_nom["Le Fictif du Thiou"]["ids"], ["sirene-99000001100017", "osm-n-990000001"])
        self.assertEqual(par_nom["Bar Voisin Exemple"]["sources"], ["sirene", "osm"])
        self.assertEqual(par_nom["Pizzeria Démo"]["sources"], ["sirene", "osm"])
        self.assertEqual(par_nom["Le Petit Fictif"]["sources"], ["osm"])
        self.assertEqual(par_nom["Le Petit Fictif"]["id"], "osm-n-990000050")
        # reprise de fonds à Sévrier : un seul prospect, le SIRET le plus récent
        guinguettes = [p for p in pr if p["nom"] == "La Guinguette Exemple"]
        self.assertEqual(len(guinguettes), 1)
        self.assertEqual(guinguettes[0]["siret"], "99000012800017")
        self.assertEqual(stats["doublons_internes_sirene"], 1)
        # EI sans enseigne : jamais le nom de la personne
        sans = [p for p in pr if p["siret"] == "99000004500017"][0]
        self.assertTrue(sans["nom"].startswith("Établissement sans enseigne"))
        self.assertNotIn("MARTIN", json.dumps(sans, ensure_ascii=False).upper())


# ---------------------------------------------------------------------------
class TestZones(unittest.TestCase):
    def z(self, lat, lon, commune="74010", cp=None):
        return P.zone_de({"lat": lat, "lon": lon, "commune": commune, "code_postal": cp}, TERR)

    def test_annecy(self):
        self.assertEqual(self.z(45.8986, 6.1270), "Vieille ville")      # Palais de l'Isle
        self.assertEqual(self.z(45.9015, 6.1345), "Bords du lac / Pâquier")  # Pâquier
        self.assertEqual(self.z(45.9020, 6.1220), "Centre / gare")      # gare
        self.assertEqual(self.z(45.9200, 6.1450, cp="74940"), "Annecy-le-Vieux")
        self.assertEqual(self.z(45.9250, 6.1600), "Annecy-le-Vieux")    # sans code postal
        self.assertEqual(self.z(45.8770, 6.0880, cp="74600"), "Autre")  # Seynod
        self.assertEqual(self.z(None, None, cp="74940"), "Annecy-le-Vieux")

    def test_autres_communes(self):
        self.assertEqual(self.z(45.84, 6.21, "74275"), "Talloires / rive est")
        self.assertEqual(self.z(45.86, 6.14, "74267"), "Sévrier / rive ouest")
        self.assertEqual(self.z(45.81, 6.01, "74002"), "Autre")
        # un polygone d'Annecy ne s'applique pas à une autre commune
        self.assertEqual(self.z(45.8986, 6.1270, "74213"), "Autre")


# ---------------------------------------------------------------------------
class TestChaines(unittest.TestCase):
    def test_detectees(self):
        for nom in ["MCDONALD'S", "Mc Donald's Annecy", "McDonalds", "BURGER KING", "KFC Seynod",
                    "Brioche Dorée", "BRIOCHE DOREE", "SAS Buffalo Grill", "Del Arte", "Domino's Pizza",
                    "Starbucks Coffee", "Paul", "Courtepaille", "O'Tacos"]:
            self.assertTrue(P.est_chaine([nom]), nom)

    def test_pas_de_faux_positif(self):
        for nom in ["Chez Paul Fictif", "Le Quick Lunch Fictif", "La Paulette", "Le Fictif du Thiou",
                    "Au Bureau de Tabac Fictif"]:
            self.assertIsNone(P.est_chaine([nom]), nom)

    def test_marque_osm(self):
        self.assertEqual(P.est_chaine(["Un nom quelconque"], "Q2925147"), "Q2925147")


# ---------------------------------------------------------------------------
class TestScore(unittest.TestCase):
    def base(self, **kw):
        p = {"zone": "Vieille ville", "nb_avis": None, "note": None, "site_google": None, "site_osm": None,
             "google_consulte": False, "place_id": None, "a_osm": False, "menu_osm": None,
             "date_creation": None, "types": [], "chaine": None}
        p.update(kw)
        P.calculer_score(p, TERR, AUJ)
        return p

    def test_bareme_complet(self):
        p = self.base(nb_avis=850, note=4.2, google_consulte=True, place_id="x", a_osm=True,
                      date_creation="2025-09-15", types=["traditionnel"])
        self.assertEqual(p["score"], 25 + 15 + 15 + 10 + 10 + 15 + 10)
        self.assertTrue(p["prospect_chaud"])
        self.assertIn("prospect chaud", p["score_detail"])

    def test_valeurs_inconnues(self):
        p = self.base(zone="Autre")
        self.assertEqual(p["score"], 0 + 5 + 5 + 3 + 5 + 0 + 0)

    def test_note_et_avis(self):
        self.assertEqual(self.base(note=3.8)["score"] - self.base(note=4.8)["score"], 15 - 3)
        self.assertEqual(self.base(note=4.6)["score"] - self.base(note=3.0)["score"], 6 - 4)
        self.assertEqual(self.base(nb_avis=9)["score"] - self.base(nb_avis=250)["score"], 0 - 12)

    def test_site_menu_creation_type(self):
        self.assertEqual(self.base(site_osm="https://x", a_osm=True, menu_osm="https://m")["score"],
                         25 + 5 + 5 + 0 + 0)
        self.assertEqual(self.base(date_creation="2024-06-01")["score"] - self.base()["score"], 5)
        self.assertEqual(self.base(date_creation="2010-01-01")["score"], self.base()["score"])
        self.assertEqual(self.base(types=["rapide", "traditionnel"])["type"], "traditionnel")
        self.assertGreater(self.base(types=["traditionnel"])["score"], self.base(types=["rapide"])["score"])

    def test_chaine_penalisee_et_bornes(self):
        p = self.base(chaine="KFC", zone="Autre")
        self.assertEqual(p["score"], 0)
        self.assertIn("chaîne", p["score_detail"])
        p = self.base(nb_avis=850, note=4.2, google_consulte=True, place_id="x", a_osm=True,
                      date_creation="2025-09-15", types=["traditionnel"])
        self.assertLessEqual(p["score"], 100)

    def test_bareme_documente_en_tete(self):
        self.assertIn("BARÈME DU SCORE DE PRIORITÉ", P.__doc__)
        self.assertIn("moins de 18 mois", P.__doc__)


# ---------------------------------------------------------------------------
class TestGoogle(unittest.TestCase):
    def prospect(self):
        return {"id": "sirene-1", "ids": ["sirene-1"], "nom": "Le Fictif du Thiou", "noms": ["Le Fictif du Thiou"],
                "adresse": "2 QUAI FICTIF 74000 ANNECY", "lat": 45.89851, "lon": 6.12552, "sources": ["sirene"]}

    def test_fieldmask_minimal_et_cle_hors_cache(self):
        with tempfile.TemporaryDirectory() as d:
            t = FauxTransport([(200, {}, fixture("exemple_places.json")["reponses"][0]["reponse"])])
            p = self.prospect()
            P.enrichir_google(http(t, cache=d), [p], "CLE-SECRETE", 10, d)
            e = t.appels[0]["entetes"]
            self.assertEqual(e["X-Goog-FieldMask"], "places.id,places.displayName,places.location,places.rating,"
                                                    "places.userRatingCount,places.websiteUri,places.googleMapsUri")
            self.assertEqual(e["X-Goog-Api-Key"], "CLE-SECRETE")
            corps = json.loads(t.appels[0]["corps"])
            self.assertEqual(corps["locationBias"]["circle"]["radius"], 200.0)
            self.assertEqual(p["place_id"], "ChIJFICTIF0000000000001")
            self.assertEqual((p["note"], p["nb_avis"]), (4.2, 850))
            self.assertIn("google", p["sources"])
            tout = "".join(f.read_text(encoding="utf-8") for f in Path(d).rglob("*.json"))
            self.assertNotIn("CLE-SECRETE", tout)
            index = json.loads((Path(d) / "google_place_ids.json").read_text(encoding="utf-8"))
            self.assertEqual(index, {"sirene-1": "ChIJFICTIF0000000000001"})
            # 2e passage : place_id connu -> Place Details (pas de nouvelle Text Search)
            t2 = FauxTransport([(200, {}, fixture("exemple_places.json")["reponses"][0]["reponse"]["places"][0])])
            for f in (Path(d) / "google").glob("*.json"):
                f.unlink()
            P.enrichir_google(http(t2, cache=d), [self.prospect()], "CLE", 10, d)
            self.assertTrue(t2.appels[0]["url"].startswith(P.URL_PLACES_DETAILS))
            self.assertEqual(t2.appels[0]["entetes"]["X-Goog-FieldMask"], P.GOOGLE_FIELDMASK_DETAILS)

    def test_candidat_trop_loin_ignore(self):
        p = self.prospect()
        loin = {"id": "X", "displayName": {"text": "Le Fictif du Thiou"}, "location": {"latitude": 45.92, "longitude": 6.12552}}
        self.assertIsNone(P.choisir_place(p, [loin]))

    def test_expiration_cache_30_jours(self):
        with tempfile.TemporaryDirectory() as d:
            h = http(FauxTransport([(200, {}, {"places": []})]), cache=d)
            h.json("google", "POST", P.URL_PLACES_TEXT, corps_json={"textQuery": "x"})
            P.sauver_index_place_ids(d, {"a": "b"})
            f = next((Path(d) / "google").glob("*.json"))
            entree = json.loads(f.read_text(encoding="utf-8"))
            entree["date"] = "2026-09-01T10:00:00+00:00"
            f.write_text(json.dumps(entree), encoding="utf-8")
            n = P.purger_cache_google(d, dt.datetime(2026, 10, 20, tzinfo=dt.timezone.utc))
            self.assertEqual(n, 1)
            self.assertFalse(f.exists())
            self.assertTrue((Path(d) / "google_place_ids.json").exists())  # place_id : conservés

    def test_cle_invalide_arrete(self):
        t = FauxTransport([(403, {}, b'{"error":{"code":403,"status":"PERMISSION_DENIED"}}')])
        with self.assertRaises(P.ErreurSource):
            P.enrichir_google(http(t), [self.prospect()], "MAUVAISE", 10)

    def test_google_sans_cle_refuse(self):
        r, _, err = lancer("--sources", "sirene,google", "--sortie", tempfile.mkdtemp())
        self.assertEqual(r, 2)
        self.assertIn("GOOGLE_MAPS_API_KEY", err)


# ---------------------------------------------------------------------------
NOEUD = shutil.which("node")
HARNAIS_JS = r"""
const fs = require("fs"), vm = require("vm");
const [audit, csv1, csv2] = process.argv.slice(2);
const store = {};
const ctx = { console, document: { readyState: "loading", addEventListener() {} } };
ctx.window = { localStorage: { getItem: k => (k in store ? store[k] : null),
  setItem: (k, v) => { store[k] = String(v); }, removeItem: k => { delete store[k]; } } };
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(audit, "utf8"), ctx);
const A = ctx.window.PolyglotteAudit;
// Même logique de fusion que importer() dans audit.js
function importer(liste, texte) {
  const r = A.depuisCsv(texte); let ajout = 0, maj = 0;
  r.prospects.forEach(p => { const i = liste.findIndex(x => x.id === p.id);
    if (i >= 0) { liste[i] = p; maj++; } else { liste.push(p); ajout++; } });
  return { ajout, maj, ignores: r.ignores };
}
const liste = [];
const r1 = importer(liste, fs.readFileSync(csv1, "utf8"));
const r2 = importer(liste, fs.readFileSync(csv2, "utf8"));
const entete = A.versCsv([]).replace(/^﻿/, "").split("\r\n")[0].split(";");
const ordre = liste.slice().sort((a, b) => (b.majLe || "").localeCompare(a.majLe || "")).map(p => p.id);
console.log(JSON.stringify({ r1, r2, entete, ordre, statuts: A.STATUTS, prospects: liste }));
"""


def analyser_csv_comme_audit(texte):
    """Reproduction Python de analyserCsv() de audit.js (repli sans node)."""
    texte = texte.lstrip("﻿")
    premiere = texte.split("\n")[0]
    sep = ";" if len(premiere.split(";")) >= len(premiere.split(",")) else ","
    lignes, ligne, cell, guill, i = [], [], "", False, 0
    while i < len(texte):
        ch = texte[i]
        if guill:
            if ch == '"':
                if i + 1 < len(texte) and texte[i + 1] == '"':
                    cell += '"'
                    i += 1
                else:
                    guill = False
            else:
                cell += ch
        elif ch == '"':
            guill = True
        elif ch == sep:
            ligne.append(cell)
            cell = ""
        elif ch in "\r\n":
            if ch == "\r" and i + 1 < len(texte) and texte[i + 1] == "\n":
                i += 1
            ligne.append(cell)
            cell = ""
            if any(ligne):
                lignes.append(ligne)
            ligne = []
        else:
            cell += ch
        i += 1
    ligne.append(cell)
    if any(ligne):
        lignes.append(ligne)
    return sep, lignes


class TestSortiesEtImportAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dossier = Path(tempfile.mkdtemp())
        cls.code, cls.out, cls.err = lancer("--fixtures", "--sortie", str(cls.dossier))
        cls.csv = (cls.dossier / "prospects.csv").read_bytes().decode("utf-8")
        cls.complet = (cls.dossier / "prospects-complet.csv").read_bytes().decode("utf-8")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.dossier, ignore_errors=True)

    def test_execution_et_resume(self):
        self.assertEqual(self.code, 0, self.err)
        for morceau in ["DONNÉES DE TEST", "Par commune", "Par zone", "Par activité", "Top 20",
                        "Prospects retenus : 26", "chaînes exclues : 2"]:
            self.assertIn(morceau, self.out)

    def test_colonnes_identiques_a_audit_js(self):
        js = AUDIT_JS.read_text(encoding="utf-8")
        bloc = re.search(r"var COLONNES = \[(.*?)\];", js, re.S).group(1)
        self.assertEqual(re.findall(r'"([^"]+)"', bloc), P.COLONNES_AUDIT)
        sep, lignes = analyser_csv_comme_audit(self.csv)
        self.assertEqual(sep, ";")
        self.assertTrue(self.csv.startswith("﻿"))
        self.assertIn("\r\n", self.csv)
        self.assertEqual(lignes[0][:21], P.COLONNES_AUDIT)
        self.assertEqual(lignes[0][21], "date_collecte")
        self.assertTrue(all(len(l) == 22 for l in lignes))

    def test_contenu_trie_et_marque_test(self):
        _, lignes = analyser_csv_comme_audit(self.csv)
        tete, corps = lignes[0], lignes[1:]
        rows = [dict(zip(tete, l)) for l in corps]
        self.assertEqual(len(rows), 26)
        self.assertTrue(all(r["statut"] == "À visiter" for r in rows))
        self.assertTrue(all(r["nom"].startswith("[TEST] ") for r in rows))
        self.assertTrue(all(r["id"].startswith("test-") for r in rows))
        self.assertTrue(all(r["quartier"] in P.QUARTIERS for r in rows))
        self.assertTrue(all(r["date_collecte"] == DATE_REF for r in rows))
        scores = [int(re.search(r"Priorité (\d+)/100", r["notes"]).group(1)) for r in rows]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertEqual(rows[0]["nom"], "[TEST] La Table Imaginaire")
        self.assertEqual(rows[0]["note"], "4,4")
        self.assertNotIn("Brioche", self.csv)
        self.assertNotIn("MCDONALD", self.csv.upper())

    def test_rgpd_pas_de_nom_de_personne(self):
        for texte in (self.csv, self.complet):
            self.assertNotIn("DUPONT", texte.upper())
            self.assertNotIn("MARTIN-EXEMPLE", texte.upper())
        self.assertIn("date_collecte", self.complet.splitlines()[0])

    def test_colonnes_completes(self):
        _, lignes = analyser_csv_comme_audit(self.complet)
        for c in ["siret", "naf", "date_creation", "adresse", "lat", "lon", "site", "telephone", "osm_id",
                  "place_id", "note", "nb_avis", "zone", "score", "score_detail", "sources", "date_collecte"]:
            self.assertIn(c, lignes[0])
        rows = [dict(zip(lignes[0], l)) for l in lignes[1:]]
        thiou = [r for r in rows if r["nom"] == "Le Fictif du Thiou"][0]
        self.assertEqual(thiou["sources"], "sirene+osm+google")
        self.assertEqual(thiou["telephone"], "04 00 00 00 01")
        self.assertEqual(thiou["donnees"], "TEST (établissement fictif)")

    @unittest.skipUnless(NOEUD, "node absent : import vérifié par la reproduction Python des règles")
    def test_import_reel_avec_audit_js(self):
        with tempfile.TemporaryDirectory() as d:
            harnais = Path(d) / "harnais.js"
            harnais.write_text(HARNAIS_JS, encoding="utf-8")
            csv1 = self.dossier / "prospects.csv"
            # 2e génération, plus tard : la réimportation doit FUSIONNER (mêmes ids), pas dupliquer
            d2 = Path(d) / "run2"
            code, _, err = lancer("--fixtures", "--sortie", str(d2))
            self.assertEqual(code, 0, err)
            r = subprocess.run([NOEUD, str(harnais), str(AUDIT_JS), str(csv1), str(d2 / "prospects.csv")],
                               capture_output=True, text=True, timeout=60)
            self.assertEqual(r.returncode, 0, r.stderr)
            res = json.loads(r.stdout)
        self.assertEqual(res["entete"], P.COLONNES_AUDIT)
        self.assertEqual(res["r1"], {"ajout": 26, "maj": 0, "ignores": 0})
        self.assertEqual(res["r2"], {"ajout": 0, "maj": 26, "ignores": 0})
        self.assertEqual(len(res["prospects"]), 26)
        self.assertEqual(res["statuts"][0], P.STATUT_INITIAL)
        par_id = {p["id"]: p for p in res["prospects"]}
        p = par_id["test-sirene-99000002900017"]
        self.assertEqual(p["statut"], "À visiter")
        self.assertEqual(p["quartier"], "Bords du lac / Pâquier")
        self.assertEqual(p["note"], "4,4")
        self.assertEqual(p["totalAvis"], "120")
        self.assertIn("Priorité 93/100", p["notes"])
        self.assertEqual(p["creeLe"], "2026-10-20T12:00:00.000Z")
        # l'ordre du pipeline (majLe décroissant) suit le score
        _, lignes = analyser_csv_comme_audit(self.csv)
        self.assertEqual(res["ordre"], [l[0] for l in lignes[1:]])
        site = [x for x in res["prospects"] if x["nom"] == "[TEST] Le Café des Fixtures"][0]
        self.assertIs(site["site"], True)

    def test_crm_existants_exclus(self):
        with tempfile.TemporaryDirectory() as d:
            export = Path(d) / "export.csv"
            # export de audit/ : un prospect importé auparavant (id OSM) et une saisie manuelle
            export.write_text("﻿" + ";".join(P.COLONNES_AUDIT) + "\r\n" +
                              "test-osm-n-990000001;Fictif Thiou;Vieille ville;;;;;;;aucun;non;non;non;non;non;Démo;;0;;;\r\n"
                              "p-abc123;LA TABLE IMAGINAIRE;Bords du lac / Pâquier;;;;;;;aucun;non;non;non;non;non;Audit remis;;0;;;\r\n",
                              encoding="utf-8")
            code, out, err = lancer("--fixtures", "--sortie", d, "--crm", str(export))
            self.assertEqual(code, 0, err)
            self.assertIn("déjà dans le pipeline : 2", out)
            texte = (Path(d) / "prospects.csv").read_bytes().decode("utf-8")
            self.assertNotIn("Table Imaginaire", texte)
            self.assertNotIn("Fictif du Thiou;", texte)
            self.assertEqual(texte.count("\r\n"), 1 + 24)
            complet = (Path(d) / "prospects-complet.csv").read_text(encoding="utf-8")
            self.assertIn("p-abc123", complet)

    def test_avec_dirigeants(self):
        ul = fixture("exemple_sirene_page1.json")["results"][2]
        ul = dict(ul, dirigeants=[{"nom": "DUPONT-FICTIF", "prenoms": "Jean", "qualite": "Entrepreneur",
                                   "type_dirigeant": "personne physique"}])
        sans = list(P.extraire_etablissements(ul, TERR, set(P.NAF_DEFAUT), {}))[0]
        avec = list(P.extraire_etablissements(ul, TERR, set(P.NAF_DEFAUT), {}, avec_dirigeants=True))[0]
        self.assertEqual(sans["dirigeants"], "")
        self.assertIn("DUPONT-FICTIF Jean", avec["dirigeants"])
        _, _, err = lancer("--fixtures", "--sortie", tempfile.mkdtemp(), "--avec-dirigeants")
        self.assertIn("données personnelles", err)

    def test_inclure_chaines(self):
        with tempfile.TemporaryDirectory() as d:
            code, out, _ = lancer("--fixtures", "--sortie", d, "--inclure-chaines")
            self.assertEqual(code, 0)
            texte = (Path(d) / "prospects-complet.csv").read_text(encoding="utf-8")
            self.assertIn("McDonald's", texte)
            self.assertIn("chaîne « McDonald's » -40", texte)

    def test_cellule_anti_formule(self):
        self.assertEqual(P.cellule("+33 4 50"), "'+33 4 50")
        self.assertEqual(P.cellule("-12"), "-12")
        self.assertEqual(P.cellule('a;"b"'), '"a;""b"""')

    def test_avertissement_expiration_google(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "prospects-complet.csv").write_text(
                "﻿id;note;nb_avis;date_collecte\r\nx;4,2;100;2026-08-01\r\n", encoding="utf-8")
            _, _, err = silencieux(P.verifier_expiration, d, AUJ)
            self.assertIn("plus de 30 jours", err)


class TestCacheEtHorsLigne(unittest.TestCase):
    def test_hors_ligne_rejoue_le_cache(self):
        with tempfile.TemporaryDirectory() as d:
            reseau = P.TransportFixtures()
            code, _, err = lancer("--sources", "sirene,osm", "--sortie", d, transport=reseau)
            self.assertEqual(code, 0, err)
            self.assertEqual(len(reseau.appels), 3)  # 2 pages Sirene + 1 Overpass
            premier = (Path(d) / "prospects.csv").read_text(encoding="utf-8")
            code, _, err = lancer("--sources", "sirene,osm", "--sortie", d, "--hors-ligne",
                                  transport=FauxTransport([]))
            self.assertEqual(code, 0, err)
            self.assertEqual((Path(d) / "prospects.csv").read_text(encoding="utf-8"), premier)

    def test_hors_ligne_sans_cache_echoue_proprement(self):
        with tempfile.TemporaryDirectory() as d:
            code, _, err = lancer("--sortie", d, "--hors-ligne", transport=FauxTransport([]))
            self.assertEqual(code, 1)
            self.assertIn("absente du cache", err)

    def test_une_source_seule(self):
        with tempfile.TemporaryDirectory() as d:
            code, out, _ = lancer("--sources", "osm", "--sortie", d, "--sans-cache", transport=P.TransportFixtures())
            self.assertEqual(code, 0)
            self.assertIn("Sources : osm", out)

    def test_options_invalides(self):
        d = tempfile.mkdtemp()
        self.assertEqual(lancer("--sources", "pagesjaunes", "--sortie", d)[0], 2)
        self.assertEqual(lancer("--naf", "5610A", "--sortie", d)[0], 2)


class TestGitignore(unittest.TestCase):
    def test_prospects_ignores(self):
        lignes = (RACINE / ".gitignore").read_text(encoding="utf-8").splitlines()
        self.assertIn("prospects/", lignes)


if __name__ == "__main__":
    unittest.main()
