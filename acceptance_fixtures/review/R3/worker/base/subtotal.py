def subtotal(items):
    total = 0
    for unit_price_cents, quantity in items:
        total += unit_price_cents * quantity
    return total
