from db import get_mariadb_connection
from utils import make_pasteable_sql, parse_number_range


def get_brand_id(cursor, brand_name):
    cursor.execute(
        "SELECT brand_id FROM brands WHERE brand_name = %s",
        (brand_name,)
    )
    row = cursor.fetchone()

    if row:
        return row[0]

    cursor.execute("SELECT MAX(brand_id) FROM brands")
    max_row = cursor.fetchone()
    max_brand_id = max_row[0] if max_row[0] is not None else 0
    new_brand_id = max_brand_id + 1

    cursor.execute(
        "INSERT INTO brands (brand_id, brand_name) VALUES (%s, %s)",
        (new_brand_id, brand_name)
    )

    return new_brand_id


def add_category_to_product(cursor, product_id, primary_category):
    if not primary_category:
        return

    primary_category = primary_category.strip()

    cursor.execute(
        """
        SELECT category_id
        FROM categories
        WHERE primary_category = %s
        LIMIT 1
        """,
        (primary_category,)
    )
    row = cursor.fetchone()

    if row:
        category_id = row[0]
    else:
        cursor.execute(
            """
            INSERT INTO categories (
                primary_category,
                secondary_category,
                tertiary_category
            )
            VALUES (%s, %s, %s)
            """,
            (primary_category, "", "")
        )
        category_id = cursor.lastrowid

    cursor.execute(
        """
        DELETE FROM product_categories
        WHERE product_id = %s
        """,
        (product_id,)
    )

    cursor.execute(
        """
        INSERT INTO product_categories (product_id, category_id)
        VALUES (%s, %s)
        """,
        (product_id, category_id)
    )


def get_product_category(cursor, product_id):
    cursor.execute(
        """
        SELECT c.primary_category, c.secondary_category, c.tertiary_category
        FROM product_categories pc, categories c
        WHERE pc.category_id = c.category_id
        AND pc.product_id = %s
        LIMIT 1
        """,
        (product_id,)
    )
    row = cursor.fetchone()

    if row:
        return {
            "primary_category": row["primary_category"] or "",
            "secondary_category": row["secondary_category"] or "",
            "tertiary_category": row["tertiary_category"] or ""
        }

    return {
        "primary_category": "",
        "secondary_category": "",
        "tertiary_category": ""
    }


def get_product_extra_text(cursor, product_id):
    cursor.execute(
        "SELECT ingredients FROM product_ingredients WHERE product_id = %s",
        (product_id,)
    )
    ingredient_row = cursor.fetchone()

    cursor.execute(
        "SELECT highlights FROM product_highlights WHERE product_id = %s",
        (product_id,)
    )
    highlight_row = cursor.fetchone()

    ingredients = ingredient_row["ingredients"] if ingredient_row else ""
    highlights = highlight_row["highlights"] if highlight_row else ""

    return ingredients or "", highlights or ""


def get_product_by_id(product_id):
    conn = get_mariadb_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            p.product_id,
            p.product_name,
            p.brand_id,
            b.brand_name,
            p.loves_count,
            p.rating,
            p.reviews,
            p.size,
            p.variation_type,
            p.variation_value,
            p.variation_desc,
            p.price_usd,
            p.value_price_usd,
            p.sale_price_usd,
            p.limited_edition,
            p.is_new AS new,
            p.online_only,
            p.out_of_stock,
            p.sephora_exclusive
        FROM products p, brands b
        WHERE p.brand_id = b.brand_id
        AND p.product_id = %s
        """,
        (product_id,)
    )

    product = cursor.fetchone()

    if product:
        cursor.execute("""
            SELECT c.category_id, c.primary_category, c.secondary_category, c.tertiary_category
            FROM product_categories pc
            JOIN categories c ON pc.category_id = c.category_id
            WHERE pc.product_id = %s
        """, (product_id,))

        product["categories"] = cursor.fetchall()
        ingredients, highlights = get_product_extra_text(cursor, product_id)
        product["ingredients"] = ingredients
        product["highlights"] = highlights

    cursor.close()
    conn.close()

    return product


def get_distinct_brands(cursor):
    cursor.execute("SELECT DISTINCT brand_name FROM brands ORDER BY brand_name")
    return [row["brand_name"] for row in cursor.fetchall()]


def get_linked_categories(cursor):
    cursor.execute("""
        SELECT DISTINCT category_name
        FROM (
            SELECT c.primary_category AS category_name
            FROM products p
            JOIN product_categories pc ON p.product_id = pc.product_id
            JOIN categories c ON pc.category_id = c.category_id
            WHERE c.primary_category IS NOT NULL AND c.primary_category != ''

            UNION

            SELECT c.secondary_category AS category_name
            FROM products p
            JOIN product_categories pc ON p.product_id = pc.product_id
            JOIN categories c ON pc.category_id = c.category_id
            WHERE c.secondary_category IS NOT NULL AND c.secondary_category != ''

            UNION

            SELECT c.tertiary_category AS category_name
            FROM products p
            JOIN product_categories pc ON p.product_id = pc.product_id
            JOIN categories c ON pc.category_id = c.category_id
            WHERE c.tertiary_category IS NOT NULL AND c.tertiary_category != ''
        ) AS linked_categories
        ORDER BY category_name
    """)
    return [row["category_name"] for row in cursor.fetchall()]


def build_product_filter_query(filters, order_by="p.product_name", limit=100, admin=False):
    params = []
    select_columns = """
            p.product_id,
            p.product_name,
            b.brand_name,
            p.loves_count,
            p.rating,
            p.reviews,
            p.size,
            p.price_usd,
            p.out_of_stock,
            GROUP_CONCAT(DISTINCT c.primary_category SEPARATOR ', ') AS categories
    """

    if admin:
        select_columns = """
            p.product_id,
            p.product_name,
            b.brand_name,
            p.price_usd,
            p.rating,
            p.reviews,
            p.out_of_stock,
            GROUP_CONCAT(DISTINCT c.primary_category SEPARATOR ', ') AS categories
        """

    query = f"""
        SELECT
            {select_columns}
        FROM products p
        JOIN brands b ON p.brand_id = b.brand_id
        LEFT JOIN product_categories pc ON p.product_id = pc.product_id
        LEFT JOIN categories c ON pc.category_id = c.category_id
    """

    where_clauses = []

    if filters.get("search"):
        where_clauses.append("p.product_name LIKE %s")
        params.append("%" + filters["search"] + "%")

    if filters.get("brand"):
        where_clauses.append("b.brand_name = %s")
        params.append(filters["brand"])

    if filters.get("category"):
        where_clauses.append("""
            (
                c.primary_category = %s
                OR c.secondary_category = %s
                OR c.tertiary_category = %s
            )
        """)
        params.extend([filters["category"], filters["category"], filters["category"]])

    rating_range = parse_number_range(filters.get("rating"))
    if rating_range:
        min_rating, max_rating = rating_range
        where_clauses.append("p.rating >= %s AND p.rating <= %s")
        params.extend([min_rating, max_rating])

    price_range = parse_number_range(filters.get("price"))
    if price_range:
        min_price, max_price = price_range
        where_clauses.append("p.price_usd >= %s AND p.price_usd <= %s")
        params.extend([min_price, max_price])

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    query += f" GROUP BY p.product_id ORDER BY {order_by} LIMIT {limit}"
    return query, params, make_pasteable_sql(query, params)


def get_product_select_options(limit=300):
    conn = get_mariadb_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT product_id, product_name
        FROM products
        ORDER BY product_name
        LIMIT %s
    """, (limit,))
    products = cursor.fetchall()

    cursor.close()
    conn.close()

    return products


def increment_product_review_count(product_id):
    conn = get_mariadb_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT reviews FROM products WHERE product_id = %s",
        (product_id,)
    )
    row = cursor.fetchone()

    current_reviews = row["reviews"] if row and row["reviews"] else 0
    new_review_count = current_reviews + 1

    cursor.execute(
        "UPDATE products SET reviews = %s WHERE product_id = %s",
        (new_review_count, product_id)
    )

    conn.commit()
    cursor.close()
    conn.close()


def get_valid_product_ids():
    conn = get_mariadb_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT product_id FROM products")
    product_ids = [str(row["product_id"]) for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    return product_ids
