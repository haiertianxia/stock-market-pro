
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取基本面数据 - 使用不同接口
"""

import akshare as ak
import pandas as pd
import json
from datetime import datetime

# 读取已有结果
with open('/home/admin/.openclaw/workspace/stock_analysis_20260418.json', 'r') as f:
    data = json.load(f)

results = data['results']

print("正在补充获取基本面数据 (市值、PE)...\n")

# 尝试用 stock_financial_us_report_em 获取
for r in results:
    if not r['current_price']:
        continue
    
    ticker = r['ticker']
    print(f"获取 {ticker} 基本面...")
    
    try:
        # 尝试获取财务指标
        indicators = ak.stock_financial_us_analysis_indicator_em(symbol=ticker)
        if not indicators.empty:
            print(f"  拿到 {len(indicators)} 条指标")
            # 找市值和PE
            for _, row in indicators.iterrows():
                item = str(row['item_name']).lower()
                if 'market' in item and 'cap' in item:
                    try:
                        val = float(row['latest'])
                        # 单位是百万人民币，需要转换为美元近似估算
                        # 大概 1:7.2 汇率
                        val_usd_mb = val / 7.2
                        r['market_cap'] = val_usd_mb * 1e6
                    except:
                        pass
                if 'pe' in item:
                    try:
                        r['pe_ratio'] = float(row['latest'])
                    except:
                        pass
    except Exception as e:
        print(f"  错误: {e}")
    
    # 如果还没有市值，尝试另一种方式
    if not r['market_cap']:
        try:
            # 从新浪获取
            info = ak.stock_us_individual_basic_info_xq(symbol=ticker)
            if not info.empty:
                for _, row in info.iterrows():
                    item = str(row['key']).lower()
                    value = str(row['value'])
                    if 'marketcap' in item:
                        try:
                            # 可能是 X.XXB 格式
                            val_str = value.replace('B', '').replace('$', '').strip()
                            r['market_cap'] = float(val_str) * 1e9
                        except:
                            pass
                    if 'pe' in item:
                        try:
                            r['pe_ratio'] = float(value)
                        except:
                            pass
        except Exception as e:
            print(f"  xq 错误: {e}")

# 重新保存
output_file = f"/home/admin/.openclaw/workspace/stock_analysis_{datetime.now().strftime('%Y%m%d')}.json"
with open(output_file, 'w') as f:
    json.dump({
        'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'results': results
    }, f, indent=2)

# 打印完整表格
print()
print("=" * 85)
print("汇总 (含基本面):")
print("-" * 85)
print(f"{'代码':<6} {'名称':<15} {'板块':<16} {'价格':>10} {'涨跌%':>8} {'市值(B$)':>10} {'PE':>8}")
print("-" * 85)
for r in results:
    mc = f"{r['market_cap']/1e9:.1f}" if r.get('market_cap') else "N/A"
    pe = f"{r['pe_ratio']:.1f}" if r.get('pe_ratio') else "N/A"
    cp = f"{r['current_price']:>8.2f}" if r['current_price'] else "N/A"
    chg = f"{r['change_percent']:>7.2f}" if r['current_price'] else "N/A"
    print(f"{r['ticker']:<6} {r['name']:<15} {r['sector']:<16} {cp} {chg} {mc:>10} {pe:>8}")
print("-" * 85)
