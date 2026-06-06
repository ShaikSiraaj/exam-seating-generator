🎓 Exam Seating Portal

A full-stack university admin portal for automated exam seating plan generation, PDF export, and supplementary exam management.


✨ Features
Core

🏛️ Clean admin portal UI — sidebar navigation, dashboard with live stats and charts
🗃️ SQLite database — students, faculty, halls, blocks, exams, seating history
📋 Full CRUD for students, faculty, halls and blocks directly from the UI
📥 Excel import for bulk student and faculty upload
Seating Algorithm

🔀 Branch interleaving — no two students from the same branch sit side by side
🪑 1 student per seat, 6 columns × 8 rows per hall (configurable per hall)
👨‍🏫 2–3 faculty randomly assigned per hall as invigilators
📊 Tracks seating history across exams

PDF Generation

📄 Page 1 — Master Summary: every room with branch-wise student count breakdown
📄 Page 2+ — Department summaries with invigilator list
📄 Remaining pages — Hall-wise seating grid (roll number + branch abbreviation per cell)
🖨️ Matches university reference format with college logo header
Branch Abbreviations (auto-detected from DB)
Full Name                      Shown As
Chemical Engineering            CHE     
Civil Engineering               Civil
Computer Science&AIM            CSM
ComputerDataScience             CSD
ComputerScience & Engineering   CSE
Electrical & Engineering        EEE
Electronics & Communication Eng ECE
Information Technology          IT 
Mechanical Engineering          MECH 
MBA (HA)                        MBA

🚀 How to Run
bash# 1. Clone or extract the project
cd Sitter-fixed

# 2. Create virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python app.py
Open your browser at: http://127.0.0.1:5000

The SQLite database and all tables are created automatically on first run.


📁 Project Structure
Sitter-fixed/
├── app.py                  # Flask app + all routes
├── models.py               # SQLAlchemy DB models
├── algorithm.py            # Seating + faculty assignment logic
├── pdf_generator.py        # PDF generation (university reference format)
├── supply_routes.py        # Supplementary exam module (Blueprint)
├── requirements.txt
│
├── templates/
│   ├── base.html               # Sidebar layout + flatpickr calendar
│   ├── dashboard.html          # Stats + charts
│   ├── students.html           # Student CRUD + Excel import
│   ├── faculty.html            # Faculty CRUD + Excel import
│   ├── halls.html              # Halls + blocks CRUD (edit/delete/6-col migration)
│   ├── generate.html           # Generate exam plan
│   ├── bulk_generate.html      # Bulk generate (6 exams at once)
│   ├── exams.html              # Exam history list
│   ├── exam_detail.html        # Hall-wise seating grid view
│   ├── results.html            # Manage results
│   ├── student_results.html    # Student-facing results portal
│   └── supply/
│       ├── supply_list.html        # All supplementary exams
│       ├── supply_create.html      # Step 1 — exam details
│       ├── supply_students.html    # Step 2 — add/import students
│       ├── supply_generate.html    # Step 3 — select halls & faculty
│       └── supply_detail.html      # View generated supply plan
│
├── static/
│   └── logo.png                # College logo (place your logo here)
│
├── instance/
│   └── exam_seating.db         # SQLite DB (auto-created on first run)
├── uploads/                    # Temporary Excel upload files
└── outputs/                    # Generated PDF files

📊 Excel Import Format
Students
ColumnRequiredAccepted NamesRoll Number✅roll_number, rollno, roll, htno, regnoBranch✅branch, department, deptSection❌section, secYear❌year
Faculty
ColumnRequiredAccepted NamesName✅name, faculty_name, staff_nameFaculty ID✅faculty_id, fid, emp_id, employee_idContact❌contact, phone, mobileDepartment❌department, dept

Any column name variant is accepted automatically — no strict formatting required.


🏢 Hall Configuration

Default layout: 6 columns × 8 rows = 48 seats per hall
Each seat holds 1 student
Halls are organised into Blocks (A-Block, B-Block, etc.)
Each block has 4 floors × 4 rooms = 16 rooms auto-created
Rows and columns are editable per room from the Halls page
Use the "Set All to 6 Cols" button once after first install to migrate old halls


📄 PDF Structure
Page 1  ─── Master Summary
             Room | Block | Total | CHE | CSD | CSE | ECE | EEE | IT | MECH | MBA
             A101   A-Blk   48      4     5     5     5    5     4    5      5
             ...
             GRAND TOTAL   1840   ...

Page 2  ─── Department Summary (A-Block)
             Hall ID | Hall Name | Students | Faculty Assigned

Page 3+ ─── Seating Grid per Hall
             6 × 8 grid, each cell: Roll Number + Branch abbreviation

⚙️ Validation & Safety

📅 Exam date cannot be set in the past — calendar picker enforces minDate: today
🔒 Supply exam students must already exist in the main student database
⚠️ Capacity check before generation — alerts if selected halls can't fit all students
🔁 Re-generating a supply exam overwrites the previous plan with a confirmation prompt


🛠️ Tech Stack
LayerTechnologyBackendPython 3, FlaskDatabaseSQLAlchemy + SQLiteFrontendBootstrap 5.3, Bootstrap IconsTablesDataTables 1.13CalendarFlatpickrChartsChart.js 4PDFReportLabExcelpandas + openpyxl
