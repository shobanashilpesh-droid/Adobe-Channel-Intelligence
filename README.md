# Adobe Channel Intelligence Hub — runnable Streamlit prototype

Two differentiated views: Adobe Vendor X4V (channel growth and revenue assurance) and Reseller X4C (customer portfolio, renewals, orders, expansion).

## Quick start (Windows, VS Code)

1. Extract the ZIP and open the **Adobe-Channel-Intelligence** folder in VS Code (the folder containing `app.py`).
2. Open **Terminal > New Terminal**.
3. Install dependencies:

   ```powershell
   py -m pip install -r requirements.txt
   ```

4. Regenerate synthetic data if desired:

   ```powershell
   py generate_data.py
   ```

5. Launch:

   ```powershell
   py -m streamlit run app.py
   ```

   Or use `python -m pip`, `python generate_data.py`, `python -m streamlit run app.py` if `py` is unavailable.

6. Open the local URL printed in the terminal, usually http://localhost:8501.

## Folder structure

- `app.py`: entry point and portal switcher
- `pages/adobe_vendor.py`: vendor dashboard
- `pages/reseller_portal.py`: reseller dashboard
- `services/data_loader.py`: CSV loading and data joins
- `services/metrics.py`: KPIs, renewal and exposure logic
- `services/workflows.py`: SQLite-based demo cases
- `services/adobe_client.py`: OPTIONAL read-only Adobe client scaffold; never called in demo
- `generate_data.py`: generates 9 synthetic CSV files
- `data/`: the 9 CSV datasets (included)
- `requirements.txt`: dependencies

## Suggested leadership demo

1. Open Adobe X4V > Channel Overview to see reseller coverage, revenue and overdue renewals.
2. Go to Pending Partner Orders, select a customer and click Request order reconciliation.
3. Switch to Reseller X4C, choose that reseller, and open My Cases to see the same case.
4. Review Renewals and prepare a renewal follow-up.
5. Review Growth Opportunities and prepare an opportunity review.

## Important limitations

- All data is fictional; no Adobe or Ingram customer information is included.
- All USD prices and revenue figures are illustrative. Annual price is not necessarily actual invoice value.
- `renewal_outcome` is a **pre-reconciled synthetic field**, not a claim that renewal status can be inferred from renewal date alone. Real reconciliation requires Adobe subscription/order and Ingram order evidence, grace periods, auto-renewal and cancellation checks.
- Pending acquisitions are outstanding order exposure, not confirmed lost revenue.
- The demo reseller selector is not authentication. In production, enforce reseller tenancy and Adobe contractual permissions server-side.
- SQLite cases are stored in `demo_cases.db` locally. Cloud-hosted local SQLite may reset and is not a production shared database.
- The Adobe API scaffold needs contract-specific base URL, auth, headers, pagination, rate limiting, API schema validation, and permission review before use.
- No live transactions or Adobe subscription changes are made.
