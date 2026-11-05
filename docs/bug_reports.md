# Bug reports

Seven defects were found in ShopLite by the CartCheck suite. Each one is tracked in the
suite as a **strict expected failure** (`@pytest.mark.xfail(strict=True)` with the bug id).
When a developer fixes a bug, its test starts passing, and strict mode turns that into a
CI failure until QA verifies the fix and removes the marker.

| ID | Title | Severity | Requirement | Found by |
|---|---|---|---|---|
| BUG-01 | Tax is charged on the subtotal before the discount | **Critical** | REQ-12 | `test_tax_is_charged_after_discount` |
| BUG-02 | Tax is truncated instead of rounded half-up | Major | REQ-12 | `test_tax_by_province[ON-half-up, AB-half-up, ON-round-up]` |
| BUG-03 | Stock is not enforced across adds or carts (overselling) | **Critical** | REQ-05, REQ-16 | `test_repeated_adds_cannot_exceed_stock`, `test_stock_never_goes_negative` |
| BUG-04 | Quantity 0 is accepted | Major | REQ-04 | `test_quantity_boundaries[boundary: just below minimum]` |
| BUG-05 | WELCOME5 rejects a subtotal of exactly $25.00 | Minor | REQ-10 | `test_welcome5_at_exact_minimum` |
| BUG-06 | A second discount code is accepted and discounts stack | Major | REQ-11 | `test_only_one_code_per_cart` |
| BUG-07 | Cart badge counts products, not total quantity | Minor | REQ-19 | `test_badge_shows_total_quantity` (UI) |

Severity scale: **Critical** = wrong money or data loss with no workaround; **Major** = wrong
behaviour that affects money or stock but has limited reach; **Minor** = cosmetic or edge case.

---

## BUG-01: Tax is charged on the subtotal before the discount

- **Severity:** Critical (every discounted order overcharges the customer)
- **Requirement:** REQ-12
- **Steps to reproduce:**
  1. `POST /api/carts`
  2. `POST /api/carts/{id}/items` with `{"product_id": 4, "quantity": 1}` (Desk Lamp, $39.00)
  3. `POST /api/carts/{id}/discount` with `{"code": "SAVE10"}`
  4. `GET /api/carts/{id}?province=ON`
- **Expected:** discount 3.90, taxable amount 35.10, tax **4.56**, total **39.66**
- **Actual:** tax **5.07** (13% of 39.00), total **40.17**, so the customer pays $0.51 too much
- **Notes:** the discount line is correct; only the tax base is wrong.

## BUG-02: Tax is truncated instead of rounded half-up

- **Severity:** Major (off by one cent on many orders; adds up across volume and fails reconciliation)
- **Requirement:** REQ-12
- **Steps to reproduce:** add 1 USB-C Cable ($10.50) to a cart, then `GET /api/carts/{id}?province=ON`
- **Expected:** 10.50 × 13% = 1.365, rounded half-up = **1.37**
- **Actual:** **1.36**
- **Other failing cases:** Wireless Mouse in AB (expected 1.25, actual 1.24); Wireless Mouse in ON (expected 3.25, actual 3.24)
- **Passing cases:** amounts that come out to exact cents (e.g. 13.00 in ON = 1.69), which is why
  normal happy-path testing would not catch it. The data-driven tax table in
  `tests/data/tax_cases.json` deliberately includes values that land on a half cent.

## BUG-03: Stock is not enforced across adds or carts (overselling)

- **Severity:** Critical (the store sells items it does not have; stock goes negative)
- **Requirements:** REQ-05, REQ-16
- **Steps to reproduce (single cart):**
  1. Create a cart and add 3 Desk Lamps (stock is 5); response 201
  2. Add 3 more Desk Lamps to the same cart
- **Expected:** 409 Conflict, since 6 would exceed the stock of 5
- **Actual:** 201 Created; the cart holds 6
- **Steps to reproduce (two carts):** two carts each add 3 Desk Lamps and both check out
- **Expected:** the second checkout returns 409
- **Actual:** both succeed and Desk Lamp stock becomes **-1**
- **Notes:** a single add of 6 is correctly rejected; the check compares only the requested
  quantity with stock, not the cart's running total, and checkout does not re-check stock.

## BUG-04: Quantity 0 is accepted

- **Severity:** Major (creates $0.00 lines and breaks the cart contract, where quantity minimum is 1)
- **Requirement:** REQ-04
- **Steps to reproduce:** `POST /api/carts/{id}/items` with `{"product_id": 3, "quantity": 0}`
- **Expected:** 400 Bad Request
- **Actual:** 201 Created; the cart contains Notebook × 0
- **Boundary results:** -1 → 400 ✔, **0 → 201 ✘**, 1 → 201 ✔, 10 → 201 ✔, 11 → 400 ✔

## BUG-05: WELCOME5 rejects a subtotal of exactly $25.00

- **Severity:** Minor (boundary edge case; customers just at the threshold lose $5)
- **Requirement:** REQ-10 ("$25.00 or more")
- **Steps to reproduce:** add 10 Sticky Notes ($2.50 each, subtotal exactly 25.00), then apply `WELCOME5`
- **Expected:** 200 OK, discount 5.00
- **Actual:** 400 "WELCOME5 needs a subtotal of at least $25.00"
- **Notes:** works at 28.24 and is correctly rejected at 24.99. The comparison is `>` instead of `>=`.

## BUG-06: A second discount code is accepted and discounts stack

- **Severity:** Major (revenue loss; codes can be applied repeatedly)
- **Requirement:** REQ-11 ("only one code can be applied per cart")
- **Steps to reproduce:** add a Desk Lamp, apply `SAVE10`, then apply `SAVE10` again
- **Expected:** 409 Conflict on the second attempt; discount stays 3.90
- **Actual:** 200 OK; discount becomes 7.80

## BUG-07: Cart badge counts products, not total quantity (UI)

- **Severity:** Minor (cosmetic, but misleading)
- **Requirement:** REQ-19
- **Steps to reproduce:** on the products page, choose quantity 3 for Notebook and click **Add to cart**
- **Expected:** header shows **Cart (3)**
- **Actual:** header shows **Cart (1)**
- **Notes:** the API's `item_count` is correct (3); only the page header uses the number of distinct products.
