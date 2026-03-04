import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import os
import requests
import time

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Shopee Commerce Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── API Key ───────────────────────────────────────────────────────────────────
def get_api_key():
    try:
        key = st.secrets["GEMINI_API_KEY"]
        if key and str(key).startswith("AIza"):
            return str(key)
    except Exception:
        pass
    return os.environ.get("GEMINI_API_KEY", "")

# ── Gemini call with auto-retry on 429 ───────────────────────────────────────
def call_gemini(api_key, history, system_prompt, retries=3):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    contents = []
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})
    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": contents,
        "generationConfig": {"maxOutputTokens": 500, "temperature": 0.7},
    }
    for attempt in range(retries):
        resp = requests.post(url, json=payload, timeout=30)
        if resp.status_code == 429:
            wait = 2 ** attempt * 5   # 5s, 10s, 20s
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    return "⏳ Gemini is busy right now (rate limit). Please wait 30 seconds and try again."

# ── Colors ────────────────────────────────────────────────────────────────────
C = {
    "blue":   "#2563eb", "cyan":   "#0891b2",
    "violet": "#7c3aed", "purple": "#9333ea",
    "green":  "#16a34a", "amber":  "#d97706",
    "red":    "#dc2626", "orange": "#ea580c",
}

# ── Cached data loader ────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    monthly = pd.DataFrame([
        {"ym":"Oct 2025","month":"Oct","revenue":88216, "orders":218,"aov":405,"customers":217,"voucher_rate":50.0,"avg_delivery":3.1,"avg_rating":4.67},
        {"ym":"Nov 2025","month":"Nov","revenue":94439, "orders":201,"aov":470,"customers":199,"voucher_rate":55.2,"avg_delivery":3.1,"avg_rating":4.64},
        {"ym":"Dec 2025","month":"Dec","revenue":96386, "orders":204,"aov":472,"customers":203,"voucher_rate":45.1,"avg_delivery":3.1,"avg_rating":4.64},
        {"ym":"Jan 2026","month":"Jan","revenue":74936, "orders":177,"aov":423,"customers":176,"voucher_rate":44.1,"avg_delivery":3.0,"avg_rating":4.64},
    ])
    monthly["rev_mom"]  = monthly["revenue"].pct_change()*100
    monthly["ord_mom"]  = monthly["orders"].pct_change()*100
    monthly["aov_mom"]  = monthly["aov"].pct_change()*100
    monthly["cust_mom"] = monthly["customers"].pct_change()*100

    weekly = pd.DataFrame([
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
    weekly["rev_wow"] = weekly["revenue"].pct_change()*100

    categories = pd.DataFrame([
        {"name":"Electronics",  "revenue":251955,"orders":324,"color":C["blue"]},
        {"name":"Home & Living","revenue":67817, "orders":164,"color":C["cyan"]},
        {"name":"Fashion",      "revenue":26834, "orders":147,"color":C["violet"]},
        {"name":"Beauty",       "revenue":7371,  "orders":165,"color":C["purple"]},
    ])
    campaigns = pd.DataFrame([
        {"name":"Double Day",   "revenue":89029,"orders":172,"color":C["blue"]},
        {"name":"Mega Campaign","revenue":75121,"orders":168,"color":C["cyan"]},
        {"name":"Brand Day",    "revenue":68307,"orders":161,"color":C["violet"]},
        {"name":"Flash Sale",   "revenue":63142,"orders":136,"color":C["purple"]},
    ])
    cities = pd.DataFrame([
        {"name":"Woodlands","revenue":67353,"orders":126},
        {"name":"Tampines", "revenue":62731,"orders":149},
        {"name":"Singapore","revenue":62174,"orders":149},
        {"name":"Punggol",  "revenue":60186,"orders":122},
        {"name":"Yishun",   "revenue":56635,"orders":138},
        {"name":"Jurong",   "revenue":44898,"orders":116},
    ])
    payments = pd.DataFrame([
        {"name":"PayNow",     "value":104497,"orders":212,"color":C["blue"]},
        {"name":"ShopeePay",  "value":92065, "orders":199,"color":C["cyan"]},
        {"name":"SPayLater",  "value":80145, "orders":190,"color":C["violet"]},
        {"name":"Credit Card","value":77270, "orders":199,"color":C["purple"]},
    ])
    brands = pd.DataFrame([
        {"name":"LG",     "revenue":227248,"orders":158,"color":C["blue"]},
        {"name":"Philips","revenue":67817, "orders":164,"color":C["cyan"]},
        {"name":"Nike",   "revenue":26834, "orders":147,"color":C["violet"]},
        {"name":"Anker",  "revenue":24707, "orders":166,"color":C["purple"]},
        {"name":"COSRX",  "revenue":7371,  "orders":165,"color":C["green"]},
    ])
    dow = pd.DataFrame([
        {"day":"Mon","revenue":45507,"orders":105},{"day":"Tue","revenue":47581,"orders":112},
        {"day":"Wed","revenue":62817,"orders":123},{"day":"Thu","revenue":41193,"orders":113},
        {"day":"Fri","revenue":56486,"orders":126},{"day":"Sat","revenue":50653,"orders":111},
        {"day":"Sun","revenue":49740,"orders":110},
    ])
    summary = {"totalRev":353977,"totalOrders":800,"totalCust":772,"repeatRate":3.6,
               "avgDelivery":3.12,"avgRating":4.65,"voucherRate":48.75,"voucherDiscount":3890,
               "revPerCust":458.5,"gross":357867}
    return monthly, weekly, categories, campaigns, cities, payments, brands, dow, summary

monthly_data, weekly_data, categories_data, campaigns_data, cities_data, payments_data, brands_data, dow_data, SUMMARY = load_data()

AI_CTX = """Shopee Singapore data Oct 2025-Jan 2026, 800 orders.
Revenue: Oct S$88,216 > Nov S$94,439(+7.1%) > Dec S$96,386(+2.1%) > Jan S$74,936(-22.3%)
Total S$353,977 | AOV avg S$442 | Repeat rate 3.6% | Delivery 3.1d avg | Rating 4.65 | Voucher 48.75%
Categories: Electronics 71% S$251,955 | Home&Living S$67,817 | Fashion S$26,834 | Beauty S$7,371
Brands: LG 64% S$227,248 | Philips S$67,817 | Nike S$26,834 | Anker S$24,707
Campaigns: Double Day S$89,029 best | Mega S$75,121 | Brand Day S$68,307 | Flash Sale S$63,142
Cities: Woodlands best S$67,353 | Jurong weakest S$44,898 (-35% gap)
Payments: PayNow leads S$104,497 | ShopeePay S$92,065 | Desktop 52% vs Mobile 48%
Weekly peaks: W52 Christmas S$33,554 | W44 S$31,646 | Best AOV W05 S$738
Day of week: Wednesday best S$62,817 | Thursday worst S$41,193
Voucher: 48.75% use vouchers, avg discount S$10, total S$3,890 leakage from S$357,867 gross"""

# ── Helpers ───────────────────────────────────────────────────────────────────
def fmt_s(v):
    return f"S${v/1000:.1f}K" if v >= 1000 else f"S${round(v)}"

def badge(pct):
    if pct is None or pd.isna(pct): return ""
    p = float(pct)
    arrow = "↑" if p>0 else ("↓" if p<0 else "→")
    color = C["green"] if p>0 else (C["red"] if p<0 else "#64748b")
    return f'<span style="color:{color};font-weight:700;font-size:12px">{arrow}{abs(p):.1f}%</span>'

PLOT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#374151", family="Inter, sans-serif", size=11),
    margin=dict(l=0, r=0, t=10, b=0), showlegend=False,
    xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(color="#6b7280", size=10)),
    yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)", zeroline=False, tickfont=dict(color="#6b7280", size=10)),
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"],.stApp{font-family:'Inter',sans-serif!important;background:#f1f5f9!important;color:#1e293b!important}
.block-container{padding:1.5rem 2rem 3rem!important;background:#f1f5f9!important}
section[data-testid="stSidebar"]{background:#fff!important;border-right:1px solid #e2e8f0!important}
section[data-testid="stSidebar"] *{color:#374151!important}
.stSelectbox>div>div{background:#f8fafc!important;border-color:#e2e8f0!important;color:#1e293b!important;border-radius:8px!important}
.stRadio>div{gap:4px!important}
.stButton>button{background:#2563eb!important;color:white!important;border:none!important;border-radius:8px!important;font-weight:600!important;font-size:13px!important}
.stButton>button:hover{background:#1d4ed8!important}
.kpi-card{background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:18px 20px;margin-bottom:10px;box-shadow:0 1px 4px rgba(0,0,0,.05)}
.kpi-val{font-size:22px;font-weight:800;margin-bottom:4px}
.kpi-label{font-size:10px;color:#6b7280;font-weight:700;text-transform:uppercase;letter-spacing:.04em;margin-bottom:3px}
.kpi-sub{font-size:11px;color:#9ca3af}
.section-header{font-size:20px;font-weight:800;color:#0f172a;margin-bottom:4px}
.section-sub{font-size:13px;color:#64748b;margin-bottom:18px}
.chart-card{background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:18px 20px;box-shadow:0 1px 4px rgba(0,0,0,.05);margin-bottom:14px}
.chart-title{font-size:14px;font-weight:700;color:#1e293b;margin-bottom:4px}
.chart-sub{font-size:11px;color:#9ca3af;margin-bottom:10px}
div[data-testid="stChatMessage"]{background:#fff!important;border:1px solid #e2e8f0!important;border-radius:12px!important;margin-bottom:8px!important}
hr{border-color:#e2e8f0!important}
.share-box{background:linear-gradient(135deg,#eff6ff,#f0fdf4);border:1px solid #bfdbfe;border-radius:14px;padding:20px 24px;margin-bottom:20px}
.chat-tip{background:#fffbeb;border:1px solid #fde68a;border-radius:8px;padding:10px 14px;font-size:12px;color:#92400e;margin-bottom:12px}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;padding-bottom:14px;border-bottom:1px solid #e2e8f0;margin-bottom:14px">
        <div style="width:36px;height:36px;border-radius:10px;background:linear-gradient(135deg,#2563eb,#0891b2);display:flex;align-items:center;justify-content:center;font-size:17px">⚡</div>
        <div>
            <div style="font-weight:800;font-size:14px;color:#0f172a">Shopee Intel</div>
            <div style="font-size:10px;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em">Commerce Dashboard</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    view = st.selectbox("View", [
        "📊 Overview", "📅 MoM Analysis", "📆 Weekly Analysis",
        "📣 Campaigns", "📍 Geography", "🤖 AI Analyst"
    ], label_visibility="collapsed")

    st.markdown('<p style="font-size:11px;font-weight:700;color:#9ca3af;text-transform:uppercase;letter-spacing:.06em;margin:14px 0 6px">Filters</p>', unsafe_allow_html=True)

    month_filter = "All Months"
    camp_filter  = "All Campaigns"
    city_filter  = "All Cities"
    if "Overview" in view or "MoM" in view:
        month_filter = st.selectbox("Month", ["All Months"]+list(monthly_data["ym"]))
    if "Campaigns" in view:
        camp_filter = st.selectbox("Campaign", ["All Campaigns"]+list(campaigns_data["name"]))
    if "Geography" in view:
        city_filter = st.selectbox("City", ["All Cities"]+list(cities_data["name"]))

    st.markdown('<p style="font-size:11px;font-weight:700;color:#9ca3af;text-transform:uppercase;letter-spacing:.06em;margin:14px 0 6px">Data Upload</p>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("CSV/Excel", type=["csv","xlsx","xls"], label_visibility="collapsed")
    if uploaded_file:
        st.success(f"✓ {uploaded_file.name}")

    st.markdown('<p style="font-size:11px;font-weight:700;color:#9ca3af;text-transform:uppercase;letter-spacing:.06em;margin:14px 0 6px">AI Status</p>', unsafe_allow_html=True)
    if get_api_key():
        st.success("✅ Gemini AI ready (free)")
    else:
        st.error("❌ Add GEMINI_API_KEY to Secrets")

    st.markdown('<p style="font-size:10px;color:#cbd5e1;text-align:center;margin-top:20px">Shopee Commerce Intelligence<br>Powered by Gemini AI</p>', unsafe_allow_html=True)

# ── Filtered data ─────────────────────────────────────────────────────────────
filt_monthly = monthly_data if month_filter=="All Months" else monthly_data[monthly_data["ym"]==month_filter]
filt_camps   = campaigns_data if camp_filter=="All Campaigns" else campaigns_data[campaigns_data["name"]==camp_filter]
filt_cities  = cities_data if city_filter=="All Cities" else cities_data[cities_data["name"]==city_filter]
tot_rev = filt_monthly["revenue"].sum()
tot_ord = filt_monthly["orders"].sum()

# ═══════════════════════════════════════════════════════════════════════════════
# OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════
if "Overview" in view:
    st.markdown('<div class="section-header">📊 Overview</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Shopee Singapore · Oct 2025 – Jan 2026 · 800 orders</div>', unsafe_allow_html=True)

    last = monthly_data.iloc[-1]
    c1,c2,c3,c4 = st.columns(4)
    for col,icon,label,val,sub,color,pct in [
        (c1,"💰","Total Revenue",   fmt_s(tot_rev),      f"{tot_ord} orders",     C["blue"],  last["rev_mom"]),
        (c2,"🧾","Avg Order Value", f"S${round(tot_rev/tot_ord) if tot_ord else 0}","Revenue ÷ Orders",C["cyan"],  last["aov_mom"]),
        (c3,"👤","Rev / Customer",  fmt_s(SUMMARY["revPerCust"]),"Total ÷ customers",  C["violet"],None),
        (c4,"🔁","Repeat Purchase", f"{SUMMARY['repeatRate']}%", "Bought 2× or more", C["purple"],None),
    ]:
        with col:
            b = badge(pct) if pct is not None else ""
            st.markdown(f"""<div class="kpi-card">
                <div style="font-size:22px;margin-bottom:8px">{icon}</div>
                <div class="kpi-val" style="color:{color}">{val}</div>
                <div class="kpi-label">{label}</div>
                <div class="kpi-sub">{sub} {b}</div>
            </div>""", unsafe_allow_html=True)

    c1,c2,c3,c4 = st.columns(4)
    for col,icon,label,val,sub,hint,color in [
        (c1,"🚚","Avg Delivery",    f"{SUMMARY['avgDelivery']}d",   "Order → doorstep",        "Target < 2d",   C["cyan"]),
        (c2,"⭐","Store Rating",    f"{SUMMARY['avgRating']}★",      "Avg across all orders",   "Target 4.8+",   C["amber"]),
        (c3,"🎫","Voucher Usage",   f"{SUMMARY['voucherRate']}%",   f"S${SUMMARY['voucherDiscount']} discounted","48.75% redeem",C["orange"]),
        (c4,"📉","Discount Leakage",fmt_s(SUMMARY['gross']-SUMMARY['totalRev']),f"Gross {fmt_s(SUMMARY['gross'])}","Voucher cost",C["red"]),
    ]:
        with col:
            st.markdown(f"""<div class="kpi-card">
                <div style="font-size:22px;margin-bottom:8px">{icon}</div>
                <div class="kpi-val" style="color:{color};font-size:19px">{val}</div>
                <div class="kpi-label">{label}</div>
                <div class="kpi-sub">{sub}</div>
                <div style="font-size:10px;color:{color};margin-top:5px;font-weight:600">{hint}</div>
            </div>""", unsafe_allow_html=True)

    col_l, col_r = st.columns([3,2])
    with col_l:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">Revenue Trend</div>', unsafe_allow_html=True)
        mkey = st.radio("m", ["revenue","orders","aov"], horizontal=True, label_visibility="collapsed",
                        format_func=lambda x: {"revenue":"Revenue","orders":"Orders","aov":"AOV"}[x])
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=filt_monthly["ym"], y=filt_monthly[mkey],
            mode="lines+markers", line=dict(color=C["blue"],width=2.5),
            marker=dict(size=7,color=C["blue"]),
            fill="tozeroy", fillcolor="rgba(37,99,235,0.08)"))
        fig.update_layout(**PLOT, height=200)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">Category Mix</div><div class="chart-sub">Revenue share</div>', unsafe_allow_html=True)
        fig2 = go.Figure(go.Pie(
            labels=categories_data["name"], values=categories_data["revenue"],
            marker_colors=categories_data["color"].tolist(),
            hole=0.55, textinfo="label+percent", textfont_size=11, textfont_color="#374151",
        ))
        fig2.update_layout(**PLOT, height=175)
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar":False})
        st.markdown('</div>', unsafe_allow_html=True)

    c1,c2,c3 = st.columns(3)
    with c1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">Best Day to Sell</div><div class="chart-sub">Revenue by day of week</div>', unsafe_allow_html=True)
        colors_dow = [C["blue"] if d=="Wed" else "#bfdbfe" for d in dow_data["day"]]
        fig3 = go.Figure(go.Bar(x=dow_data["day"], y=dow_data["revenue"], marker_color=colors_dow, marker_line_width=0))
        fig3.update_layout(**PLOT, height=130)
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar":False})
        cb,cw = st.columns(2)
        cb.markdown('<div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;padding:8px;text-align:center"><div style="font-size:9px;color:#2563eb;font-weight:700">🏆 Best</div><div style="font-size:12px;font-weight:800;color:#1e293b">Wed</div><div style="font-size:10px;color:#64748b">S$62,817</div></div>', unsafe_allow_html=True)
        cw.markdown('<div style="background:#fef2f2;border:1px solid #fecaca;border-radius:8px;padding:8px;text-align:center"><div style="font-size:9px;color:#dc2626;font-weight:700">↓ Worst</div><div style="font-size:12px;font-weight:800;color:#1e293b">Thu</div><div style="font-size:10px;color:#64748b">S$41,193</div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">Top Brands</div><div class="chart-sub">LG dominates at 64%</div>', unsafe_allow_html=True)
        for i, row in brands_data.iterrows():
            pct_bar = int((row["revenue"]/227248)*100)
            lbl = f"{row['name']} {'🏆' if i==0 else ''}"
            st.markdown(f"""<div style="margin-bottom:9px">
                <div style="display:flex;justify-content:space-between;margin-bottom:3px">
                    <span style="font-size:12px;color:#374151;font-weight:{'700' if i==0 else '400'}">{lbl}</span>
                    <span style="font-size:11px;color:{row['color']};font-weight:700">{fmt_s(row['revenue'])}</span>
                </div>
                <div style="height:6px;background:#f1f5f9;border-radius:3px">
                    <div style="height:100%;width:{pct_bar}%;background:{row['color']};border-radius:3px"></div>
                </div></div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with c3:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">Payment Split</div><div class="chart-sub">By revenue share</div>', unsafe_allow_html=True)
        for _, row in payments_data.iterrows():
            sh = round((row["value"]/353977)*100)
            st.markdown(f"""<div style="margin-bottom:10px">
                <div style="display:flex;justify-content:space-between;margin-bottom:3px">
                    <span style="font-size:11px;color:#374151">{row['name']}</span>
                    <span style="font-size:11px;color:{row['color']};font-weight:700">{sh}%</span>
                </div>
                <div style="height:6px;background:#f1f5f9;border-radius:3px">
                    <div style="height:100%;width:{sh}%;background:{row['color']};border-radius:3px"></div>
                </div>
                <div style="font-size:10px;color:#9ca3af;margin-top:2px">{fmt_s(row['value'])} · AOV S${round(row['value']/row['orders'])}</div>
            </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# MOM
# ═══════════════════════════════════════════════════════════════════════════════
elif "MoM" in view:
    st.markdown('<div class="section-header">📅 Month-over-Month Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Every metric vs prior month · Oct 2025 – Jan 2026</div>', unsafe_allow_html=True)

    st.markdown('<div class="chart-card"><div class="chart-title">Full MoM Breakdown</div>', unsafe_allow_html=True)
    disp = monthly_data.copy()
    disp["Revenue"]  = disp["revenue"].apply(fmt_s)
    disp["Rev MoM"]  = disp["rev_mom"].apply(lambda x: f"{'↑' if x>0 else '↓'}{abs(x):.1f}%" if pd.notna(x) else "—")
    disp["Orders"]   = disp["orders"]
    disp["Ord MoM"]  = disp["ord_mom"].apply(lambda x: f"{'↑' if x>0 else '↓'}{abs(x):.1f}%" if pd.notna(x) else "—")
    disp["AOV"]      = disp["aov"].apply(lambda x: f"S${x}")
    disp["AOV MoM"]  = disp["aov_mom"].apply(lambda x: f"{'↑' if x>0 else '↓'}{abs(x):.1f}%" if pd.notna(x) else "—")
    disp["Voucher%"] = disp["voucher_rate"].apply(lambda x: f"{x}%")
    disp["Delivery"] = disp["avg_delivery"].apply(lambda x: f"{x}d")
    disp["Rating"]   = disp["avg_rating"].apply(lambda x: f"{x}★")
    st.dataframe(disp[["ym","Revenue","Rev MoM","Orders","Ord MoM","AOV","AOV MoM","Voucher%","Delivery","Rating"]].rename(columns={"ym":"Month"}),
                 use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

    for (k1,l1,c1c),(k2,l2,c2c) in [
        (("rev_mom","Revenue MoM %",C["blue"]),("ord_mom","Orders MoM %",C["cyan"])),
        (("aov_mom","AOV MoM %",C["violet"]),("cust_mom","Customers MoM %",C["purple"])),
    ]:
        col1,col2 = st.columns(2)
        for col,key,label,color in [(col1,k1,l1,c1c),(col2,k2,l2,c2c)]:
            with col:
                st.markdown(f'<div class="chart-card"><div class="chart-title">{label}</div>', unsafe_allow_html=True)
                sub = monthly_data.dropna(subset=[key])
                bcolors = [color if v>=0 else C["red"] for v in sub[key]]
                fig = go.Figure(go.Bar(x=sub["month"],y=sub[key],marker_color=bcolors,marker_line_width=0))
                fig.add_hline(y=0, line_color="#e2e8f0")
                fig.update_layout(**PLOT, height=155)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
                st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("**Key Insights**")
    insights = [
        ("📈","Oct→Nov: AOV Spike",   "Revenue +7.1% despite -7.8% fewer orders. AOV jumped S$65 — Electronics driving bigger baskets.","pos"),
        ("🎄","Nov→Dec: Stable Peak", "+2.1% revenue, +1.5% orders. Christmas sustained. AOV S$472 — strongest consistent month.","pos"),
        ("📉","Dec→Jan: Sharp Dip",   "-22.3% revenue, -13.2% orders. Post-holiday slowdown. AOV fell S$49. Q1 recovery needed.","neg"),
        ("🎫","Voucher Pattern",       "Nov peaked at 55.2% voucher use. Jan dropped to 44.1% — fewer promos = fewer orders.","neu"),
        ("🚚","Peak Delivery",         "Christmas weeks W52–W01 had fastest delivery at 2.8–2.9d. Speed correlates with higher AOV.","pos"),
        ("💡","Feb Recovery Plan",     "Re-engage Dec buyers with targeted vouchers. Push Wednesday flash sales. Drive Electronics cross-sells.","pos"),
    ]
    cols = st.columns(3)
    for i,(icon,title,detail,t) in enumerate(insights):
        bg  = "#eff6ff" if t=="pos" else ("#fef2f2" if t=="neg" else "#faf5ff")
        brd = "#bfdbfe" if t=="pos" else ("#fecaca" if t=="neg" else "#e9d5ff")
        clr = C["blue"] if t=="pos" else (C["red"] if t=="neg" else C["violet"])
        with cols[i%3]:
            st.markdown(f"""<div style="background:{bg};border:1px solid {brd};border-radius:10px;padding:13px 15px;margin-bottom:10px">
                <div style="font-size:13px;font-weight:700;color:{clr};margin-bottom:5px">{icon} {title}</div>
                <div style="font-size:12px;color:#374151;line-height:1.6">{detail}</div>
            </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# WEEKLY
# ═══════════════════════════════════════════════════════════════════════════════
elif "Weekly" in view:
    st.markdown('<div class="section-header">📆 Weekly Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">18 weeks · Sep 29 2025 – Jan 26 2026</div>', unsafe_allow_html=True)

    wkey = st.radio("w", ["revenue","orders","aov","voucher_rate"], horizontal=True, label_visibility="collapsed",
                    format_func=lambda x: {"revenue":"Revenue","orders":"Orders","aov":"AOV","voucher_rate":"Voucher%"}[x])

    st.markdown('<div class="chart-card"><div class="chart-title">Weekly Trend</div>', unsafe_allow_html=True)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=weekly_data["wk"], y=weekly_data[wkey],
        mode="lines", line=dict(color=C["blue"],width=2),
        fill="tozeroy", fillcolor="rgba(37,99,235,0.07)"))
    fig.update_layout(**PLOT, height=200)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
    st.markdown('</div>', unsafe_allow_html=True)

    col_l,col_r = st.columns([3,2])
    with col_l:
        st.markdown('<div class="chart-card"><div class="chart-title">Week-over-Week Revenue Change (%)</div>', unsafe_allow_html=True)
        wow = weekly_data.dropna(subset=["rev_wow"])
        bcolors = [C["blue"] if v>=0 else C["red"] for v in wow["rev_wow"]]
        fig2 = go.Figure(go.Bar(x=wow["wk"],y=wow["rev_wow"],marker_color=bcolors,marker_line_width=0))
        fig2.add_hline(y=0, line_color="#e2e8f0")
        fig2.update_layout(**PLOT, height=190)
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar":False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="chart-card"><div class="chart-title">Last 8 Weeks</div>', unsafe_allow_html=True)
        last8 = weekly_data.tail(8).copy()
        last8["Revenue"] = last8["revenue"].apply(fmt_s)
        last8["WoW"]     = last8["rev_wow"].apply(lambda x: f"{'↑' if x>0 else '↓'}{abs(x):.1f}%" if pd.notna(x) else "—")
        last8["AOV"]     = last8["aov"].apply(lambda x: f"S${x}")
        st.dataframe(last8[["wk","Revenue","WoW","orders","AOV"]].rename(columns={"wk":"Week","orders":"Orders"}),
                     use_container_width=True, hide_index=True, height=225)
        st.markdown('</div>', unsafe_allow_html=True)

    c1,c2,c3,c4 = st.columns(4)
    for col,icon,label,val,sub,color in [
        (c1,"🏆","Peak Week",    "W52 Dec 22","S$33,554 · Christmas",C["blue"]),
        (c2,"📦","Most Orders",  "W43 Oct 20","62 orders",           C["cyan"]),
        (c3,"💎","Best AOV",     "W05 Jan 26","S$738 avg basket",    C["violet"]),
        (c4,"🎫","Peak Vouchers","W47 Nov 17","64.3% redemption",    C["amber"]),
    ]:
        with col:
            st.markdown(f"""<div class="kpi-card" style="text-align:center">
                <div style="font-size:22px;margin-bottom:6px">{icon}</div>
                <div style="font-size:9px;color:#9ca3af;text-transform:uppercase;letter-spacing:.05em">{label}</div>
                <div style="font-size:14px;font-weight:800;color:{color};margin:5px 0 3px">{val}</div>
                <div style="font-size:11px;color:#64748b">{sub}</div>
            </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# CAMPAIGNS
# ═══════════════════════════════════════════════════════════════════════════════
elif "Campaigns" in view:
    st.markdown('<div class="section-header">📣 Campaigns & Channels</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Campaign performance · voucher analysis · device split</div>', unsafe_allow_html=True)

    col_l,col_r = st.columns(2)
    with col_l:
        st.markdown('<div class="chart-card"><div class="chart-title">Campaign Revenue</div>', unsafe_allow_html=True)
        fig = go.Figure(go.Bar(x=filt_camps["name"],y=filt_camps["revenue"],
            marker_color=filt_camps["color"].tolist(),marker_line_width=0))
        fig.update_layout(**PLOT, height=210)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="chart-card"><div class="chart-title">Campaign AOV Efficiency</div><div class="chart-sub">Higher = better basket quality</div>', unsafe_allow_html=True)
        max_aov = (campaigns_data["revenue"]/campaigns_data["orders"]).max()
        for _, row in filt_camps.iterrows():
            aov = round(row["revenue"]/row["orders"])
            pct = int((aov/max_aov)*100)
            st.markdown(f"""<div style="margin-bottom:12px">
                <div style="display:flex;justify-content:space-between;margin-bottom:4px">
                    <span style="font-size:12px;color:#374151;font-weight:600">{row['name']}</span>
                    <span style="font-size:11px;color:{row['color']};font-weight:700">S${aov} · {row['orders']} orders</span>
                </div>
                <div style="height:7px;background:#f1f5f9;border-radius:3px">
                    <div style="height:100%;width:{pct}%;background:{row['color']};border-radius:3px"></div>
                </div></div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="chart-card"><div class="chart-title">Voucher Impact</div>', unsafe_allow_html=True)
    vc1,vc2,vc3,vc4,vc5 = st.columns(5)
    for col,label,val,sub,color in [
        (vc1,"Orders w/ Voucher","390 / 800","48.75% rate",  C["amber"]),
        (vc2,"Avg Discount",     "S$10",     "per voucher",   C["blue"]),
        (vc3,"Total Discount",   "S$3,890",  "from gross",    C["red"]),
        (vc4,"Gross Revenue",    "S$357,867","before disc",   C["cyan"]),
        (vc5,"Net Revenue",      "S$353,977","after disc",    C["green"]),
    ]:
        with col:
            st.markdown(f"""<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:13px;text-align:center">
                <div style="font-size:15px;font-weight:800;color:{color}">{val}</div>
                <div style="font-size:10px;color:#374151;margin-top:5px;font-weight:600">{label}</div>
                <div style="font-size:10px;color:#9ca3af;margin-top:3px">{sub}</div>
            </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    col_l,col_r = st.columns([1,2])
    with col_l:
        st.markdown('<div class="chart-card"><div class="chart-title">Device Split</div>', unsafe_allow_html=True)
        for name,rev,orders,pct,c in [("Desktop",183998,422,52,C["blue"]),("Mobile",169979,378,48,C["cyan"])]:
            st.markdown(f"""<div style="margin-bottom:14px">
                <div style="display:flex;justify-content:space-between;margin-bottom:4px">
                    <span style="font-size:12px;color:#374151">{name}</span>
                    <span style="font-size:12px;color:{c};font-weight:700">{fmt_s(rev)}</span>
                </div>
                <div style="height:9px;background:#f1f5f9;border-radius:5px">
                    <div style="height:100%;width:{pct}%;background:{c};border-radius:5px"></div>
                </div>
                <div style="font-size:10px;color:#9ca3af;margin-top:3px">{pct}% · {orders} orders · AOV S${round(rev/orders)}</div>
            </div>""", unsafe_allow_html=True)
        st.info("💡 Mobile only 4% behind desktop — audit UX to close gap.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="chart-card"><div class="chart-title">Monthly Voucher Rate Trend</div>', unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=monthly_data["month"],y=monthly_data["voucher_rate"],
            mode="lines+markers",line=dict(color=C["amber"],width=2.5),marker=dict(size=7,color=C["amber"])))
        fig.add_hline(y=48.75,line_dash="dash",line_color="#d1d5db",
                      annotation_text="Avg 48.75%",annotation_font_color="#9ca3af")
        fig.update_layout(**PLOT, height=210, yaxis_range=[35,65])
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
        st.markdown('</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# GEOGRAPHY
# ═══════════════════════════════════════════════════════════════════════════════
elif "Geography" in view:
    st.markdown('<div class="section-header">📍 Geographic Performance</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Revenue, orders & AOV across Singapore districts</div>', unsafe_allow_html=True)

    col_l,col_r = st.columns([3,2])
    with col_l:
        st.markdown('<div class="chart-card"><div class="chart-title">Revenue by District</div>', unsafe_allow_html=True)
        bar_colors = []
        for i in range(len(filt_cities)):
            if i==0: bar_colors.append(C["blue"])
            elif i==len(filt_cities)-1: bar_colors.append(C["red"])
            else: bar_colors.append(f"rgba(37,99,235,{0.75-i*0.09})")
        fig = go.Figure(go.Bar(y=filt_cities["name"],x=filt_cities["revenue"],
            orientation="h",marker_color=bar_colors,marker_line_width=0))
        fig.update_layout(**PLOT, height=250, xaxis_tickprefix="$", xaxis_tickformat=".0s")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="chart-card"><div class="chart-title">City Rankings</div>', unsafe_allow_html=True)
        for i, row in filt_cities.reset_index(drop=True).iterrows():
            nc = C["blue"] if i==0 else (C["red"] if i==len(filt_cities)-1 else "#9ca3af")
            rc = C["blue"] if i==0 else (C["red"] if i==len(filt_cities)-1 else "#374151")
            aov = round(row["revenue"]/row["orders"])
            st.markdown(f"""<div style="display:flex;align-items:center;gap:10px;margin-bottom:11px">
                <div style="width:24px;height:24px;border-radius:7px;background:#f1f5f9;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:800;color:{nc};flex-shrink:0">{i+1}</div>
                <div style="flex:1">
                    <div style="display:flex;justify-content:space-between">
                        <span style="font-size:12px;font-weight:600;color:#1e293b">{row['name']}</span>
                        <span style="font-size:12px;font-weight:700;color:{rc}">{fmt_s(row['revenue'])}</span>
                    </div>
                    <div style="font-size:10px;color:#9ca3af;margin-top:1px">{row['orders']} orders · AOV S${aov}</div>
                </div>
            </div>""", unsafe_allow_html=True)
        st.error("🚨 Jurong -35% below Woodlands. Test geo-targeted promo.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="chart-card"><div class="chart-title">Revenue vs Orders by City</div>', unsafe_allow_html=True)
    fig2 = make_subplots(specs=[[{"secondary_y":True}]])
    fig2.add_trace(go.Bar(x=filt_cities["name"],y=filt_cities["revenue"],name="Revenue SGD",
                          marker_color=C["blue"],opacity=0.85,marker_line_width=0),secondary_y=False)
    fig2.add_trace(go.Bar(x=filt_cities["name"],y=filt_cities["orders"],name="Orders",
                          marker_color=C["cyan"],opacity=0.7,marker_line_width=0),secondary_y=True)
    fig2.update_layout(**PLOT, height=200, showlegend=True,
                       legend=dict(font=dict(color="#6b7280",size=10),bgcolor="rgba(0,0,0,0)"))
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar":False})
    st.markdown('</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# AI ANALYST — dedicated full page
# ═══════════════════════════════════════════════════════════════════════════════
elif "AI Analyst" in view:
    st.markdown('<div class="section-header">🤖 AI Analyst</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Ask anything about your Shopee data · Powered by Gemini AI (free)</div>', unsafe_allow_html=True)

    # Share box
    st.markdown("""
    <div class="share-box">
        <div style="font-weight:700;font-size:15px;color:#1e293b;margin-bottom:6px">🔗 Share this dashboard</div>
        <div style="font-size:13px;color:#374151;margin-bottom:10px">Your app is publicly accessible. Click <b>Share</b> in the top-right corner of Streamlit to copy your link.</div>
        <div style="background:#fff;border:1px solid #bfdbfe;border-radius:8px;padding:10px 14px;font-family:monospace;font-size:12px;color:#1d4ed8">
            https://ai-commerce-intelligence-fnb7bxjcdyz5fa6tx8mg9z.streamlit.app
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Rate limit tip
    st.markdown("""
    <div class="chat-tip">
        💡 <b>Tip:</b> Gemini free tier allows ~15 requests/min. Wait a few seconds between questions for best results.
        The AI knows all your Shopee data — revenue, campaigns, cities, brands, vouchers and more.
    </div>
    """, unsafe_allow_html=True)

    QUICK_QS = [
        "What's causing the Jan revenue dip?",
        "Which campaign has the best ROI?",
        "Top 3 growth opportunities?",
        "Best day to run flash sales?",
        "Why is Jurong underperforming?",
        "How to improve the 3.6% repeat rate?",
        "How can we reduce voucher leakage?",
        "Which payment method should we promote?",
        "What's our biggest risk next quarter?",
    ]

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {"role":"assistant","content":"👋 Hi! I'm your Shopee analyst. Ask me anything about your data — revenue dips, campaign ROI, city gaps, voucher strategy and more."}
        ]

    # Quick chips — 3 columns
    st.markdown("**Quick questions:**")
    cols = st.columns(3)
    for i, q in enumerate(QUICK_QS):
        if cols[i%3].button(q, key=f"qb_{i}"):
            st.session_state._pending = q

    st.markdown("---")

    # Chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Clear chat button
    if len(st.session_state.chat_history) > 1:
        if st.button("🗑️ Clear chat", key="clear_chat"):
            st.session_state.chat_history = [st.session_state.chat_history[0]]
            st.rerun()

    # Handle prompt
    prompt = st.chat_input("Ask about your Shopee data…")
    if not prompt and hasattr(st.session_state, "_pending"):
        prompt = st.session_state._pending
        del st.session_state._pending

    if prompt:
        last_user = next((m["content"] for m in reversed(st.session_state.chat_history) if m["role"]=="user"), None)
        if prompt != last_user:
            st.session_state.chat_history.append({"role":"user","content":prompt})
            with st.chat_message("user"):
                st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analysing your data…"):
                api_key = get_api_key()
                if not api_key:
                    reply = "⚠️ Gemini API key not found. Add GEMINI_API_KEY to Streamlit Cloud → Settings → Secrets."
                else:
                    try:
                        system_prompt = (
                            "You are a sharp Shopee Singapore e-commerce analyst. "
                            "Be concise — max 4 sentences. Use exact numbers from the data. "
                            "Always end with 1 specific, actionable recommendation.\n\nData:\n" + AI_CTX
                        )
                        history = [
                            {"role": m["role"], "content": m["content"]}
                            for m in st.session_state.chat_history
                            if m["role"] in ("user","assistant")
                        ]
                        reply = call_gemini(api_key, history, system_prompt)
                    except requests.exceptions.HTTPError as e:
                        code = e.response.status_code
                        if code == 429:
                            reply = "⏳ Rate limit hit — please wait 15 seconds and try again."
                        else:
                            reply = f"❌ API error {code}. Check your Gemini key in Secrets."
                    except Exception as e:
                        reply = f"❌ Error: {str(e)}"

            st.write(reply)
            st.session_state.chat_history.append({"role":"assistant","content":reply})
