USE glowbase;

CREATE TABLE IF NOT EXISTS product_add_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id VARCHAR(50),
    product_name VARCHAR(255),
    action_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Existing INSERT trigger
DROP TRIGGER IF EXISTS after_product_insert;

DELIMITER //

CREATE TRIGGER after_product_insert
AFTER INSERT ON products
FOR EACH ROW
BEGIN
    INSERT INTO product_add_logs (
        product_id,
        product_name,
        action_type
    )
    VALUES (
        NEW.product_id,
        NEW.product_name,
        'INSERT'
    );
END //

DELIMITER ;

-- NEW DELETE trigger
DROP TRIGGER IF EXISTS after_product_delete;

DELIMITER //

CREATE TRIGGER after_product_delete
AFTER DELETE ON products
FOR EACH ROW
BEGIN
    INSERT INTO product_add_logs (
        product_id,
        product_name,
        action_type
    )
    VALUES (
        OLD.product_id,
        OLD.product_name,
        'DELETE'
    );
END //

DELIMITER ;