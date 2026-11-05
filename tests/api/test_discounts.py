import pytest

pytestmark = pytest.mark.api


@pytest.mark.req("REQ-09")
def test_save10_takes_ten_percent_off(api, cart_with):
    cart_id = cart_with({4: 1})  # 39.00
    cart = api.discount(cart_id, "SAVE10").json()
    assert cart["discount_code"] == "SAVE10"
    assert cart["discount"] == "3.90"


@pytest.mark.req("REQ-09")
def test_codes_are_case_insensitive(api, cart_with):
    assert api.discount(cart_with({4: 1}), "save10").status_code == 200


@pytest.mark.req("REQ-10")
def test_welcome5_above_minimum(api, cart_with):
    cart_id = cart_with({1: 1, 3: 1})  # 28.24
    resp = api.discount(cart_id, "WELCOME5")
    assert resp.status_code == 200
    assert resp.json()["discount"] == "5.00"


@pytest.mark.req("REQ-10")
@pytest.mark.xfail(reason="BUG-05: WELCOME5 rejects a subtotal of exactly $25.00")
def test_welcome5_at_exact_minimum(api, cart_with):
    cart_id = cart_with({7: 10})  # exactly 25.00
    resp = api.discount(cart_id, "WELCOME5")
    assert resp.status_code == 200


@pytest.mark.req("REQ-10")
def test_welcome5_below_minimum_is_rejected(api, cart_with):
    cart_id = cart_with({1: 1})  # 24.99
    resp = api.discount(cart_id, "WELCOME5")
    assert resp.status_code == 400
    assert "25" in resp.json()["error"]


@pytest.mark.req("REQ-11")
@pytest.mark.parametrize("code", ["OLD20", "FREESTUFF", "", "SAVE 10"])
def test_invalid_or_expired_codes_are_rejected(api, cart_with, code):
    assert api.discount(cart_with({4: 1}), code).status_code == 400


@pytest.mark.req("REQ-11")
def test_discount_needs_items_in_cart(api):
    assert api.discount(api.new_cart(), "SAVE10").status_code == 400


@pytest.mark.req("REQ-11")
@pytest.mark.xfail(reason="BUG-06: a second code is accepted and discounts stack")
def test_only_one_code_per_cart(api, cart_with):
    cart_id = cart_with({4: 1})
    assert api.discount(cart_id, "SAVE10").status_code == 200
    assert api.discount(cart_id, "SAVE10").status_code == 409


@pytest.mark.req("REQ-11")
def test_discount_is_cleared_when_cart_is_emptied(api, cart_with):
    cart_id = cart_with({4: 1})
    api.discount(cart_id, "SAVE10")
    cart = api.delete(f"/carts/{cart_id}/items/4").json()
    assert cart["discount_code"] is None and cart["discount"] == "0.00"
