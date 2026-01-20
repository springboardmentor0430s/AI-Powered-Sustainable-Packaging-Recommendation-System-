from flask import Flask, render_template, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from config import Config
from database import db
from models import User, Material
from auth import auth_bp
from recommendations import recommendations_bp
from analytics import analytics_bp


def seed_materials():
    if Material.query.first() is not None:
        return

    materials = [
        Material(
            material_name="Recycled Plastic",
            strength_rating=7,
            weight_capacity_kg=50,
            biodegradability_score=3,
            recyclability_percent=95,
            co2_emission_score=2.5,
            cost_per_kg=2.5
        ),
        Material(
            material_name="Biodegradable Plastic (PLA)",
            strength_rating=6,
            weight_capacity_kg=40,
            biodegradability_score=9,
            recyclability_percent=30,
            co2_emission_score=1.5,
            cost_per_kg=4.0
        ),
        Material(
            material_name="Kraft Paper",
            strength_rating=5,
            weight_capacity_kg=30,
            biodegradability_score=10,
            recyclability_percent=85,
            co2_emission_score=0.8,
            cost_per_kg=1.5
        ),
        Material(
            material_name="Corrugated Cardboard",
            strength_rating=8,
            weight_capacity_kg=60,
            biodegradability_score=10,
            recyclability_percent=90,
            co2_emission_score=0.6,
            cost_per_kg=1.2
        ),
        Material(
            material_name="Mushroom Leather",
            strength_rating=6,
            weight_capacity_kg=35,
            biodegradability_score=10,
            recyclability_percent=20,
            co2_emission_score=0.5,
            cost_per_kg=8.0
        ),
        Material(
            material_name="Bamboo Fiber",
            strength_rating=7,
            weight_capacity_kg=45,
            biodegradability_score=9,
            recyclability_percent=70,
            co2_emission_score=1.0,
            cost_per_kg=3.5
        ),
        Material(
            material_name="Cork",
            strength_rating=5,
            weight_capacity_kg=25,
            biodegradability_score=10,
            recyclability_percent=100,
            co2_emission_score=0.3,
            cost_per_kg=6.0
        ),
        Material(
            material_name="Glass",
            strength_rating=9,
            weight_capacity_kg=80,
            biodegradability_score=10,
            recyclability_percent=100,
            co2_emission_score=3.0,
            cost_per_kg=2.0
        ),
    ]

    db.session.bulk_save_objects(materials)
    db.session.commit()
    print("✅ Materials seeded successfully")


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # ---------------- EXTENSIONS ----------------
    db.init_app(app)

    CORS(
        app,
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        expose_headers=["Authorization"]
    )

    jwt = JWTManager(app)

    # ---------------- JWT ERROR HANDLERS ----------------
    @jwt.expired_token_loader
    def expired_token(jwt_header, jwt_payload):
        return jsonify({"error": "Token expired"}), 401

    @jwt.invalid_token_loader
    def invalid_token(error):
        return jsonify({"error": "Invalid token"}), 401

    @jwt.unauthorized_loader
    def missing_token(error):
        return jsonify({"error": "Authorization header missing"}), 401

    # ---------------- BLUEPRINTS ----------------
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(recommendations_bp, url_prefix="/api/recommendations")
    app.register_blueprint(analytics_bp, url_prefix="/api/analytics")

    # ---------------- DATABASE INIT ----------------
    with app.app_context():
        db.create_all()
        seed_materials()

    # ---------------- FRONTEND ROUTES ----------------
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/login")
    def login_page():
        return render_template("login.html")

    @app.route("/signup")
    def signup_page():
        return render_template("signup.html")

    @app.route("/dashboard")
    def dashboard_page():
        return render_template("dashboard.html")

    @app.route("/product-input")
    def product_input_page():
        return render_template("product_input.html")

    @app.route("/recommendations")
    def recommendations_page():
        return render_template("recommendations.html")

    @app.route("/analytics")
    def analytics_page():
        return render_template("analytics.html")

    @app.route("/report")
    def report_page():
        return render_template("report.html")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
