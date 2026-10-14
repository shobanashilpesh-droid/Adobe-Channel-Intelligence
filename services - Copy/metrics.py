"""Business calculations. Renewal outcome is synthetic reconciled evidence, NOT date-only inference."""
import pandas as pd

ACTION_REQUIRED = "ACTION_REQUIRED"
PROCESSING = "PROCESSING"
COMPLETED = "COMPLETED"


def subscription_metrics(df, today=None):
    today = pd.Timestamp(today).normalize() if today is not None else pd.Timestamp.today().normalize()
    active = df[df.status.eq("ACTIVE")].copy()
    days = (active.renewal_date - today).dt.days
    upcoming = {f"renewals_{n}": int(days.between(0, n).sum()) for n in (30, 60, 90)}
    overdue = df[df.renewal_outcome.eq(ACTION_REQUIRED)]
    processing = df[df.renewal_outcome.eq(PROCESSING)]
    return {
        "active_subscriptions": len(active),
        "active_licenses": int(active.current_quantity.sum()),
        "overdue_customers": int(overdue.customer_id.nunique()),
        "overdue_subscriptions": len(overdue),
        "processing_renewals": len(processing),
        "auto_renew_disabled": int((~active.auto_renew).sum()),
        **upcoming,
    }


def order_metrics(data, lookback_days=365):
    orders = data["ingram_orders"]
    today = pd.Timestamp.today().normalize()
    completed = orders[orders.status.eq("INVOICED")].copy()
    recent = completed[completed.order_date.ge(today - pd.Timedelta(days=lookback_days))]
    return {
        "channel_revenue": float(recent.invoiced_amount.sum()),
        "purchasing_resellers": int(recent.reseller_id.nunique()),
        "completed_orders": len(recent),
    }


def pending_with_values(data):
    pending = data["pending"].copy()
    if pending.empty:
        pending["estimated_value"] = pd.Series(dtype=float)
        return pending
    mapping = data["mapping"][["reseller_id", "ingram_reseller_id"]]
    pending = pending.merge(mapping, on="reseller_id", how="left")
    prices = data["prices"][["ingram_reseller_id", "offer_id", "reseller_unit_price", "currency"]]
    pending = pending.merge(prices, on=["ingram_reseller_id", "offer_id"], how="left")
    pending["estimated_value"] = pending.pending_quantity * pending.reseller_unit_price
    return pending


def reseller_sales_trend(data, days=90):
    today = pd.Timestamp.today().normalize()
    orders = data["ingram_orders"]
    paid = orders[orders.status.eq("INVOICED")]
    current = paid[paid.order_date.between(today - pd.Timedelta(days=days), today)]
    previous = paid[paid.order_date.between(today - pd.Timedelta(days=2 * days), today - pd.Timedelta(days=days + 1))]
    a = current.groupby("reseller_id").invoiced_amount.sum().rename("current_period")
    b = previous.groupby("reseller_id").invoiced_amount.sum().rename("previous_period")
    trend = data["resellers"][["reseller_id", "reseller_name"]].merge(a, on="reseller_id", how="left").merge(b, on="reseller_id", how="left")
    trend[["current_period", "previous_period"]] = trend[["current_period", "previous_period"]].fillna(0)
    trend["change_pct"] = trend.apply(lambda r: (r.current_period / r.previous_period - 1) * 100 if r.previous_period > 0 else float("nan"), axis=1)
    return trend


def renewal_worklist(data, statuses=None):
    subs = data["subscriptions"]
    if statuses:
        subs = subs[subs.renewal_outcome.isin(statuses)]
    return subs.sort_values("renewal_date").copy()


def opportunity_worklist(data):
    rec = data["recommendations"].copy()
    mapping = data["mapping"][["reseller_id", "ingram_reseller_id"]]
    rec = rec.merge(mapping, on="reseller_id", how="left")
    rec = rec.merge(data["prices"][["ingram_reseller_id", "offer_id", "reseller_unit_price", "currency"]], on=["ingram_reseller_id", "offer_id"], how="left")
    rec["illustrative_value"] = rec.suggested_quantity * rec.reseller_unit_price
    return rec


def money(value):
    return f"${value:,.0f}"  # Synthetic dataset prices are USD only.


def overdue_reseller_summary(data, today=None):
    """Renewal-driven reseller risk; never infer non-renewal from purchase inactivity.

    ACTION_REQUIRED is a synthetic *reconciled* classification, produced using
    renewal/order evidence. INVESTIGATION_REQUIRED is tracked separately.
    """
    today = pd.Timestamp(today).normalize() if today is not None else pd.Timestamp.today().normalize()
    subs = data["subscriptions"].copy()
    overdue = subs.loc[subs.renewal_outcome.eq(ACTION_REQUIRED)].copy()
    overdue = overdue[overdue.renewal_date.notna() & overdue.renewal_date.lt(today)]
    overdue["days_past_renewal"] = (today - overdue.renewal_date).dt.days
    if overdue.empty:
        cols = ["reseller_id", "reseller_name", "affected_customers", "overdue_subscriptions", "overdue_licenses", "oldest_days_overdue", "last_renewal_date"]
        return pd.DataFrame(columns=cols), overdue
    summary = overdue.groupby(["reseller_id", "reseller_name"], dropna=False).agg(
        affected_customers=("customer_id", "nunique"),
        overdue_subscriptions=("subscription_id", "nunique"),
        overdue_licenses=("current_quantity", "sum"),
        oldest_days_overdue=("days_past_renewal", "max"),
        last_renewal_date=("renewal_date", "min"),
    ).reset_index().sort_values(["affected_customers", "oldest_days_overdue"], ascending=False)
    return summary, overdue


def overdue_renewal_aging(overdue):
    """Aging based on the subscription renewal date, not last purchase date."""
    labels = ["1–7 days", "8–30 days", "31–60 days", "60+ days"]
    if overdue.empty:
        return pd.DataFrame({"aging": labels, "subscriptions": [0] * 4})
    buckets = pd.cut(overdue.days_past_renewal, bins=[0, 7, 30, 60, float("inf")], labels=labels, include_lowest=True)
    counts = buckets.value_counts().reindex(labels, fill_value=0)
    return pd.DataFrame({"aging": labels, "subscriptions": counts.values})
