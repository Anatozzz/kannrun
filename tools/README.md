# Outils IA Polyglotte (ligne de commande)

Deux scripts Python qui préparent le travail du fondateur. **Ils ne publient jamais rien eux-mêmes.**

| Script | Rôle | Sortie |
|---|---|---|
| `reponses_avis.py` | Brouillons de réponses aux avis Google, dans la langue de chaque avis | `<sortie>.csv` + `<sortie>.md` (fichier de validation) |
| `traduire_menu.py` | Traduction d'un menu français en JSON multilingue pour le menu QR | `menu/restaurants/<slug>.json` |

S'y ajoute `prospects.py` (liste priorisée des prospects, sans IA ni dépendance) : voir la section 9.

Les deux scripts IA utilisent le SDK officiel `anthropic` et, par défaut, le modèle **`claude-haiku-5-5`** (le Haiku le plus récent en octobre 2026). Option `--modele` pour en changer.

## 1. Installation

```bash
cd kannrun
python3 -m venv .venv && source .venv/bin/activate     # Python 3.10 ou plus
pip install -r tools/requirements.txt
export ANTHROPIC_API_KEY="sk-ant-..."                  # clé créée sur platform.claude.com
```

La clé n'est lue que dans la variable d'environnement. Ne l'écrivez dans aucun fichier du dépôt (le site est public).

Sans clé, `--dry-run` fonctionne : il affiche les prompts exacts et n'appelle pas l'API.

## 2. Réponses aux avis, pas à pas

1. **Exporter les avis.** Copiez les avis récents de la fiche Google dans un CSV avec les colonnes `date,auteur,note,texte`. La colonne `langue` (fr, en, de…) est facultative. Le séparateur peut être `,` ou `;`, et les lignes qui commencent par `#` sont ignorées. Modèle : `tools/avis_exemple.csv`.
2. **Remplir le profil du restaurant.** Copiez `tools/profil_exemple.json` et adaptez :
   - `nom` ;
   - `ton` (`chaleureux`, `sobre` ou `familial`) ;
   - `signature` et `prenom_gerant` ;
   - `contact_prive` (adresse proposée aux clients mécontents) ;
   - `faits_utiles` (spécialités, horaires, terrasse, réservation, autres) ;
   - `ne_jamais_promettre`.

   **Le modèle n'utilise que ces faits.** Ce qui n'est pas dans le profil n'apparaîtra pas dans les réponses.
3. **Vérifier les prompts** sans rien dépenser :
   ```bash
   python tools/reponses_avis.py --avis avis-chez-x.csv --profil profil-chez-x.json --dry-run
   ```
4. **Générer les brouillons** :
   ```bash
   python tools/reponses_avis.py --avis avis-chez-x.csv --profil profil-chez-x.json --sortie sorties/chez-x-2026-10
   ```
5. **Relire `sorties/chez-x-2026-10.md`.** Pour chaque avis, le fichier montre :
   - l'avis original ;
   - la langue détectée ;
   - le brouillon ;
   - sa traduction française, pour savoir ce que vous publiez ;
   - le détail de l'avis repris ;
   - la liste « À vérifier avant publication ».

   Cette liste signale une longueur hors cible, un chiffre ou une adresse absents du profil, une formulation qui ressemble à une promesse commerciale, une langue incohérente et les doutes du modèle.
6. **Publier à la main** depuis Google Business Profile, une fois le brouillon corrigé, puis cochez « Relu et validé ».

Ce que contient chaque brouillon :
- il est écrit dans la langue de l'avis ;
- il compte 40 à 90 mots, signature comprise (sinon le script redemande une version corrigée) ;
- il reprend un détail de l'avis ;
- face à un avis négatif, il remercie, reconnaît le problème, s'excuse sobrement et propose de poursuivre en privé.

Un brouillon ne contient jamais d'argument agressif, ni d'autre donnée personnelle que le prénom public de l'auteur.

Les avis sans texte (note seule) sont signalés et laissés à une réponse manuelle.

Options : `--modele`, `--effort low|medium|high` (défaut `medium`), `--limite N`, `--dry-run`.

## 3. Traduction du menu, pas à pas

1. **Saisir le menu en français** dans un CSV avec les colonnes `section,plat,description,prix,allergenes,tags`. La colonne `dispo` (oui/non) est facultative. Modèle : `tools/menu_exemple.csv`.
   - `prix` : `12.50`, `12,50` ou `12,50 €`.
   - `allergenes` : ids séparés par `|`, **tels que déclarés par le restaurateur**. Ids autorisés (14 allergènes UE) : `gluten`, `crustaces`, `oeufs`, `poissons`, `arachides`, `soja`, `lait`, `fruits-a-coque`, `celeri`, `moutarde`, `sesame`, `sulfites`, `lupin`, `mollusques`.
   - `tags` : `vegetarien`, `vegan`, `local`, `fait-maison`, `epice`, `sans-gluten`, `signature`.
2. **Métadonnées** : le même profil JSON sert (clés `slug`, `nom`, `sous_titre`, `adresse`, `telephone`, `avis_url`, `site`, `message_menu`, `note_allergenes`, `noms_proteges` ; les horaires viennent de `faits_utiles.horaires`).
3. **Valider sans dépenser** :
   ```bash
   python tools/traduire_menu.py --menu menu-chez-x.csv --meta profil-chez-x.json --dry-run
   ```
   Un id d'allergène ou de tag inconnu (faute de frappe, « œufs », « cacahuète »…) **bloque le script avant tout appel**, avec le numéro de ligne et une suggestion.
4. **Traduire** :
   ```bash
   python tools/traduire_menu.py --menu menu-chez-x.csv --meta profil-chez-x.json --langues en,de,it,es
   ```
   Le fichier est écrit dans `menu/restaurants/<slug>.json`, ou ailleurs avec `--sortie`. Un fichier existant n'est remplacé qu'avec `--ecraser`.
5. **Relire** les traductions dans la page du menu, puis **faire valider les allergènes par le restaurateur**.

Garanties :
- **Allergènes** : ils ne sont jamais envoyés au modèle ni déduits par lui. Ils sont recopiés du CSV, et une vérification finale compare le JSON produit à la source.
- **Spécialités savoyardes** : un plat dont le nom contient une spécialité garde son nom d'origine dans toutes les langues ; sa description est traduite. Exemples : tartiflette, fondue, diots, reblochon, raclette, croziflette, crozets, berthoud, péla, farcement, matafans, « savoyarde ». Dans les descriptions, les noms de fromages et de plats savoyards restent tels quels, et le script le vérifie. Pour protéger d'autres noms, ajoutez-les à `noms_proteges`.
- **Format** : le JSON respecte le schéma du menu QR : `slug`, `nom`, `sousTitre`, `langues`, `devise`, `maj`, `infos`, `message`, `sections[].plats[]` avec `nom`, `description`, `prix`, `allergenes`, `tags` et `dispo`, et `noteAllergenes`.

Options : `--langues` (fr toujours inclus ; possibles : en, de, it, es, nl, pt, zh, ja), `--maj AAAA-MM-JJ`, `--sortie`, `--ecraser`, `--modele`, `--effort`, `--dry-run`.

## 4. Fiabilité

- **Sortie structurée** : chaque appel impose un schéma JSON (`output_config.format`), puis le script contrôle le fond : longueur, signature, identifiants, termes protégés. En cas d'écart, il fait une nouvelle requête qui inclut la correction demandée (3 essais au maximum).
- **Erreurs** :
  - Le SDK réessaie de lui-même les erreurs 429, 5xx et réseau (4 fois), et le script ajoute un délai exponentiel par-dessus.
  - Une clé invalide (401/403) ou un modèle inconnu (404) arrêtent tout.
  - Une requête invalide (400) ou un refus du modèle n'arrêtent pas le traitement : l'avis concerné est marqué en erreur et le script passe au suivant.
- **Codes de sortie** : `0` succès ; `1` erreur API ou clé manquante ; `2` fichier d'entrée invalide.
- Le texte des avis et du menu est transmis comme **donnée**, entre balises, et le prompt demande d'ignorer toute instruction qu'il contiendrait.

## 5. Coût estimé

Tarifs publics de `claude-haiku-5-5`, relevés le 20/10/2026 sur la page de tarifs d'Anthropic, en USD :
- **0,10 $** par million de tokens en entrée ;
- **0,50 $** par million de tokens en sortie (prompts de 100 000 tokens au plus).

| Tâche | Tokens par unité (estimation) | Coût par unité |
|---|---|---|
| Une réponse à un avis | ~1 200 en entrée, ~800 en sortie (réflexion comprise) | ~0,0005 $ |
| Un menu de 40 plats, 4 langues | ~5 000 en entrée, ~12 000 en sortie | ~0,007 $ |

Exemple d'un mois avec 20 restaurants abonnés :
- 30 avis par restaurant, soit 600 réponses, pour environ 0,30 $ ;
- 2 mises à jour de menu par restaurant, soit 40 traductions, pour environ 0,30 $.

Cela fait **moins de 1 $ par mois**, y compris les réessais. Ces tokens sont estimés à partir de la taille réelle des prompts. Le coût exact dépend de la longueur des avis et de la réflexion du modèle.

Chaque exécution affiche à la fin les tokens réellement consommés et le coût correspondant. Pour vérifier les tarifs du jour : <https://platform.claude.com/docs/en/about-claude/pricing>.

## 6. Règles éthiques (non négociables)

1. **Validation humaine de chaque réponse.** Le script produit des *brouillons*. Rien n'est publié sans relecture. En cas de doute, on ne publie pas.
2. **Jamais de faux avis.** On ne rédige, n'achète et ne suscite aucun avis, positif ou négatif, contre une contrepartie. Les faux avis sont une pratique commerciale trompeuse. Les avis d'exemple de ce dossier sont **fictifs** et marqués comme tels.
3. **On répond au nom du restaurant, avec son accord.** Sa signature doit figurer dans son profil.
4. **Aucune donnée personnelle** dans les réponses, au-delà du prénom public affiché par Google. Pas de détails de réservation, de santé, de montant ni de coordonnées du client. N'ajoutez pas de données personnelles dans les CSV au-delà de ce que Google affiche publiquement.
5. **Aucun fait inventé.** Le profil est la seule source des faits. Il faut le tenir à jour et y lister les choses à ne jamais promettre (remboursement, repas offert…).
6. **Allergènes** : le restaurateur est seul responsable de ses déclarations. L'outil les recopie sans les modifier et ne les « devine » jamais.

## 7. Tests

```bash
python -m pytest tools/test_tools.py        # ou : python -m unittest tools/test_tools.py
```

Les tests n'appellent jamais le réseau : le client Anthropic est simulé. Ils couvrent :
- la lecture des CSV (séparateurs, colonnes, notes, prix) ;
- la validation des allergènes et des tags ;
- la construction du JSON de menu (schéma, allergènes recopiés, noms savoyards) ;
- les réessais (JSON invalide, réponse trop courte, réponse tronquée) ;
- les erreurs API (429, 500, 400, 401, refus) ;
- `--dry-run`.

Les 4 tests d'erreurs du SDK sont ignorés si `anthropic` n'est pas installé.

## 8. Limites connues

- La détection de langue est faite par le modèle. Si la colonne `langue` est remplie et diffère, une alerte s'affiche.
- Les contrôles automatiques (chiffres, adresses, promesses) sont des signaux, pas une garantie : la relecture reste indispensable.
- Les brouillons de réponse sont des textes courts : le script ne gère pas les fils de discussion ni les réponses déjà publiées.

## 9. Liste de prospects : `prospects.py`

Le script dresse la liste de **tous** les restaurants, cafés et bars du Grand Annecy (34 communes, EPCI 200066793), puis la trie par priorité de visite. Il produit un CSV qui s'importe directement dans l'onglet Pipeline de `audit/`.

Il n'a aucune dépendance (bibliothèque standard, Python 3.9 ou plus) et n'utilise pas Anthropic. Il ne publie rien et ne contacte personne.

| Source | Ce qu'elle apporte | Activation |
|---|---|---|
| **Sirene** : [API Recherche d'entreprises](https://recherche-entreprises.api.gouv.fr/docs/) (gratuite, sans clé) | Tous les établissements actifs immatriculés : SIRET, NAF, date de création, adresse, coordonnées | par défaut |
| **OpenStreetMap** via [Overpass](https://overpass-api.de/) (gratuit) | Nom d'usage, site, lien vers le menu, téléphone public, cuisine, horaires | par défaut |
| **Google Places API (New)** (payante) | Note, nombre d'avis, site déclaré sur la fiche, `place_id` | avec une clé seulement |

### 9.1 Pas à pas, sur votre ordinateur

1. **Voir une démonstration, sans réseau :**
   ```bash
   python3 tools/prospects.py --fixtures --sortie /tmp/demo-prospects
   ```
   La démonstration lit les exemples de `tools/fixtures/exemple_*.json`. Ce sont des **établissements fictifs**, signalés partout :
   - un bandeau « DONNÉES DE TEST » dans la console ;
   - le préfixe `[TEST]` devant chaque nom ;
   - des ids qui commencent par `test-` ;
   - la colonne `donnees` du fichier complet.

   N'importez jamais ce fichier dans votre vrai pipeline.
2. **Collecter les vraies données** (une à deux minutes) :
   ```bash
   python3 tools/prospects.py --sortie prospects/ --contact vous@exemple.fr
   ```
   `--contact` ajoute votre adresse au User-Agent. C'est facultatif, mais recommandé par Overpass.

   Le dossier `prospects/` est dans `.gitignore`. **Ne commitez jamais de données de prospection : le dépôt est public.**
3. *(Facultatif)* **Ajouter Google** pour avoir la note et le nombre d'avis :
   ```bash
   export GOOGLE_MAPS_API_KEY="..."        # clé restreinte à « Places API (New) »
   python3 tools/prospects.py --sortie prospects/ --google-max 300
   ```
4. **Lire le résumé** affiché dans la console :
   - le total ;
   - la répartition par commune, par zone et par code NAF ;
   - le top 20 ;
   - les exclusions : établissements fermés, non diffusibles, hors territoire, chaînes.
5. **Importer dans `audit/`** : ouvrez l'onglet Pipeline, cliquez sur « Importer un CSV » et choisissez `prospects/prospects.csv`. Le pipeline affiche les prospects dans l'ordre du score.
6. **Les fois suivantes, exportez d'abord votre pipeline.** Quand l'import de `audit/` trouve un id déjà présent, il **remplace** la fiche entière, y compris le statut, les notes et l'audit saisi.

   Avant de régénérer la liste, exportez donc le pipeline (« Exporter en CSV »), puis passez l'export au script :
   ```bash
   python3 tools/prospects.py --sortie prospects/ --crm ~/Téléchargements/polyglotte-prospects-2026-11-02.csv
   ```
   Les prospects déjà présents sont alors retirés de `prospects.csv`. Le script les reconnaît par id (SIRET, id OSM ou `place_id`), ou par nom et zone pour ceux que vous avez saisis à la main. Ils restent visibles dans `prospects-complet.csv`, colonne `deja_dans_crm`.

   L'import n'ajoute donc que les nouveaux prospects.
7. **Recalculer sans rien redemander aux API** (après avoir modifié les zones ou la liste de chaînes) :
   ```bash
   python3 tools/prospects.py --sortie prospects/ --hors-ligne
   ```
   Le cache des réponses brutes est dans `prospects/cache/`, ou dans le dossier donné par `--cache`. `--sans-cache` le désactive.

### 9.2 Options

| Option | Effet |
|---|---|
| `--sortie DIR` | Dossier de sortie (défaut `prospects/`) |
| `--sources sirene,osm,google` | Sources à utiliser. Par défaut `sirene,osm`, plus `google` si une clé est fournie |
| `--naf 56.10A,56.10C,56.30Z` | Codes NAF interrogés. `--avec-hotels` ajoute 55.10Z |
| `--communes FICHIER.json` ou `--communes 74010,74267` | Autre territoire (voir 9.6) |
| `--epci SIREN` | Filtre Sirene sur un EPCI |
| `--osm-bbox` | OSM interrogé sur la bbox du territoire plutôt que commune par commune |
| `--cache DIR`, `--sans-cache`, `--hors-ligne` | Gestion du cache |
| `--fixtures` | Démonstration sur données fictives, sans réseau |
| `--google-key`, `--google-max N` | Google Places : N requêtes au plus (défaut 500), par ordre de priorité |
| `--inclure-chaines` | Garde les chaînes et franchises, avec −40 points |
| `--avec-dirigeants` | Exporte les dirigeants (données personnelles : voir 9.5) |
| `--crm EXPORT.csv` | Retire de l'import les prospects déjà présents dans le pipeline |
| `--contact EMAIL` | Ajoute une adresse de contact au User-Agent |

### 9.3 Les sorties

**`prospects.csv`** suit le format exact de `audit/` : les 21 colonnes de `audit.js` dans le même ordre, séparateur `;`, UTF-8 avec BOM, fins de ligne CRLF, même protection contre l'injection de formules. Une colonne `date_collecte` s'y ajoute en dernier ; `audit/` l'ignore à l'import.

Contenu des colonnes :
- `id` : stable, ce qui permet de **fusionner** à la réimportation au lieu de dupliquer :
  - `sirene-<SIRET>` si l'établissement est connu de Sirene ;
  - sinon `osm-n-<id>`, `osm-w-<id>` ou `osm-r-<id>`.
- `statut` : « À visiter ».
- `quartier` : la zone (voir 9.4).
- `note` et `totalAvis` : remplis si Google a été interrogé.
- `site` : « oui » si un site est connu.
- `notes` :
  - le score et son détail ;
  - l'adresse, le téléphone public, le site et le menu ;
  - le SIRET et le NAF ;
  - la date de création ;
  - les sources et la date de collecte.
- `majLe` : décroît d'une seconde par rang, pour que le pipeline (trié par `majLe`) affiche les prospects dans l'ordre du score.

Les champs d'audit (avis sans réponse, menu, allergènes…) restent vides : ils se remplissent sur place. Le « Score Polyglotte » de `audit/` reste donc à 0 tant que l'audit n'est pas fait. Le score de priorité figure dans `notes`.

**`prospects-complet.csv`** contient toutes les colonnes :
- `id`, `nom`, `zone`, `commune`, `adresse`, `lat`, `lon` ;
- `siret`, `naf`, `date_creation`, `prospect_chaud` ;
- `site`, `menu_en_ligne`, `telephone` (téléphone public de l'établissement, tiré d'OSM) ;
- `osm_id`, `place_id`, `note`, `nb_avis` ;
- `chaine`, `score`, `score_detail`, `sources` (par exemple `sirene+osm+google`) ;
- `ids_alternatifs`, `deja_dans_crm`, `donnees`, `date_collecte`.

### 9.4 Méthode

**Collecte Sirene** (règles vérifiées dans l'OpenAPI officielle de l'API, en octobre 2026) :
- Requête : `activite_principale=56.10A,56.10C,56.30Z`, `code_commune=<34 codes>`, `etat_administratif=A`, `per_page=25` (le maximum), `limite_matching_etablissements=100`, `minimal=true&include=matching_etablissements,complements`.
- Pagination complète, à 5 requêtes par seconde au plus (la limite officielle est de 7 par IP). Le script respecte `Retry-After` en cas de 429.
- L'API plafonne à 10 000 résultats (`page × per_page`). Au-delà, le script fait une requête par commune.
- **`activite_principale` et `etat_administratif` ne filtrent que l'unité légale**, d'après la documentation. Le script contrôle donc lui-même chaque établissement de `matching_etablissements`. Il garde ceux qui sont :
  - actifs (`etat_administratif = "A"`) ;
  - situés dans une des 34 communes ;
  - de l'une des activités demandées ;
  - diffusibles.

**Collecte OSM** : une **seule** requête Overpass, avec un timeout de 180 s.
- Elle porte sur les zones administratives des 34 communes (`ref:INSEE`) et utilise `foreach`. Chaque commune est donc écrite avant ses lieux, ce qui rattache chaque lieu à sa commune.
- Elle cherche `amenity=restaurant|cafe|bar|fast_food|pub|ice_cream`.
- `--osm-bbox` interroge plutôt un rectangle. Les lieux sont alors rattachés par `addr:city` ou `addr:postcode`, et ceux qui restent sans commune sont exclus.

**Fusion et dédoublonnage** :
1. **Normalisation des noms** : minuscules, accents et ponctuation retirés. On retire aussi les articles (le, la, l', du…), « chez », les mots génériques (restaurant, bar, brasserie, pizzeria…) et les formes juridiques (SARL, SAS…).
2. **Similarité des noms** (0 à 1) : la plus haute des trois valeurs suivantes :
   - le ratio de `difflib` ;
   - l'indice de Jaccard des mots ;
   - 0,85 si les mots d'un nom sont tous contenus dans l'autre.
3. **Règle d'appariement Sirene ↔ OSM.** Les deux fiches doivent être dans la même commune, puis :
   - distance < 60 m et similarité ≥ 0,6 ;
   - ou distance < 150 m et similarité ≥ 0,9, car le géocodage Sirene est parfois approximatif ;
   - sans coordonnées : similarité ≥ 0,95 et même code postal.
4. **Appariement un pour un**, les meilleures paires d'abord.
5. **Doublons dans une même source** (< 30 m, similarité ≥ 0,9) :
   - en cas de reprise de fonds, le SIRET le plus récent est gardé ;
   - un lieu OSM renvoyé par deux communes voisines n'est compté qu'une fois.
6. **Google** : pour chaque prospect, une recherche texte (nom et adresse), biaisée par un cercle de 200 m. Une fiche n'est retenue qu'à moins de 150 m, avec une similarité ≥ 0,5. Deux prospects rattachés au même `place_id` sont fusionnés.
7. **Traçabilité** : la colonne `sources` (`sirene`, `osm`, `sirene+osm`, `sirene+osm+google`…) et `ids_alternatifs` gardent l'origine de chaque prospect.

**Nom affiché** : nom d'usage OSM, sinon enseigne, sinon nom commercial, sinon raison sociale. Pour une entreprise individuelle sans enseigne : « Établissement sans enseigne – adresse ».

**Zones** : règles de `tools/grand_annecy_communes.json` (`regles_zones`), appliquées dans l'ordre :
1. Dans Annecy, des polygones approximatifs : Vieille ville, puis Bords du lac / Pâquier, puis Centre / gare.
2. Le code postal 74940 = Annecy-le-Vieux, puis un polygone de repli pour le nord-est d'Annecy.
3. Ensuite, la zone de la commune :
   - Sévrier, Saint-Jorioz, Duingt → Sévrier / rive ouest ;
   - Talloires-Montmin, Menthon-Saint-Bernard, Veyrier-du-Lac, Bluffy → Talloires / rive est.
4. Sinon, « Autre ».

Les polygones sont tracés à la main. Corrigez-les dans le JSON, puis recalculez avec `--hors-ligne`.

**Score de priorité (0-100)** : le barème complet est en tête de `prospects.py`. En résumé :

| Critère | Points |
|---|---|
| Zone | jusqu'à 25 |
| Nombre d'avis | jusqu'à 15 |
| Note entre 3,8 et 4,5 (marge de progrès) | 15 |
| Pas de site web | jusqu'à 10 |
| Pas de lien vers le menu | jusqu'à 10 |
| Création il y a moins de 18 mois (prospect chaud) | 15 |
| Restauration traditionnelle (plutôt que rapide) | jusqu'à 10 |

Une valeur inconnue rapporte des points « neutres », indiqués dans le détail.

**Chaînes et franchises** : elles sont détectées par une liste de noms (McDonald's, Burger King, KFC, Subway, Domino's, Starbucks, Paul, Brioche Dorée, Flunch, Buffalo Grill, Del Arte, Courtepaille, Hippopotamus, O'Tacos…) et par les balises OSM `brand` et `brand:wikidata`. Elles sont exclues, ou pénalisées de 40 points avec `--inclure-chaines`.

Les noms courants (Paul, Quick, Au Bureau…) exigent une égalité stricte, pour que « Chez Paul » ne soit pas exclu. Complétez la liste `CHAINES` si besoin.

### 9.5 RGPD et licences

- **Données collectées** : uniquement des données publiques d'**établissements** (raison sociale, enseigne, adresse, SIRET, NAF, site, téléphone public de l'établissement, note publique). Le script ne collecte aucun e-mail.
- **Entreprises individuelles** : leur dénomination Sirene est le nom de la personne, donc une donnée personnelle. Elle n'est **pas exportée** par défaut. `--avec-dirigeants` exporte les dirigeants et la dénomination, avec un avertissement. Ne l'utilisez que si c'est nécessaire, et ne diffusez jamais ces fichiers.
- **Établissements non diffusibles** : ceux qui ont fait opposition dans Sirene (statut de diffusion « P ») sont exclus.
- **Durée de conservation** : 3 ans au plus pour les données de prospects, à compter de la collecte ou du dernier contact venu du prospect (recommandation de la CNIL). La colonne `date_collecte` sert à ce suivi : supprimez du pipeline les prospects sans suite au-delà de cette durée.
- **Information des personnes** : lors du premier contact, indiquez d'où vient l'information (« base Sirene, OpenStreetMap ») et comment s'opposer. Si quelqu'un s'oppose, supprimez sa fiche du pipeline et ne la réimportez plus (`--crm` aide à repérer les fiches déjà connues).
- **Licences** :
  - Sirene : Licence Ouverte 2.0 (Etalab).
  - OpenStreetMap : ODbL. Mentionnez « © les contributeurs OpenStreetMap ». La liste reste un usage interne : ne la publiez pas.
  - Google : voir 9.7.

### 9.6 Dupliquer dans une autre ville

1. Copiez `grand_annecy_communes.json` :
   - remplacez `epci_siren`, `communes` (codes INSEE), `bbox` et `regles_zones` ;
   - les zones doivent rester parmi les 7 noms de `audit/`.
2. Lancez `--communes ma_ville.json`.
3. Pour aller vite : `--communes 69123,69266` (toutes les zones seront « Autre ») ou `--epci <SIREN>`.

La liste des communes d'un EPCI est disponible sur <https://geo.api.gouv.fr/epcis/SIREN/communes>.

Sans liste de communes, `--epci` interroge OSM par la balise `ref:FR:SIREN` de l'EPCI. Cette balise n'a pas été vérifiée : préférez une liste de communes.

### 9.7 Coûts

- **Sirene et Overpass** : gratuits.
  - Une exécution fait quelques dizaines de requêtes Sirene (25 entreprises par page) et **une** requête Overpass.
  - Overpass demande de rester sous environ 10 000 requêtes et 1 Go par jour. Pour un usage commercial intensif, il faut une instance dédiée. Une exécution par mois est très loin de ces limites.
- **Google Places API (New)** : désactivée par défaut.
  - Le FieldMask est réduit au minimum utile : `id`, `displayName`, `location`, `rating`, `userRatingCount`, `websiteUri`, `googleMapsUri`.
  - `rating`, `userRatingCount` et `websiteUri` font facturer la requête au **SKU « Text Search Enterprise »** (documentation Google).
  - Tarif relevé en octobre 2026 sur une source secondaire : environ **35 $ les 1 000 requêtes**, après **1 000 requêtes gratuites par mois** pour ce SKU. **À vérifier** sur <https://developers.google.com/maps/billing-and-pricing/pricing>.
  - Exemple : environ 600 prospects pour le Grand Annecy reviennent à environ 0 $ dans le seuil gratuit, sinon à environ 21 $.
  - `--google-max` plafonne le nombre de requêtes, et le script affiche une estimation avant de commencer.
  - Quand un `place_id` est déjà connu, le script fait une requête Place Details à la place.
  - Réglez aussi un quota journalier dans la console Google Cloud.
- **Conditions de Google Maps Platform** :
  - Le script ne fait **aucun scraping** de Google Maps.
  - Les `place_id` peuvent être conservés : ils sont gardés dans `cache/google_place_ids.json`.
  - Les coordonnées ne peuvent être mises en cache que 30 jours ; les autres contenus (note, avis, site) n'ont pas d'exception de cache.
  - En conséquence, le cache Google brut est **supprimé après 30 jours**, et les coordonnées Google ne sont jamais exportées.
  - Le script avertit si une ancienne sortie contient des notes de plus de 30 jours.
  - Traitez la note et le nombre d'avis comme une information ponctuelle de tri : vous les relevez de toute façon sur la fiche lors de l'audit.

### 9.8 Limites connues

- **Le script n'a pas pu être testé contre les vraies API.** L'environnement de développement bloquait le réseau. Le code suit la documentation officielle :
  - pour Sirene, l'OpenAPI du dépôt `annuaire-entreprises-data-gouv-fr/search-api` (paramètres, plafonds, champs) ;
  - pour Places, la documentation Google (FieldMask, SKU).

  Les tests utilisent des réponses d'exemple fictives qui reproduisent ces formats. À la première vraie exécution, comparez quelques résultats avec <https://annuaire-entreprises.data.gouv.fr>.
- **Activité de l'unité légale.** Comme `activite_principale` ne filtre que l'unité légale, un restaurant exploité par une société dont l'activité principale est autre n'est pas trouvé par Sirene. C'est le cas d'un hôtel (utilisez `--avec-hotels`) ou d'un commerce. OSM le trouve en général.
- **NAF 2025.** Au 1er janvier 2027, Sirene passe à la NAF 2025 (par exemple, 56.10A deviendrait 56.11G ; correspondance non vérifiée). Il faudra alors adapter `--naf`.
- **Qualité des données.**
  - Sirene : les coordonnées sont géocodées et parfois imprécises, et l'enseigne est souvent vide (le nom vient alors d'OSM).
  - OSM : l'absence de balise `website` ne prouve pas l'absence de site, d'où 6 points au lieu de 10. La couverture OSM est inégale.
  - `matching_etablissements` est lu jusqu'à 100 établissements par entreprise.
- **Fusion heuristique.** Il peut y avoir de faux doublons ou des fusions manquées ; vérifiez la colonne `sources`.
- **Zones et chaînes approximatives.** Les zones sont tracées à la main et la liste de chaînes n'est pas exhaustive.
- **Communes.** Les 34 codes INSEE ont été recoupés par recherche web (voir le champ `notes` du JSON). Revérifiez-les une fois avec geo.api.gouv.fr.

### 9.9 Tests

```bash
python3 -m unittest tools/test_tools.py tools/test_prospects.py
```

Aucun accès réseau. Les tests couvrent :
- la lecture des réponses Sirene et la pagination ;
- le découpage au-delà de 10 000 résultats et les paramètres conformes à la documentation ;
- les filtres (établissement fermé, non diffusible, activité, commune, anciens codes) ;
- le 429 avec `Retry-After`, le délai entre requêtes, le cache et le mode hors ligne ;
- la requête Overpass et la lecture de sa réponse ;
- la normalisation, la similarité et la fusion ;
- les zones, le barème, les chaînes (y compris les faux positifs) ;
- Google : FieldMask, clé absente du cache, expiration à 30 jours, `place_id` ;
- le RGPD (aucun nom de personne exporté) et `--crm`.

Le format d'import est vérifié en **important réellement** le CSV généré avec le code de `audit/audit.js`, exécuté dans node. Le test vérifie l'ajout, puis la fusion par id lors d'une réimportation. Sans node, ce test est ignoré, mais la reproduction Python du parseur de `audit.js` reste testée.
