
#!/usr/bin/env python3
import akshare as ak
df = ak.stock_financial_us_analysis_indicator_em(symbol="NVDA")
print(df.head())
print("\nColumns:", df.columns.tolist())
