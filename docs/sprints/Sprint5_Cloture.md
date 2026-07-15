# Sprint 5 — Règles métier avancées : splits dynamiques, clés manuelles, VAS et contrôles

**Projet** : Dashboard P&L — Automatisation du reporting financier
**Encadrante** : Fida
**Stagiaire** : Ala
**Entreprise** : Tunisie Telecom
**Sprint** : 5 sur 6
**Statut** : ✅ Terminé
**Prérequis** : Sprint 4 clôturé (dashboard 3 pages fonctionnel)

---

## 1. Objectif du sprint

Implémenter la **véritable complexité métier** du fichier Excel de référence : les trois mécanismes de ventilation B2B/B2C, la réallocation proportionnelle des coûts VAS, et les contrôles d'intégrité comptable.

Ce sprint transforme un dashboard démonstratif en une solution qui reproduit fidèlement la logique de production.

### Livrables clés

1. Les **trois types de splits** (I, II, III) implémentés et validés
2. Le **module VAS** avec réallocation proportionnelle des coûts
3. Les **quatre check lines** d'intégrité comptable
4. Un **script de données enrichi** (v3) permettant de tester ces mécanismes
5. Le fichier `PL_Dashboard_v04.pbix`

---

## 2. Rappel du besoin fonctionnel adressé

Le cahier des charges définit le besoin n°2 :

> *« Automatisation des Splits (Revenus & VAS) : La ventilation entre B2B et B2C ne peut pas être manuelle. Le système doit être capable d'appliquer trois logiques de répartition distinctes. »*

Ce sprint répond intégralement à ce besoin.

---

## 3. Les trois types de splits — Architecture implémentée

### 3.1 — Le problème métier

Dans la balance comptable, tous les revenus ne sont pas identifiables par segment :

| Cas | Exemple | Solution |
|---|---|---|
| Le code offre est connu | Offre « Business Pro 5G » taguée B2B | **Type I** — affectation directe |
| Montant enregistré globalement | Gratuités et crédit perdu | **Type II** — ratio dynamique |
| Pas de code offre exploitable | Équipement, Interconnexion entrante | **Type III** — clés manuelles |

### 3.2 — Type I : Affectation directe

**Mécanisme** : si le code offre est identifiable dans le référentiel, 100 % du montant est affecté au segment correspondant.

**Implémentation** (héritée du Sprint 3) :

```dax
Revenue B2B (k'TND) =
CALCULATE (
    [Total Revenue (k'TND)],
    Fact_Balance[SEGMENT] = "B2B"
)
```

**Statut** : ✅ Opérationnel depuis le Sprint 3.

### 3.3 — Type II : Ratio dynamique mensuel

**Mécanisme** : pour les montants enregistrés globalement (les gratuités), on calcule chaque mois une clé de répartition à partir des revenus identifiables, puis on l'applique.

**Formule métier** (issue du fichier Excel, feuille Split Revenue) :

```
Clé B2B = Brut B2B identifié du mois / Brut Total identifié du mois
Gratuité B2B = Gratuité totale du mois × Clé B2B
```

**Implémentation DAX** :

```dax
Base Outgoing (k'TND) =
CALCULATE (
    [Total Revenue (k'TND)],
    Fact_Balance[PL_LINE] IN {
        "Outgoing National Onnet",
        "Outgoing National Offnet"
    }
)
```

```dax
Clé B2B Dynamique =
VAR BrutB2B =
    CALCULATE (
        [Base Outgoing (k'TND)],
        Fact_Balance[SEGMENT] = "B2B"
    )
VAR BrutIdentifie =
    CALCULATE (
        [Base Outgoing (k'TND)],
        REMOVEFILTERS ( Fact_Balance[SEGMENT] ),
        NOT ISBLANK ( Fact_Balance[SEGMENT] )
    )
RETURN
    DIVIDE ( BrutB2B, BrutIdentifie, 0 )
```

**Le point technique clé** : l'usage de `REMOVEFILTERS(Fact_Balance[SEGMENT])` plutôt que `ALL(Fact_Balance)`.

- `ALL(table)` effacerait **tous** les filtres, y compris le mois → le ratio deviendrait constant sur toute la période
- `REMOVEFILTERS(table[colonne])` n'efface **que** le filtre segment → le mois est conservé, le ratio reste dynamique

**Résultats de validation** :

| Mois | Clé B2B | Clé B2C | Gratuités Totales | Gratuités B2B | Gratuités B2C |
|---|---:|---:|---:|---:|---:|
| 2025-01 | 8,40 % | 81,54 % | 532,24 | 44,70 | 434,00 |
| 2025-08 | 36,39 % | 60,18 % | 591,55 | 215,25 | 356,00 |
| 2026-02 | 30,43 % | 62,96 % | 641,63 | 195,25 | 403,95 |
| **Total** | **18,49 %** | **71,57 %** | **16 487,19** | **3 048,64** | **11 799,37** |

**Contrôle d'intégrité** : la mesure `Check Clés` (somme des trois clés B2B + B2C + Wholesale) affiche **1,00 pour tous les mois** ✅

**Statut** : ✅ Validé.

### 3.4 — Type III : Clés manuelles S4 et S5

**Mécanisme** : le contrôle de gestion fournit mensuellement des tables de ratios. Le système les interroge par une jointure sur le mois.

**Formule métier** :

```
Montant B2B = Montant Total × Ratio_B2B_Manuel (lookup par mois)
```

#### Clé S4 — Équipement

Structure : `Mois × Segment → Ratio`

**Implémentation DAX** :

```dax
Ratio Équipement B2B =
LOOKUPVALUE (
    Cle_Equipement[RATIO],
    Cle_Equipement[MOIS], MIN ( Dim_Date[Date] ),
    Cle_Equipement[SEGMENT], "B2B",
    0
)
```

```dax
Revenue Équipement B2B (k'TND) =
[Revenue Équipement (k'TND)] * [Ratio Équipement B2B]
```

**Résultats de validation** :

| Mois | Ratio B2B | Revenue Équipement | Équipement B2B | Équipement B2C |
|---|---:|---:|---:|---:|
| 2025-01 | 96,71 % | 450,85 | 436,02 | 14,83 |
| 2025-04 | 98,23 % | 756,88 | 743,48 | 13,40 |
| 2026-12 | 98,20 % | 1 115,71 | 1 095,62 | 20,08 |
| **Total** | **96,71 %** | **15 116,98** | **14 619,63** | **497,35** |

**Alignement avec le fichier réel** : les ratios obtenus (96,5 % - 98,4 %) correspondent aux valeurs du fichier Excel de référence (janvier réel : 97,63 %, février : 97,21 %). L'équipement est massivement B2B, ce qui reflète la réalité du canal de distribution entreprise.

#### Clé S5 — Interconnexion entrante

Structure : `Mois × Intitulé × Segment → Ratio` (trois dimensions de lookup)

**Implémentation DAX** :

```dax
Ratio Incoming B2B =
VAR LigneCourante = SELECTEDVALUE ( Fact_Balance[PL_LINE] )
VAR Ratio =
    LOOKUPVALUE (
        Cle_Incoming[RATIO],
        Cle_Incoming[MOIS], MIN ( Dim_Date[Date] ),
        Cle_Incoming[INTITULE], LigneCourante,
        Cle_Incoming[SEGMENT], "B2B",
        0
    )
RETURN
    IF (
        LigneCourante IN {
            "Incoming National Voice",
            "Incoming National SMS/MMS",
            "Incoming International Voice"
        },
        Ratio,
        BLANK ()
    )
```

```dax
Revenue Incoming (k'TND) =
CALCULATE (
    [Total Revenue (k'TND)],
    KEEPFILTERS (
        Fact_Balance[PL_LINE] IN {
            "Incoming National Voice",
            "Incoming National SMS/MMS",
            "Incoming International Voice"
        }
    )
)
```

**Le point technique clé** : l'usage de `KEEPFILTERS`. Sans lui, `CALCULATE` remplace le contexte de ligne et affiche le total Incoming sur **toutes** les lignes de la matrice (y compris Advertising, Amortization, etc.). Avec `KEEPFILTERS`, le filtre s'ajoute au contexte existant au lieu de le remplacer.

**Résultats de validation** :

| Ligne P&L | Ratio B2B | Revenue Total | B2B | B2C |
|---|---:|---:|---:|---:|
| Incoming International Voice | 14,59 % | 12 121,36 | 1 768,51 | 10 352,85 |
| Incoming National SMS/MMS | 26,68 % | 40 323,26 | 10 758,24 | 29 565,01 |
| Incoming National Voice | 17,19 % | 25 493,43 | 4 382,32 | 21 111,11 |

**Alignement avec le fichier réel** :

| Ligne | Cible (Excel) | Obtenu | Écart |
|---|---:|---:|---|
| Incoming International Voice | ~14,3 % | 14,59 % | < 0,3 pt ✅ |
| Incoming National SMS/MMS | ~27,2 % | 26,68 % | < 0,6 pt ✅ |
| Incoming National Voice | ~16,9 % | 17,19 % | < 0,3 pt ✅ |

**Statut** : ✅ Validé.

---

## 4. Module VAS — Réallocation proportionnelle des coûts

### 4.1 — Le problème métier

Le cahier des charges précise :

> *« L'IT doit s'assurer que l'utilisateur peut filtrer le VAS Net par segment tout en ayant la garantie que les coûts ont été réalloués proportionnellement aux revenus générés. »*

Les coûts VAS (compte 604) ne sont **pas identifiables par segment** dans la balance. Il faut donc les répartir au prorata des revenus VAS générés par chaque segment.

### 4.2 — Formule métier

```
VAS Net = Σ(Revenus 705) − Σ(Remises 709) − Σ(Coûts 604)

Clé VAS B2B = VAS Revenue B2B / VAS Revenue Total
VAS Coût B2B = VAS Coût Total × Clé VAS B2B
VAS Net B2B = VAS Revenue B2B − VAS Coût B2B
```

### 4.3 — Implémentation DAX

```dax
Clé VAS B2B =
DIVIDE ( [VAS Gross B2B (k'TND)], [VAS Gross Total (k'TND)], 0 )
```

```dax
VAS Coûts B2B (k'TND) =
[VAS Coûts 604 (k'TND)] * [Clé VAS B2B]
```

```dax
Check VAS =
[VAS Coûts B2B (k'TND)] + [VAS Coûts B2C (k'TND)] - [VAS Coûts 604 (k'TND)]
```

### 4.4 — Résultats de validation

| Mois | Clé VAS B2B | VAS Coûts 604 | VAS Coûts B2B | VAS Coûts B2C | Check VAS |
|---|---:|---:|---:|---:|---:|
| 2025-01 | 19,01 % | 791,86 | 150,53 | 641,32 | **0,00** |
| 2025-05 | 37,69 % | 715,72 | 269,78 | 445,94 | **0,00** |
| 2026-12 | 34,39 % | 847,33 | 291,37 | 555,96 | **0,00** |
| **Total** | **21,03 %** | **17 738,79** | **3 729,79** | **14 009,00** | **0,00** |

**Le `Check VAS` affiche 0,00 pour tous les mois** ✅ — la réallocation est mathématiquement exacte : la somme des coûts réalloués par segment égale exactement le coût total.

**Statut** : ✅ Validé.

---

## 5. Check lines — Contrôles d'intégrité comptable

### 5.1 — Le principe

Le fichier Excel de référence comporte quatre lignes de contrôle en tête du reporting (lignes 1 à 4) : Check Rev, Check Opex, Check Cos, Check BS. Elles vérifient que le P&L reconstitué correspond bien à la balance source.

### 5.2 — Implémentation

```dax
Check Rev (TND) =
VAR TotalRevenuePL = [Total Revenue (k'TND)] * 1000
VAR TotalClasse7 =
    CALCULATE (
        SUM ( Fact_Balance[MONTANT_TND] ) * -1,
        LEFT ( Fact_Balance[COMPTE_COMPTABLE], 1 ) = "7"
    )
RETURN
    TotalRevenuePL - TotalClasse7
```

Les mesures `Check Opex` et `Check Cos` suivent la même logique sur leurs catégories respectives.

```dax
Statut Checks =
VAR Seuil = 1
RETURN
    IF (
        ABS ( [Check Rev (TND)] ) <= Seuil
            && ABS ( [Check Opex (TND)] ) <= Seuil
            && ABS ( [Check Cos (TND)] ) <= Seuil
            && ABS ( [Check VAS] ) <= Seuil,
        "✅ Tous les contrôles OK",
        "⚠ Écart détecté"
    )
```

### 5.3 — Résultats

| Contrôle | Valeur | Statut |
|---|---:|---|
| Check Rev | 0,00 | ✅ |
| Check Opex | 0,00 | ✅ |
| Check Cos | 0,00 | ✅ |
| Check VAS | 0,00 | ✅ |
| **Statut global** | **✅ Tous les contrôles OK** | ✅ |

### 5.4 — Page 3 enrichie

La page Contrôle Qualité affiche désormais :

- **5 cartes KPI** : Nb Comptes Distincts (50), Nb Comptes Non Mappés (3, en rouge), Nb Lignes CDR Manquant (84, en orange), Écart Check Revenue (0.00, en vert), Statut Checks (✅ vert)
- **Histogramme** : évolution mensuelle des CDR manquants
- **Table des comptes non mappés** : les 3 comptes orphelins nominatifs
- **Table des 4 checks** : Check Rev, Check Opex, Check Cos, Check VAS par mois

Cette page constitue la **démonstration directe** de l'objectif « Automatisation et Fiabilité » du cahier des charges.

---

## 6. Enrichissement des données mock (script v3)

Le script `03_populate_oracle_v3.py` a été développé pour permettre de tester les mécanismes de split, absents des versions précédentes.

### 6.1 — Nouveautés

| Élément | Apport |
|---|---|
| **Ligne « Gratuités et crédit perdu »** | Enregistrée globalement, **sans segment** → cible du Type II |
| **Lignes Incoming sans segment** | 3 intitulés (Voice, SMS/MMS, International) → cibles du Type III |
| **Equipment Revenue sans segment** | Cible du Type III via clé S4 |
| **Clés S4 calibrées** | Ratio B2B ~97,6 % (aligné sur le fichier réel) |
| **Clés S5 calibrées** | 3 intitulés avec ratios distincts (14 % à 27 % B2B) |
| **Comptes VAS structurés** | 705 (revenus), 709 (remises), 604 (coûts) |
| **Table Rejet** | 5 exceptions de mapping générées |

### 6.2 — Répartition des lignes de revenus

Sur 21 lignes P&L de revenus :
- **16 lignes** ont un segment identifiable → traitées par le **Type I**
- **5 lignes** sont enregistrées globalement → traitées par les **Types II et III**

Cette répartition reproduit fidèlement la situation réelle décrite dans le cahier des charges.

---

## 7. Décision assumée : non-implémentation de la table Rejet

### 7.1 — Contexte

La table Rejet contient les exceptions de mapping : des triplets (Compte + Offre + CDR) qui doivent contourner la logique standard. Le fichier réel en compte 71.

### 7.2 — Tentative d'implémentation

Une implémentation via Power Query a été tentée :
1. Création d'une colonne composite (Compte + Offre + CDR)
2. Fusion avec la table Dim_Rejet
3. Colonne conditionnelle pour arbitrer entre mapping standard et exception

### 7.3 — Difficultés rencontrées

La manipulation a généré une erreur `Expression.Error` bloquant **13 requêtes du modèle**, rendant le rapport non rafraîchissable. La cause était un décalage de nommage de colonne après fusion (`PL_LINE.1` attendu vs `Dim_Rejet.PL_LINE` réel), suivi d'une cascade de dépendances brisées.

### 7.4 — Décision et justification

**Les étapes ont été annulées et la fonctionnalité abandonnée**, pour trois raisons :

1. **Valeur démonstrative nulle en mock** — les 5 exceptions générées aléatoirement ne reproduisent pas les 71 exceptions métier réelles. Prouver que le mécanisme fonctionne sur des exceptions inventées ne démontre rien.

2. **Rapport coût/bénéfice défavorable** — le risque de casser un livrable fonctionnel dépassait largement le gain attendu.

3. **Implémentable sans refonte** — la table `DIM_REJET` existe dans le schéma Oracle, et la logique (colonne composite + fusion + colonne conditionnelle) est documentée. Lors du branchement sur les données réelles, l'implémentation prendra environ 30 minutes et sera **validable** contre le fichier Excel de référence.

**Recommandation** : implémenter le Rejet au moment du passage en production, où les exceptions ont un sens métier vérifiable.

---

## 8. Difficultés rencontrées et solutions apportées

### 8.1 — Ratio Type II figé à 100 %

**Symptôme** : la `Clé B2B Dynamique` affichait 100 % pour tous les mois.

**Cause** : la mesure de base `Base Outgoing Identifiée` contenait un filtre `NOT ISBLANK(SEGMENT)`. Lorsque le dénominateur appliquait `REMOVEFILTERS(SEGMENT)`, le `CALCULATE` interne réappliquait ce filtre, neutralisant l'effacement. Numérateur et dénominateur devenaient identiques.

**Solution** : retirer le filtre segment de la mesure de base, et appliquer `REMOVEFILTERS(SEGMENT)` + `NOT ISBLANK(SEGMENT)` directement dans le dénominateur du ratio.

**Découverte associée** : les données comportent **trois** segments (B2B, B2C, **Wholesale**) et non deux. La formule `Clé B2C = 1 − Clé B2B` était donc incorrecte. Une mesure dédiée a été créée pour chaque segment, et une mesure `Check Clés` valide que leur somme fait 100 %.

### 8.2 — LOOKUPVALUE retournant systématiquement 0

**Symptôme** : `Ratio Équipement B2B` = 0 % pour tous les mois.

**Cause** : la mesure utilisait `MAX(Dim_Date[Date])` pour identifier le mois courant. Or, dans le contexte d'un mois affiché, `MAX` retourne le **dernier jour** du mois (par exemple le 31 janvier), alors que les clés sont stockées au **premier jour** (1er janvier). Le lookup ne trouvait aucune correspondance.

**Solution** : remplacer `MAX` par `MIN(Dim_Date[Date])`, qui retourne le premier jour du contexte.

### 8.3 — Mesure Incoming s'affichant sur toutes les lignes

**Symptôme** : `Revenue Incoming` affichait 77 938,04 sur **toutes** les lignes de la matrice (Advertising, Amortization, etc.), au lieu des seules lignes Incoming.

**Cause** : `CALCULATE` avec un filtre `IN {...}` **remplace** le contexte de ligne au lieu de le respecter.

**Solution** : encapsuler le filtre dans `KEEPFILTERS()`, qui ajoute le filtre au contexte existant au lieu de l'écraser. Les lignes non-Incoming affichent alors vide.

### 8.4 — Coûts VAS 604 affichés en négatif

**Symptôme** : `VAS Coûts 604` affichait −17 738,79 (un coût devrait être positif).

**Cause** : dans le script v3, le libellé « VAS COST » figurait dans la liste `REVENUE_LINES`, ce qui a créé le compte 604100 avec la catégorie « Rev ». Ses montants ont donc été stockés en négatif (convention classe 7).

**Solution** : inverser le signe dans la mesure DAX (`* -1`). En production, les vrais comptes 604 seront correctement en classe 6, et cette inversion pourra être retirée.

### 8.5 — Écart Check Revenue de 17 738 k'TND

**Symptôme** : la mesure `Écart Check Revenue` affichait 17,74 K au lieu de 0.

**Cause** : le compte 604100 (coûts VAS), catégorisé « Rev », était inclus dans `Total Revenue` mais exclu de `Somme Classe 7` (car ne commençant pas par 7). L'écart correspondait exactement au montant des coûts VAS.

**Solution retenue (Option A)** : correction de la mesure `Total Revenue` pour exclure explicitement les comptes de classe 604 :

```dax
Total Revenue (k'TND) =
CALCULATE (
    SUM ( Fact_Balance[MONTANT_TND] ) * -1 / 1000,
    Fact_Balance[CATEGORIE] = "Rev",
    LEFT ( Fact_Balance[COMPTE_COMPTABLE], 3 ) <> "604"
)
```

Cette correction est la plus juste comptablement : un compte de charge ne doit pas être compté dans le revenu, quelle que soit sa catégorisation dans le référentiel mock. Après application, les quatre check lines affichent 0,00.

---

## 9. Points de contrôle finaux

| Point de contrôle | Statut |
|---|---|
| Script v3 exécuté (gratuités, S4/S5 calibrées, comptes VAS structurés) | ✅ |
| Power BI rafraîchi sur les nouvelles données | ✅ |
| `Clé B2B Dynamique` varie d'un mois à l'autre (8,4 % à 36,4 %) | ✅ |
| `Check Clés` = 100 % pour tous les mois | ✅ |
| Gratuités B2B + B2C + Wholesale = Gratuités Totales | ✅ |
| `Ratio Équipement B2B` ≈ 96,7 % (aligné fichier réel) | ✅ |
| Équipement B2B + B2C = Équipement Total | ✅ |
| Ratios Incoming alignés sur le fichier réel (< 0,6 pt d'écart) | ✅ |
| Incoming B2B + B2C = Incoming Total | ✅ |
| `Check VAS` = 0,00 pour tous les mois | ✅ |
| VAS Coûts B2B + B2C = VAS Coûts Total | ✅ |
| Les 4 check lines affichent 0,00 | ✅ |
| `Statut Checks` = "✅ Tous les contrôles OK" | ✅ |
| Page 3 enrichie (5 cartes + table des checks) | ✅ |
| Table Rejet : décision de non-implémentation documentée | ✅ |
| Fichier PL_Dashboard_v04.pbix sauvegardé | ✅ |

---

## 10. Bonnes pratiques mises en œuvre

### 10.1 — Comprendre avant de coder

Chaque type de split a été explicité en langage métier (avec un exemple chiffré) avant d'être traduit en DAX. Cette discipline a permis de diagnostiquer rapidement les anomalies : quand la clé affichait 100 %, la compréhension du mécanisme a orienté immédiatement vers le problème de contexte de filtre.

### 10.2 — Validation par matrice à chaque étape

Chaque mesure a été testée isolément dans une matrice dédiée avant de passer à la suivante. Cette pratique a évité l'accumulation d'erreurs et permis d'identifier précisément la source de chaque anomalie.

### 10.3 — Le garde-fou de la somme

Pour chaque split, le contrôle systématique **B2B + B2C + Wholesale = Total** a servi de test de non-régression. Ce contrôle simple a détecté immédiatement l'oubli du segment Wholesale.

### 10.4 — Savoir renoncer

L'abandon de la table Rejet, documenté et justifié, illustre une priorisation raisonnée : ne pas mettre en péril un livrable fonctionnel pour une fonctionnalité à faible valeur démonstrative.

---

## 11. Ouverture vers le Sprint 6

Le sprint final couvrira :

- **Bascule vers les données réelles** : changement du paramètre `Serveur_Oracle`, validation contre le fichier Excel
- **Implémentation de la table Rejet** sur les vraies exceptions (si l'accès aux données le permet)
- **Retrait de la correction de signe** sur les comptes 604 (inutile en production)
- **Documentation utilisateur** : guide de rafraîchissement mensuel, mise à jour des clés S4/S5
- **Réintroduction** des boutons de navigation inter-pages
- **Préparation de la présentation finale** à l'encadrement
- **Compilation du rapport de stage** à partir des six documents de clôture

---

## Annexe — Emplacements des livrables

```
C:\PL_Stage\
    01_create_user.sql
    02_create_schema.sql
    03_populate_oracle.py                    ← v1
    03_populate_oracle_v2.py                 ← v2 (calibrage sectoriel)
    03_populate_oracle_v3.py                 ← v3 (données enrichies) ✅ actuelle
    Theme_PL_Ooredoo.json
    PL_Dashboard_v01.pbix                    ← Sprint 2
    PL_Dashboard_v02.pbix                    ← Sprint 3
    PL_Dashboard_v03.pbix                    ← Sprint 4
    PL_Dashboard_v04.pbix                    ← ✨ Sprint 5 (livrable)
    Docs\
        README_Sprint1.md
        Sprint1_Cloture.md
        Sprint2_Guide.md
        Sprint2_Cloture.md
        Sprint3_Guide.md
        Sprint3_Cloture.md
        Sprint4_Guide.md
        Sprint4_Cloture.md
        Sprint5_Guide.md
        Sprint5_Cloture.md                   ← ce document
```
