-- Migration pour le flux tablette (aglae-form)
-- À exécuter sur la base MySQL avant de déployer l'endpoint /api/v1/tablet
--
--   mysql -h <DB_HOST> -u <DB_USER> -p <DB_NAME> < migrations/2026-07-21_tablet_form.sql

-- 1) Les formules tablette n'ont pas de fiche scannée
ALTER TABLE formula
    MODIFY COLUMN file_id INT NULL;

-- 2) Traçabilité et quantité choisie sur la formule
ALTER TABLE formula
    ADD COLUMN quantity VARCHAR(20) NULL,
    ADD COLUMN source VARCHAR(20) NOT NULL DEFAULT 'ocr';

-- 3) Champs collectés par le questionnaire tablette absents de customers
ALTER TABLE customers
    ADD COLUMN gender VARCHAR(10) NULL,
    ADD COLUMN birth_date DATE NULL,
    ADD COLUMN has_allergy TINYINT(1) NULL,
    ADD COLUMN liability_accepted TINYINT(1) NULL,
    ADD COLUMN rgpd_consent TINYINT(1) NULL;
