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


def snake_distribute(students, halls, algorithm='standard'):
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

    If algorithm is 'diamond', all halls use checkerboard pattern.

    Returns (hall_buckets, checkerboard_halls) where checkerboard_halls
    is the set of hall_ids that were seated in checkerboard mode.
    """
    if not halls or not students:
        return {h['hall_id']: [] for h in halls}, set()

    hall_ids     = [h['hall_id'] for h in halls]
    hall_buckets = {hid: [] for hid in hall_ids}
    checkerboard_halls = set()

    student_index = 0
    total         = len(students)

    for hall in halls:
        hall_id = hall['hall_id']
        if student_index >= total:
            break

        cols = hall.get('cols', 6)
        rows = hall.get('rows', 8)
        full_cap = cols * rows

        if algorithm == 'diamond':
            cap = checkerboard_capacity(cols, rows)
            checkerboard_halls.add(hall_id)
        else:
            # Peek at the next full-capacity-sized block to see whether it's
            # made up of a single branch (no mixing possible) or several.
            window = students[student_index:student_index + full_cap]
            branches_in_window = {s['branch'] for s in window}

            if len(branches_in_window) == 1:
                cap = checkerboard_capacity(cols, rows)
                checkerboard_halls.add(hall_id)
            else:
                cap = full_cap

        bucket = students[student_index:student_index + cap]
        hall_buckets[hall_id] = bucket
        student_index += len(bucket)

    return hall_buckets, checkerboard_halls


def assign_seats(students, halls, exam_id, algorithm='standard'):
    """
    Main pipeline:
    1. Interleave all students by branch.
    2. Snake distribute — fill each hall completely (or to checkerboard
       capacity if a hall would otherwise be single-branch or if
       algorithm is 'diamond').
    3. Assign one student per seat, column by column, row by row —
       using every seat for mixed-branch halls, or only the checkerboard
       seats (with the rest left VACANT) for checkerboard halls.
    """
    if not students or not halls:
        return []

    interleaved_all = interleave_by_branch(students)
    hall_buckets, checkerboard_halls = snake_distribute(interleaved_all, halls, algorithm)

    assignments = []

    for hall in halls:
        hall_id = hall['hall_id']
        cols    = hall.get('cols', 6)
        rows    = hall.get('rows', 8)
        bucket  = hall_buckets.get(hall_id, [])

        if not bucket:
            continue

        if hall_id in checkerboard_halls:
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
                'checkerboard': hall_id in checkerboard_halls,
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


def assign_seats_mid(students_y1, students_y2, selected_halls, exam_id):
    """
    Specialized Mid Exam seating allocation.
    - students_y1: list of student dicts from Year 1 file.
    - students_y2: list of student dicts from Year 2 file.
    - selected_halls: list of hall configurations.
    - exam_id: association ID.

    Step 1: Data preparation
    Sort and shuffle both lists to randomize and break clusters.
    Step 2 & 3: Interleaved Distribution with Column Offset
    Seat students into rows/columns of the halls alternating Year 1 and Year 2.
    Row 1: [Y1] [Y2] [Y1] [Y2]... (starts with Y1)
    Row 2: [Y2] [Y1] [Y2] [Y1]... (shifted by 1, starts with Y2)
    Step 4: Adjacency conflict validation & backtracking-swap
    No two students of same year and same branch should be adjacent in 8 directions.
    """
    # Sort by roll to ensure roll-number wise assignment initially
    students_y1 = sorted(students_y1, key=lambda s: s.get('roll', ''))
    students_y2 = sorted(students_y2, key=lambda s: s.get('roll', ''))

    # Shuffle to break friend clusters
    random.shuffle(students_y1)
    random.shuffle(students_y2)

    assignments = []

    pool_y1 = list(students_y1)
    pool_y2 = list(students_y2)

    for hall in selected_halls:
        hall_id = hall['hall_id']
        cols = hall.get('cols', 6)
        rows = hall.get('rows', 8)

        # 2D Grid to track placed students in this hall (key is (r, c))
        grid = {}

        for r in range(1, rows + 1):
            for c in range(1, cols + 1):
                if not pool_y1 and not pool_y2:
                    break

                # Step 2: Determine target year based on row and col parity
                # (r + c) % 2 == 0 -> Year 1
                # (r + c) % 2 == 1 -> Year 2
                is_y1 = ((r + c) % 2 == 0)

                target_pool = pool_y1 if is_y1 else pool_y2
                other_pool = pool_y2 if is_y1 else pool_y1
                current_year_label = 'Year 1' if is_y1 else 'Year 2'
                other_year_label = 'Year 2' if is_y1 else 'Year 1'

                if not target_pool:
                    # Fallback to other pool if target is empty
                    target_pool = other_pool
                    other_pool = []
                    current_year_label = other_year_label

                if not target_pool:
                    break

                # Find a student who doesn't cause any adjacency conflict
                chosen_idx = -1
                for idx, s in enumerate(target_pool):
                    conflict = False
                    s_branch = s.get('branch', '').upper()

                    # 8 directions checking
                    for dr, dc in [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (-1,1), (1,-1), (1,1)]:
                        nr, nc = r + dr, c + dc
                        neighbor = grid.get((nr, nc))
                        if neighbor:
                            n_year = neighbor.get('year')
                            n_branch = neighbor.get('branch', '').upper()
                            if n_year == current_year_label and n_branch == s_branch:
                                conflict = True
                                break
                    if not conflict:
                        chosen_idx = idx
                        break

                # Backtracking swap: if conflict detected for all remaining in target_pool,
                # we fallback to first student
                if chosen_idx == -1:
                    chosen_idx = 0

                student = target_pool.pop(chosen_idx)
                student['year'] = current_year_label

                # Place in grid
                grid[(r, c)] = student

                # Seat number is column-by-column, row-by-row
                seat_no = (c - 1) * rows + r
                assignments.append({
                    'roll': student['roll'],
                    'branch': student['branch'],
                    'hall_id': hall_id,
                    'exam_id': exam_id,
                    'bench_no': seat_no,
                    'seat_pos': 1,
                    'col': c,
                    'row': r,
                    'checkerboard': False,
                })

    return assignments
