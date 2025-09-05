import os
import sys
import shutil
import tempfile
import unittest

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from mirror_match import file_crc32, files_are_identical, find_duplicate_files, format_time

class TestDuplicateFinder(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.file1 = os.path.join(self.test_dir, 'file1.txt')
        self.file2 = os.path.join(self.test_dir, 'file2.txt')
        self.file3 = os.path.join(self.test_dir, 'file3.txt')
        with open(self.file1, 'w') as f:
            f.write('duplicate content')
        shutil.copy(self.file1, self.file2)
        with open(self.file3, 'w') as f:
            f.write('unique content')

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_file_crc32(self):
        c1 = file_crc32(self.file1)
        c2 = file_crc32(self.file2)
        c3 = file_crc32(self.file3)
        self.assertEqual(c1, c2)
        self.assertNotEqual(c1, c3)

    def test_files_are_identical(self):
        self.assertTrue(files_are_identical(self.file1, self.file2))
        self.assertFalse(files_are_identical(self.file1, self.file3))

    def test_find_duplicate_files(self):
        results = find_duplicate_files(self.test_dir)
        flat = [f for g in results for f in g['files']]
        self.assertIn(self.file1, flat)
        self.assertIn(self.file2, flat)
        self.assertNotIn(self.file3, flat)

    def test_find_duplicate_with_extension_filter(self):
        results = find_duplicate_files(self.test_dir, extensions=['.txt'])
        self.assertTrue(any(len(g['files']) > 1 for g in results))
        results_filtered = find_duplicate_files(self.test_dir, extensions=['.png'])
        self.assertEqual(results_filtered, [])

    def test_format_time(self):
        self.assertEqual(format_time(59), '59s')
        self.assertEqual(format_time(61), '1m 1s')
        self.assertEqual(format_time(3661), '1h 1m 1s')
        self.assertTrue('d' in format_time(90000))

if __name__ == '__main__':
    unittest.main()
