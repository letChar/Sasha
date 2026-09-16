"""Swap rows containing the global minimum and maximum matrix elements."""

from __future__ import annotations

from collections.abc import Sequence


Matrix = list[list[float]]


def _validated_copy(matrix: Sequence[Sequence[float]]) -> Matrix:
    """Return a rectangular mutable copy of *matrix* or raise ValueError."""
    if not matrix:
        raise ValueError("Матрица не должна быть пустой")

    column_count = len(matrix[0])
    if column_count == 0:
        raise ValueError("Строки матрицы не должны быть пустыми")

    result: Matrix = []
    for row in matrix:
        if len(row) != column_count:
            raise ValueError("Все строки матрицы должны иметь одинаковую длину")
        result.append([float(value) for value in row])
    return result


def swap_extreme_rows(matrix: Sequence[Sequence[float]]) -> tuple[Matrix, int, int]:
    """Swap rows with the global minimum and maximum.

    Return a new matrix together with zero-based indices of the minimum and
    maximum rows. The source matrix is not changed.
    """
    result = _validated_copy(matrix)
    min_row = max_row = 0
    min_value = max_value = result[0][0]

    for row_index, row in enumerate(result):
        for value in row:
            if value < min_value:
                min_value = value
                min_row = row_index
            if value > max_value:
                max_value = value
                max_row = row_index

    if min_row != max_row:
        result[min_row], result[max_row] = result[max_row], result[min_row]

    return result, min_row, max_row


def _read_positive_integer(prompt: str) -> int:
    while True:
        try:
            value = int(input(prompt))
            if value <= 0:
                raise ValueError
            return value
        except ValueError:
            print("Введите положительное целое число.")


def _read_matrix(row_count: int) -> Matrix:
    matrix: Matrix = []
    column_count: int | None = None

    print("Введите элементы каждой строки через пробел:")
    for row_number in range(1, row_count + 1):
        while True:
            try:
                row = [float(value) for value in input(f"Строка {row_number}: ").split()]
                if not row:
                    raise ValueError("строка пуста")
                if column_count is None:
                    column_count = len(row)
                elif len(row) != column_count:
                    raise ValueError("число элементов отличается от первой строки")
                matrix.append(row)
                break
            except ValueError as error:
                print(f"Некорректный ввод: {error}. Повторите строку.")
    return matrix


def main() -> None:
    """Run the interactive console interface."""
    row_count = _read_positive_integer("Количество строк: ")
    matrix = _read_matrix(row_count)
    result, min_row, max_row = swap_extreme_rows(matrix)

    print(
        f"Строка с минимумом: {min_row + 1}; "
        f"строка с максимумом: {max_row + 1}."
    )
    print("Готовая матрица:")
    for row in result:
        print(" ".join(f"{value:g}" for value in row))


if __name__ == "__main__":
    main()
