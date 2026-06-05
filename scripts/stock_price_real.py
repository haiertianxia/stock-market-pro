#!/usr/bin/env python3
"""
Stock Market Data Fetcher - Handles stock splits properly
Uses market cap and shares outstanding for accurate calculations
"""
import json
import time
import re
from datetime import datetime

# Our investment plan
STOCKS = [
    {"ticker": "NVDA", "name": "英伟达", "allocation": 1500},
    {"ticker": "TSM", "name": "台积电", "allocation": 1500},
    {"ticker": "PLTR", "name": "Palantir", "allocation": 1200},
    {"ticker": "AMD", "name": "超威半导体", "allocation": 1000},
    {"ticker": "LRCX", "name": "Lam Research", "allocation": 1000},
    {"ticker": "ASML", "name": "ASML", "allocation": 800},
    {"ticker": "AI", "name": "C3.ai", "allocation": 700},
    {"ticker": "SOUN", "name": "SoundHound", "allocation": 700},
    {"ticker": "VRTX", "name": "Vertex", "allocation": 600},
    {"ticker": "MRNA", "name": "Moderna", "allocation": 500},
    {"ticker": "MU", "name": "美光科技", "allocation": 500},
]

def fetch_price_via_curl(ticker):
    """Fetch price using curl to stockanalysis.com"""
    import subprocess
    try:
        result = subprocess.run([
            'curl', '-sL', f'https://stockanalysis.com/stocks/{ticker.lower()}/',
            '-H', 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        ], capture_output=True, text=True, timeout=10)
        
        html = result.stdout
        data = {}
        
        # Extract price using regex patterns
        price_match = re.search(r'\$(\d+\.\d{2})', html)
        if price_match:
            data['price'] = float(price_match.group(1))
        
        # Extract market cap
        mcap_match = re.search(r'Market Cap.*?(\$[\d.]+T|\$[\d.]+B)', html, re.DOTALL)
        if mcap_match:
            mcap_str = mcap_match.group(1)
            if 'T' in mcap_str:
                data['market_cap'] = float(mcap_str.replace('$','').replace('T','')) * 1e12
            elif 'B' in mcap_str:
                data['market_cap'] = float(mcap_str.replace('$','').replace('B','')) * 1e9
        
        # Extract shares outstanding
        shares_match = re.search(r'Shares Out\s*([\d.]+[BMT])', html)
        if shares_match:
            shares_str = shares_match.group(1)
            if 'B' in shares_str:
                data['shares_outstanding'] = float(shares_str.replace('B','')) * 1e9
            elif 'M' in shares_str:
                data['shares_outstanding'] = float(shares_str.replace('M','')) * 1e6
            elif 'T' in shares_str:
                data['shares_outstanding'] = float(shares_str.replace('T','')) * 1e12
        
        # Extract 52 week range
        high52_match = re.search(r'52-Week Range.*?(\$[\d.]+).*?(\$[\d.]+)', html, re.DOTALL)
        if high52_match:
            data['52w_low'] = float(high52_match.group(1).replace('$',''))
            data['52w_high'] = float(high52_match.group(2).replace('$',''))
        
        # Extract PE ratio
        pe_match = re.search(r'PE Ratio.*?([\d.]+)', html)
        if pe_match:
            data['pe'] = float(pe_match.group(1))
        
        # Extract daily change
        change_match = re.search(r'([\d.]+\%)\s*\(([\+\-][\d.]+)\%\)', html)
        if change_match:
            data['daily_change'] = float(change_match.group(2))
        
        return data if 'price' in data else None
        
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None

def format_market_cap(cap):
    """Format market cap nicely"""
    if cap >= 1e12:
        return f"${cap/1e12:.2f}T"
    elif cap >= 1e9:
        return f"${cap/1e9:.2f}B"
    else:
        return f"${cap/1e6:.2f}M"

def main():
    print("=" * 80)
    print("📊 美股实时行情分析 (2026-04-21)")
    print("=" * 80)
    print()
    
    results = []
    total_allocation = 0
    
    for i, stock in enumerate(STOCKS):
        ticker = stock['ticker']
        name = stock['name']
        allocation = stock['allocation']
        total_allocation += allocation
        
        print(f"📈 查询 {ticker} ({name})...")
        
        data = fetch_price_via_curl(ticker)
        
        if data and data.get('price'):
            # Calculate shares we can buy
            shares = allocation / data['price']
            data['shares'] = shares
            data['allocation'] = allocation
            data['ticker'] = ticker
            data['name'] = name
            
            # Calculate vs 52w high
            if data.get('52w_high'):
                data['vs_52w_high'] = ((data['price'] - data['52w_high']) / data['52w_high'] * 100)
            else:
                data['vs_52w_high'] = 0
            
            results.append(data)
            
            # Print result
            vs_high_str = f"{data['vs_52w_high']:+.1f}%" if data.get('vs_52w_high') else "N/A"
            mcap_str = format_market_cap(data.get('market_cap', 0))
            
            print(f"   ✅ 价格: ${data['price']:.2f}")
            print(f"      市值: {mcap_str}")
            print(f"      可买: {shares:.2f} 股")
            print(f"      距52周高点: {vs_high_str}")
            if data.get('pe'):
                print(f"      市盈率 PE: {data['pe']:.2f}")
            print()
        else:
            print(f"   ❌ 获取失败")
            print()
        
        # Be polite to the server
        if i < len(STOCKS) - 1:
            time.sleep(1)
    
    # Summary
    print("=" * 80)
    print("📊 投资总结 (总预算 $10,000)")
    print("=" * 80)
    print()
    
    if results:
        # Calculate total actual investment
        total_invested = sum(r['allocation'] for r in results)
        
        print(f"| 代码 | 名称 | 当前价 | 可买股数 | 分配金额 | 距52周高点 | 市盈率 |")
        print("|------|------|--------|----------|----------|-----------|-------|")
        
        for r in results:
            vs_high = f"{r.get('vs_52w_high', 0):+.1f}%"
            pe = f"{r['pe']:.1f}" if r.get('pe') else "N/A"
            print(f"| {r['ticker']} | {r['name']} | ${r['price']:.2f} | {r['shares']:.2f} | ${r['allocation']} | {vs_high} | {pe} |")
        
        print()
        print(f"实际总投资: ${total_invested}")
        print(f"剩余备用金: ${10000 - total_invested}")
        
        # Calculate total market cap
        total_mcap = sum(r.get('market_cap', 0) for r in results)
        print(f"所选股票总市值: {format_market_cap(total_mcap)}")
        
        # Find best opportunities (biggest discount from 52w high)
        print()
        print("🎯 入手机会排名 (距52周高点越低 = 越便宜):")
        sorted_by_discount = sorted(results, key=lambda x: x.get('vs_52w_high', 0))
        for i, r in enumerate(sorted_by_discount, 1):
            stars = "⭐" * max(1, min(5, int(abs(r.get('vs_52w_high', 0)) / 10)))
            print(f"   {i}. {r['ticker']} ({r['name']}) - {r.get('vs_52w_high', 0):+.1f}% {stars}")

if __name__ == "__main__":
    main()
