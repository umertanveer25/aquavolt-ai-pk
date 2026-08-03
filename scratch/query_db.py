import sqlite3

db_path = r"C:\Users\umert\aquavolt-ai-pk\aquavolt_telemetry.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

try:
    cur.execute("SELECT DISTINCT scene_id FROM telemetry_log;")
    scenes = cur.fetchall()
    print("Unique Satellite Scene IDs in Database:")
    for scene in scenes:
        print(f" - {scene[0]}")
    print(f"Total Unique Passes: {len(scenes)}")
    
    cur.execute("SELECT COUNT(*) FROM telemetry_log;")
    total_records = cur.fetchone()[0]
    print(f"Total Database Rows: {total_records}")
except Exception as e:
    print(f"Error querying database: {e}")

conn.close()
