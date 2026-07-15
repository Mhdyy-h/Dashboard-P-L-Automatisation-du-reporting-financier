# Sprint 3 — Mesures DAX et logique métier du waterfall P&L

**Projet** : Dashboard P&L — Automatisation du reporting financier
**Encadrante** : Fida
**Stagiaire** : Ala
**Entreprise** : Tunisie Telecom
**Sprint** : 3 sur 6
**Statut** : ✅ Terminé
**Prérequis** : Sprint 2 clôturé (modèle Power BI connecté, 3 mesures de base)

---

## 1. Objectif du sprint

Traduire toute la **logique métier du waterfall P&L de l'Excel de référence** en mesures DAX exploitables dans Power BI. Le Sprint 3 transforme un modèle de données brut en un moteur de calcul financier complet, capable de reproduire à l'identique les indicateurs du reporting actuel de Tunisie Telecom.

### Livrables clés

1. Environ **45 mesures DAX** organisées en 5 catégories couvrant tout le waterfall
2. Un **calibrage réaliste des données mock** aligné sur les ratios sectoriels télécom
3. Une **matrice de validation croisée** prouvant la cohérence bout-en-bout (Oracle → Power BI → DAX)
4. Les **check lines de fiabilité** implémentées (contrôle Zéro Null, écarts de réconciliation)

---

## 2. Rappel des objectifs stratégiques du projet

Le Sprint 3 contribue directement aux trois objectifs stratégiques :

| Objectif | Contribution du Sprint 3 |
|---|---|
| **Automatisation & Fiabilité** | Toutes les formules Excel du waterfall sont désormais reproduites en DAX. Les check lines vérifient automatiquement la cohérence entre la balance et le P&L calculé. |
| **Vue analytique granulaire** | Les mesures peuvent être filtrées dynamiquement par BU, CDR, segment, offre, techno — sans requérir de nouvelle formule pour chaque combinaison. |
| **Visualisation & Pilotage** | Les mesures Time Intelligence (MoM, YoY, YTD) permettent une analyse de tendance immédiate et le pilotage de la performance dans le temps. |

---

## 3. Besoins couverts par le Sprint 3

### Besoins fonctionnels adressés

- **Automatisation des splits** : mesures Revenue par segment B2B/B2C/Wholesale, prêtes à évoluer avec la logique Types I/II/III des Sprints suivants
- **Enrichissement du référentiel** : calculs qui exploitent toutes les colonnes de mapping (Catégorie, PL_Line, Segment)
- **Fiabilisation Zéro Null** : mesures dédiées de contrôle qualité (Nb Comptes Non Mappés, Statut Fiabilité)
- **Drill-down du consolidé au transactionnel** : mesures agrégées qui gardent le contexte de filtre pour permettre le drill-down naturel dans Power BI

### Besoins non-fonctionnels adressés

- **Fiabilité** : réconciliation Balance ↔ P&L via la mesure `Écart Check Revenue` qui tend vers zéro
- **Performance** : réutilisation des mesures existantes entre crochets `[...]` plutôt que réécriture de `CALCULATE(SUM(...))` — le moteur DAX optimise les calculs partagés
- **Maintenabilité** : convention de nommage cohérente (`[Catégorie] [Précision] (unité)`) — exemple : `Gross Margin B2B (k'TND)`
- **Traçabilité** : chaque mesure agrégée peut être décomposée en cliquant sur la valeur (drill-through natif Power BI)

---

## 4. Architecture livrée

### 4.1 — Organisation des mesures dans `_Mesures`

Toutes les mesures sont regroupées dans la table dédiée `_Mesures` (préfixée d'un underscore pour apparaître en tête de la liste). Le total atteint environ **45 mesures**, organisées en 5 catégories.

### 4.2 — Catégorie 1 : Mesures agrégées du waterfall (10)

Reproduisent la structure verticale du reporting Excel : Revenue → COS → Gross Margin → OPEX → EBITDA → D&A → Net Profit.

- `Total Revenue (k'TND)`
- `Total COS (k'TND)`
- `Total OPEX (k'TND)`
- `Total D&A (k'TND)` — filtre sur les libellés Depreciation et Amortization
- `Gross Margin (k'TND)` = Revenue − COS
- `Gross Margin %` = Gross Margin ÷ Revenue
- `EBITDA (k'TND)` = Gross Margin − OPEX
- `EBITDA %` = EBITDA ÷ Revenue
- `Net Profit (k'TND)` = EBITDA − D&A
- `Net Profit %` = Net Profit ÷ Revenue

**Principe DAX** : réutilisation des mesures entre crochets pour créer une chaîne de calcul propre et rapide. Modifier `Total Revenue` propage automatiquement le changement à toutes les mesures dérivées.

### 4.3 — Catégorie 2 : Time Intelligence (6)

Permettent l'analyse de tendance et la comparaison de périodes.

- `Revenue Mois Précédent (k'TND)` — via `DATEADD(-1, MONTH)`
- `Croissance MoM %` — variation par rapport au mois précédent
- `Revenue Année Précédente (k'TND)` — via `SAMEPERIODLASTYEAR`
- `Croissance YoY %` — variation par rapport à l'année précédente
- `Revenue YTD (k'TND)` — cumul depuis le 1er janvier
- `Revenue Moyenne Mobile 3M (k'TND)` — lissage sur 3 mois glissants

**Point d'attention** : les mesures YoY affichent 0% pour l'année 2025 (aucune donnée de 2024 pour comparaison). Ce comportement est correct et attendu.

### 4.4 — Catégorie 3 : Ventilation par segment (12)

Permettent le découpage B2B / B2C / Wholesale à tous les niveaux du waterfall.

- Revenue par segment : `Revenue B2B`, `Revenue B2C`, `Revenue Wholesale`
- Pourcentages de mix : `% Revenue B2B`, `% Revenue B2C`, `% Revenue Wholesale`
- Gross Margin par segment : `Gross Margin B2B`, `Gross Margin B2C`, `Gross Margin Wholesale`
- EBITDA par segment : `EBITDA B2B`, `EBITDA B2C`, `EBITDA Wholesale`

**Point technique documenté** : dans les données mock, les comptes COS et OPEX n'ont pas de segment attribué (contrairement aux revenus). Par conséquent, les Gross Margin et EBITDA par segment sont dans les faits égaux aux Revenue par segment (pas de déduction de charges segmentées). Ce comportement changera automatiquement lors du branchement sur les données réelles où les charges seront segmentées via les règles Types I/II/III.

### 4.5 — Catégorie 4 : VAS Net et BU (10)

Mesures pour l'analyse par Business Unit et la logique VAS spécifique.

Mesures VAS :
- `VAS Revenue (k'TND)` — filtre sur les libellés VAS Revenue, VAS Services Revenue, VAS Apigee Revenue
- `VAS Cost (k'TND)` — filtre sur VAS COST, VAS Services Cost, VAS Apigee Cost, Digital CoS
- `VAS Net (k'TND)` = VAS Revenue − VAS Cost
- `VAS Net %`

Mesures par BU (préparent les visuels du Sprint 4) :
- `Revenue Mobile (k'TND)`
- `Revenue Fixed (k'TND)`
- `Revenue Digital (k'TND)`
- `Revenue Enterprise (k'TND)`
- `Revenue Wholesale BU (k'TND)`

### 4.6 — Catégorie 5 : Contrôles qualité et check lines (7)

Ces mesures sont le socle de la démonstration de fiabilité de la solution.

- `Nb Lignes CDR Manquant` — compte les lignes sans CDR (~92 attendues, ~1% des 9 768)
- `Nb Comptes Non Mappés` — comptes distincts en catégorie Null ou sans PL_LINE (attendu : 3)
- `Statut Fiabilité` — indicateur global "✅ OK" / "⚠ À vérifier"
- `Somme Classe 7 (k'TND)` — total des comptes commençant par "7" (classe revenus)
- `Écart Check Revenue (k'TND)` — différence Total Revenue vs Somme Classe 7 (doit tendre vers 0)
- `Nb Comptes Distincts` — nombre de comptes mouvementés dans la période
- `% Comptes Mappés` — ratio de complétude du mapping

Ces mesures alimenteront la **Page 3 "Contrôle qualité"** du dashboard au Sprint 5.

---

## 5. Recalibrage des données mock (v2)

### 5.1 — Problème identifié à mi-parcours du sprint

Après la création des mesures agrégées (étape 3.1), les KPI de validation ont révélé une anomalie structurelle :

| Mesure | Valeur v1 | Situation |
|---|---:|---|
| EBITDA | -186,13K | ❌ Négatif |
| EBITDA % | -31,09% | ❌ Impossible |
| Net Profit | -252,48K | ❌ Négatif |
| Net Profit % | -42,17% | ❌ Impossible |

**Cause identifiée** : dans le script Python du Sprint 1, tous les comptes (Revenue, COS, OPEX) utilisaient la même plage de montants aléatoires `uniform(80K, 500K)`. Résultat : les charges dépassaient les revenus (142% du CA), rendant l'EBITDA structurellement négatif.

**Ce n'était pas un bug DAX** — les formules calculaient correctement. Le problème venait de la **calibration** des données mock.

### 5.2 — Solution apportée : script `03_populate_oracle_v2.py`

Une fonction `get_amount_range()` a été introduite pour attribuer des plages de montants adaptées à chaque catégorie :

| Catégorie | Plage min-max | Ratio cible du CA |
|---|---|---:|
| Revenue | 80K - 500K | 100% |
| COS | 50K - 320K | ~40% |
| OPEX (hors D&A) | 30K - 250K | ~30% |
| D&A (Depreciation, Amortization) | 200K - 500K | ~13% |

Ces ratios reproduisent la structure financière typique d'un opérateur télécom mature.

### 5.3 — Résultats après recalibrage

| Mesure | v1 | **v2** | % du CA |
|---|---:|---:|---:|
| Total Revenue | 598,76K | **598,76K** | 100% |
| Total COS | 422,05K | **269,43K** | 45% |
| Total OPEX | 362,84K | **220,91K** | 37% |
| Total D&A | 66,34K | **80,09K** | 13% |
| Gross Margin | 176,71K | **329,33K** | 55% |
| **EBITDA** | -186,13K ❌ | **108,42K ✅** | 18% |
| **Net Profit** | -252,48K ❌ | **28,33K ✅** | 4,7% |

**Verdict** : les nouveaux KPI sont réalistes et défendables devant un décideur métier.

---

## 6. Validation croisée finale (étape 3.6)

### 6.1 — Test de validation par matrice

Une matrice a été construite pour comparer les valeurs Power BI avec les totaux SQL du Sprint 1 :

- **Lignes** : les 19 catégories P&L présentes dans FACT_BALANCE
- **Colonnes** : les 24 mois de la période (2025-01 à 2026-12)
- **Valeurs** : Total Revenue (k'TND)

### 6.2 — Résultats de validation

**Total général de la matrice** : 598 759,89 k'TND
**Total de la carte KPI Power BI** : 598,76K (soit 598 760)
**Total du test SQL Sprint 1** : 598 760

**Écart : 0%** ✅

Cette égalité valide **l'ensemble de la chaîne** :
1. La connexion Oracle → Power BI est fidèle
2. L'import des 9 768 lignes n'a rien perdu
3. Les types de colonnes sont préservés (le NUMBER(18,3) Oracle devient bien un Decimal Power BI)
4. Les mesures DAX reproduisent la logique métier au dinar près
5. Le contexte de filtre fonctionne correctement (matrice avec 2 axes de filtre : PL_LINE + Mois)

### 6.3 — Observations métier confirmées

La matrice révèle plusieurs comportements que le dashboard mettra en valeur :

- **Saisonnalité touristique visible** : Outgoing International monte à 1 355 en juillet 2026 et 1 580 en août 2026, contre 924 en avril
- **Pic Équipement de fin d'année** : décembre 2026 affiche 30 403 k'TND au total (contre 27 000-28 000 les mois précédents)
- **Croissance progressive** : le total mensuel passe de 24 435 en novembre 2025 à 30 403 en décembre 2026 (+24%)
- **Croissance YoY validée** : entre 13% et 23% selon les mois, cohérent avec la simulation

---

## 7. Points de contrôle finaux

| Point de contrôle | Statut |
|---|---|
| Environ 45 mesures créées dans `_Mesures` | ✅ |
| Total Revenue affiche 598,76K (identique SQL) | ✅ |
| Gross Margin positif (329,33K, 55%) | ✅ |
| EBITDA positif (108,42K, 18%) | ✅ |
| Net Profit positif (28,33K, 4,7%) | ✅ |
| Croissance MoM cohérente (0-9%) | ✅ |
| Croissance YoY 2026 cohérente (13-23%) | ✅ |
| Somme B2B+B2C+Wholesale = Total Revenue (aux Null près) | ✅ |
| Nb Comptes Non Mappés = 3 | ✅ |
| Nb Lignes CDR Manquant ≈ 92 (~1%) | ✅ |
| Écart Check Revenue ≈ 0 | ✅ |
| Statut Fiabilité affiche "⚠ À vérifier" | ✅ (comportement voulu) |
| Matrice de validation Revenue = 598 759,89 | ✅ |
| Fichier PL_Dashboard_v02.pbix sauvegardé | ✅ |

---

## 8. Difficultés rencontrées et solutions apportées

### 8.1 — Erreur DPY-3010 sur le driver Python (identique Sprint 1)

**Symptôme** : au relancement du script v2, réapparition de l'erreur `DPY-3010: connections to this database server version are not supported by python-oracledb in thin mode`.

**Cause** : le script v2 avait été généré comme copie de la v1 initiale, sans intégrer la correction du mode thick.

**Solution** : ajout manuel de la ligne `oracledb.init_oracle_client(lib_dir=r"C:\oracle\instantclient\instantclient_23_9")` juste après les imports.

**Leçon** : toute évolution ultérieure du script Python devra systématiquement intégrer cette ligne dans les imports.

### 8.2 — EBITDA structurellement négatif dans la v1 des données mock

**Symptôme** : après création des mesures agrégées, EBITDA à -31% du CA. Un opérateur télécom ne peut pas fonctionner avec de tels ratios.

**Diagnostic** : les charges (COS + OPEX) représentaient 142% du CA, ce qui rend l'EBITDA négatif par construction. La mécanique DAX était correcte ; c'était le générateur de données qui appliquait des amplitudes uniformes à toutes les catégories sans respecter les ratios sectoriels.

**Solution** : refonte de la fonction de génération pour appliquer des plages de montants adaptées par catégorie (voir section 5). Relancement du script v2, rafraîchissement Power BI.

**Bénéfice pédagogique** : cette difficulté a permis d'apprendre que **valider ses données mock est une étape à part entière** en BI. On ne se contente pas de "que les formules marchent", on vérifie que les valeurs sont plausibles.

### 8.3 — Croissance YoY à 0% en 2025

**Symptôme** : la mesure `Croissance YoY %` affiche 0% pour tous les mois de 2025.

**Diagnostic** : les données commencent en janvier 2025. Il n'existe aucune donnée en 2024, donc `SAMEPERIODLASTYEAR` renvoie vide, et `DIVIDE(x, blank, 0)` retourne 0.

**Décision** : ne pas modifier la logique. Ce comportement est **mathématiquement correct**. Les mois de 2026 affichent bien des YoY entre 13% et 23%, ce qui prouve que la mesure fonctionne. Une note explicative sera ajoutée à la page dashboard concernée au Sprint 5.

### 8.4 — Gross Margin B2B ≠ Revenue B2B − COS B2B

**Symptôme** : la somme des Gross Margin B2B + B2C + Wholesale (598,76K) est égale au Total Revenue plutôt qu'à la Gross Margin totale (329,33K).

**Diagnostic** : dans les données mock, seuls les comptes de revenus ont un segment attribué. Les COS et OPEX ont `SEGMENT = NULL`. Par conséquent, `CALCULATE(COS, SEGMENT="B2B")` retourne 0, et `Gross Margin B2B = Revenue B2B − 0 = Revenue B2B`.

**Décision** : documenter mais ne pas corriger. En production, les COS/OPEX seront segmentés via les règles Types I/II/III (splits dynamiques du sprint 4). Les formules DAX sont extensibles : elles fonctionneront immédiatement dès que les données réelles arriveront.

---

## 9. Bonnes pratiques mises en œuvre

### 9.1 — Réutilisation des mesures existantes

Toutes les mesures composites (Gross Margin, EBITDA, Net Profit, Gross Margin B2B...) réutilisent les mesures de base entre crochets, plutôt que de réécrire `CALCULATE(SUM(...))`. Avantages :
- Code plus lisible
- Une correction dans la mesure de base se propage automatiquement
- Le moteur DAX optimise les calculs partagés (cache interne)

### 9.2 — Convention de nommage cohérente

Toutes les mesures suivent le pattern : `[Nom métier] [Segment/BU si applicable] (unité)` — exemples :
- `Revenue B2B (k'TND)`
- `Gross Margin Wholesale (k'TND)`
- `EBITDA %` (pas d'unité pour les ratios)

### 9.3 — Formatage adapté par type de mesure

Convention adoptée dans le sprint :
- Marges structurelles (Gross Margin %, EBITDA %, Net Profit %) → 2 décimales
- Taux de croissance (MoM, YoY) → 2 décimales
- Ratios de mix (% B2B, % B2C) → 1 décimale
- Ratios opérationnels (% Comptes Mappés) → 1 décimale

### 9.4 — Utilisation systématique de DIVIDE

Toutes les divisions utilisent la fonction `DIVIDE(numérateur, dénominateur, 0)` au lieu de l'opérateur `/`. Cela évite les erreurs #DIV/0 quand un dénominateur est vide (cas de la première année pour YoY, par exemple).

### 9.5 — Validation par test unitaire

Chaque mesure a été testée immédiatement après sa création, avec une carte simple. Cette pratique évite la propagation d'erreurs (impossible de savoir laquelle des 10 dernières mesures est cassée si on ne teste qu'à la fin).

---

## 10. Ouverture vers le Sprint 4

Le Sprint 4 construira le **dashboard visuel complet** en 3 pages, en s'appuyant sur les 45 mesures créées :

- **Page 1 — Vue exécutive** : cartes KPI (Revenue, Gross Margin %, EBITDA %, Net Profit %), waterfall Revenue → EBITDA, courbe de tendance MoM/YoY, treemap par BU
- **Page 2 — Analyse P&L détaillée** : matrice hiérarchique avec drill-down (comme celle de validation, enrichie), slicers BU/CDR/Segment/Techno/Offre
- **Page 3 — Contrôle qualité "Zéro Null"** : liste des comptes orphelins, indicateurs de fiabilité, écarts de réconciliation

**Objectif de validation du Sprint 4** : présentation d'un dashboard interactif complet, avec une navigation fluide entre les 3 pages et des filtres cohérents.

---

## Annexe A — Emplacements des livrables

```
C:\PL_Stage\
    01_create_user.sql
    02_create_schema.sql
    03_populate_oracle.py                ← version v1 (backup)
    03_populate_oracle_v2.py             ← version v2 (calibrée) ✅ actuelle
    PL_Dashboard_v01.pbix                ← version Sprint 2 (backup)
    PL_Dashboard_v02.pbix                ← version Sprint 3 ✅ actuelle
    Docs\
        README_Sprint1.md
        Sprint1_Cloture.md
        Sprint2_Guide.md
        Sprint2_Cloture.md
        Sprint3_Guide.md
        Sprint3_Cloture.md               ← ce document
```

---

## Annexe B — Répartition des 45 mesures créées

| Catégorie | Nombre | Progression |
|---|---:|---|
| Waterfall agrégé | 10 | ██████████ |
| Time Intelligence | 6 | ██████ |
| Ventilation B2B/B2C | 12 | ████████████ |
| VAS & BU | 10 | ██████████ |
| Contrôles qualité | 7 | ███████ |
| **Total** | **45** | |

**Cible initiale** : ~35 mesures
**Réalisé** : ~45 mesures
**Dépassement** : +30% (mesures bonus pour la ventilation par segment)
