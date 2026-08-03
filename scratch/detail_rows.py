import sqlite3

db_path = r"C:\Users\umert\aquavolt-ai-pk\aquavolt_telemetry.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

try:
    cur.execute("SELECT scene_id, count(*) FROM telemetry_log GROUP BY scene_id;")
    rows = cur.fetchall()
    print("Group by Scene ID:")
    for row in rows:
        print(f" - Scene: {row[0]} | Rows: {row[1]}")
        
    cur.execute("SELECT strftime('%Y-%m', timestamp) as m, count(*) FROM telemetry_log GROUP BY m;")
    months = cur.fetchall()
    print("\nGroup by Month:")
    for month in months:
        print(f" - Month: {month[0]} | Rows: {month[1]}")
        
    cur.execute("SELECT COUNT(*) FROM telemetry_log;")
    total = cur.fetchone()[0]
    print(f"\nTotal Rows in telemetry_log: {total}")
except Exception as e:
    print(f"Error: {e}")

conn.close()
