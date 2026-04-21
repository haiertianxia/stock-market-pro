
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加新推荐股票并获取数据
"""

import akshare as ak
import pandas as pd
import json
from datetime import datetime

# 读取原有股票池
with open('/home/admin/.openclaw/workspace/skills/stock-market-pro/scripts/stock_watchlist.json', 'r') as f:
    data = json.load(f)

# 添加新股票
new_stocks = [
    {"ticker": "GOOGL", "name": "谷歌", "sector": "AI/科技", "notes": "AI大模型+搜索广告"},
    {"ticker": "MSFT", "name": "微软", "sector": "AI/科技", "notes": "Copilot AI增值"},
    {"ticker": "SOUN", "name": "声网", "sector": "AI/科技", "notes": "实时通信AI，小市值"},
    {"ticker": "MU", "name": "美光科技", "sector": "半导体", "notes": "存储芯片周期反转"},
    {"ticker": "TSM", "name": "台积电", "sector": "半导体", "notes": "晶圆代工龙头"},
    {"ticker": "NKTR", "name": "Nektar", "sector": "生物医药", "notes": "临床阶段，小市值"},
    {"ticker": "SGEN", "name": "Seagen", "sector": "生物医药", "notes": "ADC药物技术龙头"},
]

data['watchlist'].extend(new_stocks)

# 保存更新后的股票池
with open('/home/admin/.openclaw/workspace/skills/stock-market-pro/scripts/stock_watchlist.json', 'w') as f:
    json.dump(data, f, indent=2)

print(f"已添加 {len(new_stocks)} 只新股票，总共 {len(data['watchlist'])} 只")

# 获取新数据
results = []

for stock in data['watchlist']:
    ticker = stock['ticker']
    name = stock['name']
    sector = stock['sector']
    print(f"正在获取 {ticker} - {name}...")
    
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
        except Exception as e:
            print(f"  获取历史数据失败: {e}")
        
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
    
    except Exception as e:
        print(f"  ✗ 错误: {e}")

# 保存结果
output_file = f"/home/admin/.openclaw/workspace/stock_analysis_{datetime.now().strftime('%Y%m%d')}.json"
with open(output_file, 'w') as f:
    json.dump({
        'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'results': results
    }, f, indent=2)

print()
print("=" * 85)
print("汇总:")
print("-" * 85)
print(f"{'代码':<6} {'名称':<12} {'板块':<16} {'价格':>10} {'涨跌%':>8}")
print("-" * 85)
for r in results:
    cp = f"{r['current_price']:>8.2f}" if r['current_price'] else "N/A"
    chg = f"{r['change_percent']:>7.2f}" if r['current_price'] else "N/A"
    print(f"{r['ticker']:<6} {r['name']:<12} {r['sector']:<16} {cp} {chg}")
print("-" * 85)
