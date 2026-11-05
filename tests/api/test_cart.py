import csv
import json

import pytest

from tests.conftest import DATA_DIR

pytestmark = pytest.mark.api


def quantity_cases():
    with open(DATA_DIR / "quantity_boundaries.csv", newline="") as f:
        for row in csv.DictReader(f):
            quantity = json.loads(row["quantity"])
            marks = []
            if quantity == 0:
                marks.append(pytest.mark.xfail(reason="BUG-04: quantity 0 is accepted"))
            yield pytest.param(quantity, int(row["expected_status"]), id=row["technique"], marks=marks)


@pytest.mark.smoke
@pytest.mark.req("REQ-03")
def test_new_cart_is_empty(api):
    resp = api.post("/carts")
    assert resp.status_code == 201
    cart = resp.json()
    assert cart["items"] == [] and cart["subtotal"] == "0.00" and cart["total"] == "0.00"


@pytest.mark.req("REQ-03")
def test_cart_ids_are_unique(api):
    ids = {api.new_cart() for _ in range(5)}
    assert len(ids) == 5


@pytest.mark.req("REQ-03")
def test_unknown_cart_returns_404(api):
    assert api.cart("C9999").status_code == 404


@pytest.mark.req("REQ-04")
@pytest.mark.parametrize("quantity, expected_status", list(quantity_cases()))
def test_quantity_boundaries(api, quantity, expected_status):
    cart_id = api.new_cart()
    assert api.add(cart_id, 3, quantity).status_code == expected_status


@pytest.mark.req("REQ-04")
def test_missing_body_returns_400(api):
    cart_id = api.new_cart()
    assert api.post(f"/carts/{cart_id}/items").status_code == 400


@pytest.mark.req("REQ-04")
def test_string_product_id_returns_400(api):
    cart_id = api.new_cart()
    assert api.add(cart_id, "3", 1).status_code == 400


@pytest.mark.req("REQ-02")
def test_adding_unknown_product_returns_404(api):
    cart_id = api.new_cart()
    assert api.add(cart_id, 999, 1).status_code == 404


@pytest.mark.req("REQ-05")
def test_out_of_stock_product_cannot_be_added(api):
    cart_id = api.new_cart()
    resp = api.add(cart_id, 5, 1)
    assert resp.status_code == 409
    assert "stock" in resp.json()["error"]


@pytest.mark.req("REQ-05")
def test_single_add_above_stock_returns_409(api):
    cart_id = api.new_cart()
    assert api.add(cart_id, 4, 6).status_code == 409  # Desk Lamp has 5 in stock


@pytest.mark.req("REQ-05")
def test_adding_exactly_the_stock_is_allowed(api):
    cart_id = api.new_cart()
    assert api.add(cart_id, 4, 5).status_code == 201


@pytest.mark.req("REQ-05")
@pytest.mark.xfail(reason="BUG-03: stock is checked per request, not against the cart total")
def test_repeated_adds_cannot_exceed_stock(api):
    cart_id = api.new_cart()
    assert api.add(cart_id, 4, 3).status_code == 201
    assert api.add(cart_id, 4, 3).status_code == 409  # 6 lamps would exceed stock of 5


@pytest.mark.req("REQ-06")
def test_adding_same_product_merges_quantity(api):
    cart_id = api.new_cart()
    api.add(cart_id, 3, 2)
    cart = api.add(cart_id, 3, 3).json()
    assert len(cart["items"]) == 1
    assert cart["items"][0]["quantity"] == 5


@pytest.mark.req("REQ-04", "REQ-06")
def test_merged_quantity_cannot_exceed_ten(api):
    cart_id = api.new_cart()
    api.add(cart_id, 3, 8)
    assert api.add(cart_id, 3, 3).status_code == 400


@pytest.mark.req("REQ-07")
def test_remove_item(api, cart_with):
    cart_id = cart_with({1: 1, 3: 2})
    resp = api.delete(f"/carts/{cart_id}/items/1")
    assert resp.status_code == 200
    assert [i["product_id"] for i in resp.json()["items"]] == [3]


@pytest.mark.req("REQ-07")
def test_remove_item_not_in_cart_returns_404(api, cart_with):
    cart_id = cart_with({3: 1})
    assert api.delete(f"/carts/{cart_id}/items/1").status_code == 404


@pytest.mark.req("REQ-08")
@pytest.mark.parametrize("items, expected", [
    ({3: 1}, "3.25"),
    ({1: 2, 3: 3}, "59.73"),
    ({7: 10}, "25.00"),
    ({6: 3, 2: 4}, "311.97"),
])
def test_subtotal_is_sum_of_line_totals(api, cart_with, items, expected):
    cart = api.cart(cart_with(items)).json()
    assert cart["subtotal"] == expected
    assert cart["item_count"] == sum(items.values())


@pytest.mark.req("REQ-08")
def test_line_total_is_price_times_quantity(api, cart_with):
    item = api.cart(cart_with({1: 3})).json()["items"][0]
    assert item["unit_price"] == "24.99" and item["line_total"] == "74.97"
