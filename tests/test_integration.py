import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import src.main as app
from src.json_protocol import ProtocolError, read_json, write_json_atomic
from src.matrix_input import read_matrix_from_console, write_request
from src.matrix_output import display_response, read_response
from src.matrix_processor import process_request_file, swap_extreme_rows


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.request_path = self.root / "request.json"
        self.response_path = self.root / "response.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_complete_pipeline(self):
        write_request([[1, 2], [3, 4]], self.request_path)
        process_request_file(self.request_path, self.response_path)
        response = read_response(self.response_path)
        self.assertEqual(response["matrix"], [[3.0, 4.0], [1.0, 2.0]])
        self.assertEqual((response["min_row"], response["max_row"]), (0, 1))

    def test_display_pipeline(self):
        write_request([[1, 2], [3, 4]], self.request_path)
        process_request_file(self.request_path, self.response_path)
        lines = []
        display_response(self.response_path, output_fn=lines.append)
        self.assertEqual(lines[-2:], ["3  4", "1  2"])

    def test_unknown_request_version(self):
        write_json_atomic(self.request_path, {
            "schema_version": "2.0", "matrix": [[1]], "timeout_seconds": 5
        })
        with self.assertRaises(ProtocolError):
            process_request_file(self.request_path, self.response_path)

    def test_request_without_matrix(self):
        write_json_atomic(self.request_path, {
            "schema_version": "1.0", "timeout_seconds": 5
        })
        with self.assertRaises(ProtocolError):
            process_request_file(self.request_path, self.response_path)

    def test_missing_request_file(self):
        with self.assertRaises(FileNotFoundError):
            process_request_file(self.request_path, self.response_path)

    def test_zero_timeout(self):
        with self.assertRaises(TimeoutError):
            swap_extreme_rows([[1, 2], [3, 4]], timeout_seconds=0)

    def test_invalid_timeout(self):
        with self.assertRaises(ValueError):
            swap_extreme_rows([[1]], timeout_seconds=-1)

    def test_invalid_element_type(self):
        with self.assertRaises(ValueError):
            swap_extreme_rows([[True]])

    def test_non_finite_element(self):
        with self.assertRaises(ValueError):
            swap_extreme_rows([[float("inf")]])

    def test_decimal_comma_input(self):
        answers = iter(["1", "1,5 2"])
        matrix = read_matrix_from_console(
            input_fn=lambda _prompt: next(answers), output_fn=lambda _text: None
        )
        self.assertEqual(matrix, [[1.5, 2.0]])

    def test_non_finite_console_input(self):
        answers = iter(["1", "nan"])
        with self.assertRaises(ValueError):
            read_matrix_from_console(input_fn=lambda _prompt: next(answers))

    def test_main_success(self):
        with (
            patch.object(app, "read_matrix_from_console", return_value=[[1]]),
            patch.object(app, "write_request"),
            patch.object(app, "process_request_file"),
            patch.object(app, "display_response"),
        ):
            self.assertEqual(app.main(), 0)

    def test_main_timeout(self):
        with patch.object(
            app, "read_matrix_from_console", side_effect=TimeoutError("время")
        ):
            self.assertEqual(app.main(), 1)

    def test_main_value_error(self):
        with patch.object(
            app, "read_matrix_from_console", side_effect=ValueError("ввод")
        ):
            self.assertEqual(app.main(), 1)

    def test_invalid_json(self):
        self.request_path.write_text("{broken", encoding="utf-8")
        with self.assertRaises(ProtocolError):
            read_json(self.request_path)

    def test_response_root_is_object(self):
        self.response_path.write_text(json.dumps([]), encoding="utf-8")
        with self.assertRaises(ProtocolError):
            read_response(self.response_path)


if __name__ == "__main__":
    unittest.main()
