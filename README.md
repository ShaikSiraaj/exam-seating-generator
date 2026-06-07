# 🎓 Exam Seating Portal

> A full-stack university admin portal for automated exam seating plan generation, PDF export, and student results management.

---

## ✨ Features

### Core
- 🏛️ **Clean Admin Portal UI** — sidebar navigation, dashboard with live stats and charts.
- 🗃️ **SQLite Database** — handles students, faculty, halls, blocks, exams, and seating history.
- 📋 **Full CRUD Operations** — manage students, faculty, halls, and blocks directly from the UI.
- 📥 **Excel Import** — bulk upload for students, faculty, and exam results.

### Seating Algorithm
- 🔀 **Branch Interleaving** — ensures no two students from the same branch sit side by side.
- 🪑 **Optimized Capacity** — 1 student per seat, configurable grid (default 6 columns × 8 rows).
- 👨‍🏫 **Automated Invigilation** — 2–3 faculty members randomly assigned per hall.
- 📊 **History Tracking** — keeps track of seating assignments across different exams.

### PDF Generation
- 📄 **Master Summary** — Room-wise breakdown with branch-wise student counts.
- 📄 **Department Summaries** — Detailed list of halls and assigned invigilators per department.
- 📄 **Seating Grids** — Hall-wise seating arrangement with roll numbers and branch abbreviations.
- 🖨️ **Professional Layout** — College logo header and university-standard formatting.

### Results Module
- 📈 **Semester Management** — Create and manage results for different semesters.
- 📤 **Bulk Result Import** — Upload student marks from Excel.
- 🎯 **Grade Calculation** — Automatic computation of grades and Grade Points (GP).
- 🎓 **Student Portal** — Dedicated interface for students to check their individual results.

---

## 🚀 How to Run

1. **Clone or extract the project**
   ```bash
   cd Sitter-fixed
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Mac / Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app.py
   ```
   Open your browser at: **http://127.0.0.1:5000**

> [!NOTE]
> The SQLite database and all necessary tables are created automatically on the first run.

---

## 📁 Project Structure

```text
Sitter-fixed/
├── app.py                  # Flask application routes & logic
├── models.py               # SQLAlchemy Database models
├── algorithm.py            # Seating & faculty assignment logic
├── pdf_generator.py        # ReportLab PDF generation logic
├── requirements.txt        # Python dependencies
├── render.yaml             # Render deployment configuration
├── templates/              # HTML templates (Bootstrap 5)
│   ├── base.html           # Main layout
│   ├── dashboard.html      # Stats & charts
│   ├── students.html       # Student management
│   ├── faculty.html        # Faculty management
│   ├── halls.html          # Hall & Block configuration
│   ├── generate.html       # Single exam generation
│   ├── bulk_generate.html  # Bulk exam generation
│   ├── exams.html          # Exam history
│   ├── exam_detail.html    # Detailed seating view
│   ├── results.html        # Results management
│   ├── result_semester.html # Semester-wise results
│   └── student_results.html # Student-facing results portal
├── static/
│   └── logo.png            # College logo (wide banner recommended)
├── instance/               # SQLite database location (auto-created)
├── uploads/                # Temporary Excel upload files (auto-created)
└── outputs/                # Generated PDF files (auto-created)
```

---

## 📊 Data Import Formats

### Students
| Column | Required | Accepted Headers |
|---|---|---|
| Roll Number | ✅ | `roll_number`, `rollno`, `roll`, `htno`, `regno` |
| Branch | ✅ | `branch`, `department`, `dept` |
| Section | ❌ | `section`, `sec` |

### Faculty
| Column | Required | Accepted Headers |
|---|---|---|
| Name | ✅ | `name`, `faculty_name`, `staff_name` |
| Faculty ID | ✅ | `faculty_id`, `fid`, `emp_id` |
| Contact | ❌ | `contact`, `phone` |

### Results
| Column | Required | Accepted Headers |
|---|---|---|
| Roll Number | ✅ | `roll_number`, `rollno`, `htno` |
| Name | ❌ | `name`, `student_name` |
| Subject Code | ✅ | `subject_code`, `subcode` |
| Internal Marks| ❌ | `internal`, `ia`, `sessional` |
| External Marks| ❌ | `external`, `theory`, `sem_marks` |

---

## 🛠️ Tech Stack

- **Backend:** Python 3, Flask
- **Database:** SQLAlchemy + SQLite
- **Frontend:** Bootstrap 5, DataTables, Chart.js
- **PDF:** ReportLab
- **Excel:** pandas, openpyxl

---

## 📝 Configuration & Notes

- **Logo:** Replace `static/logo.png` with your college logo (Recommended aspect ratio: 908 × 130 px).
- **Halls:** Use the "Set All to 6 Cols" button in the Halls page to standardize older hall layouts.
- **Database:** The `instance/exam_seating.db` file contains all your data. Back it up regularly!
