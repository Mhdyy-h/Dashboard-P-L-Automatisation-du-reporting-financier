# Sprint 4 — Construction du dashboard interactif

**Projet** : Dashboard P&L — Automatisation du reporting financier
**Encadrante** : Fida
**Stagiaire** : Ala
**Entreprise** : Tunisie Telecom
**Sprint** : 4 sur 6
**Statut** : ✅ Terminé
**Prérequis** : Sprint 3 clôturé (~45 mesures DAX validées)

---

## 1. Objectif du sprint

Transformer le modèle analytique (Sprint 3) en un **dashboard interactif présentable**, structuré en trois pages répondant chacune à un besoin métier distinct. Ce sprint marque le passage d'un moteur de calcul à un **produit livrable**.

### Livrables clés

1. Un **thème visuel personnalisé** aux couleurs de la marque, importable et réutilisable
2. Un dashboard **3 pages** entièrement fonctionnel et interactif
3. Une **traçabilité documentée** entre les besoins du cahier des charges et les fonctionnalités livrées
4. Le fichier `PL_Dashboard_v03.pbix` prêt pour présentation

---

## 2. Architecture du dashboard livré

### 2.1 — Identité visuelle

Un thème Power BI personnalisé (`Theme_PL_Ooredoo.json`) a été créé et importé, définissant :

| Élément | Couleur | Hex |
|---|---|---|
| Couleur principale (accents, total général) | Rouge Ooredoo | `#ED1D25` |
| Titres, valeurs KPI, en-têtes | Bleu marine | `#003366` |
| Accent secondaire | Turquoise | `#32BCAD` |
| Texte courant | Gris foncé | `#4C4D4F` |
| Libellés secondaires | Gris moyen | `#7B8794` |
| Fond de page | Gris clair | `#F5F5F5` |

Le thème configure automatiquement les cartes KPI, matrices (en-têtes bleu marine, total général rouge), slicers, waterfalls (vert = hausse, rouge = baisse, bleu = total), bordures arrondies et ombres légères.

**Bénéfice** : cohérence visuelle garantie sur l'ensemble du rapport, sans réglage manuel visuel par visuel.

### 2.2 — Page 1 : Vue Exécutive

**Public cible** : direction, décideurs
**Objectif** : comprendre la situation en 5 secondes

Contenu :
- **En-tête** : logo Ooredoo officiel + titre "Dashboard P&L"
- **6 cartes KPI** : Total Revenue (598,76K), Gross Margin % (55,00%), EBITDA (108,42K), EBITDA % (18,11%), Net Profit (28,33K), Statut Fiabilité (⚠ À vérifier)
- **Courbe d'évolution du chiffre d'affaires** : 24 mois, tri chronologique, pic de décembre 2026 visible (30,4K)
- **Waterfall "De Revenue à Net Profit"** : décomposition Revenue → D&A → OPEX → COS → Total, avec code couleur automatique
- **Treemap "Répartition par Business Unit"** : Mobile Services (267K), Wholesale/Interco (127K), Digital & VAS (109K), Fixed Services (62K), Enterprise (32K)

### 2.3 — Page 2 : Analyse P&L détaillée

**Public cible** : contrôleurs de gestion, analystes
**Objectif** : explorer et comprendre l'origine des chiffres

Contenu :
- **Matrice hiérarchique** avec drill-down par ligne P&L (VAS Revenue, VAS COST, Subscriber Roaming Voice, SOS, SMS/MMS Services, Outgoing National Onnet/Offnet, Outgoing International, Others, IOT Services...)
- **Colonnes temporelles** : mois par mois avec Total Revenue et Croissance MoM %
- **Formatage conditionnel** : les valeurs sont colorées selon leur intensité, facilitant la lecture visuelle
- **Ligne de total** : réconciliation mensuelle (21 575,28 en janvier 2025, 21 738,93 en février...)
- **5 slicers interactifs** : BU_NAME, CDR_NAME, SEGMENT, TECHNO, et un curseur temporel (mode "Entre", 01/01/2025 → 31/12/2026)

### 2.4 — Page 3 : Contrôle Qualité "Zéro Null"

**Public cible** : IT, comptabilité, encadrement
**Objectif** : prouver la fiabilité des données

Contenu :
- **4 cartes KPI avec formatage conditionnel dynamique** :
  - Nb Comptes Distincts : **47** (bleu marine, information neutre)
  - Nb Comptes Non Mappés : **3** (rouge — anomalie détectée)
  - Nb Lignes CDR Manquant : **92** (orange — vigilance)
  - Écart Check Revenue : **0.00** (vert — réconciliation parfaite)
- **Histogramme d'évolution des CDR manquants** : répartition mensuelle, permettant de détecter d'éventuels pics anormaux
- **Table des comptes non mappés** : liste nominative des 3 comptes orphelins (699000-0000, 699001-0000, 699002-0000) avec leur descriptif et leur catégorie "Null"

**Le formatage conditionnel** est piloté par des mesures DAX dédiées :

```dax
Couleur Comptes Non Mappés =
IF ( [Nb Comptes Non Mappés] > 0, "#ED1D25", "#2E7D32" )
```

```dax
Couleur CDR Manquant =
IF ( [Nb Lignes CDR Manquant] > 0, "#F5A623", "#2E7D32" )
```

```dax
Couleur Écart Check =
IF ( ABS ( [Écart Check Revenue (k'TND)] ) <= 1, "#2E7D32", "#ED1D25" )
```

Cette approche est plus robuste que les règles numériques de l'interface : la logique est explicite, versionnée dans le modèle, et réutilisable.

---

## 3. Traçabilité — Conformité aux objectifs du cahier des charges

Cette section établit la correspondance entre les objectifs stratégiques définis dans le cahier des charges et les fonctionnalités effectivement livrées.

### Objectif 1 — Automatisation et Fiabilité

> *« Industrialiser le processus d'extraction et de transformation des données pour garantir l'intégrité des chiffres financiers (élimination des erreurs humaines). »*

| Exigence | Réalisation | Statut |
|---|---|---|
| Élimination de l'extraction manuelle | Connexion directe Oracle → Power BI, rafraîchissement en 1 clic | ✅ |
| Intégrité des chiffres | Mesure `Écart Check Revenue` = 0.00 (réconciliation Balance ↔ P&L) | ✅ |
| Détection des erreurs | Page 3 complète : 3 comptes non mappés et 92 lignes sans CDR détectés automatiquement | ✅ |
| Traçabilité | Chaque valeur du dashboard remonte à ses lignes source via drill-down | ✅ |

**Verdict : objectif pleinement couvert.** La Page 3 constitue la démonstration directe de cet objectif : le système signale de lui-même les anomalies qui, dans le processus Excel actuel, passeraient inaperçues.

### Objectif 2 — Vue Analytique Granulaire

> *« Permettre un découpage analytique précis par CDR et BU pour une meilleure compréhension des leviers de rentabilité. »*

| Exigence | Réalisation | Statut |
|---|---|---|
| Découpage par BU | Slicer BU_NAME (Page 2) + Treemap par BU (Page 1) | ✅ |
| Découpage par CDR | Slicer CDR_NAME (Page 2), rattaché hiérarchiquement aux BU | ✅ |
| Compréhension des leviers | Treemap montrant que Mobile = 45% du CA, Wholesale = 21%, Digital = 18% | ✅ |
| Filtrage complémentaire | Slicers SEGMENT (B2B/B2C/Wholesale) et TECHNO | ✅ |

**Verdict : objectif couvert.** Le découpage BU et CDR est disponible et interactif.

### Objectif 3 — Visualisation et Pilotage

> *« Fournir des tableaux de bord interactifs permettant une navigation intuitive entre les données consolidées et les détails transactionnels, facilitant ainsi la prise de décision rapide. »*

| Exigence | Réalisation | Statut |
|---|---|---|
| Tableaux de bord interactifs | 3 pages avec slicers, filtres croisés, sélections propagées | ✅ |
| Navigation consolidé → détail | Matrice avec drill-down hiérarchique (Page 2) | ✅ |
| Décision rapide | Page 1 : 6 KPI lisibles en 5 secondes | ✅ |
| Dimension temporelle | Curseur de période + courbe 24 mois + croissance MoM/YoY | ✅ |

**Verdict : objectif couvert.**

### Synthèse de conformité

**Les trois objectifs stratégiques du cahier des charges sont couverts par le dashboard livré.**

---

## 4. Besoins fonctionnels — État de couverture

| Besoin fonctionnel | Statut | Commentaire |
|---|---|---|
| Enrichissement du référentiel (mapping) | ✅ | Toutes les dimensions du mapping sont exploitables dans les filtres |
| Automatisation des splits (Revenus & VAS) | 🟡 Partiel | Ventilation B2B/B2C par affectation directe. Splits Types II/III à implémenter au Sprint 5 |
| Filtres interactifs (BU, CDR, Techno, Offre, Type) | ✅ | 5 slicers opérationnels |
| Fiabilisation Zéro "Null" | ✅ | Page 3 dédiée, détection automatique |
| Drill-down consolidé → transactionnel | 🟡 Partiel | Drill-down jusqu'au compte comptable. Drill-through vers les transactions individuelles possible en amélioration |

---

## 5. Difficultés rencontrées et solutions apportées

### 5.1 — Tri chronologique inversé sur la courbe de tendance

**Symptôme** : la courbe d'évolution du CA descendait de gauche à droite, avec les dates commençant à 2026-12 et finissant à 2025-04.

**Cause** : l'axe était trié par valeur de Revenue (décroissant) au lieu d'être trié chronologiquement.

**Solution** : menu contextuel du visuel → « Trier l'axe » → sélection de `Année-Mois` → tri croissant. La courbe montre désormais correctement la progression 2025 → 2026 avec le pic de décembre.

### 5.2 — Ordre incorrect des étapes du waterfall

**Symptôme** : les barres du graphique en cascade apparaissaient dans un ordre alphabétique, brisant la logique du waterfall.

**Cause** : la colonne `Étape` de la table `Waterfall_Steps` était triée alphabétiquement par défaut.

**Solution** : `Outils de colonne` → `Trier par colonne` → sélection de la colonne `Ordre`. Le waterfall respecte désormais la séquence financière.

### 5.3 — Table Waterfall_Steps introuvable lors de la création de la mesure

**Symptôme** : erreur « table Waterfall_Steps est introuvable » lors de la création de la mesure `Waterfall Step`.

**Cause** : la mesure référençait une table qui n'existait pas encore.

**Solution** : création préalable de la table calculée via `DATATABLE()`, puis création de la mesure. **Leçon** : en DAX, toujours créer les objets référencés avant les mesures qui les utilisent.

### 5.4 — Slicer de date affichant 730 valeurs journalières

**Symptôme** : le slicer de période affichait une liste de cases à cocher jour par jour (01/01/2025, 02/01/2025...), soit 730 entrées inutilisables.

**Cause** : le style par défaut du slicer est « Liste », et la colonne `Date` de Dim_Date contient tous les jours de la période.

**Solution** : passage du style de segment en mode **« Entre »**, transformant le slicer en curseur temporel à deux poignées. Beaucoup plus compact et adapté à des données mensuelles.

### 5.5 — Formatage conditionnel introuvable sur la nouvelle carte visuelle

**Symptôme** : impossibilité de trouver l'option « Valeur d'appel → Couleur » décrite dans la documentation, la nouvelle carte visuelle de Power BI ayant une arborescence de format différente.

**Cause** : Power BI a introduit un nouveau visuel « Carte » multi-valeurs dont les options sont organisées différemment de l'ancienne carte simple.

**Solution** : l'option se trouve sous `Cartes → Légende/Valeur → Couleur → fx`. Le formatage conditionnel a été implémenté via des **mesures de couleur DAX** (style « Valeur du champ ») plutôt que par règles numériques — approche plus robuste et maintenable.

---

## 6. Décisions de conception assumées

### 6.1 — Suppression des boutons de navigation

**Décision** : les boutons de navigation inter-pages ont été retirés au profit des onglets natifs de Power BI.

**Justification** : en mode Desktop, les onglets en bas de l'écran suffisent. Cette simplification allège l'interface.

**Point de vigilance** : si le rapport est publié sur Power BI Service ou présenté en mode plein écran, des boutons de navigation explicites amélioreraient l'expérience. À reconsidérer au Sprint 6 avant la livraison finale.

### 6.2 — Suppression de la jauge de complétude

**Décision** : la jauge visuelle de complétude du mapping a été retirée de la Page 3.

**Justification** : les 4 cartes KPI avec formatage conditionnel transmettent la même information de manière plus compacte et plus précise.

**Point de vigilance** : une jauge offre une lecture visuelle immédiate du niveau de qualité. Elle pourrait être réintroduite si l'espace le permet.

### 6.3 — Positionnement du treemap sur la Page 1

**Décision** : le treemap « Revenue par BU » a été conservé en bas de la Vue Exécutive plutôt que déplacé sur la Page 2.

**Justification** : il complète bien la lecture exécutive en montrant d'où vient le chiffre d'affaires, sans nécessiter de changer de page.

---

## 7. Points de contrôle finaux

| Point de contrôle | Statut |
|---|---|
| Thème visuel personnalisé importé et appliqué | ✅ |
| Logo officiel Ooredoo intégré | ✅ |
| Page 1 : 6 KPI + courbe + waterfall + treemap | ✅ |
| Page 2 : matrice hiérarchique avec drill-down | ✅ |
| Page 2 : 5 slicers fonctionnels + curseur temporel | ✅ |
| Page 3 : 4 KPI avec formatage conditionnel dynamique | ✅ |
| Page 3 : histogramme + table des comptes non mappés | ✅ |
| Courbe triée chronologiquement | ✅ |
| Waterfall dans l'ordre financier correct | ✅ |
| Interactivité testée (filtres croisés propagés) | ✅ |
| Cohérence visuelle sur les 3 pages | ✅ |
| Conformité aux 3 objectifs stratégiques vérifiée | ✅ |
| Fichier PL_Dashboard_v03.pbix sauvegardé | ✅ |

---

## 8. Bonnes pratiques mises en œuvre

### 8.1 — Thème centralisé plutôt que formatage manuel

L'utilisation d'un fichier thème JSON garantit que tout nouveau visuel adopte automatiquement la charte graphique. Cela évite la dérive visuelle progressive typique des dashboards construits visuel par visuel.

### 8.2 — Formatage conditionnel piloté par mesures DAX

Plutôt que de configurer des règles numériques dans l'interface (fragiles, invisibles, non documentées), les couleurs conditionnelles sont pilotées par des mesures explicites. La logique métier reste dans le modèle, versionnée et auditable.

### 8.3 — Une page = un public = un objectif

Chaque page a un destinataire clair et un objectif unique. Cette discipline évite le syndrome du « dashboard fourre-tout » où l'on entasse 15 visuels par page sans hiérarchie de lecture.

### 8.4 — Vérification de conformité aux besoins

Avant de clôturer le sprint, une relecture du cahier des charges a été effectuée pour vérifier point par point l'alignement entre les besoins exprimés et les fonctionnalités livrées (voir section 3). Cette démarche est ce qui distingue un livrable « qui marche » d'un livrable « qui répond au besoin ».

---

## 9. Ouverture vers le Sprint 5

Le Sprint 5 s'attaquera aux **règles métier avancées** qui restent simplifiées dans le mock :

- **Splits Type II** : ratios dynamiques B2B/B2C calculés mensuellement (poids du Brut B2B / Brut Total)
- **Splits Type III** : application des clés manuelles S4 (Équipement) et S5 (Incoming/A2P/P2P) via LOOKUPVALUE sur le mois
- **VAS Net avancé** : implémentation de la formule exacte Σ(705) − Σ(709) − Σ(604), avec distinction VAS Services / VAS Apigee
- **Table Rejet** : intégration des exceptions de mapping (triplets Compte+Offre+CDR contournant la logique standard)
- **Drill-through transactionnel** : page de détail permettant de descendre jusqu'aux lignes individuelles de la balance
- **Réintroduction éventuelle** des boutons de navigation et de la jauge de complétude

---

## Annexe — Emplacements des livrables

```
C:\PL_Stage\
    01_create_user.sql
    02_create_schema.sql
    03_populate_oracle.py
    03_populate_oracle_v2.py
    Theme_PL_Ooredoo.json                    ← thème visuel
    PL_Dashboard_v01.pbix                    ← Sprint 2
    PL_Dashboard_v02.pbix                    ← Sprint 3
    PL_Dashboard_v03.pbix                    ← ✨ Sprint 4 (livrable)
    Docs\
        README_Sprint1.md
        Sprint1_Cloture.md
        Sprint2_Guide.md
        Sprint2_Cloture.md
        Sprint3_Guide.md
        Sprint3_Cloture.md
        Sprint4_Guide.md
        Sprint4_Cloture.md                   ← ce document
```
