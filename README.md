# QR Task Management System

A lightweight QR-driven task management system for property or house operations.
Guests can scan a QR code to submit maintenance requests, while administrators can manage tasks, houses, and bulk updates via an admin panel.

---

## 📁 Project Structure Breakdown

```
qr-task-system/
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       └── templates/
│           ├── admin.html
│           ├── confirmation.html
│           └── form.html
├── db/
│   └── tasks.db
├── docker-compose.yml
└── reset_tasks.py
```

### 🔹 `backend/`
Contains all backend logic and configuration for containerization.

- **`Dockerfile`** — Builds the FastAPI container image using `python:3.10`, installs dependencies, and launches `uvicorn`.
- **`requirements.txt`** — Lists all required Python packages (FastAPI, Jinja2, Uvicorn, etc.).

#### `backend/app/`
Core application directory.

- **`main.py`** — The main FastAPI app:
  - Handles all routes (`/submit`, `/admin`, `/import_houses`, etc.)
  - Interacts with SQLite database
  - Uses Jinja2 to render templates
  - Implements cookie-based banner messaging
  - Auto-generates unique house IDs
  - Supports CSV import/export with deduplication logic

#### `backend/app/templates/`
HTML views rendered by FastAPI using Jinja2.

- **`admin.html`** — Admin interface:
  - Create/update/delete houses
  - Manage tasks
  - Upload/download CSVs
  - Display import results via a dismissible banner

- **`form.html`** — User-facing task submission form:
  - Triggered via house-specific QR codes
  - Allows preset or custom task input

- **`confirmation.html`** — Success page confirming task submission

---

### 🔹 `db/`
Contains persistent application data.

- **`tasks.db`** — SQLite database holding two tables:
  - `houses`: Metadata about each property (ID, owner, contact info)
  - `tasks`: Task descriptions and statuses submitted by users

> 🔒 This is the most critical file to back up for live data.

---

### 🔹 `docker-compose.yml`
Defines how to launch the app with Docker Compose.

- Builds the backend service from `Dockerfile`
- Maps container port 8000 to the host
- Mounts volume for live development

Start with:
```bash
docker-compose up --build
```

---

### 🔹 `reset_tasks.py`
Optional script to delete all records in the `tasks` table.
Can be used during development or before deployments.

---

## 🚀 Features
- QR-based guest submission forms
- Admin dashboard to manage houses and tasks
- CSV import/export with validation and banner feedback
- Dismissible import messages stored via cookies
- Dockerized for easy deployment

---

## 🛠 Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/home_management.git
cd qr-task-system
```

### 2. Build and run with Docker Compose
```bash
docker-compose up --build
```
Visit [http://localhost:8000/admin](http://localhost:8000/admin) to access the admin panel.

---

## 📋 CSV Format for Import

When importing houses:
```
owner,address,manager_email,email2,phone1,phone2
```
- No `house_id` needed — generated automatically
- Duplicate (owner + address) rows are skipped with banner summary

---

## 🔐 Notes
- The system uses cookies to pass flash messages (e.g., CSV import results)
- The SQLite database file should be backed up regularly (`db/tasks.db`)

## 📋 How to Stop, Rebuild and Restart the App
From the root of your project (qr-task-system/):

✅ 1. Stop the app
docker-compose down
This stops and removes all running containers, networks, and volumes defined in your docker-compose.yml.

✅ 2. Rebuild the app (after code or dependency changes)
docker-compose build
Only needed if you’ve changed:

Dockerfile

Python dependencies (requirements.txt)

Any app code (e.g., main.py, templates)

✅ 3. Start the app
docker-compose up
---

## 📄 License
MIT or custom internal license.

---

## ✍️ Author
Shay Byrne — [shaybyrne.ca](https://shaybyrne.ca)
