from tests.ui.pages.base_page import BasePage


class ProductsPage(BasePage):
    path = "/"

    def card(self, product_id: int):
        return self.by_test_id(f"product-{product_id}")

    def product_names(self) -> list[str]:
        return self.page.get_by_test_id("product-name").all_inner_texts()

    def price(self, product_id: int) -> str:
        return self.card(product_id).get_by_test_id("product-price").inner_text()

    def add_to_cart(self, product_id: int, quantity: int = 1):
        card = self.card(product_id)
        card.get_by_test_id("qty-select").select_option(str(quantity))
        card.get_by_test_id("add-to-cart").click()
        self.by_test_id("added-notice").wait_for()
        return self

    def add_button(self, product_id: int):
        return self.card(product_id).get_by_test_id("add-to-cart")

    def is_out_of_stock(self, product_id: int) -> bool:
        return self.card(product_id).get_by_test_id("out-of-stock").is_visible()
