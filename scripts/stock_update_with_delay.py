
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新股票数据 - 添加延迟避免限流
"""

import akshare as ak
import pandas as pd
import json
import time
from datetime import datetime

print("=" * 60)
print("股票数据更新 (带延迟，避免限流)")
print("=" * 60)
print()

# 读取股票池
with open('/home/admin/.openclaw/workspace/skills/stock-market-pro/scripts/stock_watchlist.json', 'r') as f:
    watchlist = json.load(f)['watchlist']

results = []
success_count = 0

for i, stock in enumerate(watchlist):
    ticker = stock['ticker']
    name = stock['name']
    sector = stock['sector']
    print(f"[{i+1}/{len(watchlist)}] 获取 {ticker} - {name}...")
    
    try:
        current_price = None
        change_percent = 0
        market_cap = None
        pe_ratio = None
        
        # AkShare 美股代码需要前缀 105.
        ak_symbol = f"105.{ticker}"
        
        # 通过历史数据获取最新价格
        try:
            hist = ak.stock_us_hist(symbol=ak_symbol, period="daily", adjust="")
            if not hist.empty:
                latest = hist.iloc[-1]
                current_price = float(latest['收盘'])
                # 计算涨跌幅 (相比前一日)
                if len(hist) >= 2:
                    prev_close = float(hist.iloc[-2]['收盘'])
                    change_percent = (current_price - prev_close) / prev_close * 100
                success_count += 1
        except Exception as e:
            print(f"  获取历史数据失败: {e}")
    
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
        print(f"  ✓ 价格: ${current_price:.2f}  涨跌: {change_percent:.2f}%")
    else:
        print(f"  ✗ 未能获取价格")
    
    # 添加延迟避免限流，每请求一次等 30 秒
    if i != len(watchlist) - 1:
        print(f"  ⏳ 等待30秒避免限流...\n")
        time.sleep(30)

print()
print("=" * 60)
print(f"分析完成，成功获取 {success_count}/{len(watchlist)} 只")
print("=" * 60)

# 保存结果
output_file = f"/home/admin/.openclaw/workspace/stock_analysis_{datetime.now().strftime('%Y%m%d')}.json"
with open(output_file, 'w') as f:
    json.dump({
        'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'results': results
    }, f, indent=2)

print(f"结果已保存到: {output_file}")

# 打印汇总表格
print()
print("汇总:")
print("-" * 85)
print(f"{'代码':<6} {'名称':<12} {'板块':<16} {'价格':>10} {'涨跌%':>8}")
print("-" * 85)
for r in results:
    cp = f"{r['current_price']:>8.2f}" if r['current_price'] else "N/A"
    chg = f"{r['change_percent']:>7.2f}" if r['current_price'] else "N/A"
    print(f"{r['ticker']:<6} {r['name']:<12} {r['sector']:<16} {cp} {chg}")
print("-" * 85)
