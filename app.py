import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import anthropic
import os

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Shopee Commerce Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Color palette ─────────────────────────────────────────────────────────────
C = {
    "blue":   "#3b82f6",
    "cyan":   "#06b6d4",
    "violet": "#818cf8",
    "purple": "#a78bfa",
    "green":  "#34d399",
    "amber":  "#f59e0b",
    "red":    "#f87171",
    "bg":     "#060d1a",
    "card":   "#0b1526",
    "border": "rgba(59,130,246,0.15)",
}

# ── Data ─────────────────────────────────────────────────────────────────────
monthly_data = pd.DataFrame([
    {"ym":"Oct 2025","month":"Oct","revenue":88216, "orders":218,"aov":405,"customers":217,"voucher_rate":50.0,"avg_delivery":3.1,"avg_rating":4.67},
    {"ym":"Nov 2025","month":"Nov","revenue":94439, "orders":201,"aov":470,"customers":199,"voucher_rate":55.2,"avg_delivery":3.1,"avg_rating":4.64},
    {"ym":"Dec 2025","month":"Dec","revenue":96386, "orders":204,"aov":472,"customers":203,"voucher_rate":45.1,"avg_delivery":3.1,"avg_rating":4.64},
    {"ym":"Jan 2026","month":"Jan","revenue":74936, "orders":177,"aov":423,"customers":176,"voucher_rate":44.1,"avg_delivery":3.0,"avg_rating":4.64},
])

weekly_data = pd.DataFrame([
    {"wk":"W40","revenue":11572,"orders":30,"aov":386,"voucher_rate":53.3},
    {"wk":"W41","revenue":19432,"orders":46,"aov":422,"voucher_rate":60.9},
    {"wk":"W42","revenue":16052,"orders":48,"aov":334,"voucher_rate":52.1},
    {"wk":"W43","revenue":19244,"orders":62,"aov":310,"voucher_rate":41.9},
    {"wk":"W44","revenue":31646,"orders":47,"aov":673,"voucher_rate":40.4},
    {"wk":"W45","revenue":14364,"orders":39,"aov":368,"voucher_rate":56.4},
    {"wk":"W46","revenue":24173,"orders":47,"aov":514,"voucher_rate":51.1},
    {"wk":"W47","revenue":17720,"orders":42,"aov":422,"voucher_rate":64.3},
    {"wk":"W48","revenue":28452,"orders":58,"aov":491,"voucher_rate":56.9},
    {"wk":"W49","revenue":13600,"orders":41,"aov":332,"voucher_rate":51.2},
    {"wk":"W50","revenue":19176,"orders":46,"aov":417,"voucher_rate":39.1},
    {"wk":"W51","revenue":12231,"orders":40,"aov":306,"voucher_rate":42.5},
    {"wk":"W52","revenue":33554,"orders":58,"aov":579,"voucher_rate":51.7},
    {"wk":"W01","revenue":26166,"orders":42,"aov":623,"voucher_rate":38.1},
    {"wk":"W02","revenue":19392,"orders":43,"aov":451,"voucher_rate":41.9},
    {"wk":"W03","revenue":13923,"orders":43,"aov":324,"voucher_rate":51.2},
    {"wk":"W04","revenue":19257,"orders":49,"aov":393,"voucher_rate":40.8},
    {"wk":"W05","revenue":14023,"orders":19,"aov":738,"voucher_rate":42.1},
])

categories_data = pd.DataFrame([
    {"name":"Electronics",  "revenue":251955,"orders":324,"color":C["blue"]},
    {"name":"Home & Living","revenue":67817, "orders":164,"color":C["cyan"]},
    {"name":"Fashion",      "revenue":26834, "orders":147,"color":C["violet"]},
    {"name":"Beauty",       "revenue":7371,  "orders":165,"color":C["purple"]},
])

campaigns_data = pd.DataFrame([
    {"name":"Double Day",    "revenue":89029,"orders":172,"color":C["blue"]},
    {"name":"Mega Campaign", "revenue":75121,"orders":168,"color":C["cyan"]},
    {"name":"Brand Day",     "revenue":68307,"orders":161,"color":C["violet"]},
    {"name":"Flash Sale",    "revenue":63142,"orders":136,"color":C["purple"]},
])

cities_data = pd.DataFrame([
    {"name":"Woodlands","revenue":67353,"orders":126},
    {"name":"Tampines", "revenue":62731,"orders":149},
    {"name":"Singapore","revenue":62174,"orders":149},
    {"name":"Punggol",  "revenue":60186,"orders":122},
    {"name":"Yishun",   "revenue":56635,"orders":138},
    {"name":"Jurong",   "revenue":44898,"orders":116},
])

payments_data = pd.DataFrame([
    {"name":"PayNow",      "value":104497,"orders":212,"color":C["blue"]},
    {"name":"ShopeePay",   "value":92065, "orders":199,"color":C["cyan"]},
    {"name":"SPayLater",   "value":80145, "orders":190,"color":C["violet"]},
    {"name":"Credit Card", "value":77270, "orders":199,"color":C["purple"]},
])

brands_data = pd.DataFrame([
    {"name":"LG",     "revenue":227248,"orders":158,"color":C["blue"]},
    {"name":"Philips","revenue":67817, "orders":164,"color":C["cyan"]},
    {"name":"Nike",   "revenue":26834, "orders":147,"color":C["violet"]},
    {"name":"Anker",  "revenue":24707, "orders":166,"color":C["purple"]},
    {"name":"COSRX",  "revenue":7371,  "orders":165,"color":C["green"]},
])

dow_data = pd.DataFrame([
    {"day":"Mon","revenue":45507,"orders":105},
    {"day":"Tue","revenue":47581,"orders":112},
    {"day":"Wed","revenue":62817,"orders":123},
    {"day":"Thu","revenue":41193,"orders":113},
    {"day":"Fri","revenue":56486,"orders":126},
    {"day":"Sat","revenue":50653,"orders":111},
    {"day":"Sun","revenue":49740,"orders":110},
])

SUMMARY = {
    "totalRev":353977,"totalOrders":800,"totalCust":772,
    "repeatRate":3.6,"avgDelivery":3.12,"avgRating":4.65,
    "voucherRate":48.75,"voucherDiscount":3890,
    "revPerCust":458.5,"gross":357867,
}

# MoM calculations
monthly_data["rev_mom"]  = monthly_data["revenue"].pct_change() * 100
monthly_data["ord_mom"]  = monthly_data["orders"].pct_change() * 100
monthly_data["aov_mom"]  = monthly_data["aov"].pct_change() * 100
monthly_data["cust_mom"] = monthly_data["customers"].pct_change() * 100
weekly_data["rev_wow"]   = weekly_data["revenue"].pct_change() * 100

AI_CTX = """Shopee Singapore data Oct 2025–Jan 2026, 800 orders.
Revenue: Oct S$88,216 → Nov S$94,439(+7.1%) → Dec S$96,386(+2.1%) → Jan S$74,936(-22.3%)
Total S$353,977 | AOV avg S$442 | Repeat rate 3.6% | Delivery 3.1d avg | Rating 4.65★ | Voucher 48.75%
Categories: Electronics 71% S$251,955 | Home&Living S$67,817 | Fashion S$26,834 | Beauty S$7,371
Brands: LG 64% S$227,248 dominates | Philips S$67,817 | Nike S$26,834 | Anker S$24,707
Campaigns: Double Day S$89,029 best | Mega Campaign S$75,121 | Brand Day S$68,307 | Flash Sale S$63,142
Cities: Woodlands best S$67,353 | Jurong weakest S$44,898 (-35% gap)
Payments: PayNow leads S$104,497 | ShopeePay S$92,065 | Device: Desktop 52% vs Mobile 48%
Weekly peaks: W52 Christmas S$33,554 | W44 Oct S$31,646 | Best AOV W05 Jan S$738
Day of week: Wednesday best S$62,817 | Thursday worst S$41,193
Voucher: 48.75% orders use vouchers, avg discount S$10, total S$3,890 leakage from S$357,867 gross"""

# ── Helpers ──────────────────────────────────────────────────────────────────
def fmt_s(v):
    return f"S${v/1000:.1f}K" if v >= 1000 else f"S${round(v)}"

def badge_html(pct):
    if pct is None or pd.isna(pct):
        return "—"
    p = float(pct)
    arrow = "↑" if p > 0 else ("↓" if p < 0 else "→")
    color = "#34d399" if p > 0 else ("#f87171" if p < 0 else "#94a3b8")
    return f'<span style="color:{color};font-weight:700">{arrow}{abs(p):.1f}%</span>'

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#94a3b8", family="sans-serif", size=11),
    margin=dict(l=0, r=0, t=10, b=0),
    showlegend=False,
    xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(color="#64748b", size=10)),
    yaxis=dict(showgrid=True, gridcolor="rgba(59,130,246,0.07)", zeroline=False, tickfont=dict(color="#64748b", size=10)),
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    background-color: #060d1a !important;
    color: #e2e8f0 !important;
}
.stApp { background-color: #060d1a !important; }
section[data-testid="stSidebar"] {
    background: #070e1d !important;
    border-right: 1px solid rgba(59,130,246,0.12) !important;
}
section[data-testid="stSidebar"] * { color: #94a3b8 !important; }
.stSelectbox > div > div { background: #0b1526 !important; border-color: rgba(59,130,246,0.2) !important; color: #93c5fd !important; }
.stTextInput > div > div > input { background: #0b1526 !important; border-color: rgba(59,130,246,0.2) !important; color: #e2e8f0 !important; }
.stButton > button {
    background: linear-gradient(135deg,#1d4ed8,#3b82f6) !important;
    color: white !important; border: none !important;
    border-radius: 9px !important; font-weight: 700 !important;
}
.stButton > button:hover { opacity: 0.88 !important; }
div[data-testid="metric-container"] {
    background: linear-gradient(135deg,rgba(11,21,38,.98),rgba(6,13,26,1)) !important;
    border: 1px solid rgba(59,130,246,.12) !important;
    border-radius: 14px !important; padding: 16px 18px !important;
}
.kpi-card {
    background: linear-gradient(135deg,rgba(11,21,38,.98),rgba(6,13,26,1));
    border: 1px solid rgba(59,130,246,.12);
    border-radius: 14px; padding: 18px 20px; margin-bottom: 10px;
}
.kpi-val { font-family:'JetBrains Mono',monospace; font-size:22px; font-weight:700; margin-bottom:4px; }
.kpi-label { font-size:11px; color:#94a3b8; font-weight:600; margin-bottom:3px; }
.kpi-sub { font-size:10px; color:#475569; }
.section-header { font-size:18px; font-weight:800; color:#f1f5f9; margin-bottom:4px; }
.section-sub { font-size:12px; color:#475569; margin-bottom:18px; }
.insight-card {
    border-radius:12px; padding:13px 15px; margin-bottom:10px;
}
.chat-msg-user {
    background: linear-gradient(135deg,#1d4ed8,#2563eb);
    border-radius:13px 13px 3px 13px; padding:10px 13px;
    font-size:13px; color:#e2e8f0; margin:4px 0; max-width:85%; margin-left:auto;
}
.chat-msg-ai {
    background:rgba(255,255,255,.05); border:1px solid rgba(59,130,246,.12);
    border-radius:13px 13px 13px 3px; padding:10px 13px;
    font-size:13px; color:#cbd5e1; margin:4px 0; max-width:90%; line-height:1.7;
}
.stDataFrame { background:#0b1526 !important; }
div[data-testid="stHorizontalBlock"] { gap:12px; }
hr { border-color: rgba(59,130,246,0.1) !important; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;padding-bottom:16px;border-bottom:1px solid rgba(59,130,246,.12);margin-bottom:18px">
        <div style="width:34px;height:34px;border-radius:9px;background:linear-gradient(135deg,#1d4ed8,#06b6d4);display:flex;align-items:center;justify-content:center;font-size:16px">⚡</div>
        <div>
            <div style="font-weight:800;font-size:14px;color:#f1f5f9;line-height:1">Shopee Intel</div>
            <div style="font-size:9px;color:#1e3a5f;text-transform:uppercase;letter-spacing:.06em">Commerce Dashboard</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    view = st.selectbox(
        "Analysis View",
        ["📊 Overview", "📅 MoM Analysis", "📆 Weekly Analysis", "📣 Campaigns", "📍 Geography"],
        label_visibility="collapsed"
    )

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<div style="font-size:10px;color:#334155;text-transform:uppercase;letter-spacing:.07em;font-weight:700;margin-bottom:10px">Filters</div>', unsafe_allow_html=True)

    if "Overview" in view or "MoM" in view:
        month_filter = st.selectbox("Month", ["All Months"] + list(monthly_data["ym"]))
    else:
        month_filter = "All Months"

    if "Campaigns" in view:
        camp_filter = st.selectbox("Campaign", ["All Campaigns"] + list(campaigns_data["name"]))
    else:
        camp_filter = "All Campaigns"

    if "Geography" in view:
        city_filter = st.selectbox("City", ["All Cities"] + list(cities_data["name"]))
    else:
        city_filter = "All Cities"

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:10px;color:#334155;text-transform:uppercase;letter-spacing:.07em;font-weight:700;margin-bottom:8px">Data</div>
    """, unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload CSV/Excel", type=["csv","xlsx","xls"], label_visibility="collapsed")
    if uploaded_file:
        st.success(f"✓ {uploaded_file.name}")

    st.markdown("""
    <div style="margin-top:24px;font-size:10px;color:#1e3a5f;text-align:center">
    Shopee Commerce Intelligence<br>Powered by Claude AI
    </div>
    """, unsafe_allow_html=True)

# ── Filtered data ─────────────────────────────────────────────────────────────
filt_monthly = monthly_data if month_filter == "All Months" else monthly_data[monthly_data["ym"] == month_filter]
filt_camps   = campaigns_data if camp_filter == "All Campaigns" else campaigns_data[campaigns_data["name"] == camp_filter]
filt_cities  = cities_data if city_filter == "All Cities" else cities_data[cities_data["name"] == city_filter]
tot_rev  = filt_monthly["revenue"].sum()
tot_ord  = filt_monthly["orders"].sum()

# ═══════════════════════════════════════════════════════════════════════════════
# OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════
if "Overview" in view:
    st.markdown('<div class="section-header">📊 Overview</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Shopee Singapore · Oct 2025 – Jan 2026 · 800 orders</div>', unsafe_allow_html=True)

    # KPI Row 1
    c1, c2, c3, c4 = st.columns(4)
    last = monthly_data.iloc[-1]
    for col, icon, label, val, sub, color, pct in [
        (c1,"💰","Total Revenue",   fmt_s(tot_rev),     f"{tot_ord} orders",       C["blue"],   last["rev_mom"]),
        (c2,"🧾","Avg Order Value", f"S${round(tot_rev/tot_ord) if tot_ord else 0}","Revenue ÷ Orders",  C["cyan"],   last["aov_mom"]),
        (c3,"👤","Rev / Customer",  fmt_s(SUMMARY["revPerCust"]), "Total ÷ customers",   C["violet"], None),
        (c4,"🔁","Repeat Purchase", f"{SUMMARY['repeatRate']}%", "Bought 2× or more",  C["purple"], None),
    ]:
        with col:
            badge = badge_html(pct) if pct is not None else ""
            st.markdown(f"""
            <div class="kpi-card">
                <div style="font-size:20px;margin-bottom:8px">{icon}</div>
                <div class="kpi-val" style="color:{color}">{val}</div>
                <div class="kpi-label">{label}</div>
                <div class="kpi-sub">{sub} {badge}</div>
            </div>""", unsafe_allow_html=True)

    # KPI Row 2
    c1, c2, c3, c4 = st.columns(4)
    for col, icon, label, val, sub, hint, color in [
        (c1,"🚚","Avg Delivery",    f"{SUMMARY['avgDelivery']}d",      "Order → doorstep",          "Target < 2d",    C["green"]),
        (c2,"⭐","Store Rating",     f"{SUMMARY['avgRating']}★",        "Avg across all orders",     "Target 4.8+",    C["amber"]),
        (c3,"🎫","Voucher Usage",    f"{SUMMARY['voucherRate']}%",      f"S${SUMMARY['voucherDiscount']} discounted","48.75% redeem",  C["amber"]),
        (c4,"📊","Discount Leakage", fmt_s(SUMMARY['gross']-SUMMARY['totalRev']), f"Gross {fmt_s(SUMMARY['gross'])}", "Voucher cost", C["red"]),
    ]:
        with col:
            st.markdown(f"""
            <div class="kpi-card">
                <div style="font-size:20px;margin-bottom:8px">{icon}</div>
                <div class="kpi-val" style="color:{color};font-size:18px">{val}</div>
                <div class="kpi-label">{label}</div>
                <div class="kpi-sub">{sub}</div>
                <div style="font-size:10px;color:{color};opacity:.7;margin-top:5px">{hint}</div>
            </div>""", unsafe_allow_html=True)

    # Revenue Trend + Category Mix
    col_l, col_r = st.columns([3,2])
    with col_l:
        st.markdown('<div style="font-weight:700;font-size:14px;color:#f1f5f9;margin-bottom:4px">Revenue Trend</div>', unsafe_allow_html=True)
        metric_tab = st.radio("Metric", ["revenue","orders","aov"], horizontal=True, label_visibility="collapsed")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=filt_monthly["ym"], y=filt_monthly[metric_tab],
            mode="lines+markers",
            line=dict(color=C["blue"], width=2.5),
            marker=dict(size=7, color=C["blue"]),
            fill="tozeroy",
            fillcolor="rgba(59,130,246,0.1)",
            name=metric_tab.upper(),
        ))
        fig.update_layout(**PLOTLY_LAYOUT, height=220)
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.markdown('<div style="font-weight:700;font-size:14px;color:#f1f5f9;margin-bottom:4px">Category Mix</div>', unsafe_allow_html=True)
        st.caption("Revenue share — S$353.9K total")
        fig2 = go.Figure(go.Pie(
            labels=categories_data["name"], values=categories_data["revenue"],
            marker_colors=categories_data["color"].tolist(),
            hole=0.55, textinfo="label+percent", textfont_size=11,
        ))
        fig2.update_layout(**PLOTLY_LAYOUT, height=220)
        st.plotly_chart(fig2, use_container_width=True)

    # DoW + Brands + Payments
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div style="font-weight:700;font-size:13px;color:#f1f5f9;margin-bottom:4px">Best Day to Sell</div>', unsafe_allow_html=True)
        colors_dow = [C["blue"] if d == "Wed" else "rgba(59,130,246,0.28)" for d in dow_data["day"]]
        fig3 = go.Figure(go.Bar(x=dow_data["day"], y=dow_data["revenue"], marker_color=colors_dow, marker_line_width=0))
        fig3.update_layout(**PLOTLY_LAYOUT, height=160)
        st.plotly_chart(fig3, use_container_width=True)
        c_b, c_w = st.columns(2)
        c_b.markdown('<div style="background:rgba(59,130,246,.08);border:1px solid rgba(59,130,246,.15);border-radius:8px;padding:8px;text-align:center"><div style="font-size:9px;color:#3b82f6;font-weight:700">🏆 Best</div><div style="font-size:12px;font-weight:800;color:#f1f5f9">Wednesday</div><div style="font-size:10px;color:#475569">S$62,817</div></div>', unsafe_allow_html=True)
        c_w.markdown('<div style="background:rgba(248,113,113,.06);border:1px solid rgba(248,113,113,.15);border-radius:8px;padding:8px;text-align:center"><div style="font-size:9px;color:#f87171;font-weight:700">↓ Weakest</div><div style="font-size:12px;font-weight:800;color:#f1f5f9">Thursday</div><div style="font-size:10px;color:#475569">S$41,193</div></div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div style="font-weight:700;font-size:13px;color:#f1f5f9;margin-bottom:10px">Top Brands</div>', unsafe_allow_html=True)
        for i, row in brands_data.iterrows():
            pct_bar = int((row["revenue"] / 227248) * 100)
            label = f"{row['name']} {'🏆' if i==0 else ''}"
            st.markdown(f"""
            <div style="margin-bottom:9px">
                <div style="display:flex;justify-content:space-between;margin-bottom:3px">
                    <span style="font-size:11px;color:#94a3b8;font-weight:{'700' if i==0 else '400'}">{label}</span>
                    <span style="font-family:monospace;font-size:11px;color:{row['color']};font-weight:700">{fmt_s(row['revenue'])}</span>
                </div>
                <div style="height:5px;background:rgba(255,255,255,.05);border-radius:3px">
                    <div style="height:100%;width:{pct_bar}%;background:{row['color']};border-radius:3px"></div>
                </div>
            </div>""", unsafe_allow_html=True)

    with c3:
        st.markdown('<div style="font-weight:700;font-size:13px;color:#f1f5f9;margin-bottom:10px">Payment Split</div>', unsafe_allow_html=True)
        total = 353977
        for _, row in payments_data.iterrows():
            sh = round((row["value"] / total) * 100)
            st.markdown(f"""
            <div style="margin-bottom:10px">
                <div style="display:flex;justify-content:space-between;margin-bottom:3px">
                    <span style="font-size:11px;color:#94a3b8">{row['name']}</span>
                    <span style="font-size:11px;color:{row['color']};font-weight:700">{sh}%</span>
                </div>
                <div style="height:5px;background:rgba(255,255,255,.05);border-radius:3px">
                    <div style="height:100%;width:{sh}%;background:{row['color']};border-radius:3px"></div>
                </div>
                <div style="font-size:10px;color:#334155;margin-top:2px">{fmt_s(row['value'])} · AOV S${round(row['value']/row['orders'])}</div>
            </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# MOM ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════
elif "MoM" in view:
    st.markdown('<div class="section-header">📅 Month-over-Month Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Every metric vs prior month · Oct 2025 – Jan 2026</div>', unsafe_allow_html=True)

    # Table
    st.markdown("**Full MoM Breakdown**")
    display_df = monthly_data.copy()
    display_df["Revenue"] = display_df["revenue"].apply(fmt_s)
    display_df["Rev MoM"] = display_df["rev_mom"].apply(lambda x: f"{'↑' if x>0 else '↓'}{abs(x):.1f}%" if pd.notna(x) else "—")
    display_df["Orders"]  = display_df["orders"]
    display_df["Ord MoM"] = display_df["ord_mom"].apply(lambda x: f"{'↑' if x>0 else '↓'}{abs(x):.1f}%" if pd.notna(x) else "—")
    display_df["AOV"]     = display_df["aov"].apply(lambda x: f"S${x}")
    display_df["AOV MoM"] = display_df["aov_mom"].apply(lambda x: f"{'↑' if x>0 else '↓'}{abs(x):.1f}%" if pd.notna(x) else "—")
    display_df["Voucher%"]   = display_df["voucher_rate"].apply(lambda x: f"{x}%")
    display_df["Delivery"] = display_df["avg_delivery"].apply(lambda x: f"{x}d")
    display_df["Rating"]   = display_df["avg_rating"].apply(lambda x: f"{x}★")
    st.dataframe(
        display_df[["ym","Revenue","Rev MoM","Orders","Ord MoM","AOV","AOV MoM","Voucher%","Delivery","Rating"]].rename(columns={"ym":"Month"}),
        use_container_width=True, hide_index=True
    )

    # MoM bar charts
    c1, c2 = st.columns(2)
    for col, key, label, color in [
        (c1, "rev_mom",  "Revenue MoM %",   C["blue"]),
        (c2, "ord_mom",  "Orders MoM %",    C["cyan"]),
    ]:
        with col:
            st.markdown(f'<div style="font-weight:700;font-size:13px;color:#f1f5f9;margin-bottom:8px">{label}</div>', unsafe_allow_html=True)
            sub = monthly_data.dropna(subset=[key])
            bar_colors = [color if v >= 0 else C["red"] for v in sub[key]]
            fig = go.Figure(go.Bar(x=sub["month"], y=sub[key], marker_color=bar_colors, marker_line_width=0))
            fig.add_hline(y=0, line_color="rgba(255,255,255,0.08)")
            fig.update_layout(**PLOTLY_LAYOUT, height=160)
            st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)
    for col, key, label, color in [
        (c1, "aov_mom",  "AOV MoM %",       C["violet"]),
        (c2, "cust_mom", "Customers MoM %", C["purple"]),
    ]:
        with col:
            st.markdown(f'<div style="font-weight:700;font-size:13px;color:#f1f5f9;margin-bottom:8px">{label}</div>', unsafe_allow_html=True)
            sub = monthly_data.dropna(subset=[key])
            bar_colors = [color if v >= 0 else C["red"] for v in sub[key]]
            fig = go.Figure(go.Bar(x=sub["month"], y=sub[key], marker_color=bar_colors, marker_line_width=0))
            fig.add_hline(y=0, line_color="rgba(255,255,255,0.08)")
            fig.update_layout(**PLOTLY_LAYOUT, height=160)
            st.plotly_chart(fig, use_container_width=True)

    # Insights
    st.markdown("**Key Insights**")
    insights = [
        ("📈","Oct→Nov: AOV Spike",    "Revenue +7.1% despite -7.8% orders. AOV jumped S$65 — Electronics driving higher baskets.",      "pos"),
        ("🎄","Nov→Dec: Stable Peak",  "+2.1% revenue, +1.5% orders. Christmas sustained. AOV S$472 — strongest consistent month.",       "pos"),
        ("📉","Dec→Jan: Sharp Dip",    "-22.3% revenue, -13.2% orders. Post-holiday slowdown. AOV also fell S$49. Q1 recovery needed.",   "neg"),
        ("🎫","Voucher Pattern",        "Nov peaked at 55.2% voucher use. Jan dropped to 44.1% — fewer promos correlate with fewer orders.","neu"),
        ("🚚","Delivery in Peak Weeks", "Christmas weeks (W52–W01) had fastest delivery at 2.8–2.9d. Speed correlates with higher AOV.",   "pos"),
        ("💡","Feb Recovery Plan",      "Re-engage Dec buyers with targeted vouchers. Push Wednesday flash sales. Drive Electronics cross-sells.", "pos"),
    ]
    cols = st.columns(3)
    for i, (icon, title, detail, t) in enumerate(insights):
        bg  = "rgba(59,130,246,.06)"  if t=="pos" else ("rgba(248,113,113,.06)"  if t=="neg" else "rgba(129,140,248,.06)")
        brd = "rgba(59,130,246,.15)"  if t=="pos" else ("rgba(248,113,113,.15)"  if t=="neg" else "rgba(129,140,248,.15)")
        clr = C["blue"] if t=="pos" else (C["red"] if t=="neg" else C["violet"])
        with cols[i % 3]:
            st.markdown(f"""
            <div style="background:{bg};border:1px solid {brd};border-radius:12px;padding:13px 15px;margin-bottom:10px">
                <div style="font-size:12px;font-weight:700;color:{clr};margin-bottom:5px">{icon} {title}</div>
                <div style="font-size:11px;color:#64748b;line-height:1.65">{detail}</div>
            </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# WEEKLY ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════
elif "Weekly" in view:
    st.markdown('<div class="section-header">📆 Weekly Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">18 weeks · Sep 29 2025 – Jan 26 2026 · Week-over-Week</div>', unsafe_allow_html=True)

    metric = st.radio("Metric", ["revenue","orders","aov","voucher_rate"], horizontal=True, label_visibility="collapsed",
                      format_func=lambda x: {"revenue":"Revenue","orders":"Orders","aov":"AOV","voucher_rate":"Voucher%"}[x])

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=weekly_data["wk"], y=weekly_data[metric],
        mode="lines", line=dict(color=C["blue"], width=2),
        fill="tozeroy", fillcolor="rgba(59,130,246,0.08)", name=metric,
    ))
    fig.update_layout(**PLOTLY_LAYOUT, height=220)
    st.plotly_chart(fig, use_container_width=True)

    col_l, col_r = st.columns([3,2])
    with col_l:
        st.markdown("**Week-over-Week Revenue Change (%)**")
        wow = weekly_data.dropna(subset=["rev_wow"])
        bar_colors = [C["blue"] if v >= 0 else C["red"] for v in wow["rev_wow"]]
        fig2 = go.Figure(go.Bar(x=wow["wk"], y=wow["rev_wow"], marker_color=bar_colors, marker_line_width=0))
        fig2.add_hline(y=0, line_color="rgba(255,255,255,0.08)")
        fig2.update_layout(**PLOTLY_LAYOUT, height=200)
        st.plotly_chart(fig2, use_container_width=True)

    with col_r:
        st.markdown("**Last 8 Weeks**")
        last8 = weekly_data.tail(8).copy()
        last8["Revenue"] = last8["revenue"].apply(fmt_s)
        last8["WoW"] = last8["rev_wow"].apply(lambda x: f"{'↑' if x>0 else '↓'}{abs(x):.1f}%" if pd.notna(x) else "—")
        last8["AOV"] = last8["aov"].apply(lambda x: f"S${x}")
        st.dataframe(last8[["wk","Revenue","WoW","orders","AOV"]].rename(columns={"wk":"Week","orders":"Orders"}),
                     use_container_width=True, hide_index=True, height=230)

    st.markdown("**Weekly Records**")
    c1,c2,c3,c4 = st.columns(4)
    for col, icon, label, val, sub, color in [
        (c1,"🏆","Peak Week",    "W52 Dec 22","S$33,554 · Christmas",    C["blue"]),
        (c2,"📦","Most Orders",  "W43 Oct 20","62 orders",                C["cyan"]),
        (c3,"💎","Best AOV",     "W05 Jan 26","S$738 avg basket",         C["violet"]),
        (c4,"🎫","Peak Vouchers","W47 Nov 17","64.3% redemption",         C["amber"]),
    ]:
        with col:
            st.markdown(f"""
            <div class="kpi-card" style="text-align:center">
                <div style="font-size:20px;margin-bottom:6px">{icon}</div>
                <div style="font-size:9px;color:#475569;text-transform:uppercase;letter-spacing:.05em">{label}</div>
                <div style="font-family:monospace;font-size:13px;font-weight:700;color:{color};margin:5px 0 3px">{val}</div>
                <div style="font-size:10px;color:#334155">{sub}</div>
            </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# CAMPAIGNS
# ═══════════════════════════════════════════════════════════════════════════════
elif "Campaigns" in view:
    st.markdown('<div class="section-header">📣 Campaigns & Channels</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Campaign performance · payment channels · device split · voucher analysis</div>', unsafe_allow_html=True)

    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("**Campaign Revenue**")
        fig = go.Figure(go.Bar(
            x=filt_camps["name"], y=filt_camps["revenue"],
            marker_color=filt_camps["color"].tolist(), marker_line_width=0,
        ))
        fig.update_layout(**PLOTLY_LAYOUT, height=220)
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.markdown("**Campaign AOV Efficiency**")
        st.caption("Higher = better basket quality")
        max_aov = (campaigns_data["revenue"] / campaigns_data["orders"]).max()
        for _, row in filt_camps.iterrows():
            aov = round(row["revenue"] / row["orders"])
            pct = int((aov / max_aov) * 100)
            st.markdown(f"""
            <div style="margin-bottom:12px">
                <div style="display:flex;justify-content:space-between;margin-bottom:4px">
                    <span style="font-size:12px;color:#94a3b8;font-weight:600">{row['name']}</span>
                    <div style="display:flex;gap:10px">
                        <span style="font-size:10px;color:#475569">{row['orders']} orders</span>
                        <span style="font-family:monospace;font-size:11px;color:{row['color']};font-weight:700">S${aov}</span>
                    </div>
                </div>
                <div style="height:6px;background:rgba(255,255,255,.05);border-radius:3px">
                    <div style="height:100%;width:{pct}%;background:{row['color']};border-radius:3px"></div>
                </div>
            </div>""", unsafe_allow_html=True)

    # Voucher impact
    st.markdown("**Voucher Impact**")
    vc1,vc2,vc3,vc4,vc5 = st.columns(5)
    for col, label, val, sub, color in [
        (vc1,"Orders w/ Voucher","390 / 800","48.75% rate",         C["amber"]),
        (vc2,"Avg Discount",     "S$10",     "per voucher",          C["blue"]),
        (vc3,"Total Discount",   "S$3,890",  "from gross",           C["red"]),
        (vc4,"Gross Revenue",    "S$357,867","before disc",          C["cyan"]),
        (vc5,"Net Revenue",      "S$353,977","after disc",           C["green"]),
    ]:
        with col:
            st.markdown(f"""
            <div style="background:rgba(255,255,255,.02);border:1px solid rgba(59,130,246,.07);border-radius:12px;padding:13px;text-align:center;margin-bottom:10px">
                <div style="font-family:monospace;font-size:14px;font-weight:700;color:{color}">{val}</div>
                <div style="font-size:10px;color:#94a3b8;margin-top:5px;font-weight:600">{label}</div>
                <div style="font-size:10px;color:#334155;margin-top:3px">{sub}</div>
            </div>""", unsafe_allow_html=True)

    col_l, col_r = st.columns([1,2])
    with col_l:
        st.markdown("**Device Split**")
        for i, (name, rev, orders, pct, c) in enumerate([
            ("Desktop", 183998, 422, 52, C["blue"]),
            ("Mobile",  169979, 378, 48, C["cyan"]),
        ]):
            st.markdown(f"""
            <div style="margin-bottom:14px">
                <div style="display:flex;justify-content:space-between;margin-bottom:4px">
                    <span style="font-size:12px;color:#94a3b8">{name}</span>
                    <span style="font-family:monospace;font-size:12px;color:{c};font-weight:700">{fmt_s(rev)}</span>
                </div>
                <div style="height:9px;background:rgba(255,255,255,.05);border-radius:5px">
                    <div style="height:100%;width:{pct}%;background:{c};border-radius:5px"></div>
                </div>
                <div style="font-size:10px;color:#475569;margin-top:3px">{pct}% · {orders} orders · AOV S${round(rev/orders)}</div>
            </div>""", unsafe_allow_html=True)
        st.info("💡 Mobile only 4% behind — audit UX to close gap.")

    with col_r:
        st.markdown("**Monthly Voucher Rate Trend**")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=monthly_data["month"], y=monthly_data["voucher_rate"],
            mode="lines+markers", line=dict(color=C["amber"], width=2.5),
            marker=dict(size=7, color=C["amber"]),
        ))
        fig.add_hline(y=48.75, line_dash="dash", line_color="#334155",
                      annotation_text="Avg 48.75%", annotation_font_color="#475569")
        fig.update_layout(**PLOTLY_LAYOUT, height=220, yaxis_range=[35,65])
        st.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# GEOGRAPHY
# ═══════════════════════════════════════════════════════════════════════════════
elif "Geography" in view:
    st.markdown('<div class="section-header">📍 Geographic Performance</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Revenue, orders & AOV across Singapore districts</div>', unsafe_allow_html=True)

    col_l, col_r = st.columns([3,2])
    with col_l:
        st.markdown("**Revenue by District**")
        bar_colors = []
        for i in range(len(filt_cities)):
            if i == 0: bar_colors.append(C["blue"])
            elif i == len(filt_cities)-1: bar_colors.append(C["red"])
            else: bar_colors.append(f"rgba(59,130,246,{0.85-i*0.1})")
        fig = go.Figure(go.Bar(
            y=filt_cities["name"], x=filt_cities["revenue"],
            orientation="h", marker_color=bar_colors, marker_line_width=0,
        ))
        fig.update_layout(**PLOTLY_LAYOUT, height=260, xaxis_tickprefix="$", xaxis_tickformat=".0s")
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.markdown("**City Rankings**")
        for i, row in filt_cities.reset_index(drop=True).iterrows():
            num_color = C["blue"] if i==0 else (C["red"] if i==len(filt_cities)-1 else "#475569")
            rev_color = C["blue"] if i==0 else (C["red"] if i==len(filt_cities)-1 else "#94a3b8")
            aov = round(row["revenue"]/row["orders"])
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:11px">
                <div style="width:22px;height:22px;border-radius:7px;background:rgba(255,255,255,.03);display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:800;color:{num_color};flex-shrink:0">{i+1}</div>
                <div style="flex:1">
                    <div style="display:flex;justify-content:space-between">
                        <span style="font-size:12px;font-weight:600;color:#e2e8f0">{row['name']}</span>
                        <span style="font-family:monospace;font-size:12px;color:{rev_color}">{fmt_s(row['revenue'])}</span>
                    </div>
                    <div style="font-size:10px;color:#334155;margin-top:1px">{row['orders']} orders · AOV S${aov}</div>
                </div>
            </div>""", unsafe_allow_html=True)
        st.error("🚨 Jurong -35% below Woodlands. Test geo-targeted promo to assess demand.")

    st.markdown("**Revenue vs Orders by City**")
    fig2 = make_subplots(specs=[[{"secondary_y": True}]])
    fig2.add_trace(go.Bar(x=filt_cities["name"], y=filt_cities["revenue"], name="Revenue SGD",
                          marker_color=C["blue"], opacity=0.8, marker_line_width=0), secondary_y=False)
    fig2.add_trace(go.Bar(x=filt_cities["name"], y=filt_cities["orders"], name="Orders",
                          marker_color=C["cyan"], opacity=0.6, marker_line_width=0), secondary_y=True)
    fig2.update_layout(**PLOTLY_LAYOUT, height=200, showlegend=True,
                       legend=dict(font=dict(color="#64748b",size=10), bgcolor="rgba(0,0,0,0)"))
    st.plotly_chart(fig2, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# AI CHAT (bottom of every page)
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 🤖 AI Analyst")
st.caption("Ask anything about your Shopee data")

QUICK_QS = [
    "What's causing the Jan revenue dip?",
    "Which campaign has the best ROI?",
    "Top 3 growth opportunities?",
    "Best day to run flash sales?",
    "Why is Jurong underperforming?",
    "How to improve the 3.6% repeat rate?",
]

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role":"assistant","content":"👋 Hi! I'm your Shopee analyst. Ask me anything about your data — revenue dips, campaign ROI, city gaps…"}
    ]

# Quick question chips
st.markdown("**Quick questions:**")
cols = st.columns(3)
for i, q in enumerate(QUICK_QS):
    if cols[i%3].button(q, key=f"quick_{i}"):
        st.session_state.chat_history.append({"role":"user","content":q})
        st.session_state._pending_prompt = q

# Chat display
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Input
prompt = st.chat_input("Ask about your Shopee data…")
if not prompt and hasattr(st.session_state, "_pending_prompt"):
    prompt = st.session_state._pending_prompt
    del st.session_state._pending_prompt

if prompt:
    if prompt not in [m["content"] for m in st.session_state.chat_history if m["role"]=="user"]:
        st.session_state.chat_history.append({"role":"user","content":prompt})
        with st.chat_message("user"):
            st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analysing…"):
            try:
                key = st.secrets.get("ANTHROPIC_API_KEY", os.environ.get("ANTHROPIC_API_KEY", ""))
                if not key:
                    reply = "⚠️ ANTHROPIC_API_KEY not found. Please add it in Streamlit Cloud → Settings → Secrets."
                else:
                    client = anthropic.Anthropic(api_key=key)
                    history = [{"role":m["role"],"content":m["content"]}
                               for m in st.session_state.chat_history[1:]
                               if m["role"] in ("user","assistant")]
                    response = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=600,
                        system=f"You are a sharp Shopee Singapore e-commerce analyst in a live dashboard. Be concise — max 4 sentences. Use exact numbers. Give 1 clear action at the end. Data:\n{AI_CTX}",
                        messages=history,
                    )
                    reply = response.content[0].text
            except Exception as e:
                reply = f"Error: {str(e)}"

        st.write(reply)
        st.session_state.chat_history.append({"role":"assistant","content":reply})
