
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
5-10倍潜力股分析脚本
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
with open('/home/admin/.openclaw/workspace/stock_watchlist.json', 'r') as f:
    watchlist = json.load(f)['watchlist']

results = []

# 先获取一次全部美股实时报价
print("正在获取全部美股实时报价...")
all_us_stocks = ak.stock_us_spot_em()
print(f"获取完成，共 {len(all_us_stocks)} 只股票")
print()

for stock in watchlist:
    ticker = stock['ticker']
    name = stock['name']
    sector = stock['sector']
    print(f"正在分析 {ticker} - {name}...")
    
    try:
        current_price = None
        change_percent = 0
        market_cap = None
        pe_ratio = None
        
        # 查找对应的股票
        matched = all_us_stocks[all_us_stocks['代码'].str.lower() == ticker.lower()]
        
        if not matched.empty:
            row = matched.iloc[0]
            current_price = float(row['最新价']) if pd.notna(row['最新价']) else None
            change_percent = float(row['涨跌幅%']) if pd.notna(row['涨跌幅%']) else 0
        
        # 获取基本面信息
        try:
            basic_info = ak.stock_individual_basic_info_us_xq(symbol=ticker)
            if basic_info is not None and not basic_info.empty:
                for _, row in basic_info.iterrows():
                    item = str(row['item']).lower()
                    value = str(row['value'])
                    if 'market cap' in item or '市值' in item:
                        try:
                            # 处理格式 "$1500.5B" -> 1500.5e9
                            mc_str = value.replace('$', '').replace('B', '').replace(',', '').strip()
                            market_cap = float(mc_str) * 1e9
                        except:
                            pass
                    if 'pe' in item or '市盈率' in item:
                        try:
                            pe_ratio = float(value)
                        except:
                            pass
        except Exception as e:
            print(f"  获取基本面警告: {e}")
        
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
        print(f"  ✓ 价格: ${current_price:.2f}  涨跌: {change_percent:.2f}%  市值: {mc_str}B  PE: {pe_str}")
    
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
    chg = f"{r['change_percent']:>7.2f}" if r['change_percent'] else "N/A"
    print(f"{r['ticker']:<6} {r['name']:<15} {r['sector']:<16} {cp} {chg} {mc:>10} {pe:>8}")
print("-" * 85)
