from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class ScanHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Input Params
    product_name = db.Column(db.String(100))
    category = db.Column(db.String(50))
    tensile_strength = db.Column(db.Float)
    weight_capacity = db.Column(db.Float)
    moisture_barrier = db.Column(db.Float)
    biodegradability = db.Column(db.Float)
    recyclability = db.Column(db.Float)
    
    # AI Results
    result_material = db.Column(db.String(50))
    result_recommendation = db.Column(db.String(50))
    result_co2 = db.Column(db.Float)
    result_cost = db.Column(db.Float)
    
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
