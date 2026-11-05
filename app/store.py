"""ShopLite business logic: products, carts, discounts, tax and orders.

This is the application under test. It deliberately contains a handful of
defects so the CartCheck suite has real bugs to find (see docs/bug_reports.md).
State is kept in memory and can be reset between tests.
"""

from __future__ import annotations

import itertools
import re
from dataclasses import dataclass, field
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")
MAX_QTY = 10

TAX_RATES = {
    "ON": Decimal("0.13"),
    "QC": Decimal("0.14975"),
    "BC": Decimal("0.12"),
    "AB": Decimal("0.05"),
}

DISCOUNT_CODES = {
    "SAVE10": {"type": "percent", "value": Decimal("0.10"), "active": True},
    "WELCOME5": {"type": "fixed", "value": Decimal("5.00"), "min_subtotal": Decimal("25.00"), "active": True},
    "OLD20": {"type": "percent", "value": Decimal("0.20"), "active": False},
}

SEED_PRODUCTS = [
    (1, "Wireless Mouse", "24.99", 10, "electronics"),
    (2, "USB-C Cable", "10.50", 25, "electronics"),
    (3, "Notebook", "3.25", 100, "stationery"),
    (4, "Desk Lamp", "39.00", 5, "home"),
    (5, "Water Bottle", "15.00", 0, "home"),
    (6, "Headphones", "89.99", 3, "electronics"),
    (7, "Sticky Notes", "2.50", 50, "stationery"),
]

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$")


class StoreError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


@dataclass
class Product:
    id: int
    name: str
    price: Decimal
    stock: int
    category: str


@dataclass
class Cart:
    id: str
    items: dict[int, int] = field(default_factory=dict)  # product_id -> quantity
    codes: list[str] = field(default_factory=list)
    status: str = "open"


def money(value: Decimal) -> str:
    return f"{value.quantize(CENT, rounding=ROUND_HALF_UP):.2f}"


class Store:
    def __init__(self):
        self.reset()

    def reset(self) -> None:
        self.products = {
            pid: Product(pid, name, Decimal(price), stock, category)
            for pid, name, price, stock, category in SEED_PRODUCTS
        }
        self.carts: dict[str, Cart] = {}
        self.orders: dict[str, dict] = {}
        self._cart_ids = itertools.count(1)
        self._order_ids = itertools.count(1001)

    # --- products --------------------------------------------------------------
    def list_products(self) -> list[dict]:
        return [self._product_dict(p) for p in self.products.values()]

    def get_product(self, product_id: int) -> dict:
        product = self.products.get(product_id)
        if not product:
            raise StoreError(404, f"Product {product_id} not found")
        return self._product_dict(product)

    @staticmethod
    def _product_dict(p: Product) -> dict:
        return {"id": p.id, "name": p.name, "price": money(p.price), "stock": p.stock,
                "category": p.category, "in_stock": p.stock > 0}

    # --- carts -----------------------------------------------------------------
    def create_cart(self) -> str:
        cart_id = f"C{next(self._cart_ids):04d}"
        self.carts[cart_id] = Cart(cart_id)
        return cart_id

    def _open_cart(self, cart_id: str) -> Cart:
        cart = self.carts.get(cart_id)
        if not cart:
            raise StoreError(404, f"Cart {cart_id} not found")
        if cart.status != "open":
            raise StoreError(409, "Cart has already been checked out")
        return cart

    def add_item(self, cart_id: str, product_id, quantity) -> dict:
        cart = self._open_cart(cart_id)
        if not isinstance(product_id, int) or isinstance(product_id, bool):
            raise StoreError(400, "product_id must be an integer")
        if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 0 or quantity > MAX_QTY:
            raise StoreError(400, f"quantity must be a whole number from 1 to {MAX_QTY}")
        product = self.products.get(product_id)
        if not product:
            raise StoreError(404, f"Product {product_id} not found")
        if quantity > product.stock:
            raise StoreError(409, f"Only {product.stock} of {product.name} in stock")
        new_qty = cart.items.get(product_id, 0) + quantity
        if new_qty > MAX_QTY:
            raise StoreError(400, f"A cart can hold at most {MAX_QTY} of one product")
        cart.items[product_id] = new_qty
        return self.cart_summary(cart_id)

    def remove_item(self, cart_id: str, product_id: int) -> dict:
        cart = self._open_cart(cart_id)
        if product_id not in cart.items:
            raise StoreError(404, f"Product {product_id} is not in the cart")
        del cart.items[product_id]
        if not cart.items:
            cart.codes.clear()
        return self.cart_summary(cart_id)

    def apply_discount(self, cart_id: str, code: str) -> dict:
        cart = self._open_cart(cart_id)
        code = (code or "").strip().upper()
        rule = DISCOUNT_CODES.get(code)
        if not rule or not rule["active"]:
            raise StoreError(400, f"Discount code '{code}' is invalid or expired")
        if not cart.items:
            raise StoreError(400, "Add items before applying a discount")
        subtotal = self._subtotal(cart)
        if "min_subtotal" in rule and not subtotal > rule["min_subtotal"]:
            raise StoreError(400, f"{code} needs a subtotal of at least ${rule['min_subtotal']}")
        cart.codes.append(code)
        return self.cart_summary(cart_id)

    # --- pricing ---------------------------------------------------------------
    def _subtotal(self, cart: Cart) -> Decimal:
        return sum((self.products[pid].price * qty for pid, qty in cart.items.items()), Decimal("0"))

    def _discount(self, cart: Cart, subtotal: Decimal) -> Decimal:
        total = Decimal("0")
        for code in cart.codes:
            rule = DISCOUNT_CODES[code]
            if rule["type"] == "percent":
                total += (subtotal * rule["value"]).quantize(CENT, rounding=ROUND_HALF_UP)
            else:
                total += rule["value"]
        return min(total, subtotal)

    @staticmethod
    def _tax(amount: Decimal, province: str) -> Decimal:
        return (amount * TAX_RATES[province]).quantize(CENT, rounding=ROUND_DOWN)

    def cart_summary(self, cart_id: str, province: str = "ON") -> dict:
        cart = self.carts.get(cart_id)
        if not cart:
            raise StoreError(404, f"Cart {cart_id} not found")
        province = (province or "ON").upper()
        if province not in TAX_RATES:
            raise StoreError(400, f"Province '{province}' is not supported")
        subtotal = self._subtotal(cart)
        discount = self._discount(cart, subtotal)
        tax = self._tax(subtotal, province)
        items = [
            {"product_id": pid, "name": self.products[pid].name, "unit_price": money(self.products[pid].price),
             "quantity": qty, "line_total": money(self.products[pid].price * qty)}
            for pid, qty in cart.items.items()
        ]
        return {
            "cart_id": cart.id,
            "status": cart.status,
            "items": items,
            "item_count": sum(cart.items.values()),
            "subtotal": money(subtotal),
            "discount_code": cart.codes[-1] if cart.codes else None,
            "discount": money(discount),
            "province": province,
            "tax": money(tax),
            "total": money(subtotal - discount + tax),
        }

    # --- checkout --------------------------------------------------------------
    def checkout(self, cart_id: str, email: str, province: str) -> dict:
        cart = self._open_cart(cart_id)
        if not isinstance(email, str) or not EMAIL_RE.match(email.strip()):
            raise StoreError(400, "A valid email address is required")
        if not cart.items:
            raise StoreError(400, "Cart is empty")
        summary = self.cart_summary(cart_id, province)
        for pid, qty in cart.items.items():
            self.products[pid].stock -= qty
        cart.status = "ordered"
        order_id = f"ORD-{next(self._order_ids)}"
        order = {"order_id": order_id, "email": email.strip(), **{k: summary[k] for k in (
            "items", "subtotal", "discount", "province", "tax", "total")}}
        self.orders[order_id] = order
        return order

    def get_order(self, order_id: str) -> dict:
        if order_id not in self.orders:
            raise StoreError(404, f"Order {order_id} not found")
        return self.orders[order_id]
