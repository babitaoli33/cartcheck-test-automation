import pytest

from tests.conftest import assert_matches_schema

pytestmark = pytest.mark.api


@pytest.mark.smoke
def test_health_check(api):
    resp = api.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.smoke
@pytest.mark.req("REQ-01")
def test_product_list_returns_all_products(api):
    resp = api.get("/products")
    assert resp.status_code == 200
    products = resp.json()
    assert len(products) == 7
    assert len({p["id"] for p in products}) == 7, "product ids must be unique"


@pytest.mark.req("REQ-01", "REQ-18")
def test_every_product_matches_contract(api):
    for product in api.get("/products").json():
        assert_matches_schema(product, "product")


@pytest.mark.req("REQ-01")
def test_get_single_product(api):
    resp = api.get("/products/4")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Desk Lamp"
    assert resp.json()["price"] == "39.00"


@pytest.mark.req("REQ-01")
def test_out_of_stock_product_is_flagged(api):
    bottle = api.get("/products/5").json()
    assert bottle["stock"] == 0 and bottle["in_stock"] is False


@pytest.mark.req("REQ-02")
@pytest.mark.parametrize("product_id", [0, 999])
def test_unknown_product_returns_404(api, product_id):
    resp = api.get(f"/products/{product_id}")
    assert resp.status_code == 404
    assert_matches_schema(resp.json(), "error")


@pytest.mark.req("REQ-02")
def test_non_numeric_product_id_returns_404(api):
    assert api.get("/products/abc").status_code == 404
