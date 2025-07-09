import sqlite3
from datetime import datetime, timedelta

# Path to your live database on host (outside container)
DB_PATH = "./db/tasks.db"

def should_reset(last_reset, frequency):
    if not last_reset or not frequency:
        return False

    try:
        last = datetime.fromisoformat(last_reset)
    except ValueError:
        return False

    now = datetime.now()

    if frequency == "daily":
        return (now - last) >= timedelta(days=1)
    elif frequency == "weekly":
        return (now - last) >= timedelta(weeks=1)
    elif frequency == "monthly":
        return (now - last).days >= 28  # simple monthly logic
    return False

def reset_tasks():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, last_reset, reset_frequency FROM tasks
        WHERE is_recurring = 1 AND status = 'done'
    """)

    to_reset = []
    for task_id, last_reset, frequency in cursor.fetchall():
        if should_reset(last_reset, frequency):
            to_reset.append((task_id,))

    for (task_id,) in to_reset:
        print(f"Resetting task ID {task_id}")
        cursor.execute("""
            UPDATE tasks
            SET status = 'submitted', last_reset = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), task_id))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    reset_tasks()

