#!/usr/bin/env python3
"""
Stock Market Pro - Enhanced Web Service
Supports multiple data sources with automatic failover
"""
import os
import sys
import json
import time
import threading
import requests
import re
from datetime import datetime, time as dtime
from flask import Flask, render_template_string, jsonify, request

app = Flask(__name__)

PORT = int(os.environ.get('PORT', 8765))
UPDATE_INTERVAL = 300
RATE_LIMIT_DELAY = 15

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WATCHLIST_FILE = os.path.join(BASE_DIR, 'scripts', 'stock_watchlist.json')


class StockDataSource:
    name = "Base"
    rate_limited = False
    last_call = 0
    
    def fetch(self, ticker):
        raise NotImplementedError
    
    def should_delay(self):
        elapsed = time.time() - self.last_call
        if elapsed < RATE_LIMIT_DELAY:
            time.sleep(RATE_LIMIT_DELAY - elapsed)
        self.last_call = time.time()


class YahooFinanceSource(StockDataSource):
    name = "Yahoo Finance"
    
    def fetch(self, ticker):
        self.should_delay()
        try:
            import yfinance as yf
            t = yf.Ticker(ticker)
            info = t.info
            return {
                'ticker': ticker,
                'price': info.get('currentPrice') or info.get('regularMarketPrice'),
                'change': info.get('regularMarketChangePercent', 0),
                'high52': info.get('fiftyTwoWeekHigh'),
                'low52': info.get('fiftyTwoWeekLow'),
                'market_cap': info.get('marketCap'),
                'pe': info.get('trailingPE'),
                'shares': info.get('sharesOutstanding'),
                'source': self.name
            }
        except Exception as e:
            self.rate_limited = 'Too Many Requests' in str(e) or 'Rate limited' in str(e)
            return None


class StockAnalysisSource(StockDataSource):
    name = "StockAnalysis"
    
    def fetch(self, ticker):
        self.should_delay()
        try:
            url = f"https://stockanalysis.com/stocks/{ticker.lower()}/"
            resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            html = resp.text
            data = {}
            
            # Extract first major price (after ticker name)
            price_match = re.search(r'\$([1-9]\d{2,}\.\d{2})', html)
            if not price_match:
                price_match = re.search(r'\$([1-9]\d\d?\.\d{2})', html)
            if price_match:
                data['price'] = float(price_match.group(1))
            
            mcap_match = re.search(r'Market Cap.*?(\$[\d.]+[TMB])', html, re.DOTALL)
            if mcap_match:
                mcap_str = mcap_match.group(1)
                if 'T' in mcap_str:
                    data['market_cap'] = float(mcap_str.replace('$','').replace('T','')) * 1e12
                elif 'B' in mcap_str:
                    data['market_cap'] = float(mcap_str.replace('$','').replace('B','')) * 1e9
            
            pe_match = re.search(r'PE Ratio([\d.]+)', html)
            if pe_match:
                data['pe'] = float(pe_match.group(1))
            
            range_match = re.search(r'52-Week Range.*?\$([\d.]+).*?\$([\d.]+)', html, re.DOTALL)
            if range_match:
                data['low52'] = float(range_match.group(1))
                data['high52'] = float(range_match.group(2))
            
            data['ticker'] = ticker
            data['source'] = self.name
            data['shares'] = None
            data['change'] = 0
            
            return data if data.get('price') else None
        except Exception as e:
            self.rate_limited = True
            return None


class AlphaVantageSource(StockDataSource):
    name = "Alpha Vantage"
    api_key = os.environ.get('ALPHA_VANTAGE_KEY', 'demo')
    
    def fetch(self, ticker):
        self.should_delay()
        try:
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={self.api_key}"
            resp = requests.get(url, timeout=10)
            data = resp.json()
            
            if 'Global Quote' in data and data['Global Quote']:
                q = data['Global Quote']
                return {
                    'ticker': ticker,
                    'price': float(q.get('05. price', 0)),
                    'change': float(q.get('10. change percent', 0).rstrip('%')),
                    'high52': None, 'low52': None,
                    'market_cap': None, 'pe': None, 'shares': None,
                    'source': self.name
                }
            return None
        except Exception as e:
            self.rate_limited = True
            return None


class StockDataManager:
    def __init__(self):
        self.sources = [StockAnalysisSource(), YahooFinanceSource(), AlphaVantageSource()]
        self.current_source_idx = 0
        self.cache = {}
        self.cache_time = {}
        self.cache_duration = 60
    
    def get_source(self):
        for i in range(len(self.sources)):
            idx = (self.current_source_idx + i) % len(self.sources)
            if not self.sources[idx].rate_limited:
                return self.sources[idx]
        time.sleep(60)
        return self.sources[0]
    
    def fetch_stock(self, ticker, force=False):
        if not force and ticker in self.cache:
            if time.time() - self.cache_time.get(ticker, 0) < self.cache_duration:
                return self.cache[ticker]
        
        for i in range(len(self.sources)):
            source = self.get_source()
            print(f"  Trying {source.name} for {ticker}...")
            data = source.fetch(ticker)
            
            if data and data.get('price'):
                self.cache[ticker] = data
                self.cache_time[ticker] = time.time()
                print(f"  Got {ticker}: ${data['price']:.2f} from {source.name}")
                return data
            elif source.rate_limited:
                self.current_source_idx = (self.sources.index(source) + 1) % len(self.sources)
        
        print(f"  All sources failed for {ticker}")
        return None
    
    def fetch_all(self, tickers):
        results = []
        for ticker in tickers:
            data = self.fetch_stock(ticker)
            if data:
                results.append(data)
        return results


data_manager = StockDataManager()


def is_market_open():
    now = datetime.now()
    return now.weekday() < 5 and dtime(9, 30) <= now.time() <= dtime(16, 0)


def background_update():
    while True:
        try:
            if os.path.exists(WATCHLIST_FILE):
                with open(WATCHLIST_FILE, 'r') as f:
                    watchlist = json.load(f).get('watchlist', [])
                
                tickers = [s['ticker'] for s in watchlist]
                print(f"[{datetime.now()}] Updating {len(tickers)} stocks...")
                
                results = data_manager.fetch_all(tickers)
                
                with open(os.path.join(BASE_DIR, 'stock_cache.json'), 'w') as f:
                    json.dump({'data': results, 'updated': datetime.now().isoformat(), 'market_open': is_market_open()}, f, indent=2)
                
                print(f"[{datetime.now()}] Update complete, next in {UPDATE_INTERVAL}s")
        except Exception as e:
            print(f"[{datetime.now()}] Update error: {e}")
        
        time.sleep(UPDATE_INTERVAL)


HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Stock Market Pro - Real-time Dashboard</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #e2e8f0; min-height: 100vh; }
        .header { background: linear-gradient(135deg, #1e293b 0%, #334155 100%); padding: 20px 30px; border-bottom: 1px solid #334155; }
        .header h1 { font-size: 1.8rem; margin-bottom: 10px; }
        .header .meta { font-size: 0.9rem; color: #94a3b8; }
        .status { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; margin-left: 10px; }
        .status.open { background: #10b981; color: white; }
        .status.closed { background: #ef4444; color: white; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .stat-card { background: #1e293b; border-radius: 12px; padding: 20px; border: 1px solid #334155; }
        .stat-card .label { font-size: 0.8rem; color: #94a3b8; margin-bottom: 5px; }
        .stat-card .value { font-size: 1.5rem; font-weight: 600; }
        .controls { margin-bottom: 20px; display: flex; gap: 10px; flex-wrap: wrap; }
        .btn { background: #3b82f6; color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; font-size: 0.9rem; }
        .btn:hover { background: #2563eb; }
        .btn.refresh { background: #10b981; }
        .btn.refresh:hover { background: #059669; }
        table { width: 100%; border-collapse: collapse; background: #1e293b; border-radius: 12px; overflow: hidden; }
        th, td { padding: 15px; text-align: left; border-bottom: 1px solid #334155; }
        th { background: #334155; font-weight: 600; font-size: 0.85rem; text-transform: uppercase; }
        tr:hover { background: #263344; }
        .price { font-size: 1.1rem; font-weight: 600; }
        .positive { color: #10b981; }
        .negative { color: #ef4444; }
        .source-tag { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 0.7rem; background: #475569; color: #94a3b8; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Stock Market Pro Dashboard</h1>
        <div class="meta">
            Last Updated: {{ updated }}
            <span class="status {% if market_open %}open{% else %}closed{% endif %}">
                {% if market_open %}Market Open{% else %}Market Closed{% endif %}
            </span>
        </div>
    </div>
    <div class="container">
        <div class="stats">
            <div class="stat-card"><div class="label">Total Stocks</div><div class="value">{{ total_stocks }}</div></div>
            <div class="stat-card"><div class="label">Data Source</div><div class="value">Multi-Source (Auto Failover)</div></div>
        </div>
        <div class="controls">
            <button class="btn refresh" onclick="refreshData()">Refresh Now</button>
            <button class="btn" onclick="window.location.reload()">Reload Page</button>
        </div>
        <table>
            <thead>
                <tr>
                    <th>Ticker</th><th>Price</th><th>Change</th><th>52W High</th><th>52W Low</th><th>Market Cap</th><th>P/E</th><th>Source</th>
                </tr>
            </thead>
            <tbody>
                {% for stock in stocks %}
                <tr>
                    <td><strong>{{ stock.ticker }}</strong></td>
                    <td class="price">${{ "%.2f"|format(stock.price) }}</td>
                    <td class="{{ 'positive' if stock.change > 0 else 'negative' }}">{{ "%+.2f"|format(stock.change) }}%</td>
                    <td>{% if stock.high52 %}${{ "%.2f"|format(stock.high52) }}{% else %}N/A{% endif %}</td>
                    <td>{% if stock.low52 %}${{ "%.2f"|format(stock.low52) }}{% else %}N/A{% endif %}</td>
                    <td>
                        {% if stock.market_cap %}
                            {% if stock.market_cap >= 1e12 %}${{ "%.2f"|format(stock.market_cap / 1e12) }}T
                            {% elif stock.market_cap >= 1e9 %}${{ "%.2f"|format(stock.market_cap / 1e9) }}B
                            {% else %}${{ "%.0f"|format(stock.market_cap / 1e6) }}M{% endif %}
                        {% else %}N/A{% endif %}
                    </td>
                    <td>{% if stock.pe %}{{ "%.1f"|format(stock.pe) }}{% else %}N/A{% endif %}</td>
                    <td><span class="source-tag">{{ stock.source }}</span></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    <script>
        function refreshData() {
            fetch('/api/refresh').then(r => r.json()).then(d => {
                if (d.success) { alert('Refreshed ' + d.count + ' stocks!'); window.location.reload(); }
            }).catch(e => alert('Error: ' + e));
        }
        setTimeout(() => window.location.reload(), 300000);
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    cache_file = os.path.join(BASE_DIR, 'stock_cache.json')
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            cache_data = json.load(f)
        stocks = sorted(cache_data.get('data', []), key=lambda x: x.get('market_cap', 0) or 0, reverse=True)
        return render_template_string(HTML, stocks=stocks, updated=cache_data.get('updated', 'Never'), market_open=cache_data.get('market_open', False), total_stocks=len(stocks))
    return render_template_string(HTML, stocks=[], updated='Never', market_open=False, total_stocks=0)


@app.route('/api/stocks')
def api_stocks():
    cache_file = os.path.join(BASE_DIR, 'stock_cache.json')
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            return jsonify(json.load(f))
    return jsonify({'data': [], 'updated': None, 'market_open': False})


@app.route('/api/stock/<ticker>')
def api_stock(ticker):
    data = data_manager.fetch_stock(ticker, force=True)
    return jsonify(data) if data else jsonify({'error': 'Failed'}), 500


@app.route('/api/refresh')
def api_refresh():
    if os.path.exists(WATCHLIST_FILE):
        with open(WATCHLIST_FILE, 'r') as f:
            watchlist = json.load(f).get('watchlist', [])
        results = data_manager.fetch_all([s['ticker'] for s in watchlist])
        with open(os.path.join(BASE_DIR, 'stock_cache.json'), 'w') as f:
            json.dump({'data': results, 'updated': datetime.now().isoformat(), 'market_open': is_market_open()}, f, indent=2)
        return jsonify({'success': True, 'count': len(results)})
    return jsonify({'error': 'Watchlist not found'}), 404


if __name__ == '__main__':
    threading.Thread(target=background_update, daemon=True).start()
    print(f"Starting Stock Market Pro Web Service on port {PORT}...")
    app.run(host='0.0.0.0', port=PORT, debug=False)
