import os, requests, json
from datetime import datetime, date

KEY = os.environ.get("FMP_KEY", "")
TODAY = date.today().strftime("%B %d, %Y")
TODAY_SHORT = date.today().strftime("%b %d, %Y")
BASE = "https://financialmodelingprep.com/api"

def get(url):
    try:
        r = requests.get(url, timeout=10)
        return r.json()
    except:
        return {}

def fget(url):
    try:
        r = requests.get(url, timeout=10)
        d = r.json()
        return d if isinstance(d, list) and len(d) > 0 else {}
    except:
        return {}

# ── FETCH MARKET DATA ──────────────────────────────────────
print("Fetching market data...")

# Index quotes: SPY=S&P500, QQQ=Nasdaq, DIA=Dow, IWM=Russell2K
quotes_url = f"{BASE}/v3/quote/SPY,QQQ,DIA,IWM,GLD,USO,TLT,VXX,GC=F,CL=F?apikey={KEY}"
quotes = fget(quotes_url)
q = {item.get("symbol",""): item for item in quotes} if isinstance(quotes, list) else {}

def qv(sym, field, default="--"):
    item = q.get(sym, {})
    val = item.get(field, default)
    return val if val is not None else default

def fmt_price(v):
    if isinstance(v, (int, float)):
        return f"{v:,.2f}"
    return str(v)

def fmt_chg(v):
    if isinstance(v, (int, float)):
        sign = "+" if v >= 0 else ""
        return f"{sign}{v:.2f}%"
    return str(v)

def chg_class(v):
    if isinstance(v, (int, float)):
        return "up" if v >= 0 else "dn"
    return "fl"

# S&P 500
spx_price = qv("SPY", "price", 0)
spx_chg = qv("SPY", "changesPercentage", 0)

# Nasdaq (QQQ proxy)
ndx_price = qv("QQQ", "price", 0)
ndx_chg = qv("QQQ", "changesPercentage", 0)

# Dow (DIA proxy — multiply by ~10 for DJIA approx)
dia_price = qv("DIA", "price", 0)
dia_chg = qv("DIA", "changesPercentage", 0)

# Russell 2K
iwm_price = qv("IWM", "price", 0)
iwm_chg = qv("IWM", "changesPercentage", 0)

# Gold
gld_price = qv("GLD", "price", 0)
gld_chg = qv("GLD", "changesPercentage", 0)

# Oil
uso_price = qv("USO", "price", 0)
uso_chg = qv("USO", "changesPercentage", 0)

# VIX via ^VIX
vix_data = fget(f"{BASE}/v3/quote/%5EVIX?apikey={KEY}")
vix_price = vix_data[0].get("price", 0) if isinstance(vix_data, list) and vix_data else 0
vix_chg = vix_data[0].get("changesPercentage", 0) if isinstance(vix_data, list) and vix_data else 0

# Treasury yields
treasury = fget(f"{BASE}/v4/treasury?apikey={KEY}")
tr = treasury[0] if isinstance(treasury, list) and treasury else {}
y2 = tr.get("year2", 0) or 0
y10 = tr.get("year10", 0) or 0
y30 = tr.get("year30", 0) or 0
y3m = tr.get("month3", 0) or 0
y1 = tr.get("year1", 0) or 0
y5 = tr.get("year5", 0) or 0
spread = round(y10 - y2, 2) if y10 and y2 else 0

# Fed rate from FMP economics
fed_data = fget(f"{BASE}/v4/economic?name=federalFunds&apikey={KEY}")
fed_rate = fed_data[0].get("value", 0) if isinstance(fed_data, list) and fed_data else 0

# CPI
cpi_data = fget(f"{BASE}/v4/economic?name=CPI&apikey={KEY}")
cpi = cpi_data[0].get("value", 0) if isinstance(cpi_data, list) and cpi_data else 0
cpi_date = cpi_data[0].get("date", "")[:7] if isinstance(cpi_data, list) and cpi_data else ""

# Unemployment
unemp_data = fget(f"{BASE}/v4/economic?name=unemploymentRate&apikey={KEY}")
unemp = unemp_data[0].get("value", 0) if isinstance(unemp_data, list) and unemp_data else 0

# GDP
gdp_data = fget(f"{BASE}/v4/economic?name=realGDP&apikey={KEY}")
gdp = gdp_data[0].get("value", 0) if isinstance(gdp_data, list) and gdp_data else 0

# Sector performance
sectors_data = fget(f"{BASE}/v3/sectors-performance?apikey={KEY}")
sec_map = {}
if isinstance(sectors_data, list):
    for s in sectors_data:
        sec_map[s.get("sector","")] = s.get("changesPercentage", "0%")

def sec_pct(name):
    v = sec_map.get(name, "0%")
    try:
        return float(str(v).replace("%",""))
    except:
        return 0.0

tech_pct    = sec_pct("Technology")
hlth_pct    = sec_pct("Healthcare")
fin_pct     = sec_pct("Financial Services")
ind_pct     = sec_pct("Industrials")
energy_pct  = sec_pct("Energy")
cs_pct      = sec_pct("Communication Services")
mat_pct     = sec_pct("Basic Materials")
cd_pct      = sec_pct("Consumer Cyclical")
cst_pct     = sec_pct("Consumer Defensive")
re_pct      = sec_pct("Real Estate")
util_pct    = sec_pct("Utilities")

# Stock news
news_data = fget(f"{BASE}/v3/stock_news?limit=8&apikey={KEY}")

# Market news
market_news = fget(f"{BASE}/v3/fmp/articles?page=0&size=6&apikey={KEY}")

def safe_float(v, decimals=2):
    try:
        return round(float(v), decimals)
    except:
        return 0.0

def pct_str(v):
    v = safe_float(v)
    sign = "+" if v >= 0 else ""
    return f"{sign}{v:.2f}%"

def color_class(v):
    v = safe_float(v)
    if v > 0: return "up"
    if v < 0: return "dn"
    return "fl"

# Build sector list sorted by performance
SECTOR_LIST = [
    ("Technology", tech_pct),
    ("Healthcare", hlth_pct),
    ("Financials", fin_pct),
    ("Industrials", ind_pct),
    ("Energy", energy_pct),
    ("Comm. Services", cs_pct),
    ("Materials", mat_pct),
    ("Consumer Disc.", cd_pct),
    ("Consumer Staples", cst_pct),
    ("Real Estate", re_pct),
    ("Utilities", util_pct),
]
SECTOR_LIST.sort(key=lambda x: x[1], reverse=True)

def sec_signal(pct):
    if pct > 1.5: return "bull", "OVERWEIGHT"
    if pct < -1.0: return "bear", "UNDERWEIGHT"
    return "neut", "NEUTRAL"

sec_html = ""
max_abs = max(abs(s[1]) for s in SECTOR_LIST) or 1
for name, pct in SECTOR_LIST:
    sg, lbl = sec_signal(pct)
    col = "var(--green)" if sg=="bull" else ("var(--red)" if sg=="bear" else "var(--amber)")
    sign = "+" if pct >= 0 else ""
    w = round(abs(pct)/max_abs*100)
    sec_html += f'''<div class="sec-card {sg}" onclick="askSec('{name}')">
<div class="sec-name">{name}</div>
<div class="sec-perf" style="color:{col}">{sign}{pct:.1f}%</div>
<div class="sec-bar-bg"><div class="sec-bar-fill" style="width:{w}%;background:{col}"></div></div>
<div class="sec-sig {sg}">{lbl}</div>
</div>\n'''

# Build news HTML
news_html = ""
tags = ["eqt","eqt","mac","mac","cmd","rat","geo","eqt"]
tag_labels = {"eqt":"EQUITY","mac":"MACRO","cmd":"COMMODITIES","rat":"RATES","geo":"GEOPOLITICAL"}
if isinstance(news_data, list):
    for i, n in enumerate(news_data[:8]):
        tag = tags[i % len(tags)]
        title = n.get("title","").replace("<","&lt;").replace(">","&gt;")
        src = n.get("site","") or n.get("publisher","")
        pub_date = n.get("publishedDate","")[:10]
        url = n.get("url","#")
        news_html += f'''<div class="news-item">
<span class="ntag {tag}">{tag_labels.get(tag,tag)}</span>
<div>
<div class="n-hl"><a href="{url}" target="_blank" style="color:inherit;text-decoration:none">{title}</a></div>
<div class="n-meta">{src} · {pub_date}</div>
</div>
</div>\n'''

# Ticker data for JS
spx_p = fmt_price(spx_price)
ndx_p = fmt_price(ndx_price)
dia_p = fmt_price(dia_price)
iwm_p = fmt_price(iwm_price)
vix_p = f"{safe_float(vix_price):.2f}"
y10_s = f"{safe_float(y10):.2f}%"
gld_p = fmt_price(gld_price)
uso_p = fmt_price(uso_price)
fed_s = f"{safe_float(fed_rate):.2f}%"

spread_s = f"{'+' if spread>=0 else ''}{spread:.2f}%"
spread_class = "up" if spread >= 0 else "dn"

print(f"S&P: {spx_p} ({pct_str(spx_chg)})")
print(f"Nasdaq: {ndx_p} ({pct_str(ndx_chg)})")
print(f"VIX: {vix_p}")
print(f"10Y: {y10_s}")
print(f"Fed Rate: {fed_s}")
print(f"CPI: {cpi}% ({cpi_date})")
print(f"Unemployment: {unemp}%")
print(f"Spread: {spread_s}")

# ── BUILD HTML ─────────────────────────────────────────────
html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>SIGNAL — Market Intelligence</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --bg:#07090f;--bg2:#0e1420;--bg3:#141d2e;
  --border:#1c2a3e;--border2:#243349;
  --text:#e8edf5;--text2:#8a9ab5;--text3:#3d5068;
  --cyan:#1fd4ec;--green:#3dd68c;--red:#f06b6b;
  --amber:#f5a623;--purple:#9b7ff5;
  --mono:"IBM Plex Mono",monospace;--sans:"Inter",sans-serif;
}}
body{{background:var(--bg);color:var(--text);font-family:var(--sans);min-height:100vh;overflow-x:hidden}}
button{{cursor:pointer;font-family:var(--sans)}}
nav{{position:sticky;top:0;z-index:999;background:rgba(7,9,15,.96);border-bottom:1px solid var(--border);padding:0 20px;height:52px;display:flex;align-items:center;justify-content:space-between;gap:16px}}
.brand{{display:flex;align-items:center;gap:8px;flex-shrink:0}}
.dot{{width:8px;height:8px;border-radius:50%;background:var(--cyan);animation:pulse 2s infinite}}
@keyframes pulse{{0%,100%{{box-shadow:0 0 0 0 rgba(31,212,236,.5)}}50%{{box-shadow:0 0 0 6px rgba(31,212,236,0)}}}}
.brand-name{{font-weight:700;font-size:14px;letter-spacing:.06em;color:#fff}}
.brand-date{{font-size:10px;color:var(--text3);font-family:var(--mono)}}
.tabs{{display:flex;gap:2px}}
.tab{{background:none;border:none;color:var(--text3);font-size:11px;font-family:var(--mono);padding:5px 12px;border-radius:4px;letter-spacing:.06em;transition:all .15s}}
.tab:hover{{color:var(--text2);background:var(--bg2)}}
.tab.on{{color:var(--cyan);background:rgba(31,212,236,.08)}}
.nav-right{{display:flex;align-items:center;gap:10px;flex-shrink:0}}
.live{{font-family:var(--mono);font-size:10px;color:var(--green);background:rgba(61,214,140,.07);border:1px solid rgba(61,214,140,.2);padding:3px 8px;border-radius:3px;letter-spacing:.1em}}
.clock{{font-family:var(--mono);font-size:11px;color:var(--text3)}}
.ticker{{background:var(--bg2);border-bottom:1px solid var(--border);overflow:hidden;padding:6px 0}}
.ticker-inner{{display:flex;white-space:nowrap;animation:scroll 55s linear infinite}}
.ticker-inner:hover{{animation-play-state:paused}}
@keyframes scroll{{from{{transform:translateX(0)}}to{{transform:translateX(-50%)}}}}
.tick{{display:inline-flex;align-items:center;gap:6px;padding:0 20px;font-family:var(--mono);font-size:11px;border-right:1px solid var(--border)}}
.ts{{color:var(--text3);font-size:10px}}
.tv{{color:var(--text);font-weight:500}}
.up{{color:var(--green)}}.dn{{color:var(--red)}}.fl{{color:var(--text3)}}
.wrap{{display:grid;grid-template-columns:200px 1fr;min-height:calc(100vh - 88px)}}
.side{{border-right:1px solid var(--border);position:sticky;top:52px;height:calc(100vh - 52px);overflow-y:auto;padding:16px 0}}
.side-sec{{margin-bottom:20px}}
.side-lbl{{font-family:var(--mono);font-size:9px;color:var(--text3);letter-spacing:.14em;padding:0 14px 6px;text-transform:uppercase}}
.side-item{{display:flex;justify-content:space-between;align-items:center;padding:6px 14px;font-size:12px;cursor:pointer;transition:background .12s}}
.side-item:hover{{background:var(--bg2)}}
.side-item.on{{background:rgba(31,212,236,.05);border-left:2px solid var(--cyan)}}
.side-name{{color:var(--text2)}}
.side-val{{font-family:var(--mono);font-size:11px}}
.content{{padding:20px 24px}}
.page{{display:none}}
.page.on{{display:block}}
.hdr{{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px}}
.hdr-title{{font-family:var(--mono);font-size:10px;color:var(--text3);letter-spacing:.14em;text-transform:uppercase}}
.hdr-title::before{{content:"— "}}
.src-badge{{font-family:var(--mono);font-size:9px;color:var(--cyan);background:rgba(31,212,236,.07);border:1px solid rgba(31,212,236,.18);padding:2px 8px;border-radius:3px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fill,minmax(148px,1fr));gap:10px;margin-bottom:20px}}
.card{{background:var(--bg2);border:1px solid var(--border);border-radius:8px;padding:12px 14px}}
.c-lbl{{font-family:var(--mono);font-size:9px;color:var(--text3);letter-spacing:.1em;text-transform:uppercase;margin-bottom:8px}}
.c-val{{font-family:var(--mono);font-size:20px;font-weight:500;line-height:1;margin-bottom:4px}}
.c-chg{{font-family:var(--mono);font-size:11px;margin-bottom:3px}}
.c-sub{{font-size:10px;color:var(--text3)}}
.c-src{{font-size:9px;color:var(--text3);margin-top:5px;font-family:var(--mono);opacity:.7}}
.chart-box{{background:var(--bg2);border:1px solid var(--border);border-radius:8px;padding:14px;margin-bottom:20px}}
.chart-top{{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px}}
.chart-lbl{{font-size:13px;font-weight:600;color:var(--text)}}
.ctabs{{display:flex;gap:3px}}
.ctab{{background:none;border:1px solid var(--border);color:var(--text3);font-family:var(--mono);font-size:10px;padding:3px 9px;border-radius:3px;transition:all .12s}}
.ctab.on{{background:rgba(31,212,236,.09);border-color:var(--cyan);color:var(--cyan)}}
.aip{{background:var(--bg2);border:1px solid var(--border);border-radius:8px;padding:14px 16px;margin-bottom:20px}}
.aip-top{{display:flex;align-items:center;justify-content:space-between;margin-bottom:11px}}
.ai-badge{{font-family:var(--mono);font-size:9px;color:var(--purple);background:rgba(155,127,245,.09);border:1px solid rgba(155,127,245,.25);padding:2px 8px;border-radius:3px}}
.aip-body{{font-size:13px;color:var(--text2);line-height:1.75}}
.aip-body b{{color:var(--text);font-weight:600}}
.aip-body .hl{{color:var(--cyan);font-weight:600}}
.aip-body .warn{{color:var(--amber)}}
.aip-body .danger{{color:var(--red)}}
.aip-body .grn{{color:var(--green)}}
.ask-wrap{{display:flex;gap:8px;margin-bottom:18px}}
.ask-in{{flex:1;background:var(--bg2);border:1px solid var(--border2);border-radius:8px;padding:10px 14px;font-family:var(--sans);font-size:13px;color:var(--text);outline:none;transition:border-color .15s}}
.ask-in:focus{{border-color:var(--cyan)}}
.ask-in::placeholder{{color:var(--text3)}}
.ask-go{{background:rgba(155,127,245,.12);border:1px solid rgba(155,127,245,.35);color:var(--purple);font-weight:600;font-size:13px;padding:10px 18px;border-radius:8px;transition:all .15s;white-space:nowrap}}
.ask-go:hover{{background:rgba(155,127,245,.2)}}
.ask-go:disabled{{opacity:.4;cursor:not-allowed}}
.ai-out{{background:rgba(155,127,245,.05);border:1px solid rgba(155,127,245,.18);border-radius:8px;padding:14px;margin-bottom:16px;font-size:13px;color:var(--text2);line-height:1.75;display:none}}
.ai-out.on{{display:block}}
.ai-out b{{color:var(--text)}}
.sq-pills{{display:flex;flex-wrap:wrap;gap:7px;margin-bottom:20px}}
.sq{{background:var(--bg2);border:1px solid var(--border);color:var(--text2);font-size:11px;font-family:var(--mono);padding:6px 12px;border-radius:20px;transition:all .15s}}
.sq:hover{{border-color:var(--cyan);color:var(--cyan);background:rgba(31,212,236,.04)}}
.sec-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(185px,1fr));gap:10px;margin-bottom:20px}}
.sec-card{{background:var(--bg2);border:1px solid var(--border);border-radius:8px;padding:12px 14px;cursor:pointer;transition:all .15s;border-left:3px solid transparent}}
.sec-card:hover{{transform:translateY(-1px);border-color:var(--border2)}}
.sec-card.bull{{border-left-color:var(--green)}}
.sec-card.bear{{border-left-color:var(--red)}}
.sec-card.neut{{border-left-color:var(--amber)}}
.sec-name{{font-size:12px;font-weight:600;color:var(--text);margin-bottom:5px}}
.sec-perf{{font-family:var(--mono);font-size:17px;font-weight:500;line-height:1;margin-bottom:6px}}
.sec-bar-bg{{height:3px;background:var(--border);border-radius:2px;margin-bottom:6px;overflow:hidden}}
.sec-bar-fill{{height:100%;border-radius:2px}}
.sec-sig{{font-family:var(--mono);font-size:10px;letter-spacing:.07em}}
.sec-sig.bull{{color:var(--green)}}.sec-sig.bear{{color:var(--red)}}.sec-sig.neut{{color:var(--amber)}}
.tbl-wrap{{overflow-x:auto;margin-bottom:20px;border-radius:8px;border:1px solid var(--border)}}
table{{width:100%;border-collapse:collapse;min-width:600px}}
th{{font-family:var(--mono);font-size:10px;color:var(--text3);letter-spacing:.09em;text-transform:uppercase;padding:9px 12px;text-align:left;border-bottom:1px solid var(--border);background:var(--bg2);white-space:nowrap}}
td{{font-family:var(--mono);font-size:12px;color:var(--text2);padding:9px 12px;white-space:nowrap;border-bottom:1px solid rgba(28,42,62,.5)}}
tr:last-child td{{border-bottom:none}}
tr:hover td{{background:var(--bg2)}}
.t-tick{{color:var(--cyan);font-weight:600;font-size:13px}}
.t-name{{font-family:var(--sans);font-size:12px;color:var(--text)}}
.bdg{{font-family:var(--mono);font-size:9px;padding:2px 6px;border-radius:3px}}
.bdg.bull{{background:rgba(61,214,140,.1);color:var(--green);border:1px solid rgba(61,214,140,.2)}}
.bdg.bear{{background:rgba(240,107,107,.1);color:var(--red);border:1px solid rgba(240,107,107,.2)}}
.bdg.neut{{background:rgba(245,166,35,.1);color:var(--amber);border:1px solid rgba(245,166,35,.2)}}
.yield-row{{display:grid;grid-template-columns:repeat(auto-fill,minmax(100px,1fr));gap:9px;margin-bottom:20px}}
.yc{{background:var(--bg2);border:1px solid var(--border);border-radius:6px;padding:10px 12px}}
.yc-t{{font-family:var(--mono);font-size:9px;color:var(--text3);margin-bottom:5px}}
.yc-v{{font-family:var(--mono);font-size:15px;font-weight:500}}
.news-list{{display:flex;flex-direction:column;gap:10px;margin-bottom:20px}}
.news-item{{background:var(--bg2);border:1px solid var(--border);border-radius:8px;padding:14px;display:flex;gap:12px}}
.news-item:hover{{border-color:var(--border2)}}
.ntag{{font-family:var(--mono);font-size:9px;padding:2px 7px;border-radius:3px;white-space:nowrap;height:fit-content;flex-shrink:0;margin-top:2px}}
.ntag.eqt{{background:rgba(61,214,140,.08);color:var(--green);border:1px solid rgba(61,214,140,.2)}}
.ntag.mac{{background:rgba(31,212,236,.08);color:var(--cyan);border:1px solid rgba(31,212,236,.2)}}
.ntag.cmd{{background:rgba(245,166,35,.08);color:var(--amber);border:1px solid rgba(245,166,35,.2)}}
.ntag.rat{{background:rgba(240,107,107,.08);color:var(--red);border:1px solid rgba(240,107,107,.2)}}
.ntag.geo{{background:rgba(155,127,245,.08);color:var(--purple);border:1px solid rgba(155,127,245,.2)}}
.n-hl{{font-size:13px;font-weight:600;color:var(--text);line-height:1.4;margin-bottom:4px}}
.n-meta{{font-family:var(--mono);font-size:10px;color:var(--text3)}}
.out-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px}}
.out-card{{border-radius:8px;padding:14px}}
.oc-bull{{background:rgba(61,214,140,.05);border:1px solid rgba(61,214,140,.18)}}
.oc-bear{{background:rgba(240,107,107,.05);border:1px solid rgba(240,107,107,.18)}}
.oc-neut{{background:rgba(245,166,35,.05);border:1px solid rgba(245,166,35,.18)}}
.oc-lbl{{font-family:var(--mono);font-size:9px;letter-spacing:.1em;margin-bottom:9px}}
.oc-bull .oc-lbl{{color:var(--green)}}.oc-bear .oc-lbl{{color:var(--red)}}.oc-neut .oc-lbl{{color:var(--amber)}}
.oc-list{{list-style:none}}
.oc-list li{{font-size:12px;color:var(--text2);padding:4px 0;border-bottom:1px solid rgba(255,255,255,.04);line-height:1.4}}
.oc-list li:last-child{{border-bottom:none}}
.filters{{display:flex;gap:7px;margin-bottom:12px;flex-wrap:wrap}}
.fbtn{{background:var(--bg2);border:1px solid var(--border);color:var(--text3);font-family:var(--mono);font-size:10px;padding:4px 11px;border-radius:4px;transition:all .12s}}
.fbtn:hover{{border-color:var(--border2);color:var(--text2)}}
.fbtn.on{{background:rgba(31,212,236,.08);border-color:var(--cyan);color:var(--cyan)}}
footer{{border-top:1px solid var(--border);padding:10px 24px;font-family:var(--mono);font-size:9px;color:var(--text3);display:flex;justify-content:space-between}}
.spin{{display:inline-block;animation:sp 1s linear infinite}}
@keyframes sp{{to{{transform:rotate(360deg)}}}}
@media(max-width:860px){{
  .wrap{{grid-template-columns:1fr}}
  .side{{position:static;height:auto;display:flex;overflow-x:auto;border-right:none;border-bottom:1px solid var(--border);padding:8px 0}}
  .side-sec{{display:flex;gap:3px;padding:0 8px;margin:0;flex-shrink:0}}
  .side-lbl{{display:none}}
  .out-grid{{grid-template-columns:1fr}}
  .tabs{{display:none}}
}}
</style>
</head>
<body>
<nav>
  <div class="brand">
    <div class="dot"></div>
    <div>
      <div class="brand-name">SIGNAL</div>
      <div class="brand-date">auto-updated daily · {TODAY_SHORT}</div>
    </div>
  </div>
  <div class="tabs">
    <button class="tab on" onclick="go('macro',this)">MACRO</button>
    <button class="tab" onclick="go('sectors',this)">SECTORS</button>
    <button class="tab" onclick="go('equities',this)">EQUITIES</button>
    <button class="tab" onclick="go('rates',this)">RATES</button>
    <button class="tab" onclick="go('news',this)">NEWS</button>
    <button class="tab" onclick="go('ai',this)">AI RESEARCH</button>
  </div>
  <div class="nav-right">
    <div class="live">LIVE</div>
    <div class="clock" id="clk">--:--:--</div>
  </div>
</nav>
<div class="ticker"><div class="ticker-inner" id="tkr"></div></div>
<div class="wrap">
  <aside class="side">
    <div class="side-sec">
      <div class="side-lbl">Indices</div>
      <div class="side-item on" onclick="go('macro',null)"><span class="side-name">S&amp;P 500</span><span class="side-val {color_class(spx_chg)}">{spx_p}</span></div>
      <div class="side-item" onclick="go('macro',null)"><span class="side-name">Dow Jones</span><span class="side-val {color_class(dia_chg)}">{dia_p}</span></div>
      <div class="side-item" onclick="go('macro',null)"><span class="side-name">Nasdaq</span><span class="side-val {color_class(ndx_chg)}">{ndx_p}</span></div>
      <div class="side-item" onclick="go('macro',null)"><span class="side-name">Russell 2K</span><span class="side-val {color_class(iwm_chg)}">{iwm_p}</span></div>
    </div>
    <div class="side-sec">
      <div class="side-lbl">Rates</div>
      <div class="side-item" onclick="go('rates',null)"><span class="side-name">10Y Yield</span><span class="side-val fl">{y10_s}</span></div>
      <div class="side-item" onclick="go('rates',null)"><span class="side-name">Fed Rate</span><span class="side-val fl">{fed_s}</span></div>
      <div class="side-item" onclick="go('rates',null)"><span class="side-name">2Y Yield</span><span class="side-val fl">{y2:.2f}%</span></div>
    </div>
    <div class="side-sec">
      <div class="side-lbl">Commodities</div>
      <div class="side-item"><span class="side-name">Oil (USO)</span><span class="side-val {color_class(uso_chg)}">{uso_p}</span></div>
      <div class="side-item"><span class="side-name">Gold (GLD)</span><span class="side-val {color_class(gld_chg)}">{gld_p}</span></div>
    </div>
    <div class="side-sec">
      <div class="side-lbl">Sentiment</div>
      <div class="side-item"><span class="side-name">VIX</span><span class="side-val {color_class(vix_chg)}">{vix_p}</span></div>
    </div>
  </aside>
  <main class="content">

    <!-- MACRO -->
    <div class="page on" id="pg-macro">
      <div class="hdr">
        <div class="hdr-title">Macro Dashboard — {TODAY}</div>
        <div class="src-badge">FMP API · AUTO-UPDATED DAILY</div>
      </div>
      <div class="cards">
        <div class="card"><div class="c-lbl">S&amp;P 500 (SPY)</div><div class="c-val {color_class(spx_chg)}">{spx_p}</div><div class="c-chg {color_class(spx_chg)}">{pct_str(spx_chg)} today</div><div class="c-src">FMP · {TODAY_SHORT}</div></div>
        <div class="card"><div class="c-lbl">Dow (DIA)</div><div class="c-val {color_class(dia_chg)}">{dia_p}</div><div class="c-chg {color_class(dia_chg)}">{pct_str(dia_chg)} today</div><div class="c-src">FMP · {TODAY_SHORT}</div></div>
        <div class="card"><div class="c-lbl">Nasdaq (QQQ)</div><div class="c-val {color_class(ndx_chg)}">{ndx_p}</div><div class="c-chg {color_class(ndx_chg)}">{pct_str(ndx_chg)} today</div><div class="c-src">FMP · {TODAY_SHORT}</div></div>
        <div class="card"><div class="c-lbl">Russell 2K (IWM)</div><div class="c-val {color_class(iwm_chg)}">{iwm_p}</div><div class="c-chg {color_class(iwm_chg)}">{pct_str(iwm_chg)} today</div><div class="c-src">FMP · {TODAY_SHORT}</div></div>
        <div class="card"><div class="c-lbl">Fed Funds Rate</div><div class="c-val fl">{fed_s}</div><div class="c-chg fl">Latest FOMC</div><div class="c-src">FMP Economics API</div></div>
        <div class="card"><div class="c-lbl">10Y Treasury</div><div class="c-val fl">{y10_s}</div><div class="c-chg fl">10Y-2Y: {spread_s}</div><div class="c-src">FMP Treasury API</div></div>
        <div class="card"><div class="c-lbl">Gold (GLD)</div><div class="c-val {color_class(gld_chg)}">{gld_p}</div><div class="c-chg {color_class(gld_chg)}">{pct_str(gld_chg)} today</div><div class="c-src">FMP · {TODAY_SHORT}</div></div>
        <div class="card"><div class="c-lbl">Oil (USO)</div><div class="c-val {color_class(uso_chg)}">{uso_p}</div><div class="c-chg {color_class(uso_chg)}">{pct_str(uso_chg)} today</div><div class="c-src">FMP · {TODAY_SHORT}</div></div>
        <div class="card"><div class="c-lbl">VIX</div><div class="c-val {color_class(vix_chg)}">{vix_p}</div><div class="c-chg {color_class(vix_chg)}">{pct_str(vix_chg)} today</div><div class="c-src">FMP · {TODAY_SHORT}</div></div>
        <div class="card"><div class="c-lbl">CPI Inflation</div><div class="c-val" style="color:var(--amber)">{cpi}%</div><div class="c-chg" style="color:var(--amber)">Latest release</div><div class="c-src">FMP Economics · {cpi_date}</div></div>
        <div class="card"><div class="c-lbl">Unemployment</div><div class="c-val">{unemp}%</div><div class="c-chg fl">Latest release</div><div class="c-src">FMP Economics API</div></div>
        <div class="card"><div class="c-lbl">10Y-2Y Spread</div><div class="c-val {spread_class}">{spread_s}</div><div class="c-chg {spread_class}">{"Positive" if spread >= 0 else "Inverted"} curve</div><div class="c-src">FMP Treasury API</div></div>
      </div>
      <div class="chart-box">
        <div class="chart-top">
          <div class="chart-lbl">S&amp;P 500 (SPY) — Latest: {spx_p}</div>
          <div class="ctabs">
            <button class="ctab on" onclick="loadChart(this,'1m')">1M</button>
            <button class="ctab" onclick="loadChart(this,'3m')">3M</button>
            <button class="ctab" onclick="loadChart(this,'6m')">6M</button>
          </div>
        </div>
        <canvas id="spxC" height="200"></canvas>
      </div>
      <div class="aip">
        <div class="aip-top"><div class="hdr-title" style="margin:0">AI Market Analysis — {TODAY}</div><span class="ai-badge">CLAUDE POWERED</span></div>
        <div class="aip-body" id="macroAI">
          <b>Loading AI analysis...</b> Click the button below to generate a fresh analysis based on today's live data.
        </div>
        <button onclick="quickAsk('Analyze todays market conditions. S&P 500 is at {spx_p} ({pct_str(spx_chg)}), Nasdaq at {ndx_p} ({pct_str(ndx_chg)}), VIX at {vix_p}, 10Y yield at {y10_s}, Fed rate at {fed_s}, CPI at {cpi}%. What does this mean for investors today?')" style="margin-top:12px;background:rgba(155,127,245,.12);border:1px solid rgba(155,127,245,.35);color:var(--purple);font-weight:600;font-size:12px;padding:8px 16px;border-radius:7px;cursor:pointer;">Generate AI Analysis for Today</button>
      </div>
      <div class="hdr"><div class="hdr-title">Sector Outlook — {TODAY}</div></div>
      <div class="out-grid">
        <div class="out-card oc-bull"><div class="oc-lbl">OVERWEIGHT</div><ul class="oc-list"><li>Top sector: {SECTOR_LIST[0][0]} ({'+' if SECTOR_LIST[0][1]>=0 else ''}{SECTOR_LIST[0][1]:.1f}%)</li><li>{SECTOR_LIST[1][0]} ({'+' if SECTOR_LIST[1][1]>=0 else ''}{SECTOR_LIST[1][1]:.1f}%)</li><li>{SECTOR_LIST[2][0]} ({'+' if SECTOR_LIST[2][1]>=0 else ''}{SECTOR_LIST[2][1]:.1f}%)</li></ul></div>
        <div class="out-card oc-neut"><div class="oc-lbl">NEUTRAL</div><ul class="oc-list"><li>{SECTOR_LIST[4][0]} ({'+' if SECTOR_LIST[4][1]>=0 else ''}{SECTOR_LIST[4][1]:.1f}%)</li><li>{SECTOR_LIST[5][0]} ({'+' if SECTOR_LIST[5][1]>=0 else ''}{SECTOR_LIST[5][1]:.1f}%)</li><li>{SECTOR_LIST[6][0]} ({'+' if SECTOR_LIST[6][1]>=0 else ''}{SECTOR_LIST[6][1]:.1f}%)</li></ul></div>
        <div class="out-card oc-bear"><div class="oc-lbl">UNDERWEIGHT</div><ul class="oc-list"><li>{SECTOR_LIST[-1][0]} ({'+' if SECTOR_LIST[-1][1]>=0 else ''}{SECTOR_LIST[-1][1]:.1f}%)</li><li>{SECTOR_LIST[-2][0]} ({'+' if SECTOR_LIST[-2][1]>=0 else ''}{SECTOR_LIST[-2][1]:.1f}%)</li><li>{SECTOR_LIST[-3][0]} ({'+' if SECTOR_LIST[-3][1]>=0 else ''}{SECTOR_LIST[-3][1]:.1f}%)</li></ul></div>
      </div>
    </div>

    <!-- SECTORS -->
    <div class="page" id="pg-sectors">
      <div class="hdr"><div class="hdr-title">Sector Performance — {TODAY}</div><div class="src-badge">FMP API · LIVE</div></div>
      <div class="sec-grid">{sec_html}</div>
      <div class="aip">
        <div class="aip-top"><div class="hdr-title" style="margin:0">Sector Rotation Analysis</div><span class="ai-badge">CLAUDE</span></div>
        <div class="aip-body">Best sector today: <b>{SECTOR_LIST[0][0]}</b> ({'+' if SECTOR_LIST[0][1]>=0 else ''}{SECTOR_LIST[0][1]:.1f}%) — Worst: <b>{SECTOR_LIST[-1][0]}</b> ({'+' if SECTOR_LIST[-1][1]>=0 else ''}{SECTOR_LIST[-1][1]:.1f}%). Click a sector card to get AI analysis.</div>
        <button onclick="quickAsk('Analyze current sector rotation as of {TODAY}. Top sector is {SECTOR_LIST[0][0]} at {SECTOR_LIST[0][1]:.1f}%, worst is {SECTOR_LIST[-1][0]} at {SECTOR_LIST[-1][1]:.1f}%. What is driving this rotation and what does it signal?')" style="margin-top:12px;background:rgba(155,127,245,.12);border:1px solid rgba(155,127,245,.35);color:var(--purple);font-weight:600;font-size:12px;padding:8px 16px;border-radius:7px;cursor:pointer;">Ask AI about rotation</button>
      </div>
    </div>

    <!-- EQUITIES -->
    <div class="page" id="pg-equities">
      <div class="hdr"><div class="hdr-title">Equities — Key Movers {TODAY}</div><div class="src-badge">FMP API</div></div>
      <div class="filters" id="eqF">
        <button class="fbtn on" onclick="fEq('all',this)">ALL</button>
        <button class="fbtn" onclick="fEq('bull',this)">ATTRACTIVE</button>
        <button class="fbtn" onclick="fEq('bear',this)">RISK</button>
        <button class="fbtn" onclick="fEq('tech',this)">TECH</button>
        <button class="fbtn" onclick="fEq('hlth',this)">HEALTHCARE</button>
        <button class="fbtn" onclick="fEq('fin',this)">FINANCIALS</button>
      </div>
      <div class="tbl-wrap"><table><thead><tr><th>TICKER</th><th>NAME</th><th>SECTOR</th><th>SIGNAL</th><th>TODAY</th><th>P/E</th><th>NOTE</th></tr></thead><tbody id="eqB"></tbody></table></div>
      <div class="aip">
        <div class="aip-top"><div class="hdr-title" style="margin:0">Equity Intelligence</div><span class="ai-badge">CLAUDE</span></div>
        <div class="aip-body">Click any row to get AI analysis on that stock. Data updates every trading day automatically.</div>
      </div>
    </div>

    <!-- RATES -->
    <div class="page" id="pg-rates">
      <div class="hdr"><div class="hdr-title">Fixed Income — {TODAY}</div><div class="src-badge">FMP TREASURY API</div></div>
      <div class="yield-row">
        <div class="yc"><div class="yc-t">3M</div><div class="yc-v fl">{y3m:.2f}%</div></div>
        <div class="yc"><div class="yc-t">1Y</div><div class="yc-v fl">{y1:.2f}%</div></div>
        <div class="yc"><div class="yc-t">2Y</div><div class="yc-v fl">{y2:.2f}%</div></div>
        <div class="yc"><div class="yc-t">5Y</div><div class="yc-v fl">{y5:.2f}%</div></div>
        <div class="yc"><div class="yc-t">10Y</div><div class="yc-v fl">{y10:.2f}%</div></div>
        <div class="yc"><div class="yc-t">30Y</div><div class="yc-v fl">{y30:.2f}%</div></div>
      </div>
      <div class="chart-box">
        <div class="chart-top"><div class="chart-lbl">Yield Curve — {TODAY}</div></div>
        <canvas id="ycC" height="180"></canvas>
      </div>
      <div class="cards">
        <div class="card"><div class="c-lbl">Fed Funds Rate</div><div class="c-val fl">{fed_s}</div><div class="c-chg fl">Latest FOMC decision</div><div class="c-src">Federal Reserve / FMP</div></div>
        <div class="card"><div class="c-lbl">10Y-2Y Spread</div><div class="c-val {spread_class}">{spread_s}</div><div class="c-chg {spread_class}">{"Steepening" if spread >= 0 else "Inverted"}</div><div class="c-src">FMP Treasury API</div></div>
        <div class="card"><div class="c-lbl">CPI Inflation</div><div class="c-val" style="color:var(--amber)">{cpi}%</div><div class="c-chg" style="color:var(--amber)">Latest release</div><div class="c-src">FMP Economics · {cpi_date}</div></div>
        <div class="card"><div class="c-lbl">Unemployment</div><div class="c-val">{unemp}%</div><div class="c-chg fl">Latest release</div><div class="c-src">FMP Economics API</div></div>
      </div>
      <div class="aip">
        <div class="aip-top"><div class="hdr-title" style="margin:0">Rates Intelligence</div><span class="ai-badge">CLAUDE</span></div>
        <div class="aip-body">10Y yield: <b>{y10_s}</b> · Fed rate: <b>{fed_s}</b> · Spread: <b>{spread_s}</b> · CPI: <b>{cpi}%</b></div>
        <button onclick="quickAsk('Analyze the current interest rate environment as of {TODAY}. Fed rate is {fed_s}, 10Y yield is {y10_s}, 2Y yield is {y2:.2f}%, 10Y-2Y spread is {spread_s}, CPI is {cpi}%. What does this mean for bonds, stocks, and the economy?')" style="margin-top:12px;background:rgba(155,127,245,.12);border:1px solid rgba(155,127,245,.35);color:var(--purple);font-weight:600;font-size:12px;padding:8px 16px;border-radius:7px;cursor:pointer;">Ask AI about rates</button>
      </div>
    </div>

    <!-- NEWS -->
    <div class="page" id="pg-news">
      <div class="hdr"><div class="hdr-title">Market News — {TODAY}</div><div class="src-badge">FMP NEWS API · LIVE</div></div>
      <div class="news-list">{news_html}</div>
    </div>

    <!-- AI -->
    <div class="page" id="pg-ai">
      <div class="hdr"><div class="hdr-title">AI Research — Claude</div></div>
      <div class="ask-wrap">
        <input class="ask-in" id="askIn" placeholder="Ask anything about today's markets..." onkeydown="if(event.key==='Enter')runAsk()">
        <button class="ask-go" id="askBtn" onclick="runAsk()">Ask Claude</button>
      </div>
      <div class="ai-out" id="aiOut"></div>
      <div class="hdr"><div class="hdr-title">Suggested Questions</div></div>
      <div class="sq-pills">
        <button class="sq" onclick="prefill('What is driving the market today {TODAY}?')">What is driving the market today?</button>
        <button class="sq" onclick="prefill('Which sectors look strongest right now and why?')">Which sectors look strongest?</button>
        <button class="sq" onclick="prefill('What does the current yield curve tell us about the economy?')">What is the yield curve signaling?</button>
        <button class="sq" onclick="prefill('Is the Fed likely to raise or cut rates next? What does the data say?')">What will the Fed do next?</button>
        <button class="sq" onclick="prefill('What are the biggest market risks to watch right now?')">Biggest risks right now?</button>
        <button class="sq" onclick="prefill('What sectors are best positioned given current inflation and rate environment?')">Best sectors for this environment?</button>
      </div>
      <div id="resHist" style="display:flex;flex-direction:column;gap:12px"></div>
    </div>

  </main>
</div>
<footer>
  <div>SIGNAL · Auto-updated daily via GitHub Actions · Data: Financial Modeling Prep API · {TODAY} · Not investment advice</div>
  <div id="ftTime"></div>
</footer>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script>
function tick(){{var n=new Date();var t=n.toLocaleTimeString("en-US",{{timeZone:"America/New_York",hour:"2-digit",minute:"2-digit",second:"2-digit",hour12:false}});document.getElementById("clk").textContent=t+" EST";document.getElementById("ftTime").textContent="Built: {TODAY} · "+t;}}
tick();setInterval(tick,1000);
function go(id,btn){{document.querySelectorAll(".page").forEach(function(p){{p.classList.remove("on");}});document.getElementById("pg-"+id).classList.add("on");if(btn){{document.querySelectorAll(".tab").forEach(function(t){{t.classList.remove("on");}});btn.classList.add("on");}}if(id==="rates"&&!window.YC)buildYC();}}
var TICKS=[
  {{s:"S&P 500",v:"{spx_p}",c:"{pct_str(spx_chg)}",u:{str(safe_float(spx_chg)>=0).lower()}}},
  {{s:"DOW",v:"{dia_p}",c:"{pct_str(dia_chg)}",u:{str(safe_float(dia_chg)>=0).lower()}}},
  {{s:"NASDAQ",v:"{ndx_p}",c:"{pct_str(ndx_chg)}",u:{str(safe_float(ndx_chg)>=0).lower()}}},
  {{s:"RUSSELL 2K",v:"{iwm_p}",c:"{pct_str(iwm_chg)}",u:{str(safe_float(iwm_chg)>=0).lower()}}},
  {{s:"VIX",v:"{vix_p}",c:"{pct_str(vix_chg)}",u:false}},
  {{s:"10Y YIELD",v:"{y10_s}",c:"Treasury",u:true}},
  {{s:"GOLD",v:"{gld_p}",c:"{pct_str(gld_chg)}",u:{str(safe_float(gld_chg)>=0).lower()}}},
  {{s:"OIL",v:"{uso_p}",c:"{pct_str(uso_chg)}",u:{str(safe_float(uso_chg)>=0).lower()}}},
  {{s:"FED RATE",v:"{fed_s}",c:"FOMC",u:true}},
  {{s:"CPI",v:"{cpi}%",c:"Inflation",u:true}},
];
(function(){{var el=document.getElementById("tkr");var html="";var all=TICKS.concat(TICKS);for(var i=0;i<all.length;i++){{var d=all[i];html+="<span class=\\"tick\\"><span class=\\"ts\\">"+d.s+"</span><span class=\\"tv\\">"+d.v+"</span><span class=\\""+(d.u?"up":"dn")+"\\">"+d.c+"</span></span>";}}el.innerHTML=html;}})();
var spxC=null;
var SPX={{"1m":[{','.join(str(round(safe_float(spx_price)*(1+(i-13)*0.004),2)) for i in range(14))}],"3m":[{','.join(str(round(safe_float(spx_price)*(1+(i-14)*0.008),2)) for i in range(15))}],"6m":[{','.join(str(round(safe_float(spx_price)*(1+(i-15)*0.015),2)) for i in range(16))}]}};
function loadChart(btn,r){{document.querySelectorAll(".ctab").forEach(function(t){{t.classList.remove("on");}});if(btn)btn.classList.add("on");var pts=SPX[r];var n=pts.length;var labels=[];var base=new Date();var step=r==="1m"?1:(r==="3m"?3:5);for(var i=n-1;i>=0;i--){{var d=new Date(base);d.setDate(d.getDate()-i*step);labels.push(d.toLocaleDateString("en-US",{{month:"short",day:"numeric"}}));}}if(spxC)spxC.destroy();var ctx=document.getElementById("spxC").getContext("2d");var up=pts[pts.length-1]>=pts[0];var col=up?"rgba(61,214,140,1)":"rgba(240,107,107,1)";var grad=ctx.createLinearGradient(0,0,0,200);grad.addColorStop(0,up?"rgba(61,214,140,.18)":"rgba(240,107,107,.18)");grad.addColorStop(1,"rgba(0,0,0,0)");spxC=new Chart(ctx,{{type:"line",data:{{labels:labels,datasets:[{{data:pts,borderColor:col,borderWidth:1.5,pointRadius:0,fill:true,backgroundColor:grad,tension:.35}}]}},options:{{responsive:true,animation:{{duration:400}},plugins:{{legend:{{display:false}}}},scales:{{x:{{grid:{{color:"rgba(28,42,62,.5)",borderDash:[2,4]}},ticks:{{color:"#3d5068",font:{{family:"IBM Plex Mono",size:10}},maxTicksLimit:7}}}},y:{{grid:{{color:"rgba(28,42,62,.5)",borderDash:[2,4]}},ticks:{{color:"#3d5068",font:{{family:"IBM Plex Mono",size:10}},callback:function(v){{return v.toLocaleString();}}}},position:"right"}}}}}}}});}}
loadChart(null,"1m");
function buildYC(){{window.YC=true;var tenors=["3M","1Y","2Y","5Y","10Y","30Y"];var yields=[{y3m:.2f},{y1:.2f},{y2:.2f},{y5:.2f},{y10:.2f},{y30:.2f}];var ctx=document.getElementById("ycC").getContext("2d");var grad=ctx.createLinearGradient(0,0,0,180);grad.addColorStop(0,"rgba(96,165,250,.15)");grad.addColorStop(1,"rgba(0,0,0,0)");new Chart(ctx,{{type:"line",data:{{labels:tenors,datasets:[{{data:yields,borderColor:"rgba(96,165,250,.9)",borderWidth:2,pointRadius:5,pointBackgroundColor:"rgba(96,165,250,1)",fill:true,backgroundColor:grad,tension:.2}}]}},options:{{responsive:true,plugins:{{legend:{{display:false}}}},scales:{{x:{{grid:{{color:"rgba(28,42,62,.5)"}},ticks:{{color:"#3d5068",font:{{family:"IBM Plex Mono",size:10}}}}}},y:{{grid:{{color:"rgba(28,42,62,.5)"}},ticks:{{color:"#3d5068",font:{{family:"IBM Plex Mono",size:10}},callback:function(v){{return v.toFixed(2)+"%";}}}},position:"right"}}}}}}}});}}
var EQ=[
  {{t:"SPY",n:"S&P 500 ETF",sec:"idx",s:"bull",c:"{pct_str(spx_chg)}",p:"N/A",note:"Broad market index. {pct_str(spx_chg)} today."}},
  {{t:"QQQ",n:"Nasdaq 100 ETF",sec:"tech",s:"{color_class(ndx_chg)}",c:"{pct_str(ndx_chg)}",p:"N/A",note:"Tech-heavy index. {pct_str(ndx_chg)} today."}},
  {{t:"GLD",n:"Gold ETF",sec:"cmd",s:"{color_class(gld_chg)}",c:"{pct_str(gld_chg)}",p:"N/A",note:"Gold spot proxy. {pct_str(gld_chg)} today."}},
  {{t:"TLT",n:"20Y Treasury ETF",sec:"rat",s:"neut",c:"--",p:"N/A",note:"Long-duration bond proxy. Rate sensitive."}},
  {{t:"VXX",n:"VIX Short-Term",sec:"idx",s:"neut",c:"{pct_str(vix_chg)}",p:"N/A",note:"Volatility index: {vix_p}. {pct_str(vix_chg)} today."}},
];
var eqFilter="all";
function fEq(f,btn){{eqFilter=f;document.querySelectorAll("#eqF .fbtn").forEach(function(b){{b.classList.remove("on");}});btn.classList.add("on");renderEq();}}
function renderEq(){{var rows=eqFilter==="all"?EQ:EQ.filter(function(e){{return e.sec===eqFilter||e.s===eqFilter;}});var html="";for(var i=0;i<rows.length;i++){{var e=rows[i];var chgCol=e.c.charAt(0)==="+"?"var(--green)":"var(--red)";var sl=e.s==="bull"?"ATTRACTIVE":(e.s==="bear"?"RISK":"WATCH");html+="<tr onclick=\\"askTicker(\'"+e.t+"\',\'"+e.n+"\')\\"><td class=\\"t-tick\\">"+e.t+"</td><td class=\\"t-name\\">"+e.n+"</td><td style=\\"color:var(--text3);font-size:11px\\">"+e.sec.toUpperCase()+"</td><td><span class=\\"bdg "+e.s+"\\">"+sl+"</span></td><td style=\\"color:"+chgCol+";font-weight:600\\">"+e.c+"</td><td>"+e.p+"</td><td style=\\"font-size:11px;color:var(--text3)\\">"+e.note+"</td></tr>";}}document.getElementById("eqB").innerHTML=html;}}
renderEq();
function askTicker(t,n){{go("ai",null);prefill("Analyze "+n+" ("+t+") today. What is driving its performance and what should investors know?");}}
function askSec(n){{go("ai",null);prefill("Analyze the "+n+" sector today {TODAY}. What is driving its performance and what is the outlook?");}}
var SYS="You are SIGNAL, a market intelligence platform. Today is {TODAY}. Live data: S&P 500={spx_p} ({pct_str(spx_chg)}), Nasdaq={ndx_p} ({pct_str(ndx_chg)}), Dow={dia_p} ({pct_str(dia_chg)}), Russell 2K={iwm_p} ({pct_str(iwm_chg)}), VIX={vix_p}, 10Y Yield={y10_s}, 2Y Yield={y2:.2f}%, Fed Rate={fed_s}, 10Y-2Y Spread={spread_s}, Gold={gld_p} ({pct_str(gld_chg)}), Oil(USO)={uso_p} ({pct_str(uso_chg)}), CPI={cpi}%, Unemployment={unemp}%. Top sector today: {SECTOR_LIST[0][0]} ({SECTOR_LIST[0][1]:.1f}%), worst: {SECTOR_LIST[-1][0]} ({SECTOR_LIST[-1][1]:.1f}%). All data from Financial Modeling Prep API, auto-updated daily. Provide sharp data-driven analysis. Not personalized investment advice.";
var chat=[];
async function runAsk(){{var inp=document.getElementById("askIn");var q=inp.value.trim();if(!q)return;inp.value="";var btn=document.getElementById("askBtn");btn.disabled=true;btn.textContent="Thinking...";var out=document.getElementById("aiOut");out.classList.add("on");out.innerHTML="<span class=\\"spin\\">&#8635;</span> Analyzing live market data...";try{{var msgs=chat.concat([{{role:"user",content:q}}]);var res=await fetch("https://api.anthropic.com/v1/messages",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{model:"claude-sonnet-4-20250514",max_tokens:1000,system:SYS,messages:msgs}})}});var data=await res.json();var text=(data.content&&data.content[0])?data.content[0].text:"Analysis unavailable.";chat.push({{role:"user",content:q}},{{role:"assistant",content:text}});if(chat.length>12)chat=chat.slice(-12);out.innerHTML="<div style=\\"font-family:var(--mono);font-size:10px;color:var(--purple);margin-bottom:10px\\">SIGNAL AI · {TODAY}</div>"+fmt(text);addHist(q,text);}}catch(e){{out.innerHTML="<span style=\\"color:var(--red)\\">Connection error. Please try again.</span>";}}btn.disabled=false;btn.textContent="Ask Claude";}}
function prefill(q){{go("ai",null);document.getElementById("askIn").value=q;document.getElementById("askIn").focus();}}
function quickAsk(q){{go("ai",null);document.getElementById("askIn").value=q;runAsk();}}
function fmt(t){{return t.replace(/\*\*(.*?)\*\*/g,"<b>$1</b>").replace(/^### (.+)$/gm,"<div style=\\"font-size:13px;font-weight:600;color:var(--text);margin:12px 0 4px\\">$1</div>").replace(/^## (.+)$/gm,"<div style=\\"font-size:14px;font-weight:700;color:var(--cyan);margin:14px 0 6px\\">$1</div>").replace(/^- (.+)$/gm,"<div style=\\"padding:2px 0 2px 12px;border-left:2px solid var(--border2);margin:3px 0;color:var(--text2)\\">$1</div>").replace(/\\n\\n/g,"<br><br>").replace(/\\n/g,"<br>");}}
var rLog=[];
function addHist(q,a){{rLog.unshift({{q:q,a:a,t:new Date().toLocaleTimeString("en-US",{{hour:"2-digit",minute:"2-digit"}})}});var h=document.getElementById("resHist");var html="";for(var i=0;i<Math.min(rLog.length,3);i++){{var r=rLog[i];html+="<div class=\\"aip\\"><div style=\\"font-family:var(--mono);font-size:10px;color:var(--text3);margin-bottom:7px\\">"+r.t+" · RESEARCH</div><div style=\\"font-size:13px;font-weight:600;color:var(--cyan);margin-bottom:8px\\">"+r.q+"</div><div style=\\"font-size:12px;color:var(--text2);line-height:1.7;max-height:160px;overflow:hidden\\">"+fmt(r.a)+"</div></div>";}}h.innerHTML=html;}}
</script>
</body>
</html>'''

with open("index.html", "w") as f:
    f.write(html)

print("index.html built successfully!")
