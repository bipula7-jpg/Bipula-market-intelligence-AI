import os, requests, json
from datetime import datetime, date

KEY = os.environ.get("FMP_KEY", "")
TODAY = date.today().strftime("%B %d, %Y")
TODAY_SHORT = date.today().strftime("%b %d, %Y")
BASE = "https://financialmodelingprep.com/api"

print(f"API Key present: {bool(KEY)}")
print(f"Key length: {len(KEY)}")

def get_json(url):
    try:
        r = requests.get(url, timeout=15)
        print(f"  URL: {url[:80]} -> Status: {r.status_code}")
        if r.status_code == 200:
            return r.json()
        else:
            print(f"  Error body: {r.text[:200]}")
            return None
    except Exception as e:
        print(f"  Exception: {e}")
        return None

# ── FETCH QUOTES ──────────────────────────────────────────
print("\nFetching quotes...")
symbols = "SPY,QQQ,DIA,IWM,GLD,USO"
url = f"{BASE}/v3/quote/{symbols}?apikey={KEY}"
data = get_json(url)

q = {}
if isinstance(data, list):
    for item in data:
        sym = item.get("symbol", "")
        q[sym] = item
    print(f"Got quotes for: {list(q.keys())}")
elif isinstance(data, dict) and "Error Message" in data:
    print(f"API Error: {data['Error Message']}")

def qval(sym, field, default=0):
    return q.get(sym, {}).get(field, default) or default

def safe_float(v):
    try: return float(v)
    except: return 0.0

def pct_str(v):
    v = safe_float(v)
    sign = "+" if v >= 0 else ""
    return f"{sign}{v:.2f}%"

def color_class(v):
    v = safe_float(v)
    if v > 0: return "up"
    if v < 0: return "dn"
    return "fl"

def fmt_num(v):
    v = safe_float(v)
    if v == 0: return "--"
    if v > 1000: return f"{v:,.2f}"
    return f"{v:.2f}"

spx_price = qval("SPY","price",0)
spx_chg   = qval("SPY","changesPercentage",0)
ndx_price = qval("QQQ","price",0)
ndx_chg   = qval("QQQ","changesPercentage",0)
dia_price = qval("DIA","price",0)
dia_chg   = qval("DIA","changesPercentage",0)
iwm_price = qval("IWM","price",0)
iwm_chg   = qval("IWM","changesPercentage",0)
gld_price = qval("GLD","price",0)
gld_chg   = qval("GLD","changesPercentage",0)
uso_price = qval("USO","price",0)
uso_chg   = qval("USO","changesPercentage",0)

print(f"S&P(SPY): {spx_price} ({pct_str(spx_chg)})")
print(f"Nasdaq(QQQ): {ndx_price} ({pct_str(ndx_chg)})")

# ── VIX ──────────────────────────────────────────────────
print("\nFetching VIX...")
vix_data = get_json(f"{BASE}/v3/quote/%5EVIX?apikey={KEY}")
vix_price = 0
vix_chg = 0
if isinstance(vix_data, list) and vix_data:
    vix_price = vix_data[0].get("price", 0) or 0
    vix_chg = vix_data[0].get("changesPercentage", 0) or 0
print(f"VIX: {vix_price}")

# ── TREASURY YIELDS ───────────────────────────────────────
print("\nFetching treasury yields...")
treas = get_json(f"{BASE}/v4/treasury?apikey={KEY}")
y3m=y1=y2=y5=y10=y30=0.0
if isinstance(treas, list) and treas:
    t = treas[0]
    y3m = safe_float(t.get("month3",0))
    y1  = safe_float(t.get("year1",0))
    y2  = safe_float(t.get("year2",0))
    y5  = safe_float(t.get("year5",0))
    y10 = safe_float(t.get("year10",0))
    y30 = safe_float(t.get("year30",0))
print(f"10Y: {y10}%, 2Y: {y2}%")

spread = round(y10 - y2, 2)
spread_s = f"{'+' if spread>=0 else ''}{spread:.2f}%"
spread_class = "up" if spread >= 0 else "dn"

# ── ECONOMIC DATA ─────────────────────────────────────────
print("\nFetching economic data...")

# Fed rate
fed_data = get_json(f"{BASE}/v4/economic?name=federalFunds&apikey={KEY}")
fed_rate = 0.0
if isinstance(fed_data, list) and fed_data:
    fed_rate = safe_float(fed_data[0].get("value", 0))
print(f"Fed Rate: {fed_rate}%")

# CPI
cpi_data = get_json(f"{BASE}/v4/economic?name=CPI&apikey={KEY}")
cpi = 0.0
cpi_date = ""
if isinstance(cpi_data, list) and cpi_data:
    cpi = safe_float(cpi_data[0].get("value", 0))
    cpi_date = str(cpi_data[0].get("date",""))[:7]
print(f"CPI: {cpi}%")

# Unemployment
unemp_data = get_json(f"{BASE}/v4/economic?name=unemploymentRate&apikey={KEY}")
unemp = 0.0
if isinstance(unemp_data, list) and unemp_data:
    unemp = safe_float(unemp_data[0].get("value", 0))
print(f"Unemployment: {unemp}%")

# ── SECTOR PERFORMANCE ────────────────────────────────────
print("\nFetching sectors...")
sec_data = get_json(f"{BASE}/v3/sectors-performance?apikey={KEY}")
sec_map = {}
if isinstance(sec_data, list):
    for s in sec_data:
        name = s.get("sector","")
        val = str(s.get("changesPercentage","0")).replace("%","")
        try:
            sec_map[name] = float(val)
        except:
            sec_map[name] = 0.0
print(f"Sectors found: {list(sec_map.keys())[:5]}")

SECTOR_LIST = [
    ("Technology",       sec_map.get("Technology", 0.0)),
    ("Healthcare",       sec_map.get("Healthcare", 0.0)),
    ("Financials",       sec_map.get("Financial Services", 0.0)),
    ("Industrials",      sec_map.get("Industrials", 0.0)),
    ("Energy",           sec_map.get("Energy", 0.0)),
    ("Comm. Services",   sec_map.get("Communication Services", 0.0)),
    ("Materials",        sec_map.get("Basic Materials", 0.0)),
    ("Consumer Disc.",   sec_map.get("Consumer Cyclical", 0.0)),
    ("Consumer Staples", sec_map.get("Consumer Defensive", 0.0)),
    ("Real Estate",      sec_map.get("Real Estate", 0.0)),
    ("Utilities",        sec_map.get("Utilities", 0.0)),
]
SECTOR_LIST.sort(key=lambda x: x[1], reverse=True)

def sec_signal(pct):
    if pct > 0.5: return "bull", "OVERWEIGHT"
    if pct < -0.5: return "bear", "UNDERWEIGHT"
    return "neut", "NEUTRAL"

max_abs = max(abs(s[1]) for s in SECTOR_LIST) or 1
sec_html = ""
for name, pct in SECTOR_LIST:
    sg, lbl = sec_signal(pct)
    col = "var(--green)" if sg=="bull" else ("var(--red)" if sg=="bear" else "var(--amber)")
    sign = "+" if pct >= 0 else ""
    w = round(abs(pct)/max_abs*100)
    # Use escaped name for onclick
    safe_name = name.replace("'","")
    sec_html += f'<div class="sec-card {sg}" onclick="askSec(\'{safe_name}\')">'
    sec_html += f'<div class="sec-name">{name}</div>'
    sec_html += f'<div class="sec-perf" style="color:{col}">{sign}{pct:.2f}%</div>'
    sec_html += f'<div class="sec-bar-bg"><div class="sec-bar-fill" style="width:{w}%;background:{col}"></div></div>'
    sec_html += f'<div class="sec-sig {sg}">{lbl}</div>'
    sec_html += '</div>\n'

# ── NEWS ──────────────────────────────────────────────────
print("\nFetching news...")
news_data = get_json(f"{BASE}/v3/stock_news?limit=8&tickers=SPY,QQQ,AAPL,MSFT,NVDA,AMZN&apikey={KEY}")
news_html = ""
tag_cycle = ["eqt","mac","eqt","mac","cmd","rat","eqt","geo"]
tag_labels = {"eqt":"EQUITY","mac":"MACRO","cmd":"COMMODITIES","rat":"RATES","geo":"GEOPOLITICAL"}
if isinstance(news_data, list) and news_data:
    for i, n in enumerate(news_data[:8]):
        tag = tag_cycle[i % len(tag_cycle)]
        title = str(n.get("title","No title")).replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")
        src = n.get("site","") or n.get("publisher","Financial News")
        pub = str(n.get("publishedDate",""))[:10]
        url = n.get("url","#")
        news_html += f'''<div class="news-item">
<span class="ntag {tag}">{tag_labels.get(tag,tag)}</span>
<div><div class="n-hl"><a href="{url}" target="_blank" style="color:inherit;text-decoration:none">{title}</a></div>
<div class="n-meta">{src} &middot; {pub}</div></div></div>\n'''
else:
    news_html = '<div class="news-item"><span class="ntag mac">MACRO</span><div><div class="n-hl">Market data updated. Check financial news sources for latest headlines.</div><div class="n-meta">SIGNAL &middot; ' + TODAY_SHORT + '</div></div></div>'

# ── FORMAT DISPLAY VALUES ─────────────────────────────────
spx_p   = fmt_num(spx_price)
ndx_p   = fmt_num(ndx_price)
dia_p   = fmt_num(dia_price)
iwm_p   = fmt_num(iwm_price)
gld_p   = fmt_num(gld_price)
uso_p   = fmt_num(uso_price)
vix_p   = f"{safe_float(vix_price):.2f}"
y10_s   = f"{y10:.2f}%"
fed_s   = f"{fed_rate:.2f}%"

# Use fallback labels if data came back 0
spx_display = spx_p if spx_p != "--" else "Market Closed"
ndx_display = ndx_p if ndx_p != "--" else "Market Closed"

top_sec = SECTOR_LIST[0]
bot_sec = SECTOR_LIST[-1]

print(f"\nAll data fetched. Building HTML for {TODAY}...")

# ── BUILD HTML ────────────────────────────────────────────
html = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>SIGNAL — Market Intelligence</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#07090f;--bg2:#0e1420;--bg3:#141d2e;
  --border:#1c2a3e;--border2:#243349;
  --text:#e8edf5;--text2:#8a9ab5;--text3:#3d5068;
  --cyan:#1fd4ec;--green:#3dd68c;--red:#f06b6b;
  --amber:#f5a623;--purple:#9b7ff5;
  --mono:"IBM Plex Mono",monospace;--sans:"Inter",sans-serif;
}
body{background:var(--bg);color:var(--text);font-family:var(--sans);min-height:100vh;overflow-x:hidden}
button{cursor:pointer;font-family:var(--sans)}
nav{position:sticky;top:0;z-index:999;background:rgba(7,9,15,.96);border-bottom:1px solid var(--border);padding:0 20px;height:52px;display:flex;align-items:center;justify-content:space-between;gap:16px}
.brand{display:flex;align-items:center;gap:8px;flex-shrink:0}
.dot{width:8px;height:8px;border-radius:50%;background:var(--cyan);animation:pulse 2s infinite}
@keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(31,212,236,.5)}50%{box-shadow:0 0 0 6px rgba(31,212,236,0)}}
.brand-name{font-weight:700;font-size:14px;letter-spacing:.06em;color:#fff}
.brand-date{font-size:10px;color:var(--text3);font-family:var(--mono)}
.tabs{display:flex;gap:2px}
.tab{background:none;border:none;color:var(--text3);font-size:11px;font-family:var(--mono);padding:5px 12px;border-radius:4px;letter-spacing:.06em;transition:all .15s}
.tab:hover{color:var(--text2);background:var(--bg2)}
.tab.on{color:var(--cyan);background:rgba(31,212,236,.08)}
.nav-right{display:flex;align-items:center;gap:10px;flex-shrink:0}
.live{font-family:var(--mono);font-size:10px;color:var(--green);background:rgba(61,214,140,.07);border:1px solid rgba(61,214,140,.2);padding:3px 8px;border-radius:3px;letter-spacing:.1em}
.clock{font-family:var(--mono);font-size:11px;color:var(--text3)}
.ticker{background:var(--bg2);border-bottom:1px solid var(--border);overflow:hidden;padding:6px 0}
.ticker-inner{display:flex;white-space:nowrap;animation:scroll 55s linear infinite}
.ticker-inner:hover{animation-play-state:paused}
@keyframes scroll{from{transform:translateX(0)}to{transform:translateX(-50%)}}
.tick{display:inline-flex;align-items:center;gap:6px;padding:0 20px;font-family:var(--mono);font-size:11px;border-right:1px solid var(--border)}
.ts{color:var(--text3);font-size:10px}.tv{color:var(--text);font-weight:500}
.up{color:var(--green)}.dn{color:var(--red)}.fl{color:var(--text3)}
.wrap{display:grid;grid-template-columns:200px 1fr;min-height:calc(100vh - 88px)}
.side{border-right:1px solid var(--border);position:sticky;top:52px;height:calc(100vh - 52px);overflow-y:auto;padding:16px 0}
.side-sec{margin-bottom:20px}
.side-lbl{font-family:var(--mono);font-size:9px;color:var(--text3);letter-spacing:.14em;padding:0 14px 6px;text-transform:uppercase}
.side-item{display:flex;justify-content:space-between;align-items:center;padding:6px 14px;font-size:12px;cursor:pointer;transition:background .12s}
.side-item:hover{background:var(--bg2)}
.side-item.on{background:rgba(31,212,236,.05);border-left:2px solid var(--cyan)}
.side-name{color:var(--text2)}.side-val{font-family:var(--mono);font-size:11px}
.content{padding:20px 24px}
.page{display:none}.page.on{display:block}
.hdr{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px}
.hdr-title{font-family:var(--mono);font-size:10px;color:var(--text3);letter-spacing:.14em;text-transform:uppercase}
.hdr-title::before{content:"— "}
.src-badge{font-family:var(--mono);font-size:9px;color:var(--cyan);background:rgba(31,212,236,.07);border:1px solid rgba(31,212,236,.18);padding:2px 8px;border-radius:3px}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(148px,1fr));gap:10px;margin-bottom:20px}
.card{background:var(--bg2);border:1px solid var(--border);border-radius:8px;padding:12px 14px}
.c-lbl{font-family:var(--mono);font-size:9px;color:var(--text3);letter-spacing:.1em;text-transform:uppercase;margin-bottom:8px}
.c-val{font-family:var(--mono);font-size:20px;font-weight:500;line-height:1;margin-bottom:4px}
.c-chg{font-family:var(--mono);font-size:11px;margin-bottom:3px}
.c-sub{font-size:10px;color:var(--text3)}
.c-src{font-size:9px;color:var(--text3);margin-top:5px;font-family:var(--mono);opacity:.7}
.chart-box{background:var(--bg2);border:1px solid var(--border);border-radius:8px;padding:14px;margin-bottom:20px}
.chart-top{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px}
.chart-lbl{font-size:13px;font-weight:600;color:var(--text)}
.aip{background:var(--bg2);border:1px solid var(--border);border-radius:8px;padding:14px 16px;margin-bottom:20px}
.aip-top{display:flex;align-items:center;justify-content:space-between;margin-bottom:11px}
.ai-badge{font-family:var(--mono);font-size:9px;color:var(--purple);background:rgba(155,127,245,.09);border:1px solid rgba(155,127,245,.25);padding:2px 8px;border-radius:3px}
.aip-body{font-size:13px;color:var(--text2);line-height:1.75}
.aip-body b{color:var(--text)}
.ask-wrap{display:flex;gap:8px;margin-bottom:18px}
.ask-in{flex:1;background:var(--bg2);border:1px solid var(--border2);border-radius:8px;padding:10px 14px;font-family:var(--sans);font-size:13px;color:var(--text);outline:none;transition:border-color .15s}
.ask-in:focus{border-color:var(--cyan)}
.ask-in::placeholder{color:var(--text3)}
.ask-go{background:rgba(155,127,245,.12);border:1px solid rgba(155,127,245,.35);color:var(--purple);font-weight:600;font-size:13px;padding:10px 18px;border-radius:8px;transition:all .15s;white-space:nowrap}
.ask-go:hover{background:rgba(155,127,245,.2)}
.ask-go:disabled{opacity:.4;cursor:not-allowed}
.ai-out{background:rgba(155,127,245,.05);border:1px solid rgba(155,127,245,.18);border-radius:8px;padding:14px;margin-bottom:16px;font-size:13px;color:var(--text2);line-height:1.75;display:none}
.ai-out.on{display:block}
.ai-out b{color:var(--text)}
.sq-pills{display:flex;flex-wrap:wrap;gap:7px;margin-bottom:20px}
.sq{background:var(--bg2);border:1px solid var(--border);color:var(--text2);font-size:11px;font-family:var(--mono);padding:6px 12px;border-radius:20px;transition:all .15s}
.sq:hover{border-color:var(--cyan);color:var(--cyan)}
.sec-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(185px,1fr));gap:10px;margin-bottom:20px}
.sec-card{background:var(--bg2);border:1px solid var(--border);border-radius:8px;padding:12px 14px;cursor:pointer;transition:all .15s;border-left:3px solid transparent}
.sec-card:hover{transform:translateY(-1px)}
.sec-card.bull{border-left-color:var(--green)}.sec-card.bear{border-left-color:var(--red)}.sec-card.neut{border-left-color:var(--amber)}
.sec-name{font-size:12px;font-weight:600;color:var(--text);margin-bottom:5px}
.sec-perf{font-family:var(--mono);font-size:17px;font-weight:500;line-height:1;margin-bottom:6px}
.sec-bar-bg{height:3px;background:var(--border);border-radius:2px;margin-bottom:6px;overflow:hidden}
.sec-bar-fill{height:100%;border-radius:2px}
.sec-sig{font-family:var(--mono);font-size:10px;letter-spacing:.07em}
.sec-sig.bull{color:var(--green)}.sec-sig.bear{color:var(--red)}.sec-sig.neut{color:var(--amber)}
.yield-row{display:grid;grid-template-columns:repeat(auto-fill,minmax(100px,1fr));gap:9px;margin-bottom:20px}
.yc{background:var(--bg2);border:1px solid var(--border);border-radius:6px;padding:10px 12px}
.yc-t{font-family:var(--mono);font-size:9px;color:var(--text3);margin-bottom:5px}
.yc-v{font-family:var(--mono);font-size:15px;font-weight:500}
.news-list{display:flex;flex-direction:column;gap:10px;margin-bottom:20px}
.news-item{background:var(--bg2);border:1px solid var(--border);border-radius:8px;padding:14px;display:flex;gap:12px}
.news-item:hover{border-color:var(--border2)}
.ntag{font-family:var(--mono);font-size:9px;padding:2px 7px;border-radius:3px;white-space:nowrap;height:fit-content;flex-shrink:0;margin-top:2px}
.ntag.eqt{background:rgba(61,214,140,.08);color:var(--green);border:1px solid rgba(61,214,140,.2)}
.ntag.mac{background:rgba(31,212,236,.08);color:var(--cyan);border:1px solid rgba(31,212,236,.2)}
.ntag.cmd{background:rgba(245,166,35,.08);color:var(--amber);border:1px solid rgba(245,166,35,.2)}
.ntag.rat{background:rgba(240,107,107,.08);color:var(--red);border:1px solid rgba(240,107,107,.2)}
.ntag.geo{background:rgba(155,127,245,.08);color:var(--purple);border:1px solid rgba(155,127,245,.2)}
.n-hl{font-size:13px;font-weight:600;color:var(--text);line-height:1.4;margin-bottom:4px}
.n-meta{font-family:var(--mono);font-size:10px;color:var(--text3)}
.out-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px}
.out-card{border-radius:8px;padding:14px}
.oc-bull{background:rgba(61,214,140,.05);border:1px solid rgba(61,214,140,.18)}
.oc-bear{background:rgba(240,107,107,.05);border:1px solid rgba(240,107,107,.18)}
.oc-neut{background:rgba(245,166,35,.05);border:1px solid rgba(245,166,35,.18)}
.oc-lbl{font-family:var(--mono);font-size:9px;letter-spacing:.1em;margin-bottom:9px}
.oc-bull .oc-lbl{color:var(--green)}.oc-bear .oc-lbl{color:var(--red)}.oc-neut .oc-lbl{color:var(--amber)}
.oc-list{list-style:none}
.oc-list li{font-size:12px;color:var(--text2);padding:4px 0;border-bottom:1px solid rgba(255,255,255,.04);line-height:1.4}
.oc-list li:last-child{border-bottom:none}
footer{border-top:1px solid var(--border);padding:10px 24px;font-family:var(--mono);font-size:9px;color:var(--text3);display:flex;justify-content:space-between}
.spin{display:inline-block;animation:sp 1s linear infinite}
@keyframes sp{to{transform:rotate(360deg)}}
@media(max-width:860px){
  .wrap{grid-template-columns:1fr}
  .side{position:static;height:auto;display:flex;overflow-x:auto;border-right:none;border-bottom:1px solid var(--border);padding:8px 0}
  .side-sec{display:flex;gap:3px;padding:0 8px;margin:0;flex-shrink:0}
  .side-lbl{display:none}
  .out-grid{grid-template-columns:1fr}
  .tabs{display:none}
}
</style>
</head>
<body>
<nav>
  <div class="brand">
    <div class="dot"></div>
    <div>
      <div class="brand-name">SIGNAL</div>
      <div class="brand-date">auto-updated daily &middot; ''' + TODAY_SHORT + '''</div>
    </div>
  </div>
  <div class="tabs">
    <button class="tab on" onclick="go('macro',this)">MACRO</button>
    <button class="tab" onclick="go('sectors',this)">SECTORS</button>
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
      <div class="side-item on" onclick="go('macro',null)"><span class="side-name">S&amp;P 500 (SPY)</span><span class="side-val ''' + color_class(spx_chg) + '''">' + spx_p + '''</span></div>
      <div class="side-item" onclick="go('macro',null)"><span class="side-name">Nasdaq (QQQ)</span><span class="side-val ''' + color_class(ndx_chg) + '''">' + ndx_p + '''</span></div>
      <div class="side-item" onclick="go('macro',null)"><span class="side-name">Dow (DIA)</span><span class="side-val ''' + color_class(dia_chg) + '''">' + dia_p + '''</span></div>
      <div class="side-item" onclick="go('macro',null)"><span class="side-name">Russell (IWM)</span><span class="side-val ''' + color_class(iwm_chg) + '''">' + iwm_p + '''</span></div>
    </div>
    <div class="side-sec">
      <div class="side-lbl">Rates</div>
      <div class="side-item" onclick="go('rates',null)"><span class="side-name">10Y Yield</span><span class="side-val fl">''' + y10_s + '''</span></div>
      <div class="side-item" onclick="go('rates',null)"><span class="side-name">Fed Rate</span><span class="side-val fl">''' + fed_s + '''</span></div>
      <div class="side-item" onclick="go('rates',null)"><span class="side-name">2Y Yield</span><span class="side-val fl">''' + f"{y2:.2f}%" + '''</span></div>
    </div>
    <div class="side-sec">
      <div class="side-lbl">Commodities</div>
      <div class="side-item"><span class="side-name">Gold (GLD)</span><span class="side-val ''' + color_class(gld_chg) + '''">' + gld_p + '''</span></div>
      <div class="side-item"><span class="side-name">Oil (USO)</span><span class="side-val ''' + color_class(uso_chg) + '''">' + uso_p + '''</span></div>
    </div>
    <div class="side-sec">
      <div class="side-lbl">Sentiment</div>
      <div class="side-item"><span class="side-name">VIX</span><span class="side-val ''' + color_class(vix_chg) + '''">' + vix_p + '''</span></div>
      <div class="side-item"><span class="side-name">CPI</span><span class="side-val fl">''' + f"{cpi:.1f}%" + '''</span></div>
    </div>
  </aside>
  <main class="content">

    <!-- MACRO -->
    <div class="page on" id="pg-macro">
      <div class="hdr">
        <div class="hdr-title">Macro Dashboard &mdash; ''' + TODAY + '''</div>
        <div class="src-badge">FMP API &middot; AUTO-UPDATED DAILY</div>
      </div>
      <div class="cards">''' + f'''
        <div class="card"><div class="c-lbl">S&P 500 (SPY)</div><div class="c-val {color_class(spx_chg)}">{spx_p}</div><div class="c-chg {color_class(spx_chg)}">{pct_str(spx_chg)} today</div><div class="c-src">FMP &middot; {TODAY_SHORT}</div></div>
        <div class="card"><div class="c-lbl">Nasdaq (QQQ)</div><div class="c-val {color_class(ndx_chg)}">{ndx_p}</div><div class="c-chg {color_class(ndx_chg)}">{pct_str(ndx_chg)} today</div><div class="c-src">FMP &middot; {TODAY_SHORT}</div></div>
        <div class="card"><div class="c-lbl">Dow Jones (DIA)</div><div class="c-val {color_class(dia_chg)}">{dia_p}</div><div class="c-chg {color_class(dia_chg)}">{pct_str(dia_chg)} today</div><div class="c-src">FMP &middot; {TODAY_SHORT}</div></div>
        <div class="card"><div class="c-lbl">Russell 2K (IWM)</div><div class="c-val {color_class(iwm_chg)}">{iwm_p}</div><div class="c-chg {color_class(iwm_chg)}">{pct_str(iwm_chg)} today</div><div class="c-src">FMP &middot; {TODAY_SHORT}</div></div>
        <div class="card"><div class="c-lbl">Gold (GLD)</div><div class="c-val {color_class(gld_chg)}">{gld_p}</div><div class="c-chg {color_class(gld_chg)}">{pct_str(gld_chg)} today</div><div class="c-src">FMP &middot; {TODAY_SHORT}</div></div>
        <div class="card"><div class="c-lbl">Oil (USO)</div><div class="c-val {color_class(uso_chg)}">{uso_p}</div><div class="c-chg {color_class(uso_chg)}">{pct_str(uso_chg)} today</div><div class="c-src">FMP &middot; {TODAY_SHORT}</div></div>
        <div class="card"><div class="c-lbl">VIX</div><div class="c-val {color_class(vix_chg)}">{vix_p}</div><div class="c-chg {color_class(vix_chg)}">{pct_str(vix_chg)} today</div><div class="c-src">FMP &middot; {TODAY_SHORT}</div></div>
        <div class="card"><div class="c-lbl">10Y Treasury</div><div class="c-val fl">{y10_s}</div><div class="c-chg fl">Spread vs 2Y: {spread_s}</div><div class="c-src">FMP Treasury API</div></div>
        <div class="card"><div class="c-lbl">Fed Funds Rate</div><div class="c-val fl">{fed_s}</div><div class="c-chg fl">Latest FOMC</div><div class="c-src">Federal Reserve / FMP</div></div>
        <div class="card"><div class="c-lbl">CPI Inflation</div><div class="c-val" style="color:var(--amber)">{cpi:.1f}%</div><div class="c-chg" style="color:var(--amber)">Latest release</div><div class="c-src">BLS / FMP &middot; {cpi_date}</div></div>
        <div class="card"><div class="c-lbl">Unemployment</div><div class="c-val">{unemp:.1f}%</div><div class="c-chg fl">Latest release</div><div class="c-src">BLS / FMP</div></div>
        <div class="card"><div class="c-lbl">10Y-2Y Spread</div><div class="c-val {spread_class}">{spread_s}</div><div class="c-chg {spread_class)">{"Positive" if spread>=0 else "Inverted"} curve</div><div class="c-src">FMP Treasury API</div></div>
      </div>
      <div class="aip">
        <div class="aip-top"><div class="hdr-title" style="margin:0">AI Market Analysis &mdash; {TODAY}</div><span class="ai-badge">CLAUDE POWERED</span></div>
        <div class="aip-body">S&P 500 (SPY): <b>{spx_p}</b> ({pct_str(spx_chg)}) &middot; Nasdaq: <b>{ndx_p}</b> ({pct_str(ndx_chg)}) &middot; VIX: <b>{vix_p}</b> &middot; 10Y: <b>{y10_s}</b> &middot; Fed: <b>{fed_s}</b> &middot; CPI: <b>{cpi:.1f}%</b><br><br>Click below to get AI analysis of today\'s market conditions.</div>
        <button onclick="quickAsk('Analyze todays market {TODAY}. SPY={spx_p} ({pct_str(spx_chg)}), QQQ={ndx_p} ({pct_str(ndx_chg)}), VIX={vix_p}, 10Y yield={y10_s}, Fed rate={fed_s}, CPI={cpi:.1f}%, Unemployment={unemp:.1f}%. Top sector: {top_sec[0]} ({top_sec[1]:+.2f}%), worst: {bot_sec[0]} ({bot_sec[1]:+.2f}%). What does this mean for investors?')" style="margin-top:12px;background:rgba(155,127,245,.12);border:1px solid rgba(155,127,245,.35);color:var(--purple);font-weight:600;font-size:12px;padding:8px 16px;border-radius:7px;cursor:pointer;">Generate AI Analysis for Today</button>
      </div>
      <div class="hdr"><div class="hdr-title">Sector Outlook &mdash; {TODAY}</div></div>
      <div class="out-grid">
        <div class="out-card oc-bull"><div class="oc-lbl">OVERWEIGHT</div><ul class="oc-list">
          <li>{SECTOR_LIST[0][0]}: {SECTOR_LIST[0][1]:+.2f}%</li>
          <li>{SECTOR_LIST[1][0]}: {SECTOR_LIST[1][1]:+.2f}%</li>
          <li>{SECTOR_LIST[2][0]}: {SECTOR_LIST[2][1]:+.2f}%</li>
        </ul></div>
        <div class="out-card oc-neut"><div class="oc-lbl">NEUTRAL</div><ul class="oc-list">
          <li>{SECTOR_LIST[4][0]}: {SECTOR_LIST[4][1]:+.2f}%</li>
          <li>{SECTOR_LIST[5][0]}: {SECTOR_LIST[5][1]:+.2f}%</li>
          <li>{SECTOR_LIST[6][0]}: {SECTOR_LIST[6][1]:+.2f}%</li>
        </ul></div>
        <div class="out-card oc-bear"><div class="oc-lbl">UNDERWEIGHT</div><ul class="oc-list">
          <li>{SECTOR_LIST[-1][0]}: {SECTOR_LIST[-1][1]:+.2f}%</li>
          <li>{SECTOR_LIST[-2][0]}: {SECTOR_LIST[-2][1]:+.2f}%</li>
          <li>{SECTOR_LIST[-3][0]}: {SECTOR_LIST[-3][1]:+.2f}%</li>
        </ul></div>
      </div>
    </div>

    <!-- SECTORS -->
    <div class="page" id="pg-sectors">
      <div class="hdr"><div class="hdr-title">Sector Performance &mdash; {TODAY}</div><div class="src-badge">FMP API &middot; LIVE</div></div>
      <div class="sec-grid">''' + sec_html + f'''</div>
    </div>

    <!-- RATES -->
    <div class="page" id="pg-rates">
      <div class="hdr"><div class="hdr-title">Fixed Income &mdash; {TODAY}</div><div class="src-badge">FMP TREASURY API</div></div>
      <div class="yield-row">
        <div class="yc"><div class="yc-t">3M</div><div class="yc-v fl">{y3m:.2f}%</div></div>
        <div class="yc"><div class="yc-t">1Y</div><div class="yc-v fl">{y1:.2f}%</div></div>
        <div class="yc"><div class="yc-t">2Y</div><div class="yc-v fl">{y2:.2f}%</div></div>
        <div class="yc"><div class="yc-t">5Y</div><div class="yc-v fl">{y5:.2f}%</div></div>
        <div class="yc"><div class="yc-t">10Y</div><div class="yc-v fl">{y10:.2f}%</div></div>
        <div class="yc"><div class="yc-t">30Y</div><div class="yc-v fl">{y30:.2f}%</div></div>
      </div>
      <div class="cards">
        <div class="card"><div class="c-lbl">Fed Funds Rate</div><div class="c-val fl">{fed_s}</div><div class="c-chg fl">Latest FOMC</div><div class="c-src">Federal Reserve</div></div>
        <div class="card"><div class="c-lbl">10Y-2Y Spread</div><div class="c-val {spread_class}">{spread_s}</div><div class="c-chg {spread_class)">{"Positive" if spread>=0 else "Inverted"}</div><div class="c-src">FMP Treasury</div></div>
        <div class="card"><div class="c-lbl">CPI Inflation</div><div class="c-val" style="color:var(--amber)">{cpi:.1f}%</div><div class="c-chg" style="color:var(--amber)">{cpi_date}</div><div class="c-src">BLS / FMP</div></div>
        <div class="card"><div class="c-lbl">Unemployment</div><div class="c-val">{unemp:.1f}%</div><div class="c-chg fl">Latest</div><div class="c-src">BLS / FMP</div></div>
      </div>
      <div class="aip">
        <div class="aip-top"><div class="hdr-title" style="margin:0">Rates Intelligence</div><span class="ai-badge">CLAUDE</span></div>
        <div class="aip-body">10Y: <b>{y10_s}</b> &middot; Fed: <b>{fed_s}</b> &middot; Spread: <b>{spread_s}</b> &middot; CPI: <b>{cpi:.1f}%</b></div>
        <button onclick="quickAsk('Analyze the interest rate environment {TODAY}. Fed={fed_s}, 10Y={y10_s}, 2Y={y2:.2f}%, spread={spread_s}, CPI={cpi:.1f}%. What does this mean?')" style="margin-top:12px;background:rgba(155,127,245,.12);border:1px solid rgba(155,127,245,.35);color:var(--purple);font-weight:600;font-size:12px;padding:8px 16px;border-radius:7px;cursor:pointer;">Ask AI about rates</button>
      </div>
    </div>

    <!-- NEWS -->
    <div class="page" id="pg-news">
      <div class="hdr"><div class="hdr-title">Market News &mdash; {TODAY}</div><div class="src-badge">FMP NEWS API &middot; LIVE</div></div>
      <div class="news-list">''' + news_html + '''</div>
    </div>

    <!-- AI -->
    <div class="page" id="pg-ai">
      <div class="hdr"><div class="hdr-title">AI Research &mdash; Claude</div></div>
      <div class="ask-wrap">
        <input class="ask-in" id="askIn" placeholder="Ask anything about today\'s markets..." onkeydown="if(event.key===\'Enter\')runAsk()">
        <button class="ask-go" id="askBtn" onclick="runAsk()">Ask Claude</button>
      </div>
      <div class="ai-out" id="aiOut"></div>
      <div class="sq-pills">
        <button class="sq" onclick="prefill(\'What is driving the market today?\')">What is driving markets today?</button>
        <button class="sq" onclick="prefill(\'Which sectors look strongest right now?\')">Strongest sectors?</button>
        <button class="sq" onclick="prefill(\'What does the yield curve signal?\')">Yield curve signal?</button>
        <button class="sq" onclick="prefill(\'What will the Fed do next?\')">Fed next move?</button>
        <button class="sq" onclick="prefill(\'What are the biggest market risks right now?\')">Biggest risks?</button>
      </div>
      <div id="resHist" style="display:flex;flex-direction:column;gap:12px"></div>
    </div>

  </main>
</div>
<footer>
  <div>SIGNAL &middot; Auto-updated daily via GitHub Actions &middot; Data: Financial Modeling Prep API &middot; ''' + TODAY + ''' &middot; Not investment advice</div>
  <div id="ftTime"></div>
</footer>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script>
function tick(){var n=new Date();var t=n.toLocaleTimeString("en-US",{timeZone:"America/New_York",hour:"2-digit",minute:"2-digit",second:"2-digit",hour12:false});document.getElementById("clk").textContent=t+" EST";document.getElementById("ftTime").textContent="Built: ''' + TODAY + ''' "+t;}
tick();setInterval(tick,1000);
function go(id,btn){document.querySelectorAll(".page").forEach(function(p){p.classList.remove("on");});document.getElementById("pg-"+id).classList.add("on");if(btn){document.querySelectorAll(".tab").forEach(function(t){t.classList.remove("on");});btn.classList.add("on");}}
var TICKS=[''' + f'''
  {{s:"S&P(SPY)",v:"{spx_p}",u:{str(safe_float(spx_chg)>=0).lower()},c:"{pct_str(spx_chg)}"}},
  {{s:"NASDAQ(QQQ)",v:"{ndx_p}",u:{str(safe_float(ndx_chg)>=0).lower()},c:"{pct_str(ndx_chg)}"}},
  {{s:"DOW(DIA)",v:"{dia_p}",u:{str(safe_float(dia_chg)>=0).lower()},c:"{pct_str(dia_chg)}"}},
  {{s:"RUSSELL(IWM)",v:"{iwm_p}",u:{str(safe_float(iwm_chg)>=0).lower()},c:"{pct_str(iwm_chg)}"}},
  {{s:"VIX",v:"{vix_p}",u:false,c:"{pct_str(vix_chg)}"}},
  {{s:"10Y YIELD",v:"{y10_s}",u:true,c:"Treasury"}},
  {{s:"GOLD(GLD)",v:"{gld_p}",u:{str(safe_float(gld_chg)>=0).lower()},c:"{pct_str(gld_chg)}"}},
  {{s:"OIL(USO)",v:"{uso_p}",u:{str(safe_float(uso_chg)>=0).lower()},c:"{pct_str(uso_chg)}"}},
  {{s:"FED RATE",v:"{fed_s}",u:true,c:"FOMC"}},
  {{s:"CPI",v:"{cpi:.1f}%",u:true,c:"Inflation"}},
''' + '''];
(function(){var el=document.getElementById("tkr");var html="";var all=TICKS.concat(TICKS);for(var i=0;i<all.length;i++){var d=all[i];html+="<span class=\\"tick\\"><span class=\\"ts\\">"+d.s+"</span><span class=\\"tv\\">"+d.v+"</span><span class=\\""+(d.u?"up":"dn")+"\\">"+d.c+"</span></span>";}el.innerHTML=html;})();
function askSec(n){go("ai",null);prefill("Analyze the "+n+" sector today. What is driving its performance and what is the outlook?");}
var SYS="You are SIGNAL, a market intelligence platform. Today is ''' + TODAY + f'''. Live data from FMP API: SPY={spx_p} ({pct_str(spx_chg)}), QQQ={ndx_p} ({pct_str(ndx_chg)}), DIA={dia_p} ({pct_str(dia_chg)}), IWM={iwm_p} ({pct_str(iwm_chg)}), VIX={vix_p}, 10Y yield={y10_s}, 2Y yield={y2:.2f}%, Fed rate={fed_s}, spread={spread_s}, GLD={gld_p} ({pct_str(gld_chg)}), USO={uso_p} ({pct_str(uso_chg)}), CPI={cpi:.1f}%, Unemployment={unemp:.1f}%. Top sector: {top_sec[0]} ({top_sec[1]:+.2f}%), worst: {bot_sec[0]} ({bot_sec[1]:+.2f}%). Provide sharp data-driven analysis. Not personalized investment advice.";
''' + '''var chat=[];
async function runAsk(){var inp=document.getElementById("askIn");var q=inp.value.trim();if(!q)return;inp.value="";var btn=document.getElementById("askBtn");btn.disabled=true;btn.textContent="Thinking...";var out=document.getElementById("aiOut");out.classList.add("on");out.innerHTML="<span class=\\"spin\\">&#8635;</span> Analyzing live market data...";try{var msgs=chat.concat([{role:"user",content:q}]);var res=await fetch("https://api.anthropic.com/v1/messages",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({model:"claude-sonnet-4-20250514",max_tokens:1000,system:SYS,messages:msgs})});var data=await res.json();var text=(data.content&&data.content[0])?data.content[0].text:"Analysis unavailable.";chat.push({role:"user",content:q},{role:"assistant",content:text});if(chat.length>12)chat=chat.slice(-12);out.innerHTML="<div style=\\"font-family:var(--mono);font-size:10px;color:var(--purple);margin-bottom:10px\\">SIGNAL AI &middot; ''' + TODAY + '''</div>"+fmt(text);addHist(q,text);}catch(e){out.innerHTML="<span style=\\"color:var(--red)\\">Connection error.</span>";}btn.disabled=false;btn.textContent="Ask Claude";}
function prefill(q){go("ai",null);document.getElementById("askIn").value=q;document.getElementById("askIn").focus();}
function quickAsk(q){go("ai",null);document.getElementById("askIn").value=q;runAsk();}
function fmt(t){return t.replace(/\*\*(.*?)\*\*/g,"<b>$1</b>").replace(/^### (.+)$/gm,"<div style=\\"font-size:13px;font-weight:600;color:var(--text);margin:12px 0 4px\\">$1</div>").replace(/^## (.+)$/gm,"<div style=\\"font-size:14px;font-weight:700;color:var(--cyan);margin:14px 0 6px\\">$1</div>").replace(/^- (.+)$/gm,"<div style=\\"padding:2px 0 2px 12px;border-left:2px solid var(--border2);margin:3px 0;color:var(--text2)\\">$1</div>").replace(/\n\n/g,"<br><br>").replace(/\n/g,"<br>");}
var rLog=[];
function addHist(q,a){rLog.unshift({q:q,a:a,t:new Date().toLocaleTimeString("en-US",{hour:"2-digit",minute:"2-digit"})});var h=document.getElementById("resHist");var html="";for(var i=0;i<Math.min(rLog.length,3);i++){var r=rLog[i];html+="<div class=\\"aip\\"><div style=\\"font-family:var(--mono);font-size:10px;color:var(--text3);margin-bottom:7px\\">"+r.t+"</div><div style=\\"font-size:13px;font-weight:600;color:var(--cyan);margin-bottom:8px\\">"+r.q+"</div><div style=\\"font-size:12px;color:var(--text2);line-height:1.7\\">"+fmt(r.a)+"</div></div>";}h.innerHTML=html;}
</script>
</body>
</html>'''

# Fix the f-string issue with spread_class
html = html.replace('{spread_class)}', '{spread_class}')

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"\nindex.html built successfully for {TODAY}!")
print(f"File size: {len(html)} bytes")
