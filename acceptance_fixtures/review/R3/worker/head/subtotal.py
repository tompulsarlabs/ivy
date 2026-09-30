def subtotal(items):
    return sum(price_cents * quantity for price_cents, quantity in items)
