import sqlite3

try:
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    cur.execute("UPDATE packaging_history SET predicted_cost = 1.3 WHERE recommended_material = 'Molded Pulp'")
    conn.commit()
    print("Successfully updated Molded Pulp predicted_cost to 1.3")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
