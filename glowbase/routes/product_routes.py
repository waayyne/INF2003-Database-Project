from flask import Blueprint, render_template, request

from db import get_mariadb_connection
from services.products import (
    build_product_filter_query,
    get_distinct_brands,
    get_linked_categories,
    get_product_by_id,
)
from services.reviews import get_product_chemicals, get_reviews_by_product_id

product_bp = Blueprint("products", __name__)


@product_bp.route("/products")
def products():
    filters = {
        "search": request.args.get("search", ""),
        "brand": request.args.get("brand", ""),
        "category": request.args.get("category", ""),
        "rating": request.args.get("rating", ""),
        "price": request.args.get("price", ""),
    }

    conn = get_mariadb_connection()
    cursor = conn.cursor(dictionary=True)

    query, params, sql_statement_used = build_product_filter_query(filters)
    cursor.execute(query, params)
    product_list = cursor.fetchall()

    brands = get_distinct_brands(cursor)
    categories = get_linked_categories(cursor)

    cursor.close()
    conn.close()

    return render_template(
        "products.html",
        products=product_list,
        brands=brands,
        categories=categories,
        search=filters["search"],
        selected_brand=filters["brand"],
        selected_category=filters["category"],
        selected_rating=filters["rating"],
        selected_price=filters["price"],
        sql_statement_used=sql_statement_used,
    )


@product_bp.route("/product/<product_id>")
def product_detail(product_id):
    product = get_product_by_id(product_id)

    if not product:
        return "Product not found.", 404

    product["chemicals"] = get_product_chemicals(product_id)
    reviews = get_reviews_by_product_id(product_id)

    return render_template(
        "product_detail.html",
        product=product,
        reviews=reviews
    )


@product_bp.route("/category/<category_name>")
def category_products(category_name):
    conn = get_mariadb_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT DISTINCT
            p.product_id,
            p.product_name,
            b.brand_name,
            p.price_usd,
            p.rating,
            p.out_of_stock
        FROM products p
        JOIN brands b ON p.brand_id = b.brand_id
        JOIN product_categories pc ON p.product_id = pc.product_id
        JOIN categories c ON pc.category_id = c.category_id
        WHERE c.primary_category = %s
           OR c.secondary_category = %s
           OR c.tertiary_category = %s
        ORDER BY p.rating DESC
        LIMIT 50
    """, (category_name, category_name, category_name))

    product_list = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template(
        "category_products.html",
        products=product_list,
        category=category_name
    )
