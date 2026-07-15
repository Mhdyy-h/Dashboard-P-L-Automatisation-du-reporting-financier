# Sprint 2 — Modélisation Power BI et connexion à Oracle

**Projet** : Dashboard P&L — Automatisation du reporting financier
**Encadrante** : Fida
**Stagiaire** : Ala
**Entreprise** : Tunisie Telecom
**Sprint** : 2 sur 6
**Statut** : ✅ Terminé
**Prérequis** : Sprint 1 clôturé (base Oracle peuplée avec 9 768 lignes)

---

## 1. Objectif du sprint

Construire le **modèle de données Power BI** en le connectant à la base Oracle mise en place au Sprint 1. Ce sprint transforme la base de données brute en un modèle analytique prêt à recevoir les mesures avancées et les visualisations des sprints suivants.

### Livrables clés

1. Une connexion Oracle paramétrée depuis Power BI Desktop (avec mécanisme de bascule Mock ↔ Prod)
2. Un modèle de données en **schéma en étoile** avec 11 tables importées et 6 relations
3. Une **table de dates** (Dim_Date) créée en DAX avec hiérarchie temporelle complète
4. Une table de mesures dédiée (`_Mesures`) contenant les 3 premières mesures DAX validées
5. Un fichier `.pbix` sauvegardé et versionné

---

## 2. Rappel des objectifs stratégiques du projet

Le Sprint 2 contribue directement aux trois objectifs stratégiques :

| Objectif | Contribution du Sprint 2 |
|---|---|
| **Automatisation & Fiabilité** | Connexion directe Oracle → Power BI en mode Import. Aucune extraction manuelle. Le rafraîchissement des données devient un clic. |
| **Vue analytique granulaire** | Schéma en étoile avec dimensions BU, CDR, Compte, Offre reliées par des clés étrangères. Découpage possible sur toutes les dimensions. |
| **Visualisation & Pilotage** | Table Dim_Date avec hiérarchie temporelle (Année → Trimestre → Mois → Date) prête pour les drill-down. |

---

## 3. Besoins couverts par le Sprint 2

### Besoins fonctionnels adressés

- **Enrichissement du référentiel** : les 11 tables sont importées avec leurs types et relations, permettant la navigation entre le compte comptable et ses attributs enrichis (BU, CDR, Techno, Offre)
- **Filtres interactifs** : les dimensions sont reliées à la table de faits en cardinalité 1→* et direction Single, préparant le terrain pour les slicers du Sprint 5
- **Drill-down** : la hiérarchie temporelle est en place, la hiérarchie du waterfall P&L le sera au Sprint 4 via Dim_Structure_PL

### Besoins non-fonctionnels adressés

- **Portabilité** : deux paramètres Power Query (`Environnement`, `Serveur_Oracle`) permettent la bascule Mock ↔ Prod en changeant une seule valeur
- **Performance** : mode Import choisi (les données sont chargées en mémoire par Power BI, requêtes DAX ultra-rapides)
- **Maintenabilité** : convention de nommage Pascal case cohérente (`Fact_Balance`, `Dim_BU`, `Dim_CDR`...) au lieu de la casse Oracle en majuscules, améliorant la lisibilité des visuels
- **Traçabilité** : chaque mesure DAX peut être remontée jusqu'à ses lignes source dans Fact_Balance
- **Sécurité** : mot de passe stocké dans le magasin de credentials Power BI (pas en clair dans le code)

---

## 4. Architecture livrée

### 4.1 — Configuration technique

| Composant | Version | Rôle |
|---|---|---|
| Power BI Desktop | (dernière) | Environnement de développement du dashboard |
| Oracle Instant Client | 23.x | Bibliothèque native permettant la connexion depuis Power BI |
| Driver Oracle Database | intégré Power BI | Connecteur de données |

### 4.2 — Paramètres de connexion configurés

| Paramètre Power Query | Valeur actuelle | Rôle |
|---|---|---|
| `Environnement` | `Mock` | Bascule Mock ↔ Prod |
| `Serveur_Oracle` | `localhost:1521/xe` | Serveur Oracle à interroger |

**Utilisateur Oracle** : `pnl_stage` (stocké dans le magasin de credentials Power BI)

### 4.3 — Modèle de données livré

**11 tables importées + 1 table calculée (Dim_Date) = 12 tables au total**

**Table de faits centrale** : `Fact_Balance` (9 768 lignes)

**Dimensions principales reliées** :
- `Dim_Compte` → Fact_Balance (via `COMPTE_COMPTABLE`)
- `Dim_BU` → Fact_Balance (via `BU_CODE`)
- `Dim_CDR` → Fact_Balance (via `CDR_CODE`)
- `Dim_Offre` → Fact_Balance (via `OFFRE_CODE`)
- `Dim_Date` → Fact_Balance (via `Date` ↔ `MOIS`)

**Relation hiérarchique** :
- `Dim_BU` → `Dim_CDR` (via `BU_CODE`) — chaque CDR appartient à une BU

**Tables non reliées** (à connecter via DAX aux sprints suivants) :
- `Dim_Structure_PL` — sera utilisée pour construire le waterfall
- `Cle_Equipement`, `Cle_Incoming` — utilisées via LOOKUPVALUE pour les splits Type III
- `Dim_Capex`, `Dim_New_Digital`, `Dim_Rejet` — tables d'exceptions, actuellement vides

**Cardinalité et direction** : toutes les relations sont en `1 → *` (Un vers Plusieurs) avec direction de filtre **Single** depuis la dimension vers la table de faits. Aucune relation bidirectionnelle.

### 4.4 — Table calculée Dim_Date

Créée en DAX avec la formule `ADDCOLUMNS(CALENDAR(...))`. Contient **730 lignes** couvrant la période du 1er janvier 2025 au 31 décembre 2026.

**Colonnes disponibles pour le reporting** :
- `Date` (clé primaire, marquée comme date table)
- `Année`, `Mois`, `Nom Mois`, `Nom Mois Court`
- `Année-Mois` (format YYYY-MM pour tri chronologique)
- `Trimestre`, `Année-Trimestre`
- `Numéro Jour Semaine`, `Nom Jour`
- `Est Fin de Mois` (flag booléen)

**Hiérarchie créée** : `Hiérarchie Date` = Année → Année-Trimestre → Année-Mois → Date

Cette hiérarchie active les drill-down/drill-up automatiques dans les visuels temporels.

---

## 5. Mesures DAX créées

Une table de mesures dédiée `_Mesures` (préfixée d'un underscore pour apparaître en tête de la liste) contient les mesures de base validées.

### 5.1 — Total Revenue (k'TND)

```dax
Total Revenue (k'TND) =
CALCULATE (
    SUM ( Fact_Balance[MONTANT_TND] ) * -1 / 1000,
    Fact_Balance[CATEGORIE] = "Rev"
)
```

**Logique** : somme des montants filtrés sur les comptes de catégorie "Rev", multipliée par -1 (convention comptable : revenus en négatif dans la balance) et divisée par 1000 pour affichage en k'TND.

**Valeur validée** : cohérente avec le test SQL du Sprint 1 (~598 760 k'TND sur 24 mois).

### 5.2 — Total COS (k'TND)

```dax
Total COS (k'TND) =
CALCULATE (
    SUM ( Fact_Balance[MONTANT_TND] ) / 1000,
    Fact_Balance[CATEGORIE] = "Cos"
)
```

**Logique** : somme des montants filtrés sur les comptes de Cost of Sales. Pas d'inversion de signe (les charges sont déjà positives).

### 5.3 — Total OPEX (k'TND)

```dax
Total OPEX (k'TND) =
CALCULATE (
    SUM ( Fact_Balance[MONTANT_TND] ) / 1000,
    Fact_Balance[CATEGORIE] = "Opex"
)
```

**Logique** : identique à Total COS, filtrée sur la catégorie Opex.

---

## 6. Validation du sprint

### 6.1 — Test de connexion

Connexion Oracle depuis Power BI établie avec succès. Les 11 tables sont visibles dans le Navigator et importables sans erreur.

### 6.2 — Test de volumétrie

| Table | Lignes attendues | Lignes réelles Power BI | Statut |
|---|---:|---:|---|
| Fact_Balance | 9 768 | 9 768 | ✅ |
| Dim_Compte | 47 | 47 | ✅ |
| Dim_CDR | 20 | 20 | ✅ |
| Dim_BU | 5 | 5 | ✅ |
| Dim_Offre | 30 | 30 | ✅ |
| Dim_Structure_PL | 68 | 68 | ✅ |
| Cle_Equipement | 48 | 48 | ✅ |
| Cle_Incoming | 240 | 240 | ✅ |
| Dim_Date (calculée) | 730 | 730 | ✅ |

### 6.3 — Test critique de cohérence Oracle ↔ Power BI

**La mesure `Total Revenue (k'TND)` affiche une valeur cohérente avec le calcul SQL direct effectué au Sprint 1** :

- Requête SQL Sprint 1 : `SELECT SUM(-montant_tnd)/1000 FROM fact_balance WHERE categorie='Rev'` → 598 760 k'TND
- Carte Power BI Sprint 2 : ~598 760 k'TND

Cette égalité valide **l'ensemble de la chaîne** :
1. La connexion Oracle → Power BI est correcte
2. L'import des données n'a rien perdu ni altéré
3. La conversion de type sur MONTANT_TND est correcte
4. La formule DAX reproduit fidèlement la logique métier (inversion de signe + division par 1000)

### 6.4 — Points de contrôle finaux

| Point de contrôle | Statut |
|---|---|
| Oracle Instant Client dans le PATH Windows | ✅ |
| Connexion Oracle établie depuis Power BI | ✅ |
| 11 tables importées via Power Query | ✅ |
| Types de colonnes vérifiés et corrigés | ✅ |
| Tables renommées en Pascal case | ✅ |
| Paramètres Environnement et Serveur_Oracle créés | ✅ |
| Toutes les requêtes utilisent le paramètre Serveur_Oracle | ✅ |
| Relations du schéma en étoile établies (6 relations) | ✅ |
| Dim_Date créée et marquée comme table de dates | ✅ |
| Hiérarchie Date créée | ✅ |
| Table _Mesures créée | ✅ |
| Mesures Total Revenue, Total COS, Total OPEX créées | ✅ |
| Trois cartes de validation affichent des valeurs cohérentes | ✅ |
| Fichier PL_Dashboard_v01.pbix sauvegardé | ✅ |

---

## 7. Difficultés rencontrées et solutions apportées

### 7.1 — Interface Power BI en français

**Symptôme** : le guide de sprint utilisait les noms anglais des menus (Modeling, New table, Report view, etc.), mais l'interface est en français.

**Solution** : correspondance établie entre noms anglais et français :
- Modeling → Modélisation / Outils de table
- New table → Nouvelle table
- Applied Steps → Étapes appliquées
- Report view → Vue Rapport

Cette correspondance est désormais intégrée pour tous les sprints futurs.

### 7.2 — Bouton "Carte" introuvable dans l'onglet Insérer

**Symptôme** : le guide indiquait "Insert → Card", mais dans l'interface Power BI, le bouton Carte n'est pas dans le ruban Insérer.

**Cause** : les visuels de base (Card, Bar chart, Line chart, etc.) sont **directement dans le panneau "Visualisations"** au centre de l'écran, pas dans le ruban.

**Solution** : la carte est créée en cochant la mesure dans le panneau Données, puis en sélectionnant l'icône Carte dans la grille des visualisations si Power BI a choisi un autre type par défaut.

### 7.3 — Trois tables importées vides (Dim_Capex, Dim_New_Digital, Dim_Rejet)

**Symptôme** : ces trois tables apparaissent avec leurs colonnes mais aucune ligne de données.

**Cause** : elles n'ont pas été peuplées volontairement au Sprint 1. Ce sont des tables d'**exceptions métier** spécifiques à Tunisie Telecom qui n'ont pas de sens en mock.

**Décision** : elles restent dans le modèle comme coquilles prêtes à recevoir des données réelles. Elles seront branchées via DAX aux sprints suivants uniquement si nécessaire, ou remplies avec des cas de test volontaires pour valider la logique de routage.

---

## 8. Bonnes pratiques mises en œuvre

### 8.1 — Table de mesures dédiée

La création d'une table `_Mesures` séparée (au lieu de stocker les mesures dans Fact_Balance) est une bonne pratique reconnue. Avantages :
- Toutes les mesures sont regroupées à un seul endroit
- Le préfixe underscore les met en haut de la liste alphabétique
- La suppression accidentelle de la table de faits n'entraîne pas la perte des mesures

### 8.2 — Paramétrage de la connexion

L'utilisation d'un paramètre Power Query `Serveur_Oracle` (au lieu d'une chaîne de connexion en dur) prépare la bascule vers la production. Le jour où Fida fournira l'accès au vrai serveur, la modification tiendra en un seul changement de paramètre, sans toucher au modèle ni aux mesures.

### 8.3 — Convention de nommage

Adoption cohérente du Pascal case (`Fact_Balance`, `Dim_BU`) au lieu de la casse Oracle en majuscules (`FACT_BALANCE`, `DIM_BU`). Améliore significativement la lisibilité des visuels et des expressions DAX.

### 8.4 — Relations à sens unique

Toutes les relations sont en direction **Single** (dimension → fait). Cette pratique évite les ambiguïtés de propagation de filtre en DAX et rend le modèle plus prévisible.

---

## 9. Ouverture vers le Sprint 3

Le Sprint 3 s'appuiera sur ce modèle pour créer **toutes les mesures DAX du waterfall** :

- **Mesures agrégées** : Gross Margin, Gross Margin %, EBITDA, EBITDA %, Net Profit
- **Time Intelligence** : MoM Growth %, YoY Growth %, YTD, Rolling 12M
- **Ventilation B2B/B2C** : par filtrage sur Dim_Offre[SEGMENT]
- **Segmentation dynamique** : mesures paramétrées par BU, CDR, Techno

**Objectif de validation du Sprint 3** : construction d'un P&L waterfall complet, comparable ligne par ligne avec le fichier Excel de référence fourni par Fida.

---

## Annexe A — Structure du modèle de données

```
                    ┌─────────────┐
                    │  Dim_Date   │
                    │  730 lignes │
                    └──────┬──────┘
                           │ (Date ↔ MOIS)
                           │
┌────────────┐             │             ┌────────────┐
│   Dim_BU   │─────────────┤             │  Dim_Offre │
│  5 lignes  │             │             │  30 lignes │
└─────┬──────┘             │             └──────┬─────┘
      │(BU_CODE)           ▼                    │(OFFRE_CODE)
      │           ┌───────────────────┐         │
      ▼           │   Fact_Balance    │◄────────┘
┌────────────┐    │    9 768 lignes   │
│  Dim_CDR   │───▶│  (table de faits) │
│ 20 lignes  │    └────────┬──────────┘
└────────────┘             │(COMPTE_COMPTABLE)
                           ▼
                    ┌─────────────┐
                    │ Dim_Compte  │
                    │  47 lignes  │
                    └─────────────┘

Tables non reliées (utilisées via DAX aux sprints suivants) :
- Dim_Structure_PL (68 lignes)  → waterfall du reporting
- Cle_Equipement (48 lignes)    → clés de répartition S4
- Cle_Incoming (240 lignes)     → clés de répartition S5
- Dim_Rejet, Dim_Capex, Dim_New_Digital → vides, tables d'exceptions
```

---

## Annexe B — Emplacements des livrables

```
C:\PL_Stage\
    01_create_user.sql
    02_create_schema.sql
    03_populate_oracle.py
    PL_Dashboard_v01.pbix          ← livrable principal du Sprint 2
    Docs\
        README_Sprint1.md
        Sprint1_Cloture.md
        Sprint2_Guide.md
        Sprint2_Cloture.md         ← ce document
```
