#!/usr/bin/env python3
import yfinance as yf
import time
import sys

tickers = ["NVDA", "TSM", "PLTR", "AMD", "LRCX", "ASML", "AI", "SOUN", "VRTX", "MRNA", "MU"]

results = {}
for i, ticker in enumerate(tickers):
    try:
        t = yf.Ticker(ticker)
        info = t.info
        price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose')
        high52 = info.get('fiftyTwoWeekHigh')
        low52 = info.get('fiftyTwoWeekLow')
        change = info.get('regularMarketChangePercent', 0)
        cap = info.get('marketCap', 0)
        pe = info.get('trailingPE')
        
        results[ticker] = {
            'price': price,
            'high52': high52,
            'low52': low52,
            'change': change,
            'cap': cap,
            'pe': pe
        }
        
        vs_high = ((price - high52) / high52 * 100) if high52 else 0
        
        print(f"✅ {ticker}: ${price:.2f} (今日{change:+.2f}%) | 距高点: {vs_high:.1f}%")
        
    except Exception as e:
        print(f"❌ {ticker}: {e}")
        results[ticker] = None
    
    if i < len(tickers) - 1:
        time.sleep(2)

print("\n" + "="*60)
print("SUMMARY:")
for ticker, r in results.items():
    if r:
        vs_high = ((r['price'] - r['high52']) / r['high52'] * 100) if r['high52'] else 0
        cap_b = r['cap'] / 1e9 if r['cap'] else 0
        print(f"{ticker}: ${r['price']:.2f} | 52W High: ${r['high52']:.2f} | vs High: {vs_high:.1f}% | MCap: ${cap_b:.1f}B | PE: {r['pe']}")
