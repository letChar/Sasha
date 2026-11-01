"""Модуль обработки матрицы и формирования JSON-ответа."""

import math
import time
from pathlib import Path
from typing import Any

from src.json_protocol import (
    SCHEMA_VERSION,
    ProtocolError,
    read_json,
    write_json_atomic,
)


def _validated_copy(matrix: Any) -> list[list[float]]:
    """Проверяет матрицу и возвращает независимую копию типа float."""
    if not isinstance(matrix, (list, tuple)) or not matrix:
        raise ValueError("Матрица не должна быть пустой.")

    result: list[list[float]] = []
    expected_columns: int | None = None

    for row_index, row in enumerate(matrix, start=1):
        if not isinstance(row, (list, tuple)) or not row:
            raise ValueError(f"Строка {row_index} должна быть непустой.")

        if expected_columns is None:
            expected_columns = len(row)
        elif len(row) != expected_columns:
            raise ValueError("Все строки матрицы должны иметь одинаковую длину.")

        converted_row: list[float] = []

        for value in row:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError("Все элементы матрицы должны быть числами.")

            number = float(value)

            if not math.isfinite(number):
                raise ValueError(
                    "Элементы матрицы должны быть конечными числами."
                )

            converted_row.append(number)

        result.append(converted_row)

    return result


def swap_extreme_rows(
    matrix: Any,
    timeout_seconds: float | None = None,
) -> tuple[list[list[float]], int, int]:
    """Меняет местами строки с глобальными минимумом и максимумом."""
    result = _validated_copy(matrix)

    deadline: float | None = None

    if timeout_seconds is not None:
        if (
            isinstance(timeout_seconds, bool)
            or not isinstance(timeout_seconds, (int, float))
            or not math.isfinite(float(timeout_seconds))
            or timeout_seconds < 0
        ):
            raise ValueError(
                "Тайм-аут должен быть конечным неотрицательным числом."
            )

        deadline = time.monotonic() + float(timeout_seconds)

        if timeout_seconds == 0:
            raise TimeoutError("Превышено время обработки матрицы.")

    min_row = max_row = 0
    min_value = max_value = result[0][0]

    for row_index, row in enumerate(result):
        for value in row:
            if deadline is not None and time.monotonic() >= deadline:
                raise TimeoutError("Превышено время обработки матрицы.")

            if value < min_value:
                min_value, min_row = value, row_index

            if value > max_value:
                max_value, max_row = value, row_index

    if min_row != max_row:
        result[min_row], result[max_row] = result[max_row], result[min_row]

    return result, min_row, max_row


def process_request_file(
    request_path: str | Path,
    response_path: str | Path,
) -> dict[str, Any]:
    """Читает JSON-запрос, обрабатывает матрицу и записывает JSON-ответ."""
    request = read_json(request_path)

    if request.get("schema_version") != SCHEMA_VERSION:
        raise ProtocolError(
            "Несовместимая версия запроса: "
            f"ожидалась {SCHEMA_VERSION}, получена "
            f"{request.get('schema_version')!r}."
        )

    if "matrix" not in request:
        raise ProtocolError(
            "В запросе отсутствует обязательное поле 'matrix'."
        )

    timeout_seconds = request.get("timeout_seconds", 5.0)

    result, min_row, max_row = swap_extreme_rows(
        request["matrix"],
        timeout_seconds=timeout_seconds,
    )

    original = _validated_copy(request["matrix"])

    response: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": "ok",
        "matrix": result,
        "min_value": min(value for row in original for value in row),
        "max_value": max(value for row in original for value in row),
        "min_row": min_row,
        "max_row": max_row,
    }

    write_json_atomic(response_path, response)

    return response
