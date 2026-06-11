-- ============================================================
-- MODELE EN ETOILE DVF
-- Source  : base DVF (schéma relationnel)
-- Cible   : base DVF_ETOILE (modèle en étoile)
-- A exécuter dans SSMS connecté à votre serveur SQL Server
-- ============================================================

-- ============================================================
-- CRÉATION DE LA BASE DVF_ETOILE
-- ============================================================
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'DVF_ETOILE')
    CREATE DATABASE DVF_ETOILE;
GO

USE DVF_ETOILE;
GO

-- ============================================================
-- SUPPRESSION DES TABLES SI ELLES EXISTENT DÉJÀ
-- ============================================================
IF OBJECT_ID('FAIT_TRANSACTION',   'U') IS NOT NULL DROP TABLE FAIT_TRANSACTION;
IF OBJECT_ID('DIM_TEMPS',          'U') IS NOT NULL DROP TABLE DIM_TEMPS;
IF OBJECT_ID('DIM_LOCALISATION',   'U') IS NOT NULL DROP TABLE DIM_LOCALISATION;
IF OBJECT_ID('DIM_BIEN',           'U') IS NOT NULL DROP TABLE DIM_BIEN;
IF OBJECT_ID('DIM_NATURE_CULTURE', 'U') IS NOT NULL DROP TABLE DIM_NATURE_CULTURE;
GO


-- ============================================================
-- 1. DIM_TEMPS
-- Source : DVF.dbo.Mutation.date_mutation
-- ============================================================
CREATE TABLE DIM_TEMPS (
    id_temps      INT  NOT NULL,   -- format YYYYMMDD
    date_mutation DATE,
    annee         INT,
    trimestre     INT,
    mois          INT,
    CONSTRAINT PK_DIM_TEMPS PRIMARY KEY (id_temps)
);

INSERT INTO DVF_ETOILE.dbo.DIM_TEMPS (id_temps, date_mutation, annee, trimestre, mois)
SELECT DISTINCT
    CAST(FORMAT(date_mutation, 'yyyyMMdd') AS INT) AS id_temps,
    date_mutation,
    YEAR(date_mutation)                            AS annee,
    DATEPART(QUARTER, date_mutation)               AS trimestre,
    MONTH(date_mutation)                           AS mois
FROM DVF.dbo.Mutation
WHERE date_mutation IS NOT NULL;
GO


-- ============================================================
-- 2. DIM_LOCALISATION
-- Source : DVF.dbo.Parcelle + Commune + Departement + Voie
-- ============================================================
CREATE TABLE DIM_LOCALISATION (
    id_localisation     INT           NOT NULL IDENTITY(1,1),
    id_parcelle         VARCHAR(50),
    ancien_id_parcelle  VARCHAR(50),
    surface_terrain     DECIMAL(15,2),
    longitude           DECIMAL(15,10),
    latitude            DECIMAL(15,10),
    adresse_numero      VARCHAR(10),
    adresse_suffixe     VARCHAR(10),
    adresse_code_voie   VARCHAR(10),
    adresse_nom_voie    VARCHAR(150),
    code_commune        VARCHAR(10),
    nom_commune         VARCHAR(100),
    code_postal         VARCHAR(10),
    ancien_nom_commune  VARCHAR(100),
    ancien_code_commune VARCHAR(10),
    code_departement    VARCHAR(3),
    CONSTRAINT PK_DIM_LOCALISATION PRIMARY KEY (id_localisation)
);

INSERT INTO DVF_ETOILE.dbo.DIM_LOCALISATION (
    id_parcelle, ancien_id_parcelle, surface_terrain, longitude, latitude,
    adresse_numero, adresse_suffixe, adresse_code_voie, adresse_nom_voie,
    code_commune, nom_commune, code_postal,
    ancien_nom_commune, ancien_code_commune, code_departement
)
SELECT DISTINCT
    p.id_parcelle,
    p.ancien_id_parcelle,
    p.surface_terrain,
    p.longitude,
    p.latitude,
    m.adresse_numero,
    m.adresse_suffixe,
    v.adresse_code_voie,
    v.adresse_nom_voie,
    c.code_commune,
    c.nom_commune,
    c.code_postal,
    c.ancien_nom_commune,
    c.ancien_code_commune,
    d.code_departement
FROM DVF.dbo.Parcelle    p
JOIN DVF.dbo.Commune     c ON c.code_commune      = p.code_commune
JOIN DVF.dbo.Departement d ON d.code_departement  = c.code_departement
LEFT JOIN DVF.dbo.Mutation m ON m.id_parcelle     = p.id_parcelle
LEFT JOIN DVF.dbo.Voie   v  ON v.adresse_code_voie = m.adresse_code_voie;
GO


-- ============================================================
-- 3. DIM_BIEN
-- Source : DVF.dbo.Bien + Ref_Type_Local + Lot_Bien + Lot
-- ============================================================
CREATE TABLE DIM_BIEN (
    id_bien                   INT          NOT NULL IDENTITY(1,1),
    id_bien_src               INT,
    code_type_local           VARCHAR(5),
    type_local                VARCHAR(100),
    surface_reelle_bati       INT,
    nombre_pieces_principales INT,
    nombre_lots               INT,
    numero_volume             INT,
    lot1_numero               VARCHAR(20),
    lot1_surface_carrez       DECIMAL(15,2),
    lot2_numero               VARCHAR(20),
    lot2_surface_carrez       DECIMAL(15,2),
    lot3_numero               VARCHAR(20),
    lot3_surface_carrez       DECIMAL(15,2),
    lot4_numero               VARCHAR(20),
    lot4_surface_carrez       DECIMAL(15,2),
    lot5_numero               VARCHAR(20),
    lot5_surface_carrez       DECIMAL(15,2),
    CONSTRAINT PK_DIM_BIEN PRIMARY KEY (id_bien)
);

WITH lots_ranked AS (
    SELECT
        lb.id_bien,
        l.lot_numero,
        l.surface_carrez,
        l.numero_volume,
        ROW_NUMBER() OVER (PARTITION BY lb.id_bien ORDER BY l.lot_numero) AS rn
    FROM DVF.dbo.Lot_Bien lb
    JOIN DVF.dbo.Lot      l ON l.lot_numero = lb.lot_numero
)
INSERT INTO DVF_ETOILE.dbo.DIM_BIEN (
    id_bien_src, code_type_local, type_local,
    surface_reelle_bati, nombre_pieces_principales,
    nombre_lots, numero_volume,
    lot1_numero, lot1_surface_carrez,
    lot2_numero, lot2_surface_carrez,
    lot3_numero, lot3_surface_carrez,
    lot4_numero, lot4_surface_carrez,
    lot5_numero, lot5_surface_carrez
)
SELECT
    b.id_bien,
    b.code_type_local,
    tl.type_local,
    b.surface_reelle_bati,
    b.nombre_pieces_principales,
    (SELECT COUNT(*) FROM DVF.dbo.Lot_Bien lb2 WHERE lb2.id_bien = b.id_bien),
    MAX(CASE WHEN lr.rn = 1 THEN lr.numero_volume  END),
    MAX(CASE WHEN lr.rn = 1 THEN lr.lot_numero     END),
    MAX(CASE WHEN lr.rn = 1 THEN lr.surface_carrez END),
    MAX(CASE WHEN lr.rn = 2 THEN lr.lot_numero     END),
    MAX(CASE WHEN lr.rn = 2 THEN lr.surface_carrez END),
    MAX(CASE WHEN lr.rn = 3 THEN lr.lot_numero     END),
    MAX(CASE WHEN lr.rn = 3 THEN lr.surface_carrez END),
    MAX(CASE WHEN lr.rn = 4 THEN lr.lot_numero     END),
    MAX(CASE WHEN lr.rn = 4 THEN lr.surface_carrez END),
    MAX(CASE WHEN lr.rn = 5 THEN lr.lot_numero     END),
    MAX(CASE WHEN lr.rn = 5 THEN lr.surface_carrez END)
FROM DVF.dbo.Bien            b
LEFT JOIN DVF.dbo.Ref_Type_Local tl ON tl.code_type_local = b.code_type_local
LEFT JOIN lots_ranked            lr ON lr.id_bien          = b.id_bien
GROUP BY
    b.id_bien, b.code_type_local, tl.type_local,
    b.surface_reelle_bati, b.nombre_pieces_principales;
GO


-- ============================================================
-- 4. DIM_NATURE_CULTURE
-- Source : DVF.dbo.Ref_Nature_Culture
-- ============================================================
CREATE TABLE DIM_NATURE_CULTURE (
    id_nature_culture            INT         NOT NULL IDENTITY(1,1),
    code_nature_culture          VARCHAR(10),
    nature_culture               VARCHAR(100),
    code_nature_culture_speciale VARCHAR(10),
    nature_culture_speciale      VARCHAR(100),
    CONSTRAINT PK_DIM_NATURE_CULTURE PRIMARY KEY (id_nature_culture)
);

INSERT INTO DVF_ETOILE.dbo.DIM_NATURE_CULTURE (
    code_nature_culture, nature_culture,
    code_nature_culture_speciale, nature_culture_speciale
)
SELECT
    code_nature_culture,
    nature_culture,
    code_nature_culture_speciale,
    nature_culture_speciale
FROM DVF.dbo.Ref_Nature_Culture;
GO


-- ============================================================
-- 5. FAIT_TRANSACTION
-- Source : DVF.dbo.Mutation + jointures vers DVF_ETOILE
-- ============================================================
CREATE TABLE FAIT_TRANSACTION (
    id_fait             INT          NOT NULL IDENTITY(1,1),
    id_mutation         VARCHAR(50),
    id_temps            INT,
    id_localisation     INT,
    id_bien             INT,
    id_nature_culture   INT,
    valeur_fonciere     DECIMAL(15,2),
    numero_disposition  INT,
    nature_mutation     VARCHAR(100),
    CONSTRAINT PK_FAIT_TRANSACTION  PRIMARY KEY (id_fait),
    CONSTRAINT FK_FAIT_TEMPS        FOREIGN KEY (id_temps)          REFERENCES DIM_TEMPS(id_temps),
    CONSTRAINT FK_FAIT_LOCALISATION FOREIGN KEY (id_localisation)   REFERENCES DIM_LOCALISATION(id_localisation),
    CONSTRAINT FK_FAIT_BIEN         FOREIGN KEY (id_bien)           REFERENCES DIM_BIEN(id_bien),
    CONSTRAINT FK_FAIT_NC           FOREIGN KEY (id_nature_culture) REFERENCES DIM_NATURE_CULTURE(id_nature_culture)
);

INSERT INTO DVF_ETOILE.dbo.FAIT_TRANSACTION (
    id_mutation, id_temps, id_localisation, id_bien,
    id_nature_culture, valeur_fonciere, numero_disposition, nature_mutation
)
SELECT
    m.id_mutation,
    CAST(FORMAT(m.date_mutation, 'yyyyMMdd') AS INT),
    dl.id_localisation,
    db.id_bien,
    dnc.id_nature_culture,
    m.valeur_fonciere,
    m.numero_disposition,
    m.nature_mutation
FROM DVF.dbo.Mutation m
LEFT JOIN DVF_ETOILE.dbo.DIM_LOCALISATION dl
       ON dl.id_parcelle = m.id_parcelle
LEFT JOIN DVF.dbo.Bien b
       ON b.id_mutation = m.id_mutation
LEFT JOIN DVF_ETOILE.dbo.DIM_BIEN db
       ON db.id_bien_src = b.id_bien
LEFT JOIN DVF.dbo.Parcelle_Nature_Culture pnc
       ON pnc.id_parcelle = m.id_parcelle
LEFT JOIN DVF_ETOILE.dbo.DIM_NATURE_CULTURE dnc
       ON dnc.code_nature_culture = pnc.code_nature_culture;
GO


-- ============================================================
-- VÉRIFICATION RAPIDE
-- ============================================================
SELECT 'DIM_TEMPS'         AS [Table], COUNT(*) AS [Lignes] FROM DVF_ETOILE.dbo.DIM_TEMPS
UNION ALL
SELECT 'DIM_LOCALISATION',              COUNT(*)            FROM DVF_ETOILE.dbo.DIM_LOCALISATION
UNION ALL
SELECT 'DIM_BIEN',                      COUNT(*)            FROM DVF_ETOILE.dbo.DIM_BIEN
UNION ALL
SELECT 'DIM_NATURE_CULTURE',            COUNT(*)            FROM DVF_ETOILE.dbo.DIM_NATURE_CULTURE
UNION ALL
SELECT 'FAIT_TRANSACTION',              COUNT(*)            FROM DVF_ETOILE.dbo.FAIT_TRANSACTION;
GO