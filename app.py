import streamlit as st
import pandas as pd

st.set_page_config(page_title="AI Commerce Intelligence", layout="wide")
st.title("AI Commerce Intelligence Dashboard")

# Load Data
df = pd.read_excel("shopee_transactions_deep_sample.xlsx")
df["order_date"] = pd.to_datetime(df["order_date"])
df["order_week"] = df["order_date"].dt.isocalendar().week

# Sidebar Filters
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

# KPI Metrics
total_gmv = filtered_df["revenue_sgd"].sum()
unique_customers = filtered_df["user_id"].nunique()
repeat_rate = filtered_df[filtered_df.duplicated(subset=["user_id"], keep=False)]["user_id"].nunique() / max(unique_customers,1)
top_brand = filtered_df.groupby("brand")["revenue_sgd"].sum().idxmax() if not filtered_df.empty else "N/A"

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total GMV", f"${total_gmv:,.0f}")
col2.metric("Unique Customers", unique_customers)
col3.metric("Repeat Rate", f"{repeat_rate*100:.1f}%")
col4.metric("Top Brand", top_brand)

st.markdown("---")

# Visuals
st.subheader("Revenue by Brand")
brand_revenue = filtered_df.groupby("brand")["revenue_sgd"].sum()
st.bar_chart(brand_revenue)

st.subheader("Weekly Revenue Trend")
weekly_revenue = filtered_df.groupby("order_week")["revenue_sgd"].sum()
st.line_chart(weekly_revenue)

st.subheader("Campaign Revenue Breakdown")
campaign_revenue = filtered_df.groupby("campaign")["revenue_sgd"].sum()
st.bar_chart(campaign_revenue)

st.markdown("---")

# Dynamic Insight Logic
st.subheader("Automated Insights")

if filtered_df.empty:
    st.write("No data selected.")
else:
    insights = []

    # Strengths
    if total_gmv > 0:
        insights.append(f"**Revenue is positive at ${total_gmv:,.0f}**, indicating demand within selected scope.")
    if repeat_rate > 0.3:
        insights.append(f"Repeat rate ({repeat_rate*100:.1f}%) suggests strong retention potential.")
    else:
        insights.append("Repeat rate is low; consider retention strategies like loyalty bundles and post-purchase vouchers.")

    # Top products
    top_products = filtered_df.groupby("product_name")["revenue_sgd"].sum().sort_values(ascending=False).head(3)
    insights.append("Top products in this view: " + ", ".join(top_products.index.tolist()))

    # Distribution patterns
    if campaign_revenue.max() > (total_gmv * 0.4):
        top_campaign = campaign_revenue.idxmax()
        insights.append(f"Campaign **{top_campaign}** drives a large share of revenue — focus optimization here.")

    # Risks
    if len(filtered_df["brand"].unique()) < 2:
        insights.append("Revenue concentration in a narrow set of brands; consider diversifying product exposure.")

    # Present insights
    for i, line in enumerate(insights, start=1):
        st.write(f"{i}. {line}")
