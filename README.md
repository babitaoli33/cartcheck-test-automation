# CartCheck: Test Automation Framework

![tests](https://github.com/babitaoli33/cartcheck-test-automation/actions/workflows/tests.yml/badge.svg)

A Python test automation framework for **ShopLite**, a small web store with a JSON API and server-rendered pages. It combines API tests, JSON Schema contract tests and Playwright browser tests, links every test to a written requirement, and runs in GitHub Actions on every push.

| | |
|---|---|
| **Tests** | 97 total: 84 API (including contract tests) and 13 UI |
| **Requirements covered** | 20 of 20, with a traceability matrix regenerated on every run |
| **Defects found** | 7 (2 Critical, 3 Major, 2 Minor), each with a full [bug report](docs/bug_reports.md) |
| **Stack** | Python, pytest, requests, jsonschema, Playwright, pytest-html, GitHub Actions |

> ShopLite (in `app/`) is the application under test. It was built for this project and ships with defects so the framework has real bugs to find, the same way QA training sites do. The defects were not marked in the code; the suite found them through boundary, negative and data-driven tests.

## What the suite found

| ID | Defect | Severity |
|---|---|---|
| BUG-01 | Tax is charged on the subtotal **before** the discount, overcharging every discounted order | Critical |
| BUG-03 | Stock is not enforced across adds or carts; two orders can push stock below zero | Critical |
| BUG-02 | Tax is truncated instead of rounded half-up (off by a cent) | Major |
| BUG-04 | Quantity 0 is accepted | Major |
| BUG-06 | A discount code can be applied twice and stacks | Major |
| BUG-05 | WELCOME5 rejects a subtotal of exactly $25.00 | Minor |
| BUG-07 | Cart badge shows the number of products, not the total quantity (UI) | Minor |

Each bug has steps to reproduce, expected vs. actual results and a severity in [`docs/bug_reports.md`](docs/bug_reports.md).

## How it works

```
tests/
├── conftest.py              # live server, API client, schema helper, traceability report
├── requirements_catalog.py  # REQ-01 ... REQ-20
├── data/                    # data-driven inputs (tax_cases.json, quantity_boundaries.csv)
├── api/                     # products, cart, discounts, tax, checkout, contracts
└── ui/
    ├── pages/               # Page Object Model: products, cart, checkout, order pages
    └── test_shopping_flow.py
schemas/                     # JSON Schema contracts for product, cart, order, error
docs/                        # test plan and bug reports
reports/traceability.md      # requirement -> tests -> result (generated)
```

**Design choices**

- **Test pyramid:** business rules are checked at the API level, which is fast and reliable. The 13 UI tests cover the real shopper journey.
- **Requirements traceability:** every test carries `@pytest.mark.req("REQ-xx")`. A pytest hook builds [`reports/traceability.md`](reports/traceability.md) after each run and flags any requirement with no tests (`--strict-markers` blocks typos in marker names).
- **Known bugs as strict expected failures:** open defects are marked `xfail(strict=True, reason="BUG-xx")`. The build stays green while a bug is known. When a developer fixes it, the test passes unexpectedly and strict mode fails the build until QA verifies the fix. Each marker was checked by fixing its bug in a scratch copy and confirming that exactly that test flipped.
- **Test design techniques:** boundary values (quantity -1/0/1/10/11, discount threshold 24.99/25.00), equivalence classes, negative tests (wrong types, missing data, invalid emails), and money cases that land on a half cent, where rounding bugs show up.
- **Isolation:** the store resets before every test and the server runs on a random port, so tests are independent and order does not matter.
- **Stable UI locators:** pages expose `data-testid` attributes, and tests reach them only through page objects.

## Running the tests

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install chromium

python -m pytest -m smoke                 # quick health check
python -m pytest -m api                   # API + contract tests
python -m pytest -m ui --headed           # watch the browser tests run
python -m pytest --html=reports/test-report.html --self-contained-html
```

Expected result: `87 passed, 10 xfailed` (the 10 expected failures are the 7 logged bugs).

To try the store yourself: `python -m app.server`, then open http://127.0.0.1:5000.

## CI

`.github/workflows/tests.yml` installs Chromium and runs the smoke, API and UI suites on every push and pull request. It saves the HTML report, the traceability matrix and screenshots of failed UI tests as build artifacts.

## Documents

- [Test plan](docs/test_plan.md): scope, approach, techniques, entry and exit criteria
- [Bug reports](docs/bug_reports.md)
- [Traceability matrix](reports/traceability.md)

## License

MIT
