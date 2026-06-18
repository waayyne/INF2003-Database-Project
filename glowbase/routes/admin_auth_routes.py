from flask import Blueprint, redirect, render_template, request, session

from db import get_mariadb_connection, get_mongo_collection
from utils import is_admin_logged_in

admin_auth_bp = Blueprint("admin_auth", __name__)


@admin_auth_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = ""

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == "admin" and password == "admin123":
            session["admin_logged_in"] = True
            return redirect("/admin/dashboard")

        error = "Invalid username or password."

    return render_template("admin_login.html", error=error)


@admin_auth_bp.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect("/admin/login")


@admin_auth_bp.route("/admin/dashboard")
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
