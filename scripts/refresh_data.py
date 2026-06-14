#!/usr/bin/env python3
"""
Stock Data Refresh — robust pipeline with retry + backoff
Fetches prices & fundamentals for all watchlist stocks.
Tries multiple data sources: AkShare → yfinance → Alpha Vantage
"""

import os
import sys
import json
import time
import random
from datetime import datetime
from typing import Optional, Dict, List

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(SCRIPT_DIR, "stock_recommendation_history.json")
WATCHLIST_FILE = os.path.join(SCRIPT_DIR, "stock_watchlist.json")


def load_watchlist() -> List[Dict]:
    with open(WATCHLIST_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)["watchlist"]


def load_history() -> Dict:
    if not os.path.exists(HISTORY_FILE):
        return {"history": [], "total_recommendations": 0, "last_updated": None}
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_history_entry(entry: Dict):
    history = load_history()
    entry['id'] = len(history['history']) + 1
    history['history'].append(entry)
    history['last_updated'] = datetime.now().isoformat()
    history['total_recommendations'] = len(history['history'])
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def fetch_akshare(ticker: str, name: str, sector: str, notes: str) -> Optional[Dict]:
    """Fetch price via AkShare (East Money US stock data)."""
    import akshare as ak
    try:
        ak_symbol = f"105.{ticker}"
        hist = ak.stock_us_hist(symbol=ak_symbol, period="daily", adjust="")
        if hist is None or hist.empty:
            return None
        
        latest = hist.iloc[-1]
        prev = hist.iloc[-2] if len(hist) >= 2 else latest
        
        price = float(latest['收盘'])
        prev_close = float(prev['收盘'])
        change_pct = (price - prev_close) / prev_close * 100
        
        return {
            'ticker': ticker,
            'name': name,
            'sector': sector,
            'notes': notes,
            'current_price': round(price, 2),
            'change_percent': round(change_pct, 2),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        print(f"  AkShare error for {ticker}: {str(e)[:60]}")
        return None


def fetch_yfinance(ticker: str, name: str, sector: str, notes: str) -> Optional[Dict]:
    """Fetch price via yfinance as fallback."""
    try:
        import yfinance as yf
        t = yf.Ticker(ticker)
        info = t.info
        price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
        prev = info.get("regularMarketPreviousClose") or info.get("previousClose")
        
        if not price or not prev:
            # Fallback: try download
            data = yf.download(ticker, period="5d", progress=False)
            if data is not None and not data.empty:
                price = float(data['Close'].iloc[-1])
                prev = float(data['Close'].iloc[-2]) if len(data) >= 2 else price
        
        if not price:
            return None
        
        prev_close = prev or price
        change_pct = (price - prev_close) / prev_close * 100
        
        mcap = info.get("marketCap") if isinstance(info, dict) else None
        pe = info.get("forwardPE") or info.get("trailingPE") if isinstance(info, dict) else None
        
        result = {
            'ticker': ticker,
            'name': name,
            'sector': sector,
            'notes': notes,
            'current_price': round(float(price), 2),
            'change_percent': round(float(change_pct), 2),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'timestamp': datetime.now().isoformat()
        }
        if mcap:
            result['market_cap'] = int(mcap)
        if pe:
            result['pe_ratio'] = round(float(pe), 2)
        
        return result
    except Exception as e:
        if "YFRateLimitError" in str(e):
            print(f"  yfinance rate limited for {ticker}")
        else:
            print(f"  yfinance error for {ticker}: {str(e)[:60]}")
        return None


def fallback_from_cache(ticker: str, name: str, sector: str, notes: str) -> Optional[Dict]:
    """Use last known price from history if available."""
    history = load_history()
    for rec in reversed(history['history']):
        if rec['ticker'] == ticker:
            print(f"  Using cached data from {rec['date']}")
            return {
                'ticker': ticker,
                'name': name,
                'sector': sector,
                'notes': notes,
                'current_price': rec.get('current_price', rec.get('price')),
                'change_percent': 0,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'timestamp': datetime.now().isoformat(),
                'from_cache': True
            }
    return None


def fetch_stock_data(ticker: str, name: str, sector: str, notes: str, retries: int = 3) -> Optional[Dict]:
    """Try multiple sources with retry logic."""
    sources = [
        ("AkShare", fetch_akshare),
        ("yfinance", fetch_yfinance),
    ]
    
    for source_name, fetch_fn in sources:
        for attempt in range(retries):
            delay = 2 ** attempt + random.uniform(0, 1)
            print(f"  [{source_name}] attempt {attempt+1}/{retries} (wait {delay:.0f}s)...")
            
            result = fetch_fn(ticker, name, sector, notes)
            if result:
                return result
            
            if attempt < retries - 1:
                time.sleep(delay)
    
    # Fallback: use cached data
    return fallback_from_cache(ticker, name, sector, notes)


def main():
    watchlist = load_watchlist()
    today_date = datetime.now().strftime('%Y-%m-%d')
    
    print(f"🚀 数据刷新开始: {len(watchlist)} 只股票 @ {datetime.now()}")
    print("=" * 60)
    
    results = []
    success_count = 0
    
    for i, stock in enumerate(watchlist):
        ticker = stock['ticker']
        name = stock['name']
        sector = stock['sector']
        notes = stock.get('notes', '')
        
        print(f"\n[{i+1}/{len(watchlist)}] {ticker} - {name}")
        
        # Rate limiting between stocks
        if i > 0:
            delay = max(3, 8 - i // 5)  # 3-8 seconds per stock, decreasing as we go
            print(f"  ⏳ 等待 {delay}s 避免限流...")
            time.sleep(delay)
        
        result = fetch_stock_data(ticker, name, sector, notes)
        
        if result and result.get('current_price'):
            results.append(result)
            success_count += 1
            save_history_entry(result)
            print(f"  ✓ ${result['current_price']:.2f} ({result.get('change_percent', 0):+.2f}%)")
            if result.get('market_cap'):
                print(f"    市值: ${result['market_cap']/1e9:.1f}B  PE: {result.get('pe_ratio', 'N/A')}")
        else:
            print(f"  ✗ 所有数据源失败")
            results.append({
                'ticker': ticker, 'name': name, 'sector': sector,
                'current_price': None, 'change_percent': 0,
                'date': today_date, 'timestamp': datetime.now().isoformat(),
                'error': 'All data sources failed'
            })
    
    # Save snapshot
    snapshot = os.path.join(SCRIPT_DIR, f"stock_analysis_{datetime.now().strftime('%Y%m%d')}.json")
    with open(snapshot, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'=' * 60}")
    print(f"✅ 完成: {success_count}/{len(watchlist)} 成功")
    print(f"   Snapshot: {snapshot}")
    
    history = load_history()
    print(f"   历史累计: {history['total_recommendations']} 条")
    
    # Summary table
    print(f"\n{'代码':<6} {'名称':<14} {'板块':<14} {'价格':>10} {'涨跌%':>8} {'市值(B$)':>10} {'PE':>8}")
    print("-" * 80)
    for r in sorted(results, key=lambda x: x.get('current_price') or 9999):
        mc = f"{r.get('market_cap', 0)/1e9:.1f}" if r.get('market_cap') else "-"
        pe = f"{r.get('pe_ratio', 0):.1f}" if r.get('pe_ratio') else "-"
        cp = f"${r.get('current_price', 0):.2f}" if r.get('current_price') else "N/A"
        chg = f"{r.get('change_percent', 0):+.2f}%" if r.get('current_price') else "N/A"
        print(f"{r['ticker']:<6} {r['name']:<14} {r['sector']:<14} {cp:>10} {chg:>8} {mc:>10} {pe:>8}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
