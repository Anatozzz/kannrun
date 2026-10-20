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
| `assets/` | styles partagés (`css/tokens.css`), configuration des coordonnées (`js/config.js`), bibliothèque QR embarquée (`vendor/qrcode.js`, licence MIT) |

## Mise en ligne (5 minutes, 0 €)

1. Sur GitHub : **Settings → Pages → Deploy from a branch** → `main` / racine.
2. Renseignez vos coordonnées dans `assets/js/config.js` (email, téléphone, lien du formulaire, SIRET).
3. Facultatif : achetez un nom de domaine (.fr, environ 9 €/an) et faites-le pointer vers GitHub Pages.

Pour tester en local :

```bash
python3 -m http.server 8000
# ouvrir http://localhost:8000 puis http://localhost:8000/menu/?r=demo
```

## Ajouter un restaurant client

1. Saisissez sa carte en français dans un CSV, sur le modèle de `tools/menu_exemple.csv`. Les allergènes sont **déclarés et validés par le restaurateur** : l'outil ne les devine jamais.
2. `python3 tools/traduire_menu.py ...` génère `menu/restaurants/<slug>.json` (voir `tools/README.md`).
3. Relisez le fichier, puis publiez-le avec un commit sur `main`.
4. Ouvrez `menu/qr.html?r=<slug>&nom=<Nom du restaurant>`, imprimez et découpez les chevalets.

## Charte

- On ne rédige **jamais** de faux avis et on n'en achète jamais. C'est une pratique commerciale trompeuse, interdite.
- On répond uniquement aux avis réels, et chaque réponse est validée.
- On accède à la fiche Google en tant que « gestionnaire », un accès que le restaurateur peut révoquer à tout moment.
- Le restaurateur reste responsable des allergènes et des prix qu'il déclare.
