from tests.ui.pages.base_page import BasePage


class CheckoutPage(BasePage):
    path = "/checkout"

    @property
    def total(self) -> str:
        return self.by_test_id("checkout-total").inner_text().replace("$", "")

    def place_order(self, email: str, province: str | None = None):
        self.by_test_id("email-input").fill(email)
        if province:
            self.by_test_id("checkout-province").select_option(province)
        self.by_test_id("place-order").click()
        return self

    @property
    def error(self):
        return self.by_test_id("checkout-error")

    def confirmation(self):
        from tests.ui.pages.order_page import OrderPage

        page = OrderPage(self.page)
        page.by_test_id("order-heading").wait_for()
        return page
