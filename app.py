import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import os, requests, json, io
from datetime import date, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, HRFlowable, KeepTogether,
                                BaseDocTemplate, Frame, PageTemplate)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY

st.set_page_config(page_title="Shopee Commerce Intelligence", page_icon="⚡", layout="wide")

def get_api_key():
    try:
        k = st.secrets["ANTHROPIC_API_KEY"]
        if k and str(k).strip(): return str(k).strip()
    except Exception: pass
    return os.environ.get("ANTHROPIC_API_KEY", "")

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
    if legend: d["legend"] = dict(font=dict(color="#6b7280", size=10), bgcolor=None)
    d.update(kw)
    return d

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

monthly_data   = load_data()
weekly_data, categories_data, campaigns_data, cities_data, payments_data, brands_data, dow_data, SUMMARY = load_static()
daily_data     = load_daily()
actual_monthly = monthly_data[monthly_data["is_forecast"]==False]

def fmt_s(v):
    return f"S${v/1000:.1f}K" if v>=1000 else f"S${round(v)}"

def badge(p):
    if p is None or pd.isna(p): return ""
    p=float(p); arr="↑" if p>0 else("↓" if p<0 else"→")
    col=C["green"] if p>0 else(C["red"] if p<0 else"#64748b")
    return f'<span style="color:{col};font-weight:700;font-size:12px">{arr}{abs(p):.1f}%</span>'

# ── PDF Report Generator (1 page) ─────────────────────────────────────────────
def generate_pdf_report(monthly, brands, campaigns, summary,
                        selected_months=None,
                        report_title="Commerce Performance Report",
                        prepared_by="Analytics Team",
                        period_label="Oct 2025 – Jan 2026",
                        company="Shopee Singapore"):
    import importlib.util, sys, pathlib
    spec = importlib.util.spec_from_file_location("gen_report",
           pathlib.Path(__file__).parent / "gen_report.py")
    if spec is None:
        buf = io.BytesIO()
        buf.write(b"%PDF-1.4")
        buf.seek(0)
        return buf.read()
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.make_report(
        selected_months=selected_months,
        report_title=report_title,
        prepared_by=prepared_by,
        period_label=period_label,
        company=company,
    )


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
    if up: st.success(f"✓ {up.name}")

    st.markdown('<p style="font-size:11px;font-weight:700;color:#9ca3af;text-transform:uppercase;letter-spacing:.06em;margin:14px 0 6px">📥 Download Report</p>', unsafe_allow_html=True)

    all_yms  = ["Oct 2025","Nov 2025","Dec 2025","Jan 2026","Feb 2026*"]
    rpt_mons = st.multiselect("Months to include", all_yms, default=["Oct 2025","Nov 2025","Dec 2025","Jan 2026"],
                              key="rpt_months", label_visibility="visible")
    rpt_title  = st.text_input("Report title",   value="Commerce Performance Report", key="rpt_title")
    rpt_author = st.text_input("Prepared by",    value="Analytics Team", key="rpt_author")
    rpt_company = st.text_input("Company / Team", value="Shopee Singapore", key="rpt_company")

    if rpt_mons:
        first = rpt_mons[0].replace("*","").strip()
        last_m = rpt_mons[-1].replace("*","").strip()
        period_lbl = first + (" – " + last_m if last_m != first else "")
    else:
        period_lbl = "Custom Period"

    try:
        pdf_bytes = generate_pdf_report(
            monthly_data, brands_data, campaigns_data, SUMMARY,
            selected_months=rpt_mons if rpt_mons else None,
            report_title=rpt_title or "Commerce Performance Report",
            prepared_by=rpt_author or "Analytics Team",
            period_label=period_lbl,
            company=rpt_company or "Shopee Singapore",
        )
        st.download_button(
            label="⬇ Download Executive PDF",
            data=pdf_bytes,
            file_name=f"shopee_report_{date.today().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    except Exception as e:
        st.error(f"PDF error: {e}")

    st.markdown('<p style="font-size:10px;color:#cbd5e1;text-align:center;margin-top:16px">Shopee Commerce Intelligence</p>', unsafe_allow_html=True)

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
    st.markdown('<div class="section-sub">Adjust the 4 key levers — projection updates instantly</div>', unsafe_allow_html=True)

    BASE_ORDERS   = 200
    BASE_AOV      = 442
    BASE_MONTHS   = ["Feb","Mar","Apr","May","Jun","Jul"]
    BASE_VOUCHER  = 48.75   # baseline voucher rate for elasticity calc

    st.markdown('<div class="chart-card"><div class="chart-title">📐 Business Levers</div><div class="chart-sub">Drag to model your strategy</div>', unsafe_allow_html=True)
    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        order_growth = st.slider("📦 Monthly order growth %", -20, 40, 5, 1, key="sp_ord")
        st.caption("Baseline: ~5%/mo")
    with col_b:
        aov_change = st.slider("💰 AOV change %", -20, 30, 0, 1, key="sp_aov")
        st.caption("Baseline: S$442")
    with col_c:
        repeat_rate = st.slider("🔁 Repeat rate %", 1.0, 20.0, 3.6, 0.1, key="sp_rep", format="%.1f%%")
        st.caption("Baseline: 3.6% (low)")
    with col_d:
        voucher_rate = st.slider("🎫 Voucher usage %", 20.0, 70.0, 48.75, 0.25, key="sp_vr", format="%.2f%%")
        st.caption("Baseline: 48.75%")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Projection model ─────────────────────────────────────────────────────
    # Voucher elasticity: customers are price-sensitive.
    # Every 10pp drop in voucher rate → ~4% fewer orders (some buyers need the incentive).
    # Every 10pp rise → ~3% more orders (vouchers attract deal-seekers).
    def voucher_order_multiplier(vr):
        delta_pp = vr - BASE_VOUCHER           # how many pp above/below baseline
        if delta_pp >= 0:
            return 1 + (delta_pp / 10) * 0.03  # more vouchers → slightly more orders
        else:
            return 1 + (delta_pp / 10) * 0.04  # fewer vouchers → fewer orders

    def sp_project(ord_gr, aov_ch, vr, rep):
        rows   = []
        orders = float(BASE_ORDERS) * voucher_order_multiplier(vr)
        aov    = BASE_AOV * (1 + aov_ch / 100)
        vd     = 10   # fixed avg discount S$10
        for mo in BASE_MONTHS:
            orders      = max(40, orders * (1 + ord_gr / 100))
            vcost       = orders * (vr / 100) * vd
            gross       = orders * aov
            repeat_rev  = gross * (rep / 100) * 0.15
            net         = gross + repeat_rev - vcost
            rows.append({"month": mo, "orders": int(orders), "aov": round(aov),
                         "voucher_cost": round(vcost), "net": round(net)})
        return pd.DataFrame(rows)

    proj      = sp_project(order_growth, aov_change, voucher_rate, repeat_rate)
    total_rev = proj["net"].sum()
    total_ord = proj["orders"].sum()
    total_vc  = proj["voucher_cost"].sum()
    vs_base   = (total_rev - 530964) / 530964 * 100

    # ── 4 KPI summary ────────────────────────────────────────────────────────
    kc1, kc2, kc3, kc4 = st.columns(4)
    vc_col = C["green"] if vs_base >= 0 else C["red"]
    for col, icon, label, val, sub, color, bg, border in [
        (kc1,"💰","6-Month Revenue",   fmt_s(total_rev),    "Your projection",      C["blue"],  "#eff6ff","#bfdbfe"),
        (kc2,"📦","Total Orders",      f"{total_ord:,}",    "6 months",             C["cyan"],  "#ecfeff","#a5f3fc"),
        (kc3,"🎫","Voucher Cost",      fmt_s(int(total_vc)),"Discount spend",       C["amber"], "#fffbeb","#fde68a"),
        (kc4,"📈","vs Flat Baseline",  f"{'+'if vs_base>=0 else ''}{vs_base:.1f}%","vs S$530K", vc_col,
             "#f0fdf4" if vs_base>=0 else "#fef2f2",
             "#bbf7d0" if vs_base>=0 else "#fecaca"),
    ]:
        with col:
            st.markdown(
                f'<div style="background:{bg};border:1px solid {border};border-radius:12px;padding:16px 18px;margin-bottom:10px">'
                f'<div style="font-size:20px;margin-bottom:6px">{icon}</div>'
                f'<div style="font-size:20px;font-weight:900;color:{color}">{val}</div>'
                f'<div style="font-size:10px;color:#6b7280;font-weight:700;text-transform:uppercase;margin:4px 0 2px">{label}</div>'
                f'<div style="font-size:11px;color:#9ca3af">{sub}</div></div>',
                unsafe_allow_html=True
            )

    # ── Projection chart ──────────────────────────────────────────────────────
    st.markdown('<div class="chart-card"><div class="chart-title">📈 6-Month Revenue Projection</div><div class="chart-sub">Dotted = historical bridge from Oct–Jan actuals</div>', unsafe_allow_html=True)
    fig = go.Figure()
    hist_m = ["Oct","Nov","Dec","Jan", BASE_MONTHS[0]]
    hist_v = [88216, 94439, 96386, 74936, proj["net"].iloc[0]]
    fig.add_trace(go.Scatter(x=hist_m, y=hist_v, mode="lines",
        line=dict(color="#94a3b8", width=1.5, dash="dot"), name="Historical Bridge", showlegend=True))
    fig.add_trace(go.Scatter(x=proj["month"], y=proj["net"],
        mode="lines+markers", name="Your Projection",
        line=dict(color=C["blue"], width=2.5), marker=dict(size=8, color=C["blue"]),
        fill="tozeroy", fillcolor="rgba(37,99,235,0.07)"))
    fig.update_layout(**PL(height=250, legend=True))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Monthly table + lever sensitivity ─────────────────────────────────────
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
        st.dataframe(tbl[["month","Revenue","MoM","Orders","AOV","Voucher Cost"]].rename(columns={"month":"Month"}),
                     use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="chart-card"><div class="chart-title">⚡ What Moves Revenue Most?</div><div class="chart-sub">Impact of nudging each lever one step from current</div>', unsafe_allow_html=True)
        base_total = proj["net"].sum()
        def nudge(**kw):
            return sp_project(
                kw.get("og", order_growth), kw.get("ac", aov_change),
                kw.get("vr", voucher_rate), kw.get("rr", repeat_rate)
            )["net"].sum()

        levers = [
            ("📦 +5% orders",       nudge(og=order_growth+5)                 - base_total),
            ("💎 +5% AOV",          nudge(ac=aov_change+5)                   - base_total),
            ("🔁 +3% repeat rate",  nudge(rr=repeat_rate+3)                  - base_total),
            ("🎫 -5% voucher rate", nudge(vr=max(20, voucher_rate-5))        - base_total),
        ]
        levers.sort(key=lambda x: x[1], reverse=True)
        max_impact = max(abs(v) for _, v in levers) or 1
        for name, impact in levers:
            bw   = int(abs(impact)/max_impact*100)
            col_ = C["green"] if impact >= 0 else C["red"]
            bg_  = "#f0fdf4" if impact >= 0 else "#fef2f2"
            bd_  = "#bbf7d0" if impact >= 0 else "#fecaca"
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:10px;padding:10px 0;border-bottom:1px solid #f8fafc">'
                f'<div style="width:170px;font-size:12px;color:#374151;font-weight:500;flex-shrink:0">{name}</div>'
                f'<div style="flex:1;height:8px;background:#f1f5f9;border-radius:4px">'
                f'<div style="height:100%;width:{bw}%;background:{col_};border-radius:4px"></div></div>'
                f'<div style="width:85px;text-align:right">'
                f'<span style="background:{bg_};border:1px solid {bd_};border-radius:6px;padding:3px 8px;font-size:11px;font-weight:700;color:{col_}">'
                f'{"+" if impact>=0 else ""}{fmt_s(int(abs(impact)))}</span></div></div>',
                unsafe_allow_html=True
            )
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Inline Q&A ────────────────────────────────────────────────────────────
    st.markdown('<div class="chart-card"><div class="chart-title">🤖 Ask the Analyst</div><div class="chart-sub">Click any question for an instant answer</div>', unsafe_allow_html=True)
    SP_QA = {
        "Is my projection realistic?": (
            "Yes — your settings are grounded in real data. Your Oct–Jan monthly average was S$88,494, "
            "and with positive order growth and AOV adjustments applied, the 6-month outlook is achievable. "
            "The key risk is sustaining compound order growth — even 5% month-on-month adds up significantly "
            "and assumes no major supply or demand disruption.",
            "Validate your order growth assumption against last year's Feb–Jul seasonality before committing budget."
        ),
        "Which lever should I focus on first?": (
            "AOV improvement delivers the highest return because it applies to every single order. "
            "A 5% AOV increase on 200 monthly orders adds roughly S$4,400/month — S$26,400 over 6 months. "
            "Your repeat rate at 3.6% is also far below the industry average of 15–20%, making it your biggest "
            "untapped lever for recurring revenue without extra acquisition cost.",
            "Focus on upselling higher-value Electronics bundles this week to lift AOV immediately."
        ),
        "What's the risk if orders drop 10%?": (
            "A 10% order drop from 200/month would reduce monthly revenue by approximately S$8,800, "
            "totalling S$53,000 lost over 6 months. Given your 64% LG concentration, any supply disruption "
            "compounds this quickly. Note: lower voucher rates also reduce orders slightly due to price elasticity.",
            "Build a 10% demand buffer by diversifying campaigns across at least 3 channels this month."
        ),
        "How can I reduce voucher leakage?": (
            "Your voucher usage sits at 48.75% — nearly half of all orders use a voucher averaging S$10 discount. "
            "Dropping usage to 40% saves approximately S$3,500 over 6 months but will also reduce orders slightly "
            "as some price-sensitive buyers drop off. Restricting vouchers to new customers or setting a S$500 "
            "minimum order value protects margin without losing high-intent buyers.",
            "Set a S$500 minimum order threshold for voucher redemption this week and monitor conversion impact."
        ),
        "What AOV should I target for S$600K revenue?": (
            "To hit S$600K over 6 months with current order growth, you'd need a monthly AOV of approximately "
            "S$480–S$500 — around 8–13% above your current S$442 baseline. "
            "This is achievable by shifting the product mix toward higher-value Electronics bundles. "
            "Notably, your best week already hit S$738 AOV in W05 January, proving high-value orders are very possible.",
            "Create 3 Electronics bundle offers at S$500+ this week to start shifting the AOV mix upward."
        ),
        "Why do orders change when I adjust vouchers?": (
            "Voucher rate affects orders because customers are price-sensitive — vouchers are a demand driver, "
            "not just a cost. In this model, every 10pp drop in voucher usage reduces orders by ~4% as some "
            "deal-seeking buyers drop off. Conversely, increasing vouchers attracts ~3% more orders. "
            "This reflects real Shopee behaviour where promotions drive significant incremental volume.",
            "Test a 5pp voucher reduction with a parallel loyalty incentive to offset the order drop."
        ),
    }
    if "sp_chat" not in st.session_state: st.session_state.sp_chat = []
    sp_cols = st.columns(3)
    for i, q in enumerate(SP_QA.keys()):
        if sp_cols[i % 3].button(q, key=f"spq_{i}", use_container_width=True):
            st.session_state.sp_pending = q
    for msg in st.session_state.sp_chat:
        role = msg["role"]
        with st.chat_message(role, avatar="🤖" if role == "assistant" else None):
            txt = msg["content"]
            if role == "assistant" and "|||" in txt:
                body, action = txt.split("|||", 1)
                st.write(body.strip())
                st.markdown(f'<div style="background:#fffbeb;border-left:3px solid #d97706;padding:8px 12px;margin-top:6px;font-size:12px;color:#92400e;font-weight:600;border-radius:0 6px 6px 0">⚡ Action: {action.strip()}</div>', unsafe_allow_html=True)
            else:
                st.write(txt)
    if hasattr(st.session_state, "sp_pending"):
        q = st.session_state.sp_pending
        del st.session_state.sp_pending
        last_user = next((m["content"] for m in reversed(st.session_state.sp_chat) if m["role"] == "user"), None)
        if q != last_user:
            st.session_state.sp_chat.append({"role": "user", "content": q})
            body, action = SP_QA[q]
            st.session_state.sp_chat.append({"role": "assistant", "content": f"{body}|||{action}"})
            st.rerun()
    if len(st.session_state.sp_chat) > 1:
        if st.button("🗑️ Clear", key="sp_clr"):
            st.session_state.sp_chat = []
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# FLOATING AI CHATBOT
# ══════════════════════════════════════════════════════════════════════════════
HARDCODED_QA = {
    "What's causing the Jan revenue dip?": (
        "January dropped 22.3% to S$74,936 — the steepest month-on-month fall in the period. "
        "This is a classic post-holiday slowdown after December's S$96,386 peak, with order volume "
        "falling from 204 to 177 and no major SG shopping events to sustain demand. "
        "The good news: February is forecast to recover to S$82,000 (+9.4%), suggesting the dip is seasonal, not structural.",
        "Run a mid-January flash sale on Wednesdays — your highest-revenue day — to counter the seasonal slowdown next year."
    ),
    "Which campaign has the best ROI?": (
        "Double Day is your top performer at S$89,029 revenue across 172 orders — an AOV of S$518, "
        "18% higher revenue than the next best campaign Mega Campaign at S$75,121. "
        "The 11.11 Mega Sale also delivered a massive 2.8x daily revenue multiplier on Nov 11. "
        "Flash Sale has the lowest revenue at S$63,142 and the fewest orders (136), making it your least efficient campaign.",
        "Prioritise Double Day budget in your next campaign calendar and replicate its bundle structure for other campaigns."
    ),
    "Top 3 growth opportunities?": (
        "First: repeat purchase rate is just 3.6% vs industry average of 15-20% — a loyalty programme "
        "could unlock S$40K+ in incremental revenue from your existing 772 customers. "
        "Second: Jurong is 35% below Woodlands at S$44,898 — geo-targeted promos could close that gap fast. "
        "Third: Fashion and Beauty combined are only 10% of revenue despite 312 orders — higher AOV products here could shift the mix significantly.",
        "Launch a loyalty points programme this week specifically targeting your 772 existing customers with a repeat purchase incentive."
    ),
    "Best day to run flash sales?": (
        "Wednesday is your strongest day at S$62,817 — 35% above Thursday which is your worst at S$41,193. "
        "Wednesday buyers show the highest purchase intent mid-week, and the gap vs other days is consistent across all months. "
        "Pairing a 24-hour Wednesday flash sale with a countdown timer drives urgency and capitalises on peak traffic.",
        "Schedule your next flash sale for Wednesday with a 10am launch countdown — test a 24-hour window first."
    ),
    "Why is Jurong underperforming?": (
        "Jurong generates S$44,898 — 35% below top-performing Woodlands at S$67,353, despite 116 orders. "
        "The AOV gap is significant: Jurong buyers are purchasing lower-value items, suggesting a demographic "
        "or product mix mismatch rather than a volume problem. "
        "Woodlands likely benefits from higher Electronics basket sizes driven by LG product affinity.",
        "Run a Jurong-specific Electronics bundle offer this week at S$450+ to test whether AOV lifts with the right product push."
    ),
    "What's our biggest risk right now?": (
        "Your biggest risk is LG brand concentration — 64% of revenue (S$227,248) comes from a single brand. "
        "Any LG stock issue, price change, or competitor promotion could immediately hit the majority of your revenue. "
        "The 3.6% repeat rate compounds this: you're heavily dependent on new customer acquisition to sustain volume, "
        "with almost no recurring revenue buffer to absorb a demand shock.",
        "Onboard 2-3 new Electronics brands this month to reduce LG dependency below 50% of revenue."
    ),
}

CHAT_QS = list(HARDCODED_QA.keys())
qa_js_entries = []
for q, (body, action) in HARDCODED_QA.items():
    q_esc = q.replace("'", "\\'")
    body_esc = body.replace("'", "\\'").replace("\n", " ")
    action_esc = action.replace("'", "\\'").replace("\n", " ")
    qa_js_entries.append(f"  '{q_esc}': {{ body: '{body_esc}', action: '{action_esc}' }}")
QA_JS = "{\n" + ",\n".join(qa_js_entries) + "\n}"

CHAT_HTML = """<!DOCTYPE html><html><head><style>body{margin:0;padding:0;background:transparent;}</style></head><body><script>
(function() {
  const QUESTIONS = """ + json.dumps(CHAT_QS) + """;
  const QA = """ + QA_JS + """;
  const P = window.parent, PD = P.document;
  if (PD.getElementById('sc-bubble')) return;
  const style = PD.createElement('style');
  style.id = 'sc-styles';
  style.textContent = `
    @keyframes sc-slideUp { from{opacity:0;transform:translateY(14px) scale(.97)} to{opacity:1;transform:translateY(0) scale(1)} }
    @keyframes sc-msgIn   { from{opacity:0;transform:translateY(5px)} to{opacity:1;transform:translateY(0)} }
    @keyframes sc-blink   { 0%,100%{opacity:.25} 50%{opacity:1} }
    @keyframes sc-glow    { 0%,100%{box-shadow:0 4px 20px rgba(37,99,235,.45)} 50%{box-shadow:0 4px 32px rgba(37,99,235,.8)} }
    #sc-bubble{position:fixed;bottom:24px;right:24px;z-index:99999;width:54px;height:54px;border-radius:50%;border:none;cursor:pointer;background:linear-gradient(135deg,#2563eb,#0891b2);font-size:22px;display:flex;align-items:center;justify-content:center;animation:sc-glow 3s ease-in-out infinite;transition:transform .18s}
    #sc-bubble:hover{transform:scale(1.1)}
    #sc-badge{position:absolute;top:-2px;right:-2px;width:17px;height:17px;border-radius:50%;background:#16a34a;border:2px solid #fff;font-size:7px;font-weight:800;color:#fff;display:flex;align-items:center;justify-content:center;pointer-events:none}
    #sc-panel{position:fixed;bottom:88px;right:24px;z-index:99998;width:370px;height:520px;background:#fff;border:1px solid #e2e8f0;border-radius:18px;display:none;flex-direction:column;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,.18)}
    #sc-panel.sc-open{display:flex;animation:sc-slideUp .22s ease both}
    #sc-head{background:linear-gradient(135deg,#2563eb,#0891b2);padding:12px 15px;display:flex;align-items:center;gap:10px;flex-shrink:0}
    #sc-head .sc-av{width:34px;height:34px;border-radius:50%;background:rgba(255,255,255,.18);display:flex;align-items:center;justify-content:center;font-size:17px;flex-shrink:0}
    #sc-head .sc-name{font-weight:700;font-size:13px;color:#fff;font-family:Inter,sans-serif}
    #sc-head .sc-stat{font-size:10px;color:rgba(255,255,255,.8);margin-top:2px;font-family:Inter,sans-serif}
    #sc-close{background:transparent;border:none;color:rgba(255,255,255,.7);font-size:20px;cursor:pointer;padding:2px 6px;border-radius:5px}
    #sc-close:hover{color:#fff;background:rgba(255,255,255,.15)}
    #sc-msgs{flex:1;overflow-y:auto;padding:12px 12px 6px;display:flex;flex-direction:column;gap:8px}
    #sc-msgs::-webkit-scrollbar{width:3px}
    #sc-msgs::-webkit-scrollbar-thumb{background:#e2e8f0;border-radius:3px}
    .sc-msg{max-width:87%;animation:sc-msgIn .18s ease both;font-family:Inter,sans-serif}
    .sc-msg.sc-user{align-self:flex-end}
    .sc-msg.sc-ai{align-self:flex-start}
    .sc-bub-user{background:linear-gradient(135deg,#2563eb,#1d4ed8);color:#fff;padding:9px 13px;border-radius:14px 14px 3px 14px;font-size:12px;line-height:1.65}
    .sc-bub-ai{background:#f8fafc;border:1px solid #e2e8f0;color:#1e293b;padding:10px 13px;border-radius:14px 14px 14px 3px;font-size:12px;line-height:1.75}
    .sc-action{background:#fffbeb;border-left:3px solid #d97706;padding:7px 10px;margin-top:8px;font-size:11px;color:#92400e;font-weight:600;border-radius:0 6px 6px 0}
    #sc-chips{padding:0 10px 8px;display:flex;flex-wrap:wrap;gap:5px;flex-shrink:0}
    .sc-chip{background:#eff6ff;border:1px solid #bfdbfe;color:#1d4ed8;padding:4px 10px;border-radius:20px;font-size:10px;cursor:pointer;transition:all .12s;white-space:nowrap}
    .sc-chip:hover{background:#dbeafe;border-color:#93c5fd}
    .sc-typing{display:flex;gap:4px;align-items:center}
    .sc-dot{width:6px;height:6px;border-radius:50%;background:#93c5fd}
    .sc-dot:nth-child(1){animation:sc-blink 1.2s 0s infinite}
    .sc-dot:nth-child(2){animation:sc-blink 1.2s .2s infinite}
    .sc-dot:nth-child(3){animation:sc-blink 1.2s .4s infinite}
  `;
  PD.head.appendChild(style);
  const wrap = PD.createElement('div');
  wrap.id = 'sc-root';
  wrap.innerHTML = `<button id="sc-bubble" onclick="scToggle()">🤖<div id="sc-badge">AI</div></button>
    <div id="sc-panel">
      <div id="sc-head">
        <div class="sc-av">🤖</div>
        <div style="flex:1"><div class="sc-name">Shopee AI Analyst</div><div class="sc-stat">● Instant insights · tap a question below</div></div>
        <button id="sc-close" onclick="scToggle()">×</button>
      </div>
      <div id="sc-msgs"></div>
      <div id="sc-chips"></div>
    </div>`;
  PD.body.appendChild(wrap);
  let scOpen=false,scInited=false,scLoading=false;
  P.scToggle=function(){scOpen=!scOpen;PD.getElementById('sc-panel').classList.toggle('sc-open',scOpen);if(scOpen&&!scInited){scInited=true;scAddMsg('ai',"👋 Hi! I'm your Shopee analyst. Tap a question below to get instant insights.");scRenderChips();}};
  function scRenderChips(){const box=PD.getElementById('sc-chips');box.innerHTML='';QUESTIONS.forEach(q=>{const b=PD.createElement('button');b.className='sc-chip';b.textContent=q;b.onclick=()=>{scDispatch(q);};box.appendChild(b);});}
  function scAddMsg(role,text,actionText){const div=PD.createElement('div');div.className='sc-msg '+(role==='user'?'sc-user':'sc-ai');if(role==='user'){div.innerHTML='<div class="sc-bub-user">'+scEsc(text)+'</div>';}else{let inner='<div class="sc-bub-ai">'+scEsc(text);if(actionText)inner+='<div class="sc-action">⚡ Action: '+scEsc(actionText)+'</div>';inner+='</div>';div.innerHTML=inner;}PD.getElementById('sc-msgs').appendChild(div);scScrollBottom();}
  function scShowTyping(){const div=PD.createElement('div');div.id='sc-typing';div.className='sc-msg sc-ai';div.innerHTML='<div class="sc-bub-ai"><div class="sc-typing"><div class="sc-dot"></div><div class="sc-dot"></div><div class="sc-dot"></div></div></div>';PD.getElementById('sc-msgs').appendChild(div);scScrollBottom();}
  function scHideTyping(){const t=PD.getElementById('sc-typing');if(t)t.remove();}
  function scScrollBottom(){const m=PD.getElementById('sc-msgs');m.scrollTop=m.scrollHeight;}
  function scEsc(t){return t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\\n/g,'<br>');}
  function scDispatch(q){if(scLoading)return;scAddMsg('user',q);scLoading=true;scShowTyping();setTimeout(()=>{scHideTyping();const qa=QA[q];if(qa){scAddMsg('ai',qa.body,qa.action);}else{scAddMsg('ai',"I don't have a preset answer for that. Try one of the questions below!");}scLoading=false;},900);}
})();
</script></body></html>"""

components.html(CHAT_HTML, height=0, scrolling=False)
