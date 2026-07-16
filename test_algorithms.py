import unittest
from algorithm import assign_seats, checkerboard_capacity

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

if __name__ == '__main__':
    unittest.main()
