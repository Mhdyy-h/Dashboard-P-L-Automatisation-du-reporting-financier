# Documentation technique — Dashboard P&L Tunisie Telecom

**Version** : 1.0
**Public** : développeur BI, référent technique, mainteneur
**Objectif** : permettre à un tiers de comprendre, maintenir et faire évoluer la solution.

---

## 1. Vue d'ensemble de l'architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌───────────┐    ┌─────────┐
│   Oracle    │ →  │ Power Query  │ →  │ Modèle en étoile│ →  │ Mesures   │ →  │ Visuels │
│   XE 11.2   │    │ (ETL/nettoy.)│    │ (relations)     │    │ DAX (~70) │    │ 3 pages │
└─────────────┘    └──────────────┘    └─────────────────┘    └───────────┘    └─────────┘
```

Le flux est unidirectionnel : la balance comptable arrive dans Oracle, Power Query la transforme, le modèle relationnel l'organise en schéma en étoile, les mesures DAX calculent les indicateurs, et les visuels les affichent.

---

## 2. Base de données Oracle

### 2.1 — Connexion

| Paramètre | Valeur (mock) |
|---|---|
| SGBD | Oracle Database XE 11.2 |
| Hôte | localhost:1521/xe |
| Utilisateur | pnl_stage |
| Mode d'accès | lecture (le dashboard ne fait que lire) |

En production, seule la chaîne de connexion change (voir §7, paramètres de bascule).

### 2.2 — Schéma (11 tables)

| Table | Rôle |
|---|---|
| `FACT_BALANCE` | Table de faits — chaque ligne = un mouvement comptable (mois, compte, CDR, offre, BU, segment, montant) |
| `DIM_COMPTE` | Référentiel des comptes comptables et leur mapping P&L |
| `DIM_BU` | Business Units |
| `DIM_CDR` | Centres de Responsabilité (rattachés à une BU) |
| `DIM_OFFRE` | Offres commerciales (segment, techno) |
| `DIM_DATE` | Dimension calendaire |
| `DIM_STRUCTURE_PL` | Hiérarchie du waterfall P&L |
| `CLE_EQUIPEMENT` | Clés de ventilation S4 (Équipement) |
| `CLE_INCOMING` | Clés de ventilation S5 (Interconnexion) |
| `DIM_REJET` | Exceptions de mapping (triplets Compte+Offre+CDR → ligne P&L) |
| `DIM_CAPEX` / `DIM_NEW_DIGITAL` | Tables de paramétrage complémentaires |

### 2.3 — Script de peuplement

Le script `03_populate_oracle_v4.py` génère les données mock. Points clés :
- Mode THICK obligatoire : `oracledb.init_oracle_client(lib_dir=...)`
- Idempotent : vide les tables avant réinsertion
- ~9 900 lignes dans FACT_BALANCE
- Convention de signe : **revenus stockés en négatif** (classe 7), coûts en positif

---

## 3. Modèle Power BI (schéma en étoile)

### 3.1 — Table de faits

`Fact_Balance` — reliée à toutes les dimensions par des relations plusieurs-à-un.

### 3.2 — Dimensions et relations

| Dimension | Clé de liaison |
|---|---|
| Dim_Compte | COMPTE_COMPTABLE |
| Dim_BU | BU_CODE |
| Dim_CDR | CDR_CODE |
| Dim_Offre | OFFRE_CODE |
| Dim_Date | Date ↔ MOIS |

`Dim_Date` est générée en DAX via `CALENDAR()` (≈ 730 lignes couvrant 2025-2026).

### 3.3 — Tables de paramétrage (non reliées directement)

`Cle_Equipement` et `Cle_Incoming` sont interrogées par `LOOKUPVALUE` dans les mesures, pas par relation. `Dim_Rejet` est utilisée dans Power Query (fusion), pas dans le modèle.

---

## 4. Logique métier implémentée

### 4.1 — Les trois types de splits B2B/B2C

| Type | Cas d'usage | Mécanisme |
|---|---|---|
| **Type I** | Offre identifiable | Affectation directe au segment de l'offre |
| **Type II** | Montant global (gratuités) | Ratio dynamique = Brut B2B / Brut Total du mois |
| **Type III** | Équipement, Incoming | LOOKUPVALUE dans les tables de clés S4/S5 |

### 4.2 — Module VAS (Services + Apigee séparés)

Deux catégories distinctes, chacune avec son bloc de comptes :
- **VAS Services** : revenus 705100, coûts 604100
- **VAS Apigee** : revenus 705557, coûts 604450

Pour chaque catégorie : Revenue, Cost, Net, clé de répartition dynamique (B2B/B2C/Wholesale), réallocation proportionnelle des coûts, et check à 0.

Formule du VAS Net : `Σ(705) − Σ(709 remises) − Σ(604 coûts)`.

### 4.3 — Les cinq check lines

`Check Rev`, `Check Opex`, `Check Cos`, `Check VAS Services`, `Check VAS Apigee` — tous doivent être à 0. Ils réconcilient le P&L reconstitué avec la somme des comptes de la balance. `Statut Checks` agrège le tout en un indicateur vert/rouge.

### 4.4 — Table Rejet (exceptions de mapping)

Implémentée en Power Query :
1. Colonne composite `Cle_Composite` = COMPTE + OFFRE + CDR dans `Fact_Balance`
2. Fusion (jointure externe gauche) avec `Dim_Rejet` sur cette clé
3. Développement de la colonne `PL_LINE` du Rejet **avec préfixe** → `Dim_Rejet.PL_LINE`
4. Colonne conditionnelle `PL_LINE_Final` : si une exception existe, elle prime ; sinon on garde le mapping standard

```
PL_LINE_Final =
if [Dim_Rejet.PL_LINE] <> null then [Dim_Rejet.PL_LINE] else [PL_LINE]
```

**Point de vigilance critique** : lors du développement de la colonne fusionnée, **conserver le préfixe** (`Dim_Rejet.PL_LINE`). Le décocher crée un conflit de nommage `PL_LINE` vs `PL_LINE.1` qui casse la colonne conditionnelle et, en cascade, toutes les requêtes dépendantes.

**Pour que le Rejet soit visible** : les visuels doivent afficher `PL_LINE_Final`, pas `PL_LINE`. Si un visuel utilise encore `PL_LINE`, le Rejet est calculé mais sans effet à l'écran.

---

## 5. Points de vigilance DAX (leçons des sprints)

Ces règles ont été établies au prix de plusieurs bugs. À respecter impérativement.

| Règle | Pourquoi |
|---|---|
| Revenus stockés en négatif → mesures avec `× -1` | Convention classe 7 |
| Clés S4/S5 stockées au 1er du mois → `MIN(Dim_Date[Date])`, jamais `MAX` | `MAX` renvoie le dernier jour du mois → le lookup échoue |
| Filtres `IN {...}` dans CALCULATE → encapsuler dans `KEEPFILTERS` | Sinon le filtre remplace le contexte de ligne au lieu de s'y ajouter |
| `REMOVEFILTERS(colonne)` ≠ `ALL(table)` | Le premier garde le contexte temporel ; le second efface tout |
| Mesures VAS : **calcul direct** `SUM × -1`, PAS `[Total Revenue]` imbriqué | Deux filtres CALCULATE imbriqués interfèrent et faussent le résultat |
| 3 segments (B2B/B2C/Wholesale) → jamais `1 - B2B` | Le Wholesale existe ; les checks doivent inclure les 3 termes |
| `Total OPEX` exclut Depreciation/Amortization | Le D&A se soustrait APRÈS l'EBITDA, pas dedans (sinon compté 2×) |

---

## 6. Structure des mesures (~70)

Regroupées par domaine (organisation en dossiers d'affichage recommandée) :

- **Waterfall** : Total Revenue, Total COS, Gross Margin, Total OPEX, EBITDA, Net Profit
- **Time Intelligence** : Croissance MoM %, YoY %, Revenue YTD
- **Splits B2B/B2C** : Revenue B2B/B2C, clés dynamiques, gratuités ventilées
- **Clés manuelles** : Ratio Équipement, Ratio Incoming (LOOKUPVALUE)
- **VAS Services** : Revenue, Cost, Net, clés, réallocation, check
- **VAS Apigee** : idem, comptes 705557/604450
- **Contrôles qualité** : les 5 checks, Statut Checks, Nb Comptes Non Mappés

---

## 7. Bascule mock → production

### 7.1 — Paramètres de bascule

Deux paramètres Power Query pilotent la source :
- `Environnement` (Mock / Prod)
- `Serveur_Oracle` (chaîne de connexion)

Changer `Serveur_Oracle` suffit à rediriger tout le modèle vers la base de production.

### 7.2 — Contournements mock à retirer/vérifier

| Élément | Statut en production |
|---|---|
| Gratuités/Remises (709) générées avec signe revenu | Se corrige seul : vrais 709 en solde débiteur, nettés automatiquement |
| Mesures VAS en calcul direct | À conserver (bonne pratique) |
| `Total OPEX` hors D&A | À conserver (calcul correct) |
| Champ Type généré par offre | En prod, vient de `MID(offre,1,1)` de la balance |
| Exceptions Rejet aléatoires | À remplacer par les 71 vraies exceptions métier |

### 7.3 — Checklist de validation post-bascule

Vérifier que les 5 checks sont à 0, que le volume de lignes est cohérent (>> 10 000), et comparer le Total Revenue d'un mois de référence avec le fichier Excel source.

---

## 8. Procédures de maintenance courante

### Ajouter une mesure
Vue Rapport → clic droit sur `_Mesures` → Nouvelle mesure → écrire le DAX → ranger dans le bon dossier d'affichage.

### Ajouter une ligne P&L
La ligne apparaît automatiquement dès qu'un compte y est mappé dans `Dim_Compte` (Oracle) et qu'elle figure dans `Dim_Structure_PL`. Actualiser.

### Ajouter une clé S4/S5
Insérer les lignes dans `Cle_Equipement` / `Cle_Incoming` (Oracle), actualiser.

---

## 9. Fichiers du projet

```
C:\PL_Stage\
    01_create_user.sql              création de l'utilisateur Oracle
    02_create_schema.sql            création des 11 tables
    03_populate_oracle_v4.py        peuplement des données mock (version courante)
    Theme_PL_Ooredoo.json           thème visuel
    PL_Dashboard_v06_Final.pbix     rapport Power BI (livrable)
    Docs\                           documents de clôture et guides
```

---

*Pour l'utilisation courante du dashboard, se référer à GUIDE_UTILISATEUR.md. Pour la traçabilité entre le cahier des charges et la réalisation, se référer à RAPPORT_CONFORMITE.md.*
