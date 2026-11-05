"""Browser tests for the main shopping journey, written with the Page Object Model."""

import re

import pytest
from playwright.sync_api import expect

from tests.ui.pages.cart_page import CartPage
from tests.ui.pages.products_page import ProductsPage

pytestmark = pytest.mark.ui


@pytest.fixture
def products(page):
    return ProductsPage(page).open()


@pytest.mark.smoke
@pytest.mark.req("REQ-19")
def test_products_page_lists_all_products(products):
    assert len(products.product_names()) == 7
    assert products.price(4) == "$39.00"


@pytest.mark.req("REQ-19")
def test_out_of_stock_product_cannot_be_added(products):
    assert products.is_out_of_stock(5)
    expect(products.add_button(5)).to_be_disabled()


@pytest.mark.req("REQ-19")
def test_adding_a_product_updates_the_badge(products):
    products.add_to_cart(3)
    assert products.cart_badge_count == 1


@pytest.mark.req("REQ-19")
@pytest.mark.xfail(reason="BUG-07: the cart badge counts products, not total quantity")
def test_badge_shows_total_quantity(products):
    products.add_to_cart(3, quantity=3)
    assert products.cart_badge_count == 3


@pytest.mark.req("REQ-08", "REQ-19")
def test_cart_shows_line_totals_and_subtotal(products):
    products.add_to_cart(1, quantity=2).add_to_cart(3)
    cart = products.go_to_cart()
    assert cart.item_names() == ["Wireless Mouse", "Notebook"]
    assert cart.line_total(1) == "$49.98"
    assert cart.amount("subtotal") == "53.23"


@pytest.mark.req("REQ-07")
def test_removing_the_last_item_empties_the_cart(products):
    cart = products.add_to_cart(3).go_to_cart()
    cart.remove(3)
    assert cart.is_empty
    expect(cart.by_test_id("checkout-link")).to_have_count(0)


@pytest.mark.req("REQ-09", "REQ-20")
def test_valid_code_shows_discount(products):
    cart = products.add_to_cart(4).go_to_cart().apply_code("SAVE10")
    assert cart.amount("discount") == "3.90"
    expect(cart.error).to_have_count(0)


@pytest.mark.req("REQ-11", "REQ-20")
def test_invalid_code_shows_error(products):
    cart = products.add_to_cart(4).go_to_cart().apply_code("OLD20")
    expect(cart.error).to_contain_text("invalid or expired")
    expect(cart.by_test_id("discount")).to_have_count(0)


@pytest.mark.req("REQ-12")
def test_changing_province_updates_tax(products):
    cart = products.add_to_cart(4).go_to_cart()
    assert cart.amount("tax") == "5.07"  # ON 13% of 39.00
    cart.choose_province("BC")
    assert cart.amount("tax") == "4.68"  # BC 12%


@pytest.mark.smoke
@pytest.mark.req("REQ-17", "REQ-20")
def test_checkout_shows_confirmation(products):
    cart = products.add_to_cart(2).add_to_cart(3, quantity=2).go_to_cart()
    cart_total = cart.amount("total")
    checkout = cart.proceed_to_checkout()
    assert checkout.total == cart_total
    order = checkout.place_order("shopper@example.com").confirmation()
    assert re.fullmatch(r"ORD-\d+", order.order_id)
    assert order.total == cart_total


@pytest.mark.req("REQ-14")
def test_invalid_email_keeps_shopper_on_checkout(products):
    checkout = products.add_to_cart(3).go_to_cart().proceed_to_checkout()
    checkout.place_order("not-an-email")
    expect(checkout.error).to_contain_text("valid email")
    expect(checkout.page).to_have_url(re.compile(r"/checkout"))


@pytest.mark.req("REQ-15")
def test_empty_cart_has_no_checkout_link(page):
    cart = CartPage(page).open()
    assert cart.is_empty
    expect(cart.by_test_id("checkout-link")).to_have_count(0)


@pytest.mark.req("REQ-20")
def test_badge_resets_after_order(products):
    products.add_to_cart(3).go_to_cart().proceed_to_checkout().place_order("shopper@example.com").confirmation()
    assert ProductsPage(products.page).open().cart_badge_count == 0
