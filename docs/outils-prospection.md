# Outils de prospection — sources, légalité, stack à 0 €, routine (octobre 2026)

**Pour qui :** le développeur commercial de Polyglotte (Annecy).
**Contexte :** budget quasi nul, 10 packs à signer d'ici le 19 novembre ([go-to-market-30-jours.md](go-to-market-30-jours.md)), outil interne `audit/` qui sert de CRM et importe du CSV.

**Méthode.** Recherches web du 20 octobre 2026. Les pages officielles n'ont pas pu être ouvertes depuis l'environnement de travail : les chiffres viennent des extraits des moteurs de recherche, souvent relayés par des sites tiers. Quand la source est tierce, c'est indiqué. Quand un prix n'a pas été trouvé, c'est écrit « non public » ou « à vérifier ». **Avant de payer quoi que ce soit, vérifier le prix sur la page officielle.**

**En une phrase.** Pour lister les restaurants, les données publiques (Sirene, OpenStreetMap, BODACC) suffisent et sont gratuites. Pour les qualifier (avis, réponses, menu), il faut **lire la fiche Google soi-même**, sans robot. Les outils B2B payants n'apportent presque rien pour des restaurants, et les scrapers Google Maps violent les conditions de Google.

---

## 1. Les sources qui répertorient les prospects

### 1.1 Données publiques gratuites (le socle)

| Source | Ce qu'elle donne | Accès et limites | Utilité pour Polyglotte |
|---|---|---|---|
| **API Recherche d'entreprises** (`recherche-entreprises.api.gouv.fr`, le moteur derrière l'Annuaire des entreprises) | Raison sociale, enseignes, adresse, SIREN/SIRET, code NAF, date de création, tranche d'effectif, dirigeants, établissements correspondant aux filtres (`matching_etablissements`) | Gratuite, sans clé. Filtres `activite_principale` (code NAF, plusieurs valeurs séparées par des virgules), `code_commune` (code INSEE à 5 chiffres), `departement`, `epci`, `tranche_effectif_salarie`, `etat_administratif`. Débit : **7 appels par seconde** selon une documentation relayée par un projet tiers ([MCP Recherche d'entreprises](https://glama.ai/mcp/servers/@yoanbernabeu/mcp-recherche-entreprises/tree/b922a30f7dae4525feefe599e7910fb7b9113825)). Documentation officielle : [recherche-entreprises.api.gouv.fr/docs](https://recherche-entreprises.api.gouv.fr/docs/) ; code source : [GitHub search-api](https://github.com/annuaire-entreprises-data-gouv-fr/search-api). Des erreurs 429 ont été signalées pendant un incident en avril 2026 ([discussions data.gouv.fr](https://www.data.gouv.fr/dataservices/api-recherche-dentreprises/discussions)) | **Source n° 1 pour la liste exhaustive.** Un filtre NAF + `epci` sort tous les restaurants immatriculés du Grand Annecy |
| **Annuaire des entreprises** ([annuaire-entreprises.data.gouv.fr](https://annuaire-entreprises.data.gouv.fr)) | La même chose, en interface web | Gratuit. Filtres NAF, code postal, effectif et entrepreneur individuel ([data.gouv.fr](https://www.data.gouv.fr/dataservices/api-recherche-dentreprises/discussions)) | Vérifier une fiche à la main (date de création, dirigeant) avant une visite |
| **API Sirene de l'INSEE** ([portail-api.insee.fr](https://portail-api.insee.fr)) | Tout le répertoire, historique compris | Gratuite. Il faut un compte, une application et un abonnement au plan « Public » ; la clé n'expire pas ([guide INSEE](https://static.insee.fr/api-sirene/Insee_API_publique_modalites_connexion.pdf)). **30 requêtes par minute**. Un curseur ramène 1 000 résultats par page et ne compte que pour une requête ([INSEE, actualités juin 2026](https://www.insee.fr/fr/information/9019311)). Fichiers stock complets sur data.gouv.fr | Plan B si l'API Recherche d'entreprises est en panne. Plus technique (syntaxe `q=`) |
| **Base permanente des équipements (BPE, INSEE)** | Restaurants géolocalisés : nom ou raison sociale, adresse, coordonnées (x, y). 229 types d'équipements | Gratuite. Millésime 2024 paru le 27/07/2026 ; données personnelles anonymisées ([INSEE](https://www.insee.fr/fr/metadonnees/source/operation/s2216/presentation), [data.gouv.fr](https://www.data.gouv.fr/datasets/base-permanente-des-equipements-2)) | Contrôle croisé du nombre de restaurants par commune. Code exact de l'équipement « restaurant » : à vérifier dans la nomenclature BPE |
| **OpenStreetMap / Overpass API** | Lieux taggés `amenity=restaurant`, `cafe`, `bar`, `fast_food` avec, quand c'est renseigné, `website`, `phone`, `cuisine`, `opening_hours`, coordonnées | Gratuit. Serveur public : rester sous ~10 000 requêtes et 1 Go par jour ([manuel Overpass](https://dev.overpass-api.de/overpass-doc/en/preface/commons.html), [wiki OSM](https://wiki.openstreetmap.org/wiki/Overpass_API)). Une seule requête suffit pour tout le Grand Annecy. Licence **ODbL** : citer « © les contributeurs d'OpenStreetMap ». Le partage à l'identique ne s'applique que si l'on diffuse la base hors de l'entreprise ([wiki OSM, ODbL](https://wiki.openstreetmap.org/wiki/Open_Database_License)) | **Source n° 2.** Elle donne le site web, le téléphone et les horaires, que Sirene n'a pas. Couverture inégale : un champ vide ne veut pas dire « absent » |
| **BODACC** (API de la DILA) | Annonces de créations, d'immatriculations et de **ventes et cessions de fonds de commerce**, avec date, SIREN, ville et département | Gratuit, sorties CSV, JSON et Excel ([data.gouv.fr](https://www.data.gouv.fr/dataservices/672cf66ea47b8d4c15d13d5b)). Jeu `annonces-commerciales` sur `bodacc-datadila.opendatasoft.com` ([présentation DILA, mars 2026](https://echanges.dila.gouv.fr/OPENDATA/BODACC/DILA_API-BODACC_Presentation_20260327.pdf)). Champs `familleavis` et `numerodepartement` ([exemple tiers](https://apify.com/sylvainrt/bodacc-scraper)) | **Prospects chauds.** Un repreneur doit reprendre la fiche Google, souvent refaire la carte, et veut marquer son arrivée |
| **Ville d'Annecy sur data.gouv.fr** | Défibrillateurs, parkings vélo, monuments, carte scolaire… ([page de l'organisation](https://www.data.gouv.fr/organizations/ville-dannecy-1/datasets)) | Gratuit | **Aucun jeu sur les terrasses ni sur les licences de débit de boissons trouvé** pour Annecy ou le Grand Annecy. D'autres villes publient leurs autorisations de terrasse ([exemple](https://www.data.gouv.fr/datasets/domaine-public-terrasses-mobiliers-structures)). Les déclarations de licence se font en mairie ([exemple Épernay](https://epernay.fr/print/pdf/node/31041)), sans liste ouverte trouvée. Piste : demander la liste des autorisations de terrasse à la mairie (document administratif communicable, à vérifier) |
| **Offices de tourisme** | Guide des restaurants de [Lac Annecy Tourisme (PDF 2024)](https://www.lac-annecy.com/content/uploads/2024/04/en-restaurants.pdf). Fiches restaurants de [Haute-Savoie Mont-Blanc Tourisme](https://hautesavoiemontblanc-tourisme.com/en/your-trip/your-culinary-experiences/all-restaurants) ; [haute-savoie-tourisme.org](https://www.haute-savoie-tourisme.org/index.php/restaurants) affiche « 710 fiches » pour le département | Consultation gratuite | Un restaurant référencé par l'office de tourisme vise les touristes : c'est un **signal de priorité**. Les partenaires de l'office sont aussi un public pour un atelier (voir go-to-market, § 7) |
| **Apidae** (base touristique régionale) | Les fiches que saisissent les offices de tourisme : restaurants, hébergements, activités | Accès par API avec une clé, un identifiant de projet et OAuth ([client PHP tiers](https://packagist.org/packages/fm5z/apidae-api-php), [dev.apidae-tourisme.com](https://dev.apidae-tourisme.com)). **Conditions d'accès open data non trouvées** : à demander à Lac Annecy Tourisme. Les données remontées vers DATAtourisme sont sous Licence ouverte Etalab ([fiche DATAtourisme](https://www.velo-territoires.org/wp-content/uploads/2019/06/2019-DATAtourisme-FichePratiqueVELO_V1_2.pdf)). La présence de restaurants de Haute-Savoie dans DATAtourisme n'a pas été vérifiée | Bonus, pas indispensable. Utile surtout pour la verticale hôtels et loueurs |

**Trois pièges des données Sirene :**

1. **Diffusion partielle.** Un entrepreneur individuel qui s'est opposé à la diffusion n'a plus ni nom, ni enseigne, ni adresse précise dans les données publiques ([INSEE](https://www.insee.fr/fr/information/7456564)). Les entreprises non diffusibles sont aussi exclues des filtres de l'API ([data.gouv.fr](https://www.data.gouv.fr/dataservices/api-recherche-dentreprises/discussions)). La liste Sirene sera donc **incomplète**, et OSM ou la visite à pied comblent les trous. Ce statut traduit une opposition : ne pas chercher à recontacter ces personnes à distance par d'autres moyens. Passer la porte d'un restaurant ouvert au public reste possible.
2. **Code NAF.** Le filtre `activite_principale` porte sur l'unité légale, pas sur l'établissement ([description de l'API](https://glama.ai/mcp/servers/yoanbernabeu/mcp-recherche-entreprises/tools/rechercher_entreprise)). Une société dont l'activité principale déclarée n'est pas la restauration, mais qui exploite un restaurant, n'apparaîtra pas.
3. **NAF 2025.** Une nouvelle nomenclature devient la référence au **1er janvier 2027**, avec de nouveaux codes pour toutes les entreprises actives ([INSEE](https://www.insee.fr/fr/information/9019311), [circulaire](https://www.economie.gouv.fr/files/actes-BOAC/2026-01/ECOO2531026C_0_0_0.pdf)). Les filtres ci-dessous (NAF rév. 2) devront être mis à jour en janvier.

**Codes NAF rév. 2 à utiliser jusqu'à fin 2026 :**

| Cible | Codes |
|---|---|
| Restaurants (priorité 1) | 56.10A restauration traditionnelle · 56.10C restauration rapide · 56.10B cafétérias |
| Bars et cafés (priorité 2) | 56.30Z débits de boissons |
| Hôtels (verticale 2027) | 55.10Z hôtels · 55.20Z hébergement touristique de courte durée · 55.30Z campings |
| Loueurs (vélos, bateaux, ski) | 77.21Z location d'articles de loisirs et de sport |
| Commerces | 47.xx (commerce de détail), à cibler par sous-classe |

### 1.2 Plateformes d'avis

| Plateforme | Accès officiel | Prix 2026 | Utile pour prospecter ? |
|---|---|---|---|
| **Google Maps (lecture humaine)** | La fiche publique, lue par une personne | Gratuit | **Oui, c'est la source principale de qualification.** Note, nombre d'avis, avis sans réponse du propriétaire, langue des avis, menu, photos, horaires |
| **Google Places API (New)** | API officielle. Compte de facturation et carte bancaire obligatoires | Seuils gratuits par SKU et par mois depuis le 1er mars 2025, qui remplacent le crédit de 200 $ ([OpenPlaces, tiers](https://openplacesapi.com/blog/google-places-api-pricing)). D'après la [grille Google](https://developers.google.com/maps/billing-and-pricing/pricing), pour 1 000 appels : **Text Search Essentials (IDs seulement) : illimité et gratuit** ; Text Search Pro : 5 000 gratuits, puis 32 $ ; Text Search Enterprise : 35 $ ; Enterprise + Atmosphere : 40 $ ; **Place Details Essentials : 10 000 gratuits, puis 5 $** ; Pro : 5 000 gratuits, puis 17 $ ; **Enterprise : 1 000 gratuits, puis 20 $** ; Enterprise + Atmosphere : 25 $ (seuil gratuit à vérifier). La note et le nombre d'avis font passer l'appel en Enterprise, les avis en Enterprise + Atmosphere (source tierce, à vérifier dans la doc des masques de champs) | **Seulement pour récupérer le `place_id`**, le seul contenu que l'on peut stocker sans limite de durée ([politiques Places API](https://developers.google.com/maps/documentation/places/web-service/policies)). Les autres contenus ne doivent être ni pré-chargés, ni mis en cache, ni stockés en dehors des exceptions prévues. L'API ne renvoie que 5 avis par lieu, et **sans les réponses du propriétaire** (sources tierces : [JustReview](https://justreview.co/blog/google-reviews-api-what-is-allowed/), [Apify](https://apify.com/nexgendata/google-maps-reviews)). Elle ne mesure donc pas le signal clé, les avis sans réponse |
| **TripAdvisor Content API** | Clé développeur | 5 000 appels gratuits par mois, carte bancaire exigée pour le dépassement ([FAQ officielle](https://tripadvisor-content-api.readme.io/reference/faq)). 5 avis et 5 photos par lieu (source tierce, [Supergood](https://supergood.ai/api-report-card/tripadvisor)). Une migration vers une nouvelle API « Terra » est annoncée par des tiers, calendrier à vérifier | **Non.** API prévue pour l'affichage grand public (B2C), et accord séparé exigé pour un usage IA (sources tierces). Lire la page TripAdvisor à la main pour les restaurants très touristiques |
| **TheFork** | API réservée aux partenaires agréés (réservation, caisse) ([DM Champ](https://dmchamp.com/integrations/thefork/), [API Tracker](https://apitracker.io/a/thefork/products)) | Non public | **Non** comme source. Mais un restaurant présent sur TheFork est déjà outillé pour la réservation : argument « TheFork fait la réservation, moi les avis et les langues » (objection 13 des scripts) |
| **Yelp Fusion** | Clé développeur | Accès gratuit supprimé en 2024. Starter 7,99 $, Plus 9,99 $, Enterprise 14,99 $ pour 1 000 appels, essai de 30 jours ([App Developer Magazine, 2024](https://appdevelopermagazine.com/yelp-fusion-api-outrageous-new-pricing/)). Tarif 2026 non trouvé | **Non.** Yelp est peu utilisé en France |

### 1.3 Outils de prospection B2B et scrapers

**Constat général.** Ces outils enrichissent des fiches de **décideurs** : e-mail nominatif, mobile, LinkedIn. Un restaurateur indépendant d'Annecy est rarement sur LinkedIn, et ses coordonnées utiles (téléphone du restaurant, e-mail générique) figurent déjà sur sa fiche Google ou son site. **Gain faible, coût et risque réels.**

| Outil | Ce qu'il fait | Prix relevé (à vérifier sur la page officielle) | Apport pour des restaurants | Risque |
|---|---|---|---|---|
| **Pharow** | Base B2B française (Sirene + LinkedIn + signaux) | À partir de 105 € HT/mois pour 1 utilisateur en engagement annuel ([Salesdorado](https://salesdorado.com/prospection-commerciale/avis-pharow/)). Grille 2026 non affichée publiquement, paliers de 99 à 499 €+ ([Derrick](https://derrick-app.com/tools/pharow-pricing)). Essai de 15 jours avec 100 crédits | Faible : refait Sirene en payant | Faible |
| **Societeinfo** | Base d'entreprises françaises + API | Page officielle relevée : Starter 59 € HT/mois (300 crédits), Pro 159 €, Scale 449 €, Entreprise sur devis ([societeinfo.com/tarifs](https://societeinfo.com/tarifs)). D'autres comparatifs donnent d'autres grilles ([Overloop](https://overloop.com/fr/blog/base-de-donnees-b2b)) | Faible | Faible |
| **Pappers (site + API)** | Données légales, dirigeants, comptes, BODACC | Inscription gratuite pour obtenir un jeton d'API, paiement à l'usage ou abonnement ([FAQ Pappers](https://www.pappers.fr/faq)). 100 crédits à l'ouverture selon un avis tiers non daté ([Dix Mille Heures](https://www.dixmilleheures.fr/avis/pappers)). **Prix des packs : non public dans nos résultats** | Moyen : lecture confortable d'une fiche (dirigeant, date de reprise). Le site gratuit suffit | Faible |
| **Société.com** | Fiches d'entreprises | **Non public** dans nos résultats | Faible : l'Annuaire des entreprises est gratuit | Attention aux **sites imitateurs** qui vendent un Kbis à 1-2 € puis prélèvent un abonnement d'environ 44 à 50 €/mois ([Signal-Arnaques](https://www.signal-arnaques.com/scam/view/935333)). Kbis gratuit pour sa propre entreprise sur les sites officiels |
| **Kaspr** | Extension Chrome : téléphone et e-mail depuis LinkedIn | Gratuit : 15 crédits e-mail B2B, 5 téléphone et 5 e-mail direct par mois, exports limités ([Cleanlist](https://www.cleanlist.ai/blog/2026-09-01-kaspr-pricing-guide), [aide Kaspr](https://help.kaspr.io/en/articles/8800588-kaspr-pricing-and-subscription-plans)). Starter ~49 $/mois en annuel | Quasi nul | **Élevé.** La CNIL a infligé à Kaspr **240 000 € d'amende** le 5 décembre 2024 pour avoir aspiré sur LinkedIn des coordonnées dont les titulaires avaient limité la visibilité ([CNIL](https://www.cnil.fr/fr/aspiration-de-donnees-sanction-de-240-000-euros-lencontre-de-la-societe-kaspr)) |
| **Lusha** | Coordonnées de décideurs | Gratuit : 40 ou 70 crédits par mois selon les sources ; Pro de 29,90 à 52,45 $ par utilisateur et par mois selon les sources ([Landbase](https://www.landbase.com/blog/lusha-pricing), [Emelia](https://emelia.io/software/lusha/pricing)) | Quasi nul | Moyen (données de personnes physiques) |
| **Dropcontact** | Enrichissement et vérification d'e-mails, sans base de personnes stockée (argument de l'éditeur) | Environ 79 €/mois pour 500 crédits ([Emelia](https://emelia.io/fr/hub/dropcontact-prix)) ; grille différente chez [LeadHaste](https://leadhaste.com/blog/dropcontact-pricing-2026) | Faible | Faible à moyen |
| **Hunter** | Recherche d'e-mails par domaine | Gratuit : 50 crédits par mois ; Starter 34 $/mois en annuel ([MarketBetter](https://marketbetter.ai/blog/hunter-io-pricing-breakdown-2026/)) | Faible : trouve `contact@` sur le site, ce qu'on voit déjà | Deviner une adresse nominative (prenom@) reste un traitement de données personnelles |
| **Apollo** | Base mondiale + séquences d'e-mails | Gratuit : 100 crédits par mois selon [Zeliq](https://www.zeliq.com/blog/apolloio-pricing), d'autres chiffres chez [CostBench](https://costbench.com/software/sales-intelligence/apollo-io/free-plan/). Basic 49 à 59 $ par utilisateur et par mois | Quasi nul en France sur ce segment | Moyen |
| **lemlist** | Séquences d'e-mails et multicanal | Email Pro ~79 $ par utilisateur et par mois (63 $ en annuel), Multichannel Expert ~109 $ (87 $) ([Zeliq](https://www.zeliq.com/blog/lemlist-pricing)) | Nul : on ne prospecte pas par e-mail froid de masse | Élevé si envoi de masse |
| **La Growth Machine** | Séquences LinkedIn + e-mail | 60 / 120 / 180 € par identité et par mois en mensuel, 50 / 100 / 150 € en annuel ([Emelia, oct. 2026](https://emelia.io/hub/la-growth-machine-pricing)) | Nul | CGU LinkedIn sur l'automatisation |
| **Waalaxy** | Automatisation LinkedIn | À partir de 19 € par utilisateur et par mois ; e-mail sur le plan Business, 69 ou 99 €/mois selon les sources ([La Growth Machine](https://lagrowthmachine.com/fr/tarifs-waalaxy/)) | Nul | CGU LinkedIn |
| **Outscraper** (scraper Google Maps) | Extraction de fiches et d'avis Google Maps | 500 lieux gratuits par mois, puis environ 3 $ pour 1 000 ([SyncGTM](https://syncgtm.com/blog/outscraper-review-2026), [FreeTier](https://freetier.co/directory/products/outscraper)) | Élevé techniquement (il voit les réponses du propriétaire) | **Interdit par les conditions Google** (voir ci-dessous) |
| **Apify** (acteurs Google Maps) | Idem, place de marché de scrapers | 5 $ de crédit gratuit par mois, sans carte ([use-apify](https://use-apify.com/docs/what-is-apify/apify-free-plan)) ; acteur Google Maps à ~4 $ pour 1 000 lieux selon [Apify](https://blog.apify.com/best-google-maps-scrapers/) | Idem | **Interdit par les conditions Google** |
| **PhantomBuster** | Automatisations (LinkedIn, Google Maps…) | Essai de 14 jours ; Starter ~69 $/mois (59 $ chez [Capterra](https://www.capterra.com/p/173165/Phantombuster/pricing/)) ([Emelia](https://emelia.io/hub/phantombuster-pricing)) | Idem | **Interdit par les conditions Google**, risque CGU LinkedIn |
| **Data Miner** (extension Chrome) | Scraping de pages web | Gratuit : 500 pages par mois ; payant de 19,99 à 200 $/mois ([Prospeo](https://prospeo.io/s/data-miner-pricing-reviews-pros-and-cons), [FreeTier](https://freetier.co/directory/products/data-miner)) | Utile sur des pages qui l'autorisent | Interdit sur Google Maps |

**Le scraping de Google Maps est interdit.** Les conditions de Google Maps Platform contiennent une clause « No Scraping » (section 3.2.3(a), selon les versions). Elle interdit d'exporter ou d'extraire le contenu Google Maps, y compris noms, adresses et avis, pour l'utiliser hors des services Google. Une clause « No Caching » l'accompagne ([conditions officielles](https://cloud.google.com/maps-platform/terms), texte relayé par [ConductAtlas](https://conductatlas.com/platform/google-maps/google-maps-platform-terms-of-service/no-scraping-or-content-extraction/)). Les conditions grand public de Google Maps interdisent aussi le téléchargement massif ([Thunderbit](https://thunderbit.com/blog/is-scraping-google-maps-legal)). Les avis contiennent en plus le nom des auteurs, qui sont des personnes physiques : les aspirer en masse, c'est constituer un fichier sans base légale ni information des personnes (RGPD, voir § 2.6). Le précédent Kaspr montre que la CNIL sanctionne l'aspiration de données.

**Conséquence pratique.** Lire une fiche Google et **noter ses propres observations** (nombre d'avis sans réponse, langues, menu présent ou non) est un travail d'analyse humain. Polyglotte n'archive pas le contenu de Google. Ne pas recopier le texte des avis en masse, ne pas lancer de robot. Pour l'audit imprimé, utiliser les comptages que l'on a faits soi-même. N'imprimer des données issues de l'API Google Maps Platform que si les conditions l'autorisent : un développeur rapporte qu'un document généré ne peut pas en contenir ([forum Google](https://discuss.google.dev/t/data-visualisations-with-routes-api-data/279145)).

### 1.4 CRM pour suivre le pipeline

L'outil `audit/` stocke les prospects **dans le navigateur** et exporte en CSV. Il suffit pour le sprint. Faire un **export CSV chaque soir** : c'est la sauvegarde.

| Outil | Gratuit ? | Limites relevées | Quand l'utiliser |
|---|---|---|---|
| **`audit/` + export CSV** | Oui | Un seul navigateur, pas de partage | Par défaut, pendant le sprint |
| **Google Sheets** | Oui (compte Google) | Aucune contrainte gênante à ce volume | Fusion des sources, score de priorité, sauvegarde partagée. **Recommandé en complément** |
| **HubSpot CRM gratuit** | Oui, sans limite de durée | Nouveaux comptes : **2 utilisateurs, 1 000 contacts** ([page tarifs](https://www.hubspot.com/pricing/crm), [FAQ HubSpot](https://knowledge.hubspot.com/articles/kcs_article/getting-started/frequently-asked-questions)) ; 2 000 e-mails par mois | Si un 2e commercial arrive et que la liste dépasse ce que gère un tableur. 1 000 contacts suffisent pour le Grand Annecy |
| **Notion** | Oui pour un usage individuel | Pages illimitées en solo, fichiers de 5 Mo maximum ; limites d'équipe contradictoires selon les sources ([eesel](https://www.eesel.ai/fr/blog/notion-pricing)) | Fiches de connaissance (objections, partenaires), pas un CRM |
| **Folk** | Non (pas de plan gratuit) | Standard 24 à 30 $ par utilisateur et par mois selon la facturation ([CostBench](https://costbench.com/software/crm/folk/), [PricingSaaS](https://pricingsaas.com/companies/folk)) | Pas nécessaire |
| **Pipedrive** | Non (essai de 14 jours) | Lite 14 € par utilisateur et par mois en annuel (24 € en mensuel), Growth 39 € ([Meetergo, vérifié le 07/08/2026](https://meetergo.com/fr/blog/pipedrive-tarif)) | Pas avant d'avoir des revenus récurrents |

---

## 2. Cadre légal de la prospection B2B en France

Rappel : un restaurant est souvent une **entreprise individuelle**. Son nom, son mobile et son e-mail sont alors des **données personnelles** : le RGPD s'applique, même en B2B. Le nom du gérant d'une SARL aussi.

### 2.1 Tableau de synthèse par canal

| Canal | Règle B2B (vers un professionnel) | Ce que fait Polyglotte | Sources |
|---|---|---|---|
| **E-mail** | Pas de consentement préalable si le message est **en rapport avec la profession** de la personne. Il faut l'informer et lui permettre de s'opposer simplement et gratuitement. Chaque message indique l'identité de l'expéditeur et un moyen de se désinscrire. Les adresses **génériques** (`contact@`, `info@`) sont des coordonnées de la personne morale, non soumises au consentement. Les adresses **nominatives** professionnelles relèvent du même régime d'opposition, si le message vise la fonction de la personne | E-mail J+7 (scripts § 4.2) à l'adresse publiée sur la fiche ou le site. Toujours une ligne « Vous ne souhaitez plus recevoir de message ? Répondez STOP » | [CNIL, e-mail, SMS et automates](https://www.cnil.fr/fr/la-prospection-commerciale-par-courrier-electronique-sms-mms-et-automate-dappel), [CNIL, règles d'or](https://www.cnil.fr/fr/les-regles-dor-de-la-prospection-par-courrier-electronique-0), [CCI Paris IDF](https://www.entreprises.cci-paris-idf.fr/fiches-pratiques/prospection-commerciale-par-voie-electronique) ; art. L34-5 du CPCE |
| **Téléphone** | **Depuis le 11 août 2026**, le démarchage téléphonique des **particuliers** exige leur consentement préalable (art. 13 de la loi n° 2025-594 du 30 juin 2025, qui réécrit l'art. L223-1 du code de la consommation). Le consentement vaut 1 an au maximum, sa preuve se garde 3 ans, et l'amende va jusqu'à 375 000 € pour une personne morale ([donneespersonnelles.fr](https://donneespersonnelles.fr/demarchage-telephonique), [Actu-Juridique](https://www.actu-juridique.fr/affaires/droit-economique/reforme-du-demarchage-telephonique-mise-en-pratique-depuis-le-11-aout-2026/)). **Les professionnels ne sont pas soumis au consentement : ils peuvent s'opposer**, et une information leur est due ([CNIL, téléphone](https://www.cnil.fr/fr/prospection-commerciale-par-telephone-hors-automate-dappel-quelles-sont-les-regles)). Le texte vise le « consommateur » ([DGCCRF](https://www.economie.gouv.fr/dgccrf/les-fiches-pratiques/demarchage-telephonique-professionnels-mettez-vous-en-conformite-avec-la-reglementation)). Aucune source trouvée ne dit en toutes lettres que le B2B est exclu : la lecture « B2B = opposition » s'appuie sur la fiche CNIL | Appeler **uniquement le numéro du restaurant** publié sur la fiche ou le site, jamais un mobile personnel trouvé ailleurs. Le but : fixer un rendez-vous de 10 minutes (parade § 6 du go-to-market). Dire dès le début qui l'on est, d'où vient le numéro (« votre fiche Google »), et noter tout refus | CNIL, DGCCRF, ci-contre |
| **Bloctel** | Bloctel visait les consommateurs : la CNIL parle des « résidents » qui ne veulent plus être démarchés ([CNIL](https://www.cnil.fr/fr/bloctel-un-nouveau-site-pour-vous-opposer-au-demarchage-telephonique)). Avec le passage au consentement préalable, **Bloctel cesse d'exister au 11 août 2026** ([Ma Commune](https://www.macommune.info/demarchage-telephonique-une-interdiction-generalisee-entre-en-vigueur-le-11-aout-2026/)) | Sans objet. On tient sa **propre liste d'opposition** (§ 2.4) | — |
| **Horaires d'appel** | Avant le 11/08/2026 : du lundi au vendredi, 10 h-13 h et 14 h-20 h (règle pour les consommateurs). Un décret doit fixer les nouveaux créneaux ([CNIL](https://www.cnil.fr/fr/prospection-commerciale-par-telephone-hors-automate-dappel-quelles-sont-les-regles), [Swim Legal](https://www.swim.legal/blog/demarchage-telephonique-2026-loi)) | En pratique, appeler un restaurant **10 h-11 h 30 ou 15 h-17 h**, jamais pendant le service | — |
| **SMS** | Même régime que l'e-mail : en B2B, information et opposition, message en rapport avec la profession, identité de l'expéditeur et moyen de se désinscrire (« STOP ») ([CNIL, SMS](https://www.cnil.fr/fr/sms-caractere-commercial-ayez-les-bons-reflexes), [CNIL](https://www.cnil.fr/fr/la-prospection-commerciale-par-courrier-electronique-sms-mms-et-automate-dappel)) | SMS J+3 après une visite (scripts § 4.1), avec « Répondez STOP pour ne plus être contacté » | — |
| **WhatsApp** | La loi traite WhatsApp comme un message électronique. **En plus**, la politique de Meta impose un **opt-in** avant tout message d'une entreprise : la personne a donné son numéro et a accepté de recevoir des messages de cette entreprise, nommée clairement. Sanction possible : suspension du compte WhatsApp Business ([Meta, opt-in](https://developers.facebook.com/documentation/business-messaging/whatsapp/getting-opt-in)) | **Demander à la visite** : « Je peux vous écrire sur WhatsApp ? » et cocher « opt-in WhatsApp » dans les notes du CRM. Sans accord, SMS ou e-mail | — |
| **Porte-à-porte** | Pas de règle CNIL propre. Code de la consommation : un contrat signé **hors établissement** avec un professionnel de **5 salariés ou moins**, pour un service hors de son activité principale, donne droit aux protections du consommateur (art. L221-3) : 14 jours de rétractation, aucun paiement avant 7 jours ([Cass. 31/08/2022](https://www.labase-lextenso.fr/jp-commente/cc/2022-08/21-11-455-CC-31082022-21_11455), [Actu-Juridique](https://www.actu-juridique.fr/civil/obligations-contrats/retour-sur-lapplication-entre-professionnels-des-regles-relatives-aux-contrats-conclus-hors-etablissements/)) | Déjà prévu : CGV, formulaire de rétractation, lien de paiement à J+8 ([juridique-checklist.md](juridique-checklist.md)) | — |
| **Automates d'appel, e-mailing de masse** | Encadrés de près ([CNIL](https://www.cnil.fr/fr/la-prospection-commerciale-par-courrier-electronique-sms-mms-et-automate-dappel)) | **Jamais** | — |

### 2.2 Constituer un fichier à partir de sources publiques

- **Une donnée publique reste une donnée personnelle.** Les coordonnées publiées en ligne ne se réutilisent pas librement, ni à l'insu des personnes ([CNIL, réutilisation pour le démarchage](https://www.cnil.fr/fr/la-reutilisation-des-donnees-publiquement-accessibles-en-ligne-des-fins-de-demarchage-commercial)).
- **Base légale :** en B2B, l'**intérêt légitime** peut être retenu si le réutilisateur le démontre et si les intérêts des personnes ne prévalent pas ([CNIL, réutiliser les données diffusées](https://www.cnil.fr/fr/comment-reutiliser-les-donnees-diffusees)). Polyglotte peut le démontrer : il propose aux restaurants un service lié à leur métier, à partir de leurs informations professionnelles.
- **Information (art. 14 du RGPD) :** quand les données ne viennent pas de la personne, il faut l'informer au plus tard **au premier contact**, et dans tous les cas **dans le mois** qui suit la collecte. L'information indique la **source** des données, la finalité, la durée de conservation et le droit d'opposition. L'exception des « efforts disproportionnés » ne joue que dans des cas très limités, et le caractère public des données ne dispense pas d'informer ([recommandations CNIL aux réutilisateurs, juin 2024](https://www.cnil.fr/sites/default/files/2024-06/recommandations_reutilisateurs_donnees_publiees_sur_internet.pdf)).
- **Ce qu'on ajoute concrètement** au bas de l'audit imprimé et de chaque e-mail (texte proposé) :

  > *Polyglotte a préparé cet audit à partir d'informations publiques : votre fiche Google, le répertoire Sirene et OpenStreetMap. Nous conservons le nom, l'adresse et le téléphone de votre établissement, et nos observations, pour vous proposer nos services, pendant 3 ans au plus après notre dernier échange. Pour ne plus être contacté ou faire supprimer ces données, il suffit de le dire ou d'écrire à [e-mail]. Plus d'informations : [site]/mentions-legales.html.*

  À reporter aussi dans la page de confidentialité du site. **Ce fichier-ci ne modifie pas `mentions-legales.html`** : c'est une action à prévoir.
- **Minimisation :** ne garder que ce qui sert. Pas de date de naissance du dirigeant, pas de vie privée, pas de texte d'avis client archivé avec le nom de l'auteur.

### 2.3 Durée de conservation

| Donnée | Durée | Source |
|---|---|---|
| Prospect non client | **3 ans** à partir de la collecte ou du **dernier contact venant du prospect** (une demande, un clic, une réponse ; ouvrir un e-mail ne compte pas). Au bout de 3 ans, on peut lui demander s'il veut encore être sollicité ; sans réponse, on supprime | [Référentiel CNIL « gestion commerciale »](https://www.cnil.fr/sites/cnil/files/atoms/files/referentiel_traitements-donnees-caractere-personnel_gestion-activites-commerciales.pdf), [CNIL, questions-réponses](https://www.cnil.fr/fr/questions-reponses-sur-les-referentiels-relatifs-la-gestion-des-activites-commerciales-et-des) |
| Client | Durée du contrat, puis 3 ans pour la prospection ; factures 10 ans en archive comptable | Idem |
| Liste d'opposition | **3 ans au minimum**, utilisée seulement pour respecter les refus | Idem, [CNIL, liste repoussoir](https://www.cnil.fr/fr/comment-utiliser-une-liste-repoussoir-pour-respecter-lopposition-la-prospection) |

Dans `audit/`, le statut « Perdu » + une date dans `notes` suffisent pour purger une fois par an (en janvier).

### 2.4 Droit d'opposition

- Pour la prospection, l'opposition est **absolue** : sans justification, à tout moment, gratuitement. Le responsable doit arrêter ([CNIL, droit d'opposition](https://www.cnil.fr/fr/comprendre-mes-droits/le-droit-dopposition-refuser-lutilisation-de-vos-donnees)).
- **En pratique :** un « ne revenez pas » ou un « STOP » vaut opposition, à l'oral comme à l'écrit. Passer le prospect en « Perdu » et écrire `OPPOSITION AAAA-MM-JJ, canal` dans les notes. Le garder dans une liste « ne pas contacter » (nom + SIRET, rien d'autre) pour ne pas le réimporter à la prochaine extraction Sirene.

### 2.5 Faux avis et sollicitation d'avis

- Les **faux avis** sont une pratique commerciale trompeuse depuis la transposition de la directive de 2019 ([Assemblée nationale](https://www.assemblee-nationale.fr/dyn/16/amendements/1674/AN/380.pdf)). La DGCCRF a contrôlé plus de 1 200 établissements depuis juillet 2023 avec son outil « Polygraphe » ([article d'avocat, 2026](https://consultation.avocat.fr/blog/etienne-bucher/article-2981104-faux-avis-en-ligne-etat-du-droit-et-des-risques-en-2026.html)). Article exact du code de la consommation : à vérifier sur Légifrance.
- **Google** interdit les avis obtenus en échange d'une contrepartie (réduction, cadeau, tirage au sort) et le *review gating*, qui consiste à n'inviter que les clients contents ([Applause](https://www.applausehq.com/blog/googles-rules-for-incentivizing-reviews), [LaunchCodex](https://launchcodex.com/blog/seo-geo-ai/google-business-profile-review-policy-update/), synthèses tierces de la politique Google). Le chevalet QR invite **tous** les clients, sans contrepartie (objection 12 des scripts).

### 2.6 Les 3 risques légaux principaux

1. **Scraper Google Maps** (Outscraper, Apify, PhantomBuster, Data Miner) : violation des conditions Google (clauses « No Scraping » et « No Caching »), qui peut faire perdre le compte Google. Il faut un compte Google intact pour gérer les fiches des clients. Les noms des auteurs d'avis étant des données personnelles, c'est aussi un fichier RGPD sans base légale.
2. **Contacter sans information ni opposition** : un fichier tiré de sources publiques sans la mention de l'art. 14, ou un refus non respecté. C'est l'objet des plaintes que reçoit la CNIL (cas Kaspr : 240 000 €). Ajouter WhatsApp sans opt-in, c'est risquer aussi la suspension du compte.
3. **Glisser vers le B2C** : appeler un mobile personnel ou démarcher un loueur en meublé particulier par téléphone. Depuis le 11 août 2026, il faut alors un consentement préalable, sous peine d'amende administrative (jusqu'à 375 000 € pour une personne morale) et de nullité du contrat. À retenir pour la verticale « loueurs » : un particulier qui loue un meublé n'est pas un professionnel au sens de ces règles. À vérifier au cas par cas.

---

## 3. Recommandation : la stack de prospection à 0 €

### 3.1 La combinaison exacte

| Étape | Outil | Coût | Durée estimée |
|---|---|---|---|
| ① Liste exhaustive légale | **API Recherche d'entreprises**, filtres NAF + `epci=200066793` (code du Grand Annecy, voir [recherche.md](recherche.md)) + `etat_administratif=A` | 0 € | 1 h la première fois |
| ② Site, téléphone, horaires, position | **Overpass** (une requête) | 0 € | 30 min |
| ③ Prospects chauds | **BODACC** : créations et ventes de fonds en Haute-Savoie (74), mot-clé « restaura », 12 derniers mois | 0 € | 30 min par mois |
| ④ Fusion, dédoublonnage, score | **Google Sheets** | 0 € | 2 h la première fois |
| ⑤ Qualification des ~150 meilleurs | **Lecture humaine de la fiche Google** + **Claude** (prompt du § 5) | 0 € (claude.ai) ou quelques centimes (API) | 5 à 8 min par restaurant |
| ⑥ Pipeline, audits, relances | **`audit/`** (import CSV) + export CSV chaque soir vers Google Sheets | 0 € | — |
| Optionnel | **Google Places API, Text Search Essentials (IDs seulement)** pour stocker le `place_id` et ouvrir la fiche en un clic | 0 € selon la grille Google, mais carte bancaire obligatoire : poser un **plafond de quota** dans la console | 1 h de mise en place |

**À ne pas acheter :** Pharow, Kaspr, Lusha, lemlist, Waalaxy, La Growth Machine, ni les scrapers. Un restaurateur se convainc par un audit imprimé posé sur sa table, pas par une séquence d'e-mails.

### 3.2 Requêtes prêtes à adapter

> Écrites d'après la documentation relayée. **Aucune n'a pu être testée** depuis l'environnement de rédaction : tester sur 1 page avant de tout lancer.

**① Sirene, via l'API Recherche d'entreprises** (navigateur ou script) :

```
https://recherche-entreprises.api.gouv.fr/search?activite_principale=56.10A,56.10B,56.10C&epci=200066793&etat_administratif=A&per_page=25&page=1
```

- Paginer avec `page=2, 3…` jusqu'à une réponse vide, en laissant au moins 0,2 s entre deux appels (limite de 7 par seconde).
- Refaire la même extraction avec `56.30Z` pour les bars.
- Champs à garder : `siren`, `nom_complet`, enseignes du siège ou de l'établissement, adresse, `date_creation`, `tranche_effectif_salarie`, `dirigeants` (nom et qualité), coordonnées si présentes, et `matching_etablissements`, qui liste les établissements situés dans la zone.
- Si `epci` n'est pas accepté : `departement=74` puis filtrer sur la liste des 34 communes.

**② OpenStreetMap, sur [overpass-turbo.eu](https://overpass-turbo.eu)**. Les EPCI sont taggés `boundary=local_authority` avec leur SIREN dans `ref:FR:SIREN` ([wiki OSM](https://wiki.openstreetmap.org/wiki/FR:Key:local_authority:FR)) :

```
[out:csv(::type,::id,name,amenity,cuisine,"addr:housenumber","addr:street","addr:postcode","addr:city",phone,"contact:phone",website,"contact:website",opening_hours,::lat,::lon;true;";")][timeout:120];
relation["boundary"="local_authority"]["ref:FR:SIREN"="200066793"];
map_to_area->.ga;
nwr["amenity"~"^(restaurant|cafe|bar|fast_food|pub)$"](area.ga);
out center;
```

Si la zone ne remonte rien, remplacer la 2e ligne par `relation["boundary"="local_authority"]["name"="Grand Annecy"];`.

**③ BODACC.** Sur le portail `bodacc-datadila.opendatasoft.com`, jeu `annonces-commerciales`, onglet de filtres, puis export CSV, sans écrire de code. Filtres : département 74, famille « Créations » puis « Ventes et cessions », recherche plein texte « restaura », 12 derniers mois. Garder les annonces dont la ville est dans le Grand Annecy.

**④ Fusion dans Google Sheets :**
1. Un onglet par source.
2. Rapprocher Sirene et OSM par nom normalisé (minuscules, sans accents, sans « SARL ») + code postal. En cas de doute, trancher à la main au moment de la lecture Google.
3. Marquer les BODACC par SIREN.
4. Exclure les chaînes et franchises (décision au siège), les établissements fermés et les prospects de la liste d'opposition.
5. Affecter le quartier `audit/` d'après la commune et l'adresse : Vieille ville · Bords du lac / Pâquier · Centre / gare · Annecy-le-Vieux · Sévrier / rive ouest · Talloires / rive est · Autre.

Ordre de grandeur annoncé : 700 à 900 restaurants. **Non vérifié** : la requête ① donnera le chiffre réel, en sachant que les entrepreneurs en diffusion partielle n'y figurent pas.

### 3.3 Signal → où le trouver → poids dans la priorité

Score de priorité **sur 14** : la base sur 10 du go-to-market (§ 2, point 4), plus 4 points de bonus. Ne pas le confondre avec le **score d'audit** calculé par `audit/`, sur 100, où un score bas veut dire beaucoup de progrès à faire.

| Signal | Où le trouver | Poids | Note |
|---|---|---|---|
| Avis en langue étrangère **sans réponse** (sur les 30 derniers) | Fiche Google, lecture humaine | **0 à 4** (0 = aucun ; 1 = 1-2 ; 2 = 3-4 ; 3 = 5-7 ; 4 = 8 ou plus) | **Signal n° 1** : c'est la promesse de Polyglotte. Compter sur 30 avis, comme l'échantillon de `audit/` |
| Volume d'avis élevé | Fiche Google | **0 à 2** (0 si moins de 100 ; 1 de 100 à 200 ; 2 au-delà de 200) | Beaucoup d'avis = beaucoup de passage et de travail de réponse |
| Menu non traduit ou absent | Fiche Google (onglet Menu), site, photos de carte | **0 à 2** (2 = aucun menu ou FR seul ; 1 = FR + EN ; 0 = multilingue) | Allergènes absents : le noter, c'est une priorité de l'audit |
| Zone touristique | Adresse + quartier | **0 à 2** (2 = Vieille ville, bords du lac, Talloires, Sévrier, Veyrier ; 1 = centre / gare, Annecy-le-Vieux ; 0 = zones résidentielles et d'activités) | Le restaurant est aussi au guide de l'office de tourisme : +1 dans la limite de 2 |
| **Bonus** : création ou reprise depuis moins de 12 mois | BODACC (créations, ventes de fonds), `date_creation` de Sirene | **+2** | Nouveau propriétaire = fiche Google à reprendre, carte à refaire. Le meilleur moment pour vendre |
| **Bonus** : pas de site web | OSM `website` vide **et** fiche Google sans site | **+1** | La fiche Google devient la vitrine principale |
| **Bonus** : taux de réponse global sous 50 % | Fiche Google | **+1** | Personne ne s'occupe des avis |
| Malus et exclusions | — | Exclure | Chaîne ou franchise ; plus de 50 salariés ; opposition enregistrée ; établissement fermé définitivement. Note sous 3,5 : visiter plus tard, la priorité du restaurant est ailleurs |
| Modificateur de calendrier | Fiche Google (horaires), téléphone | Ordre de passage, pas de points | **Fermeture annuelle en novembre : passer avant** (go-to-market). Noter le jour de fermeture |

**Règle de travail :**
- Qualifier sur Google seulement les ~150 meilleurs selon les signaux gratuits (zone, BODACC, site absent). C'est le pré-score sur 5 qu'on peut calculer sans ouvrir Google.
- Calculer ensuite le score complet.
- Les 40 meilleurs reçoivent un audit imprimé.

### 3.4 Format d'import dans `audit/`

L'import (`audit/audit.js`, fonction `depuisCsv`) accepte `;` ou `,`, exige une colonne `nom` et **ignore les colonnes inconnues**. Il n'existe pas de colonne adresse, téléphone ou SIRET : tout cela va dans `notes`, 2 000 caractères maximum. Le score d'audit est recalculé à l'import.

| Colonne | Valeurs acceptées |
|---|---|
| `nom` | texte (80 caractères maximum) |
| `quartier` | une des 7 valeurs exactes du § 3.2, sinon « Autre » |
| `note` | décimal, `4,4` ou `4.4` |
| `totalAvis`, `sansReponse`, `etrangers`, `etrangersSansReponse` | entiers. Comptages sur les **30 derniers avis**, vide = non renseigné |
| `langues` | `EN|DE|IT|ES|NL|autre` |
| `menu` | `aucun`, `fr`, `fr-en`, `multi` |
| `allergenes` | `non`, `partiel`, `oui` |
| `horaires`, `photos`, `lienMenu`, `site` | `oui` / `non` |
| `statut` | `À visiter` (défaut), `Audit remis`, `Démo`, `Signé Pack`, `Abonné`, `Perdu` |
| `relance` | `AAAA-MM-JJ` |
| `notes` | texte libre |

Exemple fictif :

```
nom;quartier;note;totalAvis;sansReponse;etrangers;etrangersSansReponse;langues;menu;allergenes;horaires;photos;lienMenu;site;statut;relance;notes
Restaurant Exemple;Vieille ville;4,4;812;18;9;8;EN|DE;fr;non;oui;non;non;oui;À visiter;2026-10-28;"PRIO=12/14 | SIRET <à compléter> | <adresse> 74000 Annecy | tél <publié sur la fiche> | reprise BODACC <mois> | fermé lundi, fermeture annuelle nov. | place_id <si API> | sources : Sirene, OSM, Google (lecture le 2026-10-20)"
```

Mettre `PRIO=` en tête des notes permet de trier visuellement. Le tri du pipeline se fait par score d'audit, pas par priorité.

---

## 4. Routine hebdomadaire du développeur commercial (5 à 8 h)

Cette routine vaut **après le sprint** de 30 jours (« rythme de croisière : 2 demi-journées de visite par semaine », go-to-market § 8). Pendant le sprint, on suit le plan jour par jour, qui demande environ 30 h par semaine.

### 4.1 Volumes cibles par semaine

| Étape | Volume | Pourquoi ce chiffre |
|---|---|---|
| Prospects qualifiés (fiche Google lue, score calculé) | **15** | 5 à 8 min chacun avec Claude, soit environ 1 h 30 |
| Audits générés et imprimés | **6** | Les meilleurs scores de la semaine |
| Visites | **8 à 9** : 6 remises d'audit + 2 ou 3 retours (démo, signature, livraison) | 2 créneaux de 15 h-17 h, 4 à 5 visites par créneau, en grappe de rues |
| Relances | toutes celles qui sont dues : J+3 SMS ou WhatsApp (si opt-in), J+7 e-mail, J+14 dernier message | Aucune relance en retard (seuil d'alerte du tableau de bord) |
| Résultat attendu | ~1 pack par semaine | Hypothèses du go-to-market : 50 % des audits remis donnent une démo, 50 % des démos une signature. À recaler avec les vrais taux du sprint |

### 4.2 Semaine type

| Jour | Créneau | Tâche | Durée |
|---|---|---|---|
| Lundi | soir | Veille BODACC (1re semaine du mois) et nouvelles créations Sirene. Relances dues. Choix des 15 prospects à qualifier | 45 min |
| Mardi | matin ou soir | Qualification de 15 fiches Google + Claude (§ 5), import CSV dans `audit/`, impression de 6 audits | 1 h 45 |
| Mercredi | **15 h-17 h** | Tournée n° 1 : 3 remises d'audit + 1 ou 2 retours | 2 h |
| Jeudi | soir | Relances J+3 et J+7. Préparer une vraie réponse à un avis étranger pour chaque démo prévue | 30 min |
| Vendredi | **15 h-17 h** | Tournée n° 2 : 3 remises + 1 retour | 2 h |
| Dimanche | soir | KPI de la semaine dans `kpi-tracker.csv`, export CSV de `audit/` vers Google Sheets | 20 min |
| | | **Total** | **~7 h 20** |

### 4.3 Créneaux et saisons

- **Visites : 15 h-17 h**, le creux entre les deux services. En plan B, **10 h-11 h 30** pendant la mise en place. Jamais pendant un service, jamais le jour de fermeture.
- **Appels :** 10 h-11 h 30 ou 15 h-17 h, pour fixer un rendez-vous de 10 minutes, jamais pour vendre au téléphone.
- **Saisons :**
  - **Janvier à mars :** la meilleure période, on prépare la saison (« tout est prêt pour Pâques »).
  - **Septembre et octobre :** bonne période, le bilan de saison est frais.
  - **Avril à juin :** possible, le matin.
  - **Juillet et août : pas de nouvelle prospection.** Le patron est débordé. Seulement les livraisons et le suivi des clients, et des messages courts pour fixer des rendez-vous en septembre.
  - **Novembre :** beaucoup de fermetures annuelles. Passer **avant** et livrer pendant la fermeture.
- **Relances :** cadence J+3 / J+7 / J+14, puis silence jusqu'en mars (scripts § 4.3). Au-delà de 3 relances sans réponse : statut « Perdu », motif « sans réponse », et rien de plus avant la saison suivante.

---

## 5. Agents IA de prospection : Claude en assistant de qualification

### 5.1 Ce qu'on confie à Claude

- **Transformer une fiche lue par un humain en ligne CSV** pour `audit/`, avec les 3 priorités de l'audit et une accroche pour le pitch de porte.
- **Rédiger 1 brouillon de réponse** à un avis étranger, à imprimer dans l'audit (levier du go-to-market § 6). On le relit, on ne le publie pas.
- **Préparer la visite** : objection probable, plats à traduire en démo.

**Entrée :** ce que le commercial a copié ou noté lui-même depuis la fiche Google, le site du restaurant et l'Annuaire des entreprises. **Remplacer les noms des auteurs d'avis par leurs initiales** avant de coller (minimisation RGPD). Claude ne va pas chercher la fiche lui-même.

### 5.2 Prompt modèle (à copier dans claude.ai ou à passer par l'API)

```
Tu es l'assistant de qualification de Polyglotte, un service local à Annecy qui répond aux avis Google
des restaurants indépendants dans la langue de chaque client, crée un menu QR en 5 langues (FR, EN, DE, IT, ES)
avec les 14 allergènes, et optimise la fiche Google. Le restaurateur n'ouvre aucun logiciel.

Je te donne ci-dessous ce que j'ai relevé MOI-MÊME sur la fiche publique d'un restaurant
(les noms des auteurs d'avis sont remplacés par des initiales).

RÈGLES STRICTES
- N'invente rien. Si une information manque, laisse le champ vide et signale-le dans « manques ».
- Compte uniquement sur les 30 derniers avis fournis (ou moins s'il y en a moins).
- « Sans réponse » = aucun texte « Réponse du propriétaire » sous l'avis.
- Une langue étrangère = toute langue autre que le français.
- Aucune promesse chiffrée (« +20 % de clients », « plus d'étoiles ») : on promet du temps gagné,
  des réponses dans la langue du client et un menu clair.
- Ton : simple, respectueux, sans jargon. Le patron lit l'audit en 2 minutes.

PRODUIS EXACTEMENT 5 BLOCS

1) LIGNE_CSV : une seule ligne, séparateur « ; », colonnes dans cet ordre :
nom;quartier;note;totalAvis;sansReponse;etrangers;etrangersSansReponse;langues;menu;allergenes;horaires;photos;lienMenu;site;statut;relance;notes
- quartier ∈ {Vieille ville | Bords du lac / Pâquier | Centre / gare | Annecy-le-Vieux | Sévrier / rive ouest | Talloires / rive est | Autre}
- langues : codes séparés par | parmi EN, DE, IT, ES, NL, autre (langues des avis étrangers)
- menu ∈ {aucun, fr, fr-en, multi} ; allergenes ∈ {non, partiel, oui}
- horaires, photos (récentes = moins de 6 mois), lienMenu, site : oui / non
- statut = À visiter ; relance vide
- notes commence par « PRIO=x/14 » (barème ci-dessous), puis adresse | téléphone | SIRET | jour de fermeture | source et date du relevé

2) PRIORITÉ (barème sur 14, détaille chaque point)
- avis étrangers sans réponse : 0 → 0 ; 1-2 → 1 ; 3-4 → 2 ; 5-7 → 3 ; 8+ → 4
- total d'avis : <100 → 0 ; 100-200 → 1 ; >200 → 2
- menu : aucun ou fr → 2 ; fr-en → 1 ; multi → 0
- zone : Vieille ville, Bords du lac, Talloires, Sévrier, Veyrier → 2 ; Centre / gare, Annecy-le-Vieux → 1 ; autre → 0
- bonus : création ou reprise < 12 mois → +2 ; pas de site web → +1 ; taux de réponse global < 50 % → +1

3) TROIS_PRIORITÉS de l'audit, de la plus importante à la moins importante.
Choisis parmi ces constats, dans cet ordre de poids, et garde les 3 premiers qui s'appliquent :
  a. aucun avis → « Aucun avis Google pour l'instant… »
  b. N avis en langue étrangère sans réponse (cite les publics : anglophones, germanophones…)
  c. N des 30 derniers avis sans réponse
  d. menu absent, FR seul, ou FR+EN seulement
  e. allergènes non indiqués ou partiels (les 14 allergènes réglementaires sont obligatoires)
  f. fiche Google incomplète (horaires, photos de plus de 6 mois, pas de lien menu, pas de site)
Pour chacune : un constat chiffré d'une phrase + l'action Polyglotte en une phrase.

4) ACCROCHE (pitch de porte, 2 phrases, avec les vrais chiffres) :
« J'ai regardé votre fiche Google : vous avez [N] avis ces derniers mois, dont [N] en [langues],
et [N] sont restés sans réponse. »

5) BROUILLON_RÉPONSE à UN avis étranger sans réponse (le plus récent à 4 ou 5 étoiles, sinon le plus récent) :
dans la langue de l'avis, 40 à 90 mots, reprend un détail précis de l'avis, sans promesse,
signé « [Prénom du gérant] — [Nom du restaurant] », suivi de sa traduction française.
Marque-le « BROUILLON — à faire valider par le restaurateur, ne pas publier ».

Termine par « manques : » (liste des informations absentes) et « doutes : » (ce qui est incertain).

=== MES RELEVÉS ===
Nom :
Adresse / commune :
Téléphone publié :
SIRET / date de création ou de reprise (Annuaire des entreprises, BODACC) :
Note Google / nombre total d'avis :
Horaires affichés (oui/non, jour de fermeture) :
Photos : date de la plus récente publiée par le propriétaire :
Lien menu sur la fiche (oui/non) / site web (URL ou « aucun ») :
Menu : langues disponibles, allergènes indiqués (oui/partiel/non) :
Référencé par l'office de tourisme (oui/non) :
30 derniers avis (une ligne par avis : date | note | langue | initiales | résumé en 1 phrase | réponse du propriétaire oui/non) :
1.
2.
...
```

**Comment l'utiliser :**
1. Remplir la section « Mes relevés » pendant la lecture de la fiche.
2. Coller dans Claude.
3. Copier `LIGNE_CSV` dans un fichier `import-semaine.csv`, sous l'en-tête du § 3.4, puis importer dans `audit/`.
4. Les 3 priorités de Claude servent à **vérifier** celles que `audit/` calcule à partir des mêmes chiffres. Un écart signale une saisie fausse.
5. Le brouillon de réponse passe par la même relecture que pour les clients ([tools/README.md](../tools/README.md)).

### 5.3 Ce qu'il ne faut PAS automatiser

| Ne pas faire | Pourquoi |
|---|---|
| Faire lire ou scraper Google Maps par un agent ou un robot (navigateur piloté, Apify, Outscraper…) | Conditions Google (« No Scraping ») et RGPD (noms des auteurs d'avis). Risque de perdre le compte Google qui sert aux clients |
| Envoyer des e-mails, SMS ou messages WhatsApp en masse générés par l'IA | Régime d'opposition B2B, opt-in WhatsApp, réputation du domaine. Une ville de 135 000 habitants, où les restaurateurs se parlent, ne pardonne pas le spam. Chaque message part à la main, à quelqu'un qu'on a vu ou dont on a lu la fiche |
| Publier automatiquement des réponses aux avis | Promesse des CGV et des scripts : aucune réponse publiée sans relecture humaine |
| Écrire, acheter ou « suggérer » des avis, même positifs | Pratique commerciale trompeuse et politique Google. Refus net (objection 12) |
| Inviter seulement les clients contents à laisser un avis (*review gating*) | Interdit par Google |
| Automatiser LinkedIn (Waalaxy, La Growth Machine, PhantomBuster) | Inutile pour les restaurateurs, et risque CGU |
| Deviner ou acheter des e-mails ou mobiles personnels (Kaspr, Lusha, motifs prenom@) | Données personnelles sans information. Précédent Kaspr (240 000 €) |
| Appeler par automate ou avec un message vocal préenregistré | Régime renforcé ([CNIL](https://www.cnil.fr/fr/la-prospection-commerciale-par-courrier-electronique-sms-mms-et-automate-dappel)) et contraire à l'image d'un service local |
| Laisser l'IA décider qui exclure ou fixer le prix | Le score aide à trier. La décision de visiter, et le prix (jamais sous 145 €), restent humains |

---

## 6. Sources principales (récapitulatif)

- **Données publiques :**
  - [API Recherche d'entreprises (doc)](https://recherche-entreprises.api.gouv.fr/docs/) · [discussions data.gouv.fr](https://www.data.gouv.fr/dataservices/api-recherche-dentreprises/discussions)
  - [INSEE Sirene, actualités juin 2026](https://www.insee.fr/fr/information/9019311) · [connexion à l'API Sirene](https://static.insee.fr/api-sirene/Insee_API_publique_modalites_connexion.pdf) · [statut de diffusion](https://www.insee.fr/fr/information/7456564)
  - [BPE](https://www.insee.fr/fr/metadonnees/source/operation/s2216/presentation)
  - [Overpass](https://wiki.openstreetmap.org/wiki/Overpass_API) · [ODbL](https://wiki.openstreetmap.org/wiki/Open_Database_License)
  - [API BODACC](https://www.data.gouv.fr/dataservices/672cf66ea47b8d4c15d13d5b) · [présentation DILA](https://echanges.dila.gouv.fr/OPENDATA/BODACC/DILA_API-BODACC_Presentation_20260327.pdf)
  - [Ville d'Annecy sur data.gouv.fr](https://www.data.gouv.fr/organizations/ville-dannecy-1/datasets)
- **Google :** [tarifs Maps Platform](https://developers.google.com/maps/billing-and-pricing/pricing) · [politiques Places API](https://developers.google.com/maps/documentation/places/web-service/policies) · [conditions Maps Platform](https://cloud.google.com/maps-platform/terms)
- **CNIL :**
  - [e-mail, SMS, automates](https://www.cnil.fr/fr/la-prospection-commerciale-par-courrier-electronique-sms-mms-et-automate-dappel) · [téléphone](https://www.cnil.fr/fr/prospection-commerciale-par-telephone-hors-automate-dappel-quelles-sont-les-regles)
  - [réutilisation des données publiques pour le démarchage](https://www.cnil.fr/fr/la-reutilisation-des-donnees-publiquement-accessibles-en-ligne-des-fins-de-demarchage-commercial) · [recommandations aux réutilisateurs](https://www.cnil.fr/sites/default/files/2024-06/recommandations_reutilisateurs_donnees_publiees_sur_internet.pdf)
  - [référentiel gestion commerciale](https://www.cnil.fr/sites/cnil/files/atoms/files/referentiel_traitements-donnees-caractere-personnel_gestion-activites-commerciales.pdf) · [droit d'opposition](https://www.cnil.fr/fr/comprendre-mes-droits/le-droit-dopposition-refuser-lutilisation-de-vos-donnees) · [sanction Kaspr](https://www.cnil.fr/fr/aspiration-de-donnees-sanction-de-240-000-euros-lencontre-de-la-societe-kaspr)
- **Démarchage :** [DGCCRF](https://www.economie.gouv.fr/dgccrf/les-fiches-pratiques/demarchage-telephonique-professionnels-mettez-vous-en-conformite-avec-la-reglementation) · [Actu-Juridique, réforme du 11 août 2026](https://www.actu-juridique.fr/affaires/droit-economique/reforme-du-demarchage-telephonique-mise-en-pratique-depuis-le-11-aout-2026/) · [Meta, opt-in WhatsApp](https://developers.facebook.com/documentation/business-messaging/whatsapp/getting-opt-in)
