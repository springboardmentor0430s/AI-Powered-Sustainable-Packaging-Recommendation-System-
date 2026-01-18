import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, Response
import pandas as pd
import psycopg2 
from datetime import datetime
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)
app.secret_key = "EcoPackAI_Secret_Key" # Session management

# --- GOOGLE OAUTH CONFIGURATION ---
app.config['GOOGLE_CLIENT_ID'] = "854678979619-d687ehh7ju1jg74fdlra7rjfqmdl8jkk.apps.googleusercontent.com" 
app.config['GOOGLE_CLIENT_SECRET'] = "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"

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=app.config['GOOGLE_CLIENT_ID'],
    client_secret=app.config['GOOGLE_CLIENT_SECRET'],
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# --- Database Connection ---
def get_db_connection():
    try:
        return psycopg2.connect(
            database="eco_materials_db", 
            user="postgres", 
            password="Nandini", 
            host="127.0.0.1",
            port="5432"
        )
    except Exception as e:
        print(f"❌ DB Error: {e}")
        return None

# --- AUTH ROUTES ---
@app.route('/')
def home(): 
    return render_template('auth.html')

@app.route('/login/google')
def login_google():
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/authorize')
def authorize():
    token = google.authorize_access_token()
    user_info = token.get('userinfo')
    if not user_info:
        resp = google.get('https://www.googleapis.com/oauth2/v3/userinfo')
        user_info = resp.json()
    session['user'] = user_info
    return redirect(url_for('dashboard'))

@app.route('/login_check', methods=['POST'])
def login_check():
    email = request.form.get('email')
    if email:
        session['user'] = {'email': email, 'name': email.split('@')[0]}
    return redirect(url_for('dashboard'))

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    session['user'] = {'name': username or "New User"}
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard(): 
    if 'user' not in session:
        return redirect(url_for('home'))
    return render_template('index.html', user=session['user'])

@app.route('/logout')
def logout(): 
    session.pop('user', None)
    return redirect(url_for('home'))

# --- CORE LOGIC: PREDICTION (With Edge Case Handling) ---
@app.route('/predict', methods=['POST'])
def predict():
    try:
        p_name = request.form.get('product_name')
        category = request.form.get('category')
        strength_val = request.form.get('strength')
        tensile = float(strength_val) if strength_val else 0
        
        # UPDATE: Edge Case Handling for Cost
        cost_in = float(request.form.get('cost', 0))
        if cost_in <= 0:
            return jsonify({"status": "error", "message": "Unit Cost must be greater than 0!"})
        
        dynamic_score = round(min(0.99, 0.7 + (tensile / 1000)), 2)

        recs = [
            {"name": "Recycled Glass", "cost": round(cost_in * 0.82, 2), "score": dynamic_score, "carbon": "0.12kg", "tag": "Most Sustainable", "icon": "fa-wine-bottle"},
            {"name": "Bio-Polymer", "cost": round(cost_in * 0.78, 2), "score": round(dynamic_score * 0.9, 2), "carbon": "0.25kg", "tag": "Eco-Choice", "icon": "fa-seedling"},
            {"name": "Industrial Hemp", "cost": round(cost_in * 0.65, 2), "score": round(dynamic_score * 1.1, 2), "carbon": "0.05kg", "tag": "Carbon Negative", "icon": "fa-leaf"}
        ]

        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("""INSERT INTO ai_predictions (product_name, product_category, input_cost, optimized_cost, sustainability_score, created_at) 
                           VALUES (%s, %s, %s, %s, %s, %s)""", 
                        (p_name, category, cost_in, recs[0]['cost'], recs[0]['score'], datetime.now()))
            conn.commit()
            cur.close(); conn.close()

        return jsonify({"status": "success", "top_recommendations": recs})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# --- NEW: DOWNLOAD REPORT ROUTE (Enhancement) ---
@app.route('/download_report')
def download_report():
    conn = get_db_connection()
    if conn:
        df = pd.read_sql_query("SELECT * FROM ai_predictions ORDER BY created_at DESC", conn)
        conn.close()
        # Report ko CSV format mein download karwana
        csv_data = df.to_csv(index=False)
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=EcoPackAI_Report.csv"}
        )
    return "Database Error", 500

# --- ANALYTICS & HISTORY ---
@app.route('/get_analytics_data')
def get_analytics_data():
    conn = get_db_connection()
    if conn:
        df = pd.read_sql_query("SELECT product_name, optimized_cost, sustainability_score FROM ai_predictions ORDER BY id DESC LIMIT 8", conn)
        conn.close()
        return jsonify({
            "labels": df['product_name'].tolist(), 
            "costs": df['optimized_cost'].tolist(), 
            "scores": df['sustainability_score'].tolist()
        })
    return jsonify({"labels": [], "costs": [], "scores": []})

@app.route('/get_history')
def get_history():
    conn = get_db_connection()
    if conn:
        df = pd.read_sql_query("SELECT product_name, product_category, optimized_cost, created_at FROM ai_predictions ORDER BY id DESC LIMIT 15", conn)
        conn.close()
        return jsonify([{"product": r[0], "category": r[1], "cost": r[2], "date": r[3].strftime("%d %b, %H:%M")} for r in df.values])
    return jsonify([])

if __name__ == "__main__":
    app.run(debug=True, port=5000)