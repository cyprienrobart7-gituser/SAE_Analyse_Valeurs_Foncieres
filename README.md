# Analyse des Valeurs Foncières (DVF) — De la donnée brute au tableau de bord

Projet réalisé dans le cadre de la **SAE 6 — BUT 3 Science des Données** (Outil décisionnel, Modélisation statistique et Intelligence Artificielle), IUT de Lille — Site de Roubaix (Université de Lille).

**Auteurs :** Maxime De Burggraeve, Cyprien Robart

**Date :** 12 juin 2026

## Description du projet

Ce projet propose une architecture complète de Business Intelligence construite autour du jeu de données **DVF (Demandes de Valeurs Foncières)**, publié par Etalab. L'objectif est de transformer un fichier plat, dénormalisé et volumineux, en un tableau de bord interactif exploitable par un utilisateur non technique.

La chaîne de traitement suit quatre grandes étapes :

1. **Rétroconception** du fichier source DVF et élaboration d'un Modèle Conceptuel des Données (MCD) normalisé en 3FN.
2. **Conception du modèle décisionnel** : passage du modèle relationnel à un schéma en étoile (table de faits `FAIT_TRANSACTION` + 4 dimensions).
3. **Pipeline ETL en deux temps** : nettoyage et typage des données avec Python (Pandas), puis transformation multidimensionnelle avec T-SQL (SQL Server).
4. **Visualisation** des données via un tableau de bord Power BI à 5 pages.

## Structure du dépôt

```
.
├── Rapport_Analyse_Valeurs_Foncieres.pdf   # Rapport complet du projet (méthodologie, MCD, MLD, ETL, analyses)
├── source_dvf_vers_relationnel.py          # Script Python : extraction, nettoyage et chargement dans la base relationnelle DVF
├── relationnel_vers_etoile.sql             # Script T-SQL : transformation du modèle relationnel vers le schéma en étoile DVF_ETOILE
└── screens_pbi/                            # Captures d'écran du tableau de bord Power BI
    ├── screens_power_bi_GLOBAL.png
    ├── screens_power_bi_Mutations_avec_légende.png
    ├── screens_power_bi_Mutations_sans_légende.png
    ├── screens_power_bi_Valeur_fonciere.png
    └── screens_power_bi_Valeur_fonciere_par_surface_batie.png
```

## Architecture du pipeline

```
CSV (DVF brut)
   │  Script Python (Pandas)
   │  - typage strict (codes postaux/communes en str)
   │  - nettoyage des valeurs manquantes
   │  - dédoublonnement des référentiels
   ▼
Base relationnelle DVF (3FN)
   │  Script T-SQL (relationnel_vers_etoile.sql)
   │  - génération de la dimension Temps
   │  - aplatissement des dimensions (Localisation, Bien)
   │  - alimentation de la table de faits
   ▼
Base décisionnelle DVF_ETOILE (schéma en étoile)
   │
   ▼
Tableau de bord Power BI
```

### Modèle en étoile

- **FAIT_TRANSACTION** : valeur foncière, nature de la mutation, numéro de disposition.
- **DIM_TEMPS** : date, année, trimestre, mois.
- **DIM_LOCALISATION** : adresse, parcelle, commune, département, coordonnées GPS.
- **DIM_BIEN** : type de local, surfaces, pièces, lots de copropriété (jusqu'à 5 lots aplatis par ligne).
- **DIM_NATURE_CULTURE** : usage des sols (agricole, bois, etc.).

## Utilisation

### 1. Base relationnelle

Exécuter `source_dvf_vers_relationnel.py` pour extraire, nettoyer et charger le fichier DVF brut dans une base SQL Server intermédiaire (`DVF`). Nécessite Python avec Pandas et un pilote ODBC vers SQL Server.

### 2. Modèle en étoile

Exécuter `relationnel_vers_etoile.sql` dans SQL Server Management Studio (SSMS), connecté à la base `DVF`. Le script crée et alimente automatiquement la base `DVF_ETOILE`.

### 3. Tableau de bord Power BI

Connecter Power BI à la base `DVF_ETOILE` pour reproduire le tableau de bord. Les captures d'écran du dossier `screens_pbi/` donnent un aperçu des 4 pages analytiques (Power BI trop lourd pour être déposé dans GitHub) :

- **Global** : KPIs généraux, évolution mensuelle des prix, top départements/communes par valeur foncière.
- **Mutations** : volumétrie des transactions, saisonnalité, top départements/communes par activité.
- **Valeur foncière** : carte géographique des valeurs, répartition par type de bien.
- **Valeur foncière par Surface Bâtie** : relation entre surface et valeur foncière.

## Données

Le tableau de bord couvre l'ensemble du territoire national (hors Alsace-Moselle et Mayotte, absents du fichier DVF) jusqu'au 30/06/2025, soit environ **7,34 millions de mutations** et **11,68 millions de biens**, pour une valeur foncière moyenne de **338 430 €**.

## Documentation

Pour le détail de la méthodologie (analyse du MCD, règles de passage au MLD, choix techniques de l'ETL, analyse des résultats), se référer au rapport complet : [`Rapport_Analyse_Valeurs_Foncieres.pdf`](https://github.com/cyprienrobart7-gituser/SAE_Analyse_Valeurs_Foncieres/blob/master/Rapport%20Analyse%20Valeurs%20Foncieres.pdf).

## Sources

- Jeu de données DVF : [Etalab — data.gouv.fr](https://www.data.gouv.fr/)
