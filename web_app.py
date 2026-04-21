#!/usr/bin/env python3
"""
Stock Market Pro Web Service
Provides web interface for stock analysis and displays daily recommendations
"""

import os
import sys
import json
from datetime import datetime
from flask import Flask, render_template_string, jsonify, request

app = Flask(__name__)

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(BASE_DIR, 'scripts', 'stock_recommendation_history.json')
WATCHLIST_FILE = os.path.join(BASE_DIR, 'scripts', 'stock_watchlist.json')

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Stock Market Pro - Stock Screener</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { color: #333; border-bottom: 2px solid #eee; padding-bottom: 10px; }
        h2 { color: #444; margin-top: 30px; }
        table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        th { background-color: #f0f0f0; text-align: left; padding: 10px; border-bottom: 2px solid #ddd; }
        td { padding: 8px 10px; border-bottom: 1px solid #eee; }
        tr:hover { background-color: #f9f9f9; }
        .sector-AI { background-color: #e8f4ff; }
        .sector-半导体 { background-color: #fff3e8; }
        .sector-生物医药 { background-color: #e8ffe8; }
        .positive { color: #d32f2f; font-weight: bold; }
        .negative { color: #1976d2; }
        .header-stats { background: #f8f9fa; padding: 15px; border-radius: 6px; margin-bottom: 20px; }
        .filter-section { margin: 15px 0; padding: 15px; background: #f8f9fa; border-radius: 6px; }
        .filter-btn { padding: 6px 12px; margin: 2px; border: 1px solid #ddd; border-radius: 4px; background: white; cursor: pointer; }
        .filter-btn.active { background: #007bff; color: white; border-color: #007bff; }
    </style>
</head>
<body>
<div class="container">
    <h1>🐾 Stock Market Pro - 股票推荐历史</h1>
    
    <div class="header-stats">
        <strong>总共推荐:</strong> {{ total_recommendations }} 只股票 | 
        <strong>最后更新:</strong> {{ last_updated }}
    </div>

    <div class="filter-section">
        <strong>筛选板块:</strong> 
        <button class="filter-btn {{ 'active' if current_filter == 'all' else '' }}" onclick="window.location='?sector=all'">全部</button>
        {% for sector in sectors %}
        <button class="filter-btn {{ 'active' if current_filter == sector else '' }}" onclick="window.location='?sector={{ sector }}'">{{ sector }}</button>
        {% endfor %}
    </div>

    <table>
        <thead>
            <tr>
                <th>日期</th>
                <th>代码</th>
                <th>名称</th>
                <th>板块</th>
                <th>价格</th>
                <th>市值(B$)</th>
                <th>PE</th>
                <th>注释</th>
            </tr>
        </thead>
        <tbody>
        {% for rec in recommendations %}
        <tr class="sector-{{ rec.sector.split('/')[0] }}">
            <td>{{ rec.date }}</td>
            <td><strong>{{ rec.ticker }}</strong></td>
            <td>{{ rec.name }}</td>
            <td>{{ rec.sector }}</td>
            <td class="{{ 'positive' if rec.change > 0 else 'negative' }}">{{ "%.2f"|format(rec.price) }} {% if rec.change > 0 %}(+{{ "%.2f"|format(rec.change )}}%){% elif rec.change < 0 %}({{ "%.2f"|format(rec.change )}}%){% endif %}</td>
            <td>{% if rec.market_cap %}{{ "%.2f"|format(rec.market_cap) }}{% else %}-{% endif %}</td>
            <td>{% if rec.pe %}{{ "%.2f"|format(rec.pe) }}{% else %}-{% endif %}</td>
            <td>{{ rec.notes }}</td>
        </tr>
        {% endfor %}
        </tbody>
    </table>
</div>
</body>
</html>
"""

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return {"history": [], "total_recommendations": 0, "last_updated": None}
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_watchlist():
    if not os.path.exists(WATCHLIST_FILE):
        return []
    with open(WATCHLIST_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get("watchlist", [])

@app.route('/')
def index():
    sector_filter = request.args.get('sector', 'all')
    
    history = load_history()
    watchlist = load_watchlist()
    
    # Get unique sectors
    sectors = sorted(list(set([rec["sector"] for rec in history.get("history", []) if rec.get("sector")])))
    
    # Filter recommendations
    recommendations = history.get("history", [])
    if sector_filter != 'all':
        recommendations = [r for r in recommendations if r.get("sector", "").startswith(sector_filter)]
    
    # Sort by date descending
    recommendations = sorted(recommendations, key=lambda x: x.get("date", ""), reverse=True)
    
    return render_template_string(HTML_TEMPLATE,
        total_recommendations=history.get("total_recommendations", 0),
        last_updated=history.get("last_updated", "Never"),
        recommendations=recommendations,
        sectors=sectors,
        current_filter=sector_filter
    )

@app.route('/api/history')
def api_history():
    history = load_history()
    return jsonify(history)

@app.route('/api/watchlist')
def api_watchlist():
    with open(WATCHLIST_FILE, 'r', encoding='utf-8') as f:
        return jsonify(json.load(f))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8765))
    app.run(host='0.0.0.0', port=port, debug=False)
