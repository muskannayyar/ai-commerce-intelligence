import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import os, requests, json
from datetime import date, timedelta

st.set_page_config(page_title="Shopee Commerce Intelligence", page_icon="⚡", layout="wide")

# ── API Key ───────────────────────────────────────────────────────────────────
def get_api_key():
    try:
        k = st.secrets["ANTHROPIC_API_KEY"]
        if k and str(k).strip():
            return str(k).strip()
    except Exception:
        pass
    return os.environ.get("ANTHROPIC_API_KEY", "")

# ── Colors ────────────────────────────────────────────────────────────────────
C = {
    "blue":"#2563eb","cyan":"#0891b2","violet":"#7c3aed","purple":"#9333ea",
    "green":"#16a34a","amber":"#d97706","red":"#dc2626","orange":"#ea580c",
}

def PL(height=220, legend=False, **kw):
    d = dict(
        paper_bgcolor=None, plot_bgcolor=None,
        font=dict(color="#374151", family="Inter,sans-serif", size=11),
        margin=dict(l=0, r=0, t=10, b=0),
        showlegend=legend,
        xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(color="#6b7280", size=10)),
        yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)", zeroline=False,
                   tickfont=dict(color="#6b7280", size=10)),
        height=height,
    )
    if legend:
        d["legend"] = dict(font=dict(color="#6b7280", size=10), bgcolor=None)
    d.update(kw)
    return d

# ── Singapore Events ──────────────────────────────────────────────────────────
SG_EVENTS = {
    date(2025,10, 1):"🎂 Children's Day",
    date(2025,10,31):"🎃 Halloween",
    date(2025,11, 1):"🛍️ 11.11 Countdown",
    date(2025,11,11):"🛍️ 11.11 Mega Sale",
    date(2025,12,25):"🎄 Christmas Day ✦PH",
    date(2025,12,26):"🎁 Boxing Day",
    date(2025,12,31):"🎆 New Year's Eve",
    date(2026, 1, 1):"🎉 New Year's Day ✦PH",
    date(2026, 1,29):"🧧 Chinese New Year ✦PH",
    date(2026, 1,30):"🧧 CNY Day 2 ✦PH",
}

# ── Data ──────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    monthly = pd.DataFrame([
        {"ym":"Oct 2025","month":"Oct","revenue":88216, "orders":218,"aov":405,"customers":217,"voucher_rate":50.0,"avg_delivery":3.1,"avg_rating":4.67,"is_forecast":False},
        {"ym":"Nov 2025","month":"Nov","revenue":94439, "orders":201,"aov":470,"customers":199,"voucher_rate":55.2,"avg_delivery":3.1,"avg_rating":4.64,"is_forecast":False},
        {"ym":"Dec 2025","month":"Dec","revenue":96386, "orders":204,"aov":472,"customers":203,"voucher_rate":45.1,"avg_delivery":3.1,"avg_rating":4.64,"is_forecast":False},
        {"ym":"Jan 2026","month":"Jan","revenue":74936, "orders":177,"aov":423,"customers":176,"voucher_rate":44.1,"avg_delivery":3.0,"avg_rating":4.64,"is_forecast":False},
        {"ym":"Feb 2026*","month":"Feb*","revenue":82000,"orders":188,"aov":436,"customers":186,"voucher_rate":46.0,"avg_delivery":3.0,"avg_rating":4.65,"is_forecast":True},
    ])
    monthly["rev_mom"]  = monthly["revenue"].pct_change()*100
    monthly["ord_mom"]  = monthly["orders"].pct_change()*100
    monthly["aov_mom"]  = monthly["aov"].pct_change()*100
    monthly["cust_mom"] = monthly["customers"].pct_change()*100
    return monthly

@st.cache_data
def load_static():
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
        {"name":"PayNow",      "value":104497,"orders":212,"color":C["blue"]},
        {"name":"ShopeePay",   "value":92065, "orders":199,"color":C["cyan"]},
        {"name":"SPayLater",   "value":80145, "orders":190,"color":C["violet"]},
        {"name":"Credit Card", "value":77270, "orders":199,"color":C["purple"]},
    ])
    brands = pd.DataFrame([
        {"name":"LG",     "revenue":227248,"orders":158,"color":C["blue"]},
        {"name":"Philips","revenue":67817, "orders":164,"color":C["cyan"]},
        {"name":"Nike",   "revenue":26834, "orders":147,"color":C["violet"]},
        {"name":"Anker",  "revenue":24707, "orders":166,"color":C["purple"]},
        {"name":"COSRX",  "revenue":7371,  "orders":165,"color":C["green"]},
    ])
    dow = pd.DataFrame([
        {"day":"Mon","revenue":45507},{"day":"Tue","revenue":47581},
        {"day":"Wed","revenue":62817},{"day":"Thu","revenue":41193},
        {"day":"Fri","revenue":56486},{"day":"Sat","revenue":50653},{"day":"Sun","revenue":49740},
    ])
    summary = {
        "totalRev":353977,"totalOrders":800,"totalCust":772,"repeatRate":3.6,
        "avgDelivery":3.12,"avgRating":4.65,"voucherRate":48.75,"voucherDiscount":3890,
        "revPerCust":458.5,"gross":357867,
    }
    return weekly, categories, campaigns, cities, payments, brands, dow, summary

@st.cache_data
def load_daily():
    rng  = np.random.default_rng(42)
    rows = []
    d    = date(2025,10,1)
    targets = {10:88216,11:94439,12:96386,1:74936}
    while d <= date(2026,1,31):
        base  = targets[d.month]/30
        dow_m = {0:1.05,1:1.08,2:1.35,3:0.9,4:1.2,5:1.1,6:1.06}[d.weekday()]
        ev    = SG_EVENTS.get(d,"")
        ev_m  = (2.8 if "11.11" in ev else 1.9 if "Christmas" in ev else
                 1.7 if "CNY" in ev else 1.5 if "New Year" in ev and "Eve" not in ev else
                 1.3 if "PH" in ev else 1.0)
        rev    = int(base*dow_m*ev_m*rng.uniform(0.82,1.18))
        orders = max(1,int(rev/rng.uniform(380,520)))
        rows.append({"date":d,"weekday":d.strftime("%a"),"revenue":rev,"orders":orders,
                     "aov":round(rev/orders),"voucher_rate":round(rng.uniform(40,60),1),"event":ev})
        d += timedelta(days=1)
    df = pd.DataFrame(rows)
    df["rev_dod"] = df["revenue"].pct_change()*100
    return df

# Load
monthly_data   = load_data()
weekly_data, categories_data, campaigns_data, cities_data, payments_data, brands_data, dow_data, SUMMARY = load_static()
daily_data     = load_daily()
actual_monthly = monthly_data[monthly_data["is_forecast"]==False]

# ── Helpers ───────────────────────────────────────────────────────────────────
def fmt_s(v):
    return f"S${v/1000:.1f}K" if v>=1000 else f"S${round(v)}"

def badge(p):
    if p is None or pd.isna(p): return ""
    p=float(p); arr="↑" if p>0 else("↓" if p<0 else"→")
    col=C["green"] if p>0 else(C["red"] if p<0 else"#64748b")
    return f'<span style="color:{col};font-weight:700;font-size:12px">{arr}{abs(p):.1f}%</span>'

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"],.stApp{font-family:'Inter',sans-serif!important;background:#f1f5f9!important;color:#1e293b!important}
#MainMenu,footer,header[data-testid="stHeader"],div[data-testid="stToolbar"],div[data-testid="stDecoration"]{display:none!important}
.block-container{padding:1rem 2rem 3rem!important;background:#f1f5f9!important}
section[data-testid="stSidebar"]{background:#fff!important;border-right:1px solid #e2e8f0!important}
section[data-testid="stSidebar"] *{color:#374151!important}
.stSelectbox>div>div,.stMultiSelect>div>div{background:#f8fafc!important;border-color:#e2e8f0!important;color:#1e293b!important;border-radius:8px!important}
.stButton>button{background:#2563eb!important;color:white!important;border:none!important;border-radius:8px!important;font-weight:600!important}
.kpi-card{background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:18px 20px;margin-bottom:10px;box-shadow:0 1px 4px rgba(0,0,0,.05)}
.kpi-val{font-size:22px;font-weight:800;margin-bottom:4px}
.kpi-label{font-size:10px;color:#6b7280;font-weight:700;text-transform:uppercase;letter-spacing:.04em;margin-bottom:3px}
.kpi-sub{font-size:11px;color:#9ca3af}
.section-header{font-size:20px;font-weight:800;color:#0f172a;margin-bottom:4px}
.section-sub{font-size:13px;color:#64748b;margin-bottom:18px}
.chart-card{background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:18px 20px;box-shadow:0 1px 4px rgba(0,0,0,.05);margin-bottom:14px}
.chart-title{font-size:14px;font-weight:700;color:#1e293b;margin-bottom:4px}
.chart-sub{font-size:11px;color:#9ca3af;margin-bottom:10px}
hr{border-color:#e2e8f0!important}
div[data-testid="stIFrame"]{border:none!important;background:transparent!important}
</style>""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""<div style="display:flex;align-items:center;gap:10px;padding-bottom:14px;border-bottom:1px solid #e2e8f0;margin-bottom:14px">
      <div style="width:36px;height:36px;border-radius:10px;background:linear-gradient(135deg,#2563eb,#0891b2);display:flex;align-items:center;justify-content:center;font-size:17px">⚡</div>
      <div><div style="font-weight:800;font-size:14px;color:#0f172a">Shopee Intel</div>
      <div style="font-size:10px;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em">Commerce Dashboard</div></div>
    </div>""", unsafe_allow_html=True)

    view = st.selectbox("View", [
        "📊 Overview","📅 MoM Analysis","📆 Weekly",
        "📆 Daily Analysis","📣 Campaigns","📍 Geography","🎯 Scenario Planning"
    ], label_visibility="collapsed")

    st.markdown('<p style="font-size:11px;font-weight:700;color:#9ca3af;text-transform:uppercase;letter-spacing:.06em;margin:14px 0 6px">Filters</p>', unsafe_allow_html=True)

    actual_yms     = list(actual_monthly["ym"])
    month_filter   = "All Months"
    months_compare = actual_yms[:]
    camp_filter    = "All Campaigns"
    city_filter    = "All Cities"
    daily_month    = "All"

    if "Overview"  in view: month_filter   = st.selectbox("Month",["All Months"]+actual_yms)
    if "MoM"       in view:
        months_compare = st.multiselect("Compare months",actual_yms,default=actual_yms)
        if not months_compare: months_compare = actual_yms
    if "Campaigns" in view: camp_filter    = st.selectbox("Campaign",["All Campaigns"]+list(campaigns_data["name"]))
    if "Geography" in view: city_filter    = st.selectbox("City",["All Cities"]+list(cities_data["name"]))
    if "Daily"     in view: daily_month    = st.selectbox("Month",["All","Oct 2025","Nov 2025","Dec 2025","Jan 2026"])

    st.markdown('<p style="font-size:11px;font-weight:700;color:#9ca3af;text-transform:uppercase;letter-spacing:.06em;margin:14px 0 6px">Data Upload</p>', unsafe_allow_html=True)
    up = st.file_uploader("CSV/Excel",type=["csv","xlsx","xls"],label_visibility="collapsed")
    if up:
        st.success(f"✓ {up.name}")

    st.markdown('<p style="font-size:11px;font-weight:700;color:#9ca3af;text-transform:uppercase;letter-spacing:.06em;margin:14px 0 6px">AI Status</p>', unsafe_allow_html=True)
    if get_api_key():
        st.markdown('<div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:8px 12px;font-size:12px;color:#15803d;font-weight:600">✅ Claude AI ready — chat bottom right ↘</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="background:#fef2f2;border:1px solid #fecaca;border-radius:8px;padding:8px 12px;font-size:12px;color:#dc2626;font-weight:600">❌ Add ANTHROPIC_API_KEY to Secrets</div>', unsafe_allow_html=True)

    st.markdown('<p style="font-size:10px;color:#cbd5e1;text-align:center;margin-top:16px">Powered by Claude AI (Anthropic)</p>', unsafe_allow_html=True)

# ── Filtered slices ───────────────────────────────────────────────────────────
filt_m  = actual_monthly if month_filter=="All Months"   else actual_monthly[actual_monthly["ym"]==month_filter]
filt_c  = campaigns_data if camp_filter=="All Campaigns" else campaigns_data[campaigns_data["name"]==camp_filter]
filt_ci = cities_data    if city_filter=="All Cities"    else cities_data[cities_data["name"]==city_filter]
mmap    = {"Oct 2025":10,"Nov 2025":11,"Dec 2025":12,"Jan 2026":1}
filt_d  = daily_data if daily_month=="All" else daily_data[daily_data["date"].apply(lambda x:x.month==mmap.get(daily_month,0))]
tot_rev = filt_m["revenue"].sum()
tot_ord = filt_m["orders"].sum()

# ══════════════════════════════════════════════════════════════════════════════
# OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
if "Overview" in view:
    st.markdown('<div class="section-header">📊 Overview</div>',unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Shopee Singapore · Oct 2025 – Jan 2026 · 800 orders</div>',unsafe_allow_html=True)
    last = actual_monthly.iloc[-1]
    c1,c2,c3,c4 = st.columns(4)
    for col,icon,label,val,sub,color,pct in [
        (c1,"💰","Total Revenue",   fmt_s(tot_rev),                               f"{tot_ord} orders",    C["blue"],  last["rev_mom"]),
        (c2,"🧾","Avg Order Value", f"S${round(tot_rev/tot_ord) if tot_ord else 0}","Revenue ÷ Orders",   C["cyan"],  last["aov_mom"]),
        (c3,"👤","Rev / Customer",  fmt_s(SUMMARY["revPerCust"]),                  "Total ÷ customers",   C["violet"],None),
        (c4,"🔁","Repeat Purchase", f"{SUMMARY['repeatRate']}%",                   "Bought 2× or more",   C["purple"],None),
    ]:
        with col:
            st.markdown(f"""<div class="kpi-card">
                <div style="font-size:22px;margin-bottom:8px">{icon}</div>
                <div class="kpi-val" style="color:{color}">{val}</div>
                <div class="kpi-label">{label}</div>
                <div class="kpi-sub">{sub} {badge(pct)}</div>
            </div>""",unsafe_allow_html=True)

    c1,c2,c3,c4 = st.columns(4)
    for col,icon,label,val,sub,hint,color in [
        (c1,"🚚","Avg Delivery",    f"{SUMMARY['avgDelivery']}d",                   "Order → doorstep",                    "Target < 2d",  C["cyan"]),
        (c2,"⭐","Store Rating",     f"{SUMMARY['avgRating']}★",                     "Avg across orders",                   "Target 4.8+",  C["amber"]),
        (c3,"🎫","Voucher Usage",   f"{SUMMARY['voucherRate']}%",                   f"S${SUMMARY['voucherDiscount']} disc", "48.75% redeem",C["orange"]),
        (c4,"📉","Discount Leakage",fmt_s(SUMMARY["gross"]-SUMMARY["totalRev"]),    f"Gross {fmt_s(SUMMARY['gross'])}",    "Voucher cost", C["red"]),
    ]:
        with col:
            st.markdown(f"""<div class="kpi-card">
                <div style="font-size:22px;margin-bottom:8px">{icon}</div>
                <div class="kpi-val" style="color:{color};font-size:19px">{val}</div>
                <div class="kpi-label">{label}</div>
                <div class="kpi-sub">{sub}</div>
                <div style="font-size:10px;color:{color};margin-top:5px;font-weight:600">{hint}</div>
            </div>""",unsafe_allow_html=True)

    col_l,col_r = st.columns([3,2])
    with col_l:
        st.markdown('<div class="chart-card"><div class="chart-title">Revenue Trend + Feb 2026 Forecast</div>',unsafe_allow_html=True)
        mkey = st.radio("m",["revenue","orders","aov"],horizontal=True,label_visibility="collapsed",
                        format_func=lambda x:{"revenue":"Revenue","orders":"Orders","aov":"AOV"}[x])
        act=actual_monthly; fore=monthly_data[monthly_data["is_forecast"]==True]
        fig=go.Figure()
        fig.add_trace(go.Scatter(x=act["ym"],y=act[mkey],mode="lines+markers",name="Actual",
            line=dict(color=C["blue"],width=2.5),marker=dict(size=7,color=C["blue"]),
            fill="tozeroy",fillcolor="rgba(37,99,235,0.08)"))
        fig.add_trace(go.Scatter(x=[act["ym"].iloc[-1],fore["ym"].iloc[0]],y=[act[mkey].iloc[-1],fore[mkey].iloc[0]],
            mode="lines",line=dict(color=C["amber"],width=2,dash="dot"),showlegend=False))
        fig.add_trace(go.Scatter(x=fore["ym"],y=fore[mkey],mode="markers",name="Forecast",
            marker=dict(size=10,color=C["amber"],symbol="diamond")))
        fig.update_layout(**PL(height=210,legend=True))
        st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
        st.markdown('</div>',unsafe_allow_html=True)
    with col_r:
        st.markdown('<div class="chart-card"><div class="chart-title">Category Mix</div><div class="chart-sub">Revenue share</div>',unsafe_allow_html=True)
        fig2=go.Figure(go.Pie(labels=categories_data["name"],values=categories_data["revenue"],
            marker_colors=categories_data["color"].tolist(),hole=0.55,
            textinfo="label+percent",textfont_size=11,textfont_color="#374151"))
        fig2.update_layout(**PL(height=175))
        st.plotly_chart(fig2,use_container_width=True,config={"displayModeBar":False})
        st.markdown('</div>',unsafe_allow_html=True)

    c1,c2,c3 = st.columns(3)
    with c1:
        st.markdown('<div class="chart-card"><div class="chart-title">Best Day to Sell</div>',unsafe_allow_html=True)
        dc=[C["blue"] if d=="Wed" else "#bfdbfe" for d in dow_data["day"]]
        fig3=go.Figure(go.Bar(x=dow_data["day"],y=dow_data["revenue"],marker_color=dc,marker_line_width=0))
        fig3.update_layout(**PL(height=130))
        st.plotly_chart(fig3,use_container_width=True,config={"displayModeBar":False})
        ca,cb=st.columns(2)
        ca.markdown('<div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;padding:8px;text-align:center"><div style="font-size:9px;color:#2563eb;font-weight:700">🏆 Best</div><div style="font-size:12px;font-weight:800">Wed</div><div style="font-size:10px;color:#64748b">S$62,817</div></div>',unsafe_allow_html=True)
        cb.markdown('<div style="background:#fef2f2;border:1px solid #fecaca;border-radius:8px;padding:8px;text-align:center"><div style="font-size:9px;color:#dc2626;font-weight:700">↓ Worst</div><div style="font-size:12px;font-weight:800">Thu</div><div style="font-size:10px;color:#64748b">S$41,193</div></div>',unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="chart-card"><div class="chart-title">Top Brands</div><div class="chart-sub">LG dominates 64%</div>',unsafe_allow_html=True)
        for i,row in brands_data.iterrows():
            pb=int((row["revenue"]/227248)*100)
            st.markdown(f"""<div style="margin-bottom:9px">
                <div style="display:flex;justify-content:space-between;margin-bottom:3px">
                    <span style="font-size:12px;color:#374151;font-weight:{'700' if i==0 else '400'}">{row['name']} {'🏆' if i==0 else ''}</span>
                    <span style="font-size:11px;color:{row['color']};font-weight:700">{fmt_s(row['revenue'])}</span>
                </div>
                <div style="height:6px;background:#f1f5f9;border-radius:3px"><div style="height:100%;width:{pb}%;background:{row['color']};border-radius:3px"></div></div>
            </div>""",unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="chart-card"><div class="chart-title">Payment Split</div>',unsafe_allow_html=True)
        for _,row in payments_data.iterrows():
            sh=round((row["value"]/353977)*100)
            st.markdown(f"""<div style="margin-bottom:10px">
                <div style="display:flex;justify-content:space-between;margin-bottom:3px">
                    <span style="font-size:11px;color:#374151">{row['name']}</span>
                    <span style="font-size:11px;color:{row['color']};font-weight:700">{sh}%</span>
                </div>
                <div style="height:6px;background:#f1f5f9;border-radius:3px"><div style="height:100%;width:{sh}%;background:{row['color']};border-radius:3px"></div></div>
                <div style="font-size:10px;color:#9ca3af;margin-top:2px">{fmt_s(row['value'])} · AOV S${round(row['value']/row['orders'])}</div>
            </div>""",unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# MOM
# ══════════════════════════════════════════════════════════════════════════════
elif "MoM" in view:
    st.markdown('<div class="section-header">📅 Month-over-Month Analysis</div>',unsafe_allow_html=True)
    show_fc=st.toggle("Include Feb 2026 Forecast",value=True)
    comp=monthly_data[monthly_data["ym"].isin(months_compare)]
    if show_fc:
        comp=pd.concat([comp,monthly_data[monthly_data["is_forecast"]==True]],ignore_index=True)
    st.markdown('<div class="chart-card"><div class="chart-title">Month Comparison</div>',unsafe_allow_html=True)
    disp=comp.copy()
    disp["Revenue"]=disp["revenue"].apply(fmt_s)
    disp["Rev MoM"]=disp["rev_mom"].apply(lambda x:f"{'↑' if x>0 else '↓'}{abs(x):.1f}%" if pd.notna(x) else "—")
    disp["Orders"]=disp["orders"]
    disp["Ord MoM"]=disp["ord_mom"].apply(lambda x:f"{'↑' if x>0 else '↓'}{abs(x):.1f}%" if pd.notna(x) else "—")
    disp["AOV"]=disp["aov"].apply(lambda x:f"S${x}")
    disp["Voucher%"]=disp["voucher_rate"].apply(lambda x:f"{x}%")
    disp["Type"]=disp["is_forecast"].apply(lambda x:"📊 Forecast" if x else "✅ Actual")
    st.dataframe(disp[["ym","Type","Revenue","Rev MoM","Orders","Ord MoM","AOV","Voucher%"]].rename(columns={"ym":"Month"}),use_container_width=True,hide_index=True)
    st.markdown('</div>',unsafe_allow_html=True)
    for (k1,l1,c1c),(k2,l2,c2c) in [
        (("revenue","Revenue (S$)",C["blue"]),("orders","Orders",C["cyan"])),
        (("aov","AOV (S$)",C["violet"]),("voucher_rate","Voucher %",C["amber"])),
    ]:
        col1,col2=st.columns(2)
        for col,key,lbl,color in [(col1,k1,l1,c1c),(col2,k2,l2,c2c)]:
            with col:
                st.markdown(f'<div class="chart-card"><div class="chart-title">{lbl} by Month</div>',unsafe_allow_html=True)
                bc=[C["amber"] if r["is_forecast"] else color for _,r in comp.iterrows()]
                fig=go.Figure(go.Bar(x=comp["ym"],y=comp[key],marker_color=bc,marker_line_width=0))
                fig.update_layout(**PL(height=180))
                st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
                st.markdown('</div>',unsafe_allow_html=True)
    st.markdown('<div class="chart-card"><div class="chart-title">Revenue MoM % Change</div>',unsafe_allow_html=True)
    sub=comp.dropna(subset=["rev_mom"])
    bc=[C["amber"] if r["is_forecast"] else(C["blue"] if v>=0 else C["red"]) for v,(_,r) in zip(sub["rev_mom"],sub.iterrows())]
    fig=go.Figure(go.Bar(x=sub["ym"],y=sub["rev_mom"],marker_color=bc,marker_line_width=0,
        text=sub["rev_mom"].apply(lambda v:f"{'↑' if v>0 else '↓'}{abs(v):.1f}%"),
        textposition="outside",textfont=dict(size=11,color="#374151")))
    fig.add_hline(y=0,line_color="#e2e8f0")
    fig.update_layout(**PL(height=180))
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
    st.markdown('</div>',unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# WEEKLY
# ══════════════════════════════════════════════════════════════════════════════
elif "Weekly" in view:
    st.markdown('<div class="section-header">📆 Weekly Analysis</div>',unsafe_allow_html=True)
    wkey=st.radio("w",["revenue","orders","aov","voucher_rate"],horizontal=True,label_visibility="collapsed",
                  format_func=lambda x:{"revenue":"Revenue","orders":"Orders","aov":"AOV","voucher_rate":"Voucher%"}[x])
    st.markdown('<div class="chart-card"><div class="chart-title">Weekly Trend</div>',unsafe_allow_html=True)
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=weekly_data["wk"],y=weekly_data[wkey],mode="lines",
        line=dict(color=C["blue"],width=2),fill="tozeroy",fillcolor="rgba(37,99,235,0.07)"))
    fig.update_layout(**PL(height=200))
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
    st.markdown('</div>',unsafe_allow_html=True)
    col_l,col_r=st.columns([3,2])
    with col_l:
        st.markdown('<div class="chart-card"><div class="chart-title">WoW Revenue %</div>',unsafe_allow_html=True)
        wow=weekly_data.dropna(subset=["rev_wow"])
        fig2=go.Figure(go.Bar(x=wow["wk"],y=wow["rev_wow"],
            marker_color=[C["blue"] if v>=0 else C["red"] for v in wow["rev_wow"]],marker_line_width=0))
        fig2.add_hline(y=0,line_color="#e2e8f0")
        fig2.update_layout(**PL(height=190))
        st.plotly_chart(fig2,use_container_width=True,config={"displayModeBar":False})
        st.markdown('</div>',unsafe_allow_html=True)
    with col_r:
        st.markdown('<div class="chart-card"><div class="chart-title">Last 8 Weeks</div>',unsafe_allow_html=True)
        l8=weekly_data.tail(8).copy()
        l8["Revenue"]=l8["revenue"].apply(fmt_s)
        l8["WoW"]=l8["rev_wow"].apply(lambda x:f"{'↑' if x>0 else '↓'}{abs(x):.1f}%" if pd.notna(x) else "—")
        l8["AOV"]=l8["aov"].apply(lambda x:f"S${x}")
        st.dataframe(l8[["wk","Revenue","WoW","orders","AOV"]].rename(columns={"wk":"Week","orders":"Orders"}),
                     use_container_width=True,hide_index=True,height=225)
        st.markdown('</div>',unsafe_allow_html=True)
    c1,c2,c3,c4=st.columns(4)
    for col,icon,lbl,val,sub,color in [
        (c1,"🏆","Peak Week","W52 Dec 22","S$33,554 · Christmas",C["blue"]),
        (c2,"📦","Most Orders","W43 Oct 20","62 orders",C["cyan"]),
        (c3,"💎","Best AOV","W05 Jan 26","S$738 avg",C["violet"]),
        (c4,"🎫","Peak Vouchers","W47 Nov 17","64.3% redeem",C["amber"]),
    ]:
        with col:
            st.markdown(f"""<div class="kpi-card" style="text-align:center">
                <div style="font-size:22px;margin-bottom:6px">{icon}</div>
                <div style="font-size:9px;color:#9ca3af;text-transform:uppercase">{lbl}</div>
                <div style="font-size:14px;font-weight:800;color:{color};margin:5px 0 3px">{val}</div>
                <div style="font-size:11px;color:#64748b">{sub}</div>
            </div>""",unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# DAILY
# ══════════════════════════════════════════════════════════════════════════════
elif "Daily" in view:
    st.markdown('<div class="section-header">📆 Daily Analysis</div>',unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Day-by-day · Singapore holidays highlighted</div>',unsafe_allow_html=True)
    dkey=st.radio("dk",["revenue","orders","aov","voucher_rate"],horizontal=True,label_visibility="collapsed",
                  format_func=lambda x:{"revenue":"Revenue","orders":"Orders","aov":"AOV","voucher_rate":"Voucher%"}[x])
    ds=filt_d.sort_values("date"); date_strs=ds["date"].apply(lambda d:d.strftime("%d %b"))
    st.markdown('<div class="chart-card"><div class="chart-title">Daily Trend with SG Events</div><div class="chart-sub">🔴 Red diamonds = SG public holidays &amp; campaigns</div>',unsafe_allow_html=True)
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=date_strs,y=ds[dkey],mode="lines",line=dict(color=C["blue"],width=1.5),fill="tozeroy",fillcolor="rgba(37,99,235,0.06)",name="Daily"))
    ev=ds[ds["event"]!=""]
    if not ev.empty:
        fig.add_trace(go.Scatter(x=ev["date"].apply(lambda d:d.strftime("%d %b")),y=ev[dkey],
            mode="markers",marker=dict(size=12,color=C["red"],symbol="diamond"),name="SG Events",hovertext=ev["event"]))
    fig.update_layout(**PL(height=280,legend=True))
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
    st.markdown('</div>',unsafe_allow_html=True)
    c1,c2,c3,c4=st.columns(4)
    bd=ds.loc[ds["revenue"].idxmax()]; wd=ds.loc[ds["revenue"].idxmin()]
    for col,icon,lbl,val,sub,color in [
        (c1,"🏆","Best Day",bd["date"].strftime("%d %b"),f"{fmt_s(bd['revenue'])} · {bd['event'] or bd['weekday']}",C["blue"]),
        (c2,"📉","Worst Day",wd["date"].strftime("%d %b"),f"{fmt_s(wd['revenue'])} · {wd['weekday']}",C["red"]),
        (c3,"📊","Avg Daily",fmt_s(int(ds["revenue"].mean())),f"Over {len(ds)} days",C["cyan"]),
        (c4,"🎉","SG Events",str((ds["event"]!="").sum()),"Special days",C["amber"]),
    ]:
        with col:
            st.markdown(f"""<div class="kpi-card">
                <div style="font-size:22px;margin-bottom:8px">{icon}</div>
                <div class="kpi-val" style="color:{color};font-size:17px">{val}</div>
                <div class="kpi-label">{lbl}</div><div class="kpi-sub">{sub}</div>
            </div>""",unsafe_allow_html=True)
    st.markdown('<div class="chart-card"><div class="chart-title">🇸🇬 SG Events Impact</div>',unsafe_allow_html=True)
    ev_rows=ds[ds["event"]!=""].copy(); avg=ds["revenue"].mean()
    for _,row in ev_rows.iterrows():
        va=(row["revenue"]-avg)/avg*100; vc=C["green"] if va>0 else C["red"]
        st.markdown(f"""<div style="display:flex;align-items:center;gap:12px;padding:9px 0;border-bottom:1px solid #f1f5f9">
            <div style="width:60px;font-size:11px;color:#9ca3af">{row['date'].strftime('%d %b')}</div>
            <div style="flex:1"><span style="font-size:12px;font-weight:600">{row['event']}</span>
            <span style="font-size:10px;color:#9ca3af;margin-left:8px">{row['weekday']}</span></div>
            <div style="text-align:right"><div style="font-size:12px;font-weight:700">{fmt_s(row['revenue'])}</div>
            <div style="font-size:10px;color:{vc};font-weight:600">{'↑' if va>0 else '↓'}{abs(va):.1f}% vs avg</div></div>
        </div>""",unsafe_allow_html=True)
    st.markdown('</div>',unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# CAMPAIGNS
# ══════════════════════════════════════════════════════════════════════════════
elif "Campaigns" in view:
    st.markdown('<div class="section-header">📣 Campaigns & Channels</div>',unsafe_allow_html=True)
    col_l,col_r=st.columns(2)
    with col_l:
        st.markdown('<div class="chart-card"><div class="chart-title">Campaign Revenue</div>',unsafe_allow_html=True)
        fig=go.Figure(go.Bar(x=filt_c["name"],y=filt_c["revenue"],marker_color=filt_c["color"].tolist(),marker_line_width=0))
        fig.update_layout(**PL(height=210))
        st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
        st.markdown('</div>',unsafe_allow_html=True)
    with col_r:
        st.markdown('<div class="chart-card"><div class="chart-title">Campaign AOV Efficiency</div>',unsafe_allow_html=True)
        ma=(campaigns_data["revenue"]/campaigns_data["orders"]).max()
        for _,row in filt_c.iterrows():
            aov=round(row["revenue"]/row["orders"]); pct=int((aov/ma)*100)
            st.markdown(f"""<div style="margin-bottom:12px">
                <div style="display:flex;justify-content:space-between;margin-bottom:4px">
                    <span style="font-size:12px;color:#374151;font-weight:600">{row['name']}</span>
                    <span style="font-size:11px;color:{row['color']};font-weight:700">S${aov} · {row['orders']} orders</span>
                </div>
                <div style="height:7px;background:#f1f5f9;border-radius:3px"><div style="height:100%;width:{pct}%;background:{row['color']};border-radius:3px"></div></div>
            </div>""",unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)
    st.markdown('<div class="chart-card"><div class="chart-title">Voucher Impact</div>',unsafe_allow_html=True)
    vc1,vc2,vc3,vc4,vc5=st.columns(5)
    for col,lbl,val,sub,color in [
        (vc1,"Orders w/ Voucher","390/800","48.75% rate",C["amber"]),
        (vc2,"Avg Discount","S$10","per voucher",C["blue"]),
        (vc3,"Total Discount","S$3,890","from gross",C["red"]),
        (vc4,"Gross Revenue","S$357,867","before disc",C["cyan"]),
        (vc5,"Net Revenue","S$353,977","after disc",C["green"]),
    ]:
        with col:
            st.markdown(f"""<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:13px;text-align:center">
                <div style="font-size:15px;font-weight:800;color:{color}">{val}</div>
                <div style="font-size:10px;color:#374151;margin-top:5px;font-weight:600">{lbl}</div>
                <div style="font-size:10px;color:#9ca3af;margin-top:3px">{sub}</div>
            </div>""",unsafe_allow_html=True)
    st.markdown('</div>',unsafe_allow_html=True)
    col_l,col_r=st.columns([1,2])
    with col_l:
        st.markdown('<div class="chart-card"><div class="chart-title">Device Split</div>',unsafe_allow_html=True)
        for name,rev,orders,pct,c in [("Desktop",183998,422,52,C["blue"]),("Mobile",169979,378,48,C["cyan"])]:
            st.markdown(f"""<div style="margin-bottom:14px">
                <div style="display:flex;justify-content:space-between;margin-bottom:4px">
                    <span style="font-size:12px;color:#374151">{name}</span>
                    <span style="font-size:12px;color:{c};font-weight:700">{fmt_s(rev)}</span>
                </div>
                <div style="height:9px;background:#f1f5f9;border-radius:5px"><div style="height:100%;width:{pct}%;background:{c};border-radius:5px"></div></div>
                <div style="font-size:10px;color:#9ca3af;margin-top:3px">{pct}% · {orders} orders · AOV S${round(rev/orders)}</div>
            </div>""",unsafe_allow_html=True)
        st.info("💡 Mobile only 4% behind — audit UX to close gap.")
        st.markdown('</div>',unsafe_allow_html=True)
    with col_r:
        st.markdown('<div class="chart-card"><div class="chart-title">Monthly Voucher Rate Trend</div>',unsafe_allow_html=True)
        fig=go.Figure()
        fig.add_trace(go.Scatter(x=actual_monthly["month"],y=actual_monthly["voucher_rate"],
            mode="lines+markers",line=dict(color=C["amber"],width=2.5),marker=dict(size=7,color=C["amber"])))
        fig.add_hline(y=48.75,line_dash="dash",line_color="#d1d5db",annotation_text="Avg 48.75%",annotation_font_color="#9ca3af")
        fig.update_layout(**PL(height=210,yaxis=dict(showgrid=True,gridcolor="rgba(0,0,0,0.05)",zeroline=False,tickfont=dict(color="#6b7280",size=10),range=[35,65])))
        st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
        st.markdown('</div>',unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# GEOGRAPHY
# ══════════════════════════════════════════════════════════════════════════════
elif "Geography" in view:
    st.markdown('<div class="section-header">📍 Geographic Performance</div>',unsafe_allow_html=True)
    col_l,col_r=st.columns([3,2])
    with col_l:
        st.markdown('<div class="chart-card"><div class="chart-title">Revenue by District</div>',unsafe_allow_html=True)
        bc=[C["blue"] if i==0 else(C["red"] if i==len(filt_ci)-1 else f"rgba(37,99,235,{0.75-i*0.09})") for i in range(len(filt_ci))]
        fig=go.Figure(go.Bar(y=filt_ci["name"],x=filt_ci["revenue"],orientation="h",marker_color=bc,marker_line_width=0))
        fig.update_layout(**PL(height=250,xaxis=dict(showgrid=False,zeroline=False,tickfont=dict(color="#6b7280",size=10),tickprefix="$",tickformat=".0s")))
        st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
        st.markdown('</div>',unsafe_allow_html=True)
    with col_r:
        st.markdown('<div class="chart-card"><div class="chart-title">City Rankings</div>',unsafe_allow_html=True)
        for i,row in filt_ci.reset_index(drop=True).iterrows():
            nc=C["blue"] if i==0 else(C["red"] if i==len(filt_ci)-1 else"#9ca3af")
            rc=C["blue"] if i==0 else(C["red"] if i==len(filt_ci)-1 else"#374151")
            aov=round(row["revenue"]/row["orders"])
            st.markdown(f"""<div style="display:flex;align-items:center;gap:10px;margin-bottom:11px">
                <div style="width:24px;height:24px;border-radius:7px;background:#f1f5f9;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:800;color:{nc}">{i+1}</div>
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
    st.markdown('<div class="chart-card"><div class="chart-title">Revenue vs Orders by City</div>',unsafe_allow_html=True)
    ca,cb=st.columns(2)
    with ca:
        fig_a=go.Figure(go.Bar(x=filt_ci["name"],y=filt_ci["revenue"],marker_color=C["blue"],marker_line_width=0))
        fig_a.update_layout(**PL(height=180))
        st.plotly_chart(fig_a,use_container_width=True,config={"displayModeBar":False})
    with cb:
        fig_b=go.Figure(go.Bar(x=filt_ci["name"],y=filt_ci["orders"],marker_color=C["cyan"],marker_line_width=0))
        fig_b.update_layout(**PL(height=180))
        st.plotly_chart(fig_b,use_container_width=True,config={"displayModeBar":False})
    st.markdown('</div>',unsafe_allow_html=True)



# ══════════════════════════════════════════════════════════════════════════════
# SCENARIO PLANNING
# ══════════════════════════════════════════════════════════════════════════════
elif "Scenario" in view:
    st.markdown('<div class="section-header">🎯 Scenario Planning</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Adjust the sliders to model your strategy — revenue projection updates instantly</div>', unsafe_allow_html=True)

    BASE_ORDERS = 200
    BASE_AOV    = 442
    BASE_MONTHS = ["Feb","Mar","Apr","May","Jun","Jul"]

    # ── Levers ────────────────────────────────────────────────────────────────
    st.markdown('<div class="chart-card"><div class="chart-title">📐 Business Levers</div><div class="chart-sub">Drag to model your strategy</div>', unsafe_allow_html=True)
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown("**📦 Volume & Growth**")
        order_growth  = st.slider("Monthly order growth %", -20, 40, 5, 1, key="sp_ord")
        new_customers = st.slider("New customers / month", 0, 200, 30, 10, key="sp_cust")
        repeat_rate   = st.slider("Repeat purchase rate %", 1.0, 20.0, 3.6, 0.1, key="sp_rep", format="%.1f%%")
    with col_b:
        st.markdown("**💰 Pricing & Value**")
        aov_change  = st.slider("AOV change %", -20, 30, 0, 1, key="sp_aov")
        upsell_rate = st.slider("Upsell success rate %", 0, 30, 5, 1, key="sp_up")
        premium_mix = st.slider("Premium product mix %", 0, 50, 10, 5, key="sp_prem")
    with col_c:
        st.markdown("**🎫 Vouchers & Efficiency**")
        voucher_rate = st.slider("Voucher usage rate %", 20.0, 70.0, 48.75, 0.25, key="sp_vr", format="%.2f%%")
        voucher_disc = st.slider("Avg voucher discount S$", 5, 30, 10, 1, key="sp_vd")
        ops_saving   = st.slider("Ops cost saving %", 0, 15, 0, 1, key="sp_ops")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Projection ────────────────────────────────────────────────────────────
    def sp_project(ord_gr, aov_ch, vr, vd, rep, upsell, prem, ops_sav):
        rows = []
        orders = float(BASE_ORDERS)
        aov    = BASE_AOV * (1 + aov_ch/100) * (1 + prem*0.002) * (1 + upsell*0.003)
        for mo in BASE_MONTHS:
            orders = max(40, orders * (1 + ord_gr/100))
            vcost  = orders * (vr/100) * vd
            gross  = orders * aov
            repeat_rev = gross * (rep/100) * 0.15
            net    = (gross + repeat_rev - vcost) * (1 + ops_sav/100 * 0.3)
            rows.append({"month": mo, "orders": int(orders), "aov": round(aov),
                         "voucher_cost": round(vcost), "net": round(net)})
        return pd.DataFrame(rows)

    proj = sp_project(order_growth, aov_change, voucher_rate, voucher_disc,
                      repeat_rate, upsell_rate, premium_mix, ops_saving)
    total_rev  = proj["net"].sum()
    total_ord  = proj["orders"].sum()
    total_vc   = proj["voucher_cost"].sum()
    avg_aov_p  = proj["aov"].mean()
    vs_base    = (total_rev - 530964) / 530964 * 100  # vs flat baseline (88494*6)

    # ── 4 summary KPIs ────────────────────────────────────────────────────────
    kc1, kc2, kc3, kc4 = st.columns(4)
    vc = C["green"] if vs_base >= 0 else C["red"]
    vbg= "#f0fdf4" if vs_base >= 0 else "#fef2f2"
    vbd= "#bbf7d0" if vs_base >= 0 else "#fecaca"
    for col, icon, label, val, sub, color, bg, border in [
        (kc1,"💰","6-Month Revenue",    fmt_s(total_rev),    "Your projection",     C["blue"],  "#eff6ff","#bfdbfe"),
        (kc2,"📦","Total Orders",       f"{total_ord:,}",    "6 months",            C["cyan"],  "#ecfeff","#a5f3fc"),
        (kc3,"🎫","Voucher Cost",       fmt_s(int(total_vc)),"Total discount spend", C["amber"],"#fffbeb","#fde68a"),
        (kc4,"📈","vs Flat Baseline",   f"{'+'if vs_base>=0 else ''}{vs_base:.1f}%","vs S$530K baseline", vc, vbg, vbd),
    ]:
        with col:
            st.markdown(
                f'<div style="background:{bg};border:1px solid {border};border-radius:12px;padding:16px 18px;margin-bottom:10px">' +
                f'<div style="font-size:20px;margin-bottom:6px">{icon}</div>' +
                f'<div style="font-size:20px;font-weight:900;color:{color}">{val}</div>' +
                f'<div style="font-size:10px;color:#6b7280;font-weight:700;text-transform:uppercase;margin:4px 0 2px">{label}</div>' +
                f'<div style="font-size:11px;color:#9ca3af">{sub}</div></div>',
                unsafe_allow_html=True
            )

    # ── Projection chart ──────────────────────────────────────────────────────
    st.markdown('<div class="chart-card"><div class="chart-title">📈 6-Month Revenue Projection</div><div class="chart-sub">Your slider settings applied forward from Feb 2026</div>', unsafe_allow_html=True)
    fig = go.Figure()
    hist_m = ["Oct","Nov","Dec","Jan", BASE_MONTHS[0]]
    hist_v = [88216, 94439, 96386, 74936, proj["net"].iloc[0]]
    fig.add_trace(go.Scatter(x=hist_m, y=hist_v, mode="lines",
        line=dict(color="#94a3b8", width=1.5, dash="dot"),
        name="Historical Bridge", showlegend=True))
    fig.add_trace(go.Scatter(
        x=proj["month"], y=proj["net"],
        mode="lines+markers", name="Your Projection",
        line=dict(color=C["blue"], width=2.5),
        marker=dict(size=8, color=C["blue"]),
        fill="tozeroy", fillcolor="rgba(37,99,235,0.07)"
    ))
    fig.update_layout(**PL(height=260, legend=True))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Monthly table + Lever sensitivity ─────────────────────────────────────
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown('<div class="chart-card"><div class="chart-title">📋 Monthly Breakdown</div>', unsafe_allow_html=True)
        tbl = proj.copy()
        tbl["Revenue"]      = tbl["net"].apply(fmt_s)
        tbl["Orders"]       = tbl["orders"]
        tbl["AOV"]          = tbl["aov"].apply(lambda x: f"S${x}")
        tbl["Voucher Cost"] = tbl["voucher_cost"].apply(fmt_s)
        tbl["MoM"] = tbl["net"].pct_change().apply(
            lambda x: f"{'↑' if x>0 else '↓'}{abs(x)*100:.1f}%" if pd.notna(x) else "—"
        )
        st.dataframe(
            tbl[["month","Revenue","MoM","Orders","AOV","Voucher Cost"]].rename(columns={"month":"Month"}),
            use_container_width=True, hide_index=True
        )
        st.markdown('</div>', unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="chart-card"><div class="chart-title">⚡ What Moves Revenue Most?</div><div class="chart-sub">Impact of nudging each lever one step</div>', unsafe_allow_html=True)
        proj_total = proj["net"].sum()
        def nudge(**kw):
            return sp_project(
                kw.get("ord_gr", order_growth), kw.get("aov_ch", aov_change),
                kw.get("vr", voucher_rate),      kw.get("vd", voucher_disc),
                kw.get("rep", repeat_rate),       kw.get("upsell", upsell_rate),
                kw.get("prem", premium_mix),      kw.get("ops_sav", ops_saving)
            )["net"].sum()

        levers = [
            ("📦 +5% orders",        nudge(ord_gr=order_growth+5)              - proj_total),
            ("💎 +5% AOV",           nudge(aov_ch=aov_change+5)                - proj_total),
            ("🔁 +3% repeat rate",   nudge(rep=repeat_rate+3)                  - proj_total),
            ("🎫 -5% voucher rate",  nudge(vr=max(20,voucher_rate-5))          - proj_total),
            ("💸 -S$2 voucher disc", nudge(vd=max(1,voucher_disc-2))           - proj_total),
            ("⬆️ +5% upsell",        nudge(upsell=upsell_rate+5)               - proj_total),
            ("🏷️ +5% premium mix",   nudge(prem=premium_mix+5)                 - proj_total),
            ("🏭 +5% ops saving",    nudge(ops_sav=ops_saving+5)               - proj_total),
        ]
        levers.sort(key=lambda x: x[1], reverse=True)
        max_impact = max(abs(v) for _, v in levers) or 1
        for name, impact in levers:
            bw  = int(abs(impact)/max_impact*100)
            col_= C["green"] if impact>=0 else C["red"]
            bg_ = "#f0fdf4" if impact>=0 else "#fef2f2"
            bd_ = "#bbf7d0" if impact>=0 else "#fecaca"
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:10px;padding:7px 0;border-bottom:1px solid #f8fafc">' +
                f'<div style="width:160px;font-size:11px;color:#374151;font-weight:500;flex-shrink:0">{name}</div>' +
                f'<div style="flex:1;height:7px;background:#f1f5f9;border-radius:4px">' +
                f'<div style="height:100%;width:{bw}%;background:{col_};border-radius:4px"></div></div>' +
                f'<div style="width:80px;text-align:right">' +
                f'<span style="background:{bg_};border:1px solid {bd_};border-radius:6px;padding:2px 7px;font-size:10px;font-weight:700;color:{col_}">' +
                f'{"+" if impact>=0 else ""}{fmt_s(int(abs(impact)))}</span></div></div>',
                unsafe_allow_html=True
            )
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Inline AI Q&A ─────────────────────────────────────────────────────────
    st.markdown('<div class="chart-card"><div class="chart-title">🤖 Ask the AI Analyst</div><div class="chart-sub">Ask anything — your current slider settings are included in every question</div>', unsafe_allow_html=True)

    sp_api_key = get_api_key()

    SP_SYSTEM = (
        "You are a Shopee Singapore e-commerce analyst. "
        "Answer in 3-5 sentences max, cite numbers, be direct. "
        "End with: Action: [one step]. "
        "Base data: Oct S$88216 | Nov S$94439 | Dec S$96386 | Jan S$74936 | "
        "AOV S$442 | Repeat 3.6% | Voucher 48.75% | Electronics 71% | LG 64% | "
        "Double Day best campaign S$89029 | Woodlands best city S$67353 | Jurong weakest S$44898."
    )

    slider_ctx = (
        f"Current scenario settings — Order growth: {order_growth}%/mo | "
        f"AOV change: {aov_change:+d}% | Repeat rate: {repeat_rate}% | "
        f"Voucher rate: {voucher_rate:.1f}% | Voucher discount: S${voucher_disc} | "
        f"Upsell: {upsell_rate}% | Premium mix: {premium_mix}% | Ops saving: {ops_saving}% | "
        f"Projected 6-month revenue: {fmt_s(total_rev)} | Total orders: {total_ord:,}"
    )

    if "sp_chat" not in st.session_state:
        st.session_state.sp_chat = []

    QUICK_SP = [
        "Is my projection realistic?",
        "Which lever should I focus on first?",
        "What's the risk if orders drop 10%?",
        "How can I reduce voucher leakage?",
        "What AOV should I target for S$600K revenue?",
    ]

    cols_q = st.columns(len(QUICK_SP))
    for i, q in enumerate(QUICK_SP):
        if cols_q[i].button(q, key=f"spq_{i}", use_container_width=True):
            st.session_state.sp_pending = q

    for msg in st.session_state.sp_chat[-6:]:
        role = msg["role"]
        with st.chat_message(role, avatar="🤖" if role=="assistant" else None):
            content_txt = msg["content"]
            if role == "assistant" and "Action:" in content_txt:
                parts = content_txt.split("Action:", 1)
                st.write(parts[0].strip())
                st.markdown(f'<div style="background:#fffbeb;border-left:3px solid #d97706;padding:8px 12px;margin-top:6px;font-size:12px;color:#92400e;font-weight:600;border-radius:0 6px 6px 0">⚡ Action: {parts[1].strip()}</div>', unsafe_allow_html=True)
            else:
                st.write(content_txt)

    prompt = st.chat_input("Ask about your scenario…", key="sp_input")
    if not prompt and hasattr(st.session_state, "sp_pending"):
        prompt = st.session_state.sp_pending
        del st.session_state.sp_pending

    if prompt and sp_api_key:
        last_user = next((m["content"] for m in reversed(st.session_state.sp_chat) if m["role"]=="user"), None)
        if prompt != last_user:
            full_prompt = f"{slider_ctx}\n\nQuestion: {prompt}"
            st.session_state.sp_chat.append({"role":"user","content":prompt})
            with st.chat_message("user"):
                st.write(prompt)
            api_msgs = [{"role":"user","content":full_prompt}]
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("Thinking…"):
                    try:
                        r = requests.post("https://api.anthropic.com/v1/messages",
                            json={"model":"claude-haiku-4-5-20251001","max_tokens":400,
                                  "system":SP_SYSTEM,"messages":api_msgs},
                            headers={"Content-Type":"application/json",
                                     "x-api-key":sp_api_key,
                                     "anthropic-version":"2023-06-01"},
                            timeout=30)
                        reply = r.json()["content"][0]["text"]
                    except Exception as e:
                        reply = f"❌ Error: {e}"
                if "Action:" in reply:
                    parts = reply.split("Action:", 1)
                    st.write(parts[0].strip())
                    st.markdown(f'<div style="background:#fffbeb;border-left:3px solid #d97706;padding:8px 12px;margin-top:6px;font-size:12px;color:#92400e;font-weight:600;border-radius:0 6px 6px 0">⚡ Action: {parts[1].strip()}</div>', unsafe_allow_html=True)
                else:
                    st.write(reply)
            st.session_state.sp_chat.append({"role":"assistant","content":reply})
    elif prompt and not sp_api_key:
        st.warning("Add ANTHROPIC_API_KEY to Streamlit Secrets to enable AI chat.")

    if len(st.session_state.sp_chat) > 1:
        if st.button("🗑️ Clear chat", key="sp_clr"):
            st.session_state.sp_chat = []
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# FLOATING AI CHATBOT
# Injected into window.parent.document so position:fixed works on the real page
# Calls Anthropic API with required browser CORS header
# ══════════════════════════════════════════════════════════════════════════════
import streamlit.components.v1 as components
import json

api_key = get_api_key()

AI_CTX = (
    "Shopee Singapore Oct 2025-Jan 2026, 800 orders. "
    "Revenue: Oct S$88216 -> Nov S$94439(+7.1%) -> Dec S$96386(+2.1%) -> Jan S$74936(-22.3%). Feb forecast S$82000(+9.4%). "
    "Total S$353977 | AOV S$442 | Repeat 3.6% | Delivery 3.1d | Rating 4.65 | Voucher 48.75%. "
    "Electronics 71% S$251955 | Home S$67817 | Fashion S$26834 | Beauty S$7371. "
    "LG 64% S$227248 (concentration risk) | Philips S$67817 | Nike S$26834 | Anker S$24707. "
    "Double Day S$89029 best ROI | Mega Campaign S$75121 | Brand Day S$68307 | Flash Sale S$63142. "
    "Woodlands best S$67353 | Jurong weakest S$44898 (-35% gap). "
    "PayNow leads S$104497 | Desktop 52% vs Mobile 48%. "
    "Wednesday best day S$62817 | Thursday worst S$41193. "
    "Peak weeks: W52 Christmas S$33554 | W44 Oct S$31646. Best AOV: W05 Jan S$738. "
    "SG event boosts: 11.11 Mega Sale 2.8x | Christmas 1.9x | CNY 1.7x."
)

SYSTEM_PROMPT = (
    "You are a sharp Shopee Singapore e-commerce analyst. Rules: "
    "Max 4 sentences, be direct, no filler. "
    "Always cite exact numbers (S$, %, dates). "
    "End every reply with: Action: [one concrete step this week]. "
    "Data: " + AI_CTX
)

QUICK_QS = [
    "What's causing the Jan revenue dip?",
    "Which campaign has the best ROI?",
    "Top 3 growth opportunities?",
    "Best day to run flash sales?",
    "Why is Jurong underperforming?",
    "How to improve the 3.6% repeat rate?",
    "How to reduce voucher leakage?",
    "What's our biggest risk right now?",
]

cfg = json.dumps({
    "apiKey": api_key,
    "systemPrompt": SYSTEM_PROMPT,
    "quickQuestions": QUICK_QS,
    "hasKey": bool(api_key),
})

# We inject via window.parent.document so the widget floats on the REAL page
# (not trapped inside the iframe box that components.html creates)
CHAT_HTML = """
<!DOCTYPE html>
<html><head>
<style>body{margin:0;padding:0;background:transparent;}</style>
</head>
<body>
<script>
(function() {
  const CFG = """ + cfg + """;
  const P = window.parent;
  const PD = P.document;

  // ── Avoid double-inject on Streamlit rerenders ──────────────────────────
  if (PD.getElementById('sc-bubble')) return;

  // ── Inject CSS into parent page ─────────────────────────────────────────
  const style = PD.createElement('style');
  style.id = 'sc-styles';
  style.textContent = `
    @keyframes sc-slideUp {
      from { opacity:0; transform:translateY(14px) scale(.97); }
      to   { opacity:1; transform:translateY(0)    scale(1);   }
    }
    @keyframes sc-msgIn  { from{opacity:0;transform:translateY(5px)} to{opacity:1;transform:translateY(0)} }
    @keyframes sc-blink  { 0%,100%{opacity:.25} 50%{opacity:1} }
    @keyframes sc-glow   { 0%,100%{box-shadow:0 4px 20px rgba(37,99,235,.45)} 50%{box-shadow:0 4px 32px rgba(37,99,235,.8)} }

    #sc-bubble {
      position:fixed; bottom:24px; right:24px; z-index:99999;
      width:54px; height:54px; border-radius:50%; border:none; cursor:pointer;
      background:linear-gradient(135deg,#2563eb,#0891b2);
      font-size:22px; display:flex; align-items:center; justify-content:center;
      animation: sc-glow 3s ease-in-out infinite;
      transition:transform .18s;
    }
    #sc-bubble:hover { transform:scale(1.1); }

    #sc-badge {
      position:absolute; top:-2px; right:-2px;
      width:17px; height:17px; border-radius:50%;
      background:#16a34a; border:2px solid #fff;
      font-size:7px; font-weight:800; color:#fff;
      display:flex; align-items:center; justify-content:center;
      pointer-events:none;
    }

    #sc-panel {
      position:fixed; bottom:88px; right:24px; z-index:99998;
      width:370px; height:520px;
      background:#fff; border:1px solid #e2e8f0; border-radius:18px;
      display:none; flex-direction:column; overflow:hidden;
      box-shadow:0 20px 60px rgba(0,0,0,.18);
    }
    #sc-panel.sc-open {
      display:flex;
      animation:sc-slideUp .22s ease both;
    }

    #sc-head {
      background:linear-gradient(135deg,#2563eb,#0891b2);
      padding:12px 15px; display:flex; align-items:center; gap:10px; flex-shrink:0;
    }
    #sc-head .sc-av {
      width:34px; height:34px; border-radius:50%; background:rgba(255,255,255,.18);
      display:flex; align-items:center; justify-content:center; font-size:17px; flex-shrink:0;
    }
    #sc-head .sc-info { flex:1; }
    #sc-head .sc-name { font-weight:700; font-size:13px; color:#fff; font-family:Inter,sans-serif; }
    #sc-head .sc-stat { font-size:10px; color:rgba(255,255,255,.8); margin-top:2px; font-family:Inter,sans-serif; }
    #sc-close {
      background:transparent; border:none; color:rgba(255,255,255,.7);
      font-size:20px; cursor:pointer; line-height:1; padding:2px 6px; border-radius:5px;
      font-family:Inter,sans-serif;
    }
    #sc-close:hover { color:#fff; background:rgba(255,255,255,.15); }

    #sc-msgs {
      flex:1; overflow-y:auto; padding:12px 12px 6px;
      display:flex; flex-direction:column; gap:8px;
    }
    #sc-msgs::-webkit-scrollbar { width:3px; }
    #sc-msgs::-webkit-scrollbar-thumb { background:#e2e8f0; border-radius:3px; }

    .sc-msg { max-width:87%; animation:sc-msgIn .18s ease both; font-family:Inter,sans-serif; }
    .sc-msg.sc-user { align-self:flex-end; }
    .sc-msg.sc-ai   { align-self:flex-start; }

    .sc-bub-user {
      background:linear-gradient(135deg,#2563eb,#1d4ed8);
      color:#fff; padding:9px 13px; border-radius:14px 14px 3px 14px;
      font-size:12px; line-height:1.65;
    }
    .sc-bub-ai {
      background:#f8fafc; border:1px solid #e2e8f0;
      color:#1e293b; padding:10px 13px; border-radius:14px 14px 14px 3px;
      font-size:12px; line-height:1.75;
    }
    .sc-action {
      background:#fffbeb; border-left:3px solid #d97706;
      padding:7px 10px; margin-top:8px; font-size:11px;
      color:#92400e; font-weight:600; border-radius:0 6px 6px 0;
      font-family:Inter,sans-serif;
    }

    #sc-chips {
      padding:0 10px 8px; display:flex; flex-wrap:wrap; gap:5px; flex-shrink:0;
    }
    .sc-chip {
      background:#eff6ff; border:1px solid #bfdbfe; color:#1d4ed8;
      padding:4px 10px; border-radius:20px; font-size:10px; cursor:pointer;
      transition:all .12s; white-space:nowrap; font-family:Inter,sans-serif;
    }
    .sc-chip:hover { background:#dbeafe; border-color:#93c5fd; }

    #sc-foot {
      padding:8px 10px 12px; border-top:1px solid #f1f5f9;
      display:flex; gap:6px; flex-shrink:0;
    }
    #sc-inp {
      flex:1; border:1px solid #e2e8f0; border-radius:10px;
      padding:9px 12px; font-size:12px; outline:none;
      font-family:Inter,sans-serif; color:#1e293b; background:#f8fafc;
      transition:border-color .15s;
    }
    #sc-inp:focus { border-color:#93c5fd; background:#fff; }
    #sc-inp::placeholder { color:#9ca3af; }
    #sc-send {
      width:36px; height:36px; border-radius:9px; flex-shrink:0;
      background:linear-gradient(135deg,#2563eb,#0891b2);
      border:none; color:#fff; font-size:16px; cursor:pointer;
      display:flex; align-items:center; justify-content:center;
      transition:all .15s;
    }
    #sc-send:hover  { transform:scale(1.06); }
    #sc-send:disabled { background:#e2e8f0; cursor:default; transform:none; }

    .sc-typing { display:flex; gap:4px; align-items:center; }
    .sc-dot { width:6px; height:6px; border-radius:50%; background:#93c5fd; }
    .sc-dot:nth-child(1){animation:sc-blink 1.2s 0s infinite}
    .sc-dot:nth-child(2){animation:sc-blink 1.2s .2s infinite}
    .sc-dot:nth-child(3){animation:sc-blink 1.2s .4s infinite}

    #sc-nokey {
      margin:16px 12px; background:#fef2f2; border:1px solid #fecaca;
      border-radius:10px; padding:12px 14px; font-size:12px; color:#dc2626;
      font-family:Inter,sans-serif; line-height:1.6;
    }
  `;
  PD.head.appendChild(style);

  // ── Inject HTML into parent page ────────────────────────────────────────
  const wrap = PD.createElement('div');
  wrap.id = 'sc-root';
  wrap.innerHTML = `
    <button id="sc-bubble" onclick="scToggle()">
      🤖<div id="sc-badge">AI</div>
    </button>

    <div id="sc-panel">
      <div id="sc-head">
        <div class="sc-av">🤖</div>
        <div class="sc-info">
          <div class="sc-name">Shopee AI Analyst</div>
          <div class="sc-stat">● Claude AI &nbsp;·&nbsp; knows your full dataset</div>
        </div>
        <button id="sc-close" onclick="scToggle()">×</button>
      </div>
      <div id="sc-msgs"></div>
      <div id="sc-chips"></div>
      <div id="sc-foot">
        <input id="sc-inp" placeholder="Ask about your Shopee data…"
               onkeydown="if(event.key==='Enter')scSend()"/>
        <button id="sc-send" onclick="scSend()">↑</button>
      </div>
    </div>
  `;
  PD.body.appendChild(wrap);

  // ── State ────────────────────────────────────────────────────────────────
  let scOpen    = false;
  let scLoading = false;
  let scHistory = [];   // {role, content}
  let scInited  = false;

  // ── Expose functions on parent window ───────────────────────────────────
  P.scToggle = function() {
    scOpen = !scOpen;
    PD.getElementById('sc-panel').classList.toggle('sc-open', scOpen);
    if (scOpen && !scInited) {
      scInited = true;
      if (!CFG.hasKey) {
        PD.getElementById('sc-msgs').innerHTML =
          '<div id="sc-nokey"><b>❌ API key missing</b><br>Add <code>ANTHROPIC_API_KEY</code> to Streamlit Secrets to enable AI chat.</div>';
        PD.getElementById('sc-foot').style.display = 'none';
      } else {
        scAddMsg('ai', "👋 Hi! I'm your Shopee analyst. Ask anything about your data — or tap a quick question below.");
        scRenderChips();
      }
    }
  };

  P.scSend = function() {
    const inp = PD.getElementById('sc-inp');
    const txt = inp.value.trim();
    if (!txt || scLoading) return;
    inp.value = '';
    scDispatch(txt);
  };

  function scRenderChips() {
    const box = PD.getElementById('sc-chips');
    box.innerHTML = '';
    CFG.quickQuestions.forEach(q => {
      const b = PD.createElement('button');
      b.className = 'sc-chip';
      b.textContent = q;
      b.onclick = () => { box.innerHTML = ''; scDispatch(q); };
      box.appendChild(b);
    });
  }

  function scAddMsg(role, text) {
    const div = PD.createElement('div');
    div.className = 'sc-msg ' + (role === 'user' ? 'sc-user' : 'sc-ai');

    if (role === 'user') {
      div.innerHTML = '<div class="sc-bub-user">' + scEsc(text) + '</div>';
    } else {
      if (text.includes('Action:')) {
        const parts = text.split('Action:');
        div.innerHTML =
          '<div class="sc-bub-ai">' + scEsc(parts[0].trim()) +
          '<div class="sc-action">⚡ Action: ' + scEsc(parts[1].trim()) + '</div></div>';
      } else {
        div.innerHTML = '<div class="sc-bub-ai">' + scEsc(text) + '</div>';
      }
    }

    PD.getElementById('sc-msgs').appendChild(div);
    scHistory.push({ role: role === 'user' ? 'user' : 'assistant', content: text });
    scScrollBottom();
  }

  function scShowTyping() {
    const div = PD.createElement('div');
    div.id = 'sc-typing'; div.className = 'sc-msg sc-ai';
    div.innerHTML = '<div class="sc-bub-ai"><div class="sc-typing"><div class="sc-dot"></div><div class="sc-dot"></div><div class="sc-dot"></div></div></div>';
    PD.getElementById('sc-msgs').appendChild(div);
    scScrollBottom();
  }
  function scHideTyping() {
    const t = PD.getElementById('sc-typing');
    if (t) t.remove();
  }
  function scScrollBottom() {
    const m = PD.getElementById('sc-msgs');
    m.scrollTop = m.scrollHeight;
  }
  function scEsc(t) {
    return t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\\n/g,'<br>');
  }

  async function scDispatch(text) {
    scAddMsg('user', text);
    scLoading = true;
    PD.getElementById('sc-send').disabled = true;
    scShowTyping();

    // Build messages — must start with user, strictly alternate
    const msgs = [];
    for (const m of scHistory.slice(-20)) {
      if (msgs.length === 0 && m.role !== 'user') continue;
      if (msgs.length > 0 && msgs[msgs.length-1].role === m.role) continue;
      msgs.push({ role: m.role, content: m.content });
    }

    try {
      const res = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': CFG.apiKey,
          'anthropic-version': '2023-06-01',
          'anthropic-dangerous-direct-browser-access': 'true'
        },
        body: JSON.stringify({
          model: 'claude-haiku-4-5-20251001',
          max_tokens: 500,
          system: CFG.systemPrompt,
          messages: msgs
        })
      });
      const data = await res.json();
      scHideTyping();
      if (data.content && data.content[0]) {
        scAddMsg('ai', data.content[0].text);
      } else if (data.error) {
        scAddMsg('ai', '❌ ' + data.error.type + ': ' + data.error.message);
      } else {
        scAddMsg('ai', '❌ Unexpected response — check API key in Secrets.');
      }
    } catch(e) {
      scHideTyping();
      scAddMsg('ai', '❌ Network error: ' + e.message);
    }

    scLoading = false;
    PD.getElementById('sc-send').disabled = false;
  }

})();
</script>
</body></html>
"""

components.html(CHAT_HTML, height=0, scrolling=False)
