# Sprint 1 — Mise en place de la base de données Oracle mock

**Projet** : Dashboard P&L — Automatisation du reporting financier
**Encadrante** : Fida
**Stagiaire** : Ala
**Entreprise** : Tunisie Telecom
**Sprint** : 1 sur 6
**Statut** : ✅ Terminé
**Date de clôture** : Juillet 2026

---

## 1. Objectif du sprint

Mettre en place l'**infrastructure de données** du projet en construisant une base Oracle locale peuplée de données mock réalistes. Cette base servira d'environnement de développement pour toute la suite du projet (Power BI, DAX, dashboard), en attendant l'accès aux données réelles de production.

### Pourquoi cette approche

Les données de production de Tunisie Telecom sont hautement sécurisées et non accessibles au stagiaire. La solution consiste à :

1. **Reproduire la structure exacte** de la base réelle (mêmes tables, colonnes, types, relations) à partir du fichier Excel de référence fourni par l'encadrante
2. **Générer des données synthétiques réalistes** qui respectent les règles métier (saisonnalité, tendances, anomalies volontaires)
3. **Isoler la source** via des paramètres de connexion, pour que la bascule vers la production soit un simple changement de chaîne de connexion sans modification du modèle

Cette approche garantit que tout le travail réalisé sur les données mock sera directement réutilisable sur les données réelles.

---

## 2. Rappel des objectifs stratégiques du projet

Le sprint 1 contribue aux trois objectifs stratégiques définis dans le cahier des charges :

| Objectif | Contribution du Sprint 1 |
|---|---|
| **Automatisation & Fiabilité** | Base structurée relationnelle (Oracle) remplaçant les extractions manuelles Excel. Contraintes d'intégrité référentielle en place. |
| **Vue analytique granulaire** | Modélisation en étoile avec dimensions BU et CDR séparées, permettant tous les découpages analytiques exigés. |
| **Visualisation & Pilotage** | Base prête à être branchée à Power BI en mode Import ou DirectQuery. |

---

## 3. Besoins couverts par le Sprint 1

### Besoins fonctionnels adressés

- **Enrichissement du référentiel** : la table `DIM_COMPTE` reproduit la structure du référentiel Mapping General (compte comptable → P&L Line, Catégorie, NCOA Mapping, etc.)
- **Structure du waterfall P&L** : la table `DIM_STRUCTURE_PL` modélise les niveaux hiérarchiques du reporting (Section → Sous-total → Ligne détail)
- **Fiabilisation Zéro "Null"** : 3 comptes orphelins volontairement injectés (`699000-0000`, `699001-0000`, `699002-0000`) pour tester le contrôle qualité dans les sprints suivants
- **Ratios manuels S4/S5** : tables `CLE_EQUIPEMENT` et `CLE_INCOMING` prêtes à recevoir les vraies clés de répartition mensuelles

### Besoins non-fonctionnels adressés

- **Portabilité** : mot de passe et DSN externalisés dans le script Python, permettant une bascule mock → prod en changeant uniquement les paramètres de connexion
- **Maintenabilité** : script Python idempotent (relançable sans erreur), avec vidage automatique des tables avant réinsertion
- **Traçabilité** : chaque ligne de la table de faits porte les 6 dimensions (mois, compte, CDR, offre, BU, segment), permettant une auditabilité complète
- **Sécurité** : compte utilisateur `pnl_stage` dédié au projet, distinct du compte SYSTEM administratif

---

## 4. Architecture livrée

### 4.1 — Environnement technique

| Composant | Version | Rôle |
|---|---|---|
| Oracle Database XE | 11.2 | Moteur de base de données local |
| Oracle SQL Developer | 24.3 | Client SQL pour l'administration et les requêtes |
| Oracle Instant Client | 23.x | Bibliothèque native pour connexion Python |
| Python | 3.14.5 | Génération et injection des données mock |
| oracledb (driver) | dernière | Client Python Oracle (mode thick) |
| pandas, numpy, faker | dernières | Génération de données réalistes |

### 4.2 — Schéma relationnel (11 tables)

**Table de faits**
- `FACT_BALANCE` — équivalent de la Balance Comptable mensuelle

**Dimensions principales**
- `DIM_BU` — Business Units (Mobile, Fixe, Entreprise, Digital, Wholesale)
- `DIM_CDR` — Centres de Responsabilité, rattachés à une BU
- `DIM_OFFRE` — Offres avec segment (B2B/B2C/Wholesale) et technologie
- `DIM_COMPTE` — Référentiel de mapping comptable (équivalent Mapping General)

**Dimensions du reporting**
- `DIM_STRUCTURE_PL` — Waterfall P&L (sections, sous-totaux, lignes détaillées)

**Référentiels de règles métier**
- `DIM_CAPEX` — Mapping des investissements
- `DIM_NEW_DIGITAL` — Cas particuliers Digital (lookup par clé composite Compte+Offre)
- `DIM_REJET` — Exceptions de mapping (Compte+Offre+CDR non standards)

**Clés manuelles de répartition**
- `CLE_EQUIPEMENT` — Ratios S4 : ventilation B2B/B2C pour les ventes d'équipement
- `CLE_INCOMING` — Ratios S5 : ventilation B2B/B2C pour les revenus d'interconnexion

### 4.3 — Relations d'intégrité

Toutes les clés étrangères sont posées sur `FACT_BALANCE` :

```
FACT_BALANCE.compte_comptable → DIM_COMPTE.compte_comptable
FACT_BALANCE.cdr_code         → DIM_CDR.cdr_code
FACT_BALANCE.offre_code       → DIM_OFFRE.offre_code
FACT_BALANCE.bu_code          → DIM_BU.bu_code
DIM_CDR.bu_code               → DIM_BU.bu_code
```

Ces contraintes garantissent qu'il ne peut jamais y avoir de ligne orpheline dans la table de faits.

### 4.4 — Volumétrie livrée

| Table | Lignes | Rôle |
|---|---:|---|
| DIM_BU | 5 | 5 Business Units |
| DIM_CDR | 20 | 4 CDR par BU |
| DIM_OFFRE | 30 | 30 offres avec segments et technos |
| DIM_COMPTE | 47 | 44 comptes mappés + 3 comptes orphelins de test |
| DIM_STRUCTURE_PL | 68 | Structure du waterfall reporting |
| CLE_EQUIPEMENT | 48 | 24 mois × 2 segments |
| CLE_INCOMING | 240 | 24 mois × 5 catégories × 2 segments |
| **FACT_BALANCE** | **9 768** | **24 mois de balance mock** |
| DIM_REJET, DIM_CAPEX, DIM_NEW_DIGITAL | 0 | Prêtes à recevoir les vraies données |

---

## 5. Règles métier injectées dans les données mock

Pour que les futurs visuels Power BI ressemblent à une vraie situation d'entreprise et non à du bruit aléatoire, les règles suivantes ont été appliquées :

### 5.1 — Saisonnalité réaliste

- **Pic estival Voice/Roaming** (juin-août) : +40% sur les revenus Outgoing International et Roaming, cohérent avec la saison touristique tunisienne
- **Pic Équipement en décembre** : +60% sur les ventes de Box 3G/4G/5G, cohérent avec les fêtes de fin d'année
- **Pic VAS en fin d'année** (novembre-décembre) : +20% sur les services digitaux

### 5.2 — Tendance de croissance

Chaque compte suit une croissance mensuelle de 0 à 2% par mois, tirée aléatoirement. Sur 24 mois, cela génère des variations YoY (Year-on-Year) réalistes de l'ordre de +10 à +15%, comparable à un opérateur télécom mature en croissance modérée.

### 5.3 — Bruit et anomalies volontaires

- **Bruit gaussien** de ±8% autour de la tendance, pour éviter des courbes trop lisses
- **Pics exceptionnels** (~1,5% des lignes) multipliés par 2,5x à 4x, pour simuler des événements ponctuels détectables
- **CDR manquants** (~1% des lignes), pour simuler des imperfections de saisie ERP réalistes
- **3 comptes non mappés** (`Catégorie = "Null"`) pour tester concrètement le contrôle Zéro Null du cahier des charges

### 5.4 — Convention de signe respectée

Comme dans la vraie balance comptable :
- Les **revenus (classe 7)** sont stockés en **négatif**
- Les **charges (classe 6)** sont stockées en **positif**

Cette convention sera compensée lors du calcul des mesures DAX (multiplication par -1 sur les revenus).

---

## 6. Livrables du Sprint 1

| Fichier | Rôle | Localisation |
|---|---|---|
| `01_create_user.sql` | Création de l'utilisateur Oracle `pnl_stage` | `C:\PL_stage\` |
| `02_create_schema.sql` | DDL des 11 tables avec types, clés, index | `C:\PL_stage\` |
| `03_populate_oracle.py` | Script de génération et peuplement des données mock | `C:\PL_stage\` |
| `README_Sprint1.md` | Guide d'exécution pas à pas | `C:\PL_stage\` |
| `Sprint1_Cloture.md` | Ce document (bilan du sprint) | `C:\PL_stage\Docs\` |

### Compte utilisateur créé

- **Utilisateur** : `pnl_stage`
- **Mot de passe** : `pnl_stage_2026`
- **Tablespace** : `USERS`
- **Droits** : `CONNECT`, `RESOURCE`, `CREATE VIEW`, `CREATE SESSION`, `CREATE TABLE`, `CREATE SEQUENCE`

### Connexion SQL Developer

- **Nom** : `PNL_STAGE_USER`
- **Hostname** : `localhost`
- **Port** : `1521`
- **SID** : `xe`

---

## 7. Validation du sprint — Tests exécutés

Quatre requêtes SQL de contrôle qualité ont été exécutées avec succès sur la base peuplée :

### Test 1 — Volume par mois (distribution uniforme)

```sql
SELECT TO_CHAR(mois, 'YYYY-MM') AS mois, COUNT(*) AS nb_lignes
FROM fact_balance GROUP BY TO_CHAR(mois, 'YYYY-MM') ORDER BY mois;
```

**Résultat** : 24 mois × 407 lignes/mois = 9 768 lignes ✅

### Test 2 — Saisonnalité vérifiée

Le revenu mensuel affiche bien les pics attendus :
- Août 2025 : 24 825 k'TND (pic tourisme)
- Décembre 2026 : 30 403 k'TND (pic Noël + fin de croissance)
- Croissance 2025→2026 : ~+12% en glissement annuel ✅

### Test 3 — Zéro Null : les 3 comptes orphelins sont détectés

```
699000-0000  Compte non mappe (a corriger)  Null
699001-0000  Compte non mappe (a corriger)  Null
699002-0000  Compte non mappe (a corriger)  Null
```

Prêts à être utilisés pour la page de contrôle qualité au Sprint 5 ✅

### Test 4 — Répartition des revenus par BU (réalisme métier)

| BU | Revenu k'TND | % du CA |
|---|---:|---:|
| Mobile Services | 267 030 | 45% |
| Wholesale / Interco | 127 361 | 21% |
| Digital & VAS | 108 999 | 18% |
| Fixed Services | 62 565 | 11% |
| Enterprise Solutions | 32 806 | 5% |
| **Total** | **598 760** | **100%** |

Cette structure correspond exactement à celle d'un opérateur télécom mature ✅

---

## 8. Difficultés rencontrées et solutions apportées

### 8.1 — Incompatibilité de syntaxe Oracle 12c dans XE 11.2

**Symptôme** : erreur `ORA-02000: missing ( keyword` lors de la création de `FACT_BALANCE` avec la clause `GENERATED ALWAYS AS IDENTITY`.

**Cause** : cette syntaxe existe depuis Oracle 12c (2013), mais XE 11.2 est de 2011.

**Solution** : utilisation de l'ancienne méthode Oracle basée sur `SEQUENCE + TRIGGER BEFORE INSERT`, équivalent fonctionnel de IDENTITY.

### 8.2 — Driver Python `oracledb` incompatible en mode thin

**Symptôme** : erreur `DPY-3010: connections to this database server version are not supported by python-oracledb in thin mode`.

**Cause** : le mode thin (pur Python) du driver `oracledb` ne supporte que les versions Oracle ≥ 12.1.

**Solution** : installation d'Oracle Instant Client 23.x et activation du mode thick via `oracledb.init_oracle_client(lib_dir=...)` dans le script Python. Cette même bibliothèque sera aussi nécessaire pour la connexion Power BI du Sprint 2.

### 8.3 — Confusion entre "connexion SQL Developer" et "utilisateur Oracle"

**Symptôme** : ambiguïté sur ce que représente le nom `PNL_STAGE` dans SQL Developer.

**Clarification** : une **connexion** dans SQL Developer est un raccourci nommé ; l'**utilisateur** `pnl_stage` est le compte réel dans la base Oracle. Deux connexions ont donc été créées : une pour SYSTEM (administration) et une pour `pnl_stage` (travail au quotidien).

---

## 9. Points de contrôle finaux

| Point de contrôle | Statut |
|---|---|
| Oracle XE 11.2 accessible sur `localhost:1521/xe` | ✅ |
| Utilisateur `pnl_stage` créé avec droits appropriés | ✅ |
| 11 tables créées avec types, PK, FK, index | ✅ |
| Aucune erreur au peuplement Python | ✅ |
| FACT_BALANCE contient 9 768 lignes | ✅ |
| Distribution mensuelle uniforme (407 lignes × 24 mois) | ✅ |
| Saisonnalité et tendance visibles dans les revenus | ✅ |
| 3 comptes orphelins détectables pour tests Zéro Null | ✅ |
| Répartition BU réaliste (Mobile ~45%, Wholesale ~21%, etc.) | ✅ |
| Script Python idempotent (relançable sans erreur) | ✅ |

---

## 10. Ouverture vers le Sprint 2

Le Sprint 2 s'appuiera directement sur cette base pour :

1. Connecter Power BI Desktop à Oracle XE
2. Importer les 11 tables via Power Query
3. Établir les relations du schéma en étoile
4. Créer la table calendrier `Dim_Date` en DAX
5. Mettre en place le paramètre `Serveur_Oracle` pour la bascule Mock/Prod
6. Créer les 3 premières mesures DAX de validation (Total Revenue, Total COS, Total OPEX)

**Objectif de validation du Sprint 2** : la mesure `Total Revenue (k'TND)` dans Power BI doit afficher **598 760**, valeur identique à celle obtenue par requête SQL directe sur la base.

---

## Annexe — Commandes clés pour reproduire le Sprint 1

```bash
# Installer les dépendances Python
pip install oracledb pandas numpy faker

# Peupler la base (après avoir exécuté 01 et 02 en SQL Developer)
cd C:\PL_stage
python 03_populate_oracle.py
```

```sql
-- Vérifier que tout est en place
SELECT table_name FROM user_tables ORDER BY table_name;
SELECT COUNT(*) FROM fact_balance;
```
