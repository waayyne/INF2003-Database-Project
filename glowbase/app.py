from flask import Flask

from db import bootstrap_databases
from routes.admin_auth_routes import admin_auth_bp
from routes.admin_database_demo_routes import admin_database_demo_bp
from routes.admin_product_routes import admin_product_bp
from routes.admin_review_routes import admin_review_bp
from routes.analytics_routes import analytics_bp
from routes.chemical_routes import chemical_bp
from routes.home_routes import home_bp
from routes.product_routes import product_bp
from routes.review_routes import review_bp


def create_app():
    app = Flask(__name__)
    app.secret_key = "glowbase-secret-key"

    bootstrap_databases()

    app.register_blueprint(home_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(review_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(chemical_bp)
    app.register_blueprint(admin_auth_bp)
    app.register_blueprint(admin_product_bp)
    app.register_blueprint(admin_review_bp)
    app.register_blueprint(admin_database_demo_bp)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=False, use_reloader=False)
