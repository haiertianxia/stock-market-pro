
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
5-10倍潜力股分析脚本 - 逐个获取历史数据获取最新价格
使用 AkShare 获取数据
分析 AI/科技、半导体、生物医药
"""

import akshare as ak
import pandas as pd
import json
from datetime import datetime

print("=" * 60)
print("股票分析 - 5-10倍潜力股筛选")
print("=" * 60)
print()

# 读取股票池
with open('/home/admin/.openclaw/workspace/skills/stock-market-pro/scripts/stock_watchlist.json', 'r') as f:
    watchlist = json.load(f)['watchlist']

results = []

for stock in watchlist:
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
        
        # 获取基本面估值信息
        try:
            valuation = ak.stock_us_valuation_baidu(symbol=ticker)
            if not valuation.empty:
                for _, row in valuation.iterrows():
                    item = str(row['item']).lower()
                    value = str(row['value'])
                    if 'market cap' in item or '市值' in item:
                        try:
                            if 'B' in value:
                                mc_str = value.replace('$', '').replace('B', '').replace(',', '').strip()
                                market_cap = float(mc_str) * 1e9
                            elif 'T' in value:
                                mc_str = value.replace('$', '').replace('T', '').replace(',', '').strip()
                                market_cap = float(mc_str) * 1e12
                            elif 'M' in value:
                                mc_str = value.replace('$', '').replace('M', '').replace(',', '').strip()
                                market_cap = float(mc_str) * 1e6
                        except:
                            pass
                    if 'pe' in item or '市盈率' in item:
                        try:
                            pe_ratio = float(value)
                        except:
                            pass
        except Exception as e:
            print(f"  获取估值信息警告: {e}")
        
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
        mc_str = f"{market_cap/1e9:.1f}" if market_cap else "N/A"
        pe_str = f"{pe_ratio:.1f}" if pe_ratio else "N/A"
        if current_price:
            print(f"  ✓ 价格: ${current_price:.2f}  涨跌: {change_percent:.2f}%  市值: {mc_str}B  PE: {pe_str}")
        else:
            print(f"  ✗ 未能获取价格")
    
    except Exception as e:
        print(f"  ✗ 错误: {e}")

print()
print("=" * 60)
print("分析完成")
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
print(f"{'代码':<6} {'名称':<15} {'板块':<16} {'价格':>10} {'涨跌%':>8} {'市值(B$)':>10} {'PE':>8}")
print("-" * 85)
for r in results:
    mc = f"{r['market_cap']/1e9:.1f}" if r['market_cap'] else "N/A"
    pe = f"{r['pe_ratio']:.1f}" if r['pe_ratio'] else "N/A"
    cp = f"{r['current_price']:>8.2f}" if r['current_price'] else "N/A"
    chg = f"{r['change_percent']:>7.2f}" if r['current_price'] else "N/A"
    print(f"{r['ticker']:<6} {r['name']:<15} {r['sector']:<16} {cp} {chg} {mc:>10} {pe:>8}")
print("-" * 85)
