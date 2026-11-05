from tests.ui.pages.base_page import BasePage


class CartPage(BasePage):
    path = "/cart"

    def item_names(self) -> list[str]:
        return self.page.get_by_test_id("item-name").all_inner_texts()

    def row(self, product_id: int):
        return self.by_test_id(f"cart-row-{product_id}")

    def line_total(self, product_id: int) -> str:
        return self.row(product_id).get_by_test_id("line-total").inner_text()

    def remove(self, product_id: int):
        self.by_test_id(f"remove-{product_id}").click()
        return self

    def apply_code(self, code: str):
        self.by_test_id("discount-input").fill(code)
        self.by_test_id("apply-discount").click()
        return self

    def choose_province(self, province: str):
        with self.page.expect_navigation():
            self.by_test_id("province-select").select_option(province)
        return self

    def amount(self, test_id: str) -> str:
        """Read a money cell such as 'subtotal', 'tax' or 'total' without the $ sign."""
        return self.by_test_id(test_id).inner_text().replace("$", "").replace("-", "")

    @property
    def error(self):
        return self.by_test_id("cart-error")

    @property
    def is_empty(self) -> bool:
        return self.by_test_id("empty-cart").is_visible()

    def proceed_to_checkout(self):
        from tests.ui.pages.checkout_page import CheckoutPage

        self.by_test_id("checkout-link").click()
        return CheckoutPage(self.page)
