import unittest
from pdf_generator import abbr_branch
from algorithm import interleave_by_branch

class TestCore(unittest.TestCase):
    def test_abbr_branch(self):
        self.assertEqual(abbr_branch('Computer Science and Engineering'), 'CSE')
        self.assertEqual(abbr_branch('Electronics and Communication Engineering'), 'ECE')
        self.assertEqual(abbr_branch('Information Technology'), 'IT')
        self.assertEqual(abbr_branch('Mechanical Engineering'), 'MECH')
        self.assertEqual(abbr_branch('Civil Engineering'), 'Civil')
        self.assertEqual(abbr_branch('Chemical Engineering'), 'CHE')
        self.assertEqual(abbr_branch('MBA (HA)'), 'MBA')
        self.assertEqual(abbr_branch('Unknown Branch'), 'Unknown Branch')

    def test_interleave_by_branch(self):
        students = [
            {'roll': '1', 'branch': 'CSE', 'section': 'A'},
            {'roll': '2', 'branch': 'CSE', 'section': 'A'},
            {'roll': '3', 'branch': 'ECE', 'section': 'A'},
            {'roll': '4', 'branch': 'ECE', 'section': 'A'},
        ]
        result = interleave_by_branch(students)
        # Should be interleaved: CSE, ECE, CSE, ECE or ECE, CSE, ECE, CSE
        self.assertEqual(len(result), 4)
        self.assertNotEqual(result[0]['branch'], result[1]['branch'])
        self.assertNotEqual(result[1]['branch'], result[2]['branch'])
        self.assertNotEqual(result[2]['branch'], result[3]['branch'])

if __name__ == '__main__':
    unittest.main()
