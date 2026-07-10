import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from collections import defaultdict


def abbr_branch(branch):
    """Returns a short abbreviation for a given branch name."""
    if not branch:
        return ""
    b = branch.strip().upper()

    # Priority matches
    if 'COMPUTER SCIENCE' in b and ('ENGINEERING' in b or 'CSE' in b):
        return 'CSE'
    if 'ELECTRONICS' in b and ('COMMUNICATION' in b or 'ECE' in b):
        return 'ECE'
    if 'ELECTRICAL' in b or 'EEE' in b:
        return 'EEE'
    if 'INFORMATION TECHNOLOGY' in b or b == 'IT':
        return 'IT'
    if 'MECHANICAL' in b or 'MECH' in b:
        return 'MECH'
    if 'CHEMICAL' in b or 'CHE' in b:
        return 'CHE'
    if 'CIVIL' in b:
        return 'Civil'
    if 'DATA' in b and 'SCIENCE' in b:
        return 'CSD'
    if 'AIM' in b:
        return 'CSM'
    if 'MBA' in b:
        return 'MBA'

    # Fallbacks for common abbreviations if they were passed in as full name
    short_forms = {
        'CSE': 'CSE', 'ECE': 'ECE', 'EEE': 'EEE', 'IT': 'IT',
        'MECH': 'MECH', 'CHE': 'CHE', 'CIVIL': 'Civil',
        'CSD': 'CSD', 'CSM': 'CSM', 'MBA': 'MBA'
    }
    return short_forms.get(b, branch)


PAGE_W, PAGE_H = A4
MARGIN_L = 1.8 * cm
MARGIN_R = 1.8 * cm
MARGIN_T = 2.2 * cm
MARGIN_B = 1.5 * cm
BLACK    = colors.black
WHITE    = colors.white

LOGO_PATH = os.path.join(os.path.dirname(__file__), 'static', 'logo.png')
LOGO_H    = 2.1 * cm
LOGO_W    = LOGO_H * (908 / 130)


def draw_logo_header(c, page_w):
    top_y = PAGE_H - MARGIN_T
    if os.path.exists(LOGO_PATH):
        x_logo = (page_w - LOGO_W) / 2
        c.drawImage(LOGO_PATH, x_logo, top_y - LOGO_H,
                    width=LOGO_W, height=LOGO_H,
                    preserveAspectRatio=True, mask='auto')
        banner_bottom = top_y - LOGO_H
    else:
        hh = 1.9 * cm
        c.setStrokeColor(BLACK)
        c.setLineWidth(0.5)
        c.rect(MARGIN_L, top_y - hh, page_w - MARGIN_L - MARGIN_R, hh)
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(page_w / 2, top_y - 0.85 * cm,
                            "Anil Neerukonda Institute of Technology & Sciences (Autonomous)")
        c.setFont("Helvetica", 7.5)
        c.drawCentredString(page_w / 2, top_y - 1.45 * cm,
                            "Sangivalasa-531 162, Bheemunipatnam Mandal, Visakhapatnam District")
        banner_bottom = top_y - hh
    return banner_bottom - 0.2 * cm


def draw_page_header(c, exam_info, hall_name, dept_info, faculty_list, page_w, page_h):
    y = draw_logo_header(c, page_w)

    c.setFillColor(BLACK)
    c.setLineWidth(1.5)
    c.line(MARGIN_L, y, page_w - MARGIN_R, y)
    y -= 0.45 * cm

    c.setFont("Helvetica-Bold", 13)
    title = "SEATING PLAN - ABSTRACT"
    c.drawCentredString(page_w / 2, y, title)
    tw = c.stringWidth(title, "Helvetica-Bold", 13)
    c.setLineWidth(0.8)
    c.line((page_w - tw) / 2, y - 2, (page_w + tw) / 2, y - 2)
    y -= 0.5 * cm

    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(page_w / 2, y, exam_info.get('exam_name', ''))
    y -= 0.5 * cm

    batch_code = exam_info.get('batch_code', '')
    if batch_code:
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(page_w / 2, y, f"Batch : {batch_code}")
        y -= 0.42 * cm

    c.setFont("Helvetica-Bold", 9)
    c.drawString(MARGIN_L, y, f"Date : {exam_info.get('exam_date', 'N/A')}")
    c.drawString(page_w / 2, y, f"Room : {hall_name}")
    y -= 0.42 * cm

    c.setFont("Helvetica-Bold", 9)
    c.drawString(MARGIN_L, y, f"Session : {exam_info.get('session', '10:00 AM - 01:00 PM')}")
    algo = exam_info.get('algorithm', 'standard').title()
    c.drawString(page_w / 2, y, f"Algorithm : {algo}")
    y -= 0.42 * cm

    c.setFont("Helvetica", 8)
    dept_str = f"Department : {dept_info.get('department', '')}   |   Block : {dept_info.get('block_name', '')}"
    c.drawString(MARGIN_L, y, dept_str)
    y -= 0.42 * cm

    if faculty_list:
        fac_str = "Invigilators : " + "  |  ".join(
            f"{f.get('name', '')} ({f.get('faculty_id', '')})" for f in faculty_list)
        c.setFont("Helvetica", 8)
        while c.stringWidth(fac_str, "Helvetica", 8) > (page_w - MARGIN_L - MARGIN_R) and '  |  ' in fac_str:
            fac_str = fac_str.rsplit('  |  ', 1)[0] + '  |  ...'
        c.drawString(MARGIN_L, y, fac_str)
        y -= 0.38 * cm

    c.setLineWidth(0.5)
    c.line(MARGIN_L, y, page_w - MARGIN_R, y)
    return y - 0.3 * cm


def draw_dept_summary(c, dept_info, dept_halls, hall_faculty, by_hall, exam_info, page_w, page_h):
    y = draw_logo_header(c, page_w)

    c.setFillColor(BLACK)
    c.setLineWidth(1.5)
    c.line(MARGIN_L, y, page_w - MARGIN_R, y)
    y -= 0.45 * cm

    c.setFont("Helvetica-Bold", 13)
    title = "DEPARTMENT SEATING SUMMARY"
    c.drawCentredString(page_w / 2, y, title)
    tw = c.stringWidth(title, "Helvetica-Bold", 13)
    c.setLineWidth(0.8)
    c.line((page_w - tw) / 2, y - 2, (page_w + tw) / 2, y - 2)
    y -= 0.5 * cm

    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(page_w / 2, y, exam_info.get('exam_name', ''))
    y -= 0.45 * cm

    batch_code = exam_info.get('batch_code', '')
    if batch_code:
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(page_w / 2, y, f"Batch : {batch_code}")
        y -= 0.42 * cm

    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(page_w / 2, y,
        f"Department : {dept_info.get('department', '')}   |   Block : {dept_info.get('block_name', '')}")
    y -= 0.35 * cm
    c.setLineWidth(0.5)
    c.line(MARGIN_L, y, page_w - MARGIN_R, y)
    y -= 0.4 * cm

    col_w   = [2.2*cm, 5*cm, 2*cm, 7.3*cm]
    xs      = [MARGIN_L]
    for w in col_w[:-1]:
        xs.append(xs[-1] + w)

    rh      = 0.62 * cm
    headers = ["Hall ID", "Hall Name", "Students", "Faculty Assigned"]

    c.setFillColor(BLACK)
    c.rect(MARGIN_L, y - rh, sum(col_w), rh, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 8.5)
    for hdr, xp in zip(headers, xs):
        c.drawString(xp + 0.12*cm, y - rh*0.65, hdr)
    # Vertical lines in header (white on black)
    c.setStrokeColor(WHITE)
    c.setLineWidth(0.4)
    for xp in xs[1:]:
        c.line(xp, y, xp, y - rh)
    c.line(MARGIN_L, y, MARGIN_L, y - rh)
    c.line(MARGIN_L + sum(col_w), y, MARGIN_L + sum(col_w), y - rh)
    c.setFillColor(BLACK)
    y -= rh

    total = 0
    for ri, hall in enumerate(dept_halls):
        hid   = hall['hall_id']
        hname = hall.get('hall_name', hid)
        count = len(by_hall.get(hid, []))
        total += count
        facs  = hall_faculty.get(hid, [])
        fstr  = ", ".join(f"{f.get('name', '')} ({f.get('faculty_id', '')})" for f in facs)

        c.setStrokeColor(BLACK)
        c.setLineWidth(0.3)
        # Horizontal top line
        c.line(MARGIN_L, y, MARGIN_L + sum(col_w), y)
        # Vertical column lines
        for xp in xs[1:]:
            c.line(xp, y, xp, y - rh)
        # Left and right borders
        c.line(MARGIN_L, y, MARGIN_L, y - rh)
        c.line(MARGIN_L + sum(col_w), y, MARGIN_L + sum(col_w), y - rh)

        c.setFont("Helvetica-Bold", 8)
        c.drawString(xs[0]+0.12*cm, y-rh*0.65, hid)
        c.setFont("Helvetica", 8)
        c.drawString(xs[1]+0.12*cm, y-rh*0.65, hname[:38])
        c.drawString(xs[2]+0.12*cm, y-rh*0.65, str(count))
        c.drawString(xs[3]+0.12*cm, y-rh*0.65, fstr[:55])
        y -= rh

    c.setStrokeColor(BLACK)
    c.setLineWidth(0.3)
    c.line(MARGIN_L, y, MARGIN_L + sum(col_w), y)
    c.setFillColor(BLACK)
    c.rect(MARGIN_L, y - rh, sum(col_w), rh, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(xs[0]+0.12*cm, y-rh*0.65, "TOTAL")
    c.drawString(xs[2]+0.12*cm, y-rh*0.65, str(total))
    # Vertical lines in total row (white on black)
    c.setStrokeColor(WHITE)
    c.setLineWidth(0.4)
    for xp in xs[1:]:
        c.line(xp, y, xp, y - rh)
    c.line(MARGIN_L, y, MARGIN_L, y - rh)
    c.line(MARGIN_L + sum(col_w), y, MARGIN_L + sum(col_w), y - rh)
    c.setFillColor(BLACK)
    # Bottom closing line
    c.setStrokeColor(BLACK)
    c.setLineWidth(0.5)
    c.line(MARGIN_L, y - rh, MARGIN_L + sum(col_w), y - rh)
    y -= rh + 0.3 * cm

    c.setFont("Helvetica-Bold", 9)
    c.drawString(MARGIN_L, y,
        f"Date : {exam_info.get('exam_date', 'N/A')}   |   Session : {exam_info.get('session', '')}")


def draw_master_plan(c, assignments, hall_faculty, halls, exam_info, page_w, page_h):
    """
    Page 1 of PDF — Master Summary.
    Every room with branch-wise student count. No invigilators. Black and bold only.
    e.g.  A101 | Total:48 | CSE:10, ECE:8, EEE:6 ...
    """
    # Build hall_id -> {branch_abbr: count}
    hall_branch = defaultdict(lambda: defaultdict(int))
    for a in assignments:
        br = abbr_branch(a['branch'])
        hall_branch[a['hall_id']][br] += 1

    # Draw logo + header
    y = draw_logo_header(c, page_w)

    c.setFillColor(BLACK)
    c.setLineWidth(1.5)
    c.line(MARGIN_L, y, page_w - MARGIN_R, y)
    y -= 0.45 * cm

    c.setFont("Helvetica-Bold", 14)
    title = "MASTER SEATING PLAN — ROOM WISE SUMMARY"
    c.drawCentredString(page_w / 2, y, title)
    tw = c.stringWidth(title, "Helvetica-Bold", 14)
    c.setLineWidth(0.8)
    c.line((page_w - tw) / 2, y - 2, (page_w + tw) / 2, y - 2)
    y -= 0.55 * cm

    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(page_w / 2, y, exam_info.get('exam_name', ''))
    y -= 0.42 * cm

    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(page_w / 2, y,
        f"Date : {exam_info.get('exam_date', '')}   |   Session : {exam_info.get('session', '')}")
    y -= 0.35 * cm

    c.setLineWidth(0.5)
    c.line(MARGIN_L, y, page_w - MARGIN_R, y)
    y -= 0.45 * cm

    # Collect all unique branch abbreviations across all halls
    all_branches = sorted(set(
        br for hb in hall_branch.values() for br in hb.keys()
    ))

    # Column widths — no invigilator column
    col_room  = 1.5 * cm
    col_block = 1.8 * cm
    col_total = 1.2 * cm
    usable_w  = page_w - MARGIN_L - MARGIN_R
    branch_total_w = usable_w - col_room - col_block - col_total
    col_br = branch_total_w / max(len(all_branches), 1)
    col_br = max(0.9 * cm, min(col_br, 2.2 * cm))

    total_w = col_room + col_block + col_total + col_br * len(all_branches)

    # Build x positions
    xs = [MARGIN_L,
          MARGIN_L + col_room,
          MARGIN_L + col_room + col_block]
    for i in range(len(all_branches)):
        xs.append(MARGIN_L + col_room + col_block + col_total + i * col_br)

    row_h = 0.52 * cm

    def draw_header_row(y_pos):
        c.setFillColor(BLACK)
        c.rect(MARGIN_L, y_pos - row_h, total_w, row_h, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 6.5)
        c.drawString(xs[0] + 0.1*cm, y_pos - row_h*0.65, "Room")
        c.drawString(xs[1] + 0.1*cm, y_pos - row_h*0.65, "Block")
        c.drawString(xs[2] + 0.1*cm, y_pos - row_h*0.65, "Total")
        for i, br in enumerate(all_branches):
            c.drawString(xs[3 + i] + 0.1*cm, y_pos - row_h*0.65, br)
        # Vertical lines inside header
        c.setStrokeColor(WHITE)
        c.setLineWidth(0.4)
        for x_line in xs[1:]:
            c.line(x_line, y_pos, x_line, y_pos - row_h)
        # Right border
        c.line(MARGIN_L + total_w, y_pos, MARGIN_L + total_w, y_pos - row_h)
        c.setFillColor(BLACK)
        return y_pos - row_h

    y = draw_header_row(y)

    # Sort halls by hall_id
    sorted_halls = sorted(halls, key=lambda h: h['hall_id'])

    grand_total  = 0
    grand_branch = defaultdict(int)

    for ri, hall in enumerate(sorted_halls):
        hid    = hall['hall_id']
        block  = hid[0] + "-Block"
        counts = hall_branch.get(hid, {})
        total  = sum(counts.values())
        if total == 0:
            continue

        grand_total += total
        for br, cnt in counts.items():
            grand_branch[br] += cnt

        # Draw only top horizontal line per row (cleaner look)
                # Horizontal top line
        c.setStrokeColor(BLACK)
        c.setLineWidth(0.3)
        c.line(MARGIN_L, y, MARGIN_L + total_w, y)
        # Vertical column lines
        c.setLineWidth(0.3)
        for x_line in xs[1:]:
            c.line(x_line, y, x_line, y - row_h)
        # Left and right border verticals
        c.line(MARGIN_L, y, MARGIN_L, y - row_h)
        c.line(MARGIN_L + total_w, y, MARGIN_L + total_w, y - row_h)

        # Room ID — bold
        c.setFont("Helvetica-Bold", 7)
        c.drawString(xs[0] + 0.1*cm, y - row_h*0.65, hid)

        # Block
        c.setFont("Helvetica", 6.5)
        c.drawString(xs[1] + 0.1*cm, y - row_h*0.65, block)

        # Total — bold
        c.setFont("Helvetica-Bold", 7)
        c.drawString(xs[2] + 0.1*cm, y - row_h*0.65, str(total))

        # Branch counts
        for i, br in enumerate(all_branches):
            cnt = counts.get(br, 0)
            if cnt > 0:
                c.setFont("Helvetica-Bold", 6.5)
                c.drawString(xs[3 + i] + 0.1*cm, y - row_h*0.65, str(cnt))
            else:
                c.setFont("Helvetica", 6.5)
                c.drawString(xs[3 + i] + 0.1*cm, y - row_h*0.65, "-")

        y -= row_h

        # New page if running out of space
        if y < MARGIN_B + 2 * cm:
            c.showPage()
            y = PAGE_H - MARGIN_T - 0.5 * cm
            c.setFillColor(BLACK)
            c.setFont("Helvetica-Bold", 9)
            c.drawCentredString(page_w / 2, y,
                f"MASTER SUMMARY (continued) — {exam_info.get('exam_name', '')}")
            y -= 0.5 * cm
            y = draw_header_row(y)

    # Grand Total footer row — black fill, white bold text
    # Grand total — top line, black fill, white text
    c.setStrokeColor(BLACK)
    c.setLineWidth(0.3)
    c.line(MARGIN_L, y, MARGIN_L + total_w, y)
    c.setFillColor(BLACK)
    c.rect(MARGIN_L, y - row_h, total_w, row_h, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(xs[0] + 0.1*cm, y - row_h*0.65, "GRAND TOTAL")
    c.drawString(xs[2] + 0.1*cm, y - row_h*0.65, str(grand_total))
    for i, br in enumerate(all_branches):
        cnt = grand_branch.get(br, 0)
        c.drawString(xs[3 + i] + 0.1*cm, y - row_h*0.65, str(cnt) if cnt else "-")
    # Vertical lines in grand total row (white so visible on black)
    c.setStrokeColor(WHITE)
    c.setLineWidth(0.4)
    for x_line in xs[1:]:
        c.line(x_line, y, x_line, y - row_h)
    c.line(MARGIN_L, y, MARGIN_L, y - row_h)
    c.line(MARGIN_L + total_w, y, MARGIN_L + total_w, y - row_h)
    c.setFillColor(BLACK)
    # Bottom closing line
    c.setStrokeColor(BLACK)
    c.setLineWidth(0.5)
    c.line(MARGIN_L, y - row_h, MARGIN_L + total_w, y - row_h)


def generate_pdf(assignments, hall_faculty, halls, blocks, exam_info, output_path):
    c = canvas.Canvas(output_path, pagesize=A4)
    page_w, page_h = A4

    block_map = {b['prefix']: b for b in blocks}
    by_hall   = defaultdict(list)
    for a in assignments:
        by_hall[a['hall_id']].append(a)

    for hall in halls:
        hall['faculty'] = hall_faculty.get(hall['hall_id'], [])

    block_halls = defaultdict(list)
    for hall in halls:
        prefix = hall['hall_id'][0]
        block_halls[prefix].append(hall)

    # ── Page 1: Master Plan ──────────────────────────────────────────────────
    draw_master_plan(c, assignments, hall_faculty, halls, exam_info, page_w, page_h)
    c.showPage()

    # ── Per-department pages ─────────────────────────────────────────────────
    for prefix, dept_halls in sorted(block_halls.items()):
        dept_info = block_map.get(prefix, {
            'department': prefix, 'block_name': prefix+'-Block', 'prefix': prefix})

        # Department summary page
        draw_dept_summary(c, dept_info, dept_halls, hall_faculty, by_hall, exam_info, page_w, page_h)
        c.showPage()

        # Individual hall pages
        for hall in dept_halls:
            hall_id   = hall['hall_id']
            hall_name = hall.get('hall_name', hall_id)
            cols      = hall.get('cols', 6)
            rows      = hall.get('rows', 8)
            fac_list  = hall.get('faculty', [])

            hall_asgn = by_hall.get(hall_id, [])
            hall_asgn.sort(key=lambda x: (x['col'], x['row'], x['seat_pos']))

            if not hall_asgn:
                continue

            # 1 student per seat
            seat_data = {}
            for a in hall_asgn:
                seat_data[a['bench_no']] = (a['roll'], abbr_branch(a['branch']))

            display_benches = []
            for row in range(1, rows + 1):
                for col in range(1, cols + 1):
                    bench_no = (col - 1) * rows + row
                    display_benches.append((bench_no, seat_data.get(bench_no, ('', '')), row, col))

            BOX_W   = (page_w - MARGIN_L - MARGIN_R - (cols - 1) * 0.2 * cm) / cols
            BOX_H   = 1.5 * cm
            ROW_GAP = 0.22 * cm

            # Auto-scale fonts based on box width
            roll_font_size   = max(6.0, min(8.5, BOX_W / 1.8))
            branch_font_size = max(5.0, min(7.0, BOX_W / 2.2))

            header_h      = 7.0 * cm
            usable_h      = page_h - MARGIN_T - MARGIN_B - header_h
            rows_per_page = max(1, int(usable_h / (BOX_H + ROW_GAP)))

            bench_rows  = [display_benches[i:i+cols] for i in range(0, len(display_benches), cols)]
            page_groups = [bench_rows[i:i+rows_per_page] for i in range(0, len(bench_rows), rows_per_page)]
            if not page_groups:
                page_groups = [[]]

            for page_bench_rows in page_groups:
                start_y = draw_page_header(c, exam_info, hall_name, dept_info, fac_list, page_w, page_h)
                y = start_y

                for bench_row in page_bench_rows:
                    x = MARGIN_L
                    for (bench_no, seat, row, col) in bench_row:
                        roll, branch = seat if seat else ('', '')
                        c.setFillColor(BLACK)
                        c.setStrokeColor(BLACK)
                        c.setLineWidth(1.0)
                        c.rect(x, y - BOX_H, BOX_W, BOX_H)

                        if roll:
                            c.setFillColor(BLACK)
                            c.setFont("Helvetica-Bold", roll_font_size)
                            c.drawCentredString(x + BOX_W/2, y - BOX_H*0.38, roll)
                            c.setFont("Helvetica-Bold", branch_font_size)
                            c.drawCentredString(x + BOX_W/2, y - BOX_H*0.65, branch)
                        else:
                            c.setFillColor(BLACK)
                            c.setFont("Helvetica", 7.5)
                            c.drawCentredString(x + BOX_W/2, y - BOX_H*0.54, "VACANT")

                        x += BOX_W + 0.2 * cm
                    y -= (BOX_H + ROW_GAP)

                c.showPage()

    c.save()
    return output_path