from flask import Flask, render_template, request, redirect, session
from datetime import datetime
from db import get_mariadb_connection, get_mongo_collection, bootstrap_databases
from bson import ObjectId
from pathlib import Path
import matplotlib
import re
from textwrap import dedent

matplotlib.use("Agg")
import matplotlib.pyplot as plt

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


def save_bar_chart(file_path, labels, values, title, x_label, y_label, color):
    figure, axis = plt.subplots(figsize=(6, 3.5))
    figure.patch.set_facecolor("white")

    if labels and values:
        axis.bar(labels, values, color=color, edgecolor="#333333")
        axis.tick_params(axis="x", rotation=35)
    else:
        axis.text(
            0.5,
            0.5,
            "No data available",
            ha="center",
            va="center",
            transform=axis.transAxes,
            fontsize=14,
            color="#666666"
        )
        axis.set_xticks([])
        axis.set_yticks([])

    axis.set_title(title)
    axis.set_xlabel(x_label)
    axis.set_ylabel(y_label)

    for spine in ["top", "right"]:
        axis.spines[spine].set_visible(False)

    figure.tight_layout()
    figure.savefig(file_path, dpi=150, bbox_inches="tight")
    plt.close(figure)


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
    chemical = request.args.get("chemical", "") 

    conn = get_mariadb_connection()
    cursor = conn.cursor(dictionary=True)

    params = []
    no_matching_chemical_filter = False
    
    # If searching by chemical, first find matching product_ids from MongoDB
    product_ids_filter = None
    if chemical:
        reviews_collection = get_mongo_collection()
        # Find all reviews that contain this chemical in their chemicals array
        matching_reviews = list(reviews_collection.find({"chemicals": chemical}))
        # Extract unique product_ids (convert to string for consistency)
        product_ids = list(set([str(r.get("product_id")) for r in matching_reviews if r.get("product_id")]))
        
        if product_ids:
            product_ids_filter = product_ids
        else:
            no_matching_chemical_filter = True

    # Base query with categories aggregation
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
    
    # Apply product ID filter from chemical search
    if product_ids_filter:
        placeholders = ','.join(['%s'] * len(product_ids_filter))
        where_clauses.append(f"p.product_id IN ({placeholders})")
        params.extend(product_ids_filter)
    elif no_matching_chemical_filter:
        where_clauses.append("1 = 0")
    
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
        where_clauses.append("""
            (
                c.primary_category = %s
                OR c.secondary_category = %s
                OR c.tertiary_category = %s
            )
        """)
        params.extend([category, category, category])

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    query += " GROUP BY p.product_id ORDER BY p.product_name LIMIT 100"

    sql_statement_used = dedent(query).strip()
    sql_parameters_used = params[:]

    cursor.execute(query, params)
    product_list = cursor.fetchall()

    # Get distinct brands for filter
    cursor.execute("SELECT DISTINCT brand_name FROM brands ORDER BY brand_name")
    brands = [row["brand_name"] for row in cursor.fetchall()]

    # Get distinct categories from categories table
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
    categories = [row["category_name"] for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    # Get chemicals for filter dropdown
    chemicals = get_chemicals_list()

    return render_template(
        "products.html",
        products=product_list,
        brands=brands,
        categories=categories,
        chemicals=chemicals,
        search=search,
        selected_brand=brand,
        selected_category=category,
        selected_rating=rating,
        selected_price=price,
        selected_chemical=chemical,
        sql_statement_used=sql_statement_used,
        sql_parameters_used=sql_parameters_used
    )


def get_chemicals_list():
    reviews_collection = get_mongo_collection()

    pipeline = [
        {"$match": {"chemicals": {"$exists": True, "$ne": []}}},
        {"$unwind": "$chemicals"},
        {"$group": {"_id": "$chemicals", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 30}
    ]

    chemical_results = list(reviews_collection.aggregate(pipeline))
    return [chem["_id"] for chem in chemical_results if chem["_id"]]


@app.route("/product/<product_id>")
def product_detail(product_id):
    product = get_product_by_id(product_id)

    if not product:
        return "Product not found."

    reviews = get_reviews_by_product_id(product_id)
    
    # Also get chemicals from reviews for this product
    reviews_collection = get_mongo_collection()
    # Get unique chemicals from reviews of this product
    pipeline = [
        {"$match": {"product_id": product_id, "chemicals": {"$exists": True, "$ne": []}}},
        {"$unwind": "$chemicals"},
        {"$group": {"_id": "$chemicals"}}
    ]
    chemical_results = list(reviews_collection.aggregate(pipeline))
    product["chemicals"] = [chem["_id"] for chem in chemical_results]

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

    mongo_query_used = {
        "filter": mongo_filter,
        "limit": 100
    }

    review_list = list(reviews_collection.find(mongo_filter).limit(100))
    review_list = [fix_mongo_id(review) for review in review_list]

    return render_template(
        "reviews.html",
        reviews=review_list,
        search=search,
        selected_rating=rating,
        selected_recommended=recommended,
        mongo_query_used=mongo_query_used
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

        return redirect(f"/product/{product_id}")

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
    charts_dir = Path(app.static_folder) / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)

    chart_version = datetime.now().strftime("%Y%m%d%H%M%S%f")

    conn = get_mariadb_connection()
    cursor = conn.cursor(dictionary=True)

    # =========================
    # MariaDB analytics
    # =========================

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
        FROM products p
        JOIN brands b ON p.brand_id = b.brand_id
        WHERE p.rating IS NOT NULL
        ORDER BY p.rating DESC
        LIMIT 10
    """)
    top_rated = cursor.fetchall()

    cursor.execute("""
        SELECT product_name, loves_count
        FROM products
        WHERE loves_count IS NOT NULL
        ORDER BY loves_count DESC
        LIMIT 10
    """)
    most_loved = cursor.fetchall()

    cursor.execute("""
        SELECT 
            b.brand_name,
            ROUND(AVG(p.rating), 2) AS avg_rating,
            COUNT(*) AS total_products
        FROM products p
        JOIN brands b ON p.brand_id = b.brand_id
        WHERE p.rating IS NOT NULL
        GROUP BY b.brand_name
        ORDER BY avg_rating DESC
        LIMIT 10
    """)
    brand_performance = cursor.fetchall()

    cursor.execute("""
        SELECT 
            MIN(price_usd) AS min_price,
            MAX(price_usd) AS max_price,
            AVG(price_usd) AS avg_price,
            COUNT(*) AS total
        FROM products
        WHERE price_usd IS NOT NULL
    """)
    price_stats = cursor.fetchone()

    top_brands_sql = dedent("""
        SELECT b.brand_name, COUNT(p.product_id) AS product_count
        FROM products p
        JOIN brands b ON p.brand_id = b.brand_id
        GROUP BY b.brand_name
        ORDER BY product_count DESC, b.brand_name ASC
        LIMIT 10
    """).strip()

    cursor.execute(top_brands_sql)
    top_brands = cursor.fetchall()

    cursor.close()
    conn.close()

    # =========================
    # MongoDB analytics
    # =========================

    reviews_collection = get_mongo_collection()

    total_reviews = reviews_collection.count_documents({})
    recommended_count = reviews_collection.count_documents({"is_recommended": 1})
    not_recommended_count = reviews_collection.count_documents({"is_recommended": 0})

    rating_pipeline = [
        {"$match": {"rating": {"$exists": True, "$ne": None}}},
        {"$group": {"_id": "$rating", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]

    rating_results = list(reviews_collection.aggregate(rating_pipeline))

    rating_distribution = []
    for stars in [5, 4, 3, 2, 1]:
        count = reviews_collection.count_documents({"rating": stars})
        rating_distribution.append({
            "stars": stars,
            "count": count
        })

    top_chemicals = list(reviews_collection.aggregate([
        {"$match": {"chemicals": {"$exists": True, "$ne": []}}},
        {"$unwind": "$chemicals"},
        {
            "$group": {
                "_id": "$chemicals",
                "product_count": {"$sum": 1}
            }
        },
        {"$sort": {"product_count": -1}},
        {"$limit": 12}
    ]))

    # =========================
    # Matplotlib charts
    # =========================

    rating_labels = [str(row["_id"]) for row in rating_results]
    rating_values = [row["count"] for row in rating_results]

    reviews_chart_name = "reviews_by_rating.png"
    save_bar_chart(
        charts_dir / reviews_chart_name,
        rating_labels,
        rating_values,
        "Reviews by Rating",
        "Rating",
        "Review Count",
        "#4a8f7f"
    )

    brand_labels = [row["brand_name"] for row in top_brands]
    brand_values = [row["product_count"] for row in top_brands]

    brands_chart_name = "top_10_brands_by_product_count.png"
    save_bar_chart(
        charts_dir / brands_chart_name,
        brand_labels,
        brand_values,
        "Top 10 Brands by Product Count",
        "Brand",
        "Product Count",
        "#c27c5a"
    )

    recommendation_labels = ["Recommended", "Not Recommended"]
    recommendation_values = [recommended_count, not_recommended_count]

    recommendation_chart_name = "recommended_vs_not_recommended.png"
    save_bar_chart(
        charts_dir / recommendation_chart_name,
        recommendation_labels,
        recommendation_values,
        "Recommended vs Not Recommended Reviews",
        "Recommendation Status",
        "Review Count",
        "#8b6fc9"
    )

    return render_template(
        "analytics.html",
        total_products=total_products,
        avg_rating=avg_rating,
        out_of_stock_count=out_of_stock_count,
        total_reviews=total_reviews,
        recommended_count=recommended_count,
        not_recommended_count=not_recommended_count,
        top_rated=top_rated,
        most_loved=most_loved,
        brand_performance=brand_performance,
        top_chemicals=top_chemicals,
        rating_distribution=rating_distribution,
        price_stats=price_stats,

        reviews_by_rating_chart=reviews_chart_name,
        top_brands_chart=brands_chart_name,
        recommendation_chart=recommendation_chart_name,
        chart_version=chart_version,

        reviews_by_rating_pipeline=rating_pipeline,
        top_brands_sql=top_brands_sql
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
        rating = round(float(rating), 2)
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
        try:
            # Get form data
            product_name = request.form.get("product_name")
            price_usd = request.form.get("price_usd") or 0
            rating = request.form.get("rating") or 0
            rating = round(float(rating), 2)
            size = request.form.get("size") or ""
            out_of_stock = request.form.get("out_of_stock") or 0
            
            # Optional fields that might be in the edit form
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
            
            # Convert empty strings to None for price fields
            if value_price_usd == "":
                value_price_usd = None
            if sale_price_usd == "":
                sale_price_usd = None
            if child_max_price == "":
                child_max_price = None
            if child_min_price == "":
                child_min_price = None

            # Execute UPDATE - This triggers after_product_update automatically!
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
                    product_name,
                    price_usd,
                    rating,
                    size,
                    out_of_stock,
                    loves_count,
                    reviews,
                    variation_type,
                    variation_value,
                    variation_desc,
                    value_price_usd,
                    sale_price_usd,
                    limited_edition,
                    is_new,
                    online_only,
                    sephora_exclusive,
                    child_count,
                    child_max_price,
                    child_min_price,
                    product_id
                )
            )

            conn.commit()
            
            # Also update ingredients if provided
            ingredients = request.form.get("ingredients")
            if ingredients:
                # Check if ingredients record exists
                cursor.execute(
                    "SELECT COUNT(*) as count FROM product_ingredients WHERE product_id = %s",
                    (product_id,)
                )
                result = cursor.fetchone()
                
                if result["count"] > 0:
                    cursor.execute(
                        "UPDATE product_ingredients SET ingredients = %s WHERE product_id = %s",
                        (ingredients, product_id)
                    )
                else:
                    cursor.execute(
                        "INSERT INTO product_ingredients (product_id, ingredients) VALUES (%s, %s)",
                        (product_id, ingredients)
                    )
            
            # Also update highlights if provided
            highlights = request.form.get("highlights")
            if highlights:
                # Check if highlights record exists
                cursor.execute(
                    "SELECT COUNT(*) as count FROM product_highlights WHERE product_id = %s",
                    (product_id,)
                )
                result = cursor.fetchone()
                
                if result["count"] > 0:
                    cursor.execute(
                        "UPDATE product_highlights SET highlights = %s WHERE product_id = %s",
                        (highlights, product_id)
                    )
                else:
                    cursor.execute(
                        "INSERT INTO product_highlights (product_id, highlights) VALUES (%s, %s)",
                        (product_id, highlights)
                    )
            
            conn.commit()
            cursor.close()
            conn.close()

            return redirect("/admin/products")
            
        except Exception as e:
            conn.rollback()
            cursor.close()
            conn.close()
            return f"Error updating product: {str(e)}", 500

    # GET request - display edit form
    try:
        # Get main product information
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
        
        # Get product ingredients
        cursor.execute(
            "SELECT ingredients FROM product_ingredients WHERE product_id = %s",
            (product_id,)
        )
        ingredient_row = cursor.fetchone()
        ingredients = ingredient_row["ingredients"] if ingredient_row else ""
        
        # Get product highlights
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

    # Many-to-Many Query:
    # Products and their categories via the product_categories junction table,
    # filtered to only categories that have more than 5 products assigned.
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

    cursor.close()
    conn.close()

    return render_template(
        "sql_demo.html",
        above_average_products=above_average_products,
        popular_brand_products=popular_brand_products,
        above_average_price_products=above_average_price_products,
        high_rating_brands=high_rating_brands,
        highest_rating_products=highest_rating_products,
        brands_with_out_of_stock_products=brands_with_out_of_stock_products,
        category_products=category_products
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

    mongo_query_used = {
        "filter": mongo_filter,
        "limit": limit
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
        total_matching_reviews=total_matching_reviews,
        mongo_query_used=mongo_query_used
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

    # EXPLAIN without index: force full table scan by ignoring the index
    cursor.execute("""
        EXPLAIN SELECT product_id, product_name, rating, price_usd
        FROM products IGNORE INDEX (idx_products_rating)
        WHERE rating >= 4.5
        ORDER BY rating DESC
    """)
    explain_no_index = cursor.fetchall()

    # EXPLAIN with index: normal query that uses idx_products_rating
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
           OR c.secondary_category = %s
           OR c.tertiary_category = %s
        ORDER BY p.rating DESC
        LIMIT 50
    """, (category_name, category_name, category_name))

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

@app.route("/chemicals")
def chemicals():
    reviews_collection = get_mongo_collection()

    # Get only product IDs that exist in MariaDB
    conn = get_mariadb_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT product_id FROM products")
    valid_product_ids = [str(row["product_id"]) for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    # Count unique products per chemical, but only if product exists in MariaDB
    pipeline = [
        {
            "$match": {
                "product_id": {"$in": valid_product_ids},
                "chemicals": {"$exists": True, "$ne": []}
            }
        },
        {"$unwind": "$chemicals"},
        {
            "$group": {
                "_id": "$chemicals",
                "product_ids": {"$addToSet": "$product_id"}
            }
        },
        {
            "$project": {
                "_id": 1,
                "count": {"$size": "$product_ids"}
            }
        },
        {"$sort": {"count": -1}},
        {"$limit": 50}
    ]

    chemical_stats = list(reviews_collection.aggregate(pipeline))

    return render_template("chemicals.html", chemicals=chemical_stats)


@app.route("/chemicals/<path:chemical_name>")
def chemical_products(chemical_name):
    reviews_collection = get_mongo_collection()

    mongo_query_used = {
        "chemicals": chemical_name
    }

    reviews = reviews_collection.find(mongo_query_used)

    product_ids = list(set([
        str(review.get("product_id"))
        for review in reviews
        if review.get("product_id") is not None
    ]))

    conn = get_mariadb_connection()
    cursor = conn.cursor(dictionary=True)

    if product_ids:
        placeholders = ",".join(["%s"] * len(product_ids))

        chemical_products_sql = f"""
SELECT 
    p.product_id,
    p.product_name,
    COALESCE(b.brand_name, 'Unknown Brand') AS brand_name,
    p.price_usd,
    p.rating,
    p.loves_count,
    p.out_of_stock
FROM products p
LEFT JOIN brands b ON p.brand_id = b.brand_id
WHERE p.product_id IN ({placeholders})
ORDER BY p.product_name
        """

        cursor.execute(chemical_products_sql, product_ids)
        products = cursor.fetchall()

    else:
        chemical_products_sql = """
SELECT 
    p.product_id,
    p.product_name,
    COALESCE(b.brand_name, 'Unknown Brand') AS brand_name,
    p.price_usd,
    p.rating,
    p.loves_count,
    p.out_of_stock
FROM products p
LEFT JOIN brands b ON p.brand_id = b.brand_id
WHERE p.product_id IN (...)
ORDER BY p.product_name
        """

        products = []

    cursor.close()
    conn.close()

    return render_template(
        "chemical_products.html",
        chemical=chemical_name,
        products=products,
        mongo_query_used=mongo_query_used,
        chemical_products_sql=dedent(chemical_products_sql).strip(),
        product_ids=product_ids
    )

if __name__ == "__main__":
    app.run(debug=False, use_reloader=False)