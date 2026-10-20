"""Fonctions communes aux outils IA de Polyglotte (appel Claude en sortie JSON structurée).

Le SDK `anthropic` n'est importé qu'au moment d'un vrai appel : `--dry-run` et les
tests fonctionnent sans le paquet ni la clé API.
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass, field

# Le Haiku le plus récent (id vérifié dans la documentation Claude API, octobre 2026).
MODELE_DEFAUT = "claude-haiku-5-5"

# Prix publics en USD par million de tokens (entrée, sortie), prompts <= 100 000 tokens.
# Source : https://platform.claude.com/docs/en/about-claude/pricing (consultée le 2026-10-20).
PRIX_USD_MTOK = {
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-haiku-4-5": (1.00, 5.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-opus-5-5": (4.00, 20.00),
}

EFFORTS = ("low", "medium", "high")


class ErreurFatale(Exception):
    """Erreur qui doit arrêter tout le traitement (clé absente ou invalide, modèle inconnu)."""


class ErreurIA(Exception):
    """Échec pour un élément (refus, requête invalide, JSON inexploitable après réessais)."""


@dataclass
class Consommation:
    entree: int = 0
    sortie: int = 0
    appels: int = 0
    details: list = field(default_factory=list)

    def ajouter(self, usage) -> None:
        if usage is None:
            return
        self.entree += int(getattr(usage, "input_tokens", 0) or 0)
        self.sortie += int(getattr(usage, "output_tokens", 0) or 0)
        self.appels += 1

    def cout_usd(self, modele: str):
        prix = PRIX_USD_MTOK.get(modele)
        if not prix:
            return None
        return self.entree / 1e6 * prix[0] + self.sortie / 1e6 * prix[1]

    def resume(self, modele: str) -> str:
        cout = self.cout_usd(modele)
        txt = f"{self.appels} appel(s) API, {self.entree} tokens en entrée, {self.sortie} en sortie"
        if cout is not None:
            txt += f", coût estimé {cout:.4f} USD"
        return txt


def creer_client():
    """Crée le client Anthropic. La clé est lue dans ANTHROPIC_API_KEY."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise ErreurFatale(
            "Variable d'environnement ANTHROPIC_API_KEY absente. "
            "Exportez votre clé (export ANTHROPIC_API_KEY=...) ou utilisez --dry-run."
        )
    try:
        import anthropic  # import tardif : inutile en --dry-run
    except ImportError as exc:  # pragma: no cover - dépend de l'environnement
        raise ErreurFatale("Paquet `anthropic` introuvable : pip install -r tools/requirements.txt") from exc
    # Le SDK réessaie déjà 429 / 5xx / erreurs réseau ; on monte à 4 tentatives.
    return anthropic.Anthropic(max_retries=4, timeout=120.0)


def _classer_erreur(exc: Exception) -> str:
    """Renvoie 'fatale', 'reessai' ou 'element' selon le type d'erreur du SDK."""
    try:
        import anthropic
    except ImportError:  # sans SDK : on se base sur le code HTTP éventuel
        code = getattr(exc, "status_code", None)
        if code in (401, 403, 404):
            return "fatale"
        if code == 429 or (isinstance(code, int) and code >= 500):
            return "reessai"
        return "element"
    if isinstance(exc, (anthropic.AuthenticationError, anthropic.PermissionDeniedError, anthropic.NotFoundError)):
        return "fatale"
    if isinstance(exc, anthropic.BadRequestError):
        return "element"
    if isinstance(exc, anthropic.RateLimitError):
        return "reessai"
    if isinstance(exc, anthropic.APIStatusError):
        return "reessai" if exc.status_code >= 500 else "element"
    if isinstance(exc, (anthropic.APIConnectionError, anthropic.APITimeoutError)):
        return "reessai"
    return "inconnue"


def texte_reponse(message) -> str:
    """Concatène les blocs `text` (le modèle peut renvoyer d'abord des blocs `thinking`)."""
    return "".join(getattr(b, "text", "") for b in (message.content or []) if getattr(b, "type", "") == "text")


def appeler_json(
    client,
    *,
    modele: str,
    systeme: str,
    utilisateur: str,
    schema: dict,
    valider=None,
    effort: str = "medium",
    max_tokens: int = 4000,
    tentatives: int = 3,
    conso: Consommation | None = None,
    attente_base: float = 2.0,
    journal=None,
):
    """Appelle Claude avec une sortie JSON contrainte par `schema`.

    `valider(data) -> list[str]` renvoie les problèmes de fond (longueur, ids manquants…) ;
    s'il y en a, on relance une NOUVELLE requête en ajoutant les remarques au message.
    Retourne (data, problemes_restants). Lève ErreurFatale ou ErreurIA.
    """
    journal = journal or (lambda m: print(m, file=sys.stderr))
    remarques: list[str] = []
    dernier = None
    derniers_problemes: list[str] = []
    for essai in range(1, tentatives + 1):
        contenu = utilisateur
        if remarques:
            contenu += (
                "\n\n<corrections>\nUne proposition précédente ne respectait pas ces consignes, corrige-les :\n- "
                + "\n- ".join(remarques)
                + "\n</corrections>"
            )
        try:
            msg = client.messages.create(
                model=modele,
                max_tokens=max_tokens,
                system=systeme,
                messages=[{"role": "user", "content": contenu}],
                output_config={
                    "effort": effort,
                    "format": {"type": "json_schema", "schema": schema},
                },
            )
        except Exception as exc:  # classement explicite ci-dessous
            genre = _classer_erreur(exc)
            if genre == "fatale":
                raise ErreurFatale(f"Erreur API non récupérable : {exc}") from exc
            if genre == "reessai" and essai < tentatives:
                delai = attente_base * (2 ** (essai - 1))
                journal(f"  … erreur temporaire ({type(exc).__name__}), nouvel essai dans {delai:.0f} s")
                time.sleep(delai)
                continue
            raise ErreurIA(f"{type(exc).__name__} : {exc}") from exc

        if conso is not None:
            conso.ajouter(getattr(msg, "usage", None))

        arret = getattr(msg, "stop_reason", None)
        if arret == "refusal":
            raise ErreurIA("le modèle a refusé de traiter cet élément (stop_reason=refusal)")
        if arret == "max_tokens":
            max_tokens = min(max_tokens * 2, 32000)
            journal(f"  … réponse tronquée, nouvel essai avec max_tokens={max_tokens}")
            continue

        brut = texte_reponse(msg)
        try:
            data = json.loads(brut)
        except (json.JSONDecodeError, TypeError):
            remarques = ["la réponse doit être un JSON valide conforme au schéma"]
            journal("  … JSON invalide, nouvel essai")
            continue

        dernier = data
        derniers_problemes = list(valider(data)) if valider else []
        if not derniers_problemes:
            return data, []
        remarques = derniers_problemes
        journal("  … à corriger : " + " ; ".join(derniers_problemes))

    if dernier is None:
        raise ErreurIA(f"aucune réponse exploitable après {tentatives} essai(s)")
    return dernier, derniers_problemes
