#!/usr/bin/env python3
"""Get current prices for our watchlist stocks"""
import yfinance as yf
import json

# Our target stocks
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

import time

results = []
for stock in stocks:
    time.sleep(0.5)  # 避免请求过快被限流
    ticker = stock["ticker"]
    name = stock["name"]
    allocation = stock["allocation"]
    
    try:
        t = yf.Ticker(ticker)
        info = t.info
        hist = t.history(period="6mo")
        
        current_price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
        market_cap = info.get("marketCap", 0)
        pe = info.get("trailingPE")
        eps = info.get("trailingEps")
        high_52w = info.get("fiftyTwoWeekHigh")
        low_52w = info.get("fiftyTwoWeekLow")
        change_percent = info.get("regularMarketChangePercent", 0)
        price_vs_high = ((current_price - high_52w) / high_52w * 100) if high_52w else 0
        price_vs_low = ((current_price - low_52w) / low_52w * 100) if low_52w else 0
        
        # Calculate shares we can buy
        shares = allocation / current_price if current_price else 0
        
        results.append({
            "ticker": ticker,
            "name": name,
            "price": current_price,
            "shares": shares,
            "allocation": allocation,
            "pe": pe,
            "market_cap_b": market_cap / 1e9 if market_cap else 0,
            "high_52w": high_52w,
            "low_52w": low_52w,
            "vs_high": price_vs_high,
            "vs_low": price_vs_low,
            "change": change_percent
        })
        
        print(f"📈 {ticker} ({name})")
        print(f"   当前价格: ${current_price:.2f}")
        print(f"   52周最高: ${high_52w:.2f} | 52周最低: ${low_52w:.2f}")
        print(f"   距52周高点: {price_vs_high:.1f}% | 距52周低点: {price_vs_low:.1f}%")
        print(f"   市盈率 PE: {pe:.2f}" if pe else "   市盈率 PE: N/A")
        print(f"   市值: ${market_cap/1e9:.2f}B")
        print(f"   今日涨跌: {change_percent:+.2f}%")
        print(f"   ✅ 可买入: {shares:.2f} 股 (投资 ${allocation})")
        
        # Entry analysis
        if price_vs_high > -20:
            print(f"   🎯 入手机会: ⭐⭐⭐ 良好 (距高点<20%)")
        elif price_vs_high > -40:
            print(f"   🎯 入手机会: ⭐⭐⭐⭐ 优秀 (距高点20-40%)")
        else:
            print(f"   🎯 入手机会: ⭐⭐⭐⭐⭐ 极好 (距高点>40%，接近底部)")
        
        print()
        
    except Exception as e:
        print(f"❌ {ticker} 获取失败: {e}")
        print()

print("=" * 80)
print("📊 投资总结")
print("=" * 80)
total_invested = sum(r["allocation"] for r in results)
print(f"计划总投资: ${total_invested:.2f}")
print(f"实际可投资股票数: {len(results)} 只")
print()
print("| 代码 | 名称 | 当前价 | 可买股数 | 分配金额 | 距高点 | 入手机会 |")
print("|------|------|--------|----------|----------|--------|----------|")
for r in results:
    stars = "⭐" * 3 if r["vs_high"] > -20 else ("⭐" * 4 if r["vs_high"] > -40 else "⭐" * 5)
    print(f"| {r['ticker']} | {r['name']} | ${r['price']:.2f} | {r['shares']:.2f} | ${r['allocation']} | {r['vs_high']:.1f}% | {stars} |")
