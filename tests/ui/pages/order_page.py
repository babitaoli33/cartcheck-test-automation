from tests.ui.pages.base_page import BasePage


class OrderPage(BasePage):
    @property
    def order_id(self) -> str:
        return self.by_test_id("order-id").inner_text()

    @property
    def total(self) -> str:
        return self.by_test_id("order-total").inner_text().replace("$", "")
