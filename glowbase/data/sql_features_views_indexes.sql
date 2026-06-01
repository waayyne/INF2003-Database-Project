USE glowbase;

DROP VIEW IF EXISTS product_summary_view;

CREATE VIEW product_summary_view AS
SELECT
    p.product_id,
    p.product_name,
    b.brand_name,
    p.price_usd,
    p.rating,
    p.reviews,
    p.loves_count,
    p.out_of_stock
FROM products p, brands b
WHERE p.brand_id = b.brand_id;

DROP INDEX IF EXISTS idx_products_product_name ON products;
DROP INDEX IF EXISTS idx_products_brand_id ON products;
DROP INDEX IF EXISTS idx_products_rating ON products;
DROP INDEX IF EXISTS idx_products_price ON products;

CREATE INDEX idx_products_product_name
ON products(product_name);

CREATE INDEX idx_products_brand_id
ON products(brand_id);

CREATE INDEX idx_products_rating
ON products(rating);

CREATE INDEX idx_products_price
ON products(price_usd);