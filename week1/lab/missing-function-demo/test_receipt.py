"""现有回归测试；修复时保留这些用例，并补充边界用例。"""

import unittest

from receipt import build_receipt


class ReceiptTests(unittest.TestCase):
    def test_receipt_with_discount(self):
        self.assertEqual(
            build_receipt([(1999, 2), (500, 1)], discount_cents=300),
            {
                "item_count": 3,
                "subtotal_cents": 4498,
                "discount_cents": 300,
                "total_cents": 4198,
            },
        )

    def test_receipt_without_discount(self):
        self.assertEqual(build_receipt([(1250, 2)])["total_cents"], 2500)

    def test_empty_receipt(self):
        self.assertEqual(
            build_receipt([]),
            {
                "item_count": 0,
                "subtotal_cents": 0,
                "discount_cents": 0,
                "total_cents": 0,
            },
        )

    def test_negative_quantity_is_rejected(self):
        with self.assertRaises(ValueError):
            build_receipt([(100, -1)])


if __name__ == "__main__":
    unittest.main()
