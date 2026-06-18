import time

from flask import Blueprint, redirect, render_template

from db import get_mariadb_connection
from utils import is_admin_logged_in

admin_database_demo_bp = Blueprint("admin_database_demos", __name__)


@admin_database_demo_bp.route("/admin/sql-demo")
def sql_demo():
    if not is_admin_logged_in():
        return redirect("/admin/login")

    conn = get_mariadb_connection()
    cursor = conn.cursor(dictionary=True)

    demo_results = get_nested_query_demo_results(cursor)
    cursor.close()
    conn.close()

    return render_template("sql_demo.html", **demo_results)


@admin_database_demo_bp.route("/admin/trigger-demo")
def trigger_demo():
    if not is_admin_logged_in():
        return redirect("/admin/login")

    conn = get_mariadb_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT log_id, product_id, product_name, action_type, created_at
        FROM product_add_logs
        ORDER BY log_id DESC
        LIMIT 20
    """)
    add_logs = cursor.fetchall()

    cursor.execute("""
        SELECT log_id, product_id, product_name, action_type, changed_fields, created_at
        FROM product_audit_logs
        ORDER BY log_id DESC
        LIMIT 20
    """)
    audit_logs = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "trigger_demo.html",
        add_logs=add_logs,
        audit_logs=audit_logs
    )


@admin_database_demo_bp.route("/admin/view-index-demo")
def view_index_demo():
    if not is_admin_logged_in():
        return redirect("/admin/login")

    conn = get_mariadb_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT product_id, product_name, brand_name, price_usd, rating, reviews
        FROM product_summary_view
        WHERE rating >= 4.5
        ORDER BY rating DESC
        LIMIT 20
    """)
    view_results = cursor.fetchall()

    cursor.execute("SHOW INDEX FROM products")
    index_results = cursor.fetchall()

    cursor.execute("""
        EXPLAIN SELECT product_id, product_name, rating, price_usd
        FROM products IGNORE INDEX (idx_products_rating)
        WHERE rating >= 4.5
        ORDER BY rating DESC
    """)
    explain_no_index = cursor.fetchall()

    cursor.execute("""
        EXPLAIN SELECT product_id, product_name, rating, price_usd
        FROM products
        WHERE rating >= 4.5
        ORDER BY rating DESC
    """)
    explain_with_index = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "view_index_demo.html",
        view_results=view_results,
        index_results=index_results,
        explain_no_index=explain_no_index,
        explain_with_index=explain_with_index
    )


@admin_database_demo_bp.route("/admin/performance-demo")
def performance_demo():
    if not is_admin_logged_in():
        return redirect("/admin/login")

    conn = get_mariadb_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        EXPLAIN FORMAT=JSON
        SELECT p.product_id, p.product_name, b.brand_name, p.rating, p.price_usd
        FROM products p
        JOIN brands b ON p.brand_id = b.brand_id
        WHERE p.product_name LIKE '%Cream%'
        LIMIT 100
    """)
    with_index_result = cursor.fetchone()

    with_index_time, with_index_data = time_query(cursor, """
        SELECT p.product_id, p.product_name, b.brand_name, p.rating, p.price_usd
        FROM products p
        JOIN brands b ON p.brand_id = b.brand_id
        WHERE p.product_name LIKE '%Cream%'
        LIMIT 100
    """)

    price_query_time, price_query_data = time_query(cursor, """
        SELECT product_id, product_name, price_usd, rating
        FROM products
        WHERE price_usd BETWEEN 30 AND 60
        ORDER BY price_usd
        LIMIT 50
    """)

    cursor.execute("""
        EXPLAIN FORMAT=JSON
        SELECT product_id, product_name, price_usd, rating
        FROM products
        WHERE price_usd BETWEEN 30 AND 60
        ORDER BY price_usd
        LIMIT 50
    """)
    price_explain = cursor.fetchone()

    join_query_time, join_query_data = time_query(cursor, """
        SELECT p.product_name, b.brand_name, c.primary_category, p.rating
        FROM products p
        JOIN brands b ON p.brand_id = b.brand_id
        JOIN product_categories pc ON p.product_id = pc.product_id
        JOIN categories c ON pc.category_id = c.category_id
        WHERE p.rating >= 4.5
        ORDER BY p.rating DESC
        LIMIT 50
    """)

    cursor.execute("""
        EXPLAIN FORMAT=JSON
        SELECT p.product_name, b.brand_name, c.primary_category, p.rating
        FROM products p
        JOIN brands b ON p.brand_id = b.brand_id
        JOIN product_categories pc ON p.product_id = pc.product_id
        JOIN categories c ON pc.category_id = c.category_id
        WHERE p.rating >= 4.5
        ORDER BY p.rating DESC
        LIMIT 50
    """)
    join_explain = cursor.fetchone()

    cursor.execute("SHOW INDEX FROM products")
    indexes = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "performance_demo.html",
        with_index_time=round(with_index_time, 2),
        with_index_count=len(with_index_data),
        with_index_explain=with_index_result,
        price_query_time=round(price_query_time, 2),
        price_query_count=len(price_query_data),
        price_explain=price_explain,
        join_query_time=round(join_query_time, 2),
        join_query_count=len(join_query_data),
        join_explain=join_explain,
        indexes=indexes
    )


def get_nested_query_demo_results(cursor):
    cursor.execute("""
        SELECT p.product_id, p.product_name, b.brand_name, p.rating, p.price_usd
        FROM products p, brands b
        WHERE p.brand_id = b.brand_id
        AND p.rating > (SELECT AVG(rating) FROM products)
        ORDER BY p.rating DESC
        LIMIT 20
    """)
    above_average_products = cursor.fetchall()

    cursor.execute("""
        SELECT p.product_id, p.product_name, b.brand_name, p.rating, p.price_usd
        FROM products p, brands b
        WHERE p.brand_id = b.brand_id
        AND p.brand_id IN (
            SELECT brand_id
            FROM products
            GROUP BY brand_id
            HAVING COUNT(*) > 3
        )
        ORDER BY b.brand_name, p.product_name
        LIMIT 20
    """)
    popular_brand_products = cursor.fetchall()

    cursor.execute("""
        SELECT p.product_id, p.product_name, b.brand_name, p.price_usd, p.rating
        FROM products p, brands b
        WHERE p.brand_id = b.brand_id
        AND p.price_usd > (SELECT AVG(price_usd) FROM products)
        ORDER BY p.price_usd DESC
        LIMIT 20
    """)
    above_average_price_products = cursor.fetchall()

    cursor.execute("""
        SELECT b.brand_name, AVG(p.rating) AS avg_rating, COUNT(*) AS total_products
        FROM products p, brands b
        WHERE p.brand_id = b.brand_id
        GROUP BY b.brand_name
        HAVING AVG(p.rating) > (SELECT AVG(rating) FROM products)
        ORDER BY avg_rating DESC
        LIMIT 20
    """)
    high_rating_brands = cursor.fetchall()

    cursor.execute("""
        SELECT p.product_id, p.product_name, b.brand_name, p.rating, p.price_usd
        FROM products p, brands b
        WHERE p.brand_id = b.brand_id
        AND p.rating = (SELECT MAX(rating) FROM products)
        ORDER BY p.product_name
        LIMIT 20
    """)
    highest_rating_products = cursor.fetchall()

    cursor.execute("""
        SELECT p.product_id, p.product_name, b.brand_name, p.out_of_stock
        FROM products p, brands b
        WHERE p.brand_id = b.brand_id
        AND p.brand_id IN (
            SELECT brand_id
            FROM products
            WHERE out_of_stock = 1
        )
        ORDER BY b.brand_name, p.product_name
        LIMIT 20
    """)
    brands_with_out_of_stock_products = cursor.fetchall()

    cursor.execute("""
        SELECT p.product_id, p.product_name, b.brand_name,
               c.secondary_category, c.tertiary_category, p.rating
        FROM products p
        JOIN brands b ON p.brand_id = b.brand_id
        JOIN product_categories pc ON p.product_id = pc.product_id
        JOIN categories c ON pc.category_id = c.category_id
        WHERE pc.category_id IN (
            SELECT category_id
            FROM product_categories
            GROUP BY category_id
            HAVING COUNT(*) > 5
        )
        ORDER BY c.secondary_category, p.rating DESC
        LIMIT 20
    """)
    category_products = cursor.fetchall()

    return {
        "above_average_products": above_average_products,
        "popular_brand_products": popular_brand_products,
        "above_average_price_products": above_average_price_products,
        "high_rating_brands": high_rating_brands,
        "highest_rating_products": highest_rating_products,
        "brands_with_out_of_stock_products": brands_with_out_of_stock_products,
        "category_products": category_products,
    }


def time_query(cursor, query):
    start = time.time()
    cursor.execute(query)
    rows = cursor.fetchall()
    return (time.time() - start) * 1000, rows
