# Guide utilisateur — Dashboard P&L Tunisie Telecom

---

## 1. À quoi sert ce dashboard

Ce dashboard automatise le suivi du compte de résultat (P&L) de Tunisie Telecom. Il remplace le processus manuel actuel basé sur des extractions Excel retravaillées à la main.

Concrètement, il permet de :
- consulter le P&L consolidé et son évolution mois par mois ;
- analyser la rentabilité par Business Unit, Centre de Responsabilité, offre, technologie et segment (B2B / B2C / Wholesale) ;
- vérifier automatiquement l'intégrité des chiffres (réconciliation avec la balance comptable) ;
- détecter les anomalies de mapping sans intervention humaine.

Le principe fondamental : **aucune valeur n'est saisie à la main**. Toutes les données proviennent de la base Oracle et sont recalculées à chaque actualisation.

---

## 2. Comment est organisé le dashboard

Le rapport comporte **trois pages**, accessibles par les boutons de navigation en haut de chaque page.

### Page 1 — Vue Exécutive

**Pour qui** : direction, décideurs.

**Ce qu'elle montre** : la situation financière en un coup d'œil.

| Élément | Signification |
|---|---|
| Cartes KPI (haut) | Total Revenue, Gross Margin %, EBITDA, EBITDA %, Net Profit, Statut Fiabilité |
| Courbe « Évolution du chiffre d'affaires » | Tendance mensuelle du CA |
| Waterfall « De Revenue à Net Profit » | Décomposition : comment on passe du revenu au résultat net (COS, OPEX, D&A) |
| Treemap par Business Unit | Répartition du CA entre Mobile, Digital & VAS, Wholesale, Enterprise, Fixed |

**Comment la lire** : commencez par la carte « Statut Fiabilité ». Si elle est verte (« Tous les contrôles OK »), les chiffres sont réconciliés avec la balance. Puis lisez les KPI de gauche à droite, du revenu au résultat.

### Page 2 — Analyse P&L

**Pour qui** : contrôleurs de gestion, analystes.

**Ce qu'elle permet** : explorer le détail et filtrer selon plusieurs axes.

**Les filtres disponibles**  :
- **Business Unit** — Mobile, Digital, Wholesale, Enterprise, Fixed
- **CDR** — Centre de Responsabilité
- **Segment** — B2B, B2C, Wholesale
- **Date** — période
- **Offre** — les différentes offres commerciales
- **Type** — Prepaid / Postpaid
- **Technologie** — Mobile / Fixed / Digital

**La matrice centrale** : elle affiche chaque ligne du P&L par mois. Cliquez sur le **+** à gauche d'une ligne pour la détailler (drill-down) jusqu'au compte comptable.

**La table « Origine Split »** : pour chaque ligne de revenu, elle indique comment le montant B2B/B2C a été calculé :
- *Type I — Mapping automatique* : l'offre est directement rattachée à un segment
- *Type II — Ratio dynamique* : le montant global est ventilé selon un ratio calculé chaque mois
- *Type III — Clé manuelle* : la ventilation vient d'une table de clés fournie par le contrôle de gestion

### Page 3 — Contrôle Qualité

**Pour qui** : IT, comptabilité, audit.

**Ce qu'elle détecte** : les anomalies qui compromettraient la fiabilité des chiffres.

| Élément | À surveiller |
|---|---|
| Nb Comptes Non Mappés | Doit tendre vers 0. Tout compte non mappé est listé dans la table du bas. |
| Nb Lignes CDR Manquant | Lignes sans Centre de Responsabilité renseigné |
| Écart Check Revenue | **Doit être 0** |
| Statut Checks | Vert = tous les contrôles passent |
| Table des checks par mois | Check Rev, Check Opex, Check Cos, Check VAS — tous à 0 |

**Que faire si un check n'est pas à 0** : voir la section 4 ci-dessous.

---

## 3. Rafraîchir les données chaque mois

Le dashboard ne se met pas à jour tout seul. Chaque mois, après l'arrivée de la nouvelle balance dans Oracle :

1. Ouvrir le fichier `PL_Dashboard.pbix` dans Power BI Desktop
2. Ruban **Accueil → Actualiser**
3. Attendre la fin du chargement (quelques secondes à quelques minutes selon le volume)
4. Aller sur la **Page 3** et vérifier que les 5 contrôles affichent 0 et que le Statut est vert
5. Sauvegarder le fichier

Le nouveau mois apparaît automatiquement dès qu'il existe dans la balance Oracle. Aucune manipulation supplémentaire n'est nécessaire.

---

## 4. Que faire si un contrôle est en erreur

### Le Statut Fiabilité est « À vérifier » / rouge

Cela signifie qu'au moins un compte comptable mouvementé n'est pas mappé à une ligne du P&L.

**Marche à suivre** :
1. Aller sur la Page 3
2. Consulter la table des comptes non mappés (en bas à gauche)
3. Noter les numéros de compte concernés
4. Les transmettre à l'équipe en charge du référentiel de mapping pour rattachement
5. Une fois le mapping corrigé dans la source, actualiser : le compte disparaît de la liste

### Un « Check » (Rev, Opex, Cos, VAS) n'est pas à 0

Cela signale un écart entre le P&L reconstitué et la balance comptable.

**Marche à suivre** :
1. Identifier quel check est concerné (Rev, Opex, Cos ou VAS)
2. Sur la Page 3, repérer le ou les mois où l'écart apparaît (table des checks par mois)
3. Vérifier dans la balance source si un compte a changé de catégorie ou de mapping
4. Contacter le référent technique du dashboard si l'écart persiste

---

## 5. Mettre à jour les clés manuelles (S4 et S5)

Certaines ventilations B2B/B2C reposent sur des tables de clés fournies **chaque mois par le contrôle de gestion** :
- **Clé Équipement (S4)** : ratios pour les ventes de terminaux
- **Clé Incoming (S5)** : ratios pour les revenus d'interconnexion

**Procédure de mise à jour** :
1. Recevoir le fichier Excel des clés du mois auprès du contrôle de gestion
2. Injecter les nouvelles lignes dans les tables `Cle_Equipement` et `Cle_Incoming` de la base Oracle (colonne Mois, Segment, Intitulé, Ratio)
3. Actualiser Power BI
4. Vérifier sur la Page 2 que les ratios du nouveau mois sont pris en compte

**Important** : sans ces clés, les revenus Équipement et Incoming du mois concerné ne pourront pas être ventilés entre B2B et B2C.

---

## 6. Comprendre les filtres Type et Technologie

Deux filtres peuvent prêter à confusion :

- **Technologie** : Mobile / Fixed / Digital — la nature technique du service
- **Type** : Prepaid / Postpaid — le mode d'abonnement

Le cahier des charges parlait d'un filtre « Type (Mobile, Fixe...) ». En réalité, cette notion correspond à la **Technologie** dans le modèle. Le champ **Type** porte l'information Prepaid/Postpaid. Les deux filtres sont proposés pour couvrir tous les besoins d'analyse.

---

## 7. Questions fréquentes

**Pourquoi certains mois affichent-ils 0 % de croissance ?**
Les données commencent en janvier 2025. Le premier mois n'a pas de mois précédent pour calculer une croissance ; de même, la croissance annuelle (YoY) n'est disponible qu'à partir de janvier 2026.

**Pourquoi le VAS est-il séparé en « Services » et « Apigee » ?**
Ce sont deux activités distinctes avec des comptes différents. Le cahier des charges demande explicitement de les suivre séparément. Apigee (plateforme de gestion d'API) dégage une marge nette élevée ; les VAS Services sont proches de l'équilibre.

**Comment ajouter un nouveau mois ?**
Il suffit qu'il existe dans la balance Oracle, puis d'actualiser. Aucune configuration manuelle.

**Puis-je exporter les données d'un visuel ?**
Oui : cliquez sur les « … » du visuel → Exporter les données. Le fichier respecte les filtres appliqués. Note : dans un export CSV, les mois apparaissent en lignes (format « à plat »), pas en colonnes comme à l'écran.

---


*Ce dashboard a été développé dans le cadre d'un projet de stage visant à automatiser et fiabiliser le reporting P&L. Pour la documentation technique (architecture, mesures, maintenance avancée), se référer au document DOCUMENTATION_TECHNIQUE.md.*
