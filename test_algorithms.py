import unittest
from algorithm import assign_seats, checkerboard_capacity, assign_seats_mid

class TestAlgorithms(unittest.TestCase):
    def setUp(self):
        self.halls = [
            {'hall_id': 'A101', 'hall_name': 'Room A101', 'cols': 6, 'rows': 8},
        ]
        self.students = [{'roll': f'S{i}', 'branch': 'CSE'} for i in range(1, 51)]

    def test_standard_algorithm_single_branch(self):
        # In standard mode, single branch should use checkerboard (50% cap)
        # 6x8 = 48 total, checkerboard should be 24
        assignments = assign_seats(self.students, self.halls, 'E1', algorithm='standard')
        hall_a101 = [a for a in assignments if a['hall_id'] == 'A101']
        self.assertEqual(len(hall_a101), 24)
        for a in hall_a101:
            self.assertTrue((a['col'] + a['row']) % 2 == 0)

    def test_diamond_algorithm_mixed_branches(self):
        # In diamond mode, even mixed branches should use checkerboard (50% cap)
        mixed_students = [
            {'roll': 'S1', 'branch': 'CSE'},
            {'roll': 'S2', 'branch': 'ECE'},
            {'roll': 'S3', 'branch': 'CSE'},
            {'roll': 'S4', 'branch': 'ECE'},
        ]
        assignments = assign_seats(mixed_students, self.halls, 'E2', algorithm='diamond')
        hall_a101 = [a for a in assignments if a['hall_id'] == 'A101']
        self.assertEqual(len(hall_a101), 4)
        for a in hall_a101:
            self.assertTrue((a['col'] + a['row']) % 2 == 0)

    def test_standard_algorithm_mixed_branches(self):
        # In standard mode, mixed branches should use 100% cap
        mixed_students = []
        for i in range(24):
            mixed_students.append({'roll': f'CSE{i}', 'branch': 'CSE'})
            mixed_students.append({'roll': f'ECE{i}', 'branch': 'ECE'})

        assignments = assign_seats(mixed_students, self.halls, 'E3', algorithm='standard')
        hall_a101 = [a for a in assignments if a['hall_id'] == 'A101']
        self.assertEqual(len(hall_a101), 48)

    def test_assign_seats_mid(self):
        students_y1 = [{'roll': f'Y1-{i}', 'branch': 'CSE'} for i in range(1, 25)]
        students_y2 = [{'roll': f'Y2-{i}', 'branch': 'ECE'} for i in range(1, 25)]

        # Test basic mid exam seating distribution
        assignments = assign_seats_mid(students_y1, students_y2, self.halls, 'MID-TEST')
        self.assertEqual(len(assignments), 48)

        # Check alternate-seat checkerboard of years (alternating row starts)
        for a in assignments:
            row, col = a['row'], a['col']
            is_y1 = ((row + col) % 2 == 0)
            if is_y1:
                self.assertTrue(a['roll'].startswith('Y1-'))
            else:
                self.assertTrue(a['roll'].startswith('Y2-'))

if __name__ == '__main__':
    unittest.main()
