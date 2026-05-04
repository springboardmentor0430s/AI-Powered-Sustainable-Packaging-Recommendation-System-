from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import pandas as pd
import pickle
import os
from config import Config
from models import db, User, ScanHistory

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Load Models
try:
    with open('src/models/co2_model.pkl', 'rb') as f:
        co2_model = pickle.load(f)
    with open('src/models/cost_model.pkl', 'rb') as f:
        cost_model = pickle.load(f)
    with open('src/models/recommendation_model.pkl', 'rb') as f:
        rec_model = pickle.load(f)
    print("Models loaded successfully.")
except FileNotFoundError:
    print("Models not found. Please run train_models.py first.")
    co2_model = None
    cost_model = None
    rec_model = None

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        # Check if it's login or register
        action = request.form.get('action')
        username = request.form.get('username')
        password = request.form.get('password')
        
        if action == 'register':
            if User.query.filter_by(username=username).first():
                flash('Username already exists.')
                return redirect(url_for('login'))
            user = User(username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('dashboard'))
            
        else: # Login
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                return redirect(url_for('dashboard'))
            flash('Invalid username or password.')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/history')
@login_required
def history():
    scans = ScanHistory.query.filter_by(user_id=current_user.id).order_by(ScanHistory.timestamp.desc()).all()
    # Serialize for frontend if needed, or render a template
    # Here we might want to return JSON for a dynamic frontend or render a partial
    return jsonify([{
        'product_name': s.product_name,
        'category': s.category,
        'material': s.result_material,
        'co2': s.result_co2,
        'cost': s.result_cost,
        'recommendation': s.result_recommendation,
        'date': s.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'tensile_strength': s.tensile_strength,
        'weight_capacity': s.weight_capacity,
        'moisture_barrier': s.moisture_barrier
    } for s in scans])

# Predefined materials database
MATERIALS_DB = [
    {'name': 'Recycled Cardboard', 'bio': 95, 'recycle': 95},
    {'name': 'Molded Pulp', 'bio': 100, 'recycle': 100},
    {'name': 'Biodegradable Plastic', 'bio': 80, 'recycle': 50},
    {'name': 'Kraft Paper', 'bio': 90, 'recycle': 100},
    {'name': 'Mushroom Mycelium', 'bio': 100, 'recycle': 100},
    {'name': 'Cornstarch Scale', 'bio': 100, 'recycle': 100},
    {'name': 'Standard Plastic', 'bio': 5, 'recycle': 30},
    {'name': 'Styrofoam', 'bio': 0, 'recycle': 10},
    {'name': 'Aluminum Foil', 'bio': 0, 'recycle': 80}
]

def get_ai_recommendations(tensile_req, weight_req, moisture_req):
    results = []
    
    for mat in MATERIALS_DB:
        # Construct feature vector
        row = pd.DataFrame([{
            "Material_Type": mat['name'],
            "Tensile_Strength_MPa": tensile_req,
            "Weight_Capacity_kg": weight_req,
            "Biodegradability_Score": mat['bio'],
            "Recyclability_Percent": mat['recycle'],
            "Moisture_Barrier_Grade": moisture_req
        }])
        
        # Predict
        pred_co2 = co2_model.predict(row)[0]
        pred_cost = cost_model.predict(row)[0]
        pred_rec = rec_model.predict(row)[0] # "Highly Recommended", etc.
        
        results.append({
            'material': mat['name'],
            'co2': round(pred_co2, 2),
            'cost': round(pred_cost, 2),
            'recommendation': pred_rec,
            'details': mat
        })
        
    # Sort by Recommendation (Highly > Consider > Avoid) then by CO2
    rec_order = {"Highly Recommended": 0, "Consider as Option": 1, "Avoid": 2}
    results.sort(key=lambda x: (rec_order.get(x['recommendation'], 3), x['co2']))
    return results

@app.route('/api/materials')
@login_required
def get_materials_static():
    # Return static properties for Analytics Matrix
    return jsonify(MATERIALS_DB)

@app.route('/api/recommend', methods=['POST'])
@login_required
def recommend():
    if not co2_model:
        return jsonify({'error': 'Models not loaded'}), 500
        
    data = request.json
    
    # User inputs constraints
    tensile_req = float(data.get('tensile_strength', 10))
    weight_req = float(data.get('weight_capacity', 5))
    moisture_req = float(data.get('moisture_barrier', 5))
    product_name = data.get('product_name', 'Unknown')
    category = data.get('category', 'Generic')
    
    results = get_ai_recommendations(tensile_req, weight_req, moisture_req)
    
    # Save best result to history
    best = results[0]
    scan = ScanHistory(
        user_id=current_user.id,
        product_name=product_name,
        category=category,
        tensile_strength=tensile_req,
        weight_capacity=weight_req,
        moisture_barrier=moisture_req,
        biodegradability=best['details']['bio'],
        recyclability=best['details']['recycle'],
        result_material=best['material'],
        result_recommendation=best['recommendation'],
        result_co2=best['co2'],
        result_cost=best['cost']
    )
    db.session.add(scan)
    db.session.commit()
    
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
