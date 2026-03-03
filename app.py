import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="AI Commerce Intelligence", layout="wide")

st.title("AI Commerce Intelligence Dashboard")

# Load Data
df = pd.read_excel("shopee_transactions_deep_sample.xlsx")

df["order_date"] = pd.to_datetime(df["order_date"])
df["order_week"] = df["order_date"].dt.isocalendar().week

# KPIs
total_gmv = df["revenue_sgd"].sum()
top_brand = df.groupby("brand")["revenue_sgd"].sum().idxmax()
repeat_rate = df.groupby("user_id").size().gt(1).mean()

col1, col2, col3 = st.columns(3)

col1.metric("Total GMV", f"${total_gmv:,.0f}")
col2.metric("Top Brand", top_brand)
col3.metric("Repeat Rate", f"{repeat_rate*100:.1f}%")

st.divider()

# Revenue by Brand
st.subheader("Revenue by Brand")
brand_revenue = df.groupby("brand")["revenue_sgd"].sum().sort_values()
st.bar_chart(brand_revenue)

# Weekly Revenue
st.subheader("Weekly Revenue Trend")
weekly_revenue = df.groupby("order_week")["revenue_sgd"].sum()
st.line_chart(weekly_revenue)

# Campaign Performance
st.subheader("Campaign Performance")
campaign_revenue = df.groupby("campaign")["revenue_sgd"].sum()
st.bar_chart(campaign_revenue)

st.divider()

st.subheader("AI Business Insight")

insight = f"""
Total GMV stands at {total_gmv:,.0f} SGD.

{top_brand} is the leading revenue driver, indicating strong category dominance.

Repeat rate at {repeat_rate*100:.1f}% suggests healthy retention, but growth can be accelerated through structured loyalty and upselling strategies.

Double down on high-performing brands during campaign windows like Double Day to maximize revenue efficiency.
"""

st.write(insight)
