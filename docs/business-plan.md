# Polyglotte — Business plan 12 mois (Annecy, oct. 2026 → oct. 2027)

> Document de travail. Chaque chiffre externe a une source (lien). Tout le reste est une **hypothèse**, signalée comme telle. Les données de base viennent de [recherche.md](recherche.md).

---

## 1. Résumé en 10 lignes

1. Polyglotte fait, à la place du restaurateur, ce qu'il n'a pas le temps de faire : sa fiche Google, son menu en 5 langues avec allergènes, ses réponses aux avis.
2. Cible : les restaurants indépendants d'Annecy, une ville où 44 % de la clientèle de l'été 2025 était étrangère ([Sources du Lac](https://www.sources-lac-annecy.com/app/uploads/2026/06/synthese-sources-du-lac-e25.pdf)).
3. Le besoin est prouvé : 40 % des TPE-PME utilisent l'IA, mais seules 19 % paient un outil ([France Num 2026](https://www.entreprises.gouv.fr/espace-presse/barometre-france-num-2026-quatre-tpe-pme-sur-dix-utilisent-desormais-lintelligence)). Elles veulent le résultat, pas l'outil.
4. Offre : Pack Démarrage 290 € (145 € pour les 10 fondateurs), puis abonnement Sérénité 59 €/mois sans engagement.
5. Différence : un humain du coin qui passe au restaurant, plus des outils IA maison. Les concurrents (Malou, Partoo) vendent un logiciel à utiliser soi-même.
6. Investissement de départ : environ 95 €. Pas de stock, pas de local, pas de salarié.
7. Scénario central à 12 mois : 47 packs vendus, 21 abonnés actifs, 1 212 € de revenu mensuel récurrent (MRR).
8. CA 12 mois : 21 136 €. Résultat net après URSSAF et coûts : 13 548 € (avant impôt sur le revenu).
9. Temps : un sprint de 30 h/semaine le premier mois, puis 6 à 13 h/semaine. Un étudiant freelance (USMB) prend le surplus à partir d'avril 2027.
10. Croissance après 12 mois : autres verticales (hôtels, loueurs, caves) puis autres villes touristiques, en licence légère (voir [expansion.md](expansion.md)).

---

## 2. Proposition de valeur

**Promesse :** « Votre restaurant parle la langue de chaque client. »

| Douleur du restaurateur | Ce que fait Polyglotte | Ce que ça lui apporte |
|---|---|---|
| Des avis en allemand, anglais, italien sans réponse | Brouillon de réponse dans la langue du client, validé par un humain, publié sous 48 h | Image soignée, client étranger qui se sent reconnu |
| Menu papier en français seulement, serveurs qui traduisent à la volée | Menu QR en FR/EN/DE/IT/ES avec les 14 allergènes | Moins d'erreurs de commande, moins de temps perdu en salle |
| Fiche Google incomplète (horaires, photos, catégories) | Fiche optimisée, 4 posts par mois | Plus d'appels et d'itinéraires depuis Google Maps |
| « Je n'ai pas le temps, je n'y connais rien » | Tout est fait à sa place, il valide en 2 minutes par SMS/WhatsApp | Zéro outil à apprendre |
| Peur des agences qui verrouillent tout | Accès « gestionnaire » révocable, jamais le mot de passe, sans engagement | Il garde le contrôle |

**Charte (argument de vente, pas seulement une règle) :** jamais de faux avis, chaque réponse est validable, accès révocable à tout moment. Les faux avis sont une pratique commerciale trompeuse en toutes circonstances (art. L121-4, 28° du code de la consommation, voir [juridique-checklist.md](juridique-checklist.md)).

---

## 3. Cible et taille du marché local

### 3.1 Combien de restaurants ?

Aucune source officielle trouvée ne donne directement le nombre de restaurants du Grand Annecy. Voici ce qui est publié, et ce qu'on en déduit.

| Indicateur | Valeur | Source / statut |
|---|---|---|
| Restaurants référencés à Annecy (commune) sur Tripadvisor | 513 | [Tripadvisor](https://www.tripadvisor.com/Restaurants-g187260-Annecy_Haute_Savoie_Auvergne_Rhone_Alpes.html), affichage oct. 2026 |
| Annuaire local : 87 restaurants « sans spécialité » = 15 % de l'offre de la commune | soit environ 580 établissements | [restaurants-haute-savoie.fr](https://restaurants-haute-savoie.fr/communes/annecy/restaurant/) (calcul : 87 / 0,15) |
| Établissements « commerce, transports, hébergement et restauration » à Annecy fin 2024 | 3 563 (tous secteurs confondus de ce groupe) | [INSEE, dossier commune](https://www.insee.fr/fr/statistiques/2011101?geo=COM-74010) |
| Population Grand Annecy / ville d'Annecy | 213 415 / 134 985 hab. | [INSEE](https://www.insee.fr/fr/statistiques/2011101?geo=EPCI-200066793), [Ville d'Annecy](https://www.annecy.fr/fileadmin/mediatheque_annecy/Espace_presse/Recensement.pdf) |

**Hypothèse retenue :** 500 à 600 restaurants dans la commune d'Annecy, et **700 à 900 dans les 34 communes du Grand Annecy**. La ville concentre 63 % de la population et l'essentiel de l'offre touristique (vieille ville, bords du lac). On ajoute donc 40 à 50 % pour le reste de l'agglomération. C'est une fourchette, pas une mesure.

**Comment vérifier (2 heures) :**
1. Télécharger la base Sirene des établissements sur [data.gouv.fr](https://www.data.gouv.fr/fr/datasets/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/) ou interroger [annuaire-entreprises.data.gouv.fr](https://annuaire-entreprises.data.gouv.fr).
2. Filtrer : établissements **actifs**, codes NAF 56.10A (restauration traditionnelle), 56.10C (restauration rapide), 56.30Z (débits de boissons), communes du Grand Annecy (EPCI 200066793).
3. Retirer les sièges sans activité réelle (holdings, sociétés dormantes). Croiser avec Google Maps.
4. Les codes NAF ci-dessus sont ceux de la nomenclature en vigueur à notre connaissance : à confirmer sur [insee.fr](https://www.insee.fr).

### 3.2 Segmentation et marché adressable (hypothèses)

| Segment | Part estimée | Nombre (milieu de fourchette 800) | Priorité |
|---|---|---|---|
| Indépendants en zone touristique (vieille ville, lac, Veyrier, Talloires, Sévrier) avec ≥ 100 avis Google | 30 % | ~240 | **1 — cœur de cible** |
| Indépendants hors zone touristique, ≥ 50 avis | 25 % | ~200 | 2 |
| Chaînes, franchises, restauration rapide de marque | 25 % | ~200 | exclus (décision au siège) |
| Très petits / sans fiche Google active | 20 % | ~160 | 3 (Pack seul) |

- **Marché adressable (segments 1 + 2) :** environ 440 restaurants (hypothèse).
- **Objectif 12 mois (central) :** 47 packs, soit ~11 % du marché adressable. 21 abonnés actifs, soit ~5 %.
- **Valeur théorique du marché adressable :** 440 × 59 € × 12 = ~311 000 €/an si tous s'abonnaient. Ça montre le plafond local, pas une prévision.
- Juste à côté, hors Grand Annecy : la rive sud (Saint-Jorioz, Duingt, Doussard, Faverges) dépend d'un autre office de tourisme, [Sources du Lac d'Annecy](https://www.sources-lac-annecy.com/en/espace-pro/devenir-partenaire/) (204 partenaires en 2026). C'est la première extension naturelle.

---

## 4. Concurrence

| Acteur | Ce qu'il vend | Prix | Notre angle |
|---|---|---|---|
| [Malou](https://www.journaldunet.com/retail/1526345-le-francais-malou-leve-7-millions-d-euros-pour-ameliorer-la-visibilite-des-restaurants-newyorkais/) (2 000+ restaurants, 7 M€ levés) | Logiciel de gestion avis / réseaux | non publié ici | Lui, c'est un logiciel. Nous, on fait le travail. |
| [Partoo](https://www.g2.com/products/partoo/) | Logiciel de présence locale multi-sites | non publié ici | Pensé pour les chaînes, pas pour le resto seul |
| [Zerosix](https://www.lafabriquedunet.fr/logiciel/zerosix) | Fidélisation / marketing resto | 49 €/mois + 190 € de mise en service | Même prix, mais nous incluons le service humain |
| Zenchef | Réservation + marketing | 129 à 249 €/mois (source : [recherche.md](recherche.md)) | 2 à 4 fois plus cher, autre besoin |
| Agences web locales, freelances à distance | Sites, réseaux sociaux | variable | Pas spécialisés avis + menus multilingues ; aucun trouvé à Annecy |
| Le neveu / l'associé / ChatGPT | Gratuit | 0 € | Irrégulier, pas d'allergènes, pas de suivi. Voir les objections dans [scripts-terrain.md](scripts-terrain.md). |
| Menus QR gratuits en ligne | Générateurs de QR / menus | 0 à quelques €/mois | Pas de traduction validée, pas d'allergènes structurés, pas d'avis |

**Conclusion :** le prix de 59 €/mois est aligné sur ce que les restaurateurs paient déjà (Zerosix 49 €). Notre avantage n'est pas technique. Il tient à la **présence physique** et au **« fait pour vous »**.

---

## 5. Modèle économique

### 5.1 Offres

| Offre | Prix | Contenu | Temps de production (hypothèse) |
|---|---|---|---|
| Audit | Gratuit | Audit imprimé remis en main propre (outil `audit/`) | 30 min de préparation |
| Pack Démarrage | 290 € HT (= TTC, franchise de TVA) | Fiche Google optimisée, menu QR 5 langues + 14 allergènes, réponses aux 30 derniers avis, 10 chevalets QR | 4 h |
| Offre fondateurs | 145 € | Idem, pour les 10 premiers clients, contre un témoignage et une photo | 4 h |
| Sérénité | 59 €/mois sans engagement, ou 590 €/an | Réponses à tous les avis sous 48 h, menu à jour, 4 posts Google/mois, rapport mensuel | 1,1 h/client/mois |

### 5.2 Économie unitaire (hypothèses)

| Poste | Pack 290 € | Abonné / mois (59 €) |
|---|---|---|
| URSSAF 21,2 % | 61,48 € | 12,51 € |
| Paiement Stripe (1,5 % + 0,25 €, [recherche.md](recherche.md)) | 4,60 € | 1,14 € |
| Chevalets + impression (hypothèse) | 13,50 € | — |
| API Claude (hypothèse, quelques centimes par client) | ~0,30 € | ~0,30 € |
| **Marge avant temps passé** | **~210 €** | **~45 €** |
| Temps (hypothèse) | 7 h (3 h vente + 4 h production) | 1,1 h |
| **Marge horaire** | ~30 €/h | ~41 €/h |
| Si sous-traité à un étudiant à 18 €/h (hypothèse) | marge ~84 € | marge ~25 € |

- **Durée de vie d'un abonné** avec 4 % de churn mensuel : 1 / 0,04 = 25 mois en moyenne (hypothèse de churn issue du repère 3-5 %/mois de [Koji](https://www.koji.so/blog/saas-churn-rate-benchmarks-2026)).
- **Valeur d'un abonné sur sa durée de vie :** 25 × 59 € = 1 475 € de CA, soit ~1 125 € de marge avant temps.
- **Leçon :** le pack paie l'acquisition. L'abonnement fait le revenu. **L'indicateur n° 1 est le taux de passage pack → abonnement.**

### 5.3 Investissement de départ (< 150 €)

| Poste | Coût | Source / statut |
|---|---|---|
| Nom de domaine .fr | ~9 € | [recherche.md](recherche.md) |
| Impression de 40 audits couleur (4 pages) | ~40 € | hypothèse (~1 €/audit en reprographie) |
| Cartes de visite | ~20 € | hypothèse |
| 1er mois de RC Pro (paiement mensuel) | ~15 € | 100 à 200 €/an selon le [Portail auto-entrepreneur](https://www.portail-autoentrepreneur.fr/academie/creation-auto-entreprise/cout-auto-entrepreneur), 150 à 320 €/an selon [recherche.md](recherche.md) |
| Kit de démo (2 chevalets échantillons) | ~10 € | hypothèse |
| Immatriculation micro-entreprise | 0 € | gratuite sur le guichet unique (voir [juridique-checklist.md](juridique-checklist.md)) |
| Hébergement, formulaires, emailing | 0 € | GitHub/Cloudflare Pages, Tally, Brevo (offres gratuites) |
| **Total** | **~94 €** | |

Les chevalets des clients sont achetés **après** l'encaissement du pack. Le BFR est donc nul.

---

## 6. Projections 12 mois

### 6.1 Hypothèses communes (toutes explicites)

| Hypothèse | Valeur | Justification |
|---|---|---|
| Calendrier | M1 = sprint du 21 oct. au 19 nov. 2026, puis mois calendaires jusqu'à M12 = oct. 2027 | Lancement fixé |
| Prix | Pack 290 € ; 145 € pour les 10 premiers ; abonnement 59 €/mois | Grille de l'offre |
| Démarrage de l'abonnement | le mois qui suit le pack | Le pack doit être livré d'abord |
| Churn | 4 %/mois appliqué aux abonnés en début de mois | Consigne ; repère 3-5 % ([Koji](https://www.koji.so/blog/saas-churn-rate-benchmarks-2026)) |
| Cotisations URSSAF | 21,2 % du CA encaissé | [Le Coin des entrepreneurs](https://www.lecoindesentrepreneurs.fr/taux-cotisations-sociales-2026-micro-entrepreneur/). Hors ACRE (prudence). Hors CFP et éventuelle taxe consulaire, à vérifier sur urssaf.fr |
| Coûts fixes | ~24 €/mois (RC Pro 15 €, domaine 0,75 €, API 5 €, téléphone/divers 3 €) | hypothèses |
| Coûts variables | 13,50 €/pack (chevalets + impressions), Stripe 1,5 % + 0,25 €, impressions d'audits 40 € en M1 puis 8 €/mois | hypothèses |
| Temps par pack | 6,5 h de vente en M1 (froid), puis 3 h (recommandations, partenaires) + 4 h de production | hypothèse à mesurer dès la 1re semaine |
| Temps par abonné | 1,1 h/mois (avis 35 min, posts 15 min, menu + rapport 15 min) | hypothèse, outils `tools/` inclus |
| Temps fixe | 3 h/mois d'admin + 20 h de constitution de la liste et d'audits non convertis en M1 | hypothèse |
| Capacité du fondateur | 8 h/semaine = 34,7 h/mois (hors sprint M1) | consigne |
| Surplus d'heures | confié à un étudiant freelance à 18 €/h, compté dans les coûts | hypothèse |
| Saisonnalité | ventes faibles en déc.-févr. (fêtes, fermetures annuelles), fortes en mars-juin (préparation de la saison), creux en juillet-août (restaurateurs saturés) | hypothèse de bon sens, à confirmer sur le terrain |
| Résultat net | CA − URSSAF − coûts. **Avant impôt sur le revenu** | — |

Les abonnés actifs sont des valeurs moyennes attendues (d'où les décimales).

### 6.2 Scénario CENTRAL — 60 % des packs passent en abonnement

| Mois | Nouveaux packs | dont fondateurs | Abonnés actifs (fin) | Résiliations | CA packs | CA abonnements | CA total | URSSAF 21,2 % | Coûts | Résultat net | Heures/sem. | dont étudiant (h/mois) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| M1 nov. 26 | 10 | 10 | 0,0 | 0,0 | 1 450 € | 0 € | 1 450 € | 307 € | 223 € | 920 € | 29,5 | 0 |
| M2 déc. 26 | 4 | 0 | 6,0 | 0,0 | 1 160 € | 354 € | 1 514 € | 321 € | 164 € | 1 029 € | 8,7 | 3 |
| M3 janv. 27 | 2 | 0 | 8,2 | 0,2 | 580 € | 481 € | 1 061 € | 225 € | 77 € | 759 € | 6,0 | 0 |
| M4 févr. 27 | 2 | 0 | 9,0 | 0,3 | 580 € | 533 € | 1 113 € | 236 € | 78 € | 799 € | 6,2 | 0 |
| M5 mars 27 | 3 | 0 | 9,9 | 0,4 | 870 € | 582 € | 1 452 € | 308 € | 101 € | 1 044 € | 8,0 | 0 |
| M6 avr. 27 | 4 | 0 | 11,3 | 0,4 | 1 160 € | 665 € | 1 825 € | 387 € | 274 € | 1 164 € | 10,0 | 9 |
| M7 mai 27 | 5 | 0 | 13,2 | 0,5 | 1 450 € | 780 € | 2 230 € | 473 € | 459 € | 1 298 € | 12,1 | 18 |
| M8 juin 27 | 5 | 0 | 15,7 | 0,5 | 1 450 € | 926 € | 2 376 € | 504 € | 511 € | 1 362 € | 12,8 | 21 |
| M9 juil. 27 | 4 | 0 | 18,1 | 0,6 | 1 160 € | 1 066 € | 2 226 € | 472 € | 416 € | 1 338 € | 11,7 | 16 |
| M10 août 27 | 2 | 0 | 19,7 | 0,7 | 580 € | 1 165 € | 1 745 € | 370 € | 163 € | 1 212 € | 8,9 | 4 |
| M11 sept. 27 | 2 | 0 | 20,2 | 0,8 | 580 € | 1 189 € | 1 769 € | 375 € | 172 € | 1 222 € | 9,0 | 5 |
| M12 oct. 27 | 4 | 0 | 20,6 | 0,8 | 1 160 € | 1 212 € | 2 372 € | 503 € | 468 € | 1 401 € | 12,4 | 19 |
| **Total 12 mois** | **47** | 10 | **~21** | 5,2 | 12 180 € | 8 956 € | **21 136 €** | 4 481 € | 3 107 € | **13 548 €** | moy. 11,3 | 94 h |

- **MRR fin M12 :** 1 212 €, soit ~14 550 € de revenu récurrent annualisé.
- **Heures totales :** ~587 h, dont ~94 h confiées à un étudiant. Le fondateur gagne environ 27 € nets de l'heure (13 548 € / ~493 h).

### 6.3 Scénario PRUDENT — 40 % de passage en abonnement, ventes lentes

| Mois | Nouveaux packs | dont fondateurs | Abonnés actifs (fin) | Résiliations | CA packs | CA abonnements | CA total | URSSAF 21,2 % | Coûts | Résultat net | Heures/sem. | dont étudiant (h/mois) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| M1 nov. 26 | 6 | 6 | 0,0 | 0,0 | 870 € | 0 € | 870 € | 184 € | 159 € | 526 € | 19,8 | 0 |
| M2 déc. 26 | 4 | 4 | 2,4 | 0,0 | 580 € | 142 € | 722 € | 153 € | 98 € | 470 € | 7,8 | 0 |
| M3 janv. 27 | 2 | 0 | 3,9 | 0,1 | 580 € | 230 € | 810 € | 172 € | 72 € | 566 € | 4,9 | 0 |
| M4 févr. 27 | 2 | 0 | 4,5 | 0,2 | 580 € | 268 € | 848 € | 180 € | 73 € | 595 € | 5,1 | 0 |
| M5 mars 27 | 3 | 0 | 5,2 | 0,2 | 870 € | 305 € | 1 175 € | 249 € | 92 € | 834 € | 6,8 | 0 |
| M6 avr. 27 | 3 | 0 | 6,2 | 0,2 | 870 € | 363 € | 1 233 € | 261 € | 93 € | 879 € | 7,1 | 0 |
| M7 mai 27 | 4 | 0 | 7,1 | 0,2 | 1 160 € | 420 € | 1 580 € | 335 € | 187 € | 1 058 € | 9,0 | 4 |
| M8 juin 27 | 4 | 0 | 8,4 | 0,3 | 1 160 € | 497 € | 1 657 € | 351 € | 215 € | 1 091 € | 9,3 | 6 |
| M9 juil. 27 | 2 | 0 | 9,7 | 0,3 | 580 € | 572 € | 1 152 € | 244 € | 79 € | 829 € | 6,4 | 0 |
| M10 août 27 | 1 | 0 | 10,1 | 0,4 | 290 € | 596 € | 886 € | 188 € | 61 € | 637 € | 4,9 | 0 |
| M11 sept. 27 | 2 | 0 | 10,1 | 0,4 | 580 € | 596 € | 1 176 € | 249 € | 79 € | 847 € | 6,5 | 0 |
| M12 oct. 27 | 3 | 0 | 10,5 | 0,4 | 870 € | 619 € | 1 489 € | 316 € | 114 € | 1 060 € | 8,2 | 1 |
| **Total 12 mois** | **36** | 10 | **~10** | 2,7 | | | **13 598 €** | 2 883 € | 1 323 € | **9 392 €** | moy. 8,0 | 11 h |

MRR fin M12 : 619 €. Le projet reste rentable, mais il reste un revenu d'appoint.

### 6.4 Scénario AMBITIEUX — 75 % de passage, recommandations fortes

| Mois | Nouveaux packs | dont fondateurs | Abonnés actifs (fin) | Résiliations | CA packs | CA abonnements | CA total | URSSAF 21,2 % | Coûts | Résultat net | Heures/sem. | dont étudiant (h/mois) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| M1 nov. 26 | 12 | 10 | 0,0 | 0,0 | 2 030 € | 0 € | 2 030 € | 430 € | 259 € | 1 340 € | 34,4 | 0 |
| M2 déc. 26 | 6 | 0 | 9,0 | 0,0 | 1 740 € | 531 € | 2 271 € | 481 € | 515 € | 1 275 € | 12,7 | 20 |
| M3 janv. 27 | 4 | 0 | 13,1 | 0,4 | 1 160 € | 775 € | 1 935 € | 410 € | 313 € | 1 212 € | 10,5 | 11 |
| M4 févr. 27 | 4 | 0 | 15,6 | 0,5 | 1 160 € | 921 € | 2 081 € | 441 € | 365 € | 1 275 € | 11,1 | 14 |
| M5 mars 27 | 6 | 0 | 18,0 | 0,6 | 1 740 € | 1 061 € | 2 801 € | 594 € | 703 € | 1 505 € | 15,0 | 30 |
| M6 avr. 27 | 7 | 0 | 21,8 | 0,7 | 2 030 € | 1 284 € | 3 314 € | 703 € | 926 € | 1 686 € | 17,5 | 41 |
| M7 mai 27 | 8 | 0 | 26,1 | 0,9 | 2 320 € | 1 543 € | 3 863 € | 819 € | 1 162 € | 1 882 € | 20,3 | 53 |
| M8 juin 27 | 8 | 0 | 31,1 | 1,0 | 2 320 € | 1 835 € | 4 155 € | 881 € | 1 266 € | 2 009 € | 21,5 | 59 |
| M9 juil. 27 | 6 | 0 | 35,9 | 1,2 | 1 740 € | 2 116 € | 3 856 € | 817 € | 1 077 € | 1 961 € | 19,5 | 50 |
| M10 août 27 | 3 | 0 | 38,9 | 1,4 | 870 € | 2 297 € | 3 167 € | 671 € | 709 € | 1 786 € | 15,4 | 32 |
| M11 sept. 27 | 4 | 0 | 39,6 | 1,6 | 1 160 € | 2 337 € | 3 497 € | 741 € | 868 € | 1 888 € | 17,2 | 40 |
| M12 oct. 27 | 7 | 0 | 41,0 | 1,6 | 2 030 € | 2 421 € | 4 451 € | 944 € | 1 329 € | 2 178 € | 22,4 | 62 |
| **Total 12 mois** | **75** | 10 | **~41** | 10,0 | | | **37 422 €** | 7 933 € | 9 492 € | **19 996 €** | moy. 18,1 | 412 h |

MRR fin M12 : 2 421 €. Il faut 1 à 2 étudiants dès décembre 2026. **Attention à la TVA en 2027** (voir § 8).

### 6.5 Synthèse des trois scénarios

| Indicateur à M12 | Prudent | Central | Ambitieux |
|---|---|---|---|
| Packs vendus (cumul) | 36 | **47** | 75 |
| Abonnés actifs | ~10 | **~21** | ~41 |
| MRR | 619 € | **1 212 €** | 2 421 € |
| CA 12 mois | 13 598 € | **21 136 €** | 37 422 € |
| Résultat net 12 mois (avant IR) | 9 392 € | **13 548 €** | 19 996 € |
| Heures/semaine en moyenne | 8,0 | **11,3** | 18,1 |
| Recours à un étudiant | marginal | **à partir d'avril 2027** | dès décembre 2026 |

**Sensibilités (central) :**
- Chaque point de churn en plus (5 % au lieu de 4 %) coûte environ 1 abonné à M12.
- Chaque 10 points de passage pack → abonnement en plus apportent environ 3,4 abonnés à M12.
- Passer le prix à 69 €/mois, sans perte de clients, ajouterait ~210 €/mois de MRR à M12.

---

## 7. Capacité et recrutement

### 7.1 Ce que tient une personne à 8 h/semaine (34,7 h/mois)

Calcul : 3 h d'admin + 7 h par nouveau pack + 1,1 h par abonné (hypothèses du § 6.1).

| Nouveaux packs / mois | Abonnés maximum tenables |
|---|---|
| 0 | 28 |
| 1 | 22 |
| 2 | 16 |
| 3 | 9 |
| 4 | 3 |

**Lecture :** à 8 h/semaine, on ne peut pas à la fois vendre 3 packs par mois et servir plus de 10 abonnés. Au-delà, il faut déléguer la production.

**Le sprint M1 est l'exception.** Signer 10 clients en 30 jours demande 25 à 30 h/semaine pendant 4 semaines. Il faut soit poser des congés, soit être deux à 12-15 h/semaine chacun.

### 7.2 Quand recruter un étudiant freelance (USMB)

**Déclencheur :** 2 mois de suite au-dessus de 9 h/semaine, **ou** plus de 15 abonnés actifs avec au moins 2 packs vendus par mois. En scénario central, c'est **mars 2027** : on recrute en mars pour qu'il soit opérationnel en avril, avant la saison.

| Point | Recommandation |
|---|---|
| Profil | Étudiant(e) LEA, langues, IAE ou IUT d'Annecy, bilingue allemand ou italien de préférence |
| Statut | Freelance en micro-entreprise, payé à la tâche (ex. 20 € par abonné et par mois, ou 18 €/h, hypothèse). **Pas de lien de subordination** : il organise son temps lui-même, sinon risque de requalification en salariat |
| Tâches confiées | Brouillons de réponses aux avis (avec `tools/reponses_avis.py`), traduction et contrôle des menus, posts Google |
| Tâches gardées | Vente, relation client, validation finale des contenus sensibles (allergènes, avis négatifs) |
| Alternative | Stage conventionné (gratification de 4,50 €/h effective pour 2 mois ou plus, selon le [calendrier des stages USMB 2026-2027](https://www.club-entreprises.univ-smb.fr/content/uploads/Calendrier-des-stages-et-missions-Club-USMB.pdf), à vérifier), ou projet tutoré **PITON** (équipe de 2 à 4 étudiants, contact piton@univ-smb.fr) |
| Où publier | [Club des entreprises USMB](https://www.club-entreprises.univ-smb.fr) ; IAE : club-des-entreprises.iae@univ-smb.fr |
| Contrat | Contrat de sous-traitance avec clause de confidentialité et clauses RGPD art. 28 (il accède à des données de clients) |

---

## 8. Seuils à surveiller

Les seuils s'apprécient par **année civile**, pas sur 12 mois glissants.

| Seuil | Montant 2026 | Source | Situation (central) |
|---|---|---|---|
| Plafond micro-entreprise (services BIC) | 83 600 € | [tpeactu](https://tpeactu.fr/2026/02/25/micro-entrepreneurs-plafonds-chiffre-affaires-2026/) | 2026 : ~3 000 €. 2027 : ~23 000 € attendus. Large marge |
| Franchise de TVA (services) | 37 500 € (seuil majoré 41 250 €) | [Indy](https://www.indy.fr/guide/fiscalite/taxes/tva/abaissement-seuil-2026/), [Comptabook](https://comptabook.fr/tva/seuil-franchise-tva-2026/) | Central : OK. **Ambitieux : ~33 000 € de janvier à octobre 2027, puis ~9 000 € en nov.-déc. Dépassement du seuil majoré probable en décembre 2027** |
| Compte bancaire dédié obligatoire | CA > 10 000 € deux années civiles consécutives | [justice.fr](https://www.justice.fr/fiche/compte-bancaire-micro-entrepreneur-auto-entrepreneur) | À ouvrir dès le jour 1 de toute façon |

**Points d'attention :**
- Pour l'année de création, le plafond micro est réduit au prorata du temps d'activité (règle connue, à vérifier sur urssaf.fr). Avec ~3 000 € en 2026, on est loin.
- **Si le scénario ambitieux se confirme**, préparer le passage à la TVA dès septembre 2027 :
  - nos clients restaurateurs récupèrent la TVA, donc facturer 290 € HT + TVA ne leur coûte rien de plus ;
  - annoncer les prix « HT » dès le départ dans les CGV pour ne pas avoir à les augmenter.

---

## 9. Risques et parades

| Risque | Probabilité | Impact | Parade |
|---|---|---|---|
| **Google change ses règles** (API, politique avis, fonctions IA natives de réponse) | Moyenne | Fort | Ne pas dépendre d'une API non officielle : on publie en tant que gestionnaire, comme un humain. Vendre le **résultat** (réputation, langues, allergènes), pas l'outil. Le menu QR et le rapport mensuel ne dépendent pas de Google. Veille mensuelle sur la [politique de contenu Google](https://support.google.com/contributionpolicy/answer/7400114?hl=fr) |
| **Les plateformes intègrent l'IA** (Google, TheFork, Zenchef proposent des réponses automatiques) | Forte | Moyen | Notre valeur : la **validation humaine**, le ton local, la cohérence entre la fiche, le menu et les avis, et le fait que le restaurateur n'ouvre aucun outil. Monter en gamme : rapport mensuel avec conseils concrets |
| **Défendabilité faible** (n'importe qui peut copier) | Forte | Moyen | 1) **Relation locale** : visite physique trimestrielle, numéro WhatsApp direct. 2) **Volume de références** : 20+ restaurants vitrines à Annecy, logos sur le site, témoignages. 3) **Extension multi-verticales** (hôtels, loueurs, caves) : un réseau local que le concurrent n'a pas. 4) **Partenariats** (UMIH, office de tourisme) qui créent une barrière relationnelle |
| Erreur de traduction ou d'allergène | Faible | Très fort | Le restaurateur valide le menu par écrit avant publication (CGV). Double contrôle des allergènes. Mention « informations fournies par l'établissement ». RC Pro qui couvre ce cas |
| Mauvaise réponse à un avis | Moyenne | Moyen | Validation par le client pour les avis ≤ 3 étoiles. Charte de ton. Correction sous 24 h |
| Churn saisonnier (fermetures en novembre et janvier) | Forte | Moyen | Proposer une **pause saisonnière** (abonnement suspendu jusqu'à 3 mois) plutôt qu'une résiliation |
| Temps du fondateur (side project) | Forte | Fort | Plafond de capacité (§ 7). Recrutement étudiant anticipé. Process et templates |
| Démarchage : droit de rétractation des petits pros (≤ 5 salariés, art. L221-3 C. conso) | Certaine | Moyen | Formulaire de rétractation remis, pas d'encaissement avant J+8, démarrage sur demande expresse (voir [juridique-checklist.md](juridique-checklist.md)) |
| Marque « Polyglotte » déjà déposée | Moyenne (mot courant) | Moyen | Recherche d'antériorité INPI avant tout imprimé à grande échelle |
| Dépendance au fournisseur d'IA | Faible | Faible | Les scripts `tools/` sont simples et peuvent changer de modèle. Les coûts restent de quelques euros par mois |

---

## 10. Prochaines décisions

1. Immatriculer la micro-entreprise **aujourd'hui** (voir [juridique-checklist.md](juridique-checklist.md)).
2. Lancer le sprint de 30 jours le 21 octobre (voir [go-to-market-30-jours.md](go-to-market-30-jours.md)).
3. À J+30 : comparer le réel au scénario central avec [kpi-tracker.csv](kpi-tracker.csv). Recalculer le temps par pack et par abonné à partir des heures réellement passées.
4. En mars 2027 : décider du recrutement étudiant et de la première nouvelle verticale.
