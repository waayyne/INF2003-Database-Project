import re

from bson import ObjectId
from flask import Blueprint, redirect, render_template, request

from db import get_mongo_collection
from utils import fix_mongo_id, is_admin_logged_in

admin_review_bp = Blueprint("admin_reviews", __name__)


@admin_review_bp.route("/admin/reviews")
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

    if search:
        mongo_filter["$or"] = [
            {"product_name": {"$regex": search, "$options": "i"}},
            {"brand_name": {"$regex": search, "$options": "i"}},
            {"review_title": {"$regex": search, "$options": "i"}},
            {"review_text": {"$regex": search, "$options": "i"}}
        ]

    if rating:
        mongo_filter["rating"] = int(rating)

    if recommended == "1":
        mongo_filter["is_recommended"] = 1
    elif recommended == "0":
        mongo_filter["is_recommended"] = 0
    elif recommended == "null":
        mongo_filter["is_recommended"] = None

    if product_id:
        mongo_filter["product_id"] = product_id

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


@admin_review_bp.route("/admin/reviews/edit/<review_id>", methods=["GET", "POST"])
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


@admin_review_bp.route("/admin/reviews/delete/<review_id>")
def admin_delete_review(review_id):
    if not is_admin_logged_in():
        return redirect("/admin/login")

    reviews_collection = get_mongo_collection()
    reviews_collection.delete_one({"_id": ObjectId(review_id)})

    return redirect("/admin/reviews")
