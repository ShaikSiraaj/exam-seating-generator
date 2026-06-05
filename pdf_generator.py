import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from collections import defaultdict

# Branch abbreviation map — keys match uppercase DB values
BRANCH_ABBR = {
    'CHEMICAL': 'CHE',
    'CIVIL': 'Civil',
    'AIM': 'CSM',
    'DATASCIENCE': 'CSD',
    'DATA SCIENCE': 'CSD',
    'COMPUTER SCIENCE ENGINEERING': 'CSE',
    'ELECTRICAL ELECTRONICS': 'EEE',
    'ELECTRONICS COMMUNICATION': 'ECE',
    'ELECTRONICS': 'ECE',
    'INFORMATION': 'IT',
    'IT': 'IT',
    'MECHANICAL': 'MECH',
    'MECH': 'MECH',
    'MBA': 'MBA',
    'COMPUTER SCIENCE': 'CSE',
}

def abbr_branch(branch):
    b = branch.strip().upper()
    if 'CHEMICAL' in b:
        return 'CHE'
    if 'CIVIL' in b:
        return 'Civil'
    if 'AIM' in b:
        return 'CSM'
    if 'DATASCIENCE' in b or 'DATA SCIENCE' in b:
        return 'CSD'
    if 'COMPUTER SCIENCE' in b and 'ENGINEERING' in b:
        return 'CSE'
    if 'ELECTRICAL' in b and 'ELECTRONICS' in b:
        return 'EEE'
    if 'ELECTRONICS' in b and 'COMMUNICATION' in b:
        return 'ECE'
    if 'ELECTRONICS' in b:
        return 'ECE'
    if 'INFORMATION' in b or b == 'IT':
        return 'IT'
    if 'MECHANICAL' in b or b == 'MECH':
        return 'MECH'
    if 'MBA' in b:
        return 'MBA'
    if 'COMPUTER SCIENCE' in b:
        return 'CSE'
    return branch



PAGE_W, PAGE_H = A4
MARGIN_L = 1.8 * cm
MARGIN_R = 1.8 * cm
MARGIN_T = 2.2 * cm
MARGIN_B = 1.5 * cm
BLACK    = colors.black
WHITE    = colors.white

LOGO_PATH = os.path.join(os.path.dirname(__file__), 'static', 'logo.png')

# Logo is a wide banner (908x130) — we scale it to fit the full header width
LOGO_H    = 2.1 * cm   # height on PDF
LOGO_W    = LOGO_H * (908 / 130)  # keep aspect ratio → ~14.6 cm wide

def draw_logo_header(c, page_w):
    """Draw the college logo banner centred at the top. Returns y after the banner."""
    y = page_h = PAGE_H
    top_y = y - MARGIN_T

    if os.path.exists(LOGO_PATH):
        # Center the logo horizontally
        x_logo = (page_w - LOGO_W) / 2
        c.drawImage(LOGO_PATH, x_logo, top_y - LOGO_H,
                    width=LOGO_W, height=LOGO_H,
                    preserveAspectRatio=True, mask='auto')
        banner_bottom = top_y - LOGO_H
    else:
        # Fallback text header
        hh = 1.9 * cm
        c.setStrokeColor(BLACK); c.setLineWidth(0.5)
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
    # Draw college logo banner
    y = draw_logo_header(c, page_w)

    c.setLineWidth(1.5)
    c.line(MARGIN_L, y, page_w - MARGIN_R, y)
    y -= 0.45 * cm

    # Title
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

    # Batch info
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
    y -= 0.42 * cm

    c.setFont("Helvetica", 8)
    dept_str = f"Department : {dept_info.get('department', '')}   |   Block : {dept_info.get('block_name', '')}"
    c.drawString(MARGIN_L, y, dept_str)
    y -= 0.42 * cm

    if faculty_list:
        fac_str = "Invigilators : " + "  |  ".join(
            f"{f.get('name','')} ({f.get('faculty_id','')})" for f in faculty_list)
        c.setFont("Helvetica", 8)
        while c.stringWidth(fac_str, "Helvetica", 8) > (page_w - MARGIN_L - MARGIN_R) and '  |  ' in fac_str:
            fac_str = fac_str.rsplit('  |  ', 1)[0] + '  |  ...'
        c.drawString(MARGIN_L, y, fac_str)
        y -= 0.38 * cm

    c.setLineWidth(0.5)
    c.line(MARGIN_L, y, page_w - MARGIN_R, y)
    return y - 0.3 * cm


def draw_dept_summary(c, dept_info, dept_halls, hall_faculty, by_hall, exam_info, page_w, page_h):
    # Draw college logo banner
    y = draw_logo_header(c, page_w)

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
        f"Department : {dept_info.get('department','')}   |   Block : {dept_info.get('block_name','')}")
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

    # Header row
    c.setFillColor(colors.HexColor("#1a3c5e"))
    c.rect(MARGIN_L, y - rh, sum(col_w), rh, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 8.5)
    for hdr, xp in zip(headers, xs):
        c.drawString(xp + 0.12*cm, y - rh*0.65, hdr)
    c.setFillColor(BLACK)
    y -= rh

    total = 0
    for ri, hall in enumerate(dept_halls):
        hid   = hall['hall_id']
        hname = hall.get('hall_name', hid)
        count = len(by_hall.get(hid, []))
        total += count
        facs  = hall_faculty.get(hid, [])
        fstr  = ", ".join(f"{f.get('name','')} ({f.get('faculty_id','')})" for f in facs)

        bg = colors.HexColor("#f2f3f4") if ri % 2 == 0 else WHITE
        c.setFillColor(bg)
        c.rect(MARGIN_L, y - rh, sum(col_w), rh, fill=1, stroke=0)
        c.setFillColor(BLACK)
        c.setStrokeColor(colors.HexColor("#cccccc"))
        c.setLineWidth(0.3)
        c.rect(MARGIN_L, y - rh, sum(col_w), rh, fill=0, stroke=1)

        c.setFont("Helvetica-Bold", 8); c.drawString(xs[0]+0.12*cm, y-rh*0.65, hid)
        c.setFont("Helvetica", 8)
        c.drawString(xs[1]+0.12*cm, y-rh*0.65, hname[:38])
        c.drawString(xs[2]+0.12*cm, y-rh*0.65, str(count))
        c.drawString(xs[3]+0.12*cm, y-rh*0.65, fstr[:55])
        y -= rh

    c.setFillColor(colors.HexColor("#d6eaf8"))
    c.rect(MARGIN_L, y - rh, sum(col_w), rh, fill=1, stroke=0)
    c.setFillColor(BLACK)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(xs[0]+0.12*cm, y-rh*0.65, "TOTAL")
    c.drawString(xs[2]+0.12*cm, y-rh*0.65, str(total))
    y -= rh + 0.3 * cm

    c.setFont("Helvetica-Bold", 9)
    c.drawString(MARGIN_L, y,
        f"Date : {exam_info.get('exam_date','N/A')}   |   Session : {exam_info.get('session','')}")


def generate_pdf(assignments, hall_faculty, halls, blocks, exam_info, output_path):
    c = canvas.Canvas(output_path, pagesize=A4)
    page_w, page_h = A4

    hall_map  = {h['hall_id']: h for h in halls}
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

    for prefix, dept_halls in sorted(block_halls.items()):
        dept_info = block_map.get(prefix, {
            'department': prefix, 'block_name': prefix+'-Block', 'prefix': prefix})

        # Dept summary page
        draw_dept_summary(c, dept_info, dept_halls, hall_faculty, by_hall, exam_info, page_w, page_h)
        c.showPage()

        # Individual hall pages
        for hall in dept_halls:
            hall_id   = hall['hall_id']
            hall_name = hall.get('hall_name', hall_id)
            cols      = hall.get('cols', 3)
            rows      = hall.get('rows', 8)
            fac_list  = hall.get('faculty', [])

            hall_asgn = by_hall.get(hall_id, [])
            hall_asgn.sort(key=lambda x: (x['col'], x['row'], x['seat_pos']))

            bench_data = defaultdict(lambda: [('',''),('','')])
            for a in hall_asgn:
                bench_data[a['bench_no']][a['seat_pos']-1] = (a['roll'], abbr_branch(a['branch']))

            display_benches = []
            for row in range(1, rows + 1):
                for col in range(1, cols + 1):
                    bench_no = (col - 1) * rows + row
                    display_benches.append((bench_no, bench_data[bench_no], row, col))

            BOX_W   = (page_w - MARGIN_L - MARGIN_R - (cols - 1) * 0.28 * cm) / cols
            BOX_H   = 1.5 * cm
            ROW_GAP = 0.22 * cm

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
                    for (bench_no, seats, row, col) in bench_row:
                        c.setStrokeColor(BLACK); c.setLineWidth(1.0)
                        c.rect(x, y - BOX_H, BOX_W, BOX_H)

                        roll1, branch1 = seats[0] if seats[0] else ('', '')
                        roll2, branch2 = seats[1] if seats[1] else ('', '')

                        if roll1 and roll2:
                            # Seat 1
                            c.setFont("Helvetica-Bold", 8.5)
                            c.drawCentredString(x + BOX_W/2, y - BOX_H*0.2, roll1)
                            c.setFont("Helvetica", 6.5)
                            c.setFillColor(colors.HexColor("#2e86ab"))
                            c.drawCentredString(x + BOX_W/2, y - BOX_H*0.35, branch1)
                            c.setFillColor(BLACK)
                            # Divider
                            c.setStrokeColor(colors.HexColor("#bbbbbb"))
                            c.setLineWidth(0.4)
                            c.line(x+4, y-BOX_H*0.52, x+BOX_W-4, y-BOX_H*0.52)
                            c.setStrokeColor(BLACK); c.setLineWidth(1.0)
                            # Seat 2
                            c.setFont("Helvetica-Bold", 8.5)
                            c.drawCentredString(x + BOX_W/2, y - BOX_H*0.67, roll2)
                            c.setFont("Helvetica", 6.5)
                            c.setFillColor(colors.HexColor("#2e86ab"))
                            c.drawCentredString(x + BOX_W/2, y - BOX_H*0.82, branch2)
                            c.setFillColor(BLACK)
                        elif roll1:
                            c.setFont("Helvetica-Bold", 8.5)
                            c.drawCentredString(x + BOX_W/2, y - BOX_H*0.38, roll1)
                            c.setFont("Helvetica", 6.5)
                            c.setFillColor(colors.HexColor("#2e86ab"))
                            c.drawCentredString(x + BOX_W/2, y - BOX_H*0.62, branch1)
                            c.setFillColor(BLACK)
                        else:
                            c.setFillColor(colors.HexColor("#aaaaaa"))
                            c.setFont("Helvetica", 7.5)
                            c.drawCentredString(x + BOX_W/2, y - BOX_H*0.54, "VACANT")
                            c.setFillColor(BLACK)

                        x += BOX_W + 0.28 * cm
                    y -= (BOX_H + ROW_GAP)

                c.showPage()

    c.save()
    return output_path
