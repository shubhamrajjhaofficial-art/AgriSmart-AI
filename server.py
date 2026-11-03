import os
import json
import threading
from datetime import datetime, timezone

import requests
from flask import Flask, request, jsonify, render_template_string
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
DEVICE_TOKEN = os.getenv("DEVICE_TOKEN", "change-this-device-token")

_latest = {
    "temperature_c": None,
    "humidity_pct": None,
    "soil_raw": None,
    "soil_pct": None,
    "nitrogen_mgkg": None,
    "phosphorus_mgkg": None,
    "potassium_mgkg": None,
    "npk_status": "Waiting for NPK sensor data",
    "relay_on": False,
    "updated_at": None,
}
_lock = threading.Lock()

PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#f5f8f1">
<title>AgriSmart AI | Smart Farming Dashboard</title>
<style>
:root{color-scheme:dark;font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;--bg:#06120f;--panel:#0b1d1a;--panel2:#0d2420;--line:#1b4136;--text:#f2fff7;--muted:#9bb5a8;--green:#45e65e;--green2:#16883a;--cyan:#20d7e8;--blue:#168cff;--orange:#ffb326;--purple:#b66cff}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at 70% -10%,#123e35 0,transparent 36%),linear-gradient(135deg,#06120f,#071b1b 60%,#07130f);color:var(--text);font-size:14px}.layout{display:grid;grid-template-columns:226px minmax(0,1fr);min-height:100vh}.sidebar{border-right:1px solid #1a4b3b;background:rgba(3,15,13,.94);padding:24px 14px;display:flex;flex-direction:column;gap:26px}.brand{display:flex;align-items:center;gap:11px;padding:0 9px}.brand-mark{width:46px;height:46px;border-radius:15px;background:linear-gradient(135deg,#50f15e,#16883b);display:grid;place-items:center;font-size:26px;color:#03210e;box-shadow:0 0 25px #32d94a35}.brand h1{font-size:19px;margin:0;letter-spacing:-.6px}.brand h1 span{color:var(--green)}.brand p{margin:4px 0 0;color:#91b2a0;font-size:10px}.nav{display:grid;gap:8px}.nav a{padding:13px 14px;border-radius:13px;color:#b9d0c4;text-decoration:none;display:flex;align-items:center;gap:12px;font-size:13px}.nav a.active,.nav a:hover{color:#fff;background:linear-gradient(90deg,#167f36,#105b2d);box-shadow:inset 3px 0 #55f35c}.nav .ico{font-size:19px;width:23px;text-align:center}.sidebar-art{margin-top:auto;border-radius:18px;min-height:160px;padding:16px;background:radial-gradient(ellipse at 50% 100%,#1c8c3e66,transparent 60%),linear-gradient(145deg,#0c3127,#071b19);border:1px solid #1b4636;display:flex;flex-direction:column;justify-content:end}.sidebar-art .sprout{font-size:62px;line-height:1.1}.sidebar-art strong{font-size:14px}.sidebar-art small{color:#9ab5a6;margin-top:5px;line-height:1.5}.main{min-width:0;padding:24px 25px 18px}.topbar{display:flex;align-items:center;justify-content:space-between;gap:15px;margin-bottom:20px}.title h2{font-size:clamp(24px,3vw,34px);letter-spacing:-1px;margin:0}.title h2 span{color:var(--green)}.title p{color:#a6c3b5;margin:5px 0 0}.top-actions{display:flex;align-items:center;gap:10px;flex-wrap:wrap}.live-pill,.time-pill{display:flex;align-items:center;gap:8px;border:1px solid #25513f;background:#0a211b;border-radius:999px;padding:10px 13px;color:#d5f5df;font-size:12px}.dot{width:9px;height:9px;border-radius:50%;background:var(--green);box-shadow:0 0 12px #45e65e}.btn{border:0;border-radius:12px;padding:11px 15px;font:inherit;font-weight:750;cursor:pointer;transition:.2s}.btn:hover{transform:translateY(-1px);filter:brightness(1.08)}.btn-primary{background:linear-gradient(110deg,#59ef50,#22bc43);color:#03200c;box-shadow:0 5px 20px #28d94b30}.btn-secondary{background:#102b24;color:#dff9e7;border:1px solid #285641}.hero{position:relative;overflow:hidden;display:flex;align-items:center;justify-content:space-between;gap:20px;min-height:145px;border:1px solid #245641;border-radius:22px;padding:25px 28px;margin-bottom:20px;background:linear-gradient(100deg,#0d3b2b 0%,#0c3027 47%,#0a211e 100%)}.hero:after{content:'🌾';position:absolute;right:4%;bottom:-36px;font-size:150px;opacity:.16;transform:rotate(-12deg)}.eyebrow{color:#74ef8a;text-transform:uppercase;letter-spacing:1.8px;font-size:10px;font-weight:800}.hero h3{font-size:clamp(23px,2.8vw,34px);letter-spacing:-1px;margin:8px 0}.hero p{color:#c0dfcf;line-height:1.6;margin:0;max-width:570px}.hero-chip{z-index:1;min-width:170px;border:1px solid #286748;border-radius:16px;background:#071c18b8;padding:16px}.hero-chip small{color:#9eb9ab}.hero-chip strong{display:block;font-size:29px;margin-top:6px}.section-head{display:flex;align-items:end;justify-content:space-between;gap:10px;margin:22px 0 12px}.section-head h3{font-size:16px;margin:0;letter-spacing:-.3px}.section-head p{margin:4px 0 0;font-size:12px;color:var(--muted)}.small-note{font-size:11px;color:#84a898}.metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:13px}.metric{position:relative;overflow:hidden;background:linear-gradient(145deg,#0d2420,#081916);border:1px solid #1e4c3c;border-radius:18px;padding:17px;min-width:0;box-shadow:0 8px 25px #0002}.metric:after{content:'';position:absolute;left:0;right:0;bottom:0;height:3px;background:var(--accent,var(--green));opacity:.75}.metric-top{display:flex;justify-content:space-between;align-items:center;gap:8px}.metric-label{font-size:12px;color:#b1cabe;font-weight:650}.metric-icon{width:38px;height:38px;border-radius:13px;background:#153d2b;display:grid;place-items:center;font-size:20px}.metric-value{font-size:clamp(23px,2.4vw,31px);font-weight:800;letter-spacing:-1px;margin-top:13px;white-space:nowrap}.unit{font-size:13px;font-weight:650;letter-spacing:0;color:#91b1a1;margin-left:3px}.metric-foot{font-size:11px;color:#91b1a1;margin-top:7px}.metric:nth-child(1){--accent:var(--cyan)}.metric:nth-child(1) .metric-icon{background:#073e4a}.metric:nth-child(2){--accent:var(--blue)}.metric:nth-child(2) .metric-icon{background:#102e4e}.metric:nth-child(3){--accent:var(--orange)}.metric:nth-child(3) .metric-icon{background:#493317}.metric:nth-child(4){--accent:var(--purple)}.metric:nth-child(4) .metric-icon{background:#352044}.npk-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-top:13px}.npk-card{display:flex;align-items:center;gap:12px;padding:13px 15px;border-radius:15px;border:1px solid #234b3b;background:#0b201b}.npk-bubble{width:38px;height:38px;border-radius:12px;display:grid;place-items:center;font-weight:900;font-size:16px;flex-shrink:0}.n-bubble{background:#153453;color:#65b6ff}.p-bubble{background:#352044;color:#d7a2ff}.k-bubble{background:#4a3515;color:#ffcc64}.npk-name{font-size:11px;color:#9bb5a8}.npk-value{font-size:20px;font-weight:800;margin-top:3px}.npk-unit{font-size:10px;color:#789888}.content-grid{display:grid;grid-template-columns:1.18fr .82fr;gap:16px;margin-top:18px}.panel{background:linear-gradient(145deg,#0c211d,#081714);border:1px solid #1c4839;border-radius:20px;padding:20px;min-width:0}.panel-head{display:flex;align-items:center;justify-content:space-between;gap:10px}.panel h3{margin:0;font-size:16px}.panel-sub{font-size:12px;color:var(--muted);margin-top:5px}.chart-area{height:215px;margin-top:20px;border-radius:13px;position:relative;overflow:hidden;background:repeating-linear-gradient(to bottom,transparent 0,transparent 42px,#1b3a31 43px),repeating-linear-gradient(to right,transparent 0,transparent 95px,#18362e 96px);display:flex;align-items:center;justify-content:center}.chart-empty{text-align:center;color:#7f9d8e;padding:20px;font-size:12px;line-height:1.7}.chart-legend{display:flex;gap:13px;flex-wrap:wrap;margin-top:13px;color:#b6cec0;font-size:11px}.legend-dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:5px}.recommendation{margin-top:15px;border:1px solid #2d8748;border-radius:16px;background:linear-gradient(120deg,#103a25,#0b281d);padding:17px;color:#e5ffeb;line-height:1.65;white-space:pre-wrap;min-height:80px}.crop-row{display:flex;align-items:end;gap:10px;margin-top:17px;flex-wrap:wrap}.field{flex:1;min-width:160px}.field label{display:block;font-size:10px;font-weight:800;letter-spacing:.8px;color:#91b7a2;margin-bottom:7px}select{width:100%;border:1px solid #285342;border-radius:11px;padding:12px 13px;background:#081b17;color:#e8fff0;font:inherit;outline:none}select:focus{border-color:#4ce96a}.statusline{font-size:11px;color:#9ab6a7;margin-top:12px}.bottom-grid{display:grid;grid-template-columns:.85fr 1fr 1.2fr;gap:15px;margin-top:16px}.ring-wrap{display:flex;align-items:center;gap:17px;margin-top:17px}.ring{width:92px;height:92px;border-radius:50%;background:conic-gradient(var(--green) 0 68%,#19382c 68%);display:grid;place-items:center;flex-shrink:0}.ring:before{content:'—';width:70px;height:70px;border-radius:50%;background:#0a1c17;display:grid;place-items:center;font-size:22px;font-weight:800}.ring-copy strong{display:block;color:var(--green);font-size:14px}.ring-copy small{display:block;color:#9bb5a8;margin-top:6px;line-height:1.5}.pump-state{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-top:20px}.pump-state strong{font-size:20px}.state-pill{background:#152d25;border:1px solid #315242;border-radius:999px;padding:7px 15px;font-weight:800;font-size:12px}.pump-note{color:#9ab6a7;font-size:12px;margin-top:6px}.pump-btn{width:100%;margin-top:18px}.system-list{display:grid;gap:14px;margin-top:17px}.system-item{display:flex;align-items:center;justify-content:space-between;gap:10px}.sys-left{display:flex;align-items:center;gap:10px;min-width:0}.sys-icon{width:34px;height:34px;border-radius:11px;background:#14372a;display:grid;place-items:center;font-size:16px;flex-shrink:0}.sys-name{font-size:12px;font-weight:700}.sys-desc{font-size:10px;color:#8eab9c;margin-top:3px}.state{font-size:9px;font-weight:850;letter-spacing:.6px;color:#c5b87e;background:#392f16;border:1px solid #5b4b23;padding:6px 8px;border-radius:999px;white-space:nowrap}.state.ok{color:#7af58a;background:#103b20;border-color:#246b36}.warning{margin-top:18px;border:1px solid #66511f;background:#211d10;color:#e7d9a7;padding:13px 15px;border-radius:13px;font-size:11px;line-height:1.6}.footer{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;color:#769788;font-size:11px;border-top:1px solid #19392f;margin-top:18px;padding-top:14px}.mobile-menu{display:none}
@media(max-width:1050px){.layout{grid-template-columns:190px minmax(0,1fr)}.main{padding:20px 17px}.metrics{grid-template-columns:repeat(2,minmax(0,1fr))}.content-grid{grid-template-columns:1fr}.bottom-grid{grid-template-columns:1fr 1fr}.bottom-grid .panel:last-child{grid-column:1/-1}}
@media(max-width:650px){.layout{display:block}.sidebar{display:none}.main{padding:16px 12px}.topbar{align-items:flex-start;flex-direction:column}.top-actions{width:100%}.hero{padding:20px;min-height:unset}.hero-chip{display:none}.metrics{gap:9px}.metric{padding:13px}.metric-value{font-size:24px}.content-grid,.bottom-grid,.npk-grid{grid-template-columns:1fr}.bottom-grid .panel:last-child{grid-column:auto}.panel{padding:16px}.chart-area{height:170px}.footer{flex-direction:column}.section-head{align-items:flex-start;flex-direction:column}}
</style>
</head>
<body><div class="layout">
<aside class="sidebar"><div class="brand"><div class="brand-mark">🌱</div><div><h1>AgriSmart <span>AI</span></h1><p>SMART FARMING, SMART FUTURE</p></div></div>
<nav class="nav"><a class="active" href="#dashboard"><span class="ico">⌂</span>Dashboard</a><a href="#sensors"><span class="ico">▥</span>Sensor Data</a><a href="#advisor"><span class="ico">✺</span>AI Recommendation</a><a href="#pump"><span class="ico">💧</span>Pump Control</a><a href="#system"><span class="ico">⚙</span>System Status</a></nav>
<div class="sidebar-art"><div class="sprout">🌱</div><strong>Grow smarter with AgriSmart AI</strong><small>Technology for healthier crops and better decisions.</small></div></aside>
<main class="main" id="dashboard"><header class="topbar"><div class="title"><h2>AgriSmart <span>AI</span></h2><p>Smart Agriculture Dashboard</p></div><div class="top-actions"><div class="live-pill"><span class="dot"></span><span id="connection">Connecting to device</span></div><div class="time-pill">▦ <span id="clock">Live monitoring</span></div><button class="btn btn-secondary" onclick="refreshData()">↻ Refresh</button></div></header>
<section class="hero"><div><div class="eyebrow">Precision farming · made simple</div><h3>Grow smarter. Farm better.</h3><p>Monitor your soil, understand crop conditions, and get AI-powered farming guidance in one place.</p></div><div class="hero-chip"><small>Current temperature</small><strong id="heroTemp">—<span class="unit">°C</span></strong><small id="heroHumidity">—% humidity</small></div></section>
<div class="section-head" id="sensors"><div><h3>Live sensor overview</h3><p>Readings from your connected ESP8266 device</p></div><span class="small-note">Auto refresh · every 4 seconds</span></div>
<section class="metrics"><div class="metric"><div class="metric-top"><span class="metric-label">Temperature</span><span class="metric-icon">🌡️</span></div><div class="metric-value" id="temp">—<span class="unit">°C</span></div><div class="metric-foot">Air temperature</div></div><div class="metric"><div class="metric-top"><span class="metric-label">Air humidity</span><span class="metric-icon">💧</span></div><div class="metric-value" id="hum">—<span class="unit">%</span></div><div class="metric-foot">Relative humidity</div></div><div class="metric"><div class="metric-top"><span class="metric-label">Soil moisture</span><span class="metric-icon">🌿</span></div><div class="metric-value" id="soil">—</div><div class="metric-foot" id="soilFoot">Waiting for soil sensor</div></div><div class="metric"><div class="metric-top"><span class="metric-label">Water pump</span><span class="metric-icon">🚿</span></div><div class="metric-value" id="relay">—</div><div class="metric-foot">Relay output status</div></div></section>
<div class="section-head"><div><h3>Soil nutrient profile</h3><p>NPK values appear when a compatible sensor is connected</p></div></div>
<section class="npk-grid"><div class="npk-card"><div class="npk-bubble n-bubble">N</div><div><div class="npk-name">Nitrogen</div><div class="npk-value" id="n">—</div><div class="npk-unit">sensor-reported mg/kg</div></div></div><div class="npk-card"><div class="npk-bubble p-bubble">P</div><div><div class="npk-name">Phosphorus</div><div class="npk-value" id="p">—</div><div class="npk-unit">sensor-reported mg/kg</div></div></div><div class="npk-card"><div class="npk-bubble k-bubble">K</div><div><div class="npk-name">Potassium</div><div class="npk-value" id="k">—</div><div class="npk-unit">sensor-reported mg/kg</div></div></div></section>
<section class="content-grid"><div class="panel"><div class="panel-head"><h3>▥ Sensor monitoring</h3><span class="small-note">Live readings</span></div><div class="panel-sub">Temperature, humidity and soil moisture trends</div><div class="chart-area"><div class="chart-empty">📈<br><strong>Waiting for sensor history</strong><br>Trend chart will be available after historical readings are collected.</div></div><div class="chart-legend"><span><i class="legend-dot" style="background:#ffb326"></i>Temperature</span><span><i class="legend-dot" style="background:#168cff"></i>Humidity</span><span><i class="legend-dot" style="background:#45e65e"></i>Soil moisture</span></div></div>
<div class="panel" id="advisor"><div class="panel-head"><h3>✺ AI crop advisor</h3><span class="state ok">AI READY*</span></div><div class="panel-sub">Choose your crop for guidance based on latest sensor readings.</div><div class="crop-row"><div class="field"><label for="crop">SELECT YOUR CROP</label><select id="crop"><option value="Rice">Rice / धान</option><option value="Wheat">Wheat / गेहूँ</option><option value="Maize">Maize / मक्का</option><option value="Tomato">Tomato / टमाटर</option><option value="Potato">Potato / आलू</option><option value="Mustard">Mustard / सरसों</option><option value="Sugarcane">Sugarcane / गन्ना</option><option value="Cotton">Cotton / कपास</option><option value="Chickpea">Chickpea / चना</option><option value="Other">Other / अन्य</option></select></div><button id="ask" class="btn btn-primary" onclick="recommend()">Get AI advice ↗</button></div><div class="recommendation" id="recommendation">🌱 Choose a crop and request AI advice to see recommendations here.</div><div class="statusline" id="status">Connecting to backend…</div></div></section>
<section class="bottom-grid"><div class="panel"><h3>🌿 Soil health</h3><div class="panel-sub">Calibrated moisture indicator</div><div class="ring-wrap"><div class="ring" id="soilRing"></div><div class="ring-copy"><strong id="soilHealthLabel">Awaiting data</strong><small id="soilHealthDesc">Soil moisture status will appear when readings arrive.</small></div></div></div>
<div class="panel" id="pump"><h3>⚡ Quick controls</h3><div class="panel-sub">Pump relay status from the device</div><div class="pump-state"><div><strong>💧 Water pump</strong><div class="pump-note">Control is not enabled from this page.</div></div><span class="state-pill" id="pumpBadge">STATUS —</span></div><button class="btn btn-secondary pump-btn" disabled title="Pump control is intentionally disabled for safety">Pump control disabled for safety</button></div>
<div class="panel" id="system"><h3>✓ System status</h3><div class="panel-sub">Connection and sensor availability</div><div class="system-list"><div class="system-item"><div class="sys-left"><div class="sys-icon">📡</div><div><div class="sys-name">ESP8266 connection</div><div class="sys-desc">Sensor data upload</div></div></div><span class="state" id="deviceState">WAITING</span></div><div class="system-item"><div class="sys-left"><div class="sys-icon">🌱</div><div><div class="sys-name">Soil moisture sensor</div><div class="sys-desc">Raw or calibrated value</div></div></div><span class="state" id="soilState">WAITING</span></div><div class="system-item"><div class="sys-left"><div class="sys-icon">🧪</div><div><div class="sys-name">NPK sensor</div><div class="sys-desc" id="npkDesc">Waiting for NPK data</div></div></div><span class="state" id="npkState">WAITING</span></div><div class="system-item"><div class="sys-left"><div class="sys-icon">🕒</div><div><div class="sys-name">Last data update</div><div class="sys-desc" id="heroUpdated">Waiting for sensor…</div></div></div><span class="state" id="updated">—</span></div></div></div></section>
<div class="warning">⚠️ <strong>Responsible farming:</strong> AI guidance is informational, not a replacement for a laboratory soil test or local agricultural expert. Verify sensor calibration before making crop or fertilizer decisions. Pump control is disabled in this demo for safety.</div><footer class="footer"><span>© AgriSmart AI · Smart Farming, Better Future</span><span>Built for learning and responsible farming 🌾</span></footer></main></div>
<script>
const fmt=(v,suffix='') => (v===null || v===undefined || v==='') ? '—' : `${v}${suffix}`;
const el=id=>document.getElementById(id);
function setState(id,ok,text){el(id).textContent=text;el(id).className='state'+(ok?' ok':'')}
function tickClock(){const d=new Date();el('clock').textContent=d.toLocaleDateString(undefined,{day:'2-digit',month:'short',year:'numeric'})+' · '+d.toLocaleTimeString(undefined,{hour:'2-digit',minute:'2-digit',second:'2-digit'})}tickClock();setInterval(tickClock,1000);
async function refreshData(){try{const r=await fetch('/api/sensors');const d=await r.json();
 el('temp').innerHTML=fmt(d.temperature_c)+'<span class="unit">°C</span>';el('hum').innerHTML=fmt(d.humidity_pct)+'<span class="unit">%</span>';el('soil').textContent=d.soil_pct==null?fmt(d.soil_raw,' raw'):fmt(d.soil_pct,'%');el('soilFoot').textContent=d.soil_pct==null?'Raw sensor value · calibrate for %':'Calibrated soil moisture';el('n').textContent=fmt(d.nitrogen_mgkg);el('p').textContent=fmt(d.phosphorus_mgkg);el('k').textContent=fmt(d.potassium_mgkg);el('relay').textContent=d.relay_on?'ON':'OFF';el('heroTemp').innerHTML=fmt(d.temperature_c)+'<span class="unit">°C</span>';el('heroHumidity').textContent=fmt(d.humidity_pct,'% humidity');el('heroUpdated').textContent=d.updated_at||'Waiting for sensor…';el('updated').textContent=d.updated_at||'—';el('pumpBadge').textContent=d.relay_on?'PUMP ON':'PUMP OFF';
 const online=!!d.updated_at;el('connection').textContent=online?'Device data received':'Waiting for device';el('status').innerHTML=online?'<strong>✓ Sensor data received.</strong> Dashboard updates automatically.':'Waiting for ESP8266 to send data. Demo values are not fabricated.';setState('deviceState',online,online?'CONNECTED':'WAITING');const soilOk=d.soil_pct!=null||d.soil_raw!=null;setState('soilState',soilOk,soilOk?'DATA RECEIVED':'WAITING');const npkOk=d.nitrogen_mgkg!=null&&d.phosphorus_mgkg!=null&&d.potassium_mgkg!=null;setState('npkState',npkOk,npkOk?'DATA RECEIVED':'WAITING');el('npkDesc').textContent=d.npk_status||'Waiting for NPK data';if(d.soil_pct!=null){const v=Math.max(0,Math.min(100,Number(d.soil_pct)));el('soilRing').style.background=`conic-gradient(var(--green) 0 ${v}%,#19382c ${v}% 100%)`;el('soilRing').style.setProperty('--unused',v);el('soilHealthLabel').textContent=v<30?'Low moisture':v>80?'High moisture':'Moisture: '+v+'%';el('soilHealthDesc').textContent='Based on calibrated soil moisture reading.'}else{el('soilHealthLabel').textContent='Awaiting data';el('soilHealthDesc').textContent='Calibrated moisture reading not available.'}
 }catch(e){el('status').textContent='Backend not reachable: '+e.message;el('connection').textContent='Backend unavailable'}}
async function recommend(){const b=el('ask');b.disabled=true;b.textContent='Analyzing…';el('recommendation').textContent='AI is reviewing your crop selection and latest sensor readings…';try{const r=await fetch('/api/recommend',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({crop:el('crop').value})});const d=await r.json();if(!r.ok)throw new Error(d.error||'Request failed');el('recommendation').textContent=d.recommendation}catch(e){el('recommendation').textContent='Unable to get AI advice: '+e.message}finally{b.disabled=false;b.textContent='Get AI advice ↗'}}
refreshData();setInterval(refreshData,4000);
</script></body></html>"""

def clean_number(value):
    if value is None or value == "":
        return None
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return None

@app.get("/")
def index():
    return render_template_string(PAGE)

@app.get("/api/sensors")
def sensor_data():
    with _lock:
        return jsonify(dict(_latest))

@app.post("/api/sensors")
def receive_sensor_data():
    token = request.headers.get("X-Device-Token", "")
    if token != DEVICE_TOKEN:
        return jsonify({"error": "Unauthorized device token"}), 401
    body = request.get_json(silent=True) or {}
    with _lock:
        for key in ("temperature_c", "humidity_pct", "soil_raw", "soil_pct",
                    "nitrogen_mgkg", "phosphorus_mgkg", "potassium_mgkg"):
            if key in body:
                _latest[key] = clean_number(body[key])
        if "npk_status" in body:
            _latest["npk_status"] = str(body["npk_status"])[:160]
        if "relay_on" in body:
            _latest["relay_on"] = bool(body["relay_on"])
        _latest["updated_at"] = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
    return jsonify({"ok": True})

@app.post("/api/recommend")
def recommendation():
    body = request.get_json(silent=True) or {}
    crop = str(body.get("crop", "Rice"))[:60]
    with _lock:
        readings = dict(_latest)

    if not GEMINI_API_KEY:
        return jsonify({"error": "Gemini API key missing. Set GEMINI_API_KEY in the .env file and restart the server."}), 503

    prompt = f"""
You are an agricultural advisory assistant. Reply in clear Hindi (Devanagari), with short headings:
1) Sensor reading summary
2) Possible nutrient concern (N, P, K)
3) Water/soil recommendation
4) Safe next steps.
Selected crop: {crop}
Latest sensor readings (values may be null or unverified):
{json.dumps(readings, ensure_ascii=False)}
Rules:
- Do not invent missing readings. If N/P/K is missing, clearly say no valid NPK reading is available yet.
- Sensor values alone cannot prove a deficiency; phrase nutrient findings as possible concerns, not a diagnosis.
- Do not prescribe exact fertilizer quantities without soil test, crop stage, area, and local recommendation.
- Ask the user to verify NPK sensor units/calibration and follow local agricultural extension guidance.
- If soil moisture is missing or uncalibrated, say so.
- This is advisory only. Never tell the system to switch a relay or pump on/off.
"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    try:
        response = requests.post(
            url,
            headers={"x-goog-api-key": GEMINI_API_KEY, "Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}],
                  "generationConfig": {"temperature": 0.3, "maxOutputTokens": 900}},
            timeout=35,
        )
        if response.status_code >= 400:
            return jsonify({"error": f"Gemini API error ({response.status_code}): {response.text[:500]}"}), 502
        data = response.json()
        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        text = "\n".join(p.get("text", "") for p in parts).strip()
        if not text:
            return jsonify({"error": "AI returned an empty response. Check API key/model/quota."}), 502
        return jsonify({"crop": crop, "recommendation": text})
    except requests.RequestException as exc:
        return jsonify({"error": f"Could not reach Gemini API: {exc}"}), 502

if __name__ == "__main__":
    # Host on LAN so a phone/computer on the same Wi-Fi can open the dashboard.
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
