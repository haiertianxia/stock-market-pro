
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update stock prices using Alpha Vantage API
Free tier: 5 requests/minute, 500/day - enough for us
"""

import requests
import json
import time
from datetime import datetime

# You can get a free API key at https://www.alphavantage.co/
# For now, we use the demo key, but demo key only works for IBM.
# User needs to provide their own free API key.

ALPHA_KEY = "demo"  # Replace with your key

print("=" * 60)
print("股票数据更新 - Alpha Vantage API")
print("=" * 60)
print()

# Read watchlist
with open('/home/admin/.openclaw/workspace/skills/stock-market-pro/scripts/stock_watchlist.json', 'r') as f:
    watchlist = json.load(f)['watchlist']

if ALPHA_KEY == "demo":
    print("⚠️  警告: 使用的是demo key，只能查询IBM。需要你提供免费的API key")
    print("   去 https://www.alphavantage.co/ 注册一个，完全免费")
    print()

results = []
success_count = 0

for i, stock in enumerate(watchlist):
    ticker = stock['ticker']
    name = stock['name']
    sector = stock['sector']
    print(f"[{i+1}/{len(watchlist)}] 获取 {ticker} - {name}...")
    
    current_price = None
    change_percent = 0
    market_cap = None
    pe_ratio = None
    
    try:
        # Get daily data
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={ALPHA_KEY}"
        r = requests.get(url)
        data = r.json()
        
        if "Global Quote" in data and "05. price" in data["Global Quote"]:
            price_str = data["Global Quote"]["05. price"]
            change_str = data["Global Quote"]["10. change percent"]
            if price_str:
                current_price = float(price_str)
                success_count += 1
            if change_str:
                change_percent = float(change_str.strip('%'))
        
        # Get overview for market cap and PE
        url2 = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={ALPHA_KEY}"
        r2 = requests.get(url2)
        data2 = r2.json()
        
        if "MarketCapitalization" in data2 and data2["MarketCapitalization"]:
            try:
                market_cap = float(data2["MarketCapitalization"])
            except:
                pass
        if "PERatio" in data2 and data2["PERatio"]:
            try:
                pe_ratio = float(data2["PERatio"])
            except:
                pass
                
    except Exception as e:
        print(f"  ✗ 错误: {e}")
    
    result = {
        'ticker': ticker,
        'name': name,
        'sector': sector,
        'current_price': current_price,
        'change_percent': change_percent,
        'market_cap': market_cap,
        'pe_ratio': pe_ratio,
        'timestamp': datetime.now().isoformat()
    }
    results.append(result)
    
    if current_price:
        mc_str = f"{market_cap/1e9:.1f}B" if market_cap else "N/A"
        pe_str = f"{pe_ratio:.1f}" if pe_ratio else "N/A"
        print(f"  ✓ 价格: ${current_price:.2f}  涨跌: {change_percent:.2f}%  市值: {mc_str}  PE: {pe_str}")
    else:
        print(f"  ✗ 未能获取价格")
    
    # Alpha Vantage free tier: 5 requests per minute = wait 12 seconds between requests
    if i != len(watchlist) - 1 and ALPHA_KEY != "demo":
        print(f"  ⏳ 等待12秒 (遵守API限制)...\n")
        time.sleep(12)
    elif ALPHA_KEY != "demo":
        print()

print()
print("=" * 60)
print(f"分析完成，成功获取 {success_count}/{len(watchlist)} 只")
print("=" * 60)

# Save results
output_file = f"/home/admin/.openclaw/workspace/stock_analysis_{datetime.now().strftime('%Y%m%d')}.json"
with open(output_file, 'w') as f:
    json.dump({
        'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'results': results
    }, f, indent=2)

print(f"结果已保存到: {output_file}")

# Print summary
print()
print("汇总:")
print("-" * 95)
print(f"{'代码':<6} {'名称':<12} {'板块':<16} {'价格':>10} {'涨跌%':>8} {'市值(B$)':>10} {'PE':>8}")
print("-" * 95)
for r in results:
    mc = f"{r['market_cap']/1e9:.1f}" if r.get('market_cap') else "N/A"
    pe = f"{r['pe_ratio']:.1f}" if r.get('pe_ratio') else "N/A"
    cp = f"{r['current_price']:>8.2f}" if r['current_price'] else "N/A"
    chg = f"{r['change_percent']:>7.2f}" if r['current_price'] is not None else "N/A"
    print(f"{r['ticker']:<6} {r['name']:<12} {r['sector']:<16} {cp} {chg} {mc:>10} {pe:>8}")
print("-" * 95)
