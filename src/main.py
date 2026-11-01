
"""Точка входа и координатор интегрированной системы."""

from pathlib import Path

try:
    from src.matrix_input import read_matrix_from_console, write_request
    from src.matrix_output import display_response
    from src.matrix_processor import process_request_file
except ModuleNotFoundError as exc:
    print(
        "Ошибка интеграции: не найден модуль "
        f"'{exc.name}'. Проверьте структуру каталога src."
    )
    raise SystemExit(2) from exc

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"
REQUEST_PATH = DATA_DIR / "matrix_request.json"
RESPONSE_PATH = DATA_DIR / "matrix_response.json"


def main() -> int:
    """Последовательно запускает ввод, обработку и вывод результата."""
    try:
        matrix = read_matrix_from_console()
        write_request(matrix, REQUEST_PATH)
        process_request_file(REQUEST_PATH, RESPONSE_PATH)
        display_response(RESPONSE_PATH)
    except TimeoutError as exc:
        print(f"Ошибка интеграции: {exc}")
        return 1
    except (OSError, ValueError) as exc:
        print(f"Ошибка интеграции или входных данных: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
