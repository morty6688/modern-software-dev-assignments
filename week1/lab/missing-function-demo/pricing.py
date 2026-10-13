"""订单金额计算，所有金额均使用整数分。"""


def calculate_subtotal(items: list[tuple[int, int]]) -> int:
    """每项为 (单价分, 数量)；单价和数量不能为负数。"""
    subtotal = 0
    for unit_price_cents, quantity in items:
        if unit_price_cents < 0 or quantity < 0:
            raise ValueError("unit price and quantity must be non-negative")
        subtotal += unit_price_cents * quantity
    return subtotal


# calculate_total(items, discount_cents=0) 已被故意删除。
# receipt.py 仍然导入并调用它，需要在实验会话中恢复。
