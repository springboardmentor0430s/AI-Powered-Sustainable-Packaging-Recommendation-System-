from flask_login import UserMixin
from database import db
from datetime import datetime

# ================= USER ================= #
class User(UserMixin, db.Model):
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    products = db.relationship("Product", backref="user", lazy=True)
    recommendations = db.relationship("Recommendation", backref="user", lazy=True)

    def __repr__(self):
        return f"<User {self.username}>"


# ================= MATERIAL ================= #
class Material(db.Model):
    __tablename__ = "materials"

    id = db.Column(db.Integer, primary_key=True)
    material_name = db.Column(db.String(150), nullable=False)
    strength_rating = db.Column(db.Integer, nullable=False)              # 1–10
    weight_capacity_kg = db.Column(db.Float, nullable=False)
    biodegradability_score = db.Column(db.Integer, nullable=False)       # 1–10
    recyclability_percent = db.Column(db.Float, nullable=False)          # 0–100
    co2_emission_score = db.Column(db.Float, nullable=False)             # lower = better
    cost_per_kg = db.Column(db.Float, nullable=False)

    recommendations = db.relationship("Recommendation", backref="material", lazy=True)

    def calculate_eco_score(self):
        """
        Normalized eco score (0–10 scale)
        """
        bio = (self.biodegradability_score / 10) * 10
        recycle = (self.recyclability_percent / 100) * 10
        co2 = max(0, 10 - self.co2_emission_score)

        score = (bio * 0.4) + (recycle * 0.3) + (co2 * 0.3)
        return round(score, 2)

    def __repr__(self):
        return f"<Material {self.material_name}>"


# ================= PRODUCT ================= #
class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    weight_kg = db.Column(db.Float, nullable=False)
    fragility_level = db.Column(db.Integer, nullable=False)              # 1–10
    temperature_sensitive = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    recommendations = db.relationship("Recommendation", backref="product", lazy=True)

    def __repr__(self):
        return f"<Product {self.product_name}>"


# ================= RECOMMENDATION ================= #
class Recommendation(db.Model):
    __tablename__ = "recommendations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey("materials.id"), nullable=False)

    recommendation_score = db.Column(db.Float, nullable=False)
    co2_reduction_percent = db.Column(db.Float, nullable=False)
    cost_savings_percent = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Recommendation score={self.recommendation_score}>"
