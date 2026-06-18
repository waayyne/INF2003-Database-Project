from datetime import datetime
from pathlib import Path
from textwrap import dedent

from flask import Blueprint, current_app, render_template

from db import get_mariadb_connection, get_mongo_collection
from utils import save_bar_chart

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/analytics")
def analytics():
    charts_dir = Path(current_app.static_folder) / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)

    chart_version = datetime.now().strftime("%Y%m%d%H%M%S%f")

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

    reviews_chart_name = "reviews_by_rating.png"
    save_bar_chart(
        charts_dir / reviews_chart_name,
        [str(row["_id"]) for row in rating_results],
        [row["count"] for row in rating_results],
        "Reviews by Rating",
        "Rating",
        "Review Count",
        "#4a8f7f"
    )

    brands_chart_name = "top_10_brands_by_product_count.png"
    save_bar_chart(
        charts_dir / brands_chart_name,
        [row["brand_name"] for row in top_brands],
        [row["product_count"] for row in top_brands],
        "Top 10 Brands by Product Count",
        "Brand",
        "Product Count",
        "#c27c5a"
    )

    recommendation_chart_name = "recommended_vs_not_recommended.png"
    save_bar_chart(
        charts_dir / recommendation_chart_name,
        ["Recommended", "Not Recommended"],
        [recommended_count, not_recommended_count],
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
