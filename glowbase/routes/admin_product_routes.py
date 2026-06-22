from flask import Blueprint, redirect, render_template, request

from db import get_mariadb_connection
from services.products import (
    add_category_to_product,
    build_product_filter_query,
    get_brand_id,
    get_distinct_brands,
    get_linked_categories,
)
from utils import is_admin_logged_in

admin_product_bp = Blueprint("admin_products", __name__)


@admin_product_bp.route("/admin/products")
def admin_products():
    if not is_admin_logged_in():
        return redirect("/admin/login")

    filters = {
        "search": request.args.get("search", ""),
        "brand": request.args.get("brand", ""),
        "category": request.args.get("category", ""),
        "rating": request.args.get("rating", ""),
        "price": request.args.get("price", ""),
    }

    conn = get_mariadb_connection()
    cursor = conn.cursor(dictionary=True)

    query, params, sql_statement_used = build_product_filter_query(
        filters,
        order_by="p.product_id",
        admin=True
    )
    cursor.execute(query, params)
    product_list = cursor.fetchall()

    brands = get_distinct_brands(cursor)
    categories = get_linked_categories(cursor)

    cursor.close()
    conn.close()

    return render_template(
        "admin_products.html",
        products=product_list,
        brands=brands,
        categories=categories,
        search=filters["search"],
        selected_brand=filters["brand"],
        selected_category=filters["category"],
        selected_rating=filters["rating"],
        selected_price=filters["price"],
        sql_statement_used=sql_statement_used
    )


@admin_product_bp.route("/admin/products/add", methods=["GET", "POST"])
def admin_add_product():
    if not is_admin_logged_in():
        return redirect("/admin/login")

    if request.method == "POST":
        conn = get_mariadb_connection()
        cursor = conn.cursor()

        product_id = request.form.get("product_id")
        product_name = request.form.get("product_name")
        brand_name = request.form.get("brand_name")

        cursor.execute(
            "SELECT product_id FROM products WHERE product_id = %s",
            (product_id,)
        )
        existing_product = cursor.fetchone()

        if existing_product:
            cursor.close()
            conn.close()
            return render_template(
                "admin_add_product.html",
                error="Product ID already exists. Please use a different Product ID.",
                form=request.form
            )

        primary_category = request.form.get("primary_category") or ""
        price_usd = request.form.get("price_usd") or 0
        rating = round(float(request.form.get("rating") or 0), 2)
        size = request.form.get("size") or ""
        out_of_stock = request.form.get("out_of_stock") or 0
        ingredients = request.form.get("ingredients") or ""
        highlights = request.form.get("highlights") or ""

        brand_id = get_brand_id(cursor, brand_name)

        cursor.execute(
            """
            INSERT INTO products (
                product_id, product_name, brand_id, loves_count, rating,
                reviews, size, variation_type, variation_value, variation_desc,
                price_usd, value_price_usd, sale_price_usd, limited_edition,
                is_new, online_only, out_of_stock, sephora_exclusive,
                child_count, child_max_price, child_min_price
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s
            )
            """,
            (
                product_id, product_name, brand_id, 0, rating,
                0, size, "", "", "", price_usd, None, None, 0, 0, 0,
                out_of_stock, 0, 0, None, None
            )
        )

        add_category_to_product(cursor, product_id, primary_category)

        cursor.execute(
            """
            INSERT INTO product_ingredients (product_id, ingredients)
            VALUES (%s, %s)
            """,
            (product_id, ingredients)
        )

        cursor.execute(
            """
            INSERT INTO product_highlights (product_id, highlights)
            VALUES (%s, %s)
            """,
            (product_id, highlights)
        )

        conn.commit()
        cursor.close()
        conn.close()

        return redirect("/admin/products")

    return render_template("admin_add_product.html")


@admin_product_bp.route("/admin/products/edit/<product_id>", methods=["GET", "POST"])
def admin_edit_product(product_id):
    if not is_admin_logged_in():
        return redirect("/admin/login")

    conn = get_mariadb_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        try:
            product_name = request.form.get("product_name")
            price_usd = request.form.get("price_usd") or 0
            rating = round(float(request.form.get("rating") or 0), 2)
            size = request.form.get("size") or ""
            out_of_stock = request.form.get("out_of_stock") or 0
            loves_count = request.form.get("loves_count") or 0
            reviews = request.form.get("reviews") or 0
            variation_type = request.form.get("variation_type") or ""
            variation_value = request.form.get("variation_value") or ""
            variation_desc = request.form.get("variation_desc") or ""
            value_price_usd = request.form.get("value_price_usd") or None
            sale_price_usd = request.form.get("sale_price_usd") or None
            limited_edition = request.form.get("limited_edition") or 0
            is_new = request.form.get("is_new") or 0
            online_only = request.form.get("online_only") or 0
            sephora_exclusive = request.form.get("sephora_exclusive") or 0
            child_count = request.form.get("child_count") or 0
            child_max_price = request.form.get("child_max_price") or None
            child_min_price = request.form.get("child_min_price") or None

            if value_price_usd == "":
                value_price_usd = None
            if sale_price_usd == "":
                sale_price_usd = None
            if child_max_price == "":
                child_max_price = None
            if child_min_price == "":
                child_min_price = None

            cursor.execute(
                """
                UPDATE products
                SET product_name = %s,
                    price_usd = %s,
                    rating = %s,
                    size = %s,
                    out_of_stock = %s,
                    loves_count = %s,
                    reviews = %s,
                    variation_type = %s,
                    variation_value = %s,
                    variation_desc = %s,
                    value_price_usd = %s,
                    sale_price_usd = %s,
                    limited_edition = %s,
                    is_new = %s,
                    online_only = %s,
                    sephora_exclusive = %s,
                    child_count = %s,
                    child_max_price = %s,
                    child_min_price = %s
                WHERE product_id = %s
                """,
                (
                    product_name, price_usd, rating, size, out_of_stock,
                    loves_count, reviews, variation_type, variation_value,
                    variation_desc, value_price_usd, sale_price_usd,
                    limited_edition, is_new, online_only, sephora_exclusive,
                    child_count, child_max_price, child_min_price, product_id
                )
            )

            update_product_text_table(cursor, "product_ingredients", "ingredients", product_id)
            update_product_text_table(cursor, "product_highlights", "highlights", product_id)
            conn.commit()

            cursor.close()
            conn.close()

            return redirect("/admin/products")

        except Exception as e:
            conn.rollback()
            cursor.close()
            conn.close()
            return f"Error updating product: {str(e)}", 500

    try:
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
                p.is_new,
                p.online_only,
                p.out_of_stock,
                p.sephora_exclusive,
                p.child_count,
                p.child_max_price,
                p.child_min_price
            FROM products p
            JOIN brands b ON p.brand_id = b.brand_id
            WHERE p.product_id = %s
            """,
            (product_id,)
        )

        product = cursor.fetchone()

        if not product:
            cursor.close()
            conn.close()
            return "Product not found.", 404

        cursor.execute(
            "SELECT ingredients FROM product_ingredients WHERE product_id = %s",
            (product_id,)
        )
        ingredient_row = cursor.fetchone()
        ingredients = ingredient_row["ingredients"] if ingredient_row else ""

        cursor.execute(
            "SELECT highlights FROM product_highlights WHERE product_id = %s",
            (product_id,)
        )
        highlight_row = cursor.fetchone()
        highlights = highlight_row["highlights"] if highlight_row else ""

        cursor.close()
        conn.close()

        return render_template(
            "admin_edit_product.html",
            product=product,
            ingredients=ingredients,
            highlights=highlights
        )

    except Exception as e:
        cursor.close()
        conn.close()
        return f"Error loading product: {str(e)}", 500


@admin_product_bp.route("/admin/products/delete/<product_id>", methods=["POST"])
def admin_delete_product(product_id):
    if not is_admin_logged_in():
        return redirect("/admin/login")

    conn = get_mariadb_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM products WHERE product_id = %s",
        (product_id,)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/admin/products")


def update_product_text_table(cursor, table_name, column_name, product_id):
    text_value = request.form.get(column_name)
    if text_value is None:
        return

    cursor.execute(
        f"SELECT COUNT(*) as count FROM {table_name} WHERE product_id = %s",
        (product_id,)
    )
    result = cursor.fetchone()

    if result["count"] > 0:
        cursor.execute(
            f"UPDATE {table_name} SET {column_name} = %s WHERE product_id = %s",
            (text_value, product_id)
        )
    else:
        cursor.execute(
            f"INSERT INTO {table_name} (product_id, {column_name}) VALUES (%s, %s)",
            (product_id, text_value)
        )
