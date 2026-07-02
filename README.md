# 🎓 Exam Seating Portal

> A full-stack university admin portal for automated exam seating plan generation and PDF export.

🌐 **Live Demo:** https://exam-seating-generator.onrender.com/

---

## ✨ Features

### Core
- 🏛️ Clean admin portal UI — sidebar navigation, dashboard with live stats and charts
- 🗃️ SQLite database — students, faculty, halls, blocks, exams, seating history
- 📋 Full CRUD for students, faculty, halls and blocks directly from the UI
- 📥 Excel import for bulk student and faculty upload

### Seating Algorithm
- 🔀 Branch interleaving — no two students from the same branch sit side by side
- 🪑 1 student per seat, 6 columns × 8 rows per hall (configurable per hall)
- 👨–🏫 2–3 faculty randomly assigned per hall as invigilators
- 📊 Tracks seating history across exams

### PDF Generation
- 📄 Page 1 — Master Summary: every room with branch-wise student count breakdown
- 📄 Page 2+ — Department summaries with invigilator list
- 📄 Remaining pages — Hall-wise seating grid (roll number + branch abbreviation per cell)
- 🖨️ Matches university reference format with college logo header

### Branch Abbreviations (auto-detected from DB)
| Full Name | Shown As |
|---|---|
| Chemical Engineering | CHE |
| Civil Engineering | Civil |
| Computer Science & AIM | CSM |
| Computer Science & DataScience | CSD |
| Computer Science & Engineering | CSE |
| Electrical & Electronics Engineering | EEE |
| Electronics & Communication Engineering | ECE |
| Information Technology | IT |
| Mechanical Engineering | MECH |
| MBA (HA) | MBA |

---

## 🚀 How to Run

```bash
# 1. Clone the repo
git clone https://github.com/ShaikSiraaj/exam-seating-generator.git
cd exam-seating-generator

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
```

Open your browser at: **http://127.0.0.1:5000**

> The SQLite database and all tables are created automatically on first run.

---

## 📁 Project Structure

```
exam-seating-generator/
│
├── app.py                    # Flask app + all routes
├── models.py                 # SQLAlchemy DB models
├── algorithm.py              # Seating + faculty assignment logic
├── pdf_generator.py          # PDF generation (university reference format)
├── requirements.txt          # Python dependencies
│
├── templates/
│   ├── base.html             # Sidebar layout + flatpickr calendar
│   ├── dashboard.html        # Stats + charts
│   ├── students.html         # Student CRUD + Excel import
│   ├── faculty.html          # Faculty CRUD + Excel import
│   ├── halls.html            # Halls + blocks CRUD
│   ├── generate.html         # Generate exam plan
│   ├── bulk_generate.html    # Bulk generate (6 exams at once)
│   ├── exams.html            # Exam history list
│   └── exam_detail.html      # Hall-wise seating grid view
│
├── static/
│   └── logo.png              # College logo
│
├── instance/
│   └── exam_seating.db       # SQLite DB (auto-created on first run)
│
├── uploads/                  # Temporary Excel upload files
└── outputs/                  # Generated PDF files
```

---

## 📊 Excel Import Format

### Students
| Column | Required | Accepted Names |
|---|---|---|
| Roll Number | ✅ | `roll_number`, `rollno`, `roll`, `htno`, `regno` |
| Branch | ✅ | `branch`, `department`, `dept` |
| Section | ❌ | `section`, `sec` |
| Year | ❌ | `year` |

### Faculty
| Column | Required | Accepted Names |
|---|---|---|
| Name | ✅ | `name`, `faculty_name`, `staff_name` |
| Faculty ID | ✅ | `faculty_id`, `fid`, `emp_id`, `employee_id` |
| Contact | ❌ | `contact`, `phone`, `mobile` |
| Department | ❌ | `department`, `dept` |

> Any column name variant is accepted automatically — no strict formatting required.

---

## 🏢 Hall Configuration

- Default layout: **6 columns × 8 rows = 48 seats** per hall
- Each seat holds **1 student**
- Halls are organised into **Blocks** (A-Block, B-Block, etc.)
- Each block has **4 floors × 4 rooms = 16 rooms** auto-created
- Rows and columns are **editable per room** from the Halls page
- Use the **"Set All to 6 Cols"** button once after first install to migrate old halls

---

## 📄 PDF Structure
Page 1  ─── Master Summary
Room | Block | Total | CHE | CSD | CSE | ECE | EEE | IT | MECH | MBA
A101   A-Blk   48      4     5     5     5    5     4    5      5
...
GRAND TOTAL   1840   ...
Page 2  ─── Department Summary (A-Block)
Hall ID | Hall Name | Students | Faculty Assigned
Page 3+ ─── Seating Grid per Hall
6 × 8 grid, each cell: Roll Number + Branch abbreviation

---

## ⚙️ Validation & Safety

- 📅 Exam date cannot be set in the **past** — calendar picker enforces `minDate: today`
- ⚠️ Capacity check before generation — alerts if selected halls can't fit all students

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3, Flask |
| Database | SQLAlchemy + SQLite |
| Frontend | Bootstrap 5.3, Bootstrap Icons |
| Tables | DataTables 1.13 |
| Calendar | Flatpickr |
| Charts | Chart.js 4 |
| PDF | ReportLab |
| Excel | pandas + openpyxl |

---

## 📝 Notes

- Place your college logo at `static/logo.png` — it will appear on all PDF pages and the sidebar.
- The `outputs/` folder holds all generated PDFs. Back it up regularly.
- The `instance/exam_seating.db` file is your entire database — back this up before any updates.

---

## 📜 License

MIT License — see [LICENSE](LICENSE) file for details.

---

Built with ❤️ for Anil Neerukonda Institute of Technology & Sciences (ANITS)
