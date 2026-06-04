USE glowbase;

-- First, see what categories you have
SELECT category_id, primary_category FROM categories LIMIT 10;

-- Populate product_categories based on product name patterns
-- Example: Products with 'Cream' get category_id 1 (Moisturizers)
INSERT INTO product_categories (product_id, category_id)
SELECT p.product_id, 1
FROM products p
WHERE LOWER(p.product_name) LIKE '%cream%'
AND NOT EXISTS (
    SELECT 1 FROM product_categories pc 
    WHERE pc.product_id = p.product_id AND pc.category_id = 1
);

-- Products with 'Cleanser' get category_id 9 (Cleansers)
INSERT INTO product_categories (product_id, category_id)
SELECT p.product_id, 9
FROM products p
WHERE LOWER(p.product_name) LIKE '%cleanser%'
AND NOT EXISTS (
    SELECT 1 FROM product_categories pc 
    WHERE pc.product_id = p.product_id AND pc.category_id = 9
);

-- Products with 'Serum' get category_id 2 (Treatments)
INSERT INTO product_categories (product_id, category_id)
SELECT p.product_id, 2
FROM products p
WHERE LOWER(p.product_name) LIKE '%serum%'
AND NOT EXISTS (
    SELECT 1 FROM product_categories pc 
    WHERE pc.product_id = p.product_id AND pc.category_id = 2
);

-- Check results
SELECT COUNT(*) AS total_mappings FROM product_categories;