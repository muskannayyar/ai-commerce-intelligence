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
                                BaseDocTemplate, Frame, PageTemplate,
                                PageBreak, Flowable)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY

st.set_page_config(page_title="Shopee Commerce Intelligence", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

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

# ── PDF Report Generator — single-page crisp canvas ──────────────────────────
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors as rl_colors
from reportlab.lib.units import cm, mm
from reportlab.platypus import (Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, BaseDocTemplate, Frame, PageTemplate,
    PageBreak, Flowable)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas as _pdfgen

_C = {
    "navy":  rl_colors.HexColor("#0f2744"),
    "blue":  rl_colors.HexColor("#1d4ed8"),
    "lblue": rl_colors.HexColor("#dbeafe"),
    "steel": rl_colors.HexColor("#334155"),
    "dgray": rl_colors.HexColor("#64748b"),
    "lgray": rl_colors.HexColor("#f8fafc"),
    "mgray": rl_colors.HexColor("#e2e8f0"),
    "grn":   rl_colors.HexColor("#15803d"),
    "lgrn":  rl_colors.HexColor("#dcfce7"),
    "red":   rl_colors.HexColor("#b91c1c"),
    "lred":  rl_colors.HexColor("#fee2e2"),
    "amb":   rl_colors.HexColor("#b45309"),
    "lamb":  rl_colors.HexColor("#fef3c7"),
    "purp":  rl_colors.HexColor("#6d28d9"),
    "teal":  rl_colors.HexColor("#0e7490"),
    "lteal": rl_colors.HexColor("#cffafe"),
    "blk":   rl_colors.HexColor("#0f172a"),
    "wht":   rl_colors.white,
    "acc":   rl_colors.HexColor("#f97316"),
}

def generate_pdf_report(monthly, brands, campaigns, summary,
                        selected_months=None,
                        report_title="Commerce Performance Report",
                        prepared_by="Analytics Team",
                        period_label="Oct 2025 – Jan 2026",
                        company="Shopee Singapore"):

    _all_m = pd.DataFrame([
        {"ym":"Oct 2025","revenue":88216,"orders":218,"aov":405,"voucher_rate":50.0,"rev_mom":None,"ord_mom":None,"aov_mom":None,"is_forecast":False},
        {"ym":"Nov 2025","revenue":94439,"orders":201,"aov":470,"voucher_rate":55.2,"rev_mom":7.1,"ord_mom":-7.8,"aov_mom":16.0,"is_forecast":False},
        {"ym":"Dec 2025","revenue":96386,"orders":204,"aov":472,"voucher_rate":45.1,"rev_mom":2.1,"ord_mom":1.5,"aov_mom":0.4,"is_forecast":False},
        {"ym":"Jan 2026","revenue":74936,"orders":177,"aov":423,"voucher_rate":44.1,"rev_mom":-22.3,"ord_mom":-13.2,"aov_mom":-10.4,"is_forecast":False},
        {"ym":"Feb 2026*","revenue":82000,"orders":188,"aov":436,"voucher_rate":46.0,"rev_mom":9.4,"ord_mom":6.2,"aov_mom":3.1,"is_forecast":True},
    ])
    if selected_months:
        _m = _all_m[_all_m["ym"].isin(selected_months)].reset_index(drop=True)
    else:
        _m = _all_m[_all_m["is_forecast"]==False].reset_index(drop=True)
    _act = _m[_m["is_forecast"]==False].reset_index(drop=True)
    tot_rev = int(_act["revenue"].sum())
    tot_ord = int(_act["orders"].sum())
    avg_aov = tot_rev/tot_ord if tot_ord else 0
    last    = _act.iloc[-1]

    _brands = pd.DataFrame([
        {"name":"LG","revenue":227248,"orders":158,"delta":12.3},
        {"name":"Philips","revenue":67817,"orders":164,"delta":4.1},
        {"name":"Nike","revenue":26834,"orders":147,"delta":-2.8},
        {"name":"Anker","revenue":24707,"orders":166,"delta":-6.2},
        {"name":"COSRX","revenue":7371,"orders":165,"delta":-15.4},
    ])
    _camps = pd.DataFrame([
        {"name":"Double Day","revenue":89029,"orders":172,"spend":18000,"delta":18.4},
        {"name":"Mega Campaign","revenue":75121,"orders":168,"spend":22000,"delta":5.2},
        {"name":"Brand Day","revenue":68307,"orders":161,"spend":14000,"delta":-3.1},
        {"name":"Flash Sale","revenue":63142,"orders":136,"spend":8000,"delta":-8.6},
    ])

    buf = io.BytesIO()
    PW, PH = A4          # 595.28 x 841.89 pt
    c = _pdfgen.Canvas(buf, pagesize=A4)

    # ── helpers ──────────────────────────────────────────────────────────────
    def fv(v):  return "S${:,.0f}".format(v)
    def fk(v):  return "S${:.1f}K".format(v/1000)
    def pct(v):
        if v is None or (isinstance(v,float) and pd.isna(v)): return "—"
        return ("▲ +" if v>0 else "▼ ") + "{:.1f}%".format(v)
    def pctc(v,inv=False):
        if v is None or (isinstance(v,float) and pd.isna(v)): return _C["dgray"]
        return _C["grn"] if (v>=0)!=inv else _C["red"]

    def rect(x,y,w,h,fill=None,stroke=None,radius=0):
        c.saveState()
        if fill: c.setFillColor(fill)
        if stroke: c.setStrokeColor(stroke)
        if radius: c.roundRect(x,y,w,h,radius,fill=1 if fill else 0,stroke=1 if stroke else 0)
        else: c.rect(x,y,w,h,fill=1 if fill else 0,stroke=1 if stroke else 0)
        c.restoreState()

    def txt(s,x,y,font="Helvetica",size=8,color=None,align="left"):
        c.saveState()
        c.setFont(font,size)
        if color: c.setFillColor(color)
        if align=="right": c.drawRightString(x,y,str(s))
        elif align=="center": c.drawCentredString(x,y,str(s))
        else: c.drawString(x,y,str(s))
        c.restoreState()

    def hline(x,y,w,color=None,width=0.5):
        c.saveState()
        c.setLineWidth(width)
        if color: c.setStrokeColor(color)
        c.line(x,y,x+w,y)
        c.restoreState()

    def mini_bar(x,y,w,h,val,maxv,fill):
        rect(x,y,w,h,fill=_C["mgray"])
        pct_w = max(0,min(1,val/maxv))*w if maxv else 0
        rect(x,y,pct_w,h,fill=fill)

    # ── LAYOUT CONSTANTS ─────────────────────────────────────────────────────
    MG = 22          # margin pt
    CW = PW - 2*MG   # content width  551
    Y  = PH          # current Y (top of page)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # HEADER BAND
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    HDR_H = 48
    rect(0, PH-HDR_H, PW, HDR_H, fill=_C["navy"])
    rect(0, PH-HDR_H-2, PW, 2, fill=_C["acc"])

    txt(company.upper()+"  ·  "+report_title.upper(),
        MG, PH-HDR_H+17, "Helvetica-Bold", 9, _C["wht"])
    txt("CONFIDENTIAL  ·  "+period_label+"  ·  Prepared by: "+prepared_by,
        PW-MG, PH-HDR_H+17, "Helvetica", 7.5, rl_colors.HexColor("#93c5fd"), "right")
    txt("Generated: "+date.today().strftime("%d %B %Y"),
        PW-MG, PH-HDR_H+6, "Helvetica", 7, _C["dgray"], "right")

    Y = PH - HDR_H - 10   # working Y from here downward

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # KPI SCORECARD  (6 tiles in one row)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    KPI_H = 54
    KW    = CW/6 - 3

    kpis = [
        ("GMV",             fv(tot_rev),          last["rev_mom"],  False, "Total revenue"),
        ("Avg Order Value",  "S${:.0f}".format(avg_aov), last["aov_mom"], False, "Revenue ÷ orders"),
        ("Total Orders",    "{:,}".format(tot_ord), last["ord_mom"],  False, "Orders placed"),
        ("Avg Delivery",    "{:.1f}d".format(summary["avgDelivery"]), -2.9, True,  "Target <2 days"),
        ("Repeat Rate",     "{}%".format(summary["repeatRate"]),  0.2,   False, "Industry avg 15–20%"),
        ("Voucher Rate",    "{}%".format(summary["voucherRate"]), -3.1,  True,  "Lower = less leakage"),
    ]
    for i,(lbl,val,dv,inv,hint) in enumerate(kpis):
        kx = MG + i*(KW+3.6)
        rect(kx, Y-KPI_H, KW, KPI_H, fill=_C["lgray"], radius=4)
        txt(lbl,   kx+KW/2, Y-11,  "Helvetica",      6.5, _C["dgray"],  "center")
        txt(val,   kx+KW/2, Y-27,  "Helvetica-Bold", 12,  _C["navy"],   "center")
        dv_col = pctc(dv,inv)
        txt(pct(dv) if dv is not None else "—",
                   kx+KW/2, Y-38,  "Helvetica-Bold", 7.5, dv_col,       "center")
        txt(hint,  kx+KW/2, Y-49,  "Helvetica",      6,   _C["dgray"],  "center")

    Y -= (KPI_H + 9)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TWO-COLUMN LAYOUT: Monthly Trend (left) | Brand Performance (right)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    COL1 = CW * 0.52
    COL2 = CW * 0.46
    GAP  = CW * 0.02
    LX   = MG
    RX   = MG + COL1 + GAP

    # --- Section label helper ---
    def sec_label(x,y,w,label,bg=None):
        bg = bg or _C["navy"]
        rect(x,y,w,13,fill=bg,radius=2)
        txt(label, x+6, y+3.5, "Helvetica-Bold", 7, _C["wht"])

    # ── LEFT: Monthly Trend table ─────────────────────────────────────────
    sec_label(LX, Y, COL1, "MONTHLY PERFORMANCE TREND")
    Y2 = Y - 15  # table starts here

    MON_H = 13   # row height
    mo_cols = [("Month",0.22),("Rev",0.19),("MoM",0.15),("Ord",0.13),("AOV",0.14),("Voucher",0.13),]
    mo_cw   = [COL1*p for _,p in mo_cols]

    # header row
    rx = LX
    rect(LX, Y2-MON_H, COL1, MON_H, fill=_C["navy"])
    for j,(lbl,_) in enumerate(mo_cols):
        txt(lbl, rx+mo_cw[j]/2, Y2-MON_H+4, "Helvetica-Bold", 6.5, _C["wht"], "center")
        rx += mo_cw[j]
    Y2 -= MON_H

    for ri, (_, r) in enumerate(_act.iterrows()):
        bg = _C["lgray"] if ri%2==0 else _C["wht"]
        rect(LX, Y2-MON_H, COL1, MON_H, fill=bg)
        vals = [
            (r["ym"],      False, _C["navy"]),
            (fk(r["revenue"]), True, _C["blk"]),
            (pct(r["rev_mom"]), True, pctc(r["rev_mom"])),
            (str(r["orders"]), False, _C["blk"]),
            ("S${}".format(r["aov"]), False, _C["blk"]),
            ("{}%".format(r["voucher_rate"]), False, _C["steel"]),
        ]
        rx2 = LX
        for j,(v,bold,col) in enumerate(vals):
            fn = "Helvetica-Bold" if bold else "Helvetica"
            txt(v, rx2+mo_cw[j]/2, Y2-MON_H+4, fn, 6.5 if j>0 else 6.5, col, "center")
            rx2 += mo_cw[j]
        hline(LX, Y2-MON_H, COL1, _C["mgray"])
        Y2 -= MON_H

    # Forecast row if present
    if any(_m["is_forecast"]):
        fr = _m[_m["is_forecast"]].iloc[0]
        rect(LX, Y2-MON_H, COL1, MON_H, fill=_C["lpurp"] if hasattr(_C,"lpurp") else rl_colors.HexColor("#ede9fe"))
        fcast_vals = [
            (fr["ym"]+" (F)", False, rl_colors.HexColor("#6d28d9")),
            (fk(fr["revenue"]), True, rl_colors.HexColor("#6d28d9")),
            (pct(fr["rev_mom"]), True, pctc(fr["rev_mom"])),
            (str(fr["orders"]), False, _C["steel"]),
            ("S${}".format(fr["aov"]), False, _C["steel"]),
            ("{}%".format(fr["voucher_rate"]), False, _C["steel"]),
        ]
        rx2 = LX
        for j,(v,bold,col) in enumerate(fcast_vals):
            fn = "Helvetica-Bold" if bold else "Helvetica"
            txt(v, rx2+mo_cw[j]/2, Y2-MON_H+4, fn, 6.5, col, "center")
            rx2 += mo_cw[j]
        Y2 -= MON_H

    # outline
    rect(LX, Y2, COL1, Y-15-Y2, stroke=_C["mgray"], radius=0)

    # ── RIGHT: Brand Performance ──────────────────────────────────────────
    RY = Y - 15
    sec_label(RX, Y, COL2, "BRAND PERFORMANCE")

    br_cols = [("Brand",0.26),("Revenue",0.24),("Bar",0.26),("MoM",0.14),("AOV",0.10)]
    br_cw   = [COL2*p for _,p in br_cols]
    max_rev = _brands["revenue"].max()

    # header
    rect(RX, RY-MON_H, COL2, MON_H, fill=_C["navy"])
    rx3 = RX
    for lbl,_ in br_cols:
        txt(lbl, rx3+br_cw[br_cols.index((lbl,_))]/2, RY-MON_H+4,
            "Helvetica-Bold", 6.5, _C["wht"], "center")
        rx3 += br_cw[br_cols.index((lbl,_))]
    # fix iteration
    rx3 = RX
    for j,(lbl,_) in enumerate(br_cols):
        txt(lbl, rx3+br_cw[j]/2, RY-MON_H+4, "Helvetica-Bold", 6.5, _C["wht"], "center")
        rx3 += br_cw[j]
    RY -= MON_H

    for ri, (_, r) in enumerate(_brands.sort_values("revenue",ascending=False).iterrows()):
        bg = _C["lgray"] if ri%2==0 else _C["wht"]
        rect(RX, RY-MON_H, COL2, MON_H, fill=bg)
        is_top = ri < 3
        dv = r["delta"]
        bar_fill = _C["blue"] if is_top else _C["amb"]

        # Brand name
        txt(r["name"], RX+br_cw[0]/2, RY-MON_H+4, "Helvetica-Bold", 7, _C["navy"], "center")
        # Revenue
        txt(fk(r["revenue"]), RX+br_cw[0]+br_cw[1]/2, RY-MON_H+4, "Helvetica-Bold", 6.5, _C["blk"], "center")
        # Bar
        bx = RX+br_cw[0]+br_cw[1]+4
        mini_bar(bx, RY-MON_H+4, br_cw[2]-8, 5, r["revenue"], max_rev, bar_fill)
        # MoM
        txt(pct(dv), RX+br_cw[0]+br_cw[1]+br_cw[2]+br_cw[3]/2,
            RY-MON_H+4, "Helvetica-Bold", 6, pctc(dv), "center")
        # AOV
        aov_v = int(r["revenue"]/r["orders"])
        txt("S${}".format(aov_v), RX+br_cw[0]+br_cw[1]+br_cw[2]+br_cw[3]+br_cw[4]/2,
            RY-MON_H+4, "Helvetica", 6, _C["steel"], "center")
        hline(RX, RY-MON_H, COL2, _C["mgray"])
        RY -= MON_H

    rect(RX, RY, COL2, Y-15-RY, stroke=_C["mgray"])

    # sync Y to lower of Y2, RY
    Y = min(Y2, RY) - 8

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TWO-COLUMN: Campaign ROI (left) | Geography (right)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    sec_label(LX, Y, COL1, "CAMPAIGN ROI ANALYSIS", bg=rl_colors.HexColor("#6d28d9"))
    sec_label(RX, Y, COL2, "GEOGRAPHIC REVENUE", bg=_C["teal"])
    CY = Y - 15

    # Campaign table
    cr_cols=[("Campaign",0.29),("Revenue",0.19),("ROI",0.13),("ROAS",0.12),("MoM",0.13),("AOV",0.14)]
    cr_cw  =[COL1*p for _,p in cr_cols]
    rect(LX, CY-MON_H, COL1, MON_H, fill=rl_colors.HexColor("#6d28d9"))
    rx4 = LX
    for j,(lbl,_) in enumerate(cr_cols):
        txt(lbl, rx4+cr_cw[j]/2, CY-MON_H+4, "Helvetica-Bold", 6.5, _C["wht"], "center")
        rx4 += cr_cw[j]
    CY -= MON_H
    for ri,(_, r) in enumerate(_camps.sort_values("revenue",ascending=False).iterrows()):
        bg = rl_colors.HexColor("#f5f3ff") if ri%2==0 else _C["wht"]
        rect(LX, CY-MON_H, COL1, MON_H, fill=bg)
        roi  = (r["revenue"]-r["spend"])/r["spend"]*100
        roas = r["revenue"]/r["spend"]
        dv   = r["delta"]
        cvals=[
            (r["name"],                    "Helvetica-Bold",7,_C["blk"]),
            (fk(r["revenue"]),             "Helvetica-Bold",6.5,_C["navy"]),
            ("{:.0f}%".format(roi),        "Helvetica-Bold",6.5,_C["grn"] if roi>200 else _C["amb"]),
            ("{:.1f}x".format(roas),       "Helvetica",    6.5,_C["steel"]),
            (pct(dv),                      "Helvetica-Bold",6,pctc(dv)),
            ("S${}".format(int(r["revenue"]/r["orders"])),"Helvetica",6.5,_C["steel"]),
        ]
        rx5 = LX
        for j,(v,fn,sz,col) in enumerate(cvals):
            txt(v, rx5+cr_cw[j]/2, CY-MON_H+4, fn, sz, col, "center")
            rx5 += cr_cw[j]
        hline(LX, CY-MON_H, COL1, _C["mgray"])
        CY -= MON_H
    rect(LX, CY, COL1, Y-15-CY, stroke=_C["mgray"])

    # Geography
    _cities=[
        ("Woodlands",67353,126,534),("Tampines",62847,119,528),
        ("Bukit Timah",58921,108,546),("Bedok",55340,114,486),
        ("Ang Mo Kio",51209,107,479),("Punggol",48773,107,456),
        ("Jurong",44898,116,387),
    ]
    GY = Y - 15
    geo_cols=[("District",0.30),("Revenue",0.22),("Bar",0.24),("AOV",0.14),("vs#1",0.10)]
    geo_cw =[COL2*p for _,p in geo_cols]
    rect(RX, GY-MON_H, COL2, MON_H, fill=_C["teal"])
    rx6 = RX
    for j,(lbl,_) in enumerate(geo_cols):
        txt(lbl, rx6+geo_cw[j]/2, GY-MON_H+4, "Helvetica-Bold", 6.5, _C["wht"], "center")
        rx6 += geo_cw[j]
    GY -= MON_H
    top_rev_g = _cities[0][1]; max_rev_g = top_rev_g
    for ri,(name,rev,ord_,aov) in enumerate(_cities):
        bg = _C["lgray"] if ri%2==0 else _C["wht"]
        rect(RX, GY-MON_H, COL2, MON_H, fill=bg)
        vs = (rev-top_rev_g)/top_rev_g*100
        is_low = rev < top_rev_g*0.75
        bar_f = _C["teal"] if ri==0 else (_C["amb"] if is_low else _C["blue"])
        # district
        txt(name, RX+geo_cw[0]/2, GY-MON_H+4, "Helvetica-Bold" if ri==0 else "Helvetica",
            6.5, _C["teal"] if ri==0 else _C["blk"], "center")
        # revenue
        txt(fk(rev), RX+geo_cw[0]+geo_cw[1]/2, GY-MON_H+4, "Helvetica-Bold", 6.5, _C["navy"], "center")
        # bar
        gbx = RX+geo_cw[0]+geo_cw[1]+4
        mini_bar(gbx, GY-MON_H+4, geo_cw[2]-8, 5, rev, max_rev_g, bar_f)
        # aov
        txt("S${}".format(aov), RX+geo_cw[0]+geo_cw[1]+geo_cw[2]+geo_cw[3]/2,
            GY-MON_H+4, "Helvetica", 6.5, _C["steel"], "center")
        # vs#1
        vs_str = "—" if ri==0 else "{:.0f}%".format(vs)
        txt(vs_str, RX+geo_cw[0]+geo_cw[1]+geo_cw[2]+geo_cw[3]+geo_cw[4]/2,
            GY-MON_H+4, "Helvetica-Bold" if is_low else "Helvetica",
            6, _C["teal"] if ri==0 else (_C["red"] if is_low else _C["dgray"]), "center")
        hline(RX, GY-MON_H, COL2, _C["mgray"])
        GY -= MON_H
    rect(RX, GY, COL2, Y-15-GY, stroke=_C["mgray"])

    Y = min(CY, GY) - 8

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # KEY TAKEAWAYS — 6 items in 2 columns of 3
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    sec_label(LX, Y, CW, "KEY TAKEAWAYS  &  STRATEGIC RECOMMENDATIONS", bg=_C["blk"])
    Y -= 15
    TW   = (CW - 5) / 2   # tile width
    TH   = 36              # tile height
    TGAP = 4

    takeaways = [
        (_C["red"],  _C["lred"],  "1 CRITICAL RISK",
         "LG = 64% of GMV",
         "Onboard Samsung/Sony. Target LG <50% by Q3 2026."),
        (_C["amb"],  _C["lamb"],  "2 GROWTH",
         "Repeat rate 3.6% vs 15–20% avg",
         "Launch loyalty programme by Q2. Target 8% repeat rate."),
        (_C["grn"],  _C["lgrn"],  "3 QUICK WIN",
         "Double Day ROI 395%, ROAS 4.9x",
         "Scale budget +25–30%. Replicate bundle mechanic."),
        (_C["amb"],  _C["lamb"],  "4 SEASONAL RISK",
         "Jan -22.3% MoM every year",
         "Add mid-Jan Wednesday flash sale to FY26/27 calendar."),
        (_C["teal"], rl_colors.HexColor("#cffafe"), "5 GEO",
         "Jurong AOV S$387 vs S$534 top (-27%)",
         "Geo-targeted Electronics bundle at S$450+ min basket."),
        (_C["grn"],  _C["lgrn"],  "6 MARGIN",
         "Voucher leakage S$3.9K/period",
         "Set S$500 min basket + first-time buyer restriction."),
    ]
    for i,(border,bg,tag,title,action) in enumerate(takeaways):
        col = i // 3
        row = i %  3
        tx  = LX + col*(TW+5)
        ty  = Y  - row*(TH+TGAP)
        rect(tx, ty-TH, TW, TH, fill=bg, radius=3)
        # left accent bar
        rect(tx, ty-TH, 3, TH, fill=border, radius=0)
        txt(tag,    tx+8,  ty-10, "Helvetica-Bold", 6.5, border)
        txt(title,  tx+8,  ty-20, "Helvetica-Bold", 7.5, _C["blk"])
        txt(action, tx+8,  ty-31, "Helvetica",      6.5, _C["steel"])

    Y -= 3*(TH+TGAP) + 6

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # FOOTER
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    rect(0, 0, PW, 16, fill=_C["lgray"])
    hline(0, 16, PW, _C["mgray"])
    txt("Shopee Commerce Intelligence  ·  Generated "+date.today().strftime("%d %B %Y")+"  ·  CONFIDENTIAL",
        PW/2, 5, "Helvetica", 7, _C["dgray"], "center")

    c.save()
    buf.seek(0)
    return buf.read()

# ── Fixed AI Segmentation Data ────────────────────────────────────────────────
# 3 customer types: discount-driven / mid-ticket / high-ticket
CUSTOMER_SEGMENTS = [
    {
        "name": "Discount-Driven",  "emoji": "🏷️", "pct": 46,
        "aov": "S$180–S$320",       "voucher": "90%+",
        "bg": "#fff7ed", "border": "#fb923c", "color": "#b45309",
        "action": "Set S$500 min basket on vouchers to cut leakage without losing volume.",
    },
    {
        "name": "Mid-Ticket",       "emoji": "🛒", "pct": 36,
        "aov": "S$320–S$620",       "voucher": "~50%",
        "bg": "#f0fdfa", "border": "#14b8a6", "color": "#0e7490",
        "action": "Bundle SPayLater 0% instalment on S$400–600 baskets to push AOV up.",
    },
    {
        "name": "High-Ticket",      "emoji": "💎", "pct": 18,
        "aov": "S$620–S$1,800",     "voucher": "<15%",
        "bg": "#eff6ff", "border": "#3b82f6", "color": "#1d4ed8",
        "action": "Early-access invites to new LG launches — they convert without discounts.",
    },
]

# 3 product tiers: hero / stable / underperformer
PRODUCT_SEGMENTS = [
    {
        "name": "Hero",        "emoji": "🏆", "brands": ["LG"],
        "gmv": "S$227K", "pct_gmv": 64, "trend": "+12.3%",
        "bg": "#eff6ff", "border": "#3b82f6", "color": "#1d4ed8",
        "trend_col": "#15803d",
        "action": "Protect stock levels. Reduce dependency by onboarding 1 new brand/quarter.",
    },
    {
        "name": "Stable",      "emoji": "📊", "brands": ["Philips", "Nike"],
        "gmv": "S$95K",  "pct_gmv": 27, "trend": "+1–4%",
        "bg": "#f0fdfa", "border": "#14b8a6", "color": "#0e7490",
        "trend_col": "#15803d",
        "action": "Bundle Philips + Nike to cross-sell between Home and Fashion buyers.",
    },
    {
        "name": "Underperformer", "emoji": "⚠️", "brands": ["Anker", "COSRX"],
        "gmv": "S$32K",  "pct_gmv": 9,  "trend": "-6 to -15%",
        "bg": "#fff7ed", "border": "#fb923c", "color": "#b45309",
        "trend_col": "#b91c1c",
        "action": "Create category bundles — Anker accessories + COSRX skincare starter kits.",
    },
]

def _seg_customer_cards(segments):
    st.markdown("""<div style="display:flex;align-items:center;gap:8px;margin:14px 0 8px">
        <span style="font-size:14px">🧠</span>
        <span style="font-weight:700;font-size:13px;color:#0f172a">Customer Segments</span>
        <span style="background:#eff6ff;color:#1d4ed8;font-size:9px;font-weight:700;padding:1px 7px;border-radius:8px;border:1px solid #bfdbfe">AI</span>
    </div>""", unsafe_allow_html=True)
    cols = st.columns(3)
    for i, s in enumerate(segments):
        with cols[i]:
            st.markdown(f"""
            <div style="background:{s['bg']};border:1.5px solid {s['border']};border-radius:10px;padding:14px 16px">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
                    <div style="display:flex;align-items:center;gap:8px">
                        <span style="font-size:22px">{s['emoji']}</span>
                        <span style="font-weight:800;font-size:13px;color:#0f172a">{s['name']}</span>
                    </div>
                    <span style="background:{s['border']};color:white;font-size:11px;font-weight:800;padding:3px 10px;border-radius:20px">{s['pct']}%</span>
                </div>
                <div style="display:flex;gap:6px;margin-bottom:10px">
                    <div style="flex:1;background:rgba(0,0,0,.04);border-radius:6px;padding:6px 8px;text-align:center">
                        <div style="font-size:9px;color:#64748b;text-transform:uppercase;font-weight:600;margin-bottom:2px">Avg Ticket</div>
                        <div style="font-size:12px;font-weight:800;color:{s['color']}">{s['aov']}</div>
                    </div>
                    <div style="flex:1;background:rgba(0,0,0,.04);border-radius:6px;padding:6px 8px;text-align:center">
                        <div style="font-size:9px;color:#64748b;text-transform:uppercase;font-weight:600;margin-bottom:2px">Voucher Use</div>
                        <div style="font-size:12px;font-weight:800;color:{s['color']}">{s['voucher']}</div>
                    </div>
                </div>
                <div style="border-left:3px solid {s['border']};padding:5px 8px;background:rgba(0,0,0,.03);border-radius:0 6px 6px 0">
                    <div style="font-size:10px;color:#334155">⚡ {s['action']}</div>
                </div>
            </div>""", unsafe_allow_html=True)

def _seg_product_cards(segments):
    st.markdown("""<div style="display:flex;align-items:center;gap:8px;margin:14px 0 8px">
        <span style="font-size:14px">🧠</span>
        <span style="font-weight:700;font-size:13px;color:#0f172a">Product Performance Tiers</span>
        <span style="background:#eff6ff;color:#1d4ed8;font-size:9px;font-weight:700;padding:1px 7px;border-radius:8px;border:1px solid #bfdbfe">AI</span>
    </div>""", unsafe_allow_html=True)
    cols = st.columns(3)
    for i, s in enumerate(segments):
        with cols[i]:
            brands_html = "".join(f'<span style="background:{s["bg"]};border:1px solid {s["border"]};color:{s["color"]};padding:2px 8px;border-radius:10px;font-size:10px;font-weight:700;margin-right:4px">{b}</span>' for b in s['brands'])
            st.markdown(f"""
            <div style="background:{s['bg']};border:1.5px solid {s['border']};border-radius:10px;padding:14px 16px">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
                    <div style="display:flex;align-items:center;gap:8px">
                        <span style="font-size:22px">{s['emoji']}</span>
                        <span style="font-weight:800;font-size:13px;color:#0f172a">{s['name']}</span>
                    </div>
                    <span style="color:{s['trend_col']};font-size:11px;font-weight:800">{s['trend']}</span>
                </div>
                <div style="margin-bottom:8px">{brands_html}</div>
                <div style="display:flex;gap:6px;margin-bottom:10px">
                    <div style="flex:1;background:rgba(0,0,0,.04);border-radius:6px;padding:6px 8px;text-align:center">
                        <div style="font-size:9px;color:#64748b;text-transform:uppercase;font-weight:600;margin-bottom:2px">GMV</div>
                        <div style="font-size:12px;font-weight:800;color:{s['color']}">{s['gmv']}</div>
                    </div>
                    <div style="flex:1;background:rgba(0,0,0,.04);border-radius:6px;padding:6px 8px;text-align:center">
                        <div style="font-size:9px;color:#64748b;text-transform:uppercase;font-weight:600;margin-bottom:2px">Share</div>
                        <div style="font-size:12px;font-weight:800;color:{s['color']}">{s['pct_gmv']}%</div>
                    </div>
                </div>
                <div style="border-left:3px solid {s['border']};padding:5px 8px;background:rgba(0,0,0,.03);border-radius:0 6px 6px 0">
                    <div style="font-size:10px;color:#334155">⚡ {s['action']}</div>
                </div>
            </div>""", unsafe_allow_html=True)


# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
/* Font + background — ONLY target specific elements, never [class*="css"] */
html, body { font-family: 'Inter', sans-serif !important; background: #f1f5f9 !important; }
.stApp { background: #f1f5f9 !important; }
footer { visibility: hidden !important; }
div[data-testid="stDecoration"] { display: none !important; }
/* Hide toolbar text/icons but keep header alive for sidebar toggle */
div[data-testid="stToolbar"] { visibility: hidden !important; }
#MainMenu { visibility: hidden !important; }
/* Header: invisible background, no border, but full height so toggle renders */
header[data-testid="stHeader"] { background: #ffffff !important; border-bottom: 1px solid #e2e8f0 !important; box-shadow: none !important; }
/* Sidebar toggle button: always fully visible */
header[data-testid="stHeader"] button,
button[data-testid="collapsedControl"],
button[data-testid="baseButton-header"] { opacity: 1 !important; visibility: visible !important; color: #374151 !important; }

/* Sidebar styling */
section[data-testid="stSidebar"] { background: #ffffff !important; border-right: 1px solid #e2e8f0 !important; }
section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p { color: #374151 !important; }
/* Main content padding */
.block-container { padding: 1rem 2rem 3rem !important; background: #f1f5f9 !important; }
/* Form elements */
.stSelectbox > div > div, .stMultiSelect > div > div { background: #f8fafc !important; border-color: #e2e8f0 !important; border-radius: 8px !important; }
.stButton > button { background: #2563eb !important; color: white !important; border: none !important; border-radius: 8px !important; font-weight: 600 !important; }
/* KPI cards */
.kpi-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px 20px; margin-bottom: 10px; box-shadow: 0 1px 4px rgba(0,0,0,.05); }
.kpi-val { font-size: 22px; font-weight: 800; margin-bottom: 4px; }
.kpi-label { font-size: 10px; color: #6b7280; font-weight: 700; text-transform: uppercase; letter-spacing: .04em; margin-bottom: 3px; }
.kpi-sub { font-size: 11px; color: #9ca3af; }
.section-header { font-size: 22px; font-weight: 800; color: #0f172a; margin-bottom: 4px; margin-top: 0; display: block; }
.section-sub { font-size: 13px; color: #64748b; margin-bottom: 18px; }
.chart-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px 20px; box-shadow: 0 1px 4px rgba(0,0,0,.05); margin-bottom: 14px; }
.chart-title { font-size: 14px; font-weight: 700; color: #1e293b; margin-bottom: 4px; }
.chart-sub { font-size: 11px; color: #9ca3af; margin-bottom: 10px; }
hr { border-color: #e2e8f0 !important; }
div[data-testid="stIFrame"] { border: none !important; background: transparent !important; }
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
        try:
            sheets = pd.read_excel(up, sheet_name=None)
            # ── Monthly ──────────────────────────────────────────────────────
            if "Monthly" in sheets:
                _m = sheets["Monthly"].copy()
                _m.columns = [c.lower().replace(" ","_") for c in _m.columns]
                for col in ["revenue","orders","aov","customers","voucher_rate","avg_delivery","avg_rating"]:
                    if col in _m.columns: _m[col] = pd.to_numeric(_m[col], errors="coerce")
                if "is_forecast" in _m.columns:
                    _m["is_forecast"] = _m["is_forecast"].apply(lambda x: str(x).lower() in ["true","1","yes"])
                else:
                    _m["is_forecast"] = False
                _m["rev_mom"]  = _m["revenue"].pct_change()*100
                _m["ord_mom"]  = _m["orders"].pct_change()*100
                _m["aov_mom"]  = _m["aov"].pct_change()*100
                _m["cust_mom"] = _m["customers"].pct_change()*100 if "customers" in _m.columns else 0
                monthly_data   = _m
                actual_monthly = _m[_m["is_forecast"]==False]
            # ── Summary ──────────────────────────────────────────────────────
            if "Summary" in sheets:
                _s = sheets["Summary"].copy()
                _s.columns = [c.lower().replace(" ","_") for c in _s.columns]
                if "metric" in _s.columns and "value" in _s.columns:
                    for _, row in _s.iterrows():
                        k = str(row["metric"]).strip()
                        try: SUMMARY[k] = float(row["value"])
                        except: pass
            # ── Brands ───────────────────────────────────────────────────────
            if "Brands" in sheets:
                _b = sheets["Brands"].copy()
                _b.columns = [c.lower().replace(" ","_") for c in _b.columns]
                _b["revenue"] = pd.to_numeric(_b["revenue"], errors="coerce")
                _b["orders"]  = pd.to_numeric(_b["orders"],  errors="coerce")
                _COLS = [C["blue"],C["cyan"],C["violet"],C["purple"],C["green"],C["amber"]]
                _b["color"] = [_COLS[i % len(_COLS)] for i in range(len(_b))]
                brands_data = _b
            # ── Campaigns ────────────────────────────────────────────────────
            if "Campaigns" in sheets:
                _c = sheets["Campaigns"].copy()
                _c.columns = [c.lower().replace(" ","_") for c in _c.columns]
                _c["revenue"] = pd.to_numeric(_c["revenue"], errors="coerce")
                _c["orders"]  = pd.to_numeric(_c["orders"],  errors="coerce")
                _COLS2 = [C["blue"],C["cyan"],C["violet"],C["purple"],C["green"]]
                _c["color"] = [_COLS2[i % len(_COLS2)] for i in range(len(_c))]
                campaigns_data = _c
            # ── Cities ───────────────────────────────────────────────────────
            if "Cities" in sheets:
                _ci = sheets["Cities"].copy()
                _ci.columns = [c.lower().replace(" ","_") for c in _ci.columns]
                _ci["revenue"] = pd.to_numeric(_ci["revenue"], errors="coerce")
                _ci["orders"]  = pd.to_numeric(_ci["orders"],  errors="coerce")
                cities_data = _ci
            # ── Weekly ───────────────────────────────────────────────────────
            if "Weekly" in sheets:
                _w = sheets["Weekly"].copy()
                _w.columns = [c.lower().replace(" ","_") for c in _w.columns]
                for col in ["revenue","orders","aov","voucher_rate"]:
                    if col in _w.columns: _w[col] = pd.to_numeric(_w[col], errors="coerce")
                _w["rev_wow"] = _w["revenue"].pct_change()*100
                weekly_data = _w
            st.success(f"✅ {up.name} loaded — {len(sheets)} sheets detected: {', '.join(sheets.keys())}")
        except Exception as _ue:
            st.error(f"Upload error: {_ue}")

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
    st.subheader("📊 Overview")
    st.markdown('<div class="section-sub">Shopee Singapore · Oct 2025 – Jan 2026 · 800 orders</div>',unsafe_allow_html=True)
    # ── AI Customer Segmentation panel
    with st.expander("🧠 AI Customer Segments — click to expand", expanded=False):
        _seg_customer_cards(CUSTOMER_SEGMENTS)

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
    st.subheader("📅 Month-over-Month Analysis")
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
    st.subheader("📆 Weekly Analysis")
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
    st.subheader("📆 Daily Analysis")
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
    st.subheader("📣 Campaigns & Channels")
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

    # ── AI Customer Segmentation by buying behaviour
    st.markdown("---")
    with st.expander("🧠 AI Customer Segments — who's buying and why", expanded=True):
        _seg_customer_cards(CUSTOMER_SEGMENTS)

# ══════════════════════════════════════════════════════════════════════════════
# GEOGRAPHY
# ══════════════════════════════════════════════════════════════════════════════
elif "Geography" in view:
    st.subheader("📍 Geographic Performance")
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

    # ── AI Product Segmentation by brand strategy
    st.markdown("---")
    with st.expander("🧠 AI Product Segments — brand strategy & risk", expanded=True):
        _seg_product_cards(PRODUCT_SEGMENTS)

# ══════════════════════════════════════════════════════════════════════════════
# SCENARIO PLANNING
# ══════════════════════════════════════════════════════════════════════════════
elif "Scenario" in view:
    st.subheader("🎯 Scenario Planning")
    st.markdown('<div class="section-sub">Adjust the 4 key levers — projection updates instantly</div>', unsafe_allow_html=True)

    BASE_ORDERS   = 200
    BASE_AOV      = 442
    BASE_MONTHS   = ["Feb","Mar","Apr","May","Jun","Jul"]
    BASE_VOUCHER  = 48.75   # baseline voucher rate for elasticity calc

    # Lever descriptions
    LEVER_TIPS = {
        "ord": ("📦 Monthly order growth %",  "Organic growth from SEO, reviews, and repeat traffic. Baseline ~5%/mo based on Oct–Jan trend."),
        "camp": ("📣 Campaign days / month",   "Each campaign day adds ~8–12 orders. Baseline: 2 campaign days/mo (Double Day + 1 flash)."),
        "cust": ("👥 New customer growth %",   "New customer acquisition rate month-on-month. Baseline ~4%/mo from paid + organic traffic."),
        "vr":   ("🎫 Voucher usage %",         "% of orders using a voucher. Lower = less discount cost but also fewer deal-driven orders."),
    }

    st.markdown('<div class="chart-card"><div class="chart-title">📐 Business Levers</div><div class="chart-sub">All 4 levers directly drive order volume — projection updates instantly</div>', unsafe_allow_html=True)
    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        order_growth = st.slider("📦 Monthly order growth %", -20, 40, 5, 1, key="sp_ord")
        st.caption("Baseline: ~5%/mo from organic")
    with col_b:
        camp_days = st.slider("📣 Campaign days / month", 0, 12, 2, 1, key="sp_camp")
        st.caption("Baseline: 2 days (1 major + 1 flash)")
    with col_c:
        cust_growth = st.slider("👥 New customer growth %", -10, 30, 4, 1, key="sp_cust")
        st.caption("Baseline: ~4%/mo new customers")
    with col_d:
        voucher_rate = st.slider("🎫 Voucher usage %", 20.0, 70.0, 48.75, 0.25, key="sp_vr", format="%.2f%%")
        st.caption("Baseline: 48.75%")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── How each lever drives orders ──────────────────────────────────────────
    # order_growth:  direct compound monthly order multiplier
    # camp_days:     each campaign day adds ~10 orders (avg of Double Day 172/17d, Flash 136/14d)
    #                baseline 2 days = 20 bonus orders baked in; slider shows delta from baseline
    # cust_growth:   new customers at baseline 80% first-purchase conversion, avg 1.1 orders each
    #                every +1% cust growth on 772 base ≈ +0.8 new customers/mo ≈ +0.9 orders/mo
    # voucher_rate:  every 10pp change → ±3–4% orders (deal-seekers / price-sensitive buyers)

    BASE_VOUCHER  = 48.75
    BASE_CAMP     = 2         # baseline campaign days
    BASE_CUST_GR  = 4.0       # baseline new cust growth %
    AVG_DISC      = 10        # S$10 avg voucher discount

    def voucher_order_mult(vr):
        delta = vr - BASE_VOUCHER
        return 1 + (delta / 10) * (0.03 if delta >= 0 else 0.04)

    def camp_order_bonus(days):
        # Each day above baseline adds ~10 orders; each day below loses ~8
        delta = days - BASE_CAMP
        return delta * (10 if delta >= 0 else 8)

    def cust_order_boost(cgr, base_orders):
        # Additional orders from net-new customers each month
        # Every 1% above baseline new-cust growth ≈ +0.9 incremental orders/mo
        delta = cgr - BASE_CUST_GR
        return delta * 0.9

    def sp_project(ord_gr, camp_d, cgr, vr):
        rows   = []
        orders = float(BASE_ORDERS) * voucher_order_mult(vr)
        aov    = BASE_AOV           # AOV held constant — model focuses on order volume drivers
        for mo in BASE_MONTHS:
            orders  = max(40, orders * (1 + ord_gr / 100))
            orders += camp_order_bonus(camp_d)
            orders += cust_order_boost(cgr, orders)
            orders  = max(40, orders)
            vcost   = orders * (vr / 100) * AVG_DISC
            net     = orders * aov - vcost
            rows.append({"month": mo, "orders": int(orders), "aov": round(aov),
                         "voucher_cost": round(vcost), "net": round(net)})
        return pd.DataFrame(rows)

    proj      = sp_project(order_growth, camp_days, cust_growth, voucher_rate)
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
        tbl["Voucher Cost"] = tbl["voucher_cost"].apply(fmt_s)
        tbl["Net Margin"]   = ((tbl["net"] / (tbl["orders"] * BASE_AOV)) * 100).apply(lambda x: f"{x:.1f}%")
        tbl["MoM"] = tbl["net"].pct_change().apply(
            lambda x: f"{'↑' if x>0 else '↓'}{abs(x)*100:.1f}%" if pd.notna(x) else "—"
        )
        st.dataframe(tbl[["month","Revenue","MoM","Orders","Net Margin","Voucher Cost"]].rename(columns={"month":"Month"}),
                     use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="chart-card"><div class="chart-title">⚡ What Moves Revenue Most?</div><div class="chart-sub">Impact of nudging each lever one step from current</div>', unsafe_allow_html=True)
        base_total = proj["net"].sum()
        def nudge(**kw):
            return sp_project(
                kw.get("og", order_growth), kw.get("cd", camp_days),
                kw.get("cg", cust_growth),  kw.get("vr", voucher_rate)
            )["net"].sum()

        levers = [
            ("📦 +5% order growth",      nudge(og=order_growth+5)              - base_total),
            ("📣 +2 campaign days/mo",   nudge(cd=camp_days+2)                 - base_total),
            ("👥 +5% new customers/mo",  nudge(cg=cust_growth+5)              - base_total),
            ("🎫 -5% voucher rate",      nudge(vr=max(20, voucher_rate-5))     - base_total),
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
            "Yes — at 5% monthly order growth + 2 campaign days, your 6-month projection is well within range. "
            "Your Oct–Jan baseline averaged 200 orders/month. The model compounds order growth each month, "
            "so the biggest risk is sustaining growth in months 4–6 when the base is higher. "
            "Feb–Jul historically sees steadier demand than the holiday spike-dip cycle.",
            "Cross-check: if you ran 2 campaigns in Feb and hit ~210 orders, you're on track."
        ),
        "Which lever moves orders the most?": (
            "Campaign days is the single highest-impact lever for orders. Each campaign day adds ~10 incremental orders "
            "based on your Double Day (172 orders over event) and Flash Sale (136 orders) data. "
            "Going from 2 to 4 campaign days adds ~20 orders/month — equivalent to 10% organic growth "
            "but achieved in a single day. New customer growth compounds over time and is the best long-term lever.",
            "Add 1 mid-month Wednesday flash sale — your peak day — and track the order lift vs your baseline."
        ),
        "What happens if I run more campaigns?": (
            "Every campaign day above your 2-day baseline adds approximately 10 orders and S$4,420 in revenue "
            "(at S$442 AOV). Running 4 campaign days/month instead of 2 adds ~120 orders and S$53K over 6 months. "
            "However, too many campaigns train buyers to wait for deals — beyond 8 days/month, "
            "organic orders start cannibalising. Sweet spot is 4–6 campaign days for your store size.",
            "Test: add 1 extra flash sale in March and compare March organic orders to February as a control."
        ),
        "How does new customer growth affect orders?": (
            "New customer growth has a compounding effect — each new customer added this month can return next month. "
            "At 4% baseline, you're acquiring ~31 new customers/month from your 772 base. "
            "Pushing to 8% doubles that to ~62 new customers — at 80% first-purchase rate, "
            "that's +25 incremental orders/month, building to +150 orders by month 6.",
            "Invest S$500/month in Shopee Ads targeting Woodlands and Tampines — your top districts — to accelerate new customer growth."
        ),
        "How can I reduce voucher leakage?": (
            "Voucher usage at 48.75% costs S$3,900/period at S$10 avg discount. "
            "Reducing to 40% saves ~S$700/month but loses ~4% of deal-driven orders. "
            "The net effect depends on your margin — at S$442 AOV, losing 8 orders/month "
            "costs more than the S$700 saved. Smarter play: keep voucher rate but raise the minimum basket to S$500.",
            "Set S$500 minimum basket for vouchers this week. Discount Hunters segment (~34% of customers) will still convert at S$500+."
        ),
        "What order volume do I need for S$600K?": (
            "At your fixed AOV of S$442 and 48.75% voucher usage (S$10 avg discount), "
            "you need approximately 1,430 total orders over 6 months — or about 238 orders/month. "
            "That's 19% above your current 200/month baseline. "
            "Achievable with: +8% organic growth + 3 campaign days/month + 5% new customer growth combined.",
            "Set your sliders to: Order Growth 8%, Campaign Days 3, New Customers 7% and watch the projection hit S$600K."
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

# ── Floating AI chatbot ──────────────────────────────────────────────────────
_bot_qa = {q: {'b': body, 'a': action} for q, (body, action) in HARDCODED_QA.items()}
_bot_qs = CHAT_QS
_bot_css = '@keyframes gl{0%,100%{box-shadow:0 4px 18px rgba(37,99,235,.5)}50%{box-shadow:0 4px 30px rgba(37,99,235,.9)}}@keyframes up{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}@keyframes fi{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:translateY(0)}}@keyframes bl{0%,100%{opacity:.2}50%{opacity:1}}body{margin:0;background:transparent;overflow:hidden}#bub{position:fixed;bottom:20px;right:20px;width:54px;height:54px;border-radius:50%;background:linear-gradient(135deg,#2563eb,#0891b2);border:none;cursor:pointer;font-size:22px;display:flex;align-items:center;justify-content:center;animation:gl 3s ease-in-out infinite;z-index:9999;color:white}#badge{position:absolute;top:-2px;right:-2px;width:17px;height:17px;border-radius:50%;background:#16a34a;border:2px solid #fff;font-size:7px;font-weight:800;color:#fff;display:flex;align-items:center;justify-content:center;pointer-events:none}#panel{position:fixed;bottom:84px;right:20px;width:350px;height:480px;background:#fff;border:1px solid #e2e8f0;border-radius:16px;display:none;flex-direction:column;overflow:hidden;box-shadow:0 16px 48px rgba(0,0,0,.2);z-index:9998}#panel.on{display:flex;animation:up .2s ease both}#hd{background:linear-gradient(135deg,#2563eb,#0891b2);padding:12px 15px;display:flex;align-items:center;gap:10px;flex-shrink:0}#av{width:33px;height:33px;border-radius:50%;background:rgba(255,255,255,.2);display:flex;align-items:center;justify-content:center;font-size:16px}#msgs{flex:1;overflow-y:auto;padding:12px;display:flex;flex-direction:column;gap:8px}#msgs::-webkit-scrollbar{width:3px}#msgs::-webkit-scrollbar-thumb{background:#e2e8f0;border-radius:3px}.msg{max-width:88%;animation:fi .18s ease both;font-family:Inter,system-ui,sans-serif}.msg.u{align-self:flex-end}.msg.b{align-self:flex-start}.bu{background:linear-gradient(135deg,#2563eb,#1d4ed8);color:#fff;padding:9px 13px;border-radius:14px 14px 3px 14px;font-size:12px;line-height:1.6}.bb{background:#f8fafc;border:1px solid #e2e8f0;color:#1e293b;padding:10px 13px;border-radius:14px 14px 14px 3px;font-size:12px;line-height:1.75}.ac{background:#fffbeb;border-left:3px solid #d97706;padding:6px 9px;margin-top:7px;font-size:11px;color:#92400e;font-weight:600;border-radius:0 5px 5px 0}#chips{padding:8px 10px;display:flex;flex-wrap:wrap;gap:5px;border-top:1px solid #f1f5f9;flex-shrink:0}.ch{background:#eff6ff;border:1px solid #bfdbfe;color:#1d4ed8;padding:5px 11px;border-radius:20px;font-size:10px;cursor:pointer;white-space:nowrap;font-family:Inter,system-ui,sans-serif}.ch:hover{background:#dbeafe}.dots{display:flex;gap:4px;align-items:center;padding:3px 0}.dot{width:6px;height:6px;border-radius:50%;background:#93c5fd}.dot:nth-child(1){animation:bl 1.2s 0s infinite}.dot:nth-child(2){animation:bl 1.2s .2s infinite}.dot:nth-child(3){animation:bl 1.2s .4s infinite}'
_bot_js  = 'var open=false,inited=false,busy=false;function tog(){open=!open;document.getElementById(\'panel\').classList.toggle(\'on\',open);if(open&&!inited){inited=true;add(\'b\',\'Hi! I am your Shopee analyst. Tap a question below.\',null);chips();}}function chips(){var b=document.getElementById(\'chips\');b.innerHTML=\'\';QS.forEach(function(q){var e=document.createElement(\'button\');e.className=\'ch\';e.textContent=q;e.onclick=function(){go(q);};b.appendChild(e);});}function esc(t){return String(t).replace(/&/g,\'&amp;\').replace(/</g,\'&lt;\').replace(/>/g,\'&gt;\');}function add(r,t,a){var d=document.createElement(\'div\');d.className=\'msg \'+(r===\'u\'?\'u\':\'b\');var bub=r===\'u\'?\'<div class="bu">\'+esc(t)+\'</div>\':\'<div class="bb">\'+esc(t)+(a?\'<div class="ac">&#9889; \'+esc(a)+\'</div>\':\'\')+  \'</div>\';d.innerHTML=bub;var m=document.getElementById(\'msgs\');m.appendChild(d);m.scrollTop=99999;}function go(q){if(busy)return;busy=true;add(\'u\',q,null);var t=document.createElement(\'div\');t.id=\'typ\';t.className=\'msg b\';t.innerHTML=\'<div class="bb"><div class="dots"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div></div>\';var m=document.getElementById(\'msgs\');m.appendChild(t);m.scrollTop=99999;setTimeout(function(){var x=document.getElementById(\'typ\');if(x)x.remove();var r=QA[q];add(\'b\',r?r.b:\'No answer.\',r?r.a:null);busy=false;},700);}var fr=window.frameElement;if(fr){fr.style.cssText=\'position:fixed!important;bottom:0!important;right:0!important;width:420px!important;height:600px!important;border:none!important;background:transparent!important;z-index:99999!important;\';}'
_bot_html = (
    "<!DOCTYPE html><html><head><meta charset='utf-8'><style>"
    + _bot_css +
    "</style></head><body>"
    "<button id='bub' onclick='tog()'>&#x1F916;<span id='badge'>AI</span></button>"
    "<div id='panel'><div id='hd'>"
    "<div id='av'>&#x1F916;</div>"
    "<div style='flex:1'>"
    "<div style='font-weight:700;font-size:13px;color:#fff;font-family:Inter,sans-serif'>Shopee AI Analyst</div>"
    "<div style='font-size:10px;color:rgba(255,255,255,.75)'>Tap a question for an instant insight</div>"
    "</div>"
    "<button onclick='tog()' style='background:transparent;border:none;color:rgba(255,255,255,.7);font-size:22px;cursor:pointer;line-height:1;margin-left:auto'>&#215;</button>"
    "</div><div id='msgs'></div><div id='chips'></div></div>"
    "<script>var QA="
    + json.dumps(_bot_qa, ensure_ascii=False) +
    ";var QS="
    + json.dumps(_bot_qs, ensure_ascii=False) +
    ";"
    + _bot_js +
    "</script></body></html>"
)
components.html(_bot_html, height=0, scrolling=False)
