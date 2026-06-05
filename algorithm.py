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


def snake_distribute(students, halls):
    """
    Fill each hall completely before moving to next.
    Capacity = cols * rows (1 student per seat).
    """
    if not halls or not students:
        return {h['hall_id']: [] for h in halls}

    hall_capacities = {}
    for hall in halls:
        cols = hall.get('cols', 6)
        rows = hall.get('rows', 8)
        hall_capacities[hall['hall_id']] = cols * rows  # 1 student per seat

    hall_ids     = [h['hall_id'] for h in halls]
    hall_buckets = {hid: [] for hid in hall_ids}

    student_index = 0
    total         = len(students)

    for hall_id in hall_ids:
        if student_index >= total:
            break
        cap = hall_capacities[hall_id]
        while student_index < total and len(hall_buckets[hall_id]) < cap:
            hall_buckets[hall_id].append(students[student_index])
            student_index += 1

    return hall_buckets


def assign_seats(students, halls, exam_id):
    """
    Main pipeline:
    1. Interleave all students by branch.
    2. Snake distribute — fill each hall completely.
    3. Assign one student per seat, column by column, row by row.
    """
    if not students or not halls:
        return []

    # Step 1: Interleave by branch
    interleaved_all = interleave_by_branch(students)

    # Step 2: Distribute to halls (1 student per seat)
    hall_buckets = snake_distribute(interleaved_all, halls)

    assignments = []

    for hall in halls:
        hall_id = hall['hall_id']
        cols    = hall.get('cols', 6)
        rows    = hall.get('rows', 8)
        bucket  = hall_buckets.get(hall_id, [])

        if not bucket:
            continue

        # Build seat slots: column by column, row by row
        slots = []
        for col in range(1, cols + 1):
            for row in range(1, rows + 1):
                seat_no = (col - 1) * rows + row
                slots.append({'seat_no': seat_no, 'col': col, 'row': row})

        # Assign 1 student per slot
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
