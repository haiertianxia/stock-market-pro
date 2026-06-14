#!/usr/bin/env python3
"""
Price Alert System — Monitor stock movements and notify via WeChat (PushPlus)

Detects:
- Daily change > ±3% (significant move)
- Cumulative change > ±10% from first track
- Crossed key price levels (round numbers)

Tracks sent alerts to avoid duplicate notifications.
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(SCRIPT_DIR, "stock_recommendation_history.json")
ALERT_STATE_FILE = os.path.join(SCRIPT_DIR, "alert_state.json")

PUSHPLUS_TOKEN = os.environ.get("PUSHPLUS_TOKEN", "")
PUSH_ENABLED = os.environ.get("PUSH_ENABLED", "0") == "1"
PUSHPLUS_URL = "https://www.pushplus.plus/send"

# Alert thresholds
DAILY_CHANGE_THRESHOLD = 3.0     # %
CUMULATIVE_CHANGE_THRESHOLD = 10.0  # %


def load_history() -> Dict:
    if not os.path.exists(HISTORY_FILE):
        return {"history": [], "total_recommendations": 0}
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_alert_state() -> Dict:
    """Load sent alerts to avoid duplicates."""
    if not os.path.exists(ALERT_STATE_FILE):
        return {"sent_alerts": []}
    try:
        with open(ALERT_STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"sent_alerts": []}


def save_alert_state(state: Dict):
    with open(ALERT_STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def alert_already_sent(ticker: str, alert_type: str) -> bool:
    """Check if this alert was already sent recently (within 24h)."""
    state = load_alert_state()
    cutoff = datetime.now() - timedelta(hours=24)
    
    for alert in state.get("sent_alerts", []):
        if alert["ticker"] == ticker and alert["type"] == alert_type:
            try:
                alert_time = datetime.fromisoformat(alert["timestamp"])
                if alert_time > cutoff:
                    return True
            except:
                pass
    return False


def mark_alert_sent(ticker: str, alert_type: str, message: str):
    """Record that an alert was sent."""
    state = load_alert_state()
    state["sent_alerts"].append({
        "ticker": ticker,
        "type": alert_type,
        "message": message[:200],
        "timestamp": datetime.now().isoformat()
    })
    # Keep last 100 alerts
    state["sent_alerts"] = state["sent_alerts"][-100:]
    save_alert_state(state)


def pushplus_send(title: str, content: str) -> bool:
    """Send PushPlus WeChat notification."""
    if not PUSH_ENABLED or not PUSHPLUS_TOKEN:
        print(f"  PushPlus disabled (ENABLED={PUSH_ENABLED}, TOKEN={bool(PUSHPLUS_TOKEN)})")
        return False
    try:
        r = requests.get(PUSHPLUS_URL, params={
            "token": PUSHPLUS_TOKEN,
            "title": title,
            "content": content,
            "template": "html",
        }, timeout=10)
        return r.status_code == 200 and "200" in r.text
    except Exception as e:
        print(f"  PushPlus error: {e}")
        return False


def analyze_alerts() -> List[Dict]:
    """Analyze recommendation history for price alerts."""
    history = load_history()
    records = history.get("history", [])
    
    if not records:
        return []
    
    # Group by ticker, keep latest 2 entries for each
    ticker_records: Dict[str, List[Dict]] = {}
    for rec in records:
        t = rec.get("ticker", "")
        if t not in ticker_records:
            ticker_records[t] = []
        ticker_records[t].append(rec)
    
    alerts = []
    
    for ticker, recs in ticker_records.items():
        recs.sort(key=lambda x: x.get("timestamp", ""))
        name = recs[-1].get("name", ticker)
        sector = recs[-1].get("sector", "")
        notes = recs[-1].get("notes", "")
        emoji = "🤖" if "AI" in sector else ("💾" if "半" in sector else "💊")
        
        # Check for daily change (latest 2 records)
        if len(recs) >= 2:
            latest = recs[-1]
            prev = recs[-2]
            
            l_price = latest.get("current_price") or latest.get("price")
            p_price = prev.get("current_price") or prev.get("price")
            
            if l_price and p_price and p_price > 0:
                change_pct = abs((l_price - p_price) / p_price * 100)
                
                # Check if we have a new record from today
                today = datetime.now().strftime("%Y-%m-%d")
                if latest.get("date") == today:
                    # Significant daily move
                    if change_pct >= DAILY_CHANGE_THRESHOLD:
                        direction = "📈 上涨" if l_price > p_price else "📉 下跌"
                        alert_key = f"daily_{change_pct:.0f}"
                        
                        if not alert_already_sent(ticker, alert_key):
                            alerts.append({
                                "ticker": ticker,
                                "name": name,
                                "sector": sector,
                                "emoji": emoji,
                                "type": "daily",
                                "severity": "warning" if change_pct >= 6 else "info",
                                "title": f"{emoji} {ticker} {direction} {change_pct:.1f}%",
                                "message": (
                                    f"{emoji} <b>{ticker} - {name}</b><br>"
                                    f"{direction} <b>{change_pct:.1f}%</b><br>"
                                    f"昨收: ${p_price:.2f} → 现价: ${l_price:.2f}<br>"
                                    f"板块: {sector}<br>"
                                    f"{'📝 ' + notes if notes else ''}"
                                ),
                                "alert_key": alert_key
                            })
                
                # Check cumulative change from first record
                first = recs[0]
                f_price = first.get("current_price") or first.get("price")
                if l_price and f_price and f_price > 0:
                    cum_change = abs((l_price - f_price) / f_price * 100)
                    if cum_change >= CUMULATIVE_CHANGE_THRESHOLD:
                        alert_key = f"cumulative_{cum_change:.0f}"
                        
                        if not alert_already_sent(ticker, alert_key):
                            direction = "🚀 暴涨" if l_price > f_price else "💀 暴跌"
                            alerts.append({
                                "ticker": ticker,
                                "name": name,
                                "sector": sector,
                                "emoji": emoji,
                                "type": "cumulative",
                                "severity": "danger" if cum_change >= 20 else "warning",
                                "title": f"{emoji} {ticker} 累计{direction} {cum_change:.1f}%",
                                "message": (
                                    f"{emoji} <b>{ticker} - {name}</b><br>"
                                    f"累计{direction} <b>{cum_change:.1f}%</b><br>"
                                    f"首日({first.get('date', '?')}): ${f_price:.2f}<br>"
                                    f"当前价格: ${l_price:.2f}<br>"
                                    f"追踪天数: {len(recs)} 次<br>"
                                    f"板块: {sector}"
                                ),
                                "alert_key": alert_key
                            })
        
        # Check for price crossing round numbers
        latest = recs[-1]
        l_price = latest.get("current_price") or latest.get("price")
        if l_price:
            for level in [10, 20, 50, 100, 200, 500, 1000]:
                # Check if close to a round number
                dist = abs(l_price - level)
                if dist < l_price * 0.03:  # within 3%
                    alert_key = f"level_{level}"
                    if not alert_already_sent(ticker, alert_key):
                        direction = "突破" if l_price > level else "跌破"
                        alerts.append({
                            "ticker": ticker,
                            "name": name,
                            "emoji": emoji,
                            "type": "level",
                            "severity": "info",
                            "title": f"{emoji} {ticker} {direction} ${level}",
                            "message": (
                                f"{emoji} <b>{ticker} - {name}</b><br>"
                                f"{direction} <b>${level}</b> 关口<br>"
                                f"当前价格: ${l_price:.2f}<br>"
                                f"板块: {sector}"
                            ),
                            "alert_key": alert_key
                        })
    
    return alerts


def main():
    print(f"🔍 价格警报检查 @ {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    alerts = analyze_alerts()
    
    if not alerts:
        print("✓ 无警报触发")
        return 0
    
    print(f"\n⚠️  发现 {len(alerts)} 个警报:\n")
    
    sent_count = 0
    for alert in alerts:
        print(f"  {alert['title']}")
        print(f"    ↓ {alert['message'][:80]}...")
        
        if PUSH_ENABLED:
            ok = pushplus_send(alert['title'], alert['message'])
            if ok:
                mark_alert_sent(alert['ticker'], alert['alert_key'], alert['message'])
                sent_count += 1
                print(f"    ✅ 已发送微信通知")
            else:
                print(f"    ❌ 发送失败")
        else:
            print(f"    💤 推送未开启 (PUSH_ENABLED=0)")
    
    print(f"\n📊 总计: {len(alerts)} 个警报, {sent_count} 条微信通知已发送")
    return 0


if __name__ == "__main__":
    sys.exit(main())
