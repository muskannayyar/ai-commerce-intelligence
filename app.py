import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="AI Commerce Intelligence", layout="wide")

# ---- Custom Dark Theme ----
st.markdown("""
    <style>
    .main {
        background-color: #0E1117;
    }
    h1, h2, h3, h4 {
        color: #F5F5F5;
    }
    .stMetric {
        background-color: #1C1F26;
        padding: 15px;
        border-radius: 12px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("AI Commerce Intelligence Dashboard")

# ---- Load Data ----
df = pd.read_excel("shopee_transactions_deep_sample.xlsx")
df["order_date"] = pd.to_datetime(df["order_date"])
df["order_week"] = df["order_date"].dt.isocalendar().week

# ---- Sidebar Filters ----
st.sidebar.header("Filters")

brands = st.sidebar.multiselect(
    "Select Brand",
    options=df["brand"].unique(),
    default=df["brand"].unique()
)

campaigns = st.sidebar.multiselect(
    "Select Campaign",
    options=df["campaign"].unique(),
    default=df["campaign"].unique()
)

filtered_df = df[
    (df["brand"].isin(brands)) &
    (df["campaign"].isin(campaigns))
]

if filtered_df.empty:
    st.warning("No data available for selected filters.")
    st.stop()

# ---- KPI Calculations ----
total_gmv = filtered_df["revenue_sgd"].sum()
unique_customers = filtered_df["user_id"].nunique()

repeat_users = filtered_df[filtered_df.duplicated(subset=["user_id"], keep=False)]["user_id"].nunique()
repeat_rate = repeat_users / max(unique_customers, 1)

brand_revenue = filtered_df.groupby("brand")["revenue_sgd"].sum().sort_values(ascending=False)
campaign_revenue = filtered_df.groupby("campaign")["revenue_sgd"].sum().sort_values(ascending=False)
product_revenue = filtered_df.groupby("product_name")["revenue_sgd"].sum().sort_values(ascending=False)
weekly_revenue = filtered_df.groupby("order_week")["revenue_sgd"].sum()

top_brand = brand_revenue.index[0]
top_brand_share = brand_revenue.iloc[0] / total_gmv

# ---- KPI Row ----
col1, col2, col3, col4 = st.columns(4)

col1.metric("Total GMV", f"${total_gmv:,.0f}")
col2.metric("Unique Customers", unique_customers)
col3.metric("Repeat Rate", f"{repeat_rate*100:.1f}%")
col4.metric("Top Brand", top_brand)

st.markdown("---")

# ---- Revenue by Brand ----
st.subheader("Revenue by Brand")

brand_df = brand_revenue.reset_index()
brand_df.columns = ["Brand", "Revenue"]

fig_brand = px.bar(
    brand_df,
    x="Brand",
    y="Revenue",
    color="Brand",
    template="plotly_dark"
)

st.plotly_chart(fig_brand, use_container_width=True)

# ---- Weekly Revenue Trend ----
st.subheader("Weekly Revenue Trend")

weekly_df = weekly_revenue.reset_index()
weekly_df.columns = ["Week", "Revenue"]

fig_week = px.line(
    weekly_df,
    x="Week",
    y="Revenue",
    markers=True,
    template="plotly_dark"
)

st.plotly_chart(fig_week, use_container_width=True)

# ---- Campaign Revenue ----
st.subheader("Campaign Revenue")

campaign_df = campaign_revenue.reset_index()
campaign_df.columns = ["Campaign", "Revenue"]

fig_campaign = px.bar(
    campaign_df,
    x="Campaign",
    y="Revenue",
    color="Campaign",
    template="plotly_dark"
)

st.plotly_chart(fig_campaign, use_container_width=True)

st.markdown("---")

# ---- Automated Executive Intelligence ----
st.subheader("AI Executive Intelligence")

st.markdown("### Executive Summary")
st.write(f"Total GMV: ${total_gmv:,.0f}")
st.write(f"Top Brand: {top_brand} contributing {top_brand_share*100:.1f}% of revenue.")
st.write(f"Repeat Rate: {repeat_rate*100:.1f}%")

st.markdown("### Growth Drivers")

top_products = product_revenue.head(3).index.tolist()
for p in top_products:
    st.write(f"- {p}")

if campaign_revenue.iloc[0] / total_gmv > 0.4:
    st.write(f"- Revenue heavily influenced by campaign: {campaign_revenue.index[0]}")

st.markdown("### Strategic Risks")

if top_brand_share > 0.6:
    st.write("- Revenue concentration risk detected in a single brand.")
else:
    st.write("- Revenue distribution relatively balanced across brands.")

if repeat_rate < 0.4:
    st.write("- Weak retention. Opportunity to build loyalty programs.")
else:
    st.write("- Strong retention base. Upsell and premium bundling possible.")

st.markdown("### Recommended Actions")

st.write("- Double down on top-performing SKUs during high-performing campaign windows.")
st.write("- Optimize underperforming brands through visibility and pricing strategy.")
st.write("- Implement structured retention campaigns targeting repeat buyers.")
