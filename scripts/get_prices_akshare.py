#!/usr/bin/env python3
"""Get current prices using akshare"""
import akshare as ak
import time

stocks = [
    {"ticker": "NVDA", "name": "英伟达", "allocation": 1500},
    {"ticker": "TSM", "name": "台积电", "allocation": 1500},
    {"ticker": "PLTR", "name": "Palantir", "allocation": 1200},
    {"ticker": "AMD", "name": "超威半导体", "allocation": 1000},
    {"ticker": "LRCX", "name": "Lam Research", "allocation": 1000},
    {"ticker": "ASML", "name": "ASML", "allocation": 800},
    {"ticker": "AI", "name": "C3.ai", "allocation": 700},
    {"ticker": "SOUN", "name": "SoundHound", "allocation": 700},
    {"ticker": "VRTX", "name": "Vertex", "allocation": 600},
    {"ticker": "MRNA", "name": "Moderna", "allocation": 500},
    {"ticker": "MU", "name": "美光科技", "allocation": 500},
]

print("=" * 80)
print("📊 当前股价分析 - 入手机会评估")
print("=" * 80)
print()

try:
    print("获取实时报价...")
    df = ak.stock_us_spot_em()
    print(f"获取到 {len(df)} 只美股数据")
    print(df.columns.tolist())
except Exception as e:
    print(f"akshare 获取失败: {e}")
    print("尝试使用备用方法...")
    df = None

results = []
for stock in stocks:
    ticker = stock["ticker"]
    name = stock["name"]
    allocation = stock["allocation"]
    
    try:
        time.sleep(0.3)
        
        # Try akshare
        if df is not None:
            # Find the ticker in the dataframe
            ticker_col = [c for c in df.columns if '代码' in c or 'symbol' in c.lower()][0]
            price_col = [c for c in df.columns if '最新价' in c or 'price' in c.lower()][0]
            
            match = df[df[ticker_col].str.upper() == ticker.upper()]
            if not match.empty:
                current_price = float(match[price_col].values[0])
            else:
                print(f"⚠️ {ticker} 在akshare数据中未找到，尝试yfinance")
                raise ValueError("Not found in akshare")
        else:
            raise ValueError("akshare data not available")
        
        shares = allocation / current_price if current_price else 0
        
        # Try to get 52-week data
        high_52w = None
        low_52w = None
        try:
            info_df = ak.stock_us_hist(symbol=ticker, period="1y", adjust="qfq")
            if not info_df.empty:
                high_52w = float(info_df['最高'].max())
                low_52w = float(info_df['最低'].min())
        except:
            pass
        
        price_vs_high = ((current_price - high_52w) / high_52w * 100) if high_52w else -30
        price_vs_low = ((current_price - low_52w) / low_52w * 100) if low_52w else 0
        
        results.append({
            "ticker": ticker,
            "name": name,
            "price": current_price,
            "shares": shares,
            "allocation": allocation,
            "high_52w": high_52w,
            "low_52w": low_52w,
            "vs_high": price_vs_high,
            "vs_low": price_vs_low,
        })
        
        print(f"📈 {ticker} ({name})")
        print(f"   当前价格: ${current_price:.2f}")
        if high_52w and low_52w:
            print(f"   52周最高: ${high_52w:.2f} | 52周最低: ${low_52w:.2f}")
            print(f"   距52周高点: {price_vs_high:.1f}% | 距52周低点: {price_vs_low:.1f}%")
        print(f"   ✅ 可买入: {shares:.2f} 股 (投资 ${allocation})")
        
        if price_vs_high > -20:
            print(f"   🎯 入手机会: ⭐⭐⭐ 良好 (距高点<20%)")
        elif price_vs_high > -40:
            print(f"   🎯 入手机会: ⭐⭐⭐⭐ 优秀 (距高点20-40%)")
        else:
            print(f"   🎯 入手机会: ⭐⭐⭐⭐⭐ 极好 (接近底部)")
        print()
        
    except Exception as e:
        print(f"❌ {ticker} 获取失败: {e}")
        print()

print("=" * 80)
print("📊 投资总结")
print("=" * 80)
if results:
    total_invested = sum(r["allocation"] for r in results)
    print(f"计划总投资: ${total_invested:.2f}")
    print(f"实际可投资股票数: {len(results)} 只")
    print()
    print("| 代码 | 名称 | 当前价 | 可买股数 | 分配金额 | 距高点 | 入手机会 |")
    print("|------|------|--------|----------|----------|--------|----------|")
    for r in results:
        stars = "⭐" * 3 if r["vs_high"] > -20 else ("⭐" * 4 if r["vs_high"] > -40 else "⭐" * 5)
        print(f"| {r['ticker']} | {r['name']} | ${r['price']:.2f} | {r['shares']:.2f} | ${r['allocation']} | {r['vs_high']:.1f}% | {stars} |")
else:
    print("无法获取股票数据，请稍后重试")
