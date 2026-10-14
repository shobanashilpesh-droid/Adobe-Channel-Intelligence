"""Load and join the fictional Adobe + Ingram CSV datasets."""
from pathlib import Path
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FILES = {
    "resellers": "adobe_resellers.csv",
    "customers": "adobe_customers.csv",
    "subscriptions": "adobe_subscriptions.csv",
    "adobe_orders": "adobe_orders.csv",
    "ingram_orders": "ingram_orders.csv",
    "pending": "adobe_open_acquisitions.csv",
    "recommendations": "adobe_recommendations.csv",
    "mapping": "ingram_reseller_mapping.csv",
    "prices": "ingram_prices.csv",
}

@st.cache_data(show_spinner=False)
def load_data():
    missing = [filename for filename in FILES.values() if not (DATA / filename).exists()]
    if missing:
        raise FileNotFoundError("Missing CSV files: " + ", ".join(missing) + ". Run python generate_data.py")
    tables = {key: pd.read_csv(DATA / filename) for key, filename in FILES.items()}
    for name, fields in {
        "subscriptions": ["renewal_date"],
        "adobe_orders": ["order_date"],
        "ingram_orders": ["order_date"],
        "pending": ["detected_date"],
    }.items():
        for field in fields:
            tables[name][field] = pd.to_datetime(tables[name][field], errors="coerce")
    tables["subscriptions"]["auto_renew"] = tables["subscriptions"]["auto_renew"].astype(str).str.lower().eq("true")
    tables["customers"] = tables["customers"].merge(
        tables["resellers"][["reseller_id", "reseller_name", "country"]],
        on="reseller_id", how="left", suffixes=("", "_reseller")
    )
    tables["subscriptions"] = tables["subscriptions"].merge(
        tables["customers"][["customer_id", "customer_name", "reseller_id", "reseller_name", "country"]],
        on="customer_id", how="left"
    )
    tables["pending"] = tables["pending"].merge(
        tables["customers"][["customer_id", "customer_name", "reseller_name"]],
        on="customer_id", how="left"
    )
    tables["recommendations"] = tables["recommendations"].merge(
        tables["customers"][["customer_id", "customer_name", "reseller_id", "reseller_name"]],
        on="customer_id", how="left"
    )
    tables["ingram_orders"] = tables["ingram_orders"].merge(
        tables["mapping"][["ingram_reseller_id", "reseller_id"]],
        on="ingram_reseller_id", how="left"
    )
    return tables


def filtered_data(data, reseller_id=None, country=None):
    """Return new scoped tables; no mutation of cached originals."""
    out = {key: frame.copy() for key, frame in data.items()}
    permitted = data["resellers"]
    if country and country != "All countries":
        permitted = permitted[permitted.country.eq(country)]
    if reseller_id:
        permitted = permitted[permitted.reseller_id.eq(reseller_id)]
    ids = set(permitted.reseller_id)
    customers = out["customers"][out["customers"].reseller_id.isin(ids)]
    cids = set(customers.customer_id)
    out["resellers"] = permitted.copy()
    out["customers"] = customers.copy()
    for key in ["subscriptions", "adobe_orders", "ingram_orders", "pending", "recommendations"]:
        out[key] = out[key][out[key].customer_id.isin(cids)].copy()
    out["mapping"] = out["mapping"][out["mapping"].reseller_id.isin(ids)].copy()
    out["prices"] = out["prices"][out["prices"].ingram_reseller_id.isin(out["mapping"].ingram_reseller_id)].copy()
    return out
