from playwright.sync_api import Page


class BasePage:
    """Shared header elements. Locators use data-testid so tests survive styling changes."""

    path = "/"

    def __init__(self, page: Page):
        self.page = page

    def open(self, query: str = ""):
        self.page.goto(self.path + query)
        return self

    def by_test_id(self, test_id: str):
        return self.page.get_by_test_id(test_id)

    @property
    def cart_badge_count(self) -> int:
        return int(self.by_test_id("cart-badge").inner_text())

    def go_to_cart(self):
        from tests.ui.pages.cart_page import CartPage

        self.by_test_id("cart-link").click()
        return CartPage(self.page)
