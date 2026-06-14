#!/usr/bin/env python3
"""
Daily Stock Analysis and Send Recommendation via WeChat (PushPlus)
Runs the full analysis, saves to history, formats the output, and sends to WeChat.
"""

import os
import sys
import json
import argparse
import requests
from datetime import datetime
from typing import List, Dict

# Resolve paths relative to this script's location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

from stock_analysis_with_history import load_history, save_history_entry

PUSHPLUS_TOKEN = os.environ.get("PUSHPLUS_TOKEN", "")
PUSH_ENABLED = os.environ.get("PUSH_ENABLED", "0") == "1"
PUSHPLUS_URL = "https://www.pushplus.plus/send"


def pushplus_send(title: str, content: str) -> bool:
    """Send message via PushPlus to WeChat. Returns True on success."""
    if not PUSH_ENABLED or not PUSHPLUS_TOKEN:
        print(f"  PushPlus not enabled (PUSH_ENABLED={PUSH_ENABLED}, token set={bool(PUSHPLUS_TOKEN)})")
        return False
    try:
        r = requests.get(PUSHPLUS_URL, params={
            "token": PUSHPLUS_TOKEN,
            "title": title,
            "content": content,
            "template": "html",
        }, timeout=10)
        if r.status_code == 200 and "200" in r.text:
            print(f"  ✓ PushPlus notification sent: {title}")
            return True
        else:
            print(f"  ✗ PushPlus failed: {r.text[:100]}")
            return False
    except Exception as e:
        print(f"  ✗ PushPlus error: {e}")
        return False


def load_watchlist():
    """Load the stock watchlist."""
    path = os.path.join(SCRIPT_DIR, "stock_watchlist.json")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)["watchlist"]


def run_analysis_and_get_results() -> List[Dict]:
    """Run analysis for all stocks in watchlist, return results."""
    import akshare as ak

    watchlist = load_watchlist()
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
            change_percent = 0.0
            market_cap = None
            pe_ratio = None

            ak_symbol = f"105.{ticker}"

            # Get latest price from historical data
            try:
                hist = ak.stock_us_hist(symbol=ak_symbol, period="daily", adjust="")
                if not hist.empty:
                    latest = hist.iloc[-1]
                    prev = hist.iloc[-2] if len(hist) >= 2 else latest
                    current_price = float(latest['收盘'])
                    prev_close = float(prev['收盘'])
                    change_percent = (current_price - prev_close) / prev_close * 100
            except Exception as e:
                print(f"  获取历史数据失败: {e}")

            # Get fundamental data
            try:
                valuation = ak.stock_us_valuation_baidu(symbol=ticker)
                if not valuation.empty:
                    for _, row in valuation.iterrows():
                        item = str(row['item']).lower()
                        value = str(row['value'])
                        if 'market cap' in item or '市值' in item:
                            try:
                                if 'B' in value:
                                    market_cap = float(value.replace('$', '').replace('B', '').replace(',', '').strip()) * 1e9
                                elif 'T' in value:
                                    market_cap = float(value.replace('$', '').replace('T', '').replace(',', '').strip()) * 1e12
                                elif 'M' in value:
                                    market_cap = float(value.replace('$', '').replace('M', '').replace(',', '').strip()) * 1e6
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

            # Save to history
            if current_price is not None:
                save_history_entry(result)

            mc_str = f"{market_cap/1e9:.1f}" if market_cap else "N/A"
            pe_str = f"{pe_ratio:.1f}" if pe_ratio else "N/A"
            if current_price:
                print(f"  ✓ ${current_price:.2f}  {change_percent:+.2f}%  市值: {mc_str}B  PE: {pe_str}")
            else:
                print(f"  ✗ 未能获取价格")

        except Exception as e:
            print(f"  ✗ 错误: {e}")

    return results


def format_recommendations_for_wechat(results: List[Dict]) -> str:
    """Format as HTML for PushPlus/WeChat."""
    if not results:
        return "<p>今日没有获取到数据。</p>"

    sorted_recs = sorted(results, key=lambda x: x.get('market_cap', 9999))

    html = f"""
<h1>📊 每日股票推荐 - {datetime.now().strftime('%Y-%m-%d')}</h1>
<h2>🎯 今日推荐 (按市值升序，小市值优先)</h2>
<table border='1' cellpadding='8' cellspacing='0' style='border-collapse:collapse;width:100%'>
<tr style='background:#f0f0f0'>
    <th>代码</th><th>名称</th><th>板块</th><th>价格</th><th>涨跌幅</th><th>市值(B$)</th><th>PE</th>
</tr>
"""

    for rec in sorted_recs:
        price = f"${rec.get('current_price', 0):.2f}" if rec.get('current_price') else "N/A"
        change = rec.get('change_percent', 0)
        change_str = f"{change:+.2f}%" if rec else "N/A"
        change_color = "#d32f2f" if change > 0 else "#1976d2" if change < 0 else "#333"
        mc = f"{rec.get('market_cap', 0)/1e9:.1f}" if rec.get('market_cap') else "N/A"
        pe = f"{rec.get('pe_ratio', 0):.1f}" if rec.get('pe_ratio') else "N/A"
        sector_emoji = "🤖" if "AI" in rec.get('sector', '') else "💾" if "半" in rec.get('sector', '') else "💊"

        html += f"""<tr>
    <td><b>{rec['ticker']}</b></td>
    <td>{rec['name']}</td>
    <td>{sector_emoji} {rec['sector']}</td>
    <td>{price}</td>
    <td style='color:{change_color};font-weight:bold'>{change_str}</td>
    <td>{mc}</td>
    <td>{pe}</td>
</tr>"""
        # notes
        if rec.get('notes'):
            html += f"""<tr><td colspan='7' style='background:#fafafa;font-size:12px;color:#666'>📝 {rec['notes']}</td></tr>"""

    html += "</table>"

    # Stats summary
    valid = [r for r in results if r.get('current_price')]
    gainers = [r for r in valid if r.get('change_percent', 0) > 0]
    losers = [r for r in valid if r.get('change_percent', 0) < 0]

    html += f"""
<h2>📈 市场概况</h2>
<p>监控股票: {len(valid)}/{len(results)} 只获取到价格 | 上涨: {len(gainers)} | 下跌: {len(losers)}</p>
<h2>⚖️ 分析规则</h2>
<ul>
    <li>寻找 5-10 倍潜力股</li>
    <li>聚焦: AI/科技, 半导体, 生物医药</li>
    <li>小市值优先（更大上涨空间）</li>
</ul>
<p style='color:#999;font-size:12px'>🕐 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
"""

    return html


def main():
    parser = argparse.ArgumentParser(description='每日股票分析 + WeChat 推送')
    parser.add_argument("--send", action="store_true", help="发送 PushPlus 微信通知")
    parser.add_argument("--dry-run", action="store_true", help="仅打印，不保存到历史")
    args = parser.parse_args()

    print(f"🚀 每日股票分析开始 {datetime.now()}")

    # Run analysis
    try:
        results = run_analysis_and_get_results()
    except Exception as e:
        print(f"✗ 分析失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

    valid = [r for r in results if r.get('current_price')]
    print(f"\n✓ 分析完成: {len(valid)}/{len(results)} 只股票获取到数据")

    # Load history for stats
    history = load_history()
    print(f"✓ 历史累计: {history.get('total_recommendations', 0)} 条记录")

    # Save snapshot
    snapshot = os.path.join(SCRIPT_DIR, f"stock_analysis_{datetime.now().strftime('%Y%m%d')}.json")
    with open(snapshot, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"✓ 快照已保存: {snapshot}")

    # Print summary table
    print(f"\n{'代码':<6} {'名称':<14} {'板块':<14} {'价格':>10} {'涨跌%':>8} {'市值(B$)':>10} {'PE':>8}")
    print("-" * 80)
    for r in sorted(results, key=lambda x: x.get('market_cap', 9999)):
        mc = f"{r.get('market_cap', 0)/1e9:.1f}" if r.get('market_cap') else "N/A"
        pe = f"{r.get('pe_ratio', 0):.1f}" if r.get('pe_ratio') else "N/A"
        cp = f"${r.get('current_price', 0):.2f}" if r.get('current_price') else "N/A"
        chg = f"{r.get('change_percent', 0):+.2f}%" if r.get('current_price') else "N/A"
        print(f"{r['ticker']:<6} {r['name']:<14} {r['sector']:<14} {cp:>10} {chg:>8} {mc:>10} {pe:>8}")

    # Send WeChat notification
    if args.send:
        print("\n📱 正在发送微信通知...")
        html = format_recommendations_for_wechat(results)
        title = f"📊 每日股票推荐 {datetime.now().strftime('%m-%d')}"
        ok = pushplus_send(title, html)
        if ok:
            print("✓ 微信通知发送成功")
        else:
            print("⚠ 微信通知发送失败（请检查 PUSHPLUS_TOKEN）")

    return 0


if __name__ == "__main__":
    sys.exit(main())