# Polyglotte

**Votre restaurant parle la langue de chaque client.**

Side project lancé à Annecy : un service clé en main pour les restaurants indépendants. Un humain du coin, aidé par l'IA, fait le travail à la place du restaurateur :

- réponses aux avis Google dans la langue du client ;
- menu QR multilingue avec les 14 allergènes réglementaires ;
- fiche Google optimisée.

Investissement de départ inférieur à 150 €. Premiers revenus possibles dès la première semaine. Le concept se reproduit dans toute ville touristique.

## Pourquoi ce projet

| Constat | Chiffre | Source |
|---|---|---|
| Clientèle étrangère à Annecy (été 2025) | 44 % | Sources du Lac |
| Visiteurs par an | 2,5 à 3 millions | Office de tourisme, via TourMag |
| TPE-PME qui utilisent l'IA | 40 % | France Num 2026 |
| … mais qui paient un outil | 19 % | France Num 2026 |

Les restaurateurs veulent le **résultat** de l'IA, pas un logiciel de plus. Les concurrents nationaux (Malou, Partoo) vendent des logiciels. Polyglotte vend un service fait sur place, par quelqu'un qu'on peut rencontrer.

Le détail et les sources sont dans [`docs/recherche.md`](docs/recherche.md).

## L'offre

| Offre | Prix | Contenu |
|---|---|---|
| Audit | gratuit | rapport A4 imprimé, remis en main propre |
| Pack Démarrage | 290 € (**145 €** pour les 10 premiers restaurants) | fiche Google optimisée, menu QR en 5 langues, réponse aux 30 derniers avis, 10 chevalets QR |
| Abonnement Sérénité | 59 €/mois sans engagement (590 €/an) | réponse à chaque avis sous 48 h, mises à jour du menu, 4 publications Google par mois, rapport mensuel |

## Chiffres clés (business plan, scénario central)

| | 12 mois |
|---|---|
| Investissement de départ | ~95 € |
| Packs vendus | 47 (dont 10 « fondateurs ») |
| Abonnés actifs à M12 | ~21, soit un MRR de 1 212 € |
| Chiffre d'affaires | 21 136 € |
| Résultat net (après URSSAF 21,2 % et coûts, avant IR) | 13 548 € |
| Temps moyen | ~11 h/semaine (sprint de 30 h/semaine le 1er mois) |

Scénario prudent : 13 598 € de CA. Scénario ambitieux : 37 422 €. Hypothèses et détail mois par mois dans [`docs/business-plan.md`](docs/business-plan.md).

⚠️ **Signature chez le restaurateur.** Un professionnel de 5 salariés au plus, démarché hors établissement, peut avoir 14 jours de rétractation, et aucun paiement ne peut être encaissé avant 7 jours (art. L221-3 et L221-10 du code de la consommation). Le plan prévoit donc un lien de paiement envoyé à J+8. Voir [`docs/juridique-checklist.md`](docs/juridique-checklist.md).

## Contenu du dépôt

| Chemin | Rôle |
|---|---|
| `index.html` | site vitrine pour les restaurateurs |
| `menu/?r=<slug>` | **le produit livré** : menu QR multilingue (FR/EN/DE/IT/ES/NL), langue détectée automatiquement, filtres allergènes et régimes, mode sombre, sans cookies |
| `menu/restaurants/<slug>.json` | un fichier par restaurant client. `demo.json` est un restaurant fictif |
| `menu/qr.html` | générateur de chevalets QR imprimables (4 par page A4) |
| `audit/` | outil interne : audit imprimable et mini-CRM de prospection |
| `tools/` | scripts IA : brouillons de réponses aux avis, traduction de menus vers le JSON |
| `docs/` | business plan, plan de lancement sur 30 jours, scripts terrain, juridique, CGV, expansion, tableau de suivi KPI |
| `assets/` | styles partagés (`css/tokens.css`), configuration des coordonnées (`js/config.js`), bibliothèque QR embarquée (`vendor/qrcode.js`, licence MIT), polices auto-hébergées (`fonts/`, licence OFL), image de partage (`og.png`) |

## Mise en ligne

Le dépôt est relié à **Netlify** (projet `kannrunn`) : chaque push sur `main` est déployé automatiquement sur https://kannrunn.netlify.app, et chaque pull request reçoit une URL de prévisualisation.

1. Renseignez vos coordonnées dans `assets/js/config.js` (email, téléphone, lien du formulaire, SIRET).
2. Facultatif : achetez un nom de domaine (.fr, environ 9 €/an), branchez-le dans Netlify (*Domain management*), puis remplacez `kannrunn.netlify.app` dans les balises `og:` et `canonical` de `index.html`.
3. `_headers` interdit l'indexation des outils internes (`/audit/`, `/menu/qr.html`) et des menus clients, et ajoute des en-têtes de sécurité.

Pour tester en local :

```bash
python3 -m http.server 8000
# ouvrir http://localhost:8000 puis http://localhost:8000/menu/?r=demo
```

## Ajouter un restaurant client

1. Saisissez sa carte en français dans un CSV, sur le modèle de `tools/menu_exemple.csv`. Les allergènes sont **déclarés et validés par le restaurateur** : l'outil ne les devine jamais.
2. `python3 tools/traduire_menu.py` produit le JSON multilingue. Placez-le dans `menu/restaurants/<slug>.json` : options `--sortie` et `--ecraser`, voir `tools/README.md`. Il faut `ANTHROPIC_API_KEY` ; le coût est de quelques centimes par menu.
3. Relisez le fichier, puis publiez-le avec un commit sur `main`.
4. Ouvrez `menu/qr.html?r=<slug>&nom=<Nom du restaurant>`, imprimez et découpez les chevalets.

## Charte

- On ne rédige **jamais** de faux avis et on n'en achète jamais. C'est une pratique commerciale trompeuse, interdite.
- On répond uniquement aux avis réels, et chaque réponse est validée.
- On accède à la fiche Google en tant que « gestionnaire », un accès que le restaurateur peut révoquer à tout moment.
- Le restaurateur reste responsable des allergènes et des prix qu'il déclare.
