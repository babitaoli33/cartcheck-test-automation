from decimal import Decimal

import pytest

from tests.conftest import load_json

pytestmark = pytest.mark.api

# Cases where truncating instead of rounding half-up gives a different cent
ROUNDING_SENSITIVE = {"ON-half-up", "AB-half-up", "ON-round-up"}


def tax_cases():
    for case in load_json("tax_cases.json"):
        marks = []
        if case["id"] in ROUNDING_SENSITIVE:
            marks.append(pytest.mark.xfail(reason="BUG-02: tax is truncated instead of rounded half-up"))
        items = {int(k): v for k, v in case["items"].items()}
        yield pytest.param(items, case["province"], case["expected_tax"], id=case["id"], marks=marks)


@pytest.mark.req("REQ-12")
@pytest.mark.parametrize("items, province, expected_tax", list(tax_cases()))
def test_tax_by_province(api, cart_with, items, province, expected_tax):
    assert api.cart(cart_with(items), province).json()["tax"] == expected_tax


@pytest.mark.req("REQ-12")
@pytest.mark.xfail(reason="BUG-01: tax is charged on the subtotal before the discount")
def test_tax_is_charged_after_discount(api, cart_with):
    cart_id = cart_with({4: 1})  # 39.00
    api.discount(cart_id, "SAVE10")  # -3.90 -> taxable 35.10
    cart = api.cart(cart_id, "ON").json()
    assert cart["tax"] == "4.56"
    assert cart["total"] == "39.66"


@pytest.mark.req("REQ-12")
def test_total_adds_up(api, cart_with):
    cart = api.cart(cart_with({4: 1, 3: 4}), "BC").json()
    expected = Decimal(cart["subtotal"]) - Decimal(cart["discount"]) + Decimal(cart["tax"])
    assert Decimal(cart["total"]) == expected


@pytest.mark.req("REQ-13")
@pytest.mark.parametrize("province", ["XX", "NY", "123"])
def test_unsupported_province_returns_400(api, cart_with, province):
    resp = api.cart(cart_with({3: 1}), province)
    assert resp.status_code == 400
    assert "not supported" in resp.json()["error"]


@pytest.mark.req("REQ-13")
def test_province_is_case_insensitive(api, cart_with):
    assert api.cart(cart_with({3: 1}), "on").json()["province"] == "ON"
