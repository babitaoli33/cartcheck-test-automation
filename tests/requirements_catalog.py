"""The 20 written requirements for ShopLite. Tests link to them with @pytest.mark.req("REQ-xx")."""

REQUIREMENTS = {
    "REQ-01": "The product list returns every product with id, name, price, stock and category.",
    "REQ-02": "Requesting an unknown product returns 404 with an error message.",
    "REQ-03": "Creating a cart returns a new, empty cart with a unique id.",
    "REQ-04": "Item quantity must be a whole number from 1 to 10; anything else returns 400.",
    "REQ-05": "A cart can never hold more of a product than is in stock (409 Conflict).",
    "REQ-06": "Adding a product that is already in the cart increases its quantity.",
    "REQ-07": "A shopper can remove an item from the cart.",
    "REQ-08": "Subtotal is the sum of unit price x quantity, shown with 2 decimals.",
    "REQ-09": "Code SAVE10 takes 10% off the subtotal.",
    "REQ-10": "Code WELCOME5 takes $5.00 off when the subtotal is $25.00 or more.",
    "REQ-11": "Unknown or expired codes return 400, and only one code can be applied per cart.",
    "REQ-12": "Tax is charged on (subtotal - discount) at the province rate, rounded half-up to the cent.",
    "REQ-13": "An unsupported province returns 400.",
    "REQ-14": "Checkout requires a valid email address.",
    "REQ-15": "An empty cart cannot be checked out.",
    "REQ-16": "Checkout reduces stock by the quantities ordered.",
    "REQ-17": "Checkout returns an order id, and the order total equals the cart total.",
    "REQ-18": "API responses match their published JSON Schema contracts.",
    "REQ-19": "UI: a shopper can browse products, add them to the cart, and the cart badge shows the total quantity.",
    "REQ-20": "UI: a shopper can apply a discount, check out and see an order confirmation.",
}
