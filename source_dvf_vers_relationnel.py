"""
=============================================================
 IMPORT DVF COMPLET
 - Lit le fichier CSV brut DVF
 - Crée la base de données SQL Server si elle n'existe pas
 - Crée toutes les tables du schéma relationnel
 - Alimente les tables dans le bon ordre (respect des FK)
=============================================================

PRÉREQUIS
---------
pip install pandas pyodbc openpyxl

Pilote ODBC à installer (gratuit Microsoft) :
https://learn.microsoft.com/fr-fr/sql/connect/odbc/download-odbc-driver-for-sql-server
→ choisir "ODBC Driver 17 for SQL Server"

CONFIGURATION
-------------
Modifier les 3 variables ci-dessous avant de lancer le script.
"""

import pandas as pd
import pyodbc

# ── À MODIFIER ────────────────────────────────────────────────
FILE_PATH = r"C:\305779\SAE Le Veler\dvf.csv"           # chemin vers ton fichier DVF
                                # accepte aussi .xlsx si besoin
SERVER    = "localhost"         # ex: "DESKTOP-XXXX\\SQLEXPRESS"
DATABASE  = "DVF"               # nom de la base à créer
# ─────────────────────────────────────────────────────────────

DRIVER = "ODBC Driver 17 for SQL Server"


# =============================================================
# CONNEXION
# =============================================================

def connect(database: str = "master") -> pyodbc.Connection:
    return pyodbc.connect(
        f"DRIVER={{{DRIVER}}};"
        f"SERVER={SERVER};"
        f"DATABASE={database};"
        "Trusted_Connection=yes;",
        autocommit=True,
    )


# =============================================================
# ÉTAPE 1 — CRÉER LA BASE SI ELLE N'EXISTE PAS
# =============================================================

def create_database():
    print(f"[1/4] Vérification / création de la base '{DATABASE}'...")
    conn   = connect("master")
    cursor = conn.cursor()
    cursor.execute(f"IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = '{DATABASE}') "
                   f"CREATE DATABASE [{DATABASE}]")
    conn.close()
    print(f"      Base '{DATABASE}' prête.")


# =============================================================
# ÉTAPE 2 — CRÉER LES TABLES
# =============================================================

DDL = """
IF OBJECT_ID('Lot_Bien',              'U') IS NOT NULL DROP TABLE Lot_Bien;
IF OBJECT_ID('Bien',                  'U') IS NOT NULL DROP TABLE Bien;
IF OBJECT_ID('Mutation',              'U') IS NOT NULL DROP TABLE Mutation;
IF OBJECT_ID('Parcelle_Nature_Culture','U') IS NOT NULL DROP TABLE Parcelle_Nature_Culture;
IF OBJECT_ID('Ref_Nature_Culture',    'U') IS NOT NULL DROP TABLE Ref_Nature_Culture;
IF OBJECT_ID('Lot',                   'U') IS NOT NULL DROP TABLE Lot;
IF OBJECT_ID('Ref_Type_Local',        'U') IS NOT NULL DROP TABLE Ref_Type_Local;
IF OBJECT_ID('Parcelle',              'U') IS NOT NULL DROP TABLE Parcelle;
IF OBJECT_ID('Voie',                  'U') IS NOT NULL DROP TABLE Voie;
IF OBJECT_ID('Commune',               'U') IS NOT NULL DROP TABLE Commune;
IF OBJECT_ID('Departement',           'U') IS NOT NULL DROP TABLE Departement;

CREATE TABLE Departement (
    code_departement VARCHAR(3) NOT NULL,
    CONSTRAINT PK_Departement PRIMARY KEY (code_departement)
);

CREATE TABLE Commune (
    code_commune        VARCHAR(10)  NOT NULL,
    nom_commune         VARCHAR(100),
    code_postal         VARCHAR(10),
    ancien_code_commune VARCHAR(10),
    ancien_nom_commune  VARCHAR(100),
    code_departement    VARCHAR(3)   NOT NULL,
    CONSTRAINT PK_Commune      PRIMARY KEY (code_commune),
    CONSTRAINT FK_Commune_Dept FOREIGN KEY (code_departement)
        REFERENCES Departement(code_departement)
);

CREATE TABLE Voie (
    adresse_code_voie VARCHAR(10)  NOT NULL,
    adresse_nom_voie  VARCHAR(150),
    code_commune      VARCHAR(10)  NOT NULL,
    CONSTRAINT PK_Voie        PRIMARY KEY (adresse_code_voie),
    CONSTRAINT FK_Voie_Commune FOREIGN KEY (code_commune)
        REFERENCES Commune(code_commune)
);

CREATE TABLE Parcelle (
    id_parcelle        VARCHAR(50)  NOT NULL,
    ancien_id_parcelle VARCHAR(50),
    surface_terrain    DECIMAL(15,2),
    longitude          DECIMAL(15,10),
    latitude           DECIMAL(15,10),
    code_commune       VARCHAR(10)  NOT NULL,
    CONSTRAINT PK_Parcelle        PRIMARY KEY (id_parcelle),
    CONSTRAINT FK_Parcelle_Commune FOREIGN KEY (code_commune)
        REFERENCES Commune(code_commune)
);

CREATE TABLE Ref_Nature_Culture (
    code_nature_culture          VARCHAR(10)  NOT NULL,
    nature_culture               VARCHAR(100),
    code_nature_culture_speciale VARCHAR(10),
    nature_culture_speciale      VARCHAR(100),
    CONSTRAINT PK_Ref_NC PRIMARY KEY (code_nature_culture)
);

CREATE TABLE Parcelle_Nature_Culture (
    id_parcelle          VARCHAR(50) NOT NULL,
    code_nature_culture  VARCHAR(10) NOT NULL,
    surface_nature_culture DECIMAL(15,2),
    CONSTRAINT PK_Parcelle_NC  PRIMARY KEY (id_parcelle, code_nature_culture),
    CONSTRAINT FK_PNC_Parcelle FOREIGN KEY (id_parcelle)
        REFERENCES Parcelle(id_parcelle),
    CONSTRAINT FK_PNC_NC       FOREIGN KEY (code_nature_culture)
        REFERENCES Ref_Nature_Culture(code_nature_culture)
);

CREATE TABLE Ref_Type_Local (
    code_type_local VARCHAR(5)   NOT NULL,
    type_local      VARCHAR(100),
    CONSTRAINT PK_Ref_Type_Local PRIMARY KEY (code_type_local)
);

CREATE TABLE Lot (
    lot_numero    VARCHAR(20)  NOT NULL,
    numero_volume INT,
    surface_carrez DECIMAL(15,2),
    CONSTRAINT PK_Lot PRIMARY KEY (lot_numero)
);

CREATE TABLE Mutation (
    id_mutation        VARCHAR(50)  NOT NULL,
    date_mutation      DATE,
    numero_disposition INT,
    nature_mutation    VARCHAR(100),
    valeur_fonciere    DECIMAL(15,2),
    id_parcelle        VARCHAR(50)  NOT NULL,
    adresse_numero     VARCHAR(10),
    adresse_suffixe    VARCHAR(10),
    adresse_code_voie  VARCHAR(10),
    CONSTRAINT PK_Mutation         PRIMARY KEY (id_mutation),
    CONSTRAINT FK_Mutation_Parcelle FOREIGN KEY (id_parcelle)
        REFERENCES Parcelle(id_parcelle),
    CONSTRAINT FK_Mutation_Voie    FOREIGN KEY (adresse_code_voie)
        REFERENCES Voie(adresse_code_voie)
);

CREATE TABLE Bien (
    id_bien                   INT          NOT NULL,
    code_type_local           VARCHAR(5),
    surface_reelle_bati       INT,
    nombre_pieces_principales INT,
    id_mutation               VARCHAR(50)  NOT NULL,
    CONSTRAINT PK_Bien         PRIMARY KEY (id_bien),
    CONSTRAINT FK_Bien_Mutation FOREIGN KEY (id_mutation)
        REFERENCES Mutation(id_mutation),
    CONSTRAINT FK_Bien_TypeLocal FOREIGN KEY (code_type_local)
        REFERENCES Ref_Type_Local(code_type_local)
);

CREATE TABLE Lot_Bien (
    id_bien    INT         NOT NULL,
    lot_numero VARCHAR(20) NOT NULL,
    CONSTRAINT PK_Lot_Bien    PRIMARY KEY (id_bien, lot_numero),
    CONSTRAINT FK_LB_Bien     FOREIGN KEY (id_bien)
        REFERENCES Bien(id_bien),
    CONSTRAINT FK_LB_Lot      FOREIGN KEY (lot_numero)
        REFERENCES Lot(lot_numero)
);
"""


def create_tables():
    print("[2/4] Création des tables...")
    conn   = connect(DATABASE)
    cursor = conn.cursor()
    # exécute chaque instruction séparément
    for stmt in DDL.split(";"):
        stmt = stmt.strip()
        if stmt:
            cursor.execute(stmt)
    conn.commit()
    conn.close()
    print("      Tables créées.")


# =============================================================
# ÉTAPE 3 — LIRE LE FICHIER BRUT
# =============================================================

def load_file(path: str) -> pd.DataFrame:
    print(f"[3/4] Lecture du fichier '{path}'...")
    if path.endswith(".xlsx") or path.endswith(".xls"):
        df = pd.read_excel(path, dtype=str)
    else:
        df = pd.read_csv(path, sep=",", dtype=str, keep_default_na=False)
    df = df.where(df != "", other=None)   # chaînes vides → NULL
    print(f"      {len(df)} lignes, {len(df.columns)} colonnes.")
    return df


# =============================================================
# ÉTAPE 4 — ALIMENTATION DES TABLES
# =============================================================

def insert_many(cursor, table: str, cols: list, rows: list):
    if not rows:
        return 0
    ph  = ", ".join(["?"] * len(cols))
    sql = f"INSERT INTO {table} ({chr(44).join(cols)}) VALUES ({ph})"
    inserted = 0
    skipped  = 0
    for row in rows:
        try:
            cursor.execute(sql, row)
            inserted += 1
        except Exception:
            skipped += 1
    if skipped > 0:
        print(f"    ⚠ {table} : {skipped} ligne(s) ignorée(s) (valeur invalide)")
    return inserted


def to_float(val):
    """Convertit en float Python ou retourne None (NULL SQL) si invalide."""
    if val is None:
        return None
    s = str(val).strip().replace(",", ".").replace("\xa0", "").replace(" ", "")
    if s in ("", "nan", "NaN", "NULL", "None", "-"):
        return None
    try:
        result = float(s)
        if result != result or result == float("inf") or result == float("-inf"):
            return None
        return result
    except (ValueError, TypeError):
        return None


def to_int(val):
    """Convertit en int Python ou retourne None (NULL SQL) si invalide."""
    if val is None:
        return None
    s = str(val).strip().replace("\xa0", "").replace(" ", "")
    if s in ("", "nan", "NaN", "NULL", "None", "-"):
        return None
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return None


def clean_str(val, max_len=None):
    """Nettoie une chaine, retourne None si vide ou invalide."""
    if val is None:
        return None
    s = str(val).strip()
    if s in ("", "nan", "NaN", "NULL", "None"):
        return None
    return s[:max_len] if max_len else s


def feed_all(df: pd.DataFrame):
    print("[4/4] Alimentation des tables...")
    conn   = connect(DATABASE)
    cursor = conn.cursor()

    # 1. DEPARTEMENT
    codes = df["code_departement"].dropna().unique()
    rows  = [(clean_str(c, 3),) for c in codes if clean_str(c)]
    n = insert_many(cursor, "Departement", ["code_departement"], rows)
    print(f"  ✓ Departement             : {n} lignes")

    # 2. COMMUNE
    sub = df[["code_commune","nom_commune","code_postal",
              "ancien_code_commune","ancien_nom_commune","code_departement"]] \
            .drop_duplicates("code_commune").dropna(subset=["code_commune"])
    rows = [
        (clean_str(r.code_commune, 10),
         clean_str(r.nom_commune, 100),
         clean_str(r.code_postal, 10),
         clean_str(r.ancien_code_commune, 10),
         clean_str(r.ancien_nom_commune, 100),
         clean_str(r.code_departement, 3))
        for r in sub.itertuples(index=False)
    ]
    n = insert_many(cursor, "Commune",
                    ["code_commune","nom_commune","code_postal",
                     "ancien_code_commune","ancien_nom_commune","code_departement"], rows)
    print(f"  ✓ Commune                 : {n} lignes")

    # 3. VOIE
    sub = df[["adresse_code_voie","adresse_nom_voie","code_commune"]] \
            .drop_duplicates("adresse_code_voie").dropna(subset=["adresse_code_voie"])
    rows = [
        (clean_str(r.adresse_code_voie, 10),
         clean_str(r.adresse_nom_voie, 150),
         clean_str(r.code_commune, 10))
        for r in sub.itertuples(index=False)
    ]
    n = insert_many(cursor, "Voie",
                    ["adresse_code_voie","adresse_nom_voie","code_commune"], rows)
    print(f"  ✓ Voie                    : {n} lignes")

    # 4. PARCELLE
    sub = df[["id_parcelle","ancien_id_parcelle","surface_terrain",
              "longitude","latitude","code_commune"]] \
            .drop_duplicates("id_parcelle").dropna(subset=["id_parcelle"])
    rows = [
        (clean_str(r.id_parcelle, 50),
         clean_str(r.ancien_id_parcelle, 50),
         to_float(r.surface_terrain),
         to_float(r.longitude),
         to_float(r.latitude),
         clean_str(r.code_commune, 10))
        for r in sub.itertuples(index=False)
    ]
    n = insert_many(cursor, "Parcelle",
                    ["id_parcelle","ancien_id_parcelle","surface_terrain",
                     "longitude","latitude","code_commune"], rows)
    print(f"  ✓ Parcelle                : {n} lignes")

    # 5. REF_NATURE_CULTURE
    sub = df[["code_nature_culture","nature_culture",
              "code_nature_culture_speciale","nature_culture_speciale"]] \
            .drop_duplicates("code_nature_culture").dropna(subset=["code_nature_culture"])
    rows = [
        (clean_str(r.code_nature_culture, 10),
         clean_str(r.nature_culture, 100),
         clean_str(r.code_nature_culture_speciale, 10),
         clean_str(r.nature_culture_speciale, 100))
        for r in sub.itertuples(index=False)
    ]
    n = insert_many(cursor, "Ref_Nature_Culture",
                    ["code_nature_culture","nature_culture",
                     "code_nature_culture_speciale","nature_culture_speciale"], rows)
    print(f"  ✓ Ref_Nature_Culture      : {n} lignes")

    # 6. PARCELLE_NATURE_CULTURE
    sub = df[["id_parcelle","code_nature_culture","surface_terrain"]] \
            .drop_duplicates(["id_parcelle","code_nature_culture"]) \
            .dropna(subset=["id_parcelle","code_nature_culture"])
    rows = [
        (clean_str(r.id_parcelle, 50),
         clean_str(r.code_nature_culture, 10),
         to_float(r.surface_terrain))
        for r in sub.itertuples(index=False)
    ]
    n = insert_many(cursor, "Parcelle_Nature_Culture",
                    ["id_parcelle","code_nature_culture","surface_nature_culture"], rows)
    print(f"  ✓ Parcelle_Nature_Culture : {n} lignes")

    # 7. REF_TYPE_LOCAL
    sub = df[["code_type_local","type_local"]] \
            .drop_duplicates("code_type_local").dropna(subset=["code_type_local"])
    rows = [
        (clean_str(r.code_type_local, 5),
         clean_str(r.type_local, 100))
        for r in sub.itertuples(index=False)
    ]
    n = insert_many(cursor, "Ref_Type_Local", ["code_type_local","type_local"], rows)
    print(f"  ✓ Ref_Type_Local          : {n} lignes")

    # 8. LOT (dénormalisation lot1..lot5 → lignes)
    lots = []
    for i in range(1, 6):
        nc, sc = f"lot{i}_numero", f"lot{i}_surface_carrez"
        if nc not in df.columns:
            continue
        tmp = df[["numero_volume", nc, sc]].dropna(subset=[nc])
        tmp = tmp.rename(columns={nc: "lot_numero", sc: "surface_carrez"})
        lots.append(tmp)
    if lots:
        all_lots = pd.concat(lots).drop_duplicates("lot_numero")
        rows = [
            (clean_str(r.lot_numero, 20),
             to_int(r.numero_volume),
             to_float(r.surface_carrez))
            for r in all_lots.itertuples(index=False)
        ]
        n = insert_many(cursor, "Lot",
                        ["lot_numero","numero_volume","surface_carrez"], rows)
    else:
        n = 0
    print(f"  ✓ Lot                     : {n} lignes")

    # 9. MUTATION
    sub = df[["id_mutation","date_mutation","numero_disposition","nature_mutation",
              "valeur_fonciere","id_parcelle","adresse_numero","adresse_suffixe","adresse_code_voie"]] \
            .drop_duplicates("id_mutation").dropna(subset=["id_mutation"])
    rows = [
        (clean_str(r.id_mutation, 50),
         clean_str(r.date_mutation),
         to_int(r.numero_disposition),
         clean_str(r.nature_mutation, 100),
         to_float(r.valeur_fonciere),
         clean_str(r.id_parcelle, 50),
         clean_str(r.adresse_numero, 10),
         clean_str(r.adresse_suffixe, 10),
         clean_str(r.adresse_code_voie, 10))
        for r in sub.itertuples(index=False)
    ]
    n = insert_many(cursor, "Mutation",
                    ["id_mutation","date_mutation","numero_disposition","nature_mutation",
                     "valeur_fonciere","id_parcelle","adresse_numero","adresse_suffixe",
                     "adresse_code_voie"], rows)
    print(f"  ✓ Mutation                : {n} lignes")

    # 10. BIEN (génération d'un id_bien séquentiel)
    sub = df[["id_mutation","code_type_local","surface_reelle_bati","nombre_pieces_principales"]] \
            .dropna(subset=["id_mutation"]).drop_duplicates().reset_index(drop=True)
    sub.insert(0, "id_bien", range(1, len(sub) + 1))
    rows = [
        (int(r.id_bien),
         clean_str(r.code_type_local, 5),
         to_int(r.surface_reelle_bati),
         to_int(r.nombre_pieces_principales),
         clean_str(r.id_mutation, 50))
        for r in sub.itertuples(index=False)
    ]
    n = insert_many(cursor, "Bien",
                    ["id_bien","code_type_local","surface_reelle_bati",
                     "nombre_pieces_principales","id_mutation"], rows)
    print(f"  ✓ Bien                    : {n} lignes")

    # 11. LOT_BIEN
    liens = []
    for i in range(1, 6):
        nc = f"lot{i}_numero"
        if nc not in df.columns:
            continue
        tmp = df[["id_mutation", nc]].dropna(subset=[nc]).rename(columns={nc: "lot_numero"})
        tmp = tmp.merge(sub[["id_bien","id_mutation"]], on="id_mutation", how="left")
        liens.append(tmp[["id_bien","lot_numero"]].dropna())
    if liens:
        all_liens = pd.concat(liens).drop_duplicates()
        rows = [
            (int(r.id_bien), clean_str(r.lot_numero, 20))
            for r in all_liens.itertuples(index=False)
        ]
        n = insert_many(cursor, "Lot_Bien", ["id_bien","lot_numero"], rows)
    else:
        n = 0
    print(f"  ✓ Lot_Bien                : {n} lignes")

    conn.commit()
    cursor.close()
    conn.close()


# =============================================================
# LANCEMENT
# =============================================================

if __name__ == "__main__":
    create_database()
    create_tables()
    df = load_file(FILE_PATH)
    feed_all(df)
    print("\n✅ Import terminé — base DVF prête dans SQL Server.")