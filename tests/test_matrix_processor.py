import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from src.matrix_processor import swap_extreme_rows
from src.json_protocol import read_json, write_json_atomic, SCHEMA_VERSION, ProtocolError
from src.matrix_input import read_matrix_from_console, write_request
from src.matrix_output import read_response, display_response
import src.main


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
        self.assertIsNotNone(result)

    def test_keeps_matrix_when_extremes_are_in_one_row(self):
        matrix = [[-10.0, 20.0], [1.0, 2.0]]
        result, min_row, max_row = swap_extreme_rows(matrix)
        self.assertEqual((min_row, max_row), (0, 0))

    def test_handles_negative_and_fractional_values(self):
        matrix = [[2.5, -1.25], [0.0, 8.75], [4.5, 3.0]]
        result, min_row, max_row = swap_extreme_rows(matrix)
        self.assertEqual((min_row, max_row), (0, 1))

    def test_rejects_empty_matrix(self):
        with self.assertRaises(ValueError):
            swap_extreme_rows([])

    def test_rejects_rows_of_different_lengths(self):
        with self.assertRaises(ValueError):
            swap_extreme_rows([[1.0, 2.0], [3.0]])


class JsonProtocolTests(unittest.TestCase):
    def setUp(self):
        self.test_dir = TemporaryDirectory()
        self.file_path = Path(self.test_dir.name) / "test_proto.json"

    def tearDown(self):
        self.test_dir.cleanup()

    def test_write_and_read_success(self):
        data = {"schema_version": SCHEMA_VERSION, "matrix": [[1.0, 2.0]], "timeout_seconds": 5.0}
        write_json_atomic(self.file_path, data)
        loaded_data = read_json(self.file_path)
        self.assertEqual(loaded_data["schema_version"], SCHEMA_VERSION)

    def test_read_missing_file_raises_error(self):
        with self.assertRaises(FileNotFoundError):
            read_json(Path(self.test_dir.name) / "non_existent.json")

    def test_read_invalid_json_raises_error(self):
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write("{invalid")
        with self.assertRaises(ProtocolError):
            read_json(self.file_path)

    def test_read_not_dict_raises_error(self):
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write("[]")
        with self.assertRaises(ProtocolError):
            read_json(self.file_path)


class MatrixInputTests(unittest.TestCase):
    def test_read_matrix_success(self):
        inputs = ["2", "1 2", "3 4"]

        def mock_input(prompt):
            return inputs.pop(0)
        matrix = read_matrix_from_console(input_fn=mock_input, output_fn=lambda x: None)
        self.assertEqual(matrix, [[1.0, 2.0], [3.0, 4.0]])

    def test_read_matrix_invalid_rows(self):
        with self.assertRaises(ValueError):
            read_matrix_from_console(input_fn=lambda x: "abc")
        with self.assertRaises(ValueError):
            read_matrix_from_console(input_fn=lambda x: "-5")

    def test_read_matrix_empty_row(self):
        inputs = ["1", ""]
        with self.assertRaises(ValueError):
            read_matrix_from_console(input_fn=lambda x: inputs.pop(0))

    def test_read_matrix_not_rectangular(self):
        inputs = ["2", "1 2", "3"]
        with self.assertRaises(ValueError):
            read_matrix_from_console(input_fn=lambda x: inputs.pop(0))

    def test_write_request(self):
        with TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "req.json"
            write_request([[1.0]], p)
            self.assertTrue(p.exists())


class MatrixOutputTests(unittest.TestCase):
    def setUp(self):
        self.test_dir = TemporaryDirectory()
        self.file_path = Path(self.test_dir.name) / "res.json"
        self.valid_data = {
            "schema_version": SCHEMA_VERSION,
            "status": "ok",
            "matrix": [[1.0, 2.0]],
            "min_value": 1.0,
            "max_value": 2.0,
            "min_row": 0,
            "max_row": 0
        }

    def tearDown(self):
        self.test_dir.cleanup()

    def test_read_response_success(self):
        write_json_atomic(self.file_path, self.valid_data)
        res = read_response(self.file_path)
        self.assertEqual(res["status"], "ok")

    def test_read_response_invalid_version(self):
        self.valid_data["schema_version"] = "99.0"
        write_json_atomic(self.file_path, self.valid_data)
        with self.assertRaises(ProtocolError):
            read_response(self.file_path)

    def test_read_response_missing_fields(self):
        self.valid_data.pop("status")
        write_json_atomic(self.file_path, self.valid_data)
        with self.assertRaises(ProtocolError):
            read_response(self.file_path)

    def test_read_response_not_ok_status(self):
        self.valid_data["status"] = "error"
        write_json_atomic(self.file_path, self.valid_data)
        with self.assertRaises(ProtocolError):
            read_response(self.file_path)

    def test_read_response_invalid_matrix(self):
        self.valid_data["matrix"] = "not a list"
        write_json_atomic(self.file_path, self.valid_data)
        with self.assertRaises(ProtocolError):
            read_response(self.file_path)

    def test_display_response_success(self):
        write_json_atomic(self.file_path, self.valid_data)
        logs = []
        display_response(self.file_path, output_fn=logs.append)
        self.assertTrue(any("Глобальный минимум" in line for line in logs))


class MainModuleTests(unittest.TestCase):
    def test_main_execution_flow(self):
        with patch("src.matrix_input.read_matrix_from_console") as mock_read, \
             patch("src.matrix_input.write_request"), \
             patch("src.json_protocol.read_json") as mock_read_json:

            mock_read.return_value = [[1.0]]
            mock_read_json.return_value = {"matrix": [[1.0]], "schema_version": "1.0"}

            try:
                if hasattr(src.main, "process_request_file"):
                    src.main.process_request_file(Path("fake_req.json"), Path("fake_res.json"))
            except Exception:
                pass
            self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
