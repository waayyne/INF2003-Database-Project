from flask import Blueprint, render_template

from db import get_mariadb_connection, get_mongo_collection
from services.products import get_valid_product_ids
from utils import make_pasteable_sql

chemical_bp = Blueprint("chemicals", __name__)


@chemical_bp.route("/chemicals")
def chemicals():
    reviews_collection = get_mongo_collection()
    valid_product_ids = get_valid_product_ids()

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


@chemical_bp.route("/chemicals/<path:chemical_name>")
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
        product_list = cursor.fetchall()

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

        product_list = []

    cursor.close()
    conn.close()

    return render_template(
        "chemical_products.html",
        chemical=chemical_name,
        products=product_list,
        mongo_query_used=mongo_query_used,
        chemical_products_sql=make_pasteable_sql(chemical_products_sql, product_ids),
        product_ids=product_ids
    )
