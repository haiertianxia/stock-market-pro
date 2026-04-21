---
name: stock-market-pro
description: >-
  Yahoo Finance (yfinance) powered stock analysis skill: quotes, fundamentals,
  ASCII trends, high-resolution charts (RSI/MACD/BB/VWAP/ATR), plus potential stock screener
  with persistent history tracking for 5-10x bagger hunting.
---

# Stock Market Pro

**Stock Market Pro** is a complete local-first stock research and potential 5-10x bagger screener toolkit.

Two main components:
1. **General Market Research Toolkit**: Get real-time quotes, fundamentals, ASCII charts, high-resolution PNG charts with technical indicators (RSI/MACD/BB/VWAP/ATR), news search
2. **US Stock Potential Screener**: Daily screening of your watchlist focused on high-growth sectors (AI/tech, semiconductor, biotech), with permanent history tracking of all recommendations to review over time

---

## 📖 Table of Contents

- [General Market Research Toolkit](#-general-market-research-toolkit)
  - [Quick Commands](#commands-local)
  - [Pro Charts with Indicators](#pro-chart-png)
  - [One-shot Reports](#one-shot-report)
  - [Web Add-ons (News / Options Flow)](#web-add-ons-optional)
- [5-10x Bagger Potential Screener](#-5-10x-potential-stock-screener)
  - [Overview](#overview)
  - [Daily Analysis with History Tracking](#run-daily-analysis)
  - [Query Historical Recommendations](#view-history-recommendations)
  - [Add Stocks to Watchlist](#add-new-stocks-to-watchlist)
  - [Configuration](#configuration-file)
- [Examples & Reference](#-examples--reference)
  - [Ticker Examples](#ticker-examples)
  - [Dependencies](#dependencies)

---

# 🔍 General Market Research Toolkit

Get clean price + fundamentals, generate publication-ready charts with indicator panels. No account required, powered by Yahoo Finance.

## What you can do
- Get **real-time quotes** (price + change)
- Summarize **fundamentals** (Market Cap, Forward PE, EPS, ROE)
- Print **ASCII trends** (terminal-friendly)
- Generate **high-resolution PNG charts** with overlays/panels:
  - RSI / MACD / Bollinger Bands / VWAP / ATR
- Run a **one-shot report** that prints a compact summary and emits a chart path
- Search **news links** via DuckDuckGo (ddgs)
- Open **options / flow pages** (browser-first, Unusual Whales)

---

## Commands (Local)

> This skill uses `uv run --script` for dependency handling.
> If you don't have `uv`: install from https://github.com/astral-sh/uv

### 1) Quotes
```bash
uv run --script scripts/yf.py price TSLA
# shorthand
uv run --script scripts/yf.py TSLA
```

### 2) Fundamentals
```bash
uv run --script scripts/yf.py fundamentals NVDA
```

### 3) ASCII trend
```bash
uv run --script scripts/yf.py history AAPL 6mo
```

### 4) Pro chart (PNG)
```bash
# candlestick (default)
uv run --script scripts/yf.py pro 000660.KS 6mo

# line chart
uv run --script scripts/yf.py pro 000660.KS 6mo line
```

#### Indicators (optional)
```bash
uv run --script scripts/yf.py pro TSLA 6mo --rsi --macd --bb
uv run --script scripts/yf.py pro TSLA 6mo --vwap --atr
```

- `--rsi` : RSI(14)
- `--macd`: MACD(12,26,9)
- `--bb`  : Bollinger Bands(20,2)
- `--vwap`: VWAP (cumulative over the selected range)
- `--atr` : ATR(14)

### 5) One-shot report
Prints a compact text summary and generates a chart PNG.

```bash
uv run --script scripts/yf.py report 000660.KS 6mo
# output includes: CHART_PATH:/tmp/<...>.png
```

> Optional web add-ons (news/options) can be appended by the agent workflow.

---

## Web Add-ons (Optional)

### A) News search (DuckDuckGo via `ddgs`)
This skill vendors a helper script (`scripts/ddg_search.py`).

Dependency:
```bash
pip3 install -U ddgs
```

Run:
```bash
python3 scripts/news.py NVDA --max 8
# or
python3 scripts/ddg_search.py "NVDA earnings guidance" --kind news --max 8 --out md
```

### B) Options / Flow (browser-first)
Unusual Whales frequently blocks scraping/headless access.
So the recommended approach is: **open the pages in a browser and summarize what you can see**.

Quick link helper:
```bash
python3 scripts/options_links.py NVDA
```

Common URLs:
- `https://unusualwhales.com/stock/{TICKER}/overview`
- `https://unusualwhales.com/live-options-flow?ticker_symbol={TICKER}`
- `https://unusualwhales.com/stock/{TICKER}/options-flow-history`

---

## Subcommands (yf.py)
`yf.py` supports:
- `price`
- `fundamentals`
- `history`
- `pro`
- `chart` (alias)
- `report`
- `option` (best-effort; browser fallback recommended)

Check:
```bash
python3 scripts/yf.py --help
```

---

# 🚀 5-10x Potential Stock Screener

## Overview

This is a purpose-built screener for finding multi-bagger growth stocks. It's focused on three high-growth sectors:
- **AI & Technology**
- **Semiconductors**  
- **Biotechnology**

Key features:
- ✅ Daily updates of price/valuation data for your watchlist
- ✅ **Permanent history storage** - every recommendation is saved forever
- ✅ Flexible querying - filter by ticker, sector, or date
- ✅ Summary tables printed directly to terminal
- ✅ Auto-saves daily snapshots in addition to the central history

The screener uses AkShare for US market data and automatically stores every valid result in a searchable history database.

---

## Configuration File

The watchlist is configured in `scripts/stock_watchlist.json`: it contains:
- List of stocks (ticker, name, sector, notes)
- Analysis rules (what to look for, sectors to cover)
- Scheduling (pre-market / after-close times in Asia/Shanghai)

Example stock entry:
```json
{
  "ticker": "NVDA",
  "name": "英伟达",
  "sector": "AI/半导体",
  "notes": "AI GPU 龙头"
}
```

---

## Run Daily Analysis

### Quick direct analysis (for small watchlists):
```bash
python3 scripts/stock_analysis_with_history.py
```

This will:
1. Fetch current price and fundamentals for every stock in your watchlist
2. Print a summary table to the terminal
3. Automatically save **every** valid result to the history database
4. Save a full daily snapshot to `../../stock_analysis_YYYYMMDD.json`

### With rate limiting (for larger watchlists):
If you get rate-limited by AkShare, use the delayed version:
```bash
python3 scripts/stock_update_with_delay.py
```
This adds 30 seconds between requests to avoid being blocked.

### Alternative: Alpha Vantage API (more reliable)
Get a free API key from [Alpha Vantage](https://www.alphavantage.co/), then:
```bash
# Edit ALPHA_KEY in the script
python3 scripts/stock_update_alpha_vantage.py
```
Free tier: 5 requests/minute, 500 requests/day - enough for daily updates.

---

## View History Recommendations

Once you've run analysis, you can query the history database anytime:

### Basic Commands

```bash
# Show all historical recommendations (newest first, max 50)
python3 scripts/stock_analysis_with_history.py --history

# Show only the last 10 recommendations
python3 scripts/stock_analysis_with_history.py --history --limit 10

# Filter by ticker - show all historical entries for a specific stock
python3 scripts/stock_analysis_with_history.py --history --ticker NVDA

# Filter by sector - show all AI/tech sector recommendations
python3 scripts/stock_analysis_with_history.py --history --sector "AI"

# Filter by month - show all recommendations from April 2026
python3 scripts/stock_analysis_with_history.py --history --date 2026-04

# Combine filters - show last 5 semiconductor stocks
python3 scripts/stock_analysis_with_history.py --history --sector semiconductor --limit 5
```

### Output format
History output is a clean formatted table:
```
ID 日期       代码   名称            板块           价格   市值(B$)     PE
--- ---------- ------ --------------- -------------- -------- -------- ------
 1 2026-04-18 NVDA   英伟达          AI/半导体      800.00   2000.0  35.0
 ...
```

### History Database
All recommendations are stored in `scripts/stock_recommendation_history.json`:
```json
{
  "history": [...],
  "last_updated": "2026-04-20T12:34:56",
  "total_recommendations": 42
}
```

This file is compatible with git so you can version-control your recommendation history.

---

## Add New Stocks to Watchlist

Use the interactive helper:
```bash
python3 scripts/add_stocks.py
```

It will prompt you for:
1. Ticker symbol
2. Chinese/English name  
3. Sector
4. Brief notes

Then appends the new stock directly to `stock_watchlist.json`.

---

## Migrate Old Data

If you have existing daily JSON files from before the history feature was added, migrate them to the new database:
```bash
python3 scripts/migrate_existing_to_history.py
```

---

# 📌 Examples & Reference

## Ticker examples
- US: `AAPL`, `NVDA`, `TSLA`
- KR: `005930.KS`, `000660.KS`
- Crypto: `BTC-USD`, `ETH-KRW`
- FX: `USDKRW=X`

## Dependencies

Core (always required):
```bash
pip install yfinance pandas matplotlib mplfinance
```

For the screener:
```bash
pip install akshare
```

For news search:
```bash
pip install ddgs
```

This project uses `uv` for script dependency management where applicable: https://github.com/astral-sh/uv

## Scheduling

For daily automatic updates, you can schedule via cron:
```
# Pre-market: 20:40 Beijing time (US pre-market)
40 20 * * * cd /home/admin/.openclaw/workspace/skills/stock-market-pro && python3 scripts/stock_analysis_with_history.py >> /tmp/stock-screener.log 2>&1

# After-close: 05:10 Beijing time (US after-close)
10 05 * * * cd /home/admin/.openclaw/workspace/skills/stock-market-pro && python3 scripts/stock_analysis_with_history.py >> /tmp/stock-screener.log 2>&1
```

## File Structure

```
stock-market-pro/
├── SKILL.md                      # This documentation
├── main.py                       # Skill entrypoint
├── scripts/
│   ├── yf.py                     # Main YFinance toolkit
│   ├── stock_analysis_with_history.py  # ✨ NEW: Full analysis with history tracking
│   ├── stock_analysis_direct.py        # Direct analysis (no history)
│   ├── stock_analysis.py               # Original analysis
│   ├── stock_update_with_delay.py      # Delayed rate-limited update
│   ├── stock_update_alpha_vantage.py   # Alpha Vantage API update
│   ├── stock_get_fundamentals.py       # Get fundamentals standalone
│   ├── add_stocks.py                   # Interactive add to watchlist
│   ├── migrate_existing_to_history.py  # Migrate old data to history DB
│   ├── stock_watchlist.json            # Watchlist configuration
│   ├── stock_recommendation_history.json  # History database
│   ├── ddg_search.py                   # DuckDuckGo search
│   ├── news.py                        # News search for tickers
│   ├── options_links.py               # Generate Unusual Whales links
│   └── test_*.py                      # Various test scripts
└── ...
```
