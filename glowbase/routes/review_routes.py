from datetime import datetime

from flask import Blueprint, redirect, render_template, request

from db import get_mongo_collection
from services.products import (
    get_product_by_id,
    get_product_select_options,
    increment_product_review_count,
)
from utils import fix_mongo_id

review_bp = Blueprint("reviews", __name__)


@review_bp.route("/reviews")
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


@review_bp.route("/submit-review", methods=["GET", "POST"])
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
        increment_product_review_count(product_id)

        return redirect(f"/product/{product_id}")

    return render_template(
        "submit_review.html",
        products=get_product_select_options()
    )
