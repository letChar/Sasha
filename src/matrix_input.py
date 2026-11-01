"""Модуль ввода матрицы и формирования JSON-запроса."""

import math
from pathlib import Path
from typing import Callable

from src.json_protocol import SCHEMA_VERSION, write_json_atomic

DEFAULT_TIMEOUT_SECONDS = 5.0


def read_matrix_from_console(
    input_fn: Callable[[str], str] | None = None,
    output_fn: Callable[[str], None] | None = None,
) -> list[list[float]]:
    """Считывает непустую прямоугольную матрицу и проверяет ввод."""
    if input_fn is None:
        input_fn = input
    if output_fn is None:
        output_fn = print

    try:
        raw_rows = input_fn("Введите количество строк матрицы: ").strip()
        row_count = int(raw_rows)
    except (ValueError, TypeError) as exc:
        raise ValueError("Количество строк должно быть целым числом.") from exc

    if row_count <= 0:
        raise ValueError("Количество строк должно быть положительным.")

    matrix: list[list[float]] = []
    expected_columns: int | None = None

    for row_index in range(row_count):
        raw_line = input_fn(
            f"Введите элементы строки {row_index + 1} через пробел: "
        ).strip()

        tokens = raw_line.split()

        if not tokens:
            raise ValueError(f"Строка {row_index + 1} не должна быть пустой.")

        try:
            row = [float(token.replace(",", ".")) for token in tokens]
        except ValueError as exc:
            raise ValueError(
                f"В строке {row_index + 1} найдено значение "
                "нечислового формата."
            ) from exc

        if any(not math.isfinite(value) for value in row):
            raise ValueError("Элементы матрицы должны быть конечными числами.")

        if expected_columns is None:
            expected_columns = len(row)
        elif len(row) != expected_columns:
            raise ValueError(
                "Матрица должна быть прямоугольной: число столбцов во всех "
                "строках должно совпадать."
            )

        matrix.append(row)

    output_fn(
        f"Матрица принята: {len(matrix)} строк, "
        f"{len(matrix[0])} столбцов."
    )

    return matrix


def write_request(
    matrix: list[list[float]],
    path: str | Path,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, object]:
    """Сохраняет входные данные в файл JSON для модуля обработки."""
    request: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "matrix": matrix,
        "timeout_seconds": timeout_seconds,
    }

    write_json_atomic(path, request)
    return request
