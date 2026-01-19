import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Create users table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            name VARCHAR(255),
            google_id VARCHAR(255) UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create materials table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS materials (
            id SERIAL PRIMARY KEY,
            material_type VARCHAR(100),
            strength_mpa FLOAT,
            weight_capacity_kg FLOAT,
            biodegradability_pct FLOAT,
            co2_emission_g FLOAT,
            recyclability_pct FLOAT,
            cost_per_kg_inr FLOAT,
            typical_product_category VARCHAR(100)
        )
    ''')
    
    # Create predictions table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            strength_mpa FLOAT,
            weight_capacity_kg FLOAT,
            biodegradability_pct FLOAT,
            recyclability_pct FLOAT,
            predicted_co2 FLOAT,
            predicted_cost FLOAT,
            recommended_material VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Database initialized successfully!")

if __name__ == "__main__":
    init_db()