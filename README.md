🎓 Exam Seating Portal

A full-stack university admin portal for automated exam seating plan generation, PDF export, and supplementary exam management.


✨ Features
Core

🏛️ Clean admin portal UI — sidebar navigation, dashboard with live stats and charts
🗃️ SQLite database — students, faculty, halls, blocks, exams, seating history
📋 Full CRUD for students, faculty, halls and blocks directly from the UI
📥 Excel import for bulk student and faculty upload
## How to Run

```bash
cd exam-portal
python -m venv venv

# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
python app.py
```

Open: **http://127.0.0.1:5000**

## Excel Format

**Students:** `Roll Number`, `Branch` (+ optional `Year`, `Section`)
**Faculty:** `Name`, `Faculty ID`, `Contact` (+ optional `Department`)

Any column name variant is accepted automatically.

## Project Structure

```
exam-portal/
├── app.py            # Flask app + all routes
├── models.py         # SQLAlchemy DB models
├── algorithm.py      # Seating + faculty assignment logic
├── pdf_generator.py  # PDF generation (reference format)
├── requirements.txt
├── templates/
│   ├── base.html       # Sidebar layout
│   ├── dashboard.html  # Stats + charts
│   ├── students.html   # Student CRUD
│   ├── faculty.html    # Faculty CRUD
│   ├── halls.html      # Halls + blocks CRUD
│   ├── generate.html   # Generate exam plan
│   ├── exams.html      # Exam history
│   └── exam_detail.html# Hall-wise seating view
├── instance/
│   └── exam_seating.db # SQLite DB (auto-created)
├── uploads/            # Temp Excel files
└── outputs/            # Generated PDFs
```
