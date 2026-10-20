# Outils IA Polyglotte (ligne de commande)

Deux scripts Python qui préparent le travail du fondateur. **Ils ne publient jamais rien eux-mêmes.**

| Script | Rôle | Sortie |
|---|---|---|
| `reponses_avis.py` | Brouillons de réponses aux avis Google, dans la langue de chaque avis | `<sortie>.csv` + `<sortie>.md` (fichier de validation) |
| `traduire_menu.py` | Traduction d'un menu français en JSON multilingue pour le menu QR | `menu/restaurants/<slug>.json` |

Les deux scripts utilisent le SDK officiel `anthropic` et, par défaut, le modèle **`claude-haiku-5-5`** (le Haiku le plus récent en octobre 2026). Option `--modele` pour en changer.

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
