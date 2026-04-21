#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
5-10倍潜力股分析脚本 - 带历史推荐存储功能
每次分析结果自动存入历史数据库，支持查询历史推荐
"""

import akshare as ak
import pandas as pd
import json
import os
import argparse
from datetime import datetime

HISTORY_FILE = "/home/admin/.openclaw/workspace/skills/stock-market-pro/scripts/stock_recommendation_history.json"
WATCHLIST_FILE = "/home/admin/.openclaw/workspace/skills/stock-market-pro/scripts/stock_watchlist.json"

def load_history():
    """加载历史推荐数据"""
    if not os.path.exists(HISTORY_FILE):
        return {
            "history": [],
            "last_updated": None,
            "total_recommendations": 0
        }
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_history_entry(entry):
    """保存一条新推荐到历史"""
    history = load_history()
    
    # 添加唯一ID
    entry['id'] = len(history['history']) + 1
    history['history'].append(entry)
    history['last_updated'] = datetime.now().isoformat()
    history['total_recommendations'] = len(history['history'])
    
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def show_history(args):
    """显示历史推荐"""
    history = load_history()
    
    if not history['history']:
        print("还没有任何历史推荐记录")
        return
    
    print("=" * 90)
    print("历史推荐记录")
    print("=" * 90)
    print()
    
    filtered = history['history']
    
    # 根据参数筛选
    if args.ticker:
        filtered = [h for h in filtered if h['ticker'] == args.ticker.upper()]
        if not filtered:
            print(f"没有找到代码 {args.ticker} 的历史推荐")
            return
    if args.sector:
        filtered = [h for h in filtered if args.sector.lower() in h['sector'].lower()]
        if not filtered:
            print(f"没有找到板块 {args.sector} 的历史推荐")
            return
    if args.date:
        filtered = [h for h in filtered if args.date in h['date']]
        if not filtered:
            print(f"没有找到日期 {args.date} 的历史推荐")
            return
    
    # 按时间倒序排列，限制条数
    filtered = sorted(filtered, key=lambda x: x['timestamp'], reverse=True)
    if args.limit:
        filtered = filtered[:args.limit]
    
    print(f"找到 {len(filtered)} 条记录:\n")
    print("-" * 90)
    print(f"{'ID':<3} {'日期':<10} {'代码':<6} {'名称':<15} {'板块':<14} {'价格':>8} {'市值(B$)':>8} {'PE':>6}")
    print("-" * 90)
    
    for rec in filtered:
        mc = f"{rec['market_cap']/1e9:.1f}" if rec.get('market_cap') else "N/A"
        pe = f"{rec['pe_ratio']:.1f}" if rec.get('pe_ratio') else "N/A"
        cp = f"{rec['current_price']:>.2f}" if rec.get('current_price') else "N/A"
        print(f"{rec['id']:<3} {rec['date']:<10} {rec['ticker']:<6} {rec['name']:<15} {rec['sector']:<14} {cp:>8} {mc:>8} {pe:>6}")
    
    print("-" * 90)
    print(f"\n总共 {history['total_recommendations']} 条历史推荐，本次显示 {len(filtered)} 条")

def run_new_analysis():
    """运行新的分析并保存结果"""
    print("=" * 60)
    print("股票分析 - 5-10倍潜力股筛选 (带历史记录)")
    print("=" * 60)
    print()

    # 读取股票池
    with open(WATCHLIST_FILE, 'r') as f:
        watchlist = json.load(f)['watchlist']

    results = []
    today_date = datetime.now().strftime('%Y-%m-%d')

    for stock in watchlist:
        ticker = stock['ticker']
        name = stock['name']
        sector = stock['sector']
        notes = stock.get('notes', '')
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
                'notes': notes,
                'current_price': current_price,
                'change_percent': change_percent,
                'market_cap': market_cap,
                'pe_ratio': pe_ratio,
                'date': today_date,
                'timestamp': datetime.now().isoformat()
            }
            
            results.append(result)
            
            # 保存到历史数据库
            if current_price is not None:
                save_history_entry(result)
            
            mc_str = f"{market_cap/1e9:.1f}" if market_cap else "N/A"
            pe_str = f"{pe_ratio:.1f}" if pe_ratio else "N/A"
            if current_price:
                print(f"  ✓ 价格: ${current_price:.2f}  涨跌: {change_percent:.2f}%  市值: {mc_str}B  PE: {pe_str} [已存入历史]")
            else:
                print(f"  ✗ 未能获取价格")
        
        except Exception as e:
            print(f"  ✗ 错误: {e}")

    print()
    print("=" * 60)
    print(f"分析完成 - {len([r for r in results if r['current_price']])} 条结果存入历史数据库")
    print("=" * 60)

    # 保存每日结果文件 (保留原有功能)
    output_file = f"/home/admin/.openclaw/workspace/stock_analysis_{datetime.now().strftime('%Y%m%d')}.json"
    with open(output_file, 'w') as f:
        json.dump({
            'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'results': results
        }, f, indent=2)

    print(f"完整结果也已保存到: {output_file}")
    history = load_history()
    print(f"历史数据库累计: {history['total_recommendations']} 条推荐")

    # 打印汇总表格
    print()
    print("今日汇总:")
    print("-" * 85)
    print(f"{'代码':<6} {'名称':<15} {'板块':<16} {'价格':>10} {'涨跌%':>8} {'市值(B$)':>10} {'PE':>8}")
    print("-" * 85)
    for r in results:
        mc = f"{r['market_cap']/1e9:.1f}" if r.get('market_cap') else "N/A"
        pe = f"{r['pe_ratio']:.1f}" if r.get('pe_ratio') else "N/A"
        cp = f"{r['current_price']:>8.2f}" if r.get('current_price') else "N/A"
        chg = f"{r['change_percent']:>7.2f}" if r.get('current_price') else "N/A"
        print(f"{r['ticker']:<6} {r['name']:<15} {r['sector']:<16} {cp} {chg} {mc:>10} {pe:>8}")
    print("-" * 85)
    
    print()
    print("📋 查看历史推荐用法:")
    print("  python stock_analysis_with_history.py --history                 # 查看全部历史(最新在前)")
    print("  python stock_analysis_with_history.py --history --ticker NVDA   # 查看NVDA历史推荐")
    print("  python stock_analysis_with_history.py --history --sector AI      # 查看AI板块历史")
    print("  python stock_analysis_with_history.py --history --date 2026-04   # 查看2026年4月历史")
    print("  python stock_analysis_with_history.py --history --limit 10       # 只看最新10条")

def main():
    parser = argparse.ArgumentParser(description='股票分析工具 - 带历史推荐记录')
    parser.add_argument('--history', action='store_true', help='查看历史推荐而不是运行新分析')
    parser.add_argument('--ticker', help='按股票代码筛选历史')
    parser.add_argument('--sector', help='按板块筛选历史')
    parser.add_argument('--date', help='按日期筛选历史 (YYYY-MM格式)')
    parser.add_argument('--limit', type=int, default=50, help='限制显示条数 (默认50)')
    
    args = parser.parse_args()
    
    if args.history:
        show_history(args)
    else:
        run_new_analysis()

if __name__ == "__main__":
    main()
