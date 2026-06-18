from flask import Blueprint, render_template

from db import get_mariadb_connection, get_mongo_collection

home_bp = Blueprint("home", __name__)


@home_bp.route("/")
def index():
    conn = get_mariadb_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total_products FROM products")
    total_products = cursor.fetchone()["total_products"]

    cursor.execute("SELECT COUNT(*) AS total_brands FROM brands")
    total_brands = cursor.fetchone()["total_brands"]

    cursor.execute("""
        SELECT primary_category
        FROM categories
        GROUP BY primary_category
        ORDER BY COUNT(*) DESC
        LIMIT 1
    """)
    row = cursor.fetchone()
    top_category = row["primary_category"] if row else "N/A"

    cursor.close()
    conn.close()

    reviews_collection = get_mongo_collection()
    total_reviews = reviews_collection.count_documents({})

    return render_template(
        "index.html",
        total_products=total_products,
        total_brands=total_brands,
        total_reviews=total_reviews,
        top_category=top_category
    )
