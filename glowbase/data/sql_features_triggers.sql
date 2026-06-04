USE glowbase;

-- Create log tables if they don't exist
CREATE TABLE IF NOT EXISTS product_add_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id VARCHAR(50),
    product_name VARCHAR(255),
    action_type VARCHAR(50),
    changed_fields TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS product_audit_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id VARCHAR(50),
    product_name VARCHAR(255),
    action_type VARCHAR(50),
    changed_fields TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- TRIGGER 1: AFTER INSERT - Logs when admin adds a product
-- =========================================================
DROP TRIGGER IF EXISTS after_product_insert;

DELIMITER //

CREATE TRIGGER after_product_insert
AFTER INSERT ON products
FOR EACH ROW
BEGIN
    INSERT INTO product_add_logs (
        product_id,
        product_name,
        action_type,
        changed_fields
    )
    VALUES (
        NEW.product_id,
        NEW.product_name,
        'INSERT',
        CONCAT('Added new product: ', NEW.product_name, ' ($', NEW.price_usd, ')')
    );
END //

DELIMITER ;

-- =========================================================
-- TRIGGER 2: AFTER UPDATE - Logs when admin edits a product
-- =========================================================
DROP TRIGGER IF EXISTS after_product_update;

DELIMITER //

CREATE TRIGGER after_product_update
AFTER UPDATE ON products
FOR EACH ROW
BEGIN
    DECLARE changes VARCHAR(2000);
    SET changes = '';
    
    -- Track product_name changes
    IF OLD.product_name != NEW.product_name THEN
        SET changes = CONCAT(changes, 'product_name: "', OLD.product_name, '" → "', NEW.product_name, '"; ');
    END IF;
    
    -- Track price changes
    IF OLD.price_usd != NEW.price_usd THEN
        SET changes = CONCAT(changes, 'price: $', OLD.price_usd, ' → $', NEW.price_usd, '; ');
    END IF;
    
    -- Track rating changes
    IF OLD.rating != NEW.rating THEN
        SET changes = CONCAT(changes, 'rating: ', IFNULL(OLD.rating, 0), ' → ', IFNULL(NEW.rating, 0), '; ');
    END IF;
    
    -- Track out_of_stock changes
    IF OLD.out_of_stock != NEW.out_of_stock THEN
        SET changes = CONCAT(changes, 'stock: ', IF(OLD.out_of_stock=1, 'Out', 'In'), ' → ', IF(NEW.out_of_stock=1, 'Out', 'In'), '; ');
    END IF;
    
    -- Track size changes
    IF IFNULL(OLD.size, '') != IFNULL(NEW.size, '') THEN
        SET changes = CONCAT(changes, 'size: "', IFNULL(OLD.size, 'NULL'), '" → "', IFNULL(NEW.size, 'NULL'), '"; ');
    END IF;
    
    -- Only insert if something actually changed
    IF changes != '' THEN
        INSERT INTO product_audit_logs (
            product_id,
            product_name,
            action_type,
            changed_fields
        )
        VALUES (
            NEW.product_id,
            NEW.product_name,
            'UPDATE',
            changes
        );
    END IF;
END //

DELIMITER ;

-- =========================================================
-- TRIGGER 3: AFTER DELETE - Logs when admin deletes a product
-- =========================================================
DROP TRIGGER IF EXISTS after_product_delete;

DELIMITER //

CREATE TRIGGER after_product_delete
AFTER DELETE ON products
FOR EACH ROW
BEGIN
    INSERT INTO product_audit_logs (
        product_id,
        product_name,
        action_type,
        changed_fields
    )
    VALUES (
        OLD.product_id,
        OLD.product_name,
        'DELETE',
        CONCAT('Deleted product: ', OLD.product_name, ' ($', OLD.price_usd, ')')
    );
END //

DELIMITER ;

-- =========================================================
-- Verify all triggers are created
-- =========================================================
SHOW TRIGGERS FROM glowbase;