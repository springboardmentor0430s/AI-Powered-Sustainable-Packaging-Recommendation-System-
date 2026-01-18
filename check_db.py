import psycopg2
import sys

try:
    conn = psycopg2.connect(
        host="localhost",
        database="ecopackdb",
        user="postgres",
        password="password"
    )
    print("Connection successful!")
    
    cur = conn.cursor()
    
    # Check if table exists
    cur.execute("SELECT to_regclass('public.packaging_predictions');")
    if cur.fetchone()[0] is None:
        print("Table 'packaging_predictions' does NOT exist.")
    else:
        print("Table 'packaging_predictions' exists.")
        
        # Check count
        cur.execute("SELECT count(*) FROM packaging_predictions;")
        count = cur.fetchone()[0]
        print(f"Row count: {count}")
        
        # Check content
        cur.execute("SELECT * FROM packaging_predictions LIMIT 5;")
        rows = cur.fetchall()
        print("Sample rows:", rows)

    conn.close()

except Exception as e:
    print(f"Connection failed: {e}")
