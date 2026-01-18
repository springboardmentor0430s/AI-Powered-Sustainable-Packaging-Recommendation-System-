import sqlite3
import random
from datetime import datetime, timedelta

username = "Jayanth" # Using the first user found
db_path = "users.db"

categories = ["Electronics", "Food & Beverage", "Pharmaceuticals", "Automotive", "Consumer Goods"]
materials = ["Molded Pulp", "Recycled Cardboard", "Biodegradable Plastic", "Standard Plastic", "Styrofoam"]

# Mock data generation
data = []
for i in range(20):
    category = random.choice(categories)
    
    # Logic to make data look somewhat realistic
    if category == "Electronics":
        material = random.choice(["Molded Pulp", "Styrofoam", "Recycled Cardboard"])
        cost = round(random.uniform(0.5, 2.0), 2)
        score = random.randint(40, 90)
    elif category == "Food & Beverage":
        material = random.choice(["Biodegradable Plastic", "Recycled Cardboard"])
        cost = round(random.uniform(0.1, 0.5), 2)
        score = random.randint(60, 95)
    else:
        material = random.choice(materials)
        cost = round(random.uniform(0.2, 1.5), 2)
        score = random.randint(30, 90)

    # Pred cost slightly lower usually
    pred_cost = round(cost * random.uniform(0.8, 1.1), 2)
    strength = "High" if score < 50 else ("Medium" if score < 80 else "Low") # loose correlation

    data.append((
        username,
        f"Product {i+1}",
        category,
        cost,
        material,
        pred_cost,
        score,
        (datetime.now() - timedelta(days=random.randint(0, 10))).strftime("%Y-%m-%d %H:%M:%S")
    ))

try:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Clear existing to avoid duplicates if run multiple times (optional, but good for clean slate)
    cur.execute("DELETE FROM packaging_history WHERE username = ?", (username,))
    
    cur.executemany("""
        INSERT INTO packaging_history 
        (username, product_name, material_category, current_cost, recommended_material, predicted_cost, sustainability_score, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, data)
    
    conn.commit()
    print(f"Successfully inserted {len(data)} records for user '{username}'.")
    conn.close()
except Exception as e:
    print(f"Error seeding DB: {e}")
