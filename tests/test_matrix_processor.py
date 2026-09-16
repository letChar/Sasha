import unittest

from src.matrix_processor import swap_extreme_rows


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
        self.assertEqual(result[0], matrix[2])
        self.assertEqual(result[2], matrix[0])
        self.assertEqual(matrix[0][0], 1.0)

    def test_keeps_matrix_when_extremes_are_in_one_row(self):
        matrix = [[-10.0, 20.0], [1.0, 2.0]]

        result, min_row, max_row = swap_extreme_rows(matrix)

        self.assertEqual((min_row, max_row), (0, 0))
        self.assertEqual(result, matrix)

    def test_handles_negative_and_fractional_values(self):
        matrix = [[2.5, -1.25], [0.0, 8.75], [4.5, 3.0]]

        result, min_row, max_row = swap_extreme_rows(matrix)

        self.assertEqual((min_row, max_row), (0, 1))
        self.assertEqual(result, [matrix[1], matrix[0], matrix[2]])

    def test_rejects_empty_matrix(self):
        with self.assertRaisesRegex(ValueError, "не должна быть пустой"):
            swap_extreme_rows([])

    def test_rejects_rows_of_different_lengths(self):
        with self.assertRaisesRegex(ValueError, "одинаковую длину"):
            swap_extreme_rows([[1.0, 2.0], [3.0]])


if __name__ == "__main__":
    unittest.main()
