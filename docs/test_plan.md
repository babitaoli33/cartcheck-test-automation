# Test plan: ShopLite web store

## 1. Scope

**In scope:** the ShopLite JSON API (products, carts, discounts, tax, checkout, orders) and the
main browser journey (browse → add to cart → discount → checkout → confirmation).

**Out of scope:** performance and load, security testing beyond input validation, payment
processing (ShopLite has no payment step), and accessibility auditing.

The 20 requirements under test are listed in [`tests/requirements_catalog.py`](../tests/requirements_catalog.py).
Coverage is reported per requirement in `reports/traceability.md`, which every test run regenerates.

## 2. Approach

| Level | Tool | What it covers |
|---|---|---|
| Smoke | pytest `-m smoke` | Server is up, products load, one cart can check out (API and UI). Runs first in CI. |
| API | pytest + requests | Business rules, validation, error handling, money calculations |
| Contract | jsonschema | Every response shape, including error responses, against `/schemas` |
| UI | Playwright + Page Object Model | The shopper journey through real pages in Chromium |

**Why most tests are API tests:** business rules (tax, discounts, stock) are faster and more
reliable to check through the API. UI tests are kept to the flows a shopper actually
experiences, which follows the test pyramid.

## 3. Test design techniques

- **Boundary value analysis:** quantity -1, 0, 1, 10, 11; WELCOME5 at 24.99, 25.00 and 28.24; adding exactly the stock vs. one more.
- **Equivalence partitioning:** valid vs. invalid discount codes (unknown, expired, empty, malformed); supported vs. unsupported provinces.
- **Negative testing:** wrong types (string, decimal, boolean, null quantity), missing bodies, unknown ids, invalid emails, empty-cart checkout, adding to a checked-out cart.
- **Data-driven testing:** tax cases in `tests/data/tax_cases.json` and quantity boundaries in `tests/data/quantity_boundaries.csv`, so new cases need no code changes.
- **Money checks:** expected values are calculated by hand with exact decimals. Cases are chosen to land on a half cent, where rounding mistakes appear.
- **State-based testing:** stock before and after checkout, a cart locked after ordering, a discount cleared when the cart empties.

## 4. Environment and data

- The application under test runs in-process on a random free port for each test session.
- Store state is reset before **every** test, so tests are independent and can run in any order.
- Seed data: 7 products, including one that is out of stock (Water Bottle) and one with low stock (Desk Lamp, 5).
- UI tests use `data-testid` locators so styling changes do not break them.

## 5. Defect management

- Each defect is written up in [`docs/bug_reports.md`](bug_reports.md) with steps, expected vs. actual, severity and the linked requirement.
- An open defect's test is marked `xfail(strict=True)` with its bug id. The suite stays green while the bug is known. Once the bug is fixed, the test passes unexpectedly, and strict mode fails the build so QA can verify and close it.
- Before release, each strict-xfail marker was confirmed by fixing the related bug in a scratch copy and checking that exactly that test flipped.

## 6. Entry and exit criteria

**Entry:** the application starts and the smoke suite passes.

**Exit:**
- every requirement has at least one linked test (20 of 20),
- no unexpected failures,
- every remaining failure maps to a logged defect with a severity,
- the HTML report and the traceability matrix are published as CI artifacts.
