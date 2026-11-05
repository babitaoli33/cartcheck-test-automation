import pytest

pytestmark = pytest.mark.api


@pytest.mark.smoke
@pytest.mark.req("REQ-17")
def test_checkout_happy_path(api, cart_with):
    cart_id = cart_with({1: 1, 3: 2})
    cart_total = api.cart(cart_id, "QC").json()["total"]
    resp = api.checkout(cart_id, province="QC")
    assert resp.status_code == 201
    order = resp.json()
    assert order["order_id"].startswith("ORD-")
    assert order["total"] == cart_total


@pytest.mark.req("REQ-17")
def test_order_can_be_retrieved(api, cart_with):
    order = api.checkout(cart_with({3: 1})).json()
    resp = api.get(f"/orders/{order['order_id']}")
    assert resp.status_code == 200 and resp.json() == order


@pytest.mark.req("REQ-17")
def test_unknown_order_returns_404(api):
    assert api.get("/orders/ORD-0").status_code == 404


@pytest.mark.req("REQ-14")
@pytest.mark.parametrize("email", ["", "not-an-email", "a@b", "two@@example.com", "spa ce@example.com", None])
def test_invalid_email_is_rejected(api, cart_with, email):
    resp = api.checkout(cart_with({3: 1}), email=email)
    assert resp.status_code == 400
    assert "email" in resp.json()["error"]


@pytest.mark.req("REQ-15")
def test_empty_cart_cannot_check_out(api):
    resp = api.checkout(api.new_cart())
    assert resp.status_code == 400
    assert "empty" in resp.json()["error"].lower()


@pytest.mark.req("REQ-16")
def test_checkout_reduces_stock(api, cart_with):
    api.checkout(cart_with({1: 2, 4: 1}))
    assert api.get("/products/1").json()["stock"] == 8
    assert api.get("/products/4").json()["stock"] == 4


@pytest.mark.req("REQ-16")
def test_failed_checkout_does_not_change_stock(api, cart_with):
    api.checkout(cart_with({1: 2}), email="bad")
    assert api.get("/products/1").json()["stock"] == 10


@pytest.mark.req("REQ-05", "REQ-16")
@pytest.mark.xfail(reason="BUG-03: two carts can buy more than the stock; stock goes negative")
def test_stock_never_goes_negative(api, cart_with):
    first, second = cart_with({4: 3}), cart_with({4: 3})  # 6 lamps, only 5 in stock
    assert api.checkout(first).status_code == 201
    assert api.checkout(second).status_code == 409
    assert api.get("/products/4").json()["stock"] >= 0


@pytest.mark.req("REQ-17")
def test_cart_is_locked_after_checkout(api, cart_with):
    cart_id = cart_with({3: 1})
    api.checkout(cart_id)
    assert api.add(cart_id, 3, 1).status_code == 409
    assert api.checkout(cart_id).status_code == 409
