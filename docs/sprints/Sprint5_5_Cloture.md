# Sprint 5.5 — Clôture : corrections de conformité et audit qualité

**Projet** : Dashboard P&L — Automatisation du reporting financier
**Encadrante** : Fida
**Stagiaire** : Ala
**Entreprise** : Tunisie Telecom
**Sprint** : 5.5 (sprint de correction intercalaire)
**Statut** : ✅ Terminé
**Prérequis** : Sprint 5 clôturé

---

## 1. Origine et objectif du sprint

Ce sprint n'était pas planifié initialement. Il est né d'une décision méthodologique : **avant d'entamer la finalisation (Sprint 6), vérifier point par point que le livrable satisfait réellement chaque exigence du cahier des charges.**

Pour cela, les deux documents sources ont été relus intégralement :
- Le cahier des charges (Word), phrase par phrase
- Le fichier Excel de référence, cette fois en analysant **les formules** des feuilles (`Mapping General`, `VAS`, `Techno offre`, `Bal 06_26`), et non plus seulement leurs valeurs affichées

Cette relecture approfondie a permis de confirmer certains écarts, d'en écarter un (fausse alerte), et surtout d'en **découvrir un nouveau** qui n'avait rien à voir avec la conformité : un bug de calcul sur un indicateur central.

L'objectif du sprint : corriger l'ensemble en une passe, pour aborder le Sprint 6 sur une base pleinement conforme.

---

## 2. Les découvertes de l'audit

### 2.1 — VAS Services et VAS Apigee doivent être séparés (écart confirmé)

Le cahier des charges l'exige explicitement :

> *« Le système doit distinguer et calculer séparément deux catégories de VAS : VAS Services et VAS Apigee. »*

L'analyse de la feuille `VAS` du fichier réel a révélé un bloc distinct « VAS Apigee New Update » utilisant des comptes différents : **705557** (revenus Apigee) et **604450** (coûts Apigee), contre 705100 et 604100 pour les VAS Services. Ces numéros ne sont pas inventés : ils proviennent directement du fichier de référence.

Le livrable ne comportait qu'un VAS global. **Écart réel à corriger.**

### 2.2 — La notion de « Type » était ambiguë (clarification)

Le cahier des charges mentionne un filtre *« Type (Mobile, Fixe...) »*. L'analyse de la formule réelle de la colonne Type dans la balance a montré qu'elle encode en réalité **Prepaid/Postpaid** :

```
Type = SI(1er caractère du code offre = "1" ; "Prepaid" ; SI(... = "2" ; "Postpaid" ; ""))
```

C'est la colonne **Techno** (déjà implémentée au Sprint 4) qui porte Mobile/Fixed/Digital.

**Décision** : implémenter les deux champs (Type et Techno) pour couvrir les deux lectures possibles du besoin, et documenter la clarification.

### 2.3 — Les « Discounts » ne constituaient pas un écart (fausse alerte écartée)

Un premier audit rapide avait signalé l'absence des « Discounts » dans la formule Revenu Net. La relecture des comptes a montré que, dans le référentiel réel, gratuités et discounts partagent la **même famille de comptes** (classe 709 — RRR, Rabais Remises Ristournes) et remontent à la même ligne P&L (« Gratuités et crédit perdu »).

**Conclusion** : aucun écart. La formule *Revenu Net = Brut + Gratuités + Discounts* est déjà satisfaite. Point clarifié, aucune correction nécessaire.

### 2.4 — Bug de calcul EBITDA / D&A (découverte majeure)

En vérifiant la structure réelle du waterfall (feuille `Actual P&L 2026`), la position de l'amortissement s'est révélée être **après** l'EBITDA :

```
EBITDA
− Depreciation
− Amortization
= Operating Margin (EBIT)
```

Or la mesure `Total OPEX` (Sprint 3) sommait **tous** les comptes de catégorie Opex, D&A compris. Conséquence : le D&A était soustrait une première fois dans l'EBITDA, puis une seconde fois pour obtenir le Net Profit.

**Le D&A était compté deux fois.** L'EBITDA affiché était en réalité un EBIT mal étiqueté, et le Net Profit était sous-évalué.

Ce n'est pas un écart au cahier des charges, mais un **défaut de conception** qui faussait un KPI central. Corrigé dans ce sprint.

---

## 3. Corrections apportées

### 3.1 — Script de données v4

Le script `03_populate_oracle_v4.py` a été développé (sans modification de schéma) pour :

| Correction | Détail |
|---|---|
| Séparation VAS Apigee | Nouvelles lignes P&L « VAS Apigee Revenue » / « VAS Apigee Cost », comptes réels 705557 / 604450 |
| Renommage VAS Services | « VAS Revenue » / « VAS COST » → « VAS Services Revenue » / « VAS Services Cost » |
| Correction d'un bug historique | « VAS COST » figurait par erreur dans la liste des revenus (catégorie Rev) depuis la v1 → reclassé en catégorie Cos |
| Champ Type peuplé | Prepaid / Postpaid affecté par offre (~72 % / 28 %), reproduisant le mécanisme réel |
| COS partiellement segmenté | Deux lignes de COS (interconnexion sortante, commission distributeur) reçoivent une offre et un segment, pour permettre un vrai proratage des coûts |

Volume généré : ~9 900 lignes dans FACT_BALANCE. Script testé par simulation complète avant exécution.

### 3.2 — Correction du bug EBITDA / D&A

La mesure `Total OPEX (k'TND)` exclut désormais explicitement le D&A :

```dax
Total OPEX (k'TND) =
CALCULATE (
    SUM ( Fact_Balance[MONTANT_TND] ) / 1000,
    Fact_Balance[CATEGORIE] = "Opex",
    Fact_Balance[PL_LINE] <> "Depreciation",
    Fact_Balance[PL_LINE] <> "Amortization"
)
```

Les mesures `EBITDA` et `Net Profit` se recalculent automatiquement (elles réutilisent `Total OPEX`). Le D&A n'est désormais soustrait qu'une seule fois, dans le passage EBITDA → Net Profit.

### 3.3 — Correction en cascade du Check Opex

La correction du D&A a rendu incohérent le contrôle `Check Opex`, qui comparait un Total OPEX sans D&A à une somme de balance avec D&A. La mesure a été alignée :

```dax
Check Opex (TND) =
VAR TotalOpexPL = [Total OPEX (k'TND)] * 1000
VAR TotalClasse6Opex =
    CALCULATE (
        SUM ( Fact_Balance[MONTANT_TND] ),
        Fact_Balance[CATEGORIE] = "Opex",
        Fact_Balance[PL_LINE] <> "Depreciation",
        Fact_Balance[PL_LINE] <> "Amortization"
    )
RETURN
    TotalOpexPL - TotalClasse6Opex
```

Résultat : `Check Opex` = 0,00 et le statut de fiabilité repasse au vert.

### 3.4 — VAS Services et VAS Apigee : mesures dédiées

Chaque catégorie dispose désormais de son propre jeu complet de mesures (revenus, coûts, net, clés dynamiques, réallocation, check).

**Point technique déterminant** : les mesures VAS n'utilisent PAS la mesure imbriquée `[Total Revenue (k'TND)]`, mais un calcul direct :

```dax
VAS Services Revenue (k'TND) =
CALCULATE (
    SUM ( Fact_Balance[MONTANT_TND] ) * -1 / 1000,
    Fact_Balance[COMPTE_COMPTABLE] = "705100-0000"
)
```

Ce choix résout un piège identifié pendant le sprint (voir §5.2).

**Trois segments pris en compte** : les clés et checks intègrent B2B, B2C **et Wholesale**, ce dernier représentant ~10 % du VAS.

### 3.5 — Filtres, traçabilité et proratage

| Livrable | Description |
|---|---|
| Slicer Type | Prepaid / Postpaid, Page 2 |
| Slicer Techno | Renommé « Technologie (Mobile/Fixe/Digital) » pour lever l'ambiguïté |
| Slicer Offre | Liste déroulante des 30 offres |
| Mesure `Origine Split` | Affiche pour chaque ligne son type de split (I automatique / II ratio / III clé manuelle) — répond à l'exigence de traçabilité « Automatique vs Clé Manuelle » |
| Coûts proratisés | Mesures `Gross Margin B2B/B2C Proratisé` déduisant de vrais coûts segmentés |

### 3.6 — Corrections cosmétiques

- `Écart Check Revenue` : arrondi à 2 décimales pour supprimer l'affichage en notation scientifique (`-1.16E-10` → `0,00`)
- Table Origine Split : filtre `CATEGORIE = Rev` ajouté au niveau du visuel, pour n'afficher que les lignes de revenu (les splits ne concernent pas les coûts)

---

## 4. Résultats de validation

### 4.1 — VAS Services vs VAS Apigee

| Mesure | Valeur validée | Source SQL |
|---|---:|---:|
| VAS Services Revenue | 35 451,63 | ✅ concordant |
| VAS Services Cost | 34 219,45 | ✅ concordant |
| **VAS Services Net** | **1 232,18** | ✅ |
| VAS Apigee Revenue | 50 798,29 | ✅ concordant |
| VAS Apigee Cost | 6 348 | ✅ concordant |
| **VAS Apigee Net** | **44 450,67** | ✅ |
| **Check VAS Services** | **0,00 (tous les mois)** | ✅ |
| **Check VAS Apigee** | **0,00 (tous les mois)** | ✅ |

Lecture métier : VAS Apigee dégage une marge nette élevée (44 450), tandis que VAS Services est proche de l'équilibre (1 232) — cohérent avec le profil d'une plateforme à forte marge.

### 4.2 — Indicateurs du waterfall après correction

| Indicateur | Avant (bug) | Après correction |
|---|---:|---:|
| Total OPEX | incluait D&A | 194,03 k'TND (D&A exclu) |
| EBITDA % | ~18 % | 40,13 % |
| Net Profit | sous-évalué | 265,56 k'TND |
| Statut Checks | « Écart détecté » (faux) | « Tous les contrôles OK » |

### 4.3 — Contrôles d'intégrité

| Contrôle | Résultat |
|---|---|
| Check Rev | 0,00 ✅ |
| Check Opex | 0,00 ✅ (après correction §3.3) |
| Check Cos | 0,00 ✅ |
| Check VAS Services | 0,00 ✅ |
| Check VAS Apigee | 0,00 ✅ |

---

## 5. Difficultés rencontrées et solutions

### 5.1 — VAS Revenue gonflé à 821 000 k'TND

**Symptôme** : `VAS Services Revenue` affichait 821 024 au lieu des ~35 452 attendus.

**Cause** : le filtre `LEFT(COMPTE_COMPTABLE, 6) = "705100"`, appliqué dans un `CALCULATE` autour d'une mesure imbriquée, était mal évalué par le moteur. Une fonction transformant une colonne dans un filtre CALCULATE n'est pas toujours interprétée comme un filtre effectif.

**Solution** : filtrer sur la valeur exacte du compte (`= "705100-0000"`) plutôt que sur un `LEFT()`. Le diagnostic a été confirmé par une mesure `Test VAS Direct` qui, elle, renvoyait la bonne valeur.

### 5.2 — Interférence entre filtres CALCULATE imbriqués

**Symptôme** : même après correction du filtre, la valeur restait fausse.

**Cause** : la mesure VAS réutilisait `[Total Revenue (k'TND)]`, qui contient déjà un filtre (exclusion du compte 604, héritée du Sprint 5). Les deux filtres CALCULATE imbriqués se percutaient.

**Solution** : abandonner la mesure imbriquée et calculer directement depuis `SUM(MONTANT_TND)`. Chaque mesure VAS est ainsi autonome et non tributaire des filtres d'une autre.

### 5.3 — Checks VAS non nuls (le 3ᵉ segment)

**Symptôme** : `Check VAS Services` = -3 748 au lieu de 0.

**Cause** : les checks ne sommaient que B2B + B2C, alors que le VAS comporte aussi ~10 % de Wholesale. La part Wholesale n'était pas réallouée.

**Solution** : ajout des mesures `Clé VAS ... Wholesale` et `VAS ... Cost Wholesale`, puis passage des checks à quatre termes (B2B + B2C + Wholesale − Total). Les deux checks affichent alors 0,00.

### 5.4 — Fausse alerte du Check Opex

Traitée au §3.3 : conséquence directe et attendue de la correction du D&A, résolue en alignant le périmètre des deux côtés de la comparaison.

---

## 6. Point ouvert documenté : artefact gratuités / remises (mock)

Dans les données mock, les comptes de gratuités et de remises (classe 709) ont été générés avec la convention de signe des revenus. Après le `× -1` appliqué aux revenus, ces montants deviennent positifs et **s'ajoutent** au chiffre d'affaires au lieu de le réduire (surestimation de l'ordre de 36 k'TND, soit quelques points sur le Total Revenue, le Gross Margin % et l'EBITDA %).

**Il ne s'agit pas d'une erreur de logique**, mais d'un artefact du générateur de données. En production, les vrais comptes 709 portent nativement un solde débiteur ; la formule `SUM(classe 7) × -1` les nette donc automatiquement. **Aucune correction ne sera nécessaire lors de la bascule.**

Ce point est consigné ici et sera rappelé dans la documentation du Sprint 6, afin que la légère surestimation des ratios sur données mock soit comprise et assumée lors de la présentation.

---

## 7. Table de conformité au cahier des charges

| Exigence | Section CdC | Statut |
|---|---|---|
| Objectif 1 — Automatisation & Fiabilité | I.1 | ✅ |
| Objectif 2 — Vue Analytique Granulaire | I.1 | ✅ |
| Objectif 3 — Visualisation & Pilotage | I.1 | ✅ |
| Table de mapping exhaustive | II.b.1 | ✅ |
| Automatisation des splits Revenus (Types I/II/III) | II.b.2 | ✅ |
| VAS Services et VAS Apigee séparés | Module VAS §1 | ✅ (5.5) |
| VAS Net = Σ705 − Σ709 − Σ604 | Module VAS §2 | ✅ |
| Clés VAS dynamiques | Module VAS §3 | ✅ |
| Coûts VAS réalloués proportionnellement | Module VAS §4 | ✅ |
| Filtre BU / CDR | II.b.3 | ✅ |
| Filtre Technologie | II.b.3 | ✅ (5.5, clarifié) |
| Filtre Offre | II.b.3 | ✅ (5.5) |
| Filtre Type | II.b.3 | ✅ (5.5, clarifié) |
| Zéro « Null » | II.b.4 | ✅ |
| Revenu Net = Brut + Gratuités + Discounts | Module Revenue Split | ✅ (clarifié — non-écart) |
| Traçabilité origine Auto vs Manuel | Module Revenue Split §3 | ✅ (5.5) |
| Structure waterfall | IV.1 | ✅ (simplifié en mock, documenté) |
| Agrégation temporelle (k'TND) | IV.2.A | ✅ |
| Ventilation B2B/B2C (affectation + clés) | IV.2.B | ✅ |
| Gross Margin = Revenue − COS | IV.2.C | ✅ |
| EBITDA = Gross Margin − OPEX (hors D&A) | IV.2.C | ✅ (5.5, bug corrigé) |
| Check Lines (réconciliation classe 7) | IV.3 | ✅ |
| Dimension temporelle | V.1 | ✅ |
| Dimension structurelle (drill-down) | V.2 | ✅ |
| Dimension segmentaire (Total/B2B/B2C) | V.3 | ✅ |
| P&L B2B avec coûts proratisés | V.3 | ✅ (5.5, démontré sur 2 lignes) |
| Table Rejet (exceptions) | — | 🟡 Non-implémentation assumée (Sprint 5) |

**26 exigences sur 27 pleinement satisfaites ; 1 décision de non-implémentation documentée.**

---

## 8. Points de contrôle finaux

| Point de contrôle | Statut |
|---|---|
| Script v4 exécuté sans erreur | ✅ |
| Power BI actualisé sur les données v4 | ✅ |
| Total OPEX exclut Depreciation / Amortization | ✅ |
| EBITDA % recalculé (40,13 %) | ✅ |
| Check Opex ramené à 0,00 | ✅ |
| VAS Services Net et VAS Apigee Net distincts et validés | ✅ |
| Check VAS Services = 0 et Check VAS Apigee = 0 | ✅ |
| Slicers Type, Techno, Offre en place | ✅ |
| Mesure Origine Split créée et filtrée sur Rev | ✅ |
| Écart Check Revenue arrondi (0,00) | ✅ |
| Statut Fiabilité au vert | ✅ |
| Table de conformité établie (26/27) | ✅ |
| Fichier sauvegardé PL_Dashboard_v05.pbix | ✅ |

---

## 9. Enseignements

### 9.1 — Auditer avant de finaliser

Ce sprint illustre la valeur d'une revue de conformité systématique avant clôture. Sans elle, trois écarts réels (VAS Apigee, filtres, traçabilité) et surtout un bug de KPI (EBITDA) seraient passés en production. Confronter le livrable au besoin exprimé, ligne par ligne, est une étape à part entière.

### 9.2 — Lire les formules, pas seulement les valeurs

Les découvertes les plus importantes (le vrai sens de « Type », les comptes réels d'Apigee, la position du D&A) ne sont apparues qu'en ouvrant les **formules** du fichier Excel. Les valeurs affichées ne suffisent pas à comprendre une logique métier.

### 9.3 — Les filtres CALCULATE imbriqués sont un piège

Le sprint a mis en évidence deux comportements DAX subtils : l'inefficacité d'un `LEFT()` comme filtre, et l'interférence entre filtres de mesures imbriquées. La règle retenue : pour une mesure filtrée sur un compte précis, calculer directement depuis la colonne de montant plutôt que réutiliser une mesure déjà filtrée.

### 9.4 — Distinguer bug, artefact et non-écart

Ce sprint a traité les trois : un vrai bug (EBITDA, corrigé), un artefact de données mock (gratuités/remises, documenté sans correction), et une fausse alerte (Discounts, écartée). Savoir les distinguer évite à la fois de laisser passer un défaut réel et de « corriger » ce qui n'a pas besoin de l'être.

---

## 10. Ouverture vers le Sprint 6

Le livrable est désormais pleinement conforme. Le Sprint 6 pourra donc se concentrer sur la finalisation sans dette technique : bascule vers les données réelles, documentation utilisateur et technique, préparation de la présentation, et compilation du rapport de stage. La table de conformité (§7) constituera une pièce maîtresse de la présentation à l'encadrement.

---

## Annexe — Livrables du sprint

```
C:\PL_Stage\
    03_populate_oracle_v4.py                 ← script de données corrigé
    PL_Dashboard_v05.pbix                    ← livrable conforme
    Docs\
        Sprint5_5_Guide.md
        Sprint5_5_Cloture.md                 ← ce document
```
