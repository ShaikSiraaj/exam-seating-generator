import os, uuid, re
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from models import db, Batch, Block, Hall, Student, Faculty, Exam, SeatingHistory
from algorithm import assign_seats, assign_faculty
from pdf_generator import generate_pdf
import pandas as pd

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'exam-seating-secret-2024')
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
# Use /tmp for Render free tier, or local instance/ for development
if os.environ.get('RENDER'):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/exam_seating.db'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'exam_seating.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploads')
app.config['OUTPUT_FOLDER'] = os.path.join(BASE_DIR, 'outputs')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, 'instance'), exist_ok=True)

db.init_app(app)

FLOOR_NAMES    = {1: '1st Floor', 2: '2nd Floor', 3: '3rd Floor', 4: '4th Floor'}
ROOMS_PER_FLOOR = 4
FLOORS_PER_BLOCK = 4

def _seed_block_halls(prefix):
    for floor in range(1, FLOORS_PER_BLOCK + 1):
        for room in range(1, ROOMS_PER_FLOOR + 1):
            hall_id   = f"{prefix}{floor}0{room}"
            hall_name = f"Room {hall_id} ({FLOOR_NAMES[floor]})"
            if not Hall.query.filter_by(hall_id=hall_id).first():
                db.session.add(Hall(hall_id=hall_id, hall_name=hall_name,
                                    block_prefix=prefix, cols=6, rows=8))
    db.session.commit()

with app.app_context():
    db.create_all()
    if Block.query.count() == 0:
        defaults = [
            Block(prefix='A', department='CSE', block_name='Admin Block (A-Block)'),
            Block(prefix='B', department='ECE', block_name='B-Block'),
            Block(prefix='C', department='MECH', block_name='C-Block'),
            Block(prefix='D', department='CIVIL', block_name='D-Block'),
            Block(prefix='E', department='EEE', block_name='E-Block'),
        ]
        db.session.add_all(defaults)
        db.session.commit()
    if Hall.query.count() == 0:
        for b in Block.query.all():
            _seed_block_halls(b.prefix)

# ── Helpers ────────────────────────────────────────────────────────────────
def parse_batch_from_filename(filename):
    """Extract AY26-30 → join=2026, passout=2030 from filename like AY26-30.xlsx"""
    name = os.path.splitext(filename)[0].upper().strip()
    # Match patterns: AY26-30, AY2026-2030, AY 26-30
    m = re.search(r'AY\s*(\d{2,4})\s*[-–]\s*(\d{2,4})', name)
    if m:
        jy = int(m.group(1))
        py = int(m.group(2))
        if jy < 100: jy += 2000
        if py < 100: py += 2000
        batch_code = f"AY{str(jy)[2:]}-{str(py)[2:]}"
        return batch_code, jy, py
    return None, None, None

def find_col(cols, candidates):
    for c in candidates:
        if c in cols: return c
    return None

def parse_excel_students(file, batch_code=None):
    path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(path)
    df = pd.read_excel(path)
    df.columns = [str(c).strip().lower().replace(' ','_') for c in df.columns]
    cols = list(df.columns)
    roll_col   = find_col(cols, ['roll_number','rollnumber','roll_no','rollno','roll','htno','ht_no','rno']) or cols[0]
    branch_col = find_col(cols, ['branch','dept','department','stream','course']) or (cols[1] if len(cols)>1 else cols[0])
    sec_col    = find_col(cols, ['section','sec'])
    students   = []
    for _, row in df.iterrows():
        roll   = str(row[roll_col]).strip()
        branch = str(row[branch_col]).strip().upper()
        if roll and roll.lower() not in ('nan','none',''):
            students.append({
                'roll': roll, 'branch': branch,
                'section': str(row[sec_col]).strip() if sec_col else '',
                'batch_code': batch_code
            })
    return students

def parse_excel_faculty(file):
    path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(path)
    df = pd.read_excel(path)
    df.columns = [str(c).strip().lower().replace(' ','_') for c in df.columns]
    cols = list(df.columns)
    name_col    = find_col(cols, ['name','faculty_name','staff_name']) or cols[0]
    id_col      = find_col(cols, ['faculty_id','facultyid','staff_id','emp_id','id']) or (cols[1] if len(cols)>1 else cols[0])
    contact_col = find_col(cols, ['contact','phone','mobile','phone_number']) or (cols[2] if len(cols)>2 else cols[0])
    dept_col    = find_col(cols, ['dept','department'])
    facs = []
    for _, row in df.iterrows():
        name = str(row[name_col]).strip()
        if name and name.lower() not in ('nan','none',''):
            facs.append({
                'name': name,
                'faculty_id': str(row[id_col]).strip(),
                'contact': str(row[contact_col]).strip(),
                'department': str(row[dept_col]).strip() if dept_col else ''
            })
    return facs

def make_pdf_filename(exam_date, exam_name=None, batch_code=None):
    safe_date = exam_date.replace('/', '-').replace(' ', '_')
    safe_name = exam_name.replace(' ', '_').replace('/', '-')[:30] if exam_name else 'exam'
    if batch_code:
        return f"{safe_name}_{batch_code}_{safe_date}.pdf"
    return f"{safe_name}_{safe_date}.pdf"

# ── Dashboard ──────────────────────────────────────────────────────────────
@app.route('/')
def dashboard():
    stats = {
        'students': Student.query.count(),
        'faculty':  Faculty.query.count(),
        'halls':    Hall.query.count(),
        'exams':    Exam.query.count(),
        'batches':  Batch.query.count(),
    }
    recent_exams = Exam.query.order_by(Exam.created_at.desc()).limit(5).all()
    branch_data  = db.session.query(Student.branch, db.func.count(Student.id)).group_by(Student.branch).all()
    batches      = Batch.query.order_by(Batch.join_year).all()
    return render_template('dashboard.html', stats=stats, recent_exams=recent_exams,
                           branch_data=branch_data, batches=batches)

# ── Students ───────────────────────────────────────────────────────────────
@app.route('/students')
def students():
    batch_filter = request.args.get('batch', '')
    batches      = Batch.query.order_by(Batch.join_year).all()
    if batch_filter:
        all_students = Student.query.filter_by(batch_code=batch_filter).order_by(Student.branch, Student.roll_number).all()
    else:
        all_students = Student.query.order_by(Student.branch, Student.roll_number).all()
    branches = db.session.query(Student.branch).distinct().all()
    return render_template('students.html', students=all_students, branches=[b[0] for b in branches],
                           batches=batches, batch_filter=batch_filter)

@app.route('/students/add', methods=['POST'])
def add_student():
    roll   = request.form.get('roll_number','').strip()
    branch = request.form.get('branch','').strip().upper()
    if not roll or not branch:
        flash('Roll number and branch are required.', 'danger')
        return redirect(url_for('students'))
    if Student.query.filter_by(roll_number=roll).first():
        flash(f'Roll number {roll} already exists.', 'warning')
        return redirect(url_for('students'))
    db.session.add(Student(roll_number=roll, branch=branch,
                           batch_code=request.form.get('batch_code') or None,
                           section=request.form.get('section','')))
    db.session.commit()
    flash(f'Student {roll} added.', 'success')
    return redirect(url_for('students'))

@app.route('/students/edit/<int:sid>', methods=['POST'])
def edit_student(sid):
    s = Student.query.get_or_404(sid)
    s.roll_number = request.form.get('roll_number', s.roll_number).strip()
    s.branch      = request.form.get('branch', s.branch).strip().upper()
    s.batch_code  = request.form.get('batch_code') or s.batch_code
    s.section     = request.form.get('section', s.section)
    db.session.commit()
    flash('Student updated.', 'success')
    return redirect(url_for('students'))

@app.route('/students/delete/<int:sid>', methods=['POST'])
def delete_student(sid):
    db.session.delete(Student.query.get_or_404(sid))
    db.session.commit()
    flash('Student deleted.', 'success')
    return redirect(url_for('students'))

@app.route('/students/import', methods=['POST'])
def import_students():
    file = request.files.get('excel_file')
    if not file or not file.filename:
        flash('Please select an Excel file.', 'danger')
        return redirect(url_for('students'))
    try:
        # Auto-detect batch from filename
        batch_code, join_year, passout_year = parse_batch_from_filename(file.filename)

        if batch_code:
            # Create batch if not exists
            existing_batch = Batch.query.filter_by(batch_code=batch_code).first()
            if not existing_batch:
                db.session.add(Batch(batch_code=batch_code, join_year=join_year, passout_year=passout_year))
                db.session.commit()
                flash(f'Batch {batch_code} created automatically from filename.', 'info')
        else:
            # Manual batch selection
            batch_code = request.form.get('batch_code') or None

        rows    = parse_excel_students(file, batch_code)
        added   = 0; skipped = 0
        for r in rows:
            if not Student.query.filter_by(roll_number=r['roll']).first():
                db.session.add(Student(roll_number=r['roll'], branch=r['branch'],
                                       batch_code=r['batch_code'], section=r.get('section','')))
                added += 1
            else:
                skipped += 1
        db.session.commit()
        msg = f'Import complete: {added} added, {skipped} skipped.'
        if batch_code:
            msg += f' Batch: {batch_code}'
        flash(msg, 'success')
    except Exception as e:
        flash(f'Import error: {str(e)}', 'danger')
    return redirect(url_for('students'))

@app.route('/students/delete-all', methods=['POST'])
def delete_all_students():
    batch_code = request.form.get('batch_code')
    if batch_code:
        Student.query.filter_by(batch_code=batch_code).delete()
        flash(f'All students in batch {batch_code} deleted.', 'warning')
    else:
        Student.query.delete()
        flash('All students deleted.', 'warning')
    db.session.commit()
    return redirect(url_for('students'))

# ── Batches ────────────────────────────────────────────────────────────────
@app.route('/batches/add', methods=['POST'])
def add_batch():
    batch_code   = request.form.get('batch_code','').strip().upper()
    join_year    = request.form.get('join_year','').strip()
    passout_year = request.form.get('passout_year','').strip()
    if not batch_code or not join_year or not passout_year:
        flash('All batch fields required.', 'danger')
        return redirect(url_for('students'))
    if Batch.query.filter_by(batch_code=batch_code).first():
        flash(f'Batch {batch_code} already exists.', 'warning')
        return redirect(url_for('students'))
    db.session.add(Batch(batch_code=batch_code, join_year=int(join_year), passout_year=int(passout_year)))
    db.session.commit()
    flash(f'Batch {batch_code} created.', 'success')
    return redirect(url_for('students'))

@app.route('/batches/delete/<int:bid>', methods=['POST'])
def delete_batch(bid):
    b = Batch.query.get_or_404(bid)
    db.session.delete(b)
    db.session.commit()
    flash(f'Batch {b.batch_code} and all its students deleted.', 'warning')
    return redirect(url_for('students'))

# ── Faculty ────────────────────────────────────────────────────────────────
@app.route('/faculty')
def faculty():
    return render_template('faculty.html', faculty=Faculty.query.order_by(Faculty.name).all())

@app.route('/faculty/add', methods=['POST'])
def add_faculty():
    fid  = request.form.get('faculty_id','').strip()
    name = request.form.get('name','').strip()
    if not fid or not name:
        flash('Name and Faculty ID are required.', 'danger')
        return redirect(url_for('faculty'))
    if Faculty.query.filter_by(faculty_id=fid).first():
        flash(f'Faculty ID {fid} already exists.', 'warning')
        return redirect(url_for('faculty'))
    db.session.add(Faculty(name=name, faculty_id=fid,
                           contact=request.form.get('contact',''),
                           department=request.form.get('department','')))
    db.session.commit()
    flash(f'{name} added.', 'success')
    return redirect(url_for('faculty'))

@app.route('/faculty/edit/<int:fid>', methods=['POST'])
def edit_faculty(fid):
    f = Faculty.query.get_or_404(fid)
    f.name       = request.form.get('name', f.name).strip()
    f.faculty_id = request.form.get('faculty_id', f.faculty_id).strip()
    f.contact    = request.form.get('contact', f.contact)
    f.department = request.form.get('department', f.department)
    db.session.commit()
    flash('Faculty updated.', 'success')
    return redirect(url_for('faculty'))
@app.route('/faculty/delete-all', methods=['POST'])
def delete_all_faculty():
    Faculty.query.delete()
    db.session.commit()
    flash('All faculty deleted successfully.', 'success')
    return redirect(url_for('faculty'))
    
@app.route('/faculty/delete/<int:fid>', methods=['POST'])
def delete_faculty(fid):
    db.session.delete(Faculty.query.get_or_404(fid))
    db.session.commit()
    flash('Faculty deleted.', 'success')
    return redirect(url_for('faculty'))

@app.route('/faculty/import', methods=['POST'])
def import_faculty():
    file = request.files.get('excel_file')
    if not file or not file.filename:
        flash('Please select an Excel file.', 'danger')
        return redirect(url_for('faculty'))
    try:
        rows = parse_excel_faculty(file)
        added = 0; skipped = 0
        for r in rows:
            if not Faculty.query.filter_by(faculty_id=r['faculty_id']).first():
                db.session.add(Faculty(name=r['name'], faculty_id=r['faculty_id'],
                                       contact=r.get('contact',''), department=r.get('department','')))
                added += 1
            else:
                skipped += 1
        db.session.commit()
        flash(f'Import complete: {added} added, {skipped} skipped.', 'success')
    except Exception as e:
        flash(f'Import error: {str(e)}', 'danger')
    return redirect(url_for('faculty'))

# ── Halls & Blocks ─────────────────────────────────────────────────────────
@app.route('/halls')
def halls():
    blocks     = Block.query.order_by(Block.prefix).all()
    halls      = Hall.query.order_by(Hall.hall_id).all()
    total_halls = Hall.query.count()
    return render_template('halls.html', blocks=blocks, halls=halls,
                           floor_names=FLOOR_NAMES, total_halls=total_halls)

@app.route('/halls/add', methods=['POST'])
def add_hall():
    hid    = request.form.get('hall_id','').strip()
    hname  = request.form.get('hall_name','').strip()
    prefix = request.form.get('block_prefix','').strip()
    if not hid or not hname or not prefix:
        flash('Hall ID, name and block are required.', 'danger')
        return redirect(url_for('halls'))
    if Hall.query.filter_by(hall_id=hid).first():
        flash(f'Hall ID {hid} already exists.', 'warning')
        return redirect(url_for('halls'))
    db.session.add(Hall(hall_id=hid, hall_name=hname, block_prefix=prefix,
                        cols=int(request.form.get('cols',6)), rows=int(request.form.get('rows',8))))
    db.session.commit()
    flash(f'Hall {hid} added.', 'success')
    return redirect(url_for('halls'))

@app.route('/halls/edit/<int:hid>', methods=['POST'])
def edit_hall(hid):
    h = Hall.query.get_or_404(hid)
    h.hall_name    = request.form.get('hall_name', h.hall_name)
    h.block_prefix = request.form.get('block_prefix', h.block_prefix)
    h.cols         = int(request.form.get('cols', h.cols))
    h.rows         = int(request.form.get('rows', h.rows))
    h.is_active    = 'is_active' in request.form
    db.session.commit()
    flash('Hall updated.', 'success')
    return redirect(url_for('halls'))

@app.route('/halls/delete/<int:hid>', methods=['POST'])
def delete_hall(hid):
    db.session.delete(Hall.query.get_or_404(hid))
    db.session.commit()
    flash('Hall deleted.', 'success')
    return redirect(url_for('halls'))

@app.route('/blocks/add', methods=['POST'])
def add_block():
    prefix = request.form.get('prefix','').strip().upper()
    dept   = request.form.get('department','').strip()
    bname  = request.form.get('block_name','').strip()
    if not prefix or not dept or not bname:
        flash('All block fields are required.', 'danger')
        return redirect(url_for('halls'))
    if Block.query.filter_by(prefix=prefix).first():
        flash(f'Block {prefix} already exists.', 'warning')
        return redirect(url_for('halls'))
    db.session.add(Block(prefix=prefix, department=dept, block_name=bname))
    db.session.commit()
    _seed_block_halls(prefix)
    flash(f'Block {prefix} added with {FLOORS_PER_BLOCK} floors × {ROOMS_PER_FLOOR} rooms.', 'success')
    return redirect(url_for('halls'))

@app.route('/blocks/delete/<int:bid>', methods=['POST'])
def delete_block(bid):
    db.session.delete(Block.query.get_or_404(bid))
    db.session.commit()
    flash('Block deleted.', 'success')
    return redirect(url_for('halls'))

@app.route('/blocks/edit/<int:bid>', methods=['POST'])
def edit_block(bid):
    b = Block.query.get_or_404(bid)
    b.department = request.form.get('department', b.department).strip()
    b.block_name = request.form.get('block_name', b.block_name).strip()
    db.session.commit()
    flash('Block updated.', 'success')
    return redirect(url_for('halls'))

# ── Generate ───────────────────────────────────────────────────────────────
@app.route('/generate', methods=['GET', 'POST'])
def generate():
    batches = Batch.query.order_by(Batch.join_year).all()
    if request.method == 'GET':
        return render_template('generate.html', exams=Exam.query.order_by(Exam.created_at.desc()).all(),
                               student_count=Student.query.count(),
                               faculty_count=Faculty.query.count(),
                               hall_count=Hall.query.filter_by(is_active=True).count(),
                               batches=batches)
    try:
        exam_id    = request.form.get('exam_id','').strip() or f"EX{uuid.uuid4().hex[:6].upper()}"
        exam_name  = request.form.get('exam_name','').strip()
        college    = request.form.get('college','College Name').strip()
        exam_date  = request.form.get('exam_date','').strip()
        session    = request.form.get('session','10:00 AM - 01:00 PM').strip()
        batch_code = request.form.get('batch_code','').strip() or None

        # Validate exam date is not in the past
        from datetime import datetime as _dt
        try:
            _exam_dt = _dt.strptime(exam_date.replace('/', '-'), '%d-%m-%Y').date()
            if _exam_dt < _dt.today().date():
                flash('Exam date cannot be in the past. Please select today or a future date.', 'danger')
                return redirect(url_for('generate'))
        except Exception:
            pass

        if Exam.query.filter_by(exam_id=exam_id).first():
            flash(f'Exam ID {exam_id} already exists.', 'danger')
            return redirect(url_for('generate'))

        q = Student.query
        if batch_code:
            q = q.filter_by(batch_code=batch_code)
        students = [{'roll': s.roll_number, 'branch': s.branch, 'section': s.section} for s in q.all()]

        if not students:
            flash('No students found. Check batch selection.', 'danger')
            return redirect(url_for('generate'))

        faculty_list = [{'name': f.name, 'faculty_id': f.faculty_id, 'contact': f.contact}
                        for f in Faculty.query.filter_by(is_active=True).all()]
        if not faculty_list:
            flash('No faculty in database.', 'danger')
            return redirect(url_for('generate'))

        active_halls = Hall.query.filter_by(is_active=True).order_by(Hall.hall_id).all()
        total_capacity = sum(h.capacity for h in active_halls)
        if len(students) > total_capacity:
            flash(f"Insufficient capacity! Required: {len(students)}, Available: {total_capacity}. Please activate more halls.", "danger")
            return redirect(url_for('generate'))

        halls_data   = [{'hall_id': h.hall_id, 'hall_name': h.hall_name, 'cols': h.cols, 'rows': h.rows} for h in active_halls]
        blocks_data  = [{'prefix': b.prefix, 'department': b.department, 'block_name': b.block_name} for b in Block.query.all()]
        exam_info    = {'exam_id': exam_id, 'exam_name': exam_name, 'college': college,
                        'exam_date': exam_date, 'session': session, 'batch_code': batch_code or ''}

        assignments  = assign_seats(students, halls_data, exam_id)
        hall_faculty = assign_faculty(halls_data, faculty_list)

        exam_obj = Exam(exam_id=exam_id, exam_name=exam_name, college=college,
                        exam_date=exam_date, session=session, batch_code=batch_code,
                        total_students=len(assignments))
        db.session.add(exam_obj)

        for a in assignments:
            fac_str = ', '.join(f.get('name','') for f in hall_faculty.get(a['hall_id'], []))
            db.session.add(SeatingHistory(exam_id=exam_id, roll_number=a['roll'], branch=a['branch'],
                hall_id=a['hall_id'], bench_no=a['bench_no'], seat_pos=a['seat_pos'],
                col=a['col'], row=a['row'], faculty_assigned=fac_str))

        pdf_filename = make_pdf_filename(exam_date, exam_name, batch_code)
        pdf_path     = os.path.join(app.config['OUTPUT_FOLDER'], pdf_filename)
        for h in halls_data:
            h['faculty'] = hall_faculty.get(h['hall_id'], [])

        generate_pdf(assignments, hall_faculty, halls_data, blocks_data, exam_info, pdf_path)
        exam_obj.pdf_filename = pdf_filename
        db.session.commit()

        flash(f'Seating plan generated for {len(assignments)} students!', 'success')
        return redirect(url_for('exam_detail', exam_id=exam_id))

    except Exception as e:
        db.session.rollback()
        import traceback
        flash(f'Error: {str(e)}', 'danger')
        app.logger.error(traceback.format_exc())
        return redirect(url_for('generate'))

# ── Exams ──────────────────────────────────────────────────────────────────
@app.route('/exams')
def exams():
    return render_template('exams.html', exams=Exam.query.order_by(Exam.created_at.desc()).all())

@app.route('/exams/<exam_id>')
def exam_detail(exam_id):
    exam     = Exam.query.filter_by(exam_id=exam_id).first_or_404()
    seatings = SeatingHistory.query.filter_by(exam_id=exam_id).order_by(
               SeatingHistory.hall_id, SeatingHistory.bench_no, SeatingHistory.seat_pos).all()
    by_hall  = {}
    for s in seatings:
        by_hall.setdefault(s.hall_id, []).append(s)
    # Build hall config map (cols/rows) for grid display
    hall_configs = {}
    for h in Hall.query.all():
        hall_configs[h.hall_id] = {'cols': h.cols, 'rows': h.rows}
    return render_template('exam_detail.html', exam=exam, seatings=seatings,
                           by_hall=by_hall, hall_configs=hall_configs)

@app.route('/exams/delete/<exam_id>', methods=['POST'])
def delete_exam(exam_id):
    exam = Exam.query.filter_by(exam_id=exam_id).first_or_404()
    if exam.pdf_filename:
        pdf_path = os.path.join(app.config['OUTPUT_FOLDER'], exam.pdf_filename)
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
    db.session.delete(exam)
    db.session.commit()
    flash('Exam deleted.', 'success')
    return redirect(url_for('exams'))

@app.route('/download/<filename>')
def download(filename):
    return send_file(os.path.join(app.config['OUTPUT_FOLDER'], filename), as_attachment=True)

# ── Bulk Generate ──────────────────────────────────────────────────────────
@app.route('/bulk-generate', methods=['GET', 'POST'])
def bulk_generate():
    batches = Batch.query.order_by(Batch.join_year).all()
    if request.method == 'GET':
        return render_template('bulk_generate.html',
                               student_count=Student.query.count(),
                               faculty_count=Faculty.query.count(),
                               hall_count=Hall.query.filter_by(is_active=True).count(),
                               batches=batches)

    import zipfile, traceback as tb

    college    = request.form.get('college', '').strip()
    session    = request.form.get('session', '10:00 AM - 01:00 PM').strip()
    batch_code = request.form.get('batch_code', '').strip() or None
    results    = []

    q = Student.query
    if batch_code:
        q = q.filter_by(batch_code=batch_code)
    students = [{'roll': s.roll_number, 'branch': s.branch, 'section': s.section} for s in q.all()]

    faculty_list = [{'name': f.name, 'faculty_id': f.faculty_id, 'contact': f.contact}
                    for f in Faculty.query.filter_by(is_active=True).all()]
    active_halls = Hall.query.filter_by(is_active=True).order_by(Hall.hall_id).all()
    total_capacity = sum(h.capacity for h in active_halls)
    if len(students) > total_capacity:
        flash(f"Insufficient capacity for bulk generation! Required: {len(students)}, Available: {total_capacity}.", "danger")
        return redirect(url_for('bulk_generate'))

    halls_data   = [{'hall_id': h.hall_id, 'hall_name': h.hall_name, 'cols': h.cols, 'rows': h.rows} for h in active_halls]
    blocks_data  = [{'prefix': b.prefix, 'department': b.department, 'block_name': b.block_name} for b in Block.query.all()]

    exam_entries = []
    for i in range(1, 7):
        name = request.form.get(f'exam_name_{i}', '').strip()
        date = request.form.get(f'exam_date_{i}', '').strip()
        eid  = request.form.get(f'exam_id_{i}', '').strip()
        if name and date:
            if not eid:
                eid = f"EX{uuid.uuid4().hex[:6].upper()}"
            exam_entries.append({'exam_id': eid, 'exam_name': name, 'exam_date': date})

    if not exam_entries:
        flash('Please fill at least one exam name and date.', 'danger')
        return redirect(url_for('bulk_generate'))

    pdf_paths = []

    for entry in exam_entries:
        exam_id   = entry['exam_id']
        exam_name = entry['exam_name']
        exam_date = entry['exam_date']

        if Exam.query.filter_by(exam_id=exam_id).first():
            results.append({'exam_id': exam_id, 'exam_name': exam_name, 'exam_date': exam_date,
                            'status': 'skipped', 'error': 'Exam ID already exists'})
            continue

        try:
            import random as _rnd
            shuffled = students[:]
            _rnd.shuffle(shuffled)

            exam_info    = {'exam_id': exam_id, 'exam_name': exam_name, 'college': college,
                            'exam_date': exam_date, 'session': session, 'batch_code': batch_code or ''}
            assignments  = assign_seats(shuffled, halls_data, exam_id)
            hall_faculty = assign_faculty(halls_data, faculty_list)

            exam_obj = Exam(exam_id=exam_id, exam_name=exam_name, college=college,
                            exam_date=exam_date, session=session, batch_code=batch_code,
                            total_students=len(assignments))
            db.session.add(exam_obj)

            for a in assignments:
                fac_str = ', '.join(f.get('name','') for f in hall_faculty.get(a['hall_id'], []))
                db.session.add(SeatingHistory(exam_id=exam_id, roll_number=a['roll'], branch=a['branch'],
                    hall_id=a['hall_id'], bench_no=a['bench_no'], seat_pos=a['seat_pos'],
                    col=a['col'], row=a['row'], faculty_assigned=fac_str))

            pdf_filename = make_pdf_filename(exam_date, exam_name, batch_code)
            pdf_path     = os.path.join(app.config['OUTPUT_FOLDER'], pdf_filename)

            halls_with_fac = [dict(h, faculty=hall_faculty.get(h['hall_id'],[])) for h in halls_data]
            generate_pdf(assignments, hall_faculty, halls_with_fac, blocks_data, exam_info, pdf_path)
            exam_obj.pdf_filename = pdf_filename
            db.session.commit()

            pdf_paths.append({'filename': pdf_filename, 'path': pdf_path})
            results.append({'exam_id': exam_id, 'exam_name': exam_name, 'exam_date': exam_date,
                            'status': 'success', 'pdf': pdf_filename, 'count': len(assignments)})

        except Exception as e:
            db.session.rollback()
            app.logger.error(tb.format_exc())
            results.append({'exam_id': exam_id, 'exam_name': exam_name, 'exam_date': exam_date,
                            'status': 'error', 'error': str(e)})

    zip_filename = f"bulk_{batch_code+'_' if batch_code else ''}{uuid.uuid4().hex[:6].upper()}.zip"
    zip_path     = os.path.join(app.config['OUTPUT_FOLDER'], zip_filename)
    with zipfile.ZipFile(zip_path, 'w') as zf:
        for p in pdf_paths:
            zf.write(p['path'], p['filename'])

    flash(f"Bulk complete: {sum(1 for r in results if r['status']=='success')}/{len(exam_entries)} generated.", 'success')
    return render_template('bulk_generate.html',
                           student_count=Student.query.count(),
                           faculty_count=Faculty.query.count(),
                           hall_count=Hall.query.filter_by(is_active=True).count(),
                           batches=batches, results=results,
                           zip_filename=zip_filename if pdf_paths else None)

@app.route('/download-zip/<filename>')
def download_zip(filename):
    return send_file(os.path.join(app.config['OUTPUT_FOLDER'], filename),
                     as_attachment=True, download_name=filename)

# ═══════════════════════════════════════════════════════════════
# RESULTS MODULE
# ═══════════════════════════════════════════════════════════════
from models import ResultSemester, Result

def compute_grade(total, max_marks=100):
    pct = (total / max_marks) * 100 if max_marks else 0
    if pct >= 90: return 'O',   10.0
    if pct >= 80: return 'A+',   9.0
    if pct >= 70: return 'A',    8.0
    if pct >= 60: return 'B+',   7.0
    if pct >= 50: return 'B',    6.0
    if pct >= 40: return 'C',    5.0
    return 'F', 0.0

def parse_results_excel(file, semester_id):
    path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(path)
    df = pd.read_excel(path)
    df.columns = [str(c).strip().lower().replace(' ','_') for c in df.columns]
    cols = list(df.columns)
    roll_col     = find_col(cols, ['roll_number','rollno','roll','htno','ht_no','rno']) or cols[0]
    name_col     = find_col(cols, ['name','student_name','sname'])
    subcode_col  = find_col(cols, ['subject_code','sub_code','code','subcode'])
    subname_col  = find_col(cols, ['subject_name','subject','sub_name','paper'])
    internal_col = find_col(cols, ['internal','internal_marks','ia','cia','sessional'])
    external_col = find_col(cols, ['external','external_marks','theory','sem_marks','end_sem'])
    total_col    = find_col(cols, ['total','total_marks','marks'])
    max_col      = find_col(cols, ['max','max_marks','maximum'])
    grade_col    = find_col(cols, ['grade'])
    gp_col       = find_col(cols, ['grade_points','gp','points'])
    credits_col  = find_col(cols, ['credits','credit','cr'])
    status_col   = find_col(cols, ['status','result','pass_fail'])
    rows = []
    for _, row in df.iterrows():
        roll = str(row[roll_col]).strip()
        if not roll or roll.lower() in ('nan','none',''): continue
        def safe_float(col):
            try: return float(row[col]) if col and str(row[col]) not in ('nan','') else None
            except: return None
        internal = safe_float(internal_col)
        external = safe_float(external_col)
        total    = safe_float(total_col)
        max_m    = safe_float(max_col) or 100.0
        credits  = int(float(row[credits_col])) if credits_col and str(row[credits_col]) not in ('nan','') else None
        if total is None and internal is not None and external is not None:
            total = internal + external
        grade, gp = None, None
        if grade_col and str(row[grade_col]) not in ('nan',''):
            grade = str(row[grade_col]).strip()
            gp    = safe_float(gp_col)
        elif total is not None:
            grade, gp = compute_grade(total, max_m)
        status = 'PASS'
        if status_col and str(row[status_col]) not in ('nan',''):
            status = str(row[status_col]).strip().upper()
        elif grade == 'F':
            status = 'FAIL'
        rows.append(Result(
            semester_id=semester_id,
            roll_number=roll,
            student_name=str(row[name_col]).strip() if name_col and str(row[name_col]) not in ('nan','') else '',
            subject_code=str(row[subcode_col]).strip() if subcode_col else '',
            subject_name=str(row[subname_col]).strip() if subname_col else '',
            internal_marks=internal, external_marks=external,
            total_marks=total, max_marks=max_m,
            grade=grade, grade_points=gp, credits=credits, status=status,
        ))
    return rows

@app.route('/results', endpoint='results')
def results_view():
    semesters = ResultSemester.query.order_by(ResultSemester.created_at.desc()).all()
    return render_template('results.html', semesters=semesters)

@app.route('/results/semester/add', methods=['POST'])
def add_semester():
    db.session.add(ResultSemester(
        name=request.form.get('name','').strip(),
        year=request.form.get('year','').strip(),
        regulation=request.form.get('regulation','').strip(),
        declared_on=request.form.get('declared_on','').strip(),
        is_published='is_published' in request.form,
    ))
    db.session.commit()
    flash('Semester created.', 'success')
    return redirect(url_for('results'))

@app.route('/results/semester/<int:sid>/toggle', methods=['POST'])
def toggle_publish(sid):
    sem = ResultSemester.query.get_or_404(sid)
    sem.is_published = not sem.is_published
    db.session.commit()
    flash(f'Results {"published" if sem.is_published else "unpublished"}.', 'success')
    return redirect(url_for('result_semester', sid=sid))

@app.route('/results/semester/<int:sid>/delete', methods=['POST'])
def delete_semester(sid):
    db.session.delete(ResultSemester.query.get_or_404(sid))
    db.session.commit()
    flash('Semester deleted.', 'success')
    return redirect(url_for('results'))

@app.route('/results/semester/<int:sid>')
def result_semester(sid):
    sem     = ResultSemester.query.get_or_404(sid)
    res     = Result.query.filter_by(semester_id=sid).order_by(Result.roll_number, Result.subject_code).all()
    by_roll = {}
    for r in res:
        by_roll.setdefault(r.roll_number, []).append(r)
    total_students = len(by_roll)
    passed = sum(1 for roll, rlist in by_roll.items() if all(r.status=='PASS' for r in rlist))
    return render_template('result_semester.html', sem=sem, results=res, by_roll=by_roll,
                           total_students=total_students, passed=passed, failed=total_students-passed)

@app.route('/results/semester/<int:sid>/import', methods=['POST'])
def import_results(sid):
    file = request.files.get('excel_file')
    if not file or not file.filename:
        flash('Please select an Excel file.', 'danger')
        return redirect(url_for('result_semester', sid=sid))
    try:
        rows = parse_results_excel(file, sid)
        db.session.add_all(rows)
        db.session.commit()
        flash(f'{len(rows)} result records imported.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Import error: {str(e)}', 'danger')
    return redirect(url_for('result_semester', sid=sid))

@app.route('/results/semester/<int:sid>/add', methods=['POST'])
def add_result(sid):
    try:
        internal = float(request.form.get('internal_marks') or 0)
        external = float(request.form.get('external_marks') or 0)
        total    = internal + external
        max_m    = float(request.form.get('max_marks') or 100)
        grade, gp = compute_grade(total, max_m)
        db.session.add(Result(
            semester_id=sid,
            roll_number=request.form.get('roll_number','').strip(),
            student_name=request.form.get('student_name','').strip(),
            subject_code=request.form.get('subject_code','').strip(),
            subject_name=request.form.get('subject_name','').strip(),
            internal_marks=internal, external_marks=external,
            total_marks=total, max_marks=max_m,
            grade=grade, grade_points=gp,
            credits=int(request.form.get('credits') or 0),
            status='FAIL' if grade=='F' else 'PASS',
        ))
        db.session.commit()
        flash('Result added.', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'danger')
    return redirect(url_for('result_semester', sid=sid))

@app.route('/results/delete/<int:rid>', methods=['POST'])
def delete_result(rid):
    r = Result.query.get_or_404(rid)
    sid = r.semester_id
    db.session.delete(r)
    db.session.commit()
    flash('Result deleted.', 'success')
    return redirect(url_for('result_semester', sid=sid))

@app.route('/results/semester/<int:sid>/clear', methods=['POST'])
def clear_results(sid):
    Result.query.filter_by(semester_id=sid).delete()
    db.session.commit()
    flash('All results cleared.', 'success')
    return redirect(url_for('result_semester', sid=sid))

@app.route('/student-results', methods=['GET','POST'])
def student_results():
    semesters    = ResultSemester.query.filter_by(is_published=True).order_by(ResultSemester.created_at.desc()).all()
    results      = None
    student_info = None
    sem_name     = None
    error        = None
    sgpa         = None
    if request.method == 'POST':
        roll = request.form.get('roll_number','').strip().upper()
        sid  = request.form.get('semester_id','')
        sem  = ResultSemester.query.get(sid)
        if not sem or not sem.is_published:
            error = 'Results not published for this semester.'
        else:
            results = Result.query.filter_by(semester_id=sid, roll_number=roll).order_by(Result.subject_code).all()
            if not results:
                error = f'No results found for Roll Number "{roll}" in {sem.name}.'
            else:
                sem_name     = sem
                student_info = {'roll': roll, 'name': results[0].student_name}
                tc   = sum(r.credits or 0 for r in results)
                wp   = sum((r.grade_points or 0) * (r.credits or 0) for r in results)
                sgpa = round(wp / tc, 2) if tc else None
    return render_template('student_results.html', semesters=semesters, results=results,
                           student_info=student_info, sem_name=sem_name, error=error, sgpa=sgpa)



@app.route('/admin/migrate-halls-6col', methods=['POST'])
def migrate_halls_6col():
    """One-time: update all halls that still have cols=3 to cols=6."""
    updated = Hall.query.filter_by(cols=3).update({'cols': 6})
    db.session.commit()
    flash(f'Updated {updated} halls to 6 columns.', 'success')
    return redirect(url_for('halls'))

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
