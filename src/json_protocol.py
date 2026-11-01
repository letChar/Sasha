"""Общие функции файлового JSON-протокола между модулями проекта."""

import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"


class ProtocolError(ValueError):
    """Ошибка структуры или версии сообщения интеграционного протокола."""


def read_json(path: str | Path) -> dict[str, Any]:
    """Читает JSON-объект; сообщает понятную ошибку при неверном формате."""
    source = Path(path)

    try:
        with source.open("r", encoding="utf-8") as file:
            payload = json.load(file)
    except json.JSONDecodeError as exc:
        raise ProtocolError(
            f"Файл {source} содержит некорректный JSON: {exc.msg}."
        ) from exc
    except UnicodeDecodeError as exc:
        raise ProtocolError(
            f"Файл {source} должен быть сохранён в кодировке UTF-8."
        ) from exc

    if not isinstance(payload, dict):
        raise ProtocolError("Корневой элемент JSON должен быть объектом.")

    return payload


def write_json_atomic(path: str | Path, payload: dict[str, Any]) -> None:
    """Записывает JSON временно и затем атомарно переименовывает файл."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".tmp")

    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as file:
            json.dump(
                payload,
                file,
                ensure_ascii=False,
                indent=2,
                allow_nan=False,
            )
            file.write("\n")

        temporary.replace(target)

    except (OSError, TypeError, ValueError):
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise
