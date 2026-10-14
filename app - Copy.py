"""Adobe Channel Intelligence Hub — Streamlit demonstration.

Run: streamlit run app.py
No credentials required. All datasets are fictional and all actions are simulated.
"""
import streamlit as st
from services.data_loader import load_data, filtered_data
from pages import adobe_vendor, reseller_portal

st.set_page_config(page_title="Adobe Channel Intelligence | Xvantage Demo", page_icon="📊", layout="wide")
st.markdown("""<style>
.block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
[data-testid="stMetric"] {background: #f5f7fa; padding: 12px; border-radius: 10px;}
</style>""", unsafe_allow_html=True)

try:
    data = load_data()
except FileNotFoundError as exc:
    st.error(str(exc))
    st.code("python generate_data.py\nstreamlit run app.py", language="powershell")
    st.stop()

st.sidebar.title("Adobe Channel Intelligence")
st.sidebar.caption("Xvantage concept prototype")
view = st.sidebar.radio("Experience", ["Adobe Vendor — X4V", "Reseller — X4C"])
st.sidebar.divider()
if view.startswith("Adobe"):
    country = st.sidebar.selectbox("Country", ["All countries"] + sorted(data["resellers"].country.unique().tolist()))
    scoped = filtered_data(data, country=country)
    adobe_vendor.render(scoped)
else:
    resellers = data["resellers"].sort_values("reseller_name")
    options = resellers.reseller_id.tolist()
    selected = st.sidebar.selectbox("Demo signed-in reseller", options, format_func=lambda x: resellers.set_index("reseller_id").loc[x,"reseller_name"])
    scoped = filtered_data(data, reseller_id=selected)
    reseller_portal.render(scoped, selected)
st.sidebar.divider()
st.sidebar.warning("DEMO ONLY: Synthetic records, fictional USD prices, simulated actions. Not production access control.")
st.sidebar.caption("Adobe VIP Marketplace API integration scaffold: services/adobe_client.py")
