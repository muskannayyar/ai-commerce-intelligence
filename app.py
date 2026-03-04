import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import os
import requests
import time
from datetime import date, timedelta

st.set_page_config(page_title="Shopee Commerce Intelligence", page_icon="⚡", layout="wide")

# ── API Key ───────────────────────────────────────────────────────────────────
def get_api_key():
    try:
        k = st.secrets["GEMINI_API_KEY"]
        if k and str(k).startswith("AIza"): return str(k)
    except: pass
    return os.environ.get("GEMINI_API_KEY", "")

GEMINI_MODELS = ["gemini-1.5-flash-8b", "gemini-1.5-flash", "gemini-2.0-flash"]

def call_gemini(api_key, history, system_prompt):
    contents = []
    for m in history:
        role = "user" if m["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": m["content"]}]})
    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": contents,
        "generationConfig": {"maxOutputTokens": 500, "temperature": 0.7},
    }
    for model in GEMINI_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        for attempt in range(2):
            resp = requests.post(url, json=payload, timeout=30)
            if resp.status_code == 429:
                time.sleep(5)
                continue
            if resp.status_code in (400, 404):
                break
            resp.raise_for_status()
            return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    return "⏳ Gemini rate limit reached. Please wait 30 seconds and try again."

# ── Colors ────────────────────────────────────────────────────────────────────
C = {"blue":"#2563eb","cyan":"#0891b2","violet":"#7c3aed","purple":"#9333ea",
     "green":"#16a34a","amber":"#d97706","red":"#dc2626","orange":"#ea580c"}

# ── Singapore Public Holidays & Special Days ──────────────────────────────────
SG_EVENTS = {
    date(2025,10,1):  "🎂 Children's Day",
    date(2025,10,31): "🎃 Halloween",
    date(2025,11,1):  "🛍️ 11.11 Countdown",
    date(2025,11,11): "🛍️ 11.11 Mega Sale",
    date(2025,12,25): "🎄 Christmas",
    date(2025,12,26): "🎁 Boxing Day",
    date(2025,12,31): "🎆 New Year's Eve",
    date(2026,1,1):   "🎉 New Year's Day ✦PH",
    date(2026,1,29):  "🧧 Chinese New Year ✦PH",
    date(2026,1,30):  "🧧 CNY Day 2 ✦PH",
    date(2026,2,14):  "💝 Valentine's Day",
    date(2026,3,8):   "🌸 International Women's Day",
    date(2026,3,28):  "✝️ Good Friday ✦PH",
}

# ── Sample Daily Data (Oct 2025 – Jan 2026) ───────────────────────────────────
@st.cache_data
def generate_daily_data():
    rng = np.random.default_rng(42)
    rows = []
    d = date(2025, 10, 1)
    end = date(2026, 1, 31)
    monthly_targets = {10:88216, 11:94439, 12:96386, 1:74936}
    while d <= end:
        base = monthly_targets[d.month] / 30
        dow_mult = {0:1.05,1:1.08,2:1.35,3:0.9,4:1.2,5:1.1,6:1.06}[d.weekday()]
        event_mult = 1.0
        if d in SG_EVENTS:
            ev = SG_EVENTS[d]
            if "11.11" in ev: event_mult = 2.8
            elif "Christmas" in ev or "Boxing" in ev: event_mult = 1.9
            elif "New Year" in ev and "Eve" not in ev: event_mult = 1.5
            elif "CNY" in ev: event_mult = 1.7
            elif "PH" in ev: event_mult = 1.3
        noise = rng.uniform(0.8, 1.2)
        rev = int(base * dow_mult * event_mult * noise)
        orders = max(1, int(rev / rng.uniform(380, 520)))
        aov = round(rev / orders)
        voucher_pct = round(rng.uniform(40, 60), 1)
        rows.append({
            "date": d,
            "weekday": d.strftime("%a"),
            "revenue": rev,
            "orders": orders,
            "aov": aov,
            "voucher_rate": voucher_pct,
            "event": SG_EVENTS.get(d, ""),
        })
        d += timedelta(days=1)
    df = pd.DataFrame(rows)
    df["rev_dod"] = df["revenue"].pct_change() * 100
    return df

# ── Cached monthly/weekly data ────────────────────────────────────────────────
@st.cache_data
def load_data():
    monthly = pd.DataFrame([
        {"ym":"Oct 2025","month":"Oct","revenue":88216,"orders":218,"aov":405,"customers":217,"voucher_rate":50.0,"avg_delivery":3.1,"avg_rating":4.67},
        {"ym":"Nov 2025","month":"Nov","revenue":94439,"orders":201,"aov":470,"customers":199,"voucher_rate":55.2,"avg_delivery":3.1,"avg_rating":4.64},
        {"ym":"Dec 2025","month":"Dec","revenue":96386,"orders":204,"aov":472,"customers":203,"voucher_rate":45.1,"avg_delivery":3.1,"avg_rating":4.64},
        {"ym":"Jan 2026","month":"Jan","revenue":74936,"orders":177,"aov":423,"customers":176,"voucher_rate":44.1,"avg_delivery":3.0,"avg_rating":4.64},
    ])
    monthly["rev_mom"]  = monthly["revenue"].pct_change()*100
    monthly["ord_mom"]  = monthly["orders"].pct_change()*100
    monthly["aov_mom"]  = monthly["aov"].pct_change()*100
    monthly["cust_mom"] = monthly["customers"].pct_change()*100

    # Forecast Feb 2026 (simple trend + seasonal)
    forecast = pd.DataFrame([{
        "ym":"Feb 2026 (Forecast)","month":"Feb*","revenue":82000,"orders":188,"aov":436,
        "customers":186,"voucher_rate":46.0,"avg_delivery":3.0,"avg_rating":4.65,
        "rev_mom":9.4,"ord_mom":6.2,"aov_mom":3.1,"cust_mom":5.7,"is_forecast":True
    }])
    monthly["is_forecast"] = False
    monthly_all = pd.concat([monthly, forecast], ignore_index=True)

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
        {"name":"Electronics","revenue":251955,"orders":324,"color":C["blue"]},
        {"name":"Home & Living","revenue":67817,"orders":164,"color":C["cyan"]},
        {"name":"Fashion","revenue":26834,"orders":147,"color":C["violet"]},
        {"name":"Beauty","revenue":7371,"orders":165,"color":C["purple"]},
    ])
    campaigns = pd.DataFrame([
        {"name":"Double Day","revenue":89029,"orders":172,"color":C["blue"]},
        {"name":"Mega Campaign","revenue":75121,"orders":168,"color":C["cyan"]},
        {"name":"Brand Day","revenue":68307,"orders":161,"color":C["violet"]},
        {"name":"Flash Sale","revenue":63142,"orders":136,"color":C["purple"]},
    ])
    cities = pd.DataFrame([
        {"name":"Woodlands","revenue":67353,"orders":126},
        {"name":"Tampines","revenue":62731,"orders":149},
        {"name":"Singapore","revenue":62174,"orders":149},
        {"name":"Punggol","revenue":60186,"orders":122},
        {"name":"Yishun","revenue":56635,"orders":138},
        {"name":"Jurong","revenue":44898,"orders":116},
    ])
    payments = pd.DataFrame([
        {"name":"PayNow","value":104497,"orders":212,"color":C["blue"]},
        {"name":"ShopeePay","value":92065,"orders":199,"color":C["cyan"]},
        {"name":"SPayLater","value":80145,"orders":190,"color":C["violet"]},
        {"name":"Credit Card","value":77270,"orders":199,"color":C["purple"]},
    ])
    brands = pd.DataFrame([
        {"name":"LG","revenue":227248,"orders":158,"color":C["blue"]},
        {"name":"Philips","revenue":67817,"orders":164,"color":C["cyan"]},
        {"name":"Nike","revenue":26834,"orders":147,"color":C["violet"]},
        {"name":"Anker","revenue":24707,"orders":166,"color":C["purple"]},
        {"name":"COSRX","revenue":7371,"orders":165,"color":C["green"]},
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
    return monthly_all, weekly, categories, campaigns, cities, payments, brands, dow, summary

monthly_data, weekly_data, categories_data, campaigns_data, cities_data, payments_data, brands_data, dow_data, SUMMARY = load_data()
daily_data = generate_daily_data()

AI_CTX = """Shopee Singapore Oct 2025-Jan 2026, 800 orders.
Revenue: Oct S$88,216 > Nov S$94,439(+7.1%) > Dec S$96,386(+2.1%) > Jan S$74,936(-22.3%). Feb forecast S$82,000(+9.4%).
Total S$353,977 | AOV avg S$442 | Repeat rate 3.6% | Delivery 3.1d | Rating 4.65 | Voucher 48.75%
Electronics 71% S$251,955 | Home&Living S$67,817 | Fashion S$26,834 | Beauty S$7,371
LG 64% S$227,248 | Philips S$67,817 | Nike S$26,834 | Anker S$24,707
Double Day S$89,029 best ROI | Mega S$75,121 | Brand Day S$68,307 | Flash Sale S$63,142
Woodlands best S$67,353 | Jurong weakest S$44,898 (-35%)
PayNow leads S$104,497 | Desktop 52% vs Mobile 48%
Wednesday best day S$62,817 | Thursday worst S$41,193
11.11 sale peak day | Christmas W52 S$33,554 peak week"""

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
    font=dict(color="#374151", family="Inter,sans-serif", size=11),
    margin=dict(l=0,r=0,t=10,b=0), showlegend=False,
    xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(color="#6b7280",size=10)),
    yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)", zeroline=False, tickfont=dict(color="#6b7280",size=10)),
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"],.stApp{font-family:'Inter',sans-serif!important;background:#f1f5f9!important;color:#1e293b!important}
#MainMenu,footer,div[data-testid="stToolbar"],div[data-testid="stDecoration"],header[data-testid="stHeader"]{display:none!important;visibility:hidden!important}
.block-container{padding:1rem 2rem 3rem!important;background:#f1f5f9!important}
section[data-testid="stSidebar"]{background:#fff!important;border-right:1px solid #e2e8f0!important}
section[data-testid="stSidebar"] *{color:#374151!important}
.stSelectbox>div>div{background:#f8fafc!important;border-color:#e2e8f0!important;color:#1e293b!important;border-radius:8px!important}
.stMultiSelect>div>div{background:#f8fafc!important;border-color:#e2e8f0!important;border-radius:8px!important}
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
.forecast-badge{background:#fef3c7;color:#92400e;border:1px solid #fde68a;border-radius:6px;font-size:10px;font-weight:700;padding:2px 7px;margin-left:8px}
.event-pill{background:#eff6ff;color:#1d4ed8;border:1px solid #bfdbfe;border-radius:20px;font-size:10px;font-weight:600;padding:2px 8px;display:inline-block;margin:1px}
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
    </div>""", unsafe_allow_html=True)

    view = st.selectbox("View", [
        "📊 Overview","📅 MoM Analysis","📆 Weekly Analysis",
        "📆 Daily Analysis","📣 Campaigns","📍 Geography","🤖 AI Analyst"
    ], label_visibility="collapsed")

    st.markdown('<p style="font-size:11px;font-weight:700;color:#9ca3af;text-transform:uppercase;letter-spacing:.06em;margin:14px 0 6px">Filters</p>', unsafe_allow_html=True)

    month_filter = "All Months"
    months_compare = []
    camp_filter = "All Campaigns"
    city_filter = "All Cities"
    daily_month_filter = "All"

    all_months = [m for m in monthly_data["ym"].tolist() if "Forecast" not in m]

    if "Overview" in view:
        month_filter = st.selectbox("Month", ["All Months"]+all_months)
    if "MoM" in view:
        months_compare = st.multiselect("Compare months", all_months, default=all_months,
                                        help="Select 2+ months to compare side by side")
        if not months_compare:
            months_compare = all_months
    if "Campaigns" in view:
        camp_filter = st.selectbox("Campaign", ["All Campaigns"]+list(campaigns_data["name"]))
    if "Geography" in view:
        city_filter = st.selectbox("City", ["All Cities"]+list(cities_data["name"]))
    if "Daily" in view:
        daily_month_filter = st.selectbox("Month", ["All","Oct 2025","Nov 2025","Dec 2025","Jan 2026"])

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
actual_monthly = monthly_data[monthly_data["is_forecast"]==False]
filt_monthly = actual_monthly if month_filter=="All Months" else actual_monthly[actual_monthly["ym"]==month_filter]
mom_data = monthly_data[monthly_data["ym"].isin(months_compare + ["Feb 2026 (Forecast)"])]
filt_camps = campaigns_data if camp_filter=="All Campaigns" else campaigns_data[campaigns_data["name"]==camp_filter]
filt_cities = cities_data if city_filter=="All Cities" else cities_data[cities_data["name"]==city_filter]
if daily_month_filter == "All":
    filt_daily = daily_data
else:
    month_map = {"Oct 2025":10,"Nov 2025":11,"Dec 2025":12,"Jan 2026":1}
    filt_daily = daily_data[daily_data["date"].apply(lambda d: d.month==month_map.get(daily_month_filter,0))]

tot_rev = filt_monthly["revenue"].sum()
tot_ord = filt_monthly["orders"].sum()

# ═══════════════════════════════════════════════════════════════════════════════
# OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════
if "Overview" in view:
    st.markdown('<div class="section-header">📊 Overview</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Shopee Singapore · Oct 2025 – Jan 2026 · 800 orders · <span class="forecast-badge">Feb 2026 forecast included</span></div>', unsafe_allow_html=True)

    last = actual_monthly.iloc[-1]
    c1,c2,c3,c4 = st.columns(4)
    for col,icon,label,val,sub,color,pct in [
        (c1,"💰","Total Revenue",fmt_s(tot_rev),f"{tot_ord} orders",C["blue"],last["rev_mom"]),
        (c2,"🧾","Avg Order Value",f"S${round(tot_rev/tot_ord) if tot_ord else 0}","Revenue ÷ Orders",C["cyan"],last["aov_mom"]),
        (c3,"👤","Rev / Customer",fmt_s(SUMMARY["revPerCust"]),"Total ÷ customers",C["violet"],None),
        (c4,"🔁","Repeat Purchase",f"{SUMMARY['repeatRate']}%","Bought 2× or more",C["purple"],None),
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
        (c1,"🚚","Avg Delivery",f"{SUMMARY['avgDelivery']}d","Order → doorstep","Target < 2d",C["cyan"]),
        (c2,"⭐","Store Rating",f"{SUMMARY['avgRating']}★","Avg across orders","Target 4.8+",C["amber"]),
        (c3,"🎫","Voucher Usage",f"{SUMMARY['voucherRate']}%",f"S${SUMMARY['voucherDiscount']} discounted","48.75% redeem",C["orange"]),
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

    # Revenue trend with forecast
    col_l,col_r = st.columns([3,2])
    with col_l:
        st.markdown('<div class="chart-card"><div class="chart-title">Revenue Trend + Feb Forecast</div>', unsafe_allow_html=True)
        mkey = st.radio("m",["revenue","orders","aov"],horizontal=True,label_visibility="collapsed",
                        format_func=lambda x:{"revenue":"Revenue","orders":"Orders","aov":"AOV"}[x])
        actual = monthly_data[monthly_data["is_forecast"]==False]
        forecast = monthly_data[monthly_data["is_forecast"]==True]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=actual["ym"],y=actual[mkey],mode="lines+markers",
            name="Actual",line=dict(color=C["blue"],width=2.5),marker=dict(size=7,color=C["blue"]),
            fill="tozeroy",fillcolor="rgba(37,99,235,0.08)"))
        # connect actual to forecast
        connect_x = [actual["ym"].iloc[-1], forecast["ym"].iloc[0]]
        connect_y = [actual[mkey].iloc[-1], forecast[mkey].iloc[0]]
        fig.add_trace(go.Scatter(x=connect_x,y=connect_y,mode="lines",
            line=dict(color=C["amber"],width=2,dash="dot"),showlegend=False))
        fig.add_trace(go.Scatter(x=forecast["ym"],y=forecast[mkey],mode="markers",
            name="Forecast",marker=dict(size=9,color=C["amber"],symbol="diamond")))
        fig.update_layout(**PLOT,height=210,showlegend=True,
            legend=dict(font=dict(color="#6b7280",size=10),bgcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
        st.markdown('</div>',unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="chart-card"><div class="chart-title">Category Mix</div><div class="chart-sub">Revenue share</div>', unsafe_allow_html=True)
        fig2 = go.Figure(go.Pie(
            labels=categories_data["name"],values=categories_data["revenue"],
            marker_colors=categories_data["color"].tolist(),
            hole=0.55,textinfo="label+percent",textfont_size=11,textfont_color="#374151"))
        fig2.update_layout(**PLOT,height=175)
        st.plotly_chart(fig2,use_container_width=True,config={"displayModeBar":False})
        st.markdown('</div>',unsafe_allow_html=True)

    c1,c2,c3 = st.columns(3)
    with c1:
        st.markdown('<div class="chart-card"><div class="chart-title">Best Day to Sell</div><div class="chart-sub">Revenue by day of week</div>', unsafe_allow_html=True)
        colors_dow = [C["blue"] if d=="Wed" else "#bfdbfe" for d in dow_data["day"]]
        fig3 = go.Figure(go.Bar(x=dow_data["day"],y=dow_data["revenue"],marker_color=colors_dow,marker_line_width=0))
        fig3.update_layout(**PLOT,height=130)
        st.plotly_chart(fig3,use_container_width=True,config={"displayModeBar":False})
        cb,cw = st.columns(2)
        cb.markdown('<div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;padding:8px;text-align:center"><div style="font-size:9px;color:#2563eb;font-weight:700">🏆 Best</div><div style="font-size:12px;font-weight:800;color:#1e293b">Wed</div><div style="font-size:10px;color:#64748b">S$62,817</div></div>',unsafe_allow_html=True)
        cw.markdown('<div style="background:#fef2f2;border:1px solid #fecaca;border-radius:8px;padding:8px;text-align:center"><div style="font-size:9px;color:#dc2626;font-weight:700">↓ Worst</div><div style="font-size:12px;font-weight:800;color:#1e293b">Thu</div><div style="font-size:10px;color:#64748b">S$41,193</div></div>',unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="chart-card"><div class="chart-title">Top Brands</div><div class="chart-sub">LG dominates at 64%</div>', unsafe_allow_html=True)
        for i,row in brands_data.iterrows():
            pct_bar = int((row["revenue"]/227248)*100)
            st.markdown(f"""<div style="margin-bottom:9px">
                <div style="display:flex;justify-content:space-between;margin-bottom:3px">
                    <span style="font-size:12px;color:#374151;font-weight:{'700' if i==0 else '400'}">{row['name']} {'🏆' if i==0 else ''}</span>
                    <span style="font-size:11px;color:{row['color']};font-weight:700">{fmt_s(row['revenue'])}</span>
                </div>
                <div style="height:6px;background:#f1f5f9;border-radius:3px">
                    <div style="height:100%;width:{pct_bar}%;background:{row['color']};border-radius:3px"></div>
                </div></div>""",unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)

    with c3:
        st.markdown('<div class="chart-card"><div class="chart-title">Payment Split</div><div class="chart-sub">By revenue share</div>', unsafe_allow_html=True)
        for _,row in payments_data.iterrows():
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
            </div>""",unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# MOM ANALYSIS — multi-month comparison
# ═══════════════════════════════════════════════════════════════════════════════
elif "MoM" in view:
    st.markdown('<div class="section-header">📅 Month-over-Month Analysis</div>', unsafe_allow_html=True)
    show_forecast = st.toggle("Include Feb 2026 Forecast", value=True)
    compare_data = monthly_data[monthly_data["ym"].isin(months_compare)]
    if show_forecast:
        forecast_row = monthly_data[monthly_data["is_forecast"]==True]
        compare_data = pd.concat([compare_data, forecast_row], ignore_index=True)

    # Summary comparison table
    st.markdown('<div class="chart-card"><div class="chart-title">Month Comparison Table</div>', unsafe_allow_html=True)
    disp = compare_data.copy()
    disp["Revenue"]  = disp["revenue"].apply(fmt_s)
    disp["Rev MoM"]  = disp["rev_mom"].apply(lambda x: f"{'↑' if x>0 else '↓'}{abs(x):.1f}%" if pd.notna(x) else "—")
    disp["Orders"]   = disp["orders"]
    disp["Ord MoM"]  = disp["ord_mom"].apply(lambda x: f"{'↑' if x>0 else '↓'}{abs(x):.1f}%" if pd.notna(x) else "—")
    disp["AOV"]      = disp["aov"].apply(lambda x: f"S${x}")
    disp["Voucher%"] = disp["voucher_rate"].apply(lambda x: f"{x}%")
    disp["Delivery"] = disp["avg_delivery"].apply(lambda x: f"{x}d")
    disp["Rating"]   = disp["avg_rating"].apply(lambda x: f"{x}★")
    disp["Type"]     = disp["is_forecast"].apply(lambda x: "📊 Forecast" if x else "✅ Actual")
    st.dataframe(disp[["ym","Type","Revenue","Rev MoM","Orders","Ord MoM","AOV","Voucher%","Delivery","Rating"]].rename(columns={"ym":"Month"}),
                 use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Side-by-side bar comparison
    metrics = [("revenue","Revenue (S$)",C["blue"]),("orders","Orders",C["cyan"]),
               ("aov","AOV (S$)",C["violet"]),("voucher_rate","Voucher %",C["amber"])]
    for i in range(0,4,2):
        cols = st.columns(2)
        for j,col in enumerate(cols):
            if i+j >= len(metrics): break
            key,label,color = metrics[i+j]
            with col:
                st.markdown(f'<div class="chart-card"><div class="chart-title">{label} by Month</div>', unsafe_allow_html=True)
                colors_bar = [C["amber"] if row["is_forecast"] else color for _,row in compare_data.iterrows()]
                fig = go.Figure(go.Bar(
                    x=compare_data["ym"], y=compare_data[key],
                    marker_color=colors_bar, marker_line_width=0,
                    text=compare_data[key].apply(lambda v: fmt_s(v) if key=="revenue" else f"S${v}" if key=="aov" else f"{v}%{'  📊' if key=='voucher_rate' else ''}"),
                    textposition="outside", textfont=dict(size=11,color="#374151")
                ))
                fig.update_layout(**PLOT, height=200)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
                st.markdown('</div>', unsafe_allow_html=True)

    # MoM change waterfall for revenue
    st.markdown('<div class="chart-card"><div class="chart-title">Revenue MoM % Change</div>', unsafe_allow_html=True)
    sub = compare_data.dropna(subset=["rev_mom"])
    bcolors = [C["amber"] if row["is_forecast"] else (C["blue"] if v>=0 else C["red"]) for v,(_,row) in zip(sub["rev_mom"],sub.iterrows())]
    fig = go.Figure(go.Bar(x=sub["ym"],y=sub["rev_mom"],marker_color=bcolors,marker_line_width=0,
                           text=sub["rev_mom"].apply(lambda v:f"{'↑' if v>0 else '↓'}{abs(v):.1f}%"),
                           textposition="outside",textfont=dict(size=11,color="#374151")))
    fig.add_hline(y=0,line_color="#e2e8f0")
    fig.update_layout(**PLOT,height=180)
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
    if show_forecast:
        st.caption("🟡 Amber = Feb 2026 forecast based on CNY uplift + post-Jan recovery trend")
    st.markdown('</div>',unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# WEEKLY
# ═══════════════════════════════════════════════════════════════════════════════
elif "Weekly" in view and "Daily" not in view:
    st.markdown('<div class="section-header">📆 Weekly Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">18 weeks · Sep 29 2025 – Jan 26 2026</div>', unsafe_allow_html=True)

    wkey = st.radio("w",["revenue","orders","aov","voucher_rate"],horizontal=True,label_visibility="collapsed",
                    format_func=lambda x:{"revenue":"Revenue","orders":"Orders","aov":"AOV","voucher_rate":"Voucher%"}[x])

    st.markdown('<div class="chart-card"><div class="chart-title">Weekly Trend</div>', unsafe_allow_html=True)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=weekly_data["wk"],y=weekly_data[wkey],
        mode="lines",line=dict(color=C["blue"],width=2),fill="tozeroy",fillcolor="rgba(37,99,235,0.07)"))
    fig.update_layout(**PLOT,height=200)
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
    st.markdown('</div>',unsafe_allow_html=True)

    col_l,col_r = st.columns([3,2])
    with col_l:
        st.markdown('<div class="chart-card"><div class="chart-title">Week-over-Week Revenue %</div>', unsafe_allow_html=True)
        wow = weekly_data.dropna(subset=["rev_wow"])
        fig2 = go.Figure(go.Bar(x=wow["wk"],y=wow["rev_wow"],
            marker_color=[C["blue"] if v>=0 else C["red"] for v in wow["rev_wow"]],marker_line_width=0))
        fig2.add_hline(y=0,line_color="#e2e8f0")
        fig2.update_layout(**PLOT,height=190)
        st.plotly_chart(fig2,use_container_width=True,config={"displayModeBar":False})
        st.markdown('</div>',unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="chart-card"><div class="chart-title">Last 8 Weeks</div>', unsafe_allow_html=True)
        last8 = weekly_data.tail(8).copy()
        last8["Revenue"] = last8["revenue"].apply(fmt_s)
        last8["WoW"] = last8["rev_wow"].apply(lambda x: f"{'↑' if x>0 else '↓'}{abs(x):.1f}%" if pd.notna(x) else "—")
        last8["AOV"] = last8["aov"].apply(lambda x: f"S${x}")
        st.dataframe(last8[["wk","Revenue","WoW","orders","AOV"]].rename(columns={"wk":"Week","orders":"Orders"}),
                     use_container_width=True,hide_index=True,height=225)
        st.markdown('</div>',unsafe_allow_html=True)

    c1,c2,c3,c4 = st.columns(4)
    for col,icon,label,val,sub,color in [
        (c1,"🏆","Peak Week","W52 Dec 22","S$33,554 · Christmas",C["blue"]),
        (c2,"📦","Most Orders","W43 Oct 20","62 orders",C["cyan"]),
        (c3,"💎","Best AOV","W05 Jan 26","S$738 avg basket",C["violet"]),
        (c4,"🎫","Peak Vouchers","W47 Nov 17","64.3% redemption",C["amber"]),
    ]:
        with col:
            st.markdown(f"""<div class="kpi-card" style="text-align:center">
                <div style="font-size:22px;margin-bottom:6px">{icon}</div>
                <div style="font-size:9px;color:#9ca3af;text-transform:uppercase;letter-spacing:.05em">{label}</div>
                <div style="font-size:14px;font-weight:800;color:{color};margin:5px 0 3px">{val}</div>
                <div style="font-size:11px;color:#64748b">{sub}</div>
            </div>""",unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# DAILY ANALYSIS — with Singapore events
# ═══════════════════════════════════════════════════════════════════════════════
elif "Daily" in view:
    st.markdown('<div class="section-header">📆 Daily Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Day-by-day revenue · Singapore public holidays & special days highlighted</div>', unsafe_allow_html=True)

    # Daily metric selector
    dkey = st.radio("dk",["revenue","orders","aov","voucher_rate"],horizontal=True,label_visibility="collapsed",
                    format_func=lambda x:{"revenue":"Revenue","orders":"Orders","aov":"AOV","voucher_rate":"Voucher%"}[x])

    # Daily chart with event markers
    st.markdown('<div class="chart-card"><div class="chart-title">Daily Revenue with Singapore Events</div><div class="chart-sub">🔴 Red diamonds = SG public holidays & campaigns</div>', unsafe_allow_html=True)

    filt_daily_sorted = filt_daily.sort_values("date")
    date_strs = filt_daily_sorted["date"].apply(lambda d: d.strftime("%d %b"))

    fig = go.Figure()
    # Base line
    fig.add_trace(go.Scatter(
        x=date_strs, y=filt_daily_sorted[dkey],
        mode="lines", line=dict(color=C["blue"],width=1.5),
        fill="tozeroy", fillcolor="rgba(37,99,235,0.06)", name="Daily"
    ))
    # Event markers
    event_days = filt_daily_sorted[filt_daily_sorted["event"]!=""]
    if not event_days.empty:
        fig.add_trace(go.Scatter(
            x=event_days["date"].apply(lambda d: d.strftime("%d %b")),
            y=event_days[dkey],
            mode="markers+text",
            marker=dict(size=12, color=C["red"], symbol="diamond"),
            text=event_days["event"].apply(lambda e: e[:12]),
            textposition="top center",
            textfont=dict(size=8, color=C["red"]),
            name="SG Events",
            hovertext=event_days["event"],
        ))
    fig.update_layout(**PLOT, height=280, showlegend=True,
                      legend=dict(font=dict(color="#6b7280",size=10),bgcolor="rgba(0,0,0,0)"))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
    st.markdown('</div>', unsafe_allow_html=True)

    # Daily stats
    c1,c2,c3,c4 = st.columns(4)
    best_day = filt_daily_sorted.loc[filt_daily_sorted["revenue"].idxmax()]
    worst_day = filt_daily_sorted.loc[filt_daily_sorted["revenue"].idxmin()]
    avg_rev = filt_daily_sorted["revenue"].mean()
    event_days_count = (filt_daily_sorted["event"]!="").sum()
    for col,icon,label,val,sub,color in [
        (c1,"🏆","Best Day",best_day["date"].strftime("%d %b %Y"),f"{fmt_s(best_day['revenue'])} · {best_day['event'] or best_day['weekday']}",C["blue"]),
        (c2,"📉","Worst Day",worst_day["date"].strftime("%d %b %Y"),f"{fmt_s(worst_day['revenue'])} · {worst_day['weekday']}",C["red"]),
        (c3,"📊","Avg Daily Rev",fmt_s(int(avg_rev)),f"Over {len(filt_daily_sorted)} days",C["cyan"]),
        (c4,"🎉","Special Days",f"{event_days_count}",f"SG events in period",C["amber"]),
    ]:
        with col:
            st.markdown(f"""<div class="kpi-card">
                <div style="font-size:22px;margin-bottom:8px">{icon}</div>
                <div class="kpi-val" style="color:{color};font-size:17px">{val}</div>
                <div class="kpi-label">{label}</div>
                <div class="kpi-sub">{sub}</div>
            </div>""", unsafe_allow_html=True)

    # Singapore Events Calendar
    st.markdown('<div class="chart-card"><div class="chart-title">🇸🇬 Singapore Events & Impact</div><div class="chart-sub">Special days with revenue performance vs daily average</div>', unsafe_allow_html=True)
    event_rows = filt_daily_sorted[filt_daily_sorted["event"]!=""].copy()
    if not event_rows.empty:
        overall_avg = filt_daily_sorted["revenue"].mean()
        event_rows["vs_avg"] = ((event_rows["revenue"] - overall_avg) / overall_avg * 100).round(1)
        for _,row in event_rows.iterrows():
            va = row["vs_avg"]
            va_color = C["green"] if va > 0 else C["red"]
            va_str = f"{'↑' if va>0 else '↓'}{abs(va):.1f}% vs avg"
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:12px;padding:9px 0;border-bottom:1px solid #f1f5f9">
                <div style="width:70px;font-size:11px;color:#9ca3af;flex-shrink:0">{row['date'].strftime('%d %b')}</div>
                <div style="flex:1">
                    <span style="font-size:12px;font-weight:600;color:#1e293b">{row['event']}</span>
                    <span style="font-size:10px;color:#9ca3af;margin-left:8px">{row['weekday']}</span>
                </div>
                <div style="text-align:right">
                    <div style="font-size:12px;font-weight:700;color:#1e293b">{fmt_s(row['revenue'])}</div>
                    <div style="font-size:10px;color:{va_color};font-weight:600">{va_str}</div>
                </div>
            </div>""", unsafe_allow_html=True)
    else:
        st.info("No special events in selected period.")
    st.markdown('</div>', unsafe_allow_html=True)

    # DoD table
    st.markdown('<div class="chart-card"><div class="chart-title">Day-over-Day Detail Table</div>', unsafe_allow_html=True)
    table = filt_daily_sorted.copy()
    table["Date"] = table["date"].apply(lambda d: d.strftime("%d %b %Y"))
    table["Day"] = table["weekday"]
    table["Revenue"] = table["revenue"].apply(fmt_s)
    table["DoD %"] = table["rev_dod"].apply(lambda x: f"{'↑' if x>0 else '↓'}{abs(x):.1f}%" if pd.notna(x) else "—")
    table["Orders"] = table["orders"]
    table["AOV"] = table["aov"].apply(lambda x: f"S${x}")
    table["Event"] = table["event"]
    st.dataframe(table[["Date","Day","Revenue","DoD %","Orders","AOV","Event"]],
                 use_container_width=True, hide_index=True, height=300)
    st.markdown('</div>', unsafe_allow_html=True)

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
        fig.update_layout(**PLOT,height=210)
        st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
        st.markdown('</div>',unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="chart-card"><div class="chart-title">Campaign AOV Efficiency</div><div class="chart-sub">Higher = better basket quality</div>', unsafe_allow_html=True)
        max_aov = (campaigns_data["revenue"]/campaigns_data["orders"]).max()
        for _,row in filt_camps.iterrows():
            aov = round(row["revenue"]/row["orders"])
            pct = int((aov/max_aov)*100)
            st.markdown(f"""<div style="margin-bottom:12px">
                <div style="display:flex;justify-content:space-between;margin-bottom:4px">
                    <span style="font-size:12px;color:#374151;font-weight:600">{row['name']}</span>
                    <span style="font-size:11px;color:{row['color']};font-weight:700">S${aov} · {row['orders']} orders</span>
                </div>
                <div style="height:7px;background:#f1f5f9;border-radius:3px">
                    <div style="height:100%;width:{pct}%;background:{row['color']};border-radius:3px"></div>
                </div></div>""",unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)

    st.markdown('<div class="chart-card"><div class="chart-title">Voucher Impact</div>', unsafe_allow_html=True)
    vc1,vc2,vc3,vc4,vc5 = st.columns(5)
    for col,label,val,sub,color in [
        (vc1,"Orders w/ Voucher","390 / 800","48.75% rate",C["amber"]),
        (vc2,"Avg Discount","S$10","per voucher",C["blue"]),
        (vc3,"Total Discount","S$3,890","from gross",C["red"]),
        (vc4,"Gross Revenue","S$357,867","before disc",C["cyan"]),
        (vc5,"Net Revenue","S$353,977","after disc",C["green"]),
    ]:
        with col:
            st.markdown(f"""<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:13px;text-align:center">
                <div style="font-size:15px;font-weight:800;color:{color}">{val}</div>
                <div style="font-size:10px;color:#374151;margin-top:5px;font-weight:600">{label}</div>
                <div style="font-size:10px;color:#9ca3af;margin-top:3px">{sub}</div>
            </div>""",unsafe_allow_html=True)
    st.markdown('</div>',unsafe_allow_html=True)

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
            </div>""",unsafe_allow_html=True)
        st.info("💡 Mobile only 4% behind desktop — audit UX to close gap.")
        st.markdown('</div>',unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="chart-card"><div class="chart-title">Monthly Voucher Rate Trend</div>', unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=actual_monthly["month"],y=actual_monthly["voucher_rate"],
            mode="lines+markers",line=dict(color=C["amber"],width=2.5),marker=dict(size=7,color=C["amber"])))
        fig.add_hline(y=48.75,line_dash="dash",line_color="#d1d5db",
                      annotation_text="Avg 48.75%",annotation_font_color="#9ca3af")
        fig.update_layout(**PLOT,height=210,yaxis_range=[35,65])
        st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
        st.markdown('</div>',unsafe_allow_html=True)

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
        fig.update_layout(**PLOT,height=250,xaxis_tickprefix="$",xaxis_tickformat=".0s")
        st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
        st.markdown('</div>',unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="chart-card"><div class="chart-title">City Rankings</div>', unsafe_allow_html=True)
        for i,row in filt_cities.reset_index(drop=True).iterrows():
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
            </div>""",unsafe_allow_html=True)
        st.error("🚨 Jurong -35% below Woodlands. Test geo-targeted promo.")
        st.markdown('</div>',unsafe_allow_html=True)

    # Fixed: use separate figures instead of make_subplots to avoid TypeError
    st.markdown('<div class="chart-card"><div class="chart-title">Revenue vs Orders by City</div>', unsafe_allow_html=True)
    col_a,col_b = st.columns(2)
    with col_a:
        fig_rev = go.Figure(go.Bar(x=filt_cities["name"],y=filt_cities["revenue"],
            marker_color=C["blue"],opacity=0.85,marker_line_width=0,name="Revenue"))
        fig_rev.update_layout(**PLOT,height=180,title_text="Revenue (S$)",title_font_size=11)
        st.plotly_chart(fig_rev,use_container_width=True,config={"displayModeBar":False})
    with col_b:
        fig_ord = go.Figure(go.Bar(x=filt_cities["name"],y=filt_cities["orders"],
            marker_color=C["cyan"],opacity=0.85,marker_line_width=0,name="Orders"))
        fig_ord.update_layout(**PLOT,height=180,title_text="Orders",title_font_size=11)
        st.plotly_chart(fig_ord,use_container_width=True,config={"displayModeBar":False})
    st.markdown('</div>',unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# AI ANALYST
# ═══════════════════════════════════════════════════════════════════════════════
elif "AI Analyst" in view:
    st.markdown('<div class="section-header">🤖 AI Analyst</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Ask anything about your Shopee data · Powered by Gemini AI (free)</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="share-box">
        <div style="font-weight:700;font-size:15px;color:#1e293b;margin-bottom:6px">🔗 Share this dashboard</div>
        <div style="font-size:13px;color:#374151;margin-bottom:10px">Your Streamlit app URL is your shareable link. Click <b>Share</b> in the top-right of Streamlit Cloud to copy it.<br>
        To make it <b>private</b>: Manage app → Settings → Sharing → set to "Only specific people" and add emails.</div>
        <div style="background:#fff;border:1px solid #bfdbfe;border-radius:8px;padding:10px 14px;font-family:monospace;font-size:12px;color:#1d4ed8">
            https://ai-commerce-intelligence-fnb7bxjcdyz5fa6tx8mg9z.streamlit.app
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="chat-tip">💡 <b>Tip:</b> Gemini free tier auto-retries across 3 models. If still busy, wait 30 seconds. Ask one question at a time.</div>', unsafe_allow_html=True)

    QUICK_QS = [
        "What's causing the Jan revenue dip?","Which campaign has the best ROI?",
        "Top 3 growth opportunities?","Best day to run flash sales?",
        "Why is Jurong underperforming?","How to improve repeat rate?",
        "How can we reduce voucher leakage?","Which payment method to promote?",
        "What does the Feb 2026 forecast look like?",
    ]

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {"role":"assistant","content":"👋 Hi! I'm your Shopee analyst. I know your full data — revenue, campaigns, cities, brands, vouchers, daily trends and SG events. Ask me anything!"}
        ]

    st.markdown("**Quick questions:**")
    cols = st.columns(3)
    for i,q in enumerate(QUICK_QS):
        if cols[i%3].button(q,key=f"qb_{i}"):
            st.session_state._pending = q

    st.markdown("---")

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if len(st.session_state.chat_history) > 1:
        if st.button("🗑️ Clear chat"):
            st.session_state.chat_history = [st.session_state.chat_history[0]]
            st.rerun()

    prompt = st.chat_input("Ask about your Shopee data…")
    if not prompt and hasattr(st.session_state,"_pending"):
        prompt = st.session_state._pending
        del st.session_state._pending

    if prompt:
        last_user = next((m["content"] for m in reversed(st.session_state.chat_history) if m["role"]=="user"),None)
        if prompt != last_user:
            st.session_state.chat_history.append({"role":"user","content":prompt})
            with st.chat_message("user"):
                st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analysing…"):
                api_key = get_api_key()
                if not api_key:
                    reply = "⚠️ Gemini API key not found. Add GEMINI_API_KEY to Streamlit Cloud → Settings → Secrets."
                else:
                    try:
                        sys_prompt = ("You are a sharp Shopee Singapore e-commerce analyst. "
                                      "Be concise — max 4 sentences. Use exact numbers. "
                                      "End with 1 specific actionable recommendation.\n\nData:\n" + AI_CTX)
                        history = [{"role":m["role"],"content":m["content"]}
                                   for m in st.session_state.chat_history
                                   if m["role"] in ("user","assistant")]
                        reply = call_gemini(api_key, history, sys_prompt)
                    except requests.exceptions.HTTPError as e:
                        code = e.response.status_code
                        reply = f"⏳ Rate limit ({code}). Please wait 30 seconds." if code==429 else f"❌ API error {code}."
                    except Exception as e:
                        reply = f"❌ Error: {str(e)}"
            st.write(reply)
            st.session_state.chat_history.append({"role":"assistant","content":reply})
