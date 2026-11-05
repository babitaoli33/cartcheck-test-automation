"""Contract tests: responses must match the JSON Schemas in /schemas."""

import pytest

from tests.conftest import assert_matches_schema

pytestmark = [pytest.mark.api, pytest.mark.req("REQ-18")]


def test_empty_cart_contract(api):
    assert_matches_schema(api.post("/carts").json(), "cart")


def test_filled_cart_contract(api, cart_with):
    cart_id = cart_with({1: 2, 3: 1})
    api.discount(cart_id, "SAVE10")
    assert_matches_schema(api.cart(cart_id, "QC").json(), "cart")


def test_order_contract(api, cart_with):
    assert_matches_schema(api.checkout(cart_with({2: 1})).json(), "order")


@pytest.mark.parametrize("call", [
    lambda api: api.get("/products/999"),
    lambda api: api.cart("C9999"),
    lambda api: api.add(api.new_cart(), 3, 99),
    lambda api: api.discount(api.new_cart(), "NOPE"),
    lambda api: api.checkout(api.new_cart()),
], ids=["unknown-product", "unknown-cart", "bad-quantity", "bad-code", "empty-checkout"])
def test_error_contract(api, call):
    resp = call(api)
    assert 400 <= resp.status_code < 500
    assert_matches_schema(resp.json(), "error")


def test_content_type_is_json(api):
    assert api.get("/products").headers["Content-Type"].startswith("application/json")
