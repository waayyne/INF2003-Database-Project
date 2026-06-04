from flask import Flask, render_template, request, redirect, session
from datetime import datetime
from db import get_mariadb_connection, get_mongo_collection, bootstrap_databases
from bson import ObjectId
import re

app = Flask(__name__)
app.secret_key = "glowbase-secret-key"
bootstrap_databases()


# =========================================================
# Basic helper functions
# =========================================================

def is_admin_logged_in():
    return session.get("admin_logged_in") == True


def fix_mongo_id(review):
    if "_id" in review:
        review["_id"] = str(review["_id"])
    return review


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

    cursor.execute(
        "SELECT category_id FROM categories WHERE primary_category = %s LIMIT 1",
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

        cursor.execute(
            "SELECT category_id FROM categories WHERE primary_category = %s LIMIT 1",
            (primary_category,)
        )
        category_id = cursor.fetchone()[0]

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


def add_display_fields(cursor, product):
    category = get_product_category(cursor, product["product_id"])
    ingredients, highlights = get_product_extra_text(cursor, product["product_id"])

    product["primary_category"] = category["primary_category"]
    product["secondary_category"] = category["secondary_category"]
    product["tertiary_category"] = category["tertiary_category"]
    product["ingredients"] = ingredients
    product["highlights"] = highlights

    return product


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
        # Get ALL categories for this product (many-to-many!)
        cursor.execute("""
            SELECT c.category_id, c.primary_category, c.secondary_category, c.tertiary_category
            FROM product_categories pc
            JOIN categories c ON pc.category_id = c.category_id
            WHERE pc.product_id = %s
        """, (product_id,))
        
        product_categories = cursor.fetchall()
        product["categories"] = product_categories
        
        # Also get ingredients and highlights
        ingredients, highlights = get_product_extra_text(cursor, product_id)
        product["ingredients"] = ingredients
        product["highlights"] = highlights

    cursor.close()
    conn.close()

    return product

def get_reviews_by_product_id(product_id):
    reviews_collection = get_mongo_collection()

    reviews = list(
        reviews_collection.find(
            {"product_id": str(product_id)}
        ).limit(10)
    )

    return [fix_mongo_id(review) for review in reviews]


# =========================================================
# Public pages
# =========================================================

@app.route("/")
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

@app.route("/products")
def products():
    search = request.args.get("search", "")
    brand = request.args.get("brand", "")
    category = request.args.get("category", "")
    rating = request.args.get("rating", "")
    price = request.args.get("price", "")

    conn = get_mariadb_connection()
    cursor = conn.cursor(dictionary=True)

    params = []

    # FIXED QUERY - includes categories from junction table
    query = """
        SELECT 
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
        FROM products p
        JOIN brands b ON p.brand_id = b.brand_id
        LEFT JOIN product_categories pc ON p.product_id = pc.product_id
        LEFT JOIN categories c ON pc.category_id = c.category_id
    """

    where_clauses = []
    
    if search:
        where_clauses.append("p.product_name LIKE %s")
        params.append("%" + search + "%")

    if brand:
        where_clauses.append("b.brand_name = %s")
        params.append(brand)

    if rating:
        min_rating, max_rating = rating.split("-")
        where_clauses.append("p.rating >= %s AND p.rating <= %s")
        params.append(float(min_rating))
        params.append(float(max_rating))
        
    if price:
        min_price, max_price = price.split("-")
        where_clauses.append("p.price_usd >= %s AND p.price_usd <= %s")
        params.append(float(min_price))
        params.append(float(max_price))

    if category:
        where_clauses.append("c.primary_category = %s")
        params.append(category)

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    query += " GROUP BY p.product_id ORDER BY p.product_name LIMIT 100"

    cursor.execute(query, params)
    product_list = cursor.fetchall()

    # Debug: Print first product to check if categories are fetched
    if product_list:
        print(f"DEBUG - First product categories: {product_list[0].get('categories', 'NOT FOUND')}")

    # Get distinct brands for filter
    cursor.execute("SELECT DISTINCT brand_name FROM brands ORDER BY brand_name")
    brands = [row["brand_name"] for row in cursor.fetchall()]

    # Get distinct categories from categories table
    cursor.execute("""
        SELECT DISTINCT primary_category 
        FROM categories 
        WHERE primary_category IS NOT NULL 
        ORDER BY primary_category
    """)
    categories = [row["primary_category"] for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    return render_template(
        "products.html",
        products=product_list,
        brands=brands,
        categories=categories,
        search=search,
        selected_brand=brand,
        selected_category=category,
        selected_rating=rating,
        selected_price=price
    )

@app.route("/product/<product_id>")
def product_detail(product_id):
    product = get_product_by_id(product_id)

    if not product:
        return "Product not found."

    reviews = get_reviews_by_product_id(product_id)

    return render_template(
        "product_detail.html",
        product=product,
        reviews=reviews
    )


@app.route("/reviews")
def reviews():
    search = request.args.get("search", "")
    rating = request.args.get("rating", "")
    recommended = request.args.get("recommended", "")

    reviews_collection = get_mongo_collection()

    mongo_filter = {}

    if search:
        mongo_filter["$or"] = [
            {"product_name": {"$regex": search, "$options": "i"}},
            {"brand_name": {"$regex": search, "$options": "i"}},
            {"review_title": {"$regex": search, "$options": "i"}},
            {"review_text": {"$regex": search, "$options": "i"}}
        ]

    if rating:
        min_rating, max_rating = rating.split("-")
        mongo_filter["rating"] = {
            "$gte": float(min_rating),
            "$lte": float(max_rating)
        }

    if recommended != "":
        mongo_filter["is_recommended"] = int(recommended)

    review_list = list(reviews_collection.find(mongo_filter).limit(100))
    review_list = [fix_mongo_id(review) for review in review_list]

    return render_template(
        "reviews.html",
        reviews=review_list,
        search=search,
        selected_rating=rating,
        selected_recommended=recommended
    )


@app.route("/submit-review", methods=["GET", "POST"])
def submit_review():
    if request.method == "POST":
        product_id = request.form.get("product_id")
        product = get_product_by_id(product_id)

        if not product:
            return "Product not found."

        review_data = {
            "author_name": request.form.get("author_name"),
            "product_id": product["product_id"],
            "product_name": product["product_name"],
            "brand_name": product["brand_name"],
            "price_usd": float(product["price_usd"]) if product["price_usd"] else 0,
            "rating": int(request.form.get("rating")),
            "is_recommended": int(request.form.get("is_recommended")),
            "review_title": request.form.get("review_title"),
            "review_text": request.form.get("review_text"),
            "skin_type": request.form.get("skin_type"),
            "skin_tone": request.form.get("skin_tone"),
            "eye_color": None,
            "hair_color": None,
            "helpfulness": None,
            "total_feedback_count": 0,
            "total_neg_feedback_count": 0,
            "total_pos_feedback_count": 0,
            "submission_time": datetime.now().strftime("%d/%m/%Y")
        }

        reviews_collection = get_mongo_collection()
        reviews_collection.insert_one(review_data)

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

        return redirect("/reviews")

    conn = get_mariadb_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT product_id, product_name
        FROM products
        ORDER BY product_name
        LIMIT 300
    """)
    product_list = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "submit_review.html",
        products=product_list
    )


@app.route("/analytics")
def analytics():
    conn = get_mariadb_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total_products FROM products")
    total_products = cursor.fetchone()["total_products"]

    cursor.execute("SELECT AVG(rating) AS avg_rating FROM products")
    avg_row = cursor.fetchone()
    avg_rating = round(float(avg_row["avg_rating"]), 2) if avg_row["avg_rating"] else 0

    cursor.execute("""
        SELECT COUNT(*) AS out_of_stock_count
        FROM products
        WHERE out_of_stock = 1
    """)
    out_of_stock_count = cursor.fetchone()["out_of_stock_count"]

    cursor.execute("""
        SELECT p.product_name, b.brand_name, p.rating
        FROM products p, brands b
        WHERE p.brand_id = b.brand_id
        AND p.rating IS NOT NULL
        ORDER BY p.rating DESC
        LIMIT 10
    """)
    top_rated = cursor.fetchall()

    cursor.execute("""
        SELECT p.product_name, b.brand_name, p.loves_count
        FROM products p, brands b
        WHERE p.brand_id = b.brand_id
        AND p.loves_count IS NOT NULL
        ORDER BY p.loves_count DESC
        LIMIT 10
    """)
    most_loved = cursor.fetchall()

    cursor.execute("""
        SELECT b.brand_name,
               COUNT(*) AS total_products,
               AVG(p.rating) AS avg_rating
        FROM products p, brands b
        WHERE p.brand_id = b.brand_id
        GROUP BY b.brand_name
        ORDER BY avg_rating DESC
        LIMIT 10
    """)
    brand_performance = cursor.fetchall()

    for brand_row in brand_performance:
        if brand_row["avg_rating"] is not None:
            brand_row["avg_rating"] = round(float(brand_row["avg_rating"]), 2)

    cursor.close()
    conn.close()

    reviews_collection = get_mongo_collection()
    recommended_count = reviews_collection.count_documents({"is_recommended": 1})

    return render_template(
        "analytics.html",
        total_products=total_products,
        avg_rating=avg_rating,
        out_of_stock_count=out_of_stock_count,
        recommended_count=recommended_count,
        top_rated=top_rated,
        most_loved=most_loved,
        brand_performance=brand_performance
    )


# =========================================================
# Admin pages
# =========================================================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = ""

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == "admin" and password == "admin123":
            session["admin_logged_in"] = True
            return redirect("/admin/dashboard")
        else:
            error = "Invalid username or password."

    return render_template("admin_login.html", error=error)


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect("/admin/login")


@app.route("/admin/dashboard")
def admin_dashboard():
    if not is_admin_logged_in():
        return redirect("/admin/login")

    conn = get_mariadb_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total_products FROM products")
    total_products = cursor.fetchone()["total_products"]

    cursor.close()
    conn.close()

    reviews_collection = get_mongo_collection()
    total_reviews = reviews_collection.count_documents({})

    return render_template(
        "admin_dashboard.html",
        total_products=total_products,
        total_reviews=total_reviews
    )


@app.route("/admin/products")
def admin_products():
    if not is_admin_logged_in():
        return redirect("/admin/login")

    conn = get_mariadb_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            p.product_id,
            p.product_name,
            b.brand_name,
            p.price_usd,
            p.rating
        FROM products p, brands b
        WHERE p.brand_id = b.brand_id
        ORDER BY p.product_id
        LIMIT 100
    """)
    product_list = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "admin_products.html",
        products=product_list
    )


@app.route("/admin/products/add", methods=["GET", "POST"])
def admin_add_product():
    if not is_admin_logged_in():
        return redirect("/admin/login")

    if request.method == "POST":
        conn = get_mariadb_connection()
        cursor = conn.cursor()

        product_id = request.form.get("product_id")
        product_name = request.form.get("product_name")
        brand_name = request.form.get("brand_name")
        primary_category = request.form.get("primary_category") or ""
        price_usd = request.form.get("price_usd") or 0
        rating = request.form.get("rating") or 0
        size = request.form.get("size") or ""
        out_of_stock = request.form.get("out_of_stock") or 0
        ingredients = request.form.get("ingredients") or ""
        highlights = request.form.get("highlights") or ""

        brand_id = get_brand_id(cursor, brand_name)

        cursor.execute(
            """
            INSERT INTO products (
                product_id,
                product_name,
                brand_id,
                loves_count,
                rating,
                reviews,
                size,
                variation_type,
                variation_value,
                variation_desc,
                price_usd,
                value_price_usd,
                sale_price_usd,
                limited_edition,
                is_new,
                online_only,
                out_of_stock,
                sephora_exclusive,
                child_count,
                child_max_price,
                child_min_price
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
                product_id,
                product_name,
                brand_id,
                0,
                rating,
                0,
                size,
                "",
                "",
                "",
                price_usd,
                None,
                None,
                0,
                0,
                0,
                out_of_stock,
                0,
                0,
                None,
                None
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
@app.route("/admin/products/edit/<product_id>", methods=["GET", "POST"])
def admin_edit_product(product_id):
    if not is_admin_logged_in():
        return redirect("/admin/login")

    conn = get_mariadb_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        product_name = request.form.get("product_name")
        price_usd = request.form.get("price_usd") or 0
        rating = request.form.get("rating") or 0
        size = request.form.get("size") or ""
        out_of_stock = request.form.get("out_of_stock") or 0

        cursor.execute(
            """
            UPDATE products
            SET product_name = %s,
                price_usd = %s,
                rating = %s,
                size = %s,
                out_of_stock = %s
            WHERE product_id = %s
            """,
            (
                product_name,
                price_usd,
                rating,
                size,
                out_of_stock,
                product_id
            )
        )

        conn.commit()
        cursor.close()
        conn.close()

        return redirect("/admin/products")

    cursor.execute(
        """
        SELECT product_id, product_name, price_usd, rating, size, out_of_stock
        FROM products
        WHERE product_id = %s
        """,
        (product_id,)
    )

    product = cursor.fetchone()

    cursor.close()
    conn.close()

    if not product:
        return "Product not found."

    return render_template(
        "admin_edit_product.html",
        product=product
    )

@app.route("/admin/products/delete/<product_id>")
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


@app.route("/admin/sql-demo")
def sql_demo():
    if not is_admin_logged_in():
        return redirect("/admin/login")

    conn = get_mariadb_connection()
    cursor = conn.cursor(dictionary=True)

    # Nested Query 1:
    # Products above the average product rating.
    cursor.execute("""
        SELECT p.product_id, p.product_name, b.brand_name, p.rating, p.price_usd
        FROM products p, brands b
        WHERE p.brand_id = b.brand_id
        AND p.rating > (
            SELECT AVG(rating)
            FROM products
        )
        ORDER BY p.rating DESC
        LIMIT 20
    """)
    above_average_products = cursor.fetchall()

    # Nested Query 2:
    # Products from brands with more than 3 products.
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

    # Nested Query 3:
    # Products that are more expensive than the average product price.
    cursor.execute("""
        SELECT p.product_id, p.product_name, b.brand_name, p.price_usd, p.rating
        FROM products p, brands b
        WHERE p.brand_id = b.brand_id
        AND p.price_usd > (
            SELECT AVG(price_usd)
            FROM products
        )
        ORDER BY p.price_usd DESC
        LIMIT 20
    """)
    above_average_price_products = cursor.fetchall()

    # Nested Query 4:
    # Brands whose average rating is higher than the overall average rating.
    cursor.execute("""
        SELECT b.brand_name, AVG(p.rating) AS avg_rating, COUNT(*) AS total_products
        FROM products p, brands b
        WHERE p.brand_id = b.brand_id
        GROUP BY b.brand_name
        HAVING AVG(p.rating) > (
            SELECT AVG(rating)
            FROM products
        )
        ORDER BY avg_rating DESC
        LIMIT 20
    """)
    high_rating_brands = cursor.fetchall()

    # Nested Query 5:
    # Products that have the highest rating in the whole product table.
    cursor.execute("""
        SELECT p.product_id, p.product_name, b.brand_name, p.rating, p.price_usd
        FROM products p, brands b
        WHERE p.brand_id = b.brand_id
        AND p.rating = (
            SELECT MAX(rating)
            FROM products
        )
        ORDER BY p.product_name
        LIMIT 20
    """)
    highest_rating_products = cursor.fetchall()

    # Nested Query 6:
    # Products from brands that have at least one out-of-stock product.
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

    cursor.close()
    conn.close()

    return render_template(
        "sql_demo.html",
        above_average_products=above_average_products,
        popular_brand_products=popular_brand_products,
        above_average_price_products=above_average_price_products,
        high_rating_brands=high_rating_brands,
        highest_rating_products=highest_rating_products,
        brands_with_out_of_stock_products=brands_with_out_of_stock_products
    )


@app.route("/admin/trigger-demo")
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
    trigger_logs = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "trigger_demo.html",
        trigger_logs=trigger_logs
    )

@app.route("/admin/reviews")
def admin_reviews():
    if not is_admin_logged_in():
        return redirect("/admin/login")

    search = request.args.get("search", "").strip()
    rating = request.args.get("rating", "").strip()
    recommended = request.args.get("recommended", "").strip()
    product_id = request.args.get("product_id", "").strip()
    brand_name = request.args.get("brand_name", "").strip()
    selected_limit = request.args.get("limit", "100").strip()

    try:
        limit = int(selected_limit)
    except ValueError:
        limit = 100

    if limit not in [50, 100, 200, 500]:
        limit = 100

    reviews_collection = get_mongo_collection()
    mongo_filter = {}

    # Search product name, brand name, review title, and review text
    if search:
        mongo_filter["$or"] = [
            {"product_name": {"$regex": search, "$options": "i"}},
            {"brand_name": {"$regex": search, "$options": "i"}},
            {"review_title": {"$regex": search, "$options": "i"}},
            {"review_text": {"$regex": search, "$options": "i"}}
        ]

    # Exact rating filter
    if rating:
        mongo_filter["rating"] = int(rating)

    # Recommended filter
    # Dataset has 1, 0, and null, so handle all clearly.
    if recommended == "1":
        mongo_filter["is_recommended"] = 1
    elif recommended == "0":
        mongo_filter["is_recommended"] = 0
    elif recommended == "null":
        mongo_filter["is_recommended"] = None

    # Product ID exact match
    if product_id:
        mongo_filter["product_id"] = product_id

    # Brand filter, case-insensitive exact match
    if brand_name:
        mongo_filter["brand_name"] = {
            "$regex": "^" + re.escape(brand_name) + "$",
            "$options": "i"
        }

    review_list = list(
        reviews_collection.find(mongo_filter).limit(limit)
    )

    review_list = [fix_mongo_id(review) for review in review_list]

    brand_rows = reviews_collection.distinct("brand_name")
    brands = sorted([brand for brand in brand_rows if brand])

    total_matching_reviews = reviews_collection.count_documents(mongo_filter)

    return render_template(
        "admin_reviews.html",
        reviews=review_list,
        search=search,
        selected_rating=rating,
        selected_recommended=recommended,
        selected_product_id=product_id,
        selected_brand=brand_name,
        selected_limit=str(limit),
        brands=brands,
        total_matching_reviews=total_matching_reviews
    )

@app.route("/admin/reviews/edit/<review_id>", methods=["GET", "POST"])
def admin_edit_review(review_id):
    if not is_admin_logged_in():
        return redirect("/admin/login")

    reviews_collection = get_mongo_collection()

    if request.method == "POST":
        rating = request.form.get("rating")
        is_recommended = request.form.get("is_recommended")
        review_title = request.form.get("review_title")
        review_text = request.form.get("review_text")

        reviews_collection.update_one(
            {"_id": ObjectId(review_id)},
            {
                "$set": {
                    "rating": int(rating),
                    "is_recommended": int(is_recommended),
                    "review_title": review_title,
                    "review_text": review_text
                }
            }
        )

        return redirect("/admin/reviews")

    review = reviews_collection.find_one({"_id": ObjectId(review_id)})

    if not review:
        return "Review not found."

    review = fix_mongo_id(review)

    return render_template(
        "admin_edit_review.html",
        review=review
    )


@app.route("/admin/reviews/delete/<review_id>")
def admin_delete_review(review_id):
    if not is_admin_logged_in():
        return redirect("/admin/login")

    reviews_collection = get_mongo_collection()

    reviews_collection.delete_one(
        {"_id": ObjectId(review_id)}
    )

    return redirect("/admin/reviews")


@app.route("/admin/view-index-demo")
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

    cursor.close()
    conn.close()

    return render_template(
        "view_index_demo.html",
        view_results=view_results,
        index_results=index_results
    )

@app.route("/category/<category_name>")
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
        ORDER BY p.rating DESC
        LIMIT 50
    """, (category_name,))
    
    products = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template("category_products.html", products=products, category=category_name)

@app.route("/admin/performance-demo")
def performance_demo():
    if not is_admin_logged_in():
        return redirect("/admin/login")
    
    conn = get_mariadb_connection()
    cursor = conn.cursor(dictionary=True)
    
    # =========================================================
    # Query 1: Search by product name (uses idx_products_product_name)
    # =========================================================
    
    # WITH INDEX (normal query)
    cursor.execute("""
        EXPLAIN FORMAT=JSON
        SELECT p.product_id, p.product_name, b.brand_name, p.rating, p.price_usd
        FROM products p
        JOIN brands b ON p.brand_id = b.brand_id
        WHERE p.product_name LIKE '%Cream%'
        LIMIT 100
    """)
    with_index_result = cursor.fetchone()
    
    # Measure actual execution time WITH index
    import time
    start = time.time()
    cursor.execute("""
        SELECT p.product_id, p.product_name, b.brand_name, p.rating, p.price_usd
        FROM products p
        JOIN brands b ON p.brand_id = b.brand_id
        WHERE p.product_name LIKE '%Cream%'
        LIMIT 100
    """)
    with_index_data = cursor.fetchall()
    with_index_time = (time.time() - start) * 1000  # milliseconds
    
    # =========================================================
    # Query 2: Search by price range (uses idx_products_price)
    # =========================================================
    
    start = time.time()
    cursor.execute("""
        SELECT product_id, product_name, price_usd, rating
        FROM products
        WHERE price_usd BETWEEN 30 AND 60
        ORDER BY price_usd
        LIMIT 50
    """)
    price_query_data = cursor.fetchall()
    price_query_time = (time.time() - start) * 1000
    
    cursor.execute("""
        EXPLAIN FORMAT=JSON
        SELECT product_id, product_name, price_usd, rating
        FROM products
        WHERE price_usd BETWEEN 30 AND 60
        ORDER BY price_usd
        LIMIT 50
    """)
    price_explain = cursor.fetchone()
    
    # =========================================================
    # Query 3: Join with categories (complex query)
    # =========================================================
    
    start = time.time()
    cursor.execute("""
        SELECT p.product_name, b.brand_name, c.primary_category, p.rating
        FROM products p
        JOIN brands b ON p.brand_id = b.brand_id
        JOIN product_categories pc ON p.product_id = pc.product_id
        JOIN categories c ON pc.category_id = c.category_id
        WHERE p.rating >= 4.5
        ORDER BY p.rating DESC
        LIMIT 50
    """)
    join_query_data = cursor.fetchall()
    join_query_time = (time.time() - start) * 1000
    
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
    
    # =========================================================
    # List all indexes on products table
    # =========================================================
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

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)