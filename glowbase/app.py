from flask import Flask, render_template, request, redirect, session, url_for
import pandas as pd
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "glowbase-secret-key"

PRODUCTS_CSV = "data/product_info_matched_clean.csv"
REVIEWS_CSV = "data/productreviews_clean.csv"
USER_REVIEWS_CSV = "data/user_reviews.csv"

products_df = pd.read_csv(PRODUCTS_CSV, encoding="latin1")
reviews_df = pd.read_csv(REVIEWS_CSV, encoding="latin1")

products_df = products_df.fillna("")
reviews_df = reviews_df.fillna("")


def load_user_reviews():
    if os.path.exists(USER_REVIEWS_CSV):
        return pd.read_csv(USER_REVIEWS_CSV, encoding="latin1").fillna("")
    return pd.DataFrame(columns=[
        "author_name",
        "product_id",
        "product_name",
        "rating",
        "is_recommended",
        "review_title",
        "review_text",
        "skin_type",
        "skin_tone",
        "submission_time"
    ])


def save_user_review(review_data):
    user_reviews_df = load_user_reviews()
    user_reviews_df.loc[len(user_reviews_df)] = review_data
    user_reviews_df.to_csv(USER_REVIEWS_CSV, index=False, encoding="latin1")


def is_admin_logged_in():
    return session.get("admin_logged_in") == True


@app.route("/")
def index():
    total_products = len(products_df)
    total_brands = products_df["brand_name"].nunique() if "brand_name" in products_df.columns else 0

    user_reviews_df = load_user_reviews()
    total_reviews = len(reviews_df) + len(user_reviews_df)

    top_category = "N/A"
    if "primary_category" in products_df.columns and not products_df["primary_category"].empty:
        top_category = products_df["primary_category"].mode()[0]

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

    filtered = products_df.copy()

    if search and "product_name" in filtered.columns:
        filtered = filtered[filtered["product_name"].astype(str).str.contains(search, case=False, na=False)]

    if brand and "brand_name" in filtered.columns:
        filtered = filtered[filtered["brand_name"] == brand]

    if category and "primary_category" in filtered.columns:
        filtered = filtered[filtered["primary_category"] == category]

    if rating and "rating" in filtered.columns:
        filtered["rating"] = pd.to_numeric(filtered["rating"], errors="coerce")
        filtered = filtered[filtered["rating"] >= float(rating)]

    if price and "price_usd" in filtered.columns:
        min_price, max_price = price.split("-")
        filtered["price_usd"] = pd.to_numeric(filtered["price_usd"], errors="coerce")
        filtered = filtered[
            (filtered["price_usd"] >= float(min_price)) &
            (filtered["price_usd"] <= float(max_price))
        ]

    brands = []
    categories = []

    if "brand_name" in products_df.columns:
        brands = sorted(products_df["brand_name"].dropna().astype(str).unique())

    if "primary_category" in products_df.columns:
        categories = sorted(products_df["primary_category"].dropna().astype(str).unique())

    return render_template(
        "products.html",
        products=filtered.head(100).to_dict(orient="records"),
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
    if "product_id" not in products_df.columns:
        return "Product ID column not found."

    product = products_df[products_df["product_id"].astype(str) == str(product_id)]

    if product.empty:
        return "Product not found."

    product = product.iloc[0].to_dict()

    dataset_reviews = pd.DataFrame()
    if "product_id" in reviews_df.columns:
        dataset_reviews = reviews_df[reviews_df["product_id"].astype(str) == str(product_id)]

    user_reviews_df = load_user_reviews()
    user_reviews = user_reviews_df[user_reviews_df["product_id"].astype(str) == str(product_id)]

    combined_reviews = pd.concat([dataset_reviews, user_reviews], ignore_index=True)
    combined_reviews = combined_reviews.head(10).to_dict(orient="records")

    return render_template(
        "product_detail.html",
        product=product,
        reviews=combined_reviews
    )


@app.route("/reviews")
def reviews():
    search = request.args.get("search", "")
    rating = request.args.get("rating", "")
    recommended = request.args.get("recommended", "")

    user_reviews_df = load_user_reviews()
    filtered = pd.concat([reviews_df, user_reviews_df], ignore_index=True).fillna("")

    if search:
        product_match = pd.Series(False, index=filtered.index)
        review_match = pd.Series(False, index=filtered.index)

        if "product_name" in filtered.columns:
            product_match = filtered["product_name"].astype(str).str.contains(search, case=False, na=False)

        if "review_text" in filtered.columns:
            review_match = filtered["review_text"].astype(str).str.contains(search, case=False, na=False)

        filtered = filtered[product_match | review_match]

    if rating and "rating" in filtered.columns:
        filtered["rating"] = pd.to_numeric(filtered["rating"], errors="coerce")
        filtered = filtered[filtered["rating"] >= float(rating)]

    if recommended and "is_recommended" in filtered.columns:
        filtered = filtered[filtered["is_recommended"].astype(str) == recommended]

    return render_template(
        "reviews.html",
        reviews=filtered.head(100).to_dict(orient="records"),
        search=search,
        selected_rating=rating,
        selected_recommended=recommended
    )


@app.route("/submit-review", methods=["GET", "POST"])
def submit_review():
    if request.method == "POST":
        product_id = request.form.get("product_id")
        product = products_df[products_df["product_id"].astype(str) == str(product_id)]

        product_name = ""
        if not product.empty:
            product_name = product.iloc[0]["product_name"]

        review_data = {
            "author_name": request.form.get("author_name"),
            "product_id": product_id,
            "product_name": product_name,
            "rating": request.form.get("rating"),
            "is_recommended": request.form.get("is_recommended"),
            "review_title": request.form.get("review_title"),
            "review_text": request.form.get("review_text"),
            "skin_type": request.form.get("skin_type"),
            "skin_tone": request.form.get("skin_tone"),
            "submission_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        save_user_review(review_data)
        return redirect("/reviews")

    product_list = products_df[["product_id", "product_name"]].head(300).to_dict(orient="records")

    return render_template(
        "submit_review.html",
        products=product_list
    )


@app.route("/analytics")
def analytics():
    total_products = len(products_df)

    avg_rating = 0
    if "rating" in products_df.columns:
        ratings = pd.to_numeric(products_df["rating"], errors="coerce")
        avg_rating = round(ratings.mean(), 2)

    out_of_stock_count = 0
    if "out_of_stock" in products_df.columns:
        out_of_stock_count = len(
            products_df[products_df["out_of_stock"].astype(str).isin(["1", "True", "true"])]
        )

    user_reviews_df = load_user_reviews()
    combined_reviews = pd.concat([reviews_df, user_reviews_df], ignore_index=True).fillna("")

    recommended_count = 0
    if "is_recommended" in combined_reviews.columns:
        recommended_count = len(combined_reviews[combined_reviews["is_recommended"].astype(str) == "1"])

    top_rated = products_df.copy()
    if "rating" in top_rated.columns:
        top_rated["rating"] = pd.to_numeric(top_rated["rating"], errors="coerce")
        top_rated = top_rated.sort_values(by="rating", ascending=False).head(10)

    most_loved = products_df.copy()
    if "loves_count" in most_loved.columns:
        most_loved["loves_count"] = pd.to_numeric(most_loved["loves_count"], errors="coerce")
        most_loved = most_loved.sort_values(by="loves_count", ascending=False).head(10)

    brand_performance = []
    if "brand_name" in products_df.columns and "rating" in products_df.columns:
        temp = products_df.copy()
        temp["rating"] = pd.to_numeric(temp["rating"], errors="coerce")

        brand_performance = (
            temp.groupby("brand_name")
            .agg(total_products=("product_id", "count"), avg_rating=("rating", "mean"))
            .reset_index()
            .sort_values(by="avg_rating", ascending=False)
            .head(10)
        )

        brand_performance["avg_rating"] = brand_performance["avg_rating"].round(2)
        brand_performance = brand_performance.to_dict(orient="records")

    return render_template(
        "analytics.html",
        total_products=total_products,
        avg_rating=avg_rating,
        out_of_stock_count=out_of_stock_count,
        recommended_count=recommended_count,
        top_rated=top_rated.to_dict(orient="records"),
        most_loved=most_loved.to_dict(orient="records"),
        brand_performance=brand_performance
    )


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

    return render_template(
        "admin_dashboard.html",
        total_products=len(products_df),
        total_reviews=len(reviews_df) + len(load_user_reviews())
    )


@app.route("/admin/products")
def admin_products():
    if not is_admin_logged_in():
        return redirect("/admin/login")

    return render_template(
        "admin_products.html",
        products=products_df.head(100).to_dict(orient="records")
    )


@app.route("/admin/products/add", methods=["GET", "POST"])
def admin_add_product():
    global products_df

    if not is_admin_logged_in():
        return redirect("/admin/login")

    if request.method == "POST":
        new_product = {
            "product_id": request.form.get("product_id"),
            "product_name": request.form.get("product_name"),
            "brand_name": request.form.get("brand_name"),
            "primary_category": request.form.get("primary_category"),
            "secondary_category": request.form.get("secondary_category"),
            "tertiary_category": request.form.get("tertiary_category"),
            "price_usd": request.form.get("price_usd"),
            "rating": request.form.get("rating"),
            "reviews": request.form.get("reviews"),
            "loves_count": request.form.get("loves_count"),
            "size": request.form.get("size"),
            "variation_type": request.form.get("variation_type"),
            "variation_value": request.form.get("variation_value"),
            "limited_edition": request.form.get("limited_edition"),
            "new": request.form.get("new"),
            "online_only": request.form.get("online_only"),
            "out_of_stock": request.form.get("out_of_stock"),
            "sephora_exclusive": request.form.get("sephora_exclusive"),
            "ingredients": request.form.get("ingredients"),
            "highlights": request.form.get("highlights")
        }

        for column in products_df.columns:
            if column not in new_product:
                new_product[column] = ""

        products_df.loc[len(products_df)] = new_product
        products_df.to_csv(PRODUCTS_CSV, index=False, encoding="latin1")

        return redirect("/admin/products")

    return render_template("admin_add_product.html")


@app.route("/admin/products/delete/<product_id>")
def admin_delete_product(product_id):
    global products_df

    if not is_admin_logged_in():
        return redirect("/admin/login")

    products_df = products_df[products_df["product_id"].astype(str) != str(product_id)]
    products_df.to_csv(PRODUCTS_CSV, index=False, encoding="latin1")

    return redirect("/admin/products")


if __name__ == "__main__":
    app.run(debug=True)