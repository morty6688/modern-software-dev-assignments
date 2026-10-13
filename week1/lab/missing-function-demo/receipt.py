"""生成订单收据。"""

from pricing import calculate_subtotal, calculate_total


def build_receipt(
    items: list[tuple[int, int]], discount_cents: int = 0
) -> dict[str, int]:
    """返回商品总件数、折前金额、优惠金额和实付金额。"""
    total_cents = calculate_total(items, discount_cents)
    return {
        "item_count": sum(quantity for _, quantity in items),
        "subtotal_cents": calculate_subtotal(items),
        "discount_cents": discount_cents,
        "total_cents": total_cents,
    }
