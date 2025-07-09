from fastapi import FastAPI, Request, Form, UploadFile, File, Response, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import sqlite3
import datetime
import os
import uuid
import csv
import codecs
from io import StringIO
from collections import namedtuple

app = FastAPI()
templates = Jinja2Templates(directory="templates")

db_dir = "/app/db"
os.makedirs(db_dir, exist_ok=True)
db_path = os.path.join(db_dir, "tasks.db")
conn = sqlite3.connect(db_path, check_same_thread=False)

cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    house_id TEXT,
    task_description TEXT,
    status TEXT,
    created_at TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS houses (
    house_id TEXT PRIMARY KEY,
    owner TEXT,
    address TEXT,
    manager_email TEXT,
    email2 TEXT,
    phone1 TEXT,
    phone2 TEXT
)
""")
conn.commit()

@app.get("/house/{house_id}", response_class=HTMLResponse)
async def show_form(request: Request, house_id: str):
    cursor.execute("SELECT * FROM tasks WHERE house_id = ? ORDER BY created_at DESC", (house_id,))
    tasks = cursor.fetchall()
    cursor.execute("SELECT * FROM houses WHERE house_id = ?", (house_id,))
    house = cursor.fetchone()
    house_metadata = None
    if house:
        house_metadata = {
            "house_id": house[0],
            "owner": house[1],
            "address": house[2],
            "manager_email": house[3],
            "email2": house[4],
            "phone1": house[5],
            "phone2": house[6]
        }
    return templates.TemplateResponse("form.html", {
        "request": request,
        "house_id": house_id,
        "tasks": tasks,
        "house_metadata": house_metadata
    })

@app.post("/submit")
async def submit_task(request: Request, house_id: str = Form(...), preset_task: str = Form(""), custom_task: str = Form("")):
    task_description = custom_task if preset_task == "Other" else preset_task
    if not task_description:
        return HTMLResponse(content="No task provided", status_code=400)
    cursor.execute("""
        INSERT INTO tasks (house_id, task_description, status, created_at)
        VALUES (?, ?, ?, ?)
    """, (house_id, task_description, "pending", datetime.datetime.now().isoformat()))
    conn.commit()
    return templates.TemplateResponse("confirmation.html", {
        "request": request,
        "house_id": house_id,
        "task_description": task_description
    })

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request, import_banner: str = Cookie(None)):
    Task = namedtuple("Task", ["id", "house_id", "task_description", "status", "created_at"])
    House = namedtuple("House", ["house_id", "owner", "address", "manager_email", "email2", "phone1", "phone2"])
    cursor.execute("SELECT * FROM tasks ORDER BY created_at DESC")
    tasks = [Task(*row) for row in cursor.fetchall()]
    cursor.execute("SELECT * FROM houses ORDER BY house_id ASC")
    houses = [House(*row) for row in cursor.fetchall()]
    response = templates.TemplateResponse("admin.html", {
        "request": request,
        "tasks": tasks,
        "houses": houses,
        "import_banner": import_banner
    })
    if import_banner:
        response.delete_cookie("import_banner")
    return response

@app.post("/add_house")
async def add_house(
    owner: str = Form(""),
    address: str = Form(""),
    manager_email: str = Form(""),
    email2: str = Form(""),
    phone1: str = Form(""),
    phone2: str = Form("")
):
    house_id = str(uuid.uuid4())[:8]
    cursor.execute("SELECT 1 FROM houses WHERE house_id = ?", (house_id,))
    while cursor.fetchone():
        house_id = str(uuid.uuid4())[:8]
    cursor.execute("""
        INSERT INTO houses (house_id, owner, address, manager_email, email2, phone1, phone2)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (house_id, owner, address, manager_email, email2, phone1, phone2))
    conn.commit()
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/admin/update_house")
async def admin_update_house(
    house_id: str = Form(...),
    owner: str = Form(...),
    address: str = Form(...),
    manager_email: str = Form(...),
    email2: str = Form(...),
    phone1: str = Form(...),
    phone2: str = Form(...)
):
    cursor.execute("""
        UPDATE houses
        SET owner = ?, address = ?, manager_email = ?, email2 = ?, phone1 = ?, phone2 = ?
        WHERE house_id = ?
    """, (owner, address, manager_email, email2, phone1, phone2, house_id))
    conn.commit()
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/delete_house")
async def delete_house(house_id: str = Form(...)):
    cursor.execute("DELETE FROM houses WHERE house_id = ?", (house_id,))
    conn.commit()
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/delete")
async def delete_task(task_id: int = Form(...), house_id: str = Form(...)):
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    return RedirectResponse(url=f"/house/{house_id}", status_code=303)

@app.post("/complete")
async def complete_task(task_id: int = Form(...), house_id: str = Form(...)):
    cursor.execute("UPDATE tasks SET status = 'done' WHERE id = ?", (task_id,))
    conn.commit()
    return RedirectResponse(url=f"/house/{house_id}", status_code=303)

@app.post("/edit")
async def edit_task(task_id: int = Form(...), house_id: str = Form(...), new_description: str = Form(...)):
    cursor.execute("UPDATE tasks SET task_description = ? WHERE id = ?", (new_description, task_id))
    conn.commit()
    return RedirectResponse(url=f"/house/{house_id}", status_code=303)

@app.get("/export_houses")
async def export_houses():
    cursor.execute("SELECT * FROM houses")
    rows = cursor.fetchall()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["house_id", "owner", "address", "manager_email", "email2", "phone1", "phone2"])
    writer.writerows(rows)
    output.seek(0)
    return StreamingResponse(output, media_type="text/csv", headers={
        "Content-Disposition": "attachment; filename=houses.csv"
    })

@app.post("/import_houses")
async def import_houses(request: Request, file: UploadFile = File(...)):
    content = codecs.iterdecode(file.file, 'utf-8')
    reader = csv.DictReader(content)
    added_count = 0
    skipped_rows = []
    total = 0

    for row in reader:
        total += 1
        owner = row.get("owner", "").strip()
        address = row.get("address", "").strip()
        cursor.execute("SELECT 1 FROM houses WHERE owner = ? AND address = ?", (owner, address))
        if cursor.fetchone():
            skipped_rows.append(f"{owner} - {address}")
            continue
        house_id = str(uuid.uuid4())[:8]
        cursor.execute("SELECT 1 FROM houses WHERE house_id = ?", (house_id,))
        while cursor.fetchone():
            house_id = str(uuid.uuid4())[:8]
        cursor.execute("""
            INSERT INTO houses (house_id, owner, address, manager_email, email2, phone1, phone2)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            house_id,
            owner,
            address,
            row.get("manager_email", "").strip(),
            row.get("email2", "").strip(),
            row.get("phone1", "").strip(),
            row.get("phone2", "").strip()
        ))
        added_count += 1

    conn.commit()
    banner_message = f"Imported {added_count} of {total} records. {len(skipped_rows)} skipped."
    if skipped_rows:
        banner_message += " Skipped duplicates: " + ", ".join(skipped_rows[:5])
        if len(skipped_rows) > 5:
            banner_message += f" (+{len(skipped_rows)-5} more)"

    response = RedirectResponse(url="/admin", status_code=303)
    response.set_cookie("import_banner", banner_message, max_age=10)
    return response
