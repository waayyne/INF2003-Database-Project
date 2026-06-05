USE glowbase;

-- =========================================================
-- Populate product_categories junction table
-- Uses INSERT INTO ... SELECT ... WHERE LIKE pattern
-- Products can belong to multiple categories (many-to-many)
-- Safe to re-run: clears existing data first
-- =========================================================

DELETE FROM product_categories;

-- ---------------------------------------------------------
-- Category 2: Treatments (serums, peels, acne treatments)
-- ---------------------------------------------------------
INSERT INTO product_categories (product_id, category_id)
SELECT p.product_id, 2
FROM products p
WHERE LOWER(p.product_name) LIKE '%serum%'
   OR LOWER(p.product_name) LIKE '%retinol%'
   OR LOWER(p.product_name) LIKE '%vitamin c%'
   OR LOWER(p.product_name) LIKE '%peel%'
   OR LOWER(p.product_name) LIKE '%glycolic%'
   OR LOWER(p.product_name) LIKE '%niacinamide%'
   OR LOWER(p.product_name) LIKE '%brightening%'
   OR LOWER(p.product_name) LIKE '%blemish%'
   OR LOWER(p.product_name) LIKE '%acne%';

-- ---------------------------------------------------------
-- Category 3: Eye Care
-- ---------------------------------------------------------
INSERT INTO product_categories (product_id, category_id)
SELECT p.product_id, 3
FROM products p
WHERE (LOWER(p.product_name) LIKE '%eye%'
    OR LOWER(p.product_name) LIKE '%lash%')
AND NOT EXISTS (
    SELECT 1 FROM product_categories pc
    WHERE pc.product_id = p.product_id AND pc.category_id = 3
);

-- ---------------------------------------------------------
-- Category 8: Lip Balms & Treatments
-- ---------------------------------------------------------
INSERT INTO product_categories (product_id, category_id)
SELECT p.product_id, 8
FROM products p
WHERE (LOWER(p.product_name) LIKE '%lip balm%'
    OR LOWER(p.product_name) LIKE '%lip treatment%'
    OR LOWER(p.product_name) LIKE '%lip mask%')
AND NOT EXISTS (
    SELECT 1 FROM product_categories pc
    WHERE pc.product_id = p.product_id AND pc.category_id = 8
);

-- ---------------------------------------------------------
-- Category 9: Cleansers (washes, scrubs, toners, exfoliators)
-- ---------------------------------------------------------
INSERT INTO product_categories (product_id, category_id)
SELECT p.product_id, 9
FROM products p
WHERE (LOWER(p.product_name) LIKE '%cleanser%'
    OR LOWER(p.product_name) LIKE '%cleansing%'
    OR LOWER(p.product_name) LIKE '%face wash%'
    OR LOWER(p.product_name) LIKE '%facial soap%'
    OR LOWER(p.product_name) LIKE '%scrub%'
    OR LOWER(p.product_name) LIKE '%exfoliat%'
    OR LOWER(p.product_name) LIKE '%toner%'
    OR LOWER(p.product_name) LIKE '%micellar%'
    OR LOWER(p.product_name) LIKE '%makeup remover%')
AND NOT EXISTS (
    SELECT 1 FROM product_categories pc
    WHERE pc.product_id = p.product_id AND pc.category_id = 9
);

-- ---------------------------------------------------------
-- Category 40: Masks
-- ---------------------------------------------------------
INSERT INTO product_categories (product_id, category_id)
SELECT p.product_id, 40
FROM products p
WHERE (LOWER(p.product_name) LIKE '%mask%'
    OR LOWER(p.product_name) LIKE '%masque%')
AND NOT EXISTS (
    SELECT 1 FROM product_categories pc
    WHERE pc.product_id = p.product_id AND pc.category_id = 40
);

-- ---------------------------------------------------------
-- Category 59: Sunscreen
-- ---------------------------------------------------------
INSERT INTO product_categories (product_id, category_id)
SELECT p.product_id, 59
FROM products p
WHERE (LOWER(p.product_name) LIKE '%spf%'
    OR LOWER(p.product_name) LIKE '%sunscreen%'
    OR LOWER(p.product_name) LIKE '%sun protection%')
AND NOT EXISTS (
    SELECT 1 FROM product_categories pc
    WHERE pc.product_id = p.product_id AND pc.category_id = 59
);

-- ---------------------------------------------------------
-- Category 109: Self Tanners
-- ---------------------------------------------------------
INSERT INTO product_categories (product_id, category_id)
SELECT p.product_id, 109
FROM products p
WHERE (LOWER(p.product_name) LIKE '%self tan%'
    OR LOWER(p.product_name) LIKE '%tanning%'
    OR LOWER(p.product_name) LIKE '%bronzing drop%')
AND NOT EXISTS (
    SELECT 1 FROM product_categories pc
    WHERE pc.product_id = p.product_id AND pc.category_id = 109
);

-- ---------------------------------------------------------
-- Category 1: Moisturizers (broad fallback — catches anything
-- hydrating that wasn't already categorised above)
-- ---------------------------------------------------------
INSERT INTO product_categories (product_id, category_id)
SELECT p.product_id, 1
FROM products p
WHERE (LOWER(p.product_name) LIKE '%moisturizer%'
    OR LOWER(p.product_name) LIKE '%moisturising%'
    OR LOWER(p.product_name) LIKE '%cream%'
    OR LOWER(p.product_name) LIKE '%lotion%'
    OR LOWER(p.product_name) LIKE '%gel%'
    OR LOWER(p.product_name) LIKE '%mist%'
    OR LOWER(p.product_name) LIKE '%essence%'
    OR LOWER(p.product_name) LIKE '%hydrat%'
    OR LOWER(p.product_name) LIKE '%face oil%'
    OR LOWER(p.product_name) LIKE '%facial oil%'
    OR LOWER(p.product_name) LIKE '%argan oil%'
    OR LOWER(p.product_name) LIKE '%watery oil%'
    OR LOWER(p.product_name) LIKE '%face butter%'
    OR LOWER(p.product_name) LIKE '%night%'
    OR LOWER(p.product_name) LIKE '%balm%'
    OR LOWER(p.product_name) LIKE '%sorbet%'
    OR LOWER(p.product_name) LIKE '%radiance pad%'
    OR LOWER(p.product_name) LIKE '%facial spray%'
    OR LOWER(p.product_name) LIKE '%water facial%'
    OR LOWER(p.product_name) LIKE '%skin perfector%')
AND NOT EXISTS (
    SELECT 1 FROM product_categories pc
    WHERE pc.product_id = p.product_id AND pc.category_id = 1
);

-- ---------------------------------------------------------
-- Fallback: any product still with no category -> Moisturizers
-- ---------------------------------------------------------
INSERT INTO product_categories (product_id, category_id)
SELECT p.product_id, 1
FROM products p
WHERE NOT EXISTS (
    SELECT 1 FROM product_categories pc
    WHERE pc.product_id = p.product_id
);

-- ---------------------------------------------------------
-- Verify results
-- ---------------------------------------------------------
SELECT COUNT(*) AS total_mappings FROM product_categories;

SELECT c.secondary_category, COUNT(*) AS product_count
FROM product_categories pc
JOIN categories c ON pc.category_id = c.category_id
GROUP BY c.secondary_category
ORDER BY product_count DESC;