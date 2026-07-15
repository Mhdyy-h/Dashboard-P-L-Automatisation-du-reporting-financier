# Dashboard P&L — Automatisation du reporting financier

Automatisation du reporting du compte de résultat (Profit & Loss) d'un opérateur télécom, migrant un processus manuel Excel vers une chaîne décisionnelle **Oracle → Power BI** entièrement automatisée.

> Projet réalisé dans le cadre d'un stage en Business Intelligence. Développé et validé sur données **mock** réalistes, la solution est conçue pour basculer sur les données de production par un simple changement de paramètre.

---

## 🎯 Contexte

Le suivi du P&L reposait sur des extractions manuelles retravaillées dans Excel — un processus lent, difficile à auditer et exposé aux erreurs humaines. Ce projet industrialise le processus de bout en bout : extraction de la balance comptable, application des règles de gestion, calcul des indicateurs et restitution dans un tableau de bord interactif.

Contrainte structurante : **aucun accès aux données de production** pendant le développement. L'ensemble a donc été construit sur un jeu de données généré, calibré pour reproduire la structure et les ordres de grandeur réels.

---

## ✨ Fonctionnalités

- **Pipeline automatisé** Oracle → Power Query → modèle en étoile → mesures DAX → visuels
- **~70 mesures DAX**, dont plusieurs avancées (time intelligence, splits dynamiques, réallocation de coûts)
- **Trois types de ventilation B2B/B2C** :
  - Type I — affectation directe par mapping
  - Type II — ratio dynamique recalculé chaque mois
  - Type III — clés manuelles par `LOOKUPVALUE` sur la période
- **Module VAS** avec séparation Services / Apigee et réallocation proportionnelle des coûts
- **Cinq contrôles d'intégrité** réconciliant en permanence le P&L avec la balance comptable
- **Détection automatique des anomalies** de mapping (comptes non rattachés)
- **Mécanisme d'exceptions** (table de rejet) via fusion Power Query
- **Bascule mock ↔ production** par paramètre, sans modification de code

---

## 🏗️ Architecture

```
┌─────────────┐   ┌──────────────┐   ┌──────────────────┐   ┌───────────┐   ┌─────────┐
│   Oracle    │ → │ Power Query  │ → │ Modèle en étoile │ → │ Mesures   │ → │ Visuels │
│   XE 11.2   │   │  (ETL)       │   │  (relations)     │   │ DAX       │   │ 3 pages │
└─────────────┘   └──────────────┘   └──────────────────┘   └───────────┘   └─────────┘
```

**Modèle en étoile** : une table de faits (`Fact_Balance`) reliée à des dimensions (comptes, BU, CDR, offre, date), plus des tables de paramétrage interrogées par lookup (clés de ventilation) et une table d'exceptions.

---

## 🧰 Stack technique

| Composant | Technologie |
|---|---|
| Base de données | Oracle Database XE 11.2 |
| Génération des données | Python (oracledb, faker, numpy, pandas) |
| ETL / modélisation | Power Query, Power BI Desktop |
| Langage de calcul | DAX |
| Restitution | Power BI (3 pages, thème personnalisé) |

---

## 📂 Structure du dépôt

```
.
├── sql/
│   ├── 01_create_user.sql          # création de l'utilisateur et des droits
│   └── 02_create_schema.sql        # création des 11 tables
├── scripts/
│   └── 03_populate_oracle_v4.py    # génération des données mock
├── powerbi/
│   ├── Theme_PL.json               # thème visuel
│   └── PL_Dashboard.pbix           # rapport (si versionné — voir note plus bas)
├── docs/
│   ├── GUIDE_UTILISATEUR.md        # guide pour l'utilisateur final
│   ├── DOCUMENTATION_TECHNIQUE.md  # architecture et maintenance
│   ├── RAPPORT_CONFORMITE.md       # traçabilité besoin → réalisation
│   └── sprints/                    # documents de clôture par sprint
├── .gitignore
└── README.md
```

---

## 🚀 Mise en route

### Prérequis

- Oracle Database XE 11.2 installé et démarré
- Python 3.x avec Oracle Instant Client (mode thick)
- Power BI Desktop

### Installation

```bash
# 1. Cloner le dépôt
git clone <url-du-depot>
cd <nom-du-depot>

# 2. Installer les dépendances Python
pip install oracledb faker numpy pandas

# 3. Créer l'utilisateur et le schéma Oracle
#    (exécuter les scripts SQL avec un compte administrateur)
sqlplus system/<mot_de_passe> @sql/01_create_user.sql
sqlplus system/<mot_de_passe> @sql/02_create_schema.sql

# 4. Adapter la configuration dans le script Python
#    (chemin de l'Instant Client, chaîne de connexion)
#    puis peupler la base
python scripts/03_populate_oracle_v4.py
```

### Ouvrir le dashboard

1. Ouvrir `powerbi/PL_Dashboard.pbix` dans Power BI Desktop
2. Ruban **Accueil → Actualiser** pour charger les données
3. Vérifier sur la page Contrôle Qualité que les cinq contrôles sont à 0

---

## 📊 Aperçu des pages

| Page | Public | Contenu |
|---|---|---|
| **Vue Exécutive** | Direction | KPI clés, tendance du CA, waterfall Revenue → Net Profit, répartition par BU |
| **Analyse P&L** | Contrôle de gestion | Matrice à drill-down, filtres multi-axes, traçabilité de l'origine des splits |
| **Contrôle Qualité** | IT / Comptabilité | Contrôles d'intégrité, comptes non mappés, réconciliation avec la balance |

---

## 🔒 Sécurité et données

- **Aucune donnée de production** n'est présente dans ce dépôt. Les données sont générées par le script Python.
- **Ne jamais committer** de credentials, chaînes de connexion réelles, fichiers d'export ou balances réelles. Le `.gitignore` fourni exclut les extensions sensibles.
- Le fichier `.pbix` peut être volumineux et contenir des données mises en cache : évaluer s'il doit être versionné ou distribué autrement (par ex. via les *releases*).

---

## 🗺️ Feuille de route

- [x] Base de données et génération de données mock
- [x] Modélisation en étoile et connexion Power BI
- [x] Mesures DAX (waterfall, time intelligence, splits)
- [x] Dashboard trois pages
- [x] Règles métier avancées (splits, VAS, contrôles)
- [x] Audit de conformité et corrections
- [x] Mécanisme d'exceptions (table de rejet)
- [ ] Bascule sur données de production
- [ ] Alimentation des exceptions réelles
- [ ] Publication sur le service Power BI

---

## 📝 Notes de conception

Quelques choix et enseignements techniques documentés en détail dans `docs/DOCUMENTATION_TECHNIQUE.md` :

- Les revenus sont stockés en négatif (convention classe 7) ; les mesures appliquent un facteur `-1`.
- Les clés de ventilation sont datées au premier jour du mois : les lookups utilisent `MIN(date)`, pas `MAX`.
- `REMOVEFILTERS(colonne)` est privilégié à `ALL(table)` pour préserver le contexte temporel dans les ratios.
- Les mesures VAS calculent directement depuis la colonne de montant plutôt que d'imbriquer une mesure déjà filtrée (évite les interférences de contextes de filtre).
- Le modèle gère trois segments (B2B / B2C / Wholesale) : les contrôles somment les trois, jamais `1 − B2B`.

---

## 📄 Licence

À définir selon le contexte de publication. En l'absence de licence explicite, ce dépôt est considéré comme tous droits réservés.

---

## 🙋 Auteur

Projet de stage en Business Intelligence — conception, développement et documentation de la solution complète.
