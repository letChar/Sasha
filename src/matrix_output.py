"""Модуль чтения JSON-ответа и отображения результата."""

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

    if not isinstance(response["matrix"], list) or not response["matrix"]:
        raise ProtocolError(
            "Поле 'matrix' в ответе должно быть непустым списком."
        )

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
