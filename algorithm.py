import random
from collections import defaultdict
from models import SeatingHistory, db

def get_student_history(roll_number):
    records = SeatingHistory.query.filter_by(roll_number=roll_number).all()
    halls = defaultdict(int)
    seats = defaultdict(int)
    for r in records:
        halls[r.hall_id] += 1
        seat_key = f"{r.hall_id}_c{r.col}_r{r.row}"
        seats[seat_key] += 1
    return halls, seats

def interleave_by_branch(students):
    """
    Interleave students by branch (round-robin), so adjacent seats
    have different branches.
    """
    if not students:
        return []

    groups = defaultdict(lambda: defaultdict(list))
    for s in students:
        groups[s['branch']][s.get('section', '')].append(s)

    branch_queues = {}
    for branch, sections in groups.items():
        sec_list = sorted(sections.keys())
        sec_queues = [sections[sec] for sec in sec_list]
        interleaved_branch = []
        idx = 0
        total_in_branch = sum(len(q) for q in sec_queues)
        while len(interleaved_branch) < total_in_branch:
            q = sec_queues[idx % len(sec_queues)]
            if q:
                interleaved_branch.append(q.pop(0))
            idx += 1
        branch_queues[branch] = interleaved_branch

    sorted_branches = sorted(branch_queues.keys(), key=lambda b: -len(branch_queues[b]))
    queues  = [branch_queues[b] for b in sorted_branches]
    n       = len(queues)
    total   = sum(len(q) for q in queues)
    result  = []
    pointer = 0
    stuck   = 0

    while len(result) < total:
        non_empty = [q for q in queues if q]
        if not non_empty:
            break
        q = queues[pointer % n]
        if q:
            last_branch = result[-1]['branch'] if result else None
            if q[0]['branch'] != last_branch:
                result.append(q.pop(0))
                stuck = 0
            else:
                stuck += 1
                if stuck >= n * 3:
                    for fq in queues:
                        if fq:
                            result.append(fq.pop(0))
                            stuck = 0
                            break
        pointer += 1

    return result


def checkerboard_capacity(cols, rows):
    """
    Number of usable seats in a hall when seating in a checkerboard
    (alternate-seat) pattern: every other seat in every row, offset
    row to row, so no two filled seats touch left-right or front-back.
    """
    count = 0
    for col in range(1, cols + 1):
        for row in range(1, rows + 1):
            if (col + row) % 2 == 0:
                count += 1
    return count


def checkerboard_slots(cols, rows):
    """
    Seat slots usable under the checkerboard pattern, in column-by-column,
    row-by-row order. Only positions where (col + row) is even are filled.
    """
    slots = []
    for col in range(1, cols + 1):
        for row in range(1, rows + 1):
            if (col + row) % 2 == 0:
                seat_no = (col - 1) * rows + row
                slots.append({'seat_no': seat_no, 'col': col, 'row': row})
    return slots


def full_slots(cols, rows):
    """
    Every seat in the hall, column by column, row by row.
    """
    slots = []
    for col in range(1, cols + 1):
        for row in range(1, rows + 1):
            seat_no = (col - 1) * rows + row
            slots.append({'seat_no': seat_no, 'col': col, 'row': row})
    return slots


def snake_distribute(students, halls):
    """
    Fill each hall before moving to the next.

    Normal case: capacity = cols * rows (1 student per seat), filled
    consecutively, since interleave_by_branch() already keeps same-branch
    students from sitting next to each other.

    Single-branch case: if the next block of students destined for a hall
    all belong to the same branch (no other branch left to interleave
    with), that hall is seated in a checkerboard pattern instead — every
    other seat, offset row to row — so same-branch students still never
    sit adjacent. This halves the usable capacity for that hall, so any
    overflow is pushed on to the next hall.

    Returns (hall_buckets, single_branch_halls) where single_branch_halls
    is the set of hall_ids that were seated in checkerboard mode.
    """
    if not halls or not students:
        return {h['hall_id']: [] for h in halls}, set()

    hall_ids     = [h['hall_id'] for h in halls]
    hall_buckets = {hid: [] for hid in hall_ids}
    single_branch_halls = set()

    student_index = 0
    total         = len(students)

    for hall in halls:
        hall_id = hall['hall_id']
        if student_index >= total:
            break

        cols = hall.get('cols', 6)
        rows = hall.get('rows', 8)
        full_cap = cols * rows

        # Peek at the next full-capacity-sized block to see whether it's
        # made up of a single branch (no mixing possible) or several.
        window = students[student_index:student_index + full_cap]
        branches_in_window = {s['branch'] for s in window}

        if len(branches_in_window) == 1:
            cap = checkerboard_capacity(cols, rows)
            single_branch_halls.add(hall_id)
        else:
            cap = full_cap

        bucket = students[student_index:student_index + cap]
        hall_buckets[hall_id] = bucket
        student_index += len(bucket)

    return hall_buckets, single_branch_halls


def assign_seats(students, halls, exam_id):
    """
    Main pipeline:
    1. Interleave all students by branch.
    2. Snake distribute — fill each hall completely (or to checkerboard
       capacity if a hall would otherwise be single-branch).
    3. Assign one student per seat, column by column, row by row —
       using every seat for mixed-branch halls, or only the checkerboard
       seats (with the rest left VACANT) for single-branch halls.
    """
    if not students or not halls:
        return []

    interleaved_all = interleave_by_branch(students)
    hall_buckets, single_branch_halls = snake_distribute(interleaved_all, halls)

    assignments = []

    for hall in halls:
        hall_id = hall['hall_id']
        cols    = hall.get('cols', 6)
        rows    = hall.get('rows', 8)
        bucket  = hall_buckets.get(hall_id, [])

        if not bucket:
            continue

        if hall_id in single_branch_halls:
            slots = checkerboard_slots(cols, rows)
        else:
            slots = full_slots(cols, rows)

        for i, student in enumerate(bucket):
            if i >= len(slots):
                break
            slot = slots[i]
            assignments.append({
                'roll':     str(student['roll']),
                'branch':   student['branch'],
                'hall_id':  hall_id,
                'exam_id':  exam_id,
                'bench_no': slot['seat_no'],   # kept for DB compat, means seat number
                'seat_pos': 1,                  # always 1 (single occupancy)
                'col':      slot['col'],
                'row':      slot['row'],
                'checkerboard': hall_id in single_branch_halls,
            })

    return assignments


def assign_faculty(halls, faculty_list):
    """
    Circular random faculty assignment — 2 or 3 per hall.
    """
    if not faculty_list:
        return {hall['hall_id']: [] for hall in halls}

    shuffled = faculty_list[:]
    random.shuffle(shuffled)
    hall_faculty = {}
    n   = len(shuffled)
    idx = 0

    for hall in halls:
        count    = random.choice([2, 2, 3])
        assigned = [shuffled[(idx + i) % n] for i in range(min(count, n))]
        hall_faculty[hall['hall_id']] = assigned
        idx = (idx + count) % n

    return hall_faculty
