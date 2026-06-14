#!/usr/bin/env python3
"""
Stock Market Pro v2 — Enhanced Web Dashboard
Dark-themed, responsive, with charts, search, and performance tracking.
"""

import os
import sys
import json
import subprocess
from datetime import datetime, timedelta
from flask import Flask, render_template_string, jsonify, request, send_file
from io import BytesIO
import base64

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(BASE_DIR, 'scripts', 'stock_recommendation_history.json')
WATCHLIST_FILE = os.path.join(BASE_DIR, 'scripts', 'stock_watchlist.json')

app = Flask(__name__)

# ──────────────────────────────────────────────
# Data helpers
# ──────────────────────────────────────────────

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return {"history": [], "total_recommendations": 0, "last_updated": None}
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"history": [], "total_recommendations": 0, "last_updated": None}

def load_watchlist():
    if not os.path.exists(WATCHLIST_FILE):
        return []
    try:
        with open(WATCHLIST_FILE, 'r', encoding='utf-8') as f:
            return json.load(f).get("watchlist", [])
    except:
        return []

def compute_performance(history):
    """For each ticker, track price evolution over time."""
    import pandas as pd
    
    records = history.get("history", [])
    if not records:
        return {}
    
    # Group by ticker, sort by date
    tickers = {}
    for rec in records:
        t = rec.get("ticker", "")
        if t not in tickers:
            tickers[t] = []
        tickers[t].append(rec)
    
    perf = {}
    for ticker, recs in tickers.items():
        recs.sort(key=lambda x: x.get("timestamp", ""))
        first = recs[0]
        last = recs[-1]
        
        first_price = first.get("current_price") if "current_price" in first else first.get("price")
        last_price = last.get("current_price") if "current_price" in last else last.get("price")
        
        if first_price and last_price and first_price > 0:
            change_pct = (last_price - first_price) / first_price * 100
        else:
            change_pct = 0
        
        # Get price history for sparkline
        price_history = []
        for r in recs:
            p = r.get("current_price") if "current_price" in r else r.get("price")
            if p:
                price_history.append({
                    "date": r.get("date", ""),
                    "price": p
                })
        
        perf[ticker] = {
            "name": last.get("name", ticker),
            "sector": last.get("sector", ""),
            "first_price": first_price,
            "last_price": last_price,
            "change_pct": round(change_pct, 2),
            "first_date": first.get("date", ""),
            "last_date": last.get("date", ""),
            "count": len(recs),
            "price_history": price_history,
            "market_cap": last.get("market_cap", 0),
            "pe_ratio": last.get("pe_ratio", 0),
            "notes": last.get("notes", "")
        }
    
    return perf

def format_cap(cap):
    if not cap:
        return "-"
    b = cap / 1e9
    if b >= 1000:
        return f"${b/1000:.2f}T"
    return f"${b:.2f}B"


# ──────────────────────────────────────────────
# HTML Template (modern dark theme, single page)
# ──────────────────────────────────────────────

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>📊 Stock Market Pro</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
  <style>
    :root {
      --bg-primary: #0d1117;
      --bg-secondary: #161b22;
      --bg-card: #1c2333;
      --bg-hover: #252d3f;
      --border: #30363d;
      --text-primary: #f0f6fc;
      --text-secondary: #8b949e;
      --text-muted: #6e7681;
      --accent-blue: #58a6ff;
      --accent-green: #3fb950;
      --accent-red: #f85149;
      --accent-purple: #bc8cff;
      --accent-orange: #d29922;
      --accent-teal: #56d4dd;
      --gradient-1: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #1c2333 100%);
      --shadow: 0 4px 24px rgba(0,0,0,0.3);
    }
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: var(--gradient-1);
      color: var(--text-primary);
      min-height: 100vh;
    }
    /* Scrollbar */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: var(--bg-secondary); }
    ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
    
    .app-container {
      max-width: 1400px;
      margin: 0 auto;
      padding: 16px;
    }
    /* Header */
    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 20px 0;
      border-bottom: 1px solid var(--border);
      margin-bottom: 24px;
      flex-wrap: wrap;
      gap: 12px;
    }
    .header h1 {
      font-size: 24px;
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .header h1 span { 
      background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    .header-actions {
      display: flex;
      gap: 8px;
      align-items: center;
    }
    .last-update {
      font-size: 12px;
      color: var(--text-muted);
    }
    .badge {
      display: inline-block;
      padding: 3px 10px;
      border-radius: 99px;
      font-size: 11px;
      font-weight: 600;
      background: var(--bg-card);
      border: 1px solid var(--border);
      color: var(--text-secondary);
      cursor: default;
    }
    .badge-count {
      background: #1f6feb22;
      border-color: #1f6feb44;
      color: var(--accent-blue);
    }
    
    /* Stats cards */
    .stats-row {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 12px;
      margin-bottom: 24px;
    }
    .stat-card {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 16px 18px;
      transition: transform 0.15s, box-shadow 0.15s;
    }
    .stat-card:hover {
      transform: translateY(-2px);
      box-shadow: var(--shadow);
    }
    .stat-label {
      font-size: 12px;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 6px;
    }
    .stat-value {
      font-size: 24px;
      font-weight: 700;
    }
    .stat-sub {
      font-size: 11px;
      color: var(--text-secondary);
      margin-top: 4px;
    }
    .stat-green { color: var(--accent-green); }
    .stat-red { color: var(--accent-red); }
    .stat-blue { color: var(--accent-blue); }
    .stat-purple { color: var(--accent-purple); }
    
    /* Section headers */
    .section-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin: 28px 0 16px;
    }
    .section-header h2 {
      font-size: 18px;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    
    /* Charts row */
    .charts-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      margin-bottom: 24px;
    }
    @media (max-width: 800px) {
      .charts-row { grid-template-columns: 1fr; }
    }
    .chart-card {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 16px;
      position: relative;
    }
    .chart-card h3 {
      font-size: 14px;
      color: var(--text-secondary);
      margin-bottom: 8px;
    }
    .chart-card canvas {
      max-height: 220px;
    }
    
    /* Top movers */
    .movers-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      margin-bottom: 24px;
    }
    @media (max-width: 800px) {
      .movers-row { grid-template-columns: 1fr; }
    }
    .mover-card {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 16px;
    }
    .mover-card h3 {
      font-size: 14px;
      margin-bottom: 12px;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .mover-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 0;
      border-bottom: 1px solid var(--border);
    }
    .mover-item:last-child { border-bottom: none; }
    .mover-left { display: flex; align-items: center; gap: 8px; }
    .mover-ticker {
      font-weight: 700;
      font-size: 14px;
    }
    .mover-name {
      font-size: 12px;
      color: var(--text-secondary);
    }
    .mover-change {
      font-weight: 700;
      font-size: 14px;
    }
    
    /* Sector breakdown list */
    .sector-list {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 24px;
    }
    .sector-tag {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 6px 14px;
      border-radius: 99px;
      font-size: 13px;
      border: 1px solid var(--border);
      background: var(--bg-card);
      cursor: pointer;
      transition: all 0.15s;
    }
    .sector-tag:hover {
      background: var(--bg-hover);
      border-color: var(--accent-blue);
    }
    .sector-tag.active {
      background: #1f6feb33;
      border-color: var(--accent-blue);
    }
    .sector-dot {
      width: 10px; height: 10px;
      border-radius: 50%;
      display: inline-block;
    }
    
    /* Search */
    .search-bar {
      display: flex;
      gap: 8px;
      margin-bottom: 16px;
    }
    .search-input {
      flex: 1;
      padding: 10px 16px;
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 8px;
      color: var(--text-primary);
      font-size: 14px;
      outline: none;
      transition: border-color 0.15s;
    }
    .search-input:focus {
      border-color: var(--accent-blue);
    }
    .search-input::placeholder {
      color: var(--text-muted);
    }
    
    /* Table */
    .table-wrapper {
      overflow-x: auto;
      border: 1px solid var(--border);
      border-radius: 12px;
      background: var(--bg-card);
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }
    thead th {
      background: var(--bg-secondary);
      padding: 12px 14px;
      text-align: left;
      font-weight: 600;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.3px;
      color: var(--text-secondary);
      border-bottom: 1px solid var(--border);
      white-space: nowrap;
      position: sticky;
      top: 0;
    }
    tbody tr {
      border-bottom: 1px solid var(--border);
      transition: background 0.1s;
    }
    tbody tr:last-child { border-bottom: none; }
    tbody tr:hover { background: var(--bg-hover); }
    tbody td {
      padding: 10px 14px;
      vertical-align: middle;
    }
    .ticker-cell {
      font-weight: 700;
      color: var(--accent-blue);
      cursor: pointer;
    }
    .ticker-cell:hover { text-decoration: underline; }
    .price-up { color: var(--accent-green); }
    .price-down { color: var(--accent-red); }
    
    /* Sparkline mini chart */
    .sparkline {
      width: 80px;
      height: 28px;
      display: inline-block;
    }
    
    /* Detail modal */
    .modal-overlay {
      display: none;
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0,0,0,0.7);
      z-index: 1000;
      justify-content: center;
      align-items: center;
      padding: 20px;
    }
    .modal-overlay.show { display: flex; }
    .modal {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 16px;
      max-width: 600px;
      width: 100%;
      max-height: 80vh;
      overflow-y: auto;
      padding: 24px;
      position: relative;
    }
    .modal-close {
      position: absolute;
      top: 16px; right: 16px;
      background: none;
      border: none;
      color: var(--text-secondary);
      font-size: 20px;
      cursor: pointer;
    }
    .modal-close:hover { color: var(--text-primary); }
    .modal h2 { margin-bottom: 16px; }
    .modal-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin: 12px 0;
    }
    .modal-field {
      padding: 8px 12px;
      background: var(--bg-secondary);
      border-radius: 8px;
    }
    .modal-field label {
      font-size: 11px;
      color: var(--text-muted);
      display: block;
    }
    .modal-field .val {
      font-size: 16px;
      font-weight: 600;
      margin-top: 2px;
    }
    .total-row {
      grid-column: 1 / -1;
    }
    
    /* Loading */
    .loading { opacity: 0.5; }
    
    /* Responsive */
    @media (max-width: 600px) {
      .app-container { padding: 10px; }
      .header h1 { font-size: 18px; }
      .stat-value { font-size: 20px; }
      table { font-size: 13px; }
      tbody td { padding: 8px 10px; }
      .stats-row { grid-template-columns: repeat(2, 1fr); }
    }
  </style>
</head>
<body>
<div class="app-container">
  <!-- Header -->
  <div class="header">
    <h1>🐾 <span>Stock Market Pro</span></h1>
    <div class="header-actions">
      <span class="last-update" id="lastUpdate">{{ last_updated }}</span>
      <span class="badge badge-count">{{ total_recs }} 条推荐</span>
      <span class="badge">{{ stocks_count }} 只股票</span>
    </div>
  </div>

  <!-- Stats Cards -->
  <div class="stats-row">
    <div class="stat-card">
      <div class="stat-label">📈 跟踪股票</div>
      <div class="stat-value stat-blue">{{ stocks_count }}</div>
      <div class="stat-sub">{{ sectors|length }} 个板块</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">📊 总推荐</div>
      <div class="stat-value stat-purple">{{ total_recs }}</div>
      <div class="stat-sub">{{ avg_recs_per_stock }} 次/股</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">📈 最佳表现</div>
      <div class="stat-value stat-green">{% if best_performer %}{{ best_performer.ticker }}{% else %}-{% endif %}</div>
      <div class="stat-sub">{% if best_performer %}+{{ best_performer.change_pct }}%{% endif %}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">📉 最差表现</div>
      <div class="stat-value stat-red">{% if worst_performer %}{{ worst_performer.ticker }}{% else %}-{% endif %}</div>
      <div class="stat-sub">{% if worst_performer %}{{ worst_performer.change_pct }}%{% endif %}</div>
    </div>
  </div>

  <!-- Charts -->
  <div class="charts-row">
    <div class="chart-card">
      <h3>🏭 板块分布</h3>
      <canvas id="sectorChart"></canvas>
    </div>
    <div class="chart-card">
      <h3>📊 板块表现</h3>
      <canvas id="sectorPerfChart"></canvas>
    </div>
  </div>

  <!-- Sector Tags (for filtering) -->
  <div class="sector-list" id="sectorList">
    <div class="sector-tag active" data-sector="all" onclick="filterSector('all')">📋 全部</div>
    {% for sector in sectors %}
    <div class="sector-tag" data-sector="{{ sector }}" onclick="filterSector('{{ sector }}')">
      {% if 'AI' in sector %}🤖{% elif '半' in sector %}💾{% else %}💊{% endif %}
      {{ sector }}
    </div>
    {% endfor %}
  </div>

  <!-- Search -->
  <div class="search-bar">
    <input type="text" class="search-input" id="searchInput" 
           placeholder="🔍 搜索股票名称或代码..." oninput="filterTable()">
  </div>

  <!-- Main Table -->
  <div class="section-header">
    <h2>📋 股票绩效追踪</h2>
  </div>
  <div class="table-wrapper">
    <table>
      <thead>
        <tr>
          <th onclick="sortTable('ticker')">代码 ↕</th>
          <th onclick="sortTable('name')">名称 ↕</th>
          <th>板块</th>
          <th>首次推荐</th>
          <th>首价</th>
          <th>最新价</th>
          <th onclick="sortTable('change')">涨跌幅 ↕</th>
          <th>市值</th>
          <th>追踪次数</th>
          <th>走势</th>
        </tr>
      </thead>
      <tbody id="stockTableBody">
        {% for p in perf_data %}
        <tr data-ticker="{{ p.ticker }}" data-sector="{{ p.sector }}" 
            data-change="{{ p.change_pct }}" data-ticker-name="{{ p.ticker }} {{ p.name }}">
          <td class="ticker-cell" onclick="showDetail('{{ p.ticker }}')">{{ p.ticker }}</td>
          <td>{{ p.name }}</td>
          <td>
            <span class="badge">
              {% if 'AI' in p.sector %}🤖{% elif '半' in p.sector %}💾{% else %}💊{% endif %}
              {{ p.sector }}
            </span>
          </td>
          <td>{{ p.first_date }}</td>
          <td>{% if p.first_price %}${{ "%.2f"|format(p.first_price) }}{% else %}-{% endif %}</td>
          <td class="{% if p.change_pct > 0 %}price-up{% elif p.change_pct < 0 %}price-down{% endif %}">
            {% if p.last_price %}${{ "%.2f"|format(p.last_price) }}{% else %}-{% endif %}
          </td>
          <td class="{% if p.change_pct > 0 %}price-up{% elif p.change_pct < 0 %}price-down{% endif %}">
            {% if p.change_pct > 0 %}▲{% elif p.change_pct < 0 %}▼{% endif %}
            {% if p.change_pct != 0 %}{{ "%.2f"|format(p.change_pct) }}%{% else %}-{% endif %}
          </td>
          <td>{{ p.market_cap_str }}</td>
          <td>{{ p.count }}x</td>
          <td>
            <canvas class="sparkline" id="spark-{{ p.ticker }}"></canvas>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
  <div style="text-align:center;padding:20px;color:var(--text-muted);font-size:13px">
    🐾 Stock Market Pro · 数据来源: AkShare + yfinance · 
    <a href="/api/history" style="color:var(--accent-blue)">API</a>
  </div>
</div>

<!-- Detail Modal -->
<div class="modal-overlay" id="detailModal" onclick="closeModal(event)">
  <div class="modal" onclick="event.stopPropagation()">
    <button class="modal-close" onclick="closeModal()">✕</button>
    <div id="modalContent">
      <h2>Loading...</h2>
    </div>
  </div>
</div>

<script>
// ─── Data ───
const perfData = {{ perf_json|safe }};
const sectorData = {{ sector_json|safe }};

// ─── Search / Filter ───
function filterSector(sector) {
  document.querySelectorAll('.sector-tag').forEach(el => el.classList.remove('active'));
  document.querySelector(`[data-sector="${sector}"]`).classList.add('active');
  filterTable();
}

function filterTable() {
  const q = document.getElementById('searchInput').value.toLowerCase();
  const activeSector = document.querySelector('.sector-tag.active');
  const sector = activeSector ? activeSector.dataset.sector : 'all';
  
  document.querySelectorAll('#stockTableBody tr').forEach(row => {
    const rowSector = row.dataset.sector;
    const rowText = row.dataset.tickerName.toLowerCase();
    const matchSector = sector === 'all' || rowSector === sector;
    const matchSearch = !q || rowText.includes(q);
    row.style.display = matchSector && matchSearch ? '' : 'none';
  });
}

// ─── Sort ───
let sortDir = {};
function sortTable(col) {
  const dir = (sortDir[col] || 1) * -1;
  sortDir[col] = dir;
  
  const tbody = document.getElementById('stockTableBody');
  const rows = Array.from(tbody.querySelectorAll('tr'));
  
  rows.sort((a, b) => {
    let va = a.dataset[col] || a.cells[getColIndex(col)]?.innerText || '';
    let vb = b.dataset[col] || b.cells[getColIndex(col)]?.innerText || '';
    let numA = parseFloat(va), numB = parseFloat(vb);
    if (!isNaN(numA) && !isNaN(numB)) return (numA - numB) * dir;
    return va.localeCompare(vb) * dir;
  });
  
  rows.forEach(r => tbody.appendChild(r));
}
function getColIndex(col) {
  const map = {ticker:0, name:1, sector:2, firstDate:3, firstPrice:4, lastPrice:5, change:6, cap:7, count:8};
  return map[col] !== undefined ? map[col] : 0;
}

// ─── Sparklines ───
function drawSparklines() {
  Object.entries(perfData).forEach(([ticker, data]) => {
    const canvas = document.getElementById('spark-' + ticker);
    if (!canvas || !data.price_history || data.price_history.length < 2) return;
    
    const prices = data.price_history.map(p => p.price);
    const ctx = canvas.getContext('2d');
    const w = canvas.width = 80;
    const h = canvas.height = 28;
    
    const min = Math.min(...prices);
    const max = Math.max(...prices);
    const range = max - min || 1;
    
    ctx.clearRect(0, 0, w, h);
    ctx.beginPath();
    
    const stepX = w / (prices.length - 1);
    prices.forEach((p, i) => {
      const x = i * stepX;
      const y = h - ((p - min) / range) * (h - 4) - 2;
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });
    
    const isUp = prices[prices.length - 1] >= prices[0];
    ctx.strokeStyle = isUp ? '#3fb950' : '#f85149';
    ctx.lineWidth = 1.5;
    ctx.stroke();
  });
}

// ─── Charts ───
function drawCharts() {
  const sectors = Object.keys(sectorData);
  const colors = ['#58a6ff','#3fb950','#f85149','#bc8cff','#d29922','#56d4dd','#f778ba','#79c0ff'];
  
  // Sector Distribution (pie)
  const ctx1 = document.getElementById('sectorChart').getContext('2d');
  new Chart(ctx1, {
    type: 'doughnut',
    data: {
      labels: sectors,
      datasets: [{
        data: sectors.map(s => sectorData[s].count),
        backgroundColor: colors.slice(0, sectors.length),
        borderWidth: 0
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'right', labels: { color: '#8b949e', font: { size: 11 } } }
      }
    }
  });
  
  // Sector Performance (bar)
  const ctx2 = document.getElementById('sectorPerfChart').getContext('2d');
  new Chart(ctx2, {
    type: 'bar',
    data: {
      labels: sectors,
      datasets: [{
        label: '平均涨跌幅 %',
        data: sectors.map(s => sectorData[s].avg_change),
        backgroundColor: sectors.map(s => sectorData[s].avg_change >= 0 ? '#3fb95066' : '#f8514966'),
        borderColor: sectors.map(s => sectorData[s].avg_change >= 0 ? '#3fb950' : '#f85149'),
        borderWidth: 1,
        borderRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        y: { 
          ticks: { color: '#8b949e', callback: v => v + '%' },
          grid: { color: '#30363d33' }
        },
        x: { ticks: { color: '#8b949e', font: { size: 10 } } }
      }
    }
  });
}

// ─── Detail Modal ───
function showDetail(ticker) {
  const data = perfData[ticker];
  if (!data) return;
  
  const prices = data.price_history || [];
  const priceRows = prices.map((p, i) => 
    `<tr><td>${i+1}</td><td>${p.date}</td><td>$${p.price.toFixed(2)}</td></tr>`
  ).reverse().slice(0, 10).join('');
  
  const html = `
    <h2>${data.emoji || '📊'} ${ticker} — ${data.name}</h2>
    <div class="modal-grid">
      <div class="modal-field">
        <label>板块</label>
        <div class="val">${data.sector || '-'}</div>
      </div>
      <div class="modal-field">
        <label>推荐次数</label>
        <div class="val">${data.count}x</div>
      </div>
      <div class="modal-field">
        <label>首次价格</label>
        <div class="val">$${(data.first_price || 0).toFixed(2)}</div>
      </div>
      <div class="modal-field">
        <label>最新价格</label>
        <div class="val ${data.change_pct > 0 ? 'price-up' : data.change_pct < 0 ? 'price-down' : ''}">
          $${(data.last_price || 0).toFixed(2)}
        </div>
      </div>
      <div class="modal-field total-row">
        <label>累计涨跌幅</label>
        <div class="val ${data.change_pct > 0 ? 'price-up' : data.change_pct < 0 ? 'price-down' : ''}">
          ${data.change_pct > 0 ? '▲' : data.change_pct < 0 ? '▼' : ''} ${(data.change_pct || 0).toFixed(2)}%
        </div>
      </div>
    </div>
    <h3 style="margin:16px 0 8px;font-size:14px;color:var(--text-secondary)">📋 价格记录 (最新10次)</h3>
    <table style="font-size:13px">
      <thead><tr><th>#</th><th>日期</th><th>价格</th></tr></thead>
      <tbody>${priceRows}</tbody>
    </table>
    ${data.notes ? `<p style="margin-top:12px;color:var(--text-muted);font-size:12px">📝 ${data.notes}</p>` : ''}
  `;
  document.getElementById('modalContent').innerHTML = html;
  document.getElementById('detailModal').classList.add('show');
}

function closeModal(e) {
  if (e && e.target !== e.currentTarget) return;
  document.getElementById('detailModal').classList.remove('show');
}
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(e); });

// ─── Init ───
document.addEventListener('DOMContentLoaded', () => {
  drawCharts();
  drawSparklines();
});
</script>
</body>
</html>
"""

# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────

@app.route('/')
def index():
    history = load_history()
    watchlist = load_watchlist()
    
    perf = compute_performance(history)
    
    # Prepare performance data for template
    perf_list = []
    for ticker, data in sorted(perf.items(), key=lambda x: abs(x[1].get('change_pct', 0)), reverse=True):
        mc_str = format_cap(data.get('market_cap', 0))
        sec = data.get('sector', '')
        emoji = '🤖' if 'AI' in sec else ('💾' if '半' in sec else '💊')
        perf_list.append({
            'ticker': ticker,
            'name': data.get('name', ticker),
            'sector': sec,
            'emoji': emoji,
            'first_date': data.get('first_date', ''),
            'first_price': data.get('first_price', 0),
            'last_price': data.get('last_price', 0),
            'change_pct': data.get('change_pct', 0),
            'market_cap_str': mc_str,
            'count': data.get('count', 0),
            'price_history': data.get('price_history', []),
            'notes': data.get('notes', '')
        })
    
    # Sector aggregation
    sectors = {}
    for ticker, data in perf.items():
        sec = data.get('sector', '其他')
        if sec not in sectors:
            sectors[sec] = {'count': 0, 'change_sum': 0.0, 'tickers': []}
        sectors[sec]['count'] += 1
        sectors[sec]['tickers'].append(ticker)
        sectors[sec]['change_sum'] += data.get('change_pct', 0)
    
    sector_list = list(sectors.keys())
    for sec in sectors:
        c = sectors[sec]['count']
        sectors[sec]['avg_change'] = round(sectors[sec]['change_sum'] / c, 2) if c > 0 else 0
    
    # Best/worst performers
    valid_perf = [(t, d) for t, d in perf.items() if d.get('change_pct') != 0]
    valid_perf.sort(key=lambda x: x[1]['change_pct'], reverse=True)
    best = valid_perf[0] if valid_perf else None
    worst = valid_perf[-1] if len(valid_perf) > 1 else None
    
    best_performer = {'ticker': best[0], 'change_pct': round(best[1]['change_pct'], 2)} if best else None
    worst_performer = {'ticker': worst[0], 'change_pct': round(worst[1]['change_pct'], 2)} if worst else None
    
    total_recs = history.get('total_recommendations', 0)
    stocks_count = len(perf)
    avg_recs = round(total_recs / stocks_count, 1) if stocks_count > 0 else 0
    
    last_update = history.get('last_updated', '')
    if last_update:
        try:
            dt = datetime.fromisoformat(last_update)
            last_update = dt.strftime('%m-%d %H:%M')
        except:
            pass
    
    return render_template_string(HTML_TEMPLATE,
        stocks_count=stocks_count,
        total_recs=total_recs,
        avg_recs_per_stock=avg_recs,
        sectors=sector_list,
        best_performer=best_performer,
        worst_performer=worst_performer,
        perf_data=perf_list,
        last_updated=last_update,
        perf_json=json.dumps(perf),
        sector_json=json.dumps(sectors)
    )


@app.route('/api/history')
def api_history():
    return jsonify(load_history())


@app.route('/api/performance')
def api_performance():
    history = load_history()
    return jsonify(compute_performance(history))


@app.route('/api/watchlist')
def api_watchlist():
    return jsonify(load_watchlist())


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8765))
    print(f"🚀 Stock Market Pro v2 — http://localhost:{port}")
    print(f"   Dashboard: http://localhost:{port}/")
    print(f"   API:       http://localhost:{port}/api/performance")
    app.run(host='0.0.0.0', port=port, debug=False)
