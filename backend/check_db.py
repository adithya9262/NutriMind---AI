import sqlite3

def check_completed_tasks():
    conn = sqlite3.connect('c:/nutrimind-ai/backend/nutrimind.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, status, completed_at FROM tasks WHERE status = 'completed'")
    rows = cursor.fetchall()
    print(f"Found {len(rows)} completed tasks.")
    for r in rows:
        print(f"Task: {r[1]} | Status: {r[2]} | Completed At: {r[3]}")
        if r[3] is None:
            print("ERROR: completed_at is NULL!")
        else:
            print("SUCCESS: completed_at is NOT NULL")
    conn.close()

if __name__ == '__main__':
    check_completed_tasks()
