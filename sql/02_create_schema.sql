-- ============================================================
-- 02_create_schema.sql
-- ============================================================
-- A EXECUTER connecte en PNL_STAGE (pas en SYSTEM)
-- Cree les 9 tables du modele : 8 dimensions + 1 table de faits
-- ============================================================

-- Nettoyage : suppression des tables si elles existent deja
-- (utile pour rejouer le script en developpement)
BEGIN
   FOR t IN (SELECT table_name FROM user_tables
             WHERE table_name IN (
                'FACT_BALANCE','DIM_COMPTE','DIM_OFFRE','DIM_CDR',
                'DIM_BU','DIM_STRUCTURE_PL','DIM_REJET','DIM_CAPEX',
                'CLE_EQUIPEMENT','CLE_INCOMING','DIM_NEW_DIGITAL'))
   LOOP
      EXECUTE IMMEDIATE 'DROP TABLE ' || t.table_name || ' CASCADE CONSTRAINTS';
   END LOOP;
END;
/

-- ============================================================
-- DIMENSIONS
-- ============================================================

-- Business Units (5 valeurs : Mobile, Fixe, Entreprise, Digital, Wholesale)
CREATE TABLE dim_bu (
   bu_code      VARCHAR2(20)  PRIMARY KEY,
   bu_name      VARCHAR2(100) NOT NULL,
   bu_type      VARCHAR2(20)  -- B2B / B2C / Wholesale
);

-- Centres de responsabilite (rattaches a une BU)
CREATE TABLE dim_cdr (
   cdr_code     VARCHAR2(20)  PRIMARY KEY,
   cdr_name     VARCHAR2(150) NOT NULL,
   bu_code      VARCHAR2(20)  NOT NULL,
   CONSTRAINT fk_cdr_bu FOREIGN KEY (bu_code) REFERENCES dim_bu(bu_code)
);
CREATE INDEX ix_cdr_bu ON dim_cdr(bu_code);

-- Offres (Nature offre + Techno offre fusionnes)
CREATE TABLE dim_offre (
   offre_code   VARCHAR2(20)  PRIMARY KEY,
   offre_name   VARCHAR2(150),
   segment      VARCHAR2(20),  -- B2B / B2C / Wholesale
   techno       VARCHAR2(50)   -- Mobile / Fixed / Digital
);
CREATE INDEX ix_offre_segment ON dim_offre(segment);

-- Referentiel de mapping comptable (equivalent Mapping General de l'Excel)
CREATE TABLE dim_compte (
   compte_comptable  VARCHAR2(20)  PRIMARY KEY,
   descriptif        VARCHAR2(300),
   assets            VARCHAR2(150),
   assets_conso      VARCHAR2(150),
   liabilities       VARCHAR2(150),
   liabilities_conso VARCHAR2(150),
   pl_line           VARCHAR2(150),
   pl_conso          VARCHAR2(150),
   categorie         VARCHAR2(50),   -- Rev / Cos / Opex / Null
   ncoa_mapping      VARCHAR2(50)
);
CREATE INDEX ix_compte_pl_line ON dim_compte(pl_line);
CREATE INDEX ix_compte_categorie ON dim_compte(categorie);

-- Structure du waterfall P&L (les 221 lignes du reporting)
CREATE TABLE dim_structure_pl (
   pl_id         NUMBER(5)     PRIMARY KEY,
   ordre         NUMBER(5)     NOT NULL,
   section       VARCHAR2(50),   -- Revenue / COS / Opex / Sous-total
   niveau        NUMBER(2),      -- 1 = section, 2 = sous-total, 3 = ligne detail
   parent_id     NUMBER(5),
   libelle       VARCHAR2(150) NOT NULL,
   segment       VARCHAR2(20),
   type_calcul   VARCHAR2(20)    -- 'SUMIFS' / 'SPLIT' / 'FORMULA'
);

-- Mapping Capex
CREATE TABLE dim_capex (
   compte_comptable  VARCHAR2(20)  PRIMARY KEY,
   capex_category    VARCHAR2(100),
   capex_detail      VARCHAR2(150)
);

-- Exceptions de mapping (Rejet)
CREATE TABLE dim_rejet (
   cle_composite   VARCHAR2(60) PRIMARY KEY,  -- Compte+Offre+CDR concatenes
   compte          VARCHAR2(20),
   offre           VARCHAR2(20),
   cdr             VARCHAR2(20),
   pl_line         VARCHAR2(150),
   bu              VARCHAR2(20)
);

-- Cas particuliers Digital (New Digital de l'Excel)
CREATE TABLE dim_new_digital (
   cle_composite  VARCHAR2(60) PRIMARY KEY,   -- Compte&Offre
   compte         VARCHAR2(20),
   offre          VARCHAR2(20),
   pl_line        VARCHAR2(150),
   pl_conso       VARCHAR2(150),
   categorie      VARCHAR2(50)
);

-- Cles manuelles S4 : Ratios Equipement B2B/B2C par mois
CREATE TABLE cle_equipement (
   mois         DATE          NOT NULL,
   segment      VARCHAR2(10)  NOT NULL,
   ratio        NUMBER(6,4)   NOT NULL,
   CONSTRAINT pk_cle_equip PRIMARY KEY (mois, segment)
);

-- Cles manuelles S5 : Ratios Incoming/A2P/P2P B2B/B2C par mois
CREATE TABLE cle_incoming (
   mois         DATE          NOT NULL,
   intitule     VARCHAR2(50)  NOT NULL,
   segment      VARCHAR2(10)  NOT NULL,
   ratio        NUMBER(6,4)   NOT NULL,
   CONSTRAINT pk_cle_incoming PRIMARY KEY (mois, intitule, segment)
);

-- ============================================================
-- TABLE DE FAITS
-- ============================================================

-- Balance consolidee (12 mois x tous les comptes/CDR/offres)
CREATE TABLE fact_balance (
   id                NUMBER          GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
   mois              DATE            NOT NULL,
   compte_comptable  VARCHAR2(20)    NOT NULL,
   cdr_code          VARCHAR2(20),
   offre_code        VARCHAR2(20),
   bu_code           VARCHAR2(20),
   segment           VARCHAR2(20),
   pl_line           VARCHAR2(150),
   pl_conso          VARCHAR2(150),
   categorie         VARCHAR2(50),
   techno            VARCHAR2(50),
   type              VARCHAR2(30),
   montant_tnd       NUMBER(18,3)    NOT NULL,
   CONSTRAINT fk_fact_compte  FOREIGN KEY (compte_comptable) REFERENCES dim_compte(compte_comptable),
   CONSTRAINT fk_fact_cdr     FOREIGN KEY (cdr_code)         REFERENCES dim_cdr(cdr_code),
   CONSTRAINT fk_fact_offre   FOREIGN KEY (offre_code)       REFERENCES dim_offre(offre_code),
   CONSTRAINT fk_fact_bu      FOREIGN KEY (bu_code)          REFERENCES dim_bu(bu_code)
);

-- Index pour accelerer les requetes Power BI
CREATE INDEX ix_fact_mois    ON fact_balance(mois);
CREATE INDEX ix_fact_bu      ON fact_balance(bu_code);
CREATE INDEX ix_fact_cdr     ON fact_balance(cdr_code);
CREATE INDEX ix_fact_pl_line ON fact_balance(pl_line);
CREATE INDEX ix_fact_segment ON fact_balance(segment);

-- ============================================================
-- VERIFICATION
-- ============================================================
SELECT table_name, num_rows
FROM   user_tables
ORDER  BY table_name;

COMMIT;
