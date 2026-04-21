
import yfinance as yf

ticker = yf.Ticker("TSLA")
print("Testing yfinance...")
info = ticker.info
print(f"Got info, keys: {list(info.keys())[:20]}")
print(f"RegularMarketPrice: {info.get('regularMarketPrice')}")
print(f"CurrentPrice: {info.get('currentPrice')}")
print(f"ShortName: {info.get('shortName')}")
