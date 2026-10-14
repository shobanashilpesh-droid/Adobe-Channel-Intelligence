"""Reseller-facing X4C dashboard, scoped to a single demo reseller."""
import pandas as pd
import plotly.express as px
import streamlit as st
from services.metrics import subscription_metrics, pending_with_values, renewal_worklist, opportunity_worklist, money
from services.workflows import create_case, list_cases, update_case, STATUSES


def render(data, reseller_id):
    reseller = data["resellers"].iloc[0]
    st.title("My Adobe Business | Reseller Workspace")
    st.caption(f"X4C reseller experience · {reseller.reseller_name} ({reseller_id}) · Fictional data")
    metrics = subscription_metrics(data["subscriptions"])
    pending = pending_with_values(data)
    tabs = st.tabs(["My Customers", "My Subscriptions", "Renewals", "Pending Orders", "Growth Opportunities", "My Cases"])
    with tabs[0]:
        a,b,c,d = st.columns(4)
        a.metric("My customers", data["customers"].customer_id.nunique())
        b.metric("Active subscriptions", metrics["active_subscriptions"])
        c.metric("Active licenses", metrics["active_licenses"])
        d.metric("Overdue renewal customers", metrics["overdue_customers"])
        st.dataframe(data["customers"][["customer_id", "customer_name", "country", "status"]], use_container_width=True, hide_index=True)
    with tabs[1]:
        st.subheader("My Adobe subscriptions")
        st.dataframe(data["subscriptions"][["customer_name", "subscription_id", "product_name", "current_quantity", "renewal_date", "auto_renew", "status", "renewal_outcome"]].sort_values("renewal_date"), use_container_width=True, hide_index=True)
    with tabs[2]:
        a,b,c,d = st.columns(4)
        a.metric("Renewals in 30 days", metrics["renewals_30"])
        b.metric("Renewals in 90 days", metrics["renewals_90"])
        c.metric("Action required", metrics["overdue_subscriptions"])
        d.metric("Auto-renew disabled", metrics["auto_renew_disabled"])
        st.caption("Overdue cases require checking renewal order status, grace periods and cancellations before action.")
        renewals = renewal_worklist(data, ["UPCOMING", "ACTION_REQUIRED", "PROCESSING", "GRACE_PERIOD", "INVESTIGATION_REQUIRED"])
        st.dataframe(renewals[["customer_name", "subscription_id", "product_name", "current_quantity", "renewal_date", "renewal_outcome"]], use_container_width=True, hide_index=True)
        if not renewals.empty:
            with st.form("reseller_renewal_preview"):
                idx = st.selectbox("Choose subscription", renewals.index.tolist(), format_func=lambda i: f"{renewals.loc[i,'customer_name']} — {renewals.loc[i,'subscription_id']}")
                if st.form_submit_button("Prepare renewal follow-up (demo)"):
                    row = renewals.loc[idx]
                    case_id = create_case("RENEWAL_REVIEW", row.customer_id, reseller_id, row.subscription_id, f"Review renewal eligibility and pricing for {row.product_name}", "Reseller Account Team")
                    st.success(f"Review case created: {case_id}. No Adobe renewal order has been placed.")
    with tabs[3]:
        a,b,c = st.columns(3)
        a.metric("Pending license quantity", int(pending.pending_quantity.sum()))
        b.metric("Affected customers", pending.customer_id.nunique())
        c.metric("Illustrative exposure", money(pending.estimated_value.sum()))
        st.dataframe(pending[["customer_name", "subscription_id", "offer_id", "pending_quantity", "estimated_value", "detected_date"]], use_container_width=True, hide_index=True)
        if not pending.empty:
            with st.form("reseller_pending_case"):
                idx = st.selectbox("Pending acquisition", pending.index.tolist(), format_func=lambda i: f"{pending.loc[i,'customer_name']} — {pending.loc[i,'pending_quantity']} licenses")
                if st.form_submit_button("Investigate pending licenses"):
                    row = pending.loc[idx]
                    case_id = create_case("PENDING_PARTNER_ORDER", row.customer_id, reseller_id, row.subscription_id, f"Check existing orders before preparing purchase for {row.offer_id}", "Ingram Operations")
                    st.success(f"Investigation created: {case_id}. No purchase has been placed.")
        st.subheader("My recent Ingram orders")
        orders = data["ingram_orders"].sort_values("order_date", ascending=False)
        st.dataframe(orders[["ingram_order_id", "customer_id", "offer_id", "order_date", "quantity", "status", "invoiced_amount"]].head(50), use_container_width=True, hide_index=True)
    with tabs[4]:
        st.subheader("Adobe growth opportunities")
        rec = opportunity_worklist(data)
        st.caption("Recommendations and prices are synthetic. Eligibility, country and pricing must be checked before any live order.")
        if rec.empty:
            st.info("No current synthetic recommendations for this reseller.")
        else:
            st.dataframe(rec[["customer_name", "offer_id", "recommendation_type", "suggested_quantity", "confidence", "reseller_unit_price", "illustrative_value"]], use_container_width=True, hide_index=True)
            with st.form("reseller_opportunity_case"):
                idx = st.selectbox("Opportunity", rec.index.tolist(), format_func=lambda i: f"{rec.loc[i,'customer_name']} — {rec.loc[i,'recommendation_type']}")
                if st.form_submit_button("Prepare opportunity review"):
                    row = rec.loc[idx]
                    case_id = create_case("EXPANSION_OPPORTUNITY", row.customer_id, reseller_id, row.subscription_id, f"Validate {row.suggested_quantity} additional licenses for {row.offer_id}", "Reseller Sales")
                    st.success(f"Opportunity review created: {case_id}. This is not a quote or purchase.")
    with tabs[5]:
        st.subheader("My cases")
        cases = list_cases(reseller_id)
        if cases:
            st.dataframe(pd.DataFrame(cases), use_container_width=True, hide_index=True)
            with st.form("reseller_case_update"):
                selected = st.selectbox("Case", [c["case_id"] for c in cases])
                status = st.selectbox("New status", STATUSES)
                if st.form_submit_button("Update my case"):
                    update_case(selected, status)
                    st.success("Case status updated.")
        else:
            st.info("No cases for this reseller yet.")
