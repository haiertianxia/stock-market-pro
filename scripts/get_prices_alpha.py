#!/usr/bin/env python3
"""Get stock prices using Alpha Vantage free API"""
import urllib.request
import json
import time

# Free API key for limited requests
ALPHA_VANTAGE_KEY = "demo"  # Using demo key first

stocks = [
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

print("=" * 80)
print("📊 当前股价分析 - 入手机会评估")
print("=" * 80)
print()

for stock in stocks:
    ticker = stock["ticker"]
    name = stock["name"]
    allocation = stock["allocation"]
    
    try:
        time.sleep(15)  # Alpha Vantage free tier: 5 requests/minute
        
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={ALPHA_VANTAGE_KEY}"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
        
        if 'Global Quote' in data and data['Global Quote']:
            quote = data['Global Quote']
            current_price = float(quote.get('05. price', 0))
            high_52w = float(quote.get('03. high', current_price * 1.1))
            low_52w = float(quote.get('04. low', current_price * 0.9))
            change_percent = float(quote.get('10. change percent', 0).rstrip('%'))
            
            shares = allocation / current_price if current_price else 0
            price_vs_high = ((current_price - high_52w) / high_52w * 100) if high_52w else 0
            
            print(f"📈 {ticker} ({name})")
            print(f"   当前价格: ${current_price:.2f}")
            print(f"   今日涨跌: {change_percent:+.2f}%")
            print(f"   ✅ 可买入: {shares:.2f} 股 (投资 ${allocation})")
            
            if price_vs_high > -20:
                print(f"   🎯 入手机会: ⭐⭐⭐ 良好 (距高点{price_vs_high:.1f}%)")
            elif price_vs_high > -40:
                print(f"   🎯 入手机会: ⭐⭐⭐⭐ 优秀 (距高点{price_vs_high:.1f}%)")
            else:
                print(f"   🎯 入手机会: ⭐⭐⭐⭐⭐ 极好 (距高点{price_vs_high:.1f}%)")
            print()
        else:
            print(f"⚠️ {ticker} API返回空数据")
            
    except Exception as e:
        print(f"❌ {ticker} 获取失败: {e}")
        print()

print("=" * 80)
