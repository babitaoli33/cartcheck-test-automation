"""ShopLite Flask app: a JSON API under /api and server-rendered pages for the UI tests.

Run it on its own with:  python -m app.server   (http://127.0.0.1:5000)
"""

from __future__ import annotations

from flask import Flask, jsonify, redirect, render_template, request, session, url_for

from .store import TAX_RATES, Store, StoreError

store = Store()


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = "shoplite-demo-only"

    @app.errorhandler(StoreError)
    def handle_store_error(err: StoreError):
        if request.path.startswith("/api/"):
            return jsonify({"error": err.message}), err.status
        return render_template("error.html", message=err.message), err.status

    # ------------------------------------------------------------------ API
    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    @app.get("/api/products")
    def products():
        return jsonify(store.list_products())

    @app.get("/api/products/<int:product_id>")
    def product(product_id: int):
        return jsonify(store.get_product(product_id))

    @app.post("/api/carts")
    def create_cart():
        cart_id = store.create_cart()
        return jsonify(store.cart_summary(cart_id)), 201

    @app.get("/api/carts/<cart_id>")
    def get_cart(cart_id: str):
        return jsonify(store.cart_summary(cart_id, request.args.get("province", "ON")))

    @app.post("/api/carts/<cart_id>/items")
    def add_item(cart_id: str):
        body = request.get_json(silent=True) or {}
        return jsonify(store.add_item(cart_id, body.get("product_id"), body.get("quantity"))), 201

    @app.delete("/api/carts/<cart_id>/items/<int:product_id>")
    def remove_item(cart_id: str, product_id: int):
        return jsonify(store.remove_item(cart_id, product_id))

    @app.post("/api/carts/<cart_id>/discount")
    def discount(cart_id: str):
        body = request.get_json(silent=True) or {}
        return jsonify(store.apply_discount(cart_id, body.get("code")))

    @app.post("/api/carts/<cart_id>/checkout")
    def checkout(cart_id: str):
        body = request.get_json(silent=True) or {}
        return jsonify(store.checkout(cart_id, body.get("email"), body.get("province", "ON"))), 201

    @app.get("/api/orders/<order_id>")
    def order(order_id: str):
        return jsonify(store.get_order(order_id))

    # ------------------------------------------------------------------ UI
    def current_cart_id() -> str:
        cart_id = session.get("cart_id")
        if cart_id not in store.carts or store.carts[cart_id].status != "open":
            cart_id = store.create_cart()
            session["cart_id"] = cart_id
        return cart_id

    @app.context_processor
    def inject_cart():
        cart_id = session.get("cart_id")
        cart = store.carts.get(cart_id) if cart_id else None
        return {"cart_lines": len(cart.items) if cart and cart.status == "open" else 0}

    @app.get("/")
    def home():
        return render_template("products.html", products=store.list_products())

    @app.post("/cart/add")
    def ui_add():
        store.add_item(current_cart_id(), int(request.form["product_id"]), int(request.form.get("quantity", 1)))
        return redirect(url_for("home", added=request.form["product_id"]))

    @app.get("/cart")
    def ui_cart():
        province = request.args.get("province", "ON")
        error = request.args.get("error")
        return render_template("cart.html", cart=store.cart_summary(current_cart_id(), province),
                               provinces=sorted(TAX_RATES), error=error)

    @app.post("/cart/remove/<int:product_id>")
    def ui_remove(product_id: int):
        store.remove_item(current_cart_id(), product_id)
        return redirect(url_for("ui_cart"))

    @app.post("/cart/discount")
    def ui_discount():
        try:
            store.apply_discount(current_cart_id(), request.form.get("code", ""))
        except StoreError as err:
            return redirect(url_for("ui_cart", error=err.message))
        return redirect(url_for("ui_cart"))

    @app.route("/checkout", methods=["GET", "POST"])
    def ui_checkout():
        cart_id = current_cart_id()
        error = None
        if request.method == "POST":
            try:
                order = store.checkout(cart_id, request.form.get("email", ""), request.form.get("province", "ON"))
                return redirect(url_for("ui_order", order_id=order["order_id"]))
            except StoreError as err:
                error = err.message
        province = request.form.get("province", request.args.get("province", "ON"))
        return render_template("checkout.html", cart=store.cart_summary(cart_id, province),
                               provinces=sorted(TAX_RATES), error=error), (400 if error else 200)

    @app.get("/order/<order_id>")
    def ui_order(order_id: str):
        return render_template("order.html", order=store.get_order(order_id))

    return app


if __name__ == "__main__":
    create_app().run(debug=False)
