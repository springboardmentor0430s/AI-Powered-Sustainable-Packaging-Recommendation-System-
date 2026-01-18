import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, Response
import pandas as pd
import psycopg2 
from datetime import datetime
from authlib.integrations.flask_client import OAuth
from flask_sqlalchemy import SQLAlchemy  

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "EcoPackAI_Secret_Key")

# --- DATABASE CONFIGURATION (FOR RENDER) ---
DB_URL = os.environ.get('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

def get_db_connection():
    try:
        if not DB_URL:
            print("❌ Error: SQLALCHEMY_DATABASE_URI is not set in Render")
            return None
        return psycopg2.connect(DB_URL)
    except Exception as e:
        print(f"❌ Cloud DB Error: {e}")
        return None

# --- OAUTH CONFIGURATION (GOOGLE & GITHUB) ---
oauth = OAuth(app)

# Google Config
google = oauth.register(
    name='google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID', "854678979619-d687ehh7ju1jg74fdlra7rjfqmdl8jkk.apps.googleusercontent.com"),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET', "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"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# GitHub Config (नवीन जोडलेले)
github = oauth.register(
    name='github',
    client_id=os.environ.get('GITHUB_CLIENT_ID'), # Render वर Environment Variable मध्ये टाका
    client_secret=os.environ.get('GITHUB_CLIENT_SECRET'), # Render वर टाका
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize',
    api_base_url='https://api.github.com/',
    client_kwargs={'scope': 'user:email'}
)

# --- AUTH ROUTES ---
@app.route('/')
def home(): 
    return render_template('auth.html')

# Google Login Routes
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

# GitHub Login Routes (अपडेटेड)
@app.route('/login/github')
def login_github():
    redirect_uri = url_for('authorize_github', _external=True)
    return github.authorize_redirect(redirect_uri)

@app.route('/authorize_github')
def authorize_github():
    token = github.authorize_access_token()
    resp = github.get('user')
    user_info = resp.json()
    # GitHub युजर माहिती सेव्ह करणे
    session['user'] = {
        'name': user_info.get('login'), 
        'email': user_info.get('email'),
        'picture': user_info.get('avatar_url')
    }
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

# --- CORE LOGIC: PREDICTION ---
@app.route('/predict', methods=['POST'])
def predict():
    try:
        p_name = request.form.get('product_name')
        category = request.form.get('category')
        strength_val = request.form.get('strength')
        tensile = float(strength_val) if strength_val else 0
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
            cur.execute("""CREATE TABLE IF NOT EXISTS ai_predictions (
                            id SERIAL PRIMARY KEY,
                            product_name VARCHAR(100),
                            product_category VARCHAR(100),
                            input_cost FLOAT,
                            optimized_cost FLOAT,
                            sustainability_score FLOAT,
                            created_at TIMESTAMP)""")
            
            cur.execute("""INSERT INTO ai_predictions (product_name, product_category, input_cost, optimized_cost, sustainability_score, created_at) 
                           VALUES (%s, %s, %s, %s, %s, %s)""", 
                        (p_name, category, cost_in, recs[0]['cost'], recs[0]['score'], datetime.now()))
            conn.commit()
            cur.close(); conn.close()

        return jsonify({"status": "success", "top_recommendations": recs})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# --- ANALYTICS & HISTORY ---
@app.route('/download_report')
def download_report():
    conn = get_db_connection()
    if conn:
        df = pd.read_sql_query("SELECT * FROM ai_predictions ORDER BY created_at DESC", conn)
        conn.close()
        csv_data = df.to_csv(index=False)
        return Response(csv_data, mimetype="text/csv", headers={"Content-disposition": "attachment; filename=EcoPackAI_Report.csv"})
    return "Database Error", 500

@app.route('/get_analytics_data')
def get_analytics_data():
    conn = get_db_connection()
    if conn:
        df = pd.read_sql_query("SELECT product_name, optimized_cost, sustainability_score FROM ai_predictions ORDER BY created_at DESC LIMIT 8", conn)
        conn.close()
        return jsonify({"labels": df['product_name'].tolist(), "costs": df['optimized_cost'].tolist(), "scores": df['sustainability_score'].tolist()})
    return jsonify({"labels": [], "costs": [], "scores": []})

@app.route('/get_history')
def get_history():
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        cur.execute("SELECT product_name, product_category, optimized_cost, created_at FROM ai_predictions ORDER BY created_at DESC LIMIT 15")
        rows = cur.fetchall()
        cur.close(); conn.close()
        return jsonify([{"product": r[0], "category": r[1], "cost": r[2], "date": r[3].strftime("%d %b, %H:%M")} for r in rows])
    return jsonify([])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)