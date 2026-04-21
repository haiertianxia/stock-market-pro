#!/usr/bin/env python3
"""
Daily Stock Analysis and Send Recommendation via OpenClaw
Runs the full analysis, saves to history, formats the output, and sends to your WeChat
"""

import os
import sys
import json
import argparse
import subprocess
from datetime import datetime
from typing import List, Dict

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stock_analysis_with_history import run_full_analysis, load_watchlist, get_history

def format_recommendations(recommendations: List[Dict], limit: int = 10) -> str:
    """Format recommendations for markdown output"""
    if not recommendations:
        return "今日没有新的推荐股票。"
    
    # Sort by market cap ascending (smaller = more potential upside)
    sorted_recs = sorted(recommendations, key=lambda x: x.get("market_cap", 9999))
    
    output = f"# 📊 每日股票推荐分析 - {datetime.now().strftime('%Y-%m-%d')}\n\n"
    output += "## 🎯 今日推荐 (按市值从小到大排序):\n\n"
    output += "| 日期 | 代码 | 名称 | 板块 | 价格 | 市值(十亿美元) | PE |\n"
    output += "|------|------|------|------|------|--------------|----|\n"
    
    for rec in sorted_recs[-limit:]:
        date = rec.get("date", datetime.now().strftime("%Y-%m-%d"))
        ticker = rec.get("ticker", "")
        name = rec.get("name", "")
        sector = rec.get("sector", "")
        price = f"{rec.get('price', 0):.2f}" if rec.get("price") else "-"
        cap = f"{rec.get('market_cap', 0):.2f}" if rec.get("market_cap") else "-"
        pe = f"{rec.get('pe', 0):.2f}" if rec.get("pe") else "-"
        output += f"| {date} | {ticker} | {name} | {sector} | {price} | {cap} | {pe} |\n"
    
    # Add analysis rules reminder
    output += "\n## ⚖️ 分析规则:\n"
    output += "- 寻找 5-10 倍潜力股\n"
    output += "- 聚焦: AI/科技, 半导体, 生物医药\n"
    output += "- 提供买入/卖出建议和止损位\n"
    
    output += f"\n🔗 **查看完整历史**: [Web Interface](http://your-server:8765/)\n"
    
    return output

def send_via_openclaw(message: str):
    """Send message via openclaw to your configured channel"""
    # This assumes openclaw is already installed and configured
    # The message will be delivered to your WeChat via the configured channel
    try:
        # Write to temp file and send via openclaw
        with open("/tmp/daily_stock_recommendation.md", "w", encoding="utf-8") as f:
            f.write(message)
        
        # Use openclaw to send (depends on your configuration)
        # For direct chat with your user:
        result = subprocess.run(
            ["openclaw", "message", "send", "--file", "/tmp/daily_stock_recommendation.md"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✓ Message sent successfully via OpenClaw")
        else:
            print(f"⚠ Failed to send via OpenClaw: {result.stderr}")
    except Exception as e:
        print(f"⚠ Error sending message: {e}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--send", action="store_true", help="Send recommendation via OpenClaw")
    parser.add_argument("--limit", type=int, default=10, help="Number of recommendations to show")
    args = parser.parse_args()
    
    print(f"🚀 Starting daily analysis at {datetime.now()}")
    
    # Run the full analysis
    try:
        recommendations = run_full_analysis(save_to_history=True)
        print(f"✓ Completed analysis, {len(recommendations)} recommendations generated")
        
        # Get the full history
        history = get_history()
        print(f"✓ Total recommendations in history: {history.get('total_recommendations', 0)}")
        
        # Format output
        markdown = format_recommendations(recommendations, args.limit)
        
        # Print to console
        print("\n" + "="*60)
        print(markdown)
        print("="*60 + "\n")
        
        # Send via OpenClaw if requested
        if args.send:
            send_via_openclaw(markdown)
        
        # Save today's snapshot
        today = datetime.now().strftime("%Y%m%d")
        snapshot_file = f"stock_analysis_{today}.json"
        with open(snapshot_file, "w", encoding="utf-8") as f:
            json.dump(recommendations, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved today's snapshot to {snapshot_file}")
        
        return 0
    except Exception as e:
        print(f"✗ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
