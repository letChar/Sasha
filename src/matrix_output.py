"""Модуль чтения JSON-ответа и отображения результата."""

import math
from pathlib import Path
from typing import Any, Callable

from src.json_protocol import SCHEMA_VERSION, ProtocolError, read_json


def read_response(path: str | Path) -> dict[str, Any]:
    """Читает ответ и проверяет версию и обязательные поля протокола."""
    response = read_json(path)

    if response.get("schema_version") != SCHEMA_VERSION:
        raise ProtocolError(
            "Несовместимая версия ответа: "
            f"ожидалась {SCHEMA_VERSION}, получена "
            f"{response.get('schema_version')!r}."
        )

    required = {
        "status", "matrix", "min_value", "max_value", "min_row", "max_row"
    }

    missing = required.difference(response)

    if missing:
        raise ProtocolError(
            "В ответе отсутствуют обязательные поля: "
            + ", ".join(sorted(missing))
        )

    if response["status"] != "ok":
        raise ProtocolError(
            "Модуль обработки вернул статус, отличный от 'ok'."
        )

    matrix = response["matrix"]

    if not isinstance(matrix, list) or not matrix:
        raise ProtocolError(
            "Поле 'matrix' в ответе должно быть непустым списком."
        )

    column_count: int | None = None

    for row in matrix:
        if not isinstance(row, list) or not row:
            raise ProtocolError("Строки матрицы в ответе должны быть непустыми.")

        if column_count is None:
            column_count = len(row)
        elif len(row) != column_count:
            raise ProtocolError("Матрица в ответе должна быть прямоугольной.")

        for value in row:
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(float(value))
            ):
                raise ProtocolError("Матрица в ответе должна содержать конечные числа.")

    for field in ("min_value", "max_value"):
        value = response[field]
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
        ):
            raise ProtocolError(f"Поле '{field}' должно содержать конечное число.")

    for field in ("min_row", "max_row"):
        value = response[field]
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value < len(matrix):
            raise ProtocolError(f"Поле '{field}' содержит неверный номер строки.")

    return response


def display_response(
    response_path: str | Path,
    output_fn: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """Выводит экстремумы и результирующую матрицу."""
    if output_fn is None:
        output_fn = print

    response = read_response(response_path)

    output_fn(
        f"Глобальный минимум: {response['min_value']:g}; "
        f"исходная строка: {response['min_row'] + 1}."
    )

    output_fn(
        f"Глобальный максимум: {response['max_value']:g}; "
        f"исходная строка: {response['max_row'] + 1}."
    )

    output_fn("Готовая матрица:")

    for row in response["matrix"]:
        output_fn("  ".join(f"{float(value):g}" for value in row))

    return response
