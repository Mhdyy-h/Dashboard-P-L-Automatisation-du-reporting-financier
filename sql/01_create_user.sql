-- ============================================================
-- 01_create_user.sql
-- ============================================================
-- A EXECUTER UNE SEULE FOIS, connecté en SYSTEM
-- Cree un utilisateur dedie au projet P&L avec ses droits
-- ============================================================

-- Suppression eventuelle d'une ancienne version (utile si on rejoue le script)
BEGIN
   EXECUTE IMMEDIATE 'DROP USER pnl_stage CASCADE';
EXCEPTION
   WHEN OTHERS THEN
      IF SQLCODE != -1918 THEN RAISE; END IF;  -- ignore "user does not exist"
END;
/

-- Creation de l'utilisateur
CREATE USER pnl_stage
   IDENTIFIED BY pnl_stage_2026
   DEFAULT TABLESPACE users
   TEMPORARY TABLESPACE temp
   QUOTA UNLIMITED ON users;

-- Droits necessaires pour ce projet
GRANT CONNECT, RESOURCE TO pnl_stage;
GRANT CREATE VIEW TO pnl_stage;
GRANT CREATE SESSION TO pnl_stage;
GRANT CREATE TABLE TO pnl_stage;
GRANT CREATE SEQUENCE TO pnl_stage;

-- Desactiver expiration du mot de passe pour cet utilisateur aussi
ALTER USER pnl_stage IDENTIFIED BY pnl_stage_2026;

-- Verification
SELECT username, account_status, default_tablespace
FROM   dba_users
WHERE  username = 'PNL_STAGE';
