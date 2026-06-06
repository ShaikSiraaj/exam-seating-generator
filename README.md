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
