"""
03_populate_oracle_v4.py
==========================
VERSION 4 - Sprint 5.5 : corrections issues de l'audit de conformite
au cahier des charges (relecture croisee Word + Excel de reference).

Nouveautes par rapport a la v3:
  1. VAS APIGEE vs VAS SERVICES : deux blocs distincts avec les VRAIS
     prefixes de comptes du fichier Excel (705557/604450 = Apigee,
     705100/604100 = Services). Corrige au passage le bug historique
     ou "VAS COST" etait classe par erreur en categorie "Rev".
  2. CHAMP TYPE (Prepaid/Postpaid) : le cahier des charges demande un
     filtre "Type (Mobile, Fixe...)", mais l'analyse du fichier Excel
     reel montre que la colonne TYPE de la balance encode en realite
     Prepaid/Postpaid (via MID(offre,1,1)), et que "Mobile/Fixe" est
     porte par la colonne TECHNO (deja geree). On implemente donc les
     DEUX champs pour couvrir les deux lectures possibles du besoin.
  3. COS PARTIELLEMENT SEGMENTE : deux lignes de COS realistes
     (interconnexion sortante, commission distributeur) recoivent
     desormais un code offre et un segment, permettant de calculer
     un Gross Margin B2B/B2C reellement proratise (et non plus un
     Gross Margin egal au Revenue faute de couts segmentes).

IMPORTANT: adapter le chemin de l'Instant Client ci-dessous si besoin.

USAGE:  python 03_populate_oracle_v4.py
Le script vide les tables avant reinsertion (idempotent).
"""

import random
from datetime import date
import numpy as np
import pandas as pd
import oracledb
from faker import Faker

# Mode thick obligatoire pour Oracle XE 11.2
# ADAPTER LE CHEMIN si votre Instant Client est ailleurs
oracledb.init_oracle_client(lib_dir=r"C:\oracle\instantclient\instantclient_23_0")


# ============================================================
# CONFIG - a ajuster selon votre environnement
# ============================================================
CONNECTION = {
    "user": "pnl_stage",
    "password": "pnl_stage_2026",
    "dsn": "localhost:1521/xe",   # XE 11.2 utilise SID = xe
}

random.seed(42)
np.random.seed(42)
fake = Faker("fr_FR")

# Periode : 24 mois (2025 + 2026) pour permettre YoY dans Power BI
MOIS_LISTE = pd.date_range(start="2025-01-01", periods=24, freq="MS")

# ============================================================
# 1. CONNEXION ORACLE
# ============================================================
print("=" * 60)
print("PEUPLEMENT DE LA BASE ORACLE PNL_STAGE")
print("=" * 60)

conn = oracledb.connect(**CONNECTION)
cur = conn.cursor()
print(f"[OK] Connecte a Oracle: {CONNECTION['dsn']}")


def truncate_all():
    """Vide les tables dans le bon ordre (respect des FK)."""
    tables = [
        "FACT_BALANCE", "CLE_EQUIPEMENT", "CLE_INCOMING",
        "DIM_STRUCTURE_PL", "DIM_REJET", "DIM_NEW_DIGITAL",
        "DIM_CAPEX", "DIM_OFFRE", "DIM_CDR", "DIM_BU", "DIM_COMPTE",
    ]
    for t in tables:
        cur.execute(f"DELETE FROM {t}")
    # Reset la sequence de FACT_BALANCE (specifique XE 11.2)
    try:
        cur.execute("DROP SEQUENCE seq_fact_balance")
        cur.execute("CREATE SEQUENCE seq_fact_balance START WITH 1 INCREMENT BY 1 NOCACHE")
    except oracledb.DatabaseError:
        pass  # sequence n'existe pas encore, ce n'est pas grave
    conn.commit()
    print("[OK] Tables videes")


truncate_all()


# ============================================================
# 2. DIM_BU
# ============================================================
BUS = [
    ("BU_MOBILE",     "Mobile Services",       "B2C"),
    ("BU_FIXE",       "Fixed Services",        "B2C"),
    ("BU_ENTREPRISE", "Enterprise Solutions",  "B2B"),
    ("BU_DIGITAL",    "Digital & VAS",         "B2C"),
    ("BU_WHOLESALE",  "Wholesale / Interco",   "Wholesale"),
]
cur.executemany(
    "INSERT INTO dim_bu (bu_code, bu_name, bu_type) VALUES (:1, :2, :3)",
    BUS,
)
print(f"[OK] DIM_BU: {len(BUS)} lignes")


# ============================================================
# 3. DIM_CDR (4 CDR par BU)
# ============================================================
cdr_rows = []
for bu_code, bu_name, _ in BUS:
    for i in range(1, 5):
        cdr_rows.append((
            f"{bu_code}_CDR{i:02d}",
            f"{bu_name} - {fake.city()}",
            bu_code,
        ))
cur.executemany(
    "INSERT INTO dim_cdr (cdr_code, cdr_name, bu_code) VALUES (:1, :2, :3)",
    cdr_rows,
)
print(f"[OK] DIM_CDR: {len(cdr_rows)} lignes")


# ============================================================
# 4. DIM_OFFRE
# ============================================================
TECHNOS = ["Mobile", "Fixed", "Digital"]
offre_rows = []
for i in range(1, 31):
    segment = np.random.choice(["B2C", "B2B", "Wholesale"], p=[0.60, 0.30, 0.10])
    techno = np.random.choice(TECHNOS, p=[0.60, 0.25, 0.15])
    offre_rows.append((
        f"OFR{i:03d}",
        f"Offre {fake.word().capitalize()} {i}",
        segment,
        techno,
    ))
cur.executemany(
    "INSERT INTO dim_offre (offre_code, offre_name, segment, techno) "
    "VALUES (:1, :2, :3, :4)",
    offre_rows,
)
print(f"[OK] DIM_OFFRE: {len(offre_rows)} lignes")

# NOUVEAU V4: champ TYPE (Prepaid/Postpaid).
# Dans le fichier Excel reel, Type = IF(1er digit du code offre = "1",
# "Prepaid", ...="2","Postpaid",...). Notre mock ne reproduit pas ce
# codage numerique, mais reproduit le RESULTAT : chaque offre a un type
# d'abonnement fixe et coherent (~72% Prepaid, ~28% Postpaid, realiste
# pour un marche telecom grand public). Stocke cote Python (pas besoin
# de modifier le schema DIM_OFFRE) et applique a chaque ligne de fait
# qui porte un code offre.
OFFRE_TYPE = {
    row[0]: np.random.choice(["Prepaid", "Postpaid"], p=[0.72, 0.28])
    for row in offre_rows
}


# ============================================================
# 5. DIM_COMPTE (Mapping General)
# ============================================================
# Lignes de P&L reprises du fichier reel de reference
REVENUE_LINES = [
    ("Outgoing National Onnet",   "Voice",     "BU_MOBILE"),
    ("Outgoing National Offnet",  "Voice",     "BU_MOBILE"),
    ("Outgoing International",    "Voice",     "BU_MOBILE"),
    ("Subscriber Roaming Voice",  "Voice",     "BU_MOBILE"),
    ("DATA Services",             "Data",      "BU_MOBILE"),
    ("SMS/MMS Services",          "Messaging", "BU_MOBILE"),
    # NOUVEAU V4: VAS Services et VAS Apigee separes (le cahier des
    # charges exige explicitement cette distinction ; le fichier reel
    # les traite dans deux blocs de comptes distincts : 705100/604100
    # pour Services, 705557/604450 pour Apigee).
    ("VAS Services Revenue",      "Digital",   "BU_DIGITAL"),
    ("VAS Apigee Revenue",        "Digital",   "BU_DIGITAL"),
    ("Incoming National Voice",   "Interco",   "BU_WHOLESALE"),
    ("Incoming National SMS/MMS", "Interco",   "BU_WHOLESALE"),
    ("Incoming International Voice", "Interco", "BU_WHOLESALE"),
    ("Interoperators Revenue",    "Interco",   "BU_WHOLESALE"),
    ("Connection Fees",           "Other",     "BU_MOBILE"),
    ("Equipment Revenue",         "Equipment", "BU_FIXE"),
    ("Fixed Revenue",             "Fixed",     "BU_FIXE"),
    ("ICT services",              "Other",     "BU_ENTREPRISE"),
    ("IOT Services",              "Other",     "BU_ENTREPRISE"),
    ("Others (Miscellaneous)",    "Other",     "BU_MOBILE"),
    ("Commercial Partnership",    "Other",     "BU_DIGITAL"),
    ("SOS",                       "Other",     "BU_DIGITAL"),
    # NOUVEAU V3: les gratuites, enregistrees globalement SANS segment.
    # C'est cette ligne qui doit etre ventilee par le Split Type II.
    ("Gratuités et crédit perdu", "Voice",     "BU_MOBILE"),
]
COS_LINES = [
    # NOUVEAU V4: ces deux lignes recoivent desormais un code offre et
    # un segment (voir COS_LINES_AVEC_OFFRE plus bas), pour permettre
    # un vrai proratage B2B/B2C des couts -- pas seulement des revenus.
    ("CoS- VOICE Outgoing Off Net Mobile",     "Voice",     "BU_WHOLESALE"),
    ("Dealer Commission",                      "Other",     "BU_MOBILE"),
    ("CoS- VOICE Outgoing International",      "Voice",     "BU_WHOLESALE"),
    ("CoS- VOICE International Roaming",       "Voice",     "BU_WHOLESALE"),
    ("COS National SMS/MMS",                   "Messaging", "BU_WHOLESALE"),
    ("COS Internationnal SMS/MMS",             "Messaging", "BU_WHOLESALE"),
    ("Digital CoS",                            "Digital",   "BU_DIGITAL"),
    ("SIM Cards costs",                        "Other",     "BU_MOBILE"),
    ("Recharge Cards COST",                    "Other",     "BU_MOBILE"),
    ("Equipment costs",                        "Equipment", "BU_FIXE"),
    ("Wholesale CoS",                          "Interco",   "BU_WHOLESALE"),
    ("Other Cost of sales items",              "Other",     "BU_MOBILE"),
    # NOUVEAU V4: VAS COST correctement classes en COS (categorie "Cos"),
    # ce qui corrige le bug historique v1-v3 ou "VAS COST" figurait par
    # erreur dans REVENUE_LINES (categorie "Rev"), obligeant a exclure
    # manuellement le compte 604 de la mesure Total Revenue en DAX.
    ("VAS Services Cost",                      "Digital",   "BU_DIGITAL"),
    ("VAS Apigee Cost",                        "Digital",   "BU_DIGITAL"),
]

# NOUVEAU V4: lignes de COS qui recoivent un code offre + segment,
# permettant de calculer des couts reellement proratises par segment
# (au lieu d'un Gross Margin B2B egal au Revenue B2B faute de couts
# identifiables). Choix realiste : interconnexion sortante et
# commission distributeur sont, dans la vraie balance, rattachees a
# une offre (donc a un segment) au niveau transaction.
COS_LINES_AVEC_OFFRE = {
    "CoS- VOICE Outgoing Off Net Mobile",
    "Dealer Commission",
}
OPEX_LINES = [
    ("Network operation and maintenance", "Other", "BU_ENTREPRISE"),
    ("Leased Lines",                      "Other", "BU_ENTREPRISE"),
    ("Employee salaries",                 "Other", "BU_ENTREPRISE"),
    ("Employee benefits",                 "Other", "BU_ENTREPRISE"),
    ("Marketing",                         "Other", "BU_ENTREPRISE"),
    ("Advertising",                       "Other", "BU_ENTREPRISE"),
    ("Bad Debts Provisions",              "Other", "BU_ENTREPRISE"),
    ("Office rent",                       "Other", "BU_ENTREPRISE"),
    ("Office utilities",                  "Other", "BU_ENTREPRISE"),
    ("Legal and professional fees",       "Other", "BU_ENTREPRISE"),
    ("Business Travel",                   "Other", "BU_ENTREPRISE"),
    ("Depreciation",                      "Other", "BU_ENTREPRISE"),
    ("Amortization",                      "Other", "BU_ENTREPRISE"),
]

compte_rows = []

# NOUVEAU V4: prefixes REELS releves dans le fichier Excel de reference
# (feuille Mapping General). Ce sont ces prefixes exacts qui permettent
# a la mesure DAX LEFT(compte,6) de distinguer Apigee de Services --
# authentique, pas invente.
VAS_ACCOUNT_MAP = {
    "VAS Services Revenue": "705100",   # revenus VAS Services -> 705100
    "VAS Services Cost":    "604100",   # couts VAS Services   -> 604100
    "VAS Apigee Revenue":   "705557",   # revenus VAS Apigee   -> 705557 (reel)
    "VAS Apigee Cost":      "604450",   # couts VAS Apigee     -> 604450 (reel)
}

account_num = 700000  # Revenus commencent en classe 7
for libelle, techno, bu in REVENUE_LINES:
    if libelle in VAS_ACCOUNT_MAP:
        numero = VAS_ACCOUNT_MAP[libelle]
    else:
        account_num += 100
        numero = f"{account_num}"
    compte_rows.append((
        f"{numero}-0000",
        libelle,
        libelle, "Rev",
        numero[:3],
    ))

# NOUVEAU V3: compte de remises VAS (classe 709), separe des revenus
compte_rows.append((
    "709100-0000",
    "VAS Remises et discounts",
    "VAS Remises", "Rev",
    "709",
))

account_num = 600000  # Charges commencent en classe 6
for libelle, techno, bu in COS_LINES:
    if libelle in VAS_ACCOUNT_MAP:
        numero = VAS_ACCOUNT_MAP[libelle]
    else:
        account_num += 100
        numero = f"{account_num}"
    compte_rows.append((
        f"{numero}-0000",
        libelle,
        libelle, "Cos",
        numero[:3],
    ))
for libelle, techno, bu in OPEX_LINES:
    account_num += 100
    compte_rows.append((
        f"{account_num}-0000",
        libelle,
        libelle, "Opex",
        "610",
    ))

# 3 comptes volontairement "orphelins" pour tester le controle Zero Null
for i in range(3):
    compte_rows.append((
        f"69900{i}-0000",
        "Compte non mappe (a corriger)",
        None, "Null",
        None,
    ))

# Insertion DIM_COMPTE
insert_compte = """
INSERT INTO dim_compte (compte_comptable, descriptif, pl_line, categorie, ncoa_mapping)
VALUES (:1, :2, :3, :4, :5)
"""
cur.executemany(insert_compte, compte_rows)
print(f"[OK] DIM_COMPTE: {len(compte_rows)} lignes")


# ============================================================
# 6. DIM_STRUCTURE_PL (waterfall des 221 lignes du reporting)
# ============================================================
STRUCTURE = [
    # (ordre, section, niveau, parent_id, libelle, segment, type_calcul)
    (10,  "Revenue", 1, None, "B2B Service Revenue",        "B2B",    "AGG"),
    (20,  "Revenue", 2, 10,   "B2B Mobile Service",         "B2B",    "AGG"),
    (30,  "Revenue", 3, 20,   "Outgoing National Onnet",    "B2B",    "SPLIT"),
    (40,  "Revenue", 3, 20,   "Outgoing National Offnet",   "B2B",    "SPLIT"),
    (50,  "Revenue", 3, 20,   "Outgoing International",     "B2B",    "SPLIT"),
    (60,  "Revenue", 3, 20,   "Subscriber Roaming Voice",   "B2B",    "SPLIT"),
    (70,  "Revenue", 3, 20,   "DATA Services",              "B2B",    "SPLIT"),
    (80,  "Revenue", 3, 20,   "VAS Services Revenue",       "B2B",    "SPLIT"),
    (85,  "Revenue", 3, 20,   "VAS Apigee Revenue",         "B2B",    "SPLIT"),
    (90,  "Revenue", 3, 20,   "SMS/MMS Services",           "B2B",    "SPLIT"),
    (100, "Revenue", 3, 20,   "Commercial Partnership",     "B2B",    "SUMIFS"),
    (110, "Revenue", 3, 20,   "SOS",                        "B2B",    "SUMIFS"),
    (120, "Revenue", 3, 20,   "Connection Fees",            "B2B",    "SUMIFS"),
    (130, "Revenue", 3, 20,   "Others (Miscellaneous)",     "B2B",    "SUMIFS"),
    (140, "Revenue", 3, 20,   "ICT services",               "B2B",    "SUMIFS"),
    (150, "Revenue", 3, 20,   "IOT Services",               "B2B",    "SUMIFS"),

    (200, "Revenue", 1, None, "B2C Service Revenue",        "B2C",    "AGG"),
    (210, "Revenue", 2, 200,  "B2C Mobile Service",         "B2C",    "AGG"),
    (220, "Revenue", 3, 210,  "Outgoing National Onnet",    "B2C",    "SPLIT"),
    (230, "Revenue", 3, 210,  "Outgoing National Offnet",   "B2C",    "SPLIT"),
    (240, "Revenue", 3, 210,  "Outgoing International",     "B2C",    "SPLIT"),
    (250, "Revenue", 3, 210,  "Subscriber Roaming Voice",   "B2C",    "SPLIT"),
    (260, "Revenue", 3, 210,  "DATA Services",              "B2C",    "SPLIT"),
    (270, "Revenue", 3, 210,  "VAS Services Revenue",       "B2C",    "SPLIT"),
    (275, "Revenue", 3, 210,  "VAS Apigee Revenue",         "B2C",    "SPLIT"),
    (280, "Revenue", 3, 210,  "SMS/MMS Services",           "B2C",    "SPLIT"),
    (290, "Revenue", 3, 210,  "Connection Fees",            "B2C",    "SUMIFS"),
    (300, "Revenue", 3, 210,  "Fixed Revenue",              "B2C",    "SUMIFS"),

    (400, "Revenue", 1, None, "Wholesales Revenue",         "Wholesale", "AGG"),
    (410, "Revenue", 3, 400,  "Incoming National Voice",    "Wholesale", "SPLIT"),
    (420, "Revenue", 3, 400,  "Incoming National SMS/MMS",  "Wholesale", "SPLIT"),
    (430, "Revenue", 3, 400,  "Interoperators Revenue",     "Wholesale", "SUMIFS"),

    (500, "Revenue", 1, None, "Equipment Revenue",          None,     "AGG"),
    (510, "Revenue", 3, 500,  "Equipment Revenue",          None,     "SUMIFS"),

    (600, "Revenue", 1, None, "TOTAL REVENUE",              None,     "FORMULA"),

    (700, "COS", 1, None, "Service COST",                   None,     "AGG"),
    (710, "COS", 3, 700,  "CoS- VOICE Outgoing Off Net Mobile", None, "SUMIFS"),
    (720, "COS", 3, 700,  "CoS- VOICE Outgoing International",  None, "SUMIFS"),
    (730, "COS", 3, 700,  "CoS- VOICE International Roaming",   None, "SUMIFS"),
    (740, "COS", 3, 700,  "COS National SMS/MMS",               None, "SUMIFS"),
    (750, "COS", 3, 700,  "COS Internationnal SMS/MMS",         None, "SUMIFS"),
    (760, "COS", 3, 700,  "Digital CoS",                        None, "SUMIFS"),
    (770, "COS", 3, 700,  "Dealer Commission",                  None, "SUMIFS"),
    (780, "COS", 3, 700,  "SIM Cards costs",                    None, "SUMIFS"),
    (790, "COS", 3, 700,  "Recharge Cards COST",                None, "SUMIFS"),
    (800, "COS", 3, 700,  "Wholesale CoS",                      None, "SUMIFS"),
    (810, "COS", 3, 700,  "Other Cost of sales items",          None, "SUMIFS"),
    (820, "COS", 3, 700,  "Equipment costs",                    None, "SUMIFS"),
    (830, "COS", 1, None, "Total Cost of Sales",                None, "FORMULA"),

    (900, "GrossMargin", 1, None, "Gross Margin",           None,     "FORMULA"),
    (910, "GrossMargin", 1, None, "Gross Margin %",         None,     "FORMULA"),

    (1000, "Opex", 1, None, "OPERATING EXPENSES",           None,     "AGG"),
    (1010, "Opex", 3, 1000, "Network operation and maintenance", None, "SUMIFS"),
    (1020, "Opex", 3, 1000, "Leased Lines",                  None,    "SUMIFS"),
    (1030, "Opex", 3, 1000, "Employee salaries",             None,    "SUMIFS"),
    (1040, "Opex", 3, 1000, "Employee benefits",             None,    "SUMIFS"),
    (1050, "Opex", 3, 1000, "Marketing",                     None,    "SUMIFS"),
    (1060, "Opex", 3, 1000, "Advertising",                   None,    "SUMIFS"),
    (1070, "Opex", 3, 1000, "Bad Debts Provisions",          None,    "SUMIFS"),
    (1080, "Opex", 3, 1000, "Office rent",                   None,    "SUMIFS"),
    (1090, "Opex", 3, 1000, "Office utilities",              None,    "SUMIFS"),
    (1100, "Opex", 3, 1000, "Legal and professional fees",   None,    "SUMIFS"),
    (1110, "Opex", 3, 1000, "Business Travel",               None,    "SUMIFS"),
    (1120, "Opex", 1, None, "Total Operating Expenses (OPEX)", None,  "FORMULA"),

    (1200, "EBITDA", 1, None, "EBITDA",                     None,     "FORMULA"),
    (1210, "EBITDA", 1, None, "EBITDA %",                   None,     "FORMULA"),
    (1220, "EBITDA", 3, 1200, "Depreciation",               None,     "SUMIFS"),
    (1230, "EBITDA", 3, 1200, "Amortization",               None,     "SUMIFS"),
    (1240, "EBIT",   1, None, "Operating Margin EBIT",      None,     "FORMULA"),
    (1300, "Net",    1, None, "NET PROFIT/(LOSS)",          None,     "FORMULA"),
]

# Ajoute un pl_id sequentiel
structure_rows = []
for pl_id, row in enumerate(STRUCTURE, start=1):
    ordre, section, niveau, parent_id, libelle, segment, type_calcul = row
    structure_rows.append((
        pl_id, ordre, section, niveau, parent_id, libelle, segment, type_calcul,
    ))

cur.executemany(
    "INSERT INTO dim_structure_pl (pl_id, ordre, section, niveau, parent_id, "
    "libelle, segment, type_calcul) VALUES (:1, :2, :3, :4, :5, :6, :7, :8)",
    structure_rows,
)
print(f"[OK] DIM_STRUCTURE_PL: {len(structure_rows)} lignes")


# ============================================================
# 7. CLES MANUELLES (S4 Equipement + S5 Incoming)
# ============================================================
# NOUVEAU V3: ratios calibres sur les valeurs reelles du fichier Excel.
# S4 Equipement: le B2B domine tres largement (~97-98%), car les ventes
# de terminaux/box passent majoritairement par les canaux entreprise.
cle_equip_rows = []
for mois in MOIS_LISTE:
    ratio_b2b = np.clip(np.random.normal(0.976, 0.006), 0.960, 0.995)
    cle_equip_rows.append((mois.date(), "B2B", round(ratio_b2b, 4)))
    cle_equip_rows.append((mois.date(), "B2C", round(1 - ratio_b2b, 4)))
cur.executemany(
    "INSERT INTO cle_equipement (mois, segment, ratio) VALUES (:1, :2, :3)",
    cle_equip_rows,
)
print(f"[OK] CLE_EQUIPEMENT: {len(cle_equip_rows)} lignes (ratio B2B ~97.6%)")

# S5 Incoming: 3 intitules reels, avec des ratios B2B distincts par nature
# de trafic (calibres sur le fichier Excel de reference).
INCOMING_RATIOS = {
    "Incoming National Voice":      0.169,   # ~17% B2B
    "Incoming National SMS/MMS":    0.272,   # ~27% B2B (l'A2P tire vers le haut)
    "Incoming International Voice": 0.143,   # ~14% B2B
}
cle_incoming_rows = []
for mois in MOIS_LISTE:
    for intitule, ratio_moyen in INCOMING_RATIOS.items():
        ratio_b2b = np.clip(
            np.random.normal(ratio_moyen, 0.008),
            ratio_moyen - 0.03,
            ratio_moyen + 0.03,
        )
        cle_incoming_rows.append((mois.date(), intitule, "B2B", round(ratio_b2b, 6)))
        cle_incoming_rows.append((mois.date(), intitule, "B2C", round(1 - ratio_b2b, 6)))
cur.executemany(
    "INSERT INTO cle_incoming (mois, intitule, segment, ratio) "
    "VALUES (:1, :2, :3, :4)",
    cle_incoming_rows,
)
print(f"[OK] CLE_INCOMING: {len(cle_incoming_rows)} lignes (3 intitules reels)")


# ============================================================
# 7bis. TABLE REJET - exceptions de mapping (NOUVEAU V3)
# ============================================================
# Certains triplets Compte+Offre+CDR doivent contourner la logique de
# mapping standard. Le fichier Excel reel a 71 exceptions; on en simule 5.
cur.execute("SELECT compte_comptable FROM dim_compte WHERE categorie = 'Rev'")
comptes_rev = [r[0] for r in cur.fetchall()]
cur.execute("SELECT offre_code FROM dim_offre")
offres_all = [r[0] for r in cur.fetchall()]
cur.execute("SELECT cdr_code, bu_code FROM dim_cdr")
cdrs_all = cur.fetchall()

rejet_rows = []
for i in range(5):
    compte = random.choice(comptes_rev)
    offre = random.choice(offres_all)
    cdr, bu = random.choice(cdrs_all)
    cle_composite = f"{compte}{offre}{cdr}"
    rejet_rows.append((
        cle_composite[:60],
        compte,
        offre,
        cdr,
        "Others (Miscellaneous)",   # mapping force par exception
        bu,
    ))
cur.executemany(
    "INSERT INTO dim_rejet (cle_composite, compte, offre, cdr, pl_line, bu) "
    "VALUES (:1, :2, :3, :4, :5, :6)",
    rejet_rows,
)
print(f"[OK] DIM_REJET: {len(rejet_rows)} exceptions de mapping")


# ============================================================
# 8. FACT_BALANCE - Le gros morceau
# ============================================================
# Recupere les mappings a partir des dimensions inserees
cur.execute("SELECT bu_code FROM dim_bu")
bus_codes = [r[0] for r in cur.fetchall()]

cur.execute("SELECT cdr_code, bu_code FROM dim_cdr")
cdr_by_bu = {}
for cdr_code, bu_code in cur.fetchall():
    cdr_by_bu.setdefault(bu_code, []).append(cdr_code)

cur.execute("SELECT offre_code, segment, techno FROM dim_offre")
all_offres = cur.fetchall()

cur.execute("SELECT compte_comptable, pl_line, categorie FROM dim_compte")
comptes = cur.fetchall()

# Mapping compte -> BU probable (via le libelle P&L)
def guess_bu(pl_line):
    if pl_line is None:
        return None
    pl = pl_line.lower()
    if any(k in pl for k in ["fixed", "equipment"]):
        return "BU_FIXE"
    if any(k in pl for k in ["ict", "iot", "salar", "benef", "office",
                              "marketing", "advert", "legal", "travel",
                              "leased", "network", "bad debts"]):
        return "BU_ENTREPRISE"
    if any(k in pl for k in ["vas", "digital", "commercial", "sos"]):
        return "BU_DIGITAL"
    if any(k in pl for k in ["incoming", "interoperator", "wholesale",
                              "voice outgoing", "sms/mms international"]):
        return "BU_WHOLESALE"
    return "BU_MOBILE"


def seasonal_factor(mois_ts, techno_or_pl):
    """Saisonnalite realiste."""
    m = mois_ts.month
    label = (techno_or_pl or "").lower()
    if any(k in label for k in ["roaming", "international"]) and m in (6, 7, 8):
        return 1.40  # pic ete tourisme
    if "equipment" in label and m == 12:
        return 1.60  # pic Noel
    if "vas" in label and m in (11, 12):
        return 1.20
    return 1.0


fact_rows = []


def get_amount_range(categorie, pl_line):
    """Retourne (min, max) pour base_amount, calibre aux ratios telecom.
    
    Objectif: reproduire les proportions typiques d'un operateur telecom:
    Revenue 100%, COS 40%, OPEX 30%, D&A 13%, EBITDA 30%, Net Profit 17%.
    """
    if categorie == "Rev":
        return (80_000, 500_000)   # avg 290K -> Revenue total 598K
    if categorie == "Cos":
        return (50_000, 320_000)   # avg 185K -> COS total ~240K (40% du CA)
    if categorie == "Opex":
        # D&A traite separement: peu de comptes -> montants unitaires plus grands
        if pl_line in ("Depreciation", "Amortization"):
            return (200_000, 500_000)  # avg 350K -> D&A total ~80K (13% du CA)
        return (30_000, 250_000)   # avg 140K -> OPEX total ~180K (30% du CA)
    return (50_000, 300_000)       # fallback pour comptes orphelins


for compte, pl_line, categorie in comptes:
    bu_code = guess_bu(pl_line)
    if bu_code is None:
        # compte orphelin -> 1 CDR aleatoire, quelques mouvements
        random_bu = random.choice(bus_codes)
        cdr_pool = cdr_by_bu[random_bu][:1]
    else:
        cdr_pool = cdr_by_bu[bu_code]

    is_revenue = (categorie == "Rev")
    # NOUVEAU EN V2: plage adaptee a la categorie du compte
    min_amt, max_amt = get_amount_range(categorie, pl_line)
    base_amount = np.random.uniform(min_amt, max_amt)
    monthly_trend = np.random.uniform(0.00, 0.02)  # croissance

    # NOUVEAU V3: certaines lignes P&L sont enregistrees GLOBALEMENT,
    # sans distinction B2B/B2C. Elles n'ont donc pas de segment et devront
    # etre ventilees par les splits Type II (ratio dynamique) ou Type III
    # (cles manuelles S4/S5). C'est toute la complexite metier du projet.
    LIGNES_SANS_SEGMENT = {
        "Gratuités et crédit perdu",      # -> Type II (ratio dynamique)
        "Equipment Revenue",              # -> Type III (cle S4)
        "Incoming National Voice",        # -> Type III (cle S5)
        "Incoming National SMS/MMS",      # -> Type III (cle S5)
        "Incoming International Voice",   # -> Type III (cle S5)
    }
    ligne_globale = pl_line in LIGNES_SANS_SEGMENT

    # NOUVEAU V4: une ligne de COS peut desormais porter une offre/segment
    # si elle figure dans COS_LINES_AVEC_OFFRE (voir plus haut). On la
    # traite alors comme une ligne "avec offre", au meme titre qu'une
    # ligne de revenu, tout en gardant sa categorie Cos (donc son signe
    # positif) intacte.
    cos_avec_offre = (categorie == "Cos") and (pl_line in COS_LINES_AVEC_OFFRE)
    assigne_offre = (is_revenue and not ligne_globale) or cos_avec_offre

    # Pour les lignes avec offre: chaque compte/CDR/mois genere plusieurs
    # mouvements (multiples offres), ce qui reflete une vraie balance
    nb_offres_par_mois = 4 if assigne_offre else 1

    for cdr in cdr_pool:
        for idx, mois in enumerate(MOIS_LISTE):
            for _ in range(nb_offres_par_mois):
                if assigne_offre:
                    offre_choice = random.choice(all_offres)
                    offre_code, seg, techno = offre_choice
                else:
                    # Ligne globale (Type II/III) ou ligne standard sans
                    # offre (Opex, la plupart des Cos) : pas d'offre.
                    offre_code, seg, techno = None, None, None

                # NOUVEAU V4: TYPE (Prepaid/Postpaid), derive de l'offre
                # quand elle existe -- exactement comme la vraie formule
                # Excel MID(offre,1,1), qui depend elle aussi du code
                # offre et est donc vide quand il n'y a pas d'offre.
                type_abonnement = OFFRE_TYPE.get(offre_code) if offre_code else None

                noise = np.random.normal(1.0, 0.08)
                season = seasonal_factor(mois, pl_line)
                # Chaque offre = fraction du montant total du compte
                montant = (base_amount / nb_offres_par_mois) * \
                          ((1 + monthly_trend) ** idx) * season * noise

                # Anomalie ponctuelle: pics exceptionnels
                if np.random.rand() < 0.015:
                    montant *= np.random.uniform(2.5, 4)

                # Convention de signe: revenus en negatif (classe 7)
                montant = -abs(montant) if is_revenue else abs(montant)

                # Anomalie qualite: ~1% CDR manquants (donnee realiste)
                cdr_final = cdr if np.random.rand() > 0.01 else None

                fact_rows.append((
                    mois.date(),
                    compte,
                    cdr_final,
                    offre_code,
                    bu_code,
                    seg,
                    pl_line,
                    pl_line,      # pl_conso = meme chose en mock
                    categorie,
                    techno,
                    type_abonnement,   # NOUVEAU V4: Prepaid/Postpaid
                    round(montant, 3),
                ))

# Insertion en batch (executemany avec commit unique = rapide)
print(f"[..] Insertion FACT_BALANCE ({len(fact_rows):,} lignes)...")
insert_fact = """
INSERT INTO fact_balance
   (mois, compte_comptable, cdr_code, offre_code, bu_code, segment,
    pl_line, pl_conso, categorie, techno, type, montant_tnd)
VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11, :12)
"""
BATCH = 5000
for i in range(0, len(fact_rows), BATCH):
    cur.executemany(insert_fact, fact_rows[i:i + BATCH])
    conn.commit()
    print(f"     {i + BATCH:,} / {len(fact_rows):,} lignes inserees...")

print(f"[OK] FACT_BALANCE: {len(fact_rows):,} lignes")


# ============================================================
# 9. VERIFICATION FINALE
# ============================================================
print("\n" + "=" * 60)
print("RECAP FINAL")
print("=" * 60)
tables = ["DIM_BU", "DIM_CDR", "DIM_OFFRE", "DIM_COMPTE", "DIM_STRUCTURE_PL",
          "CLE_EQUIPEMENT", "CLE_INCOMING", "DIM_REJET", "FACT_BALANCE"]
for t in tables:
    cur.execute(f"SELECT COUNT(*) FROM {t}")
    n = cur.fetchone()[0]
    print(f"  {t:25s} {n:>10,} lignes")

# Quelques KPI de coherence
print("\nSanity checks:")
cur.execute("""
   SELECT ROUND(SUM(CASE WHEN categorie='Rev' THEN -montant_tnd ELSE 0 END)/1000, 0)
   FROM fact_balance
""")
print(f"  Revenu total 24 mois (k'TND): {cur.fetchone()[0]:,}")

cur.execute("""
   SELECT COUNT(DISTINCT mois) FROM fact_balance
""")
print(f"  Nombre de mois distincts:     {cur.fetchone()[0]}")

cur.execute("""
   SELECT COUNT(*) FROM fact_balance WHERE cdr_code IS NULL
""")
print(f"  Lignes CDR manquant (attendu ~1%): {cur.fetchone()[0]}")

cur.execute("""
   SELECT COUNT(*) FROM dim_compte WHERE categorie = 'Null'
""")
print(f"  Comptes non mappes (Null):    {cur.fetchone()[0]}")

# ============================================================
# CHECKS SPECIFIQUES V3 (regles metier avancees)
# ============================================================
print("\n--- Checks V3 (Sprint 5) ---")

cur.execute("""
   SELECT ROUND(SUM(-montant_tnd)/1000, 0)
   FROM   fact_balance
   WHERE  pl_line = 'Gratuités et crédit perdu'
""")
grat = cur.fetchone()[0]
print(f"  Gratuites totales (k'TND):    {grat:,}  <- a ventiler par Type II")

cur.execute("""
   SELECT COUNT(*)
   FROM   fact_balance
   WHERE  segment IS NULL AND categorie = 'Rev'
""")
print(f"  Lignes revenus SANS segment:  {cur.fetchone()[0]:,}  <- cibles des splits")

cur.execute("""
   SELECT SUBSTR(compte_comptable, 1, 3) AS classe, COUNT(*)
   FROM   fact_balance
   WHERE  SUBSTR(compte_comptable, 1, 3) IN ('705', '709', '604')
   GROUP  BY SUBSTR(compte_comptable, 1, 3)
   ORDER  BY classe
""")
print("  Comptes VAS structures:")
for classe, n in cur.fetchall():
    label = {"604": "Couts", "705": "Revenus", "709": "Remises"}.get(classe, "?")
    print(f"    {classe} ({label:8s}): {n:>6,} lignes")

cur.execute("SELECT ROUND(AVG(ratio), 4) FROM cle_equipement WHERE segment = 'B2B'")
print(f"  Ratio moyen S4 Equipement B2B: {cur.fetchone()[0]}  (attendu ~0.976)")

cur.execute("""
   SELECT intitule, ROUND(AVG(ratio), 4)
   FROM   cle_incoming WHERE segment = 'B2B'
   GROUP  BY intitule ORDER BY intitule
""")
print("  Ratios moyens S5 Incoming B2B:")
for intitule, r in cur.fetchall():
    print(f"    {intitule:32s} {r}")

# ============================================================
# CHECKS SPECIFIQUES V4 (Sprint 5.5 - corrections d'audit)
# ============================================================
print("\n--- Checks V4 (Sprint 5.5) ---")

cur.execute("""
   SELECT pl_line, ROUND(SUM(CASE WHEN categorie='Rev' THEN -montant_tnd
                                   ELSE montant_tnd END)/1000, 0)
   FROM   fact_balance
   WHERE  pl_line IN ('VAS Services Revenue','VAS Apigee Revenue',
                       'VAS Services Cost','VAS Apigee Cost')
   GROUP  BY pl_line
   ORDER  BY pl_line
""")
print("  VAS Services vs Apigee (k'TND):")
for pl, v in cur.fetchall():
    print(f"    {pl:24s} {v:>10,}")

cur.execute("""
   SELECT COUNT(*) FROM fact_balance WHERE type IS NOT NULL
""")
n_type = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM fact_balance")
n_total = cur.fetchone()[0]
print(f"  Lignes avec TYPE renseigne: {n_type:,} / {n_total:,} ({n_type/n_total*100:.1f}%)")

cur.execute("""
   SELECT pl_line, COUNT(*), ROUND(SUM(montant_tnd)/1000, 0)
   FROM   fact_balance
   WHERE  pl_line IN ('CoS- VOICE Outgoing Off Net Mobile', 'Dealer Commission')
     AND  segment IS NOT NULL
   GROUP  BY pl_line
""")
print("  COS desormais segmente (proratisable B2B/B2C):")
for pl, n, v in cur.fetchall():
    print(f"    {pl:38s} {n:>5,} lignes, {v:>8,} k'TND")

conn.commit()
cur.close()
conn.close()
print("\n[OK] Base V4 peuplee. Rafraichissez Power BI (Accueil > Actualiser).")
