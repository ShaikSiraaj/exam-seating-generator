from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()

def get_utc_now():
    return datetime.now(timezone.utc)

class Batch(db.Model):
    __tablename__ = 'batches'
    id            = db.Column(db.Integer, primary_key=True)
    batch_code    = db.Column(db.String(20), unique=True, nullable=False)  # e.g. AY26-30
    join_year     = db.Column(db.Integer, nullable=False)   # 2026
    passout_year  = db.Column(db.Integer, nullable=False)   # 2030
    students      = db.relationship('Student', backref='batch', lazy=True, cascade='all, delete-orphan')

    @property
    def current_year_label(self):
        current = get_utc_now().year
        diff = current - self.join_year + 1
        labels = {1: '1st Year', 2: '2nd Year', 3: '3rd Year', 4: '4th Year'}
        return labels.get(diff, f'Year {diff}')

    @property
    def student_count(self):
        return len(self.students)

class Block(db.Model):
    __tablename__ = 'blocks'
    id            = db.Column(db.Integer, primary_key=True)
    prefix        = db.Column(db.String(5), unique=True, nullable=False)
    department    = db.Column(db.String(100), nullable=False)
    block_name    = db.Column(db.String(150), nullable=False)
    halls         = db.relationship('Hall', backref='block', lazy=True, cascade='all, delete-orphan')

    @property
    def floors(self):
        grouped = {1: [], 2: [], 3: [], 4: []}
        for h in sorted(self.halls, key=lambda x: x.hall_id):
            try:
                floor_num = int(str(h.hall_id)[len(self.prefix)])
                if floor_num in grouped:
                    grouped[floor_num].append(h)
            except (ValueError, IndexError):
                grouped[1].append(h)
        return grouped

class Hall(db.Model):
    __tablename__ = 'halls'
    id            = db.Column(db.Integer, primary_key=True)
    hall_id       = db.Column(db.String(20), unique=True, nullable=False)
    hall_name     = db.Column(db.String(150), nullable=False)
    block_prefix  = db.Column(db.String(5), db.ForeignKey('blocks.prefix'), nullable=False)
    cols          = db.Column(db.Integer, default=6)
    rows          = db.Column(db.Integer, default=8)
    is_active     = db.Column(db.Boolean, default=True)

    @property
    def capacity(self):
        return self.cols * self.rows

    @property
    def floor_number(self):
        try:
            return int(str(self.hall_id)[len(self.block_prefix)])
        except (ValueError, IndexError):
            return 1

    @property
    def floor_label(self):
        labels = {1: '1st Floor', 2: '2nd Floor', 3: '3rd Floor', 4: '4th Floor'}
        return labels.get(self.floor_number, f'Floor {self.floor_number}')

class Student(db.Model):
    __tablename__ = 'students'
    id            = db.Column(db.Integer, primary_key=True)
    roll_number   = db.Column(db.String(50), unique=True, nullable=False)
    branch        = db.Column(db.String(50), nullable=False)
    batch_code    = db.Column(db.String(20), db.ForeignKey('batches.batch_code'), nullable=True)
    section       = db.Column(db.String(10), nullable=True)
    created_at    = db.Column(db.DateTime, default=get_utc_now)

class Faculty(db.Model):
    __tablename__ = 'faculty'
    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(150), nullable=False)
    faculty_id    = db.Column(db.String(50), unique=True, nullable=False)
    contact       = db.Column(db.String(20), nullable=True)
    email         = db.Column(db.String(150), nullable=True)
    department    = db.Column(db.String(100), nullable=True)
    is_active     = db.Column(db.Boolean, default=True)
    created_at    = db.Column(db.DateTime, default=get_utc_now)

class Exam(db.Model):
    __tablename__ = 'exams'
    id            = db.Column(db.Integer, primary_key=True)
    exam_id       = db.Column(db.String(50), unique=True, nullable=False)
    exam_name     = db.Column(db.String(255), nullable=False)
    college       = db.Column(db.String(255), nullable=False)
    exam_date     = db.Column(db.String(30), nullable=False)
    session       = db.Column(db.String(50), nullable=False)
    batch_code    = db.Column(db.String(20), nullable=True)
    pdf_filename  = db.Column(db.String(255), nullable=True)
    total_students= db.Column(db.Integer, default=0)
    created_at    = db.Column(db.DateTime, default=get_utc_now)
    seatings      = db.relationship('SeatingHistory', backref='exam', lazy=True, cascade='all, delete-orphan')

class SeatingHistory(db.Model):
    __tablename__ = 'seating_history'
    id            = db.Column(db.Integer, primary_key=True)
    exam_id       = db.Column(db.String(50), db.ForeignKey('exams.exam_id'), nullable=False)
    roll_number   = db.Column(db.String(50), nullable=False)
    branch        = db.Column(db.String(50), nullable=False)
    hall_id       = db.Column(db.String(20), nullable=False)
    bench_no      = db.Column(db.Integer, nullable=False)
    seat_pos      = db.Column(db.Integer, nullable=False)
    col           = db.Column(db.Integer, nullable=False)
    row           = db.Column(db.Integer, nullable=False)
    faculty_assigned = db.Column(db.String(255), nullable=True)

