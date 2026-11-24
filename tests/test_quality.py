import json

import pytest

import src.main as app
from src.json_protocol import ProtocolError, read_json, write_json_atomic
from src.matrix_input import read_matrix_from_console, write_request
from src.matrix_output import display_response, read_response
from src.matrix_processor import process_request_file, swap_extreme_rows


@pytest.mark.parametrize(
    ("matrix", "expected_rows", "expected_extremes"),
    [
        ([[1]], [[1.0]], (0, 0)),
        ([[-5, 2], [3, 10]], [[3.0, 10.0], [-5.0, 2.0]], (0, 1)),
        ([[7, -9], [0, 1], [8, 2]], [[8.0, 2.0], [0.0, 1.0], [7.0, -9.0]], (0, 2)),
        ([[-4, 9], [3, 1]], [[-4.0, 9.0], [3.0, 1.0]], (0, 0)),
    ],
)
def test_cause_effect_valid_matrices(matrix, expected_rows, expected_extremes):
    result, min_row, max_row = swap_extreme_rows(matrix)
    assert result == expected_rows
    assert (min_row, max_row) == expected_extremes


@pytest.mark.parametrize(
    "matrix",
    [
        None,
        [],
        [[]],
        [[1, 2], [3]],
        [[True]],
        [["1"]],
        [[float("nan")]],
        [[float("inf")]],
    ],
)
def test_cause_effect_invalid_matrices(matrix):
    with pytest.raises(ValueError):
        swap_extreme_rows(matrix)


@pytest.mark.parametrize(
    ("timeout", "error"),
    [
        (0, TimeoutError),
        (-1, ValueError),
        (True, ValueError),
        (float("inf"), ValueError),
        ("1", ValueError),
    ],
)
def test_cause_effect_timeout_rules(timeout, error):
    with pytest.raises(error):
        swap_extreme_rows([[1]], timeout_seconds=timeout)


@pytest.mark.parametrize(
    "answers",
    [
        ["0"],
        ["abc"],
        ["1", ""],
        ["1", "one"],
        ["2", "1 2", "3"],
        ["1", "nan"],
    ],
)
def test_cause_effect_console_input_errors(answers):
    values = iter(answers)
    with pytest.raises(ValueError):
        read_matrix_from_console(input_fn=lambda _prompt: next(values))


def test_json_protocol_unicode_round_trip(tmp_path):
    path = tmp_path / "nested" / "message.json"
    payload = {"status": "готово", "matrix": [[1, 2]]}
    write_json_atomic(path, payload)
    assert read_json(path) == payload
    assert json.loads(path.read_text(encoding="utf-8")) == payload


def test_complete_file_pipeline(tmp_path):
    request_path = tmp_path / "request.json"
    response_path = tmp_path / "response.json"
    write_request([[1, 2], [3, 4]], request_path)
    response = process_request_file(request_path, response_path)
    assert read_response(response_path) == response
    assert response["matrix"] == [[3.0, 4.0], [1.0, 2.0]]


def test_display_response_lines(tmp_path):
    request_path = tmp_path / "request.json"
    response_path = tmp_path / "response.json"
    write_request([[-2, 1], [5, 3]], request_path)
    process_request_file(request_path, response_path)
    lines = []
    display_response(response_path, output_fn=lines.append)
    assert lines[-2:] == ["5  3", "-2  1"]


def test_main_reports_operating_system_error(monkeypatch, capsys):
    monkeypatch.setattr(app, "read_matrix_from_console", lambda: [[1]])
    monkeypatch.setattr(app, "write_request", lambda *_args: None)
    monkeypatch.setattr(
        app,
        "process_request_file",
        lambda *_args: (_ for _ in ()).throw(OSError("нет доступа")),
    )
    assert app.main() == 1
    assert "нет доступа" in capsys.readouterr().out


class TestRegression:
    def test_malformed_response_matrix_is_rejected(self, tmp_path):
        response_path = tmp_path / "response.json"
        write_json_atomic(
            response_path,
            {
                "schema_version": "1.0",
                "status": "ok",
                "matrix": [[1], ["broken"]],
                "min_value": 1,
                "max_value": 2,
                "min_row": 0,
                "max_row": 1,
            },
        )
        with pytest.raises(ProtocolError):
            read_response(response_path)

    def test_failed_request_removes_stale_response(self, tmp_path):
        request_path = tmp_path / "request.json"
        response_path = tmp_path / "response.json"
        response_path.write_text('{"status": "ok"}', encoding="utf-8")
        request_path.write_text("{broken", encoding="utf-8")

        with pytest.raises(ProtocolError):
            process_request_file(request_path, response_path)

        assert not response_path.exists()
