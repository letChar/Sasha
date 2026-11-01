import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.matrix_processor import swap_extreme_rows
from src.json_protocol import read_json, write_json_atomic, SCHEMA_VERSION, ProtocolError


class SwapExtremeRowsTests(unittest.TestCase):
    def test_swaps_first_and_last_rows(self):
        matrix = [
            [1.0, 2.0, 3.0, 4.0],
            [5.0, 6.0, 7.0, 8.0],
            [9.0, 10.0, 11.0, 12.0],
        ]

        result, min_row, max_row = swap_extreme_rows(matrix)

        self.assertEqual(min_row, 0)
        self.assertEqual(max_row, 2)
        self.assertEqual(
            result,
            [
                [9.0, 10.0, 11.0, 12.0],
                [5.0, 6.0, 7.0, 8.0],
                [1.0, 2.0, 3.0, 4.0],
            ]
        )

    def test_keeps_matrix_when_extremes_are_in_one_row(self):
        matrix = [[-10.0, 20.0], [1.0, 2.0]]

        result, min_row, max_row = swap_extreme_rows(matrix)

        self.assertEqual((min_row, max_row), (0, 0))
        self.assertEqual(result, matrix)

    def test_handles_negative_and_fractional_values(self):
        matrix = [[2.5, -1.25], [0.0, 8.75], [4.5, 3.0]]

        result, min_row, max_row = swap_extreme_rows(matrix)

        self.assertEqual((min_row, max_row), (0, 1))
        self.assertIsNotNone(result)

    def test_rejects_empty_matrix(self):
        with self.assertRaisesRegex(ValueError, "не должна быть пустой"):
            swap_extreme_rows([])

    def test_rejects_rows_of_different_lengths(self):
        with self.assertRaisesRegex(ValueError, "одинаковую длину"):
            swap_extreme_rows([[1.0, 2.0], [3.0]])


class JsonProtocolTests(unittest.TestCase):
    def setUp(self):
        self.test_dir = TemporaryDirectory()
        self.file_path = Path(self.test_dir.name) / "test_proto.json"

    def tearDown(self):
        self.test_dir.cleanup()

    def test_write_and_read_success(self):
        data = {
            "schema_version": SCHEMA_VERSION,
            "matrix": [[1.0, 2.0]],
            "timeout_seconds": 5.0
        }
        write_json_atomic(self.file_path, data)

        loaded_data = read_json(self.file_path)
        self.assertEqual(loaded_data["schema_version"], SCHEMA_VERSION)
        self.assertEqual(loaded_data["matrix"], [[1.0, 2.0]])

    def test_read_missing_file_raises_error(self):
        with self.assertRaises(FileNotFoundError):
            read_json(Path(self.test_dir.name) / "non_existent.json")

    def test_read_invalid_json_raises_error(self):
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write("{invalid json...")
        with self.assertRaises(ProtocolError):
            read_json(self.file_path)

    def test_read_not_dict_raises_error(self):
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write("[]")
        with self.assertRaisesRegex(ProtocolError, "должен быть объектом"):
            read_json(self.file_path)


if __name__ == "__main__":
    unittest.main()
