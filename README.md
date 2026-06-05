# 美股潜力股分析工具

每日盘前盘后自动更新股票池价格和基本面数据，筛选 5-10 倍潜力股。

聚焦三大赛道：AI/科技、半导体、生物医药。

## 文件说明

| 脚本 | 功能 | 说明 |
|------|------|------|
| `stock_analysis_with_history.py` | 完整分析 + 历史推荐存储 | **推荐使用** - 每次运行自动保存推荐到历史库，支持查看历史 |
| `stock_analysis_direct.py` | 直接获取所有股票数据 | AkShare 直接拉取，适合股票少的情况 |
| `stock_update_with_delay.py` | 带延迟更新避免限流 | 每只股票间隔 30 秒，防止被封 |
| `stock_update_alpha_vantage.py` | Alpha Vantage API 更新 | 更稳定，需要免费 API key |
| `add_stocks.py` | 添加新股到观察池 | 交互式添加 |
| `stock_get_fundamentals.py` | 单独获取基本面 | 市值、PE 等数据 |
| `migrate_existing_to_history.py` | 迁移旧数据 | 将旧的每日文件导入历史数据库 |
| `stock_recommendation_history.json` | 历史推荐数据库 | 永久存储所有推荐记录 |
| `stock_watchlist.json` | 观察池配置 | 包含股票列表、分析规则、定时设置 |

## 使用方法

### 1. 直接更新（快速，适合少量股票）

```bash
python3 stock_analysis_direct.py
```

输出会打印汇总表，并保存结果到 `stock_analysis_YYYYMMDD.json`。

### 2. 带延迟更新（避免限流，适合完整股票池）

```bash
python3 stock_update_with_delay.py
```

每只股票间隔 30 秒，遵守 AkShare 限流规则。

### 3. Alpha Vantage API 更新（更稳定）

1. 去 [Alpha Vantage](https://www.alphavantage.co/) 注册免费 API key
2. 在 `stock_update_alpha_vantage.py` 中修改 `ALPHA_KEY` 为你的 key
3. 运行：

```bash
python3 stock_update_alpha_vantage.py
```

免费额度：5 请求/分钟，500 请求/天，足够每日更新。

### 4. 添加新股

```bash
python3 add_stocks.py
```

按提示输入股票代码、名称、板块、备注即可。

### 5. 查看历史推荐

使用 `stock_analysis_with_history.py` 的 `--history` 模式查询历史推荐:

```bash
# 查看所有历史推荐（最新在前，默认最多50条）
python3 stock_analysis_with_history.py --history

# 查看特定股票的历史推荐
python3 stock_analysis_with_history.py --history --ticker NVDA

# 查看特定板块的历史推荐
python3 stock_analysis_with_history.py --history --sector "AI"

# 查看特定月份的推荐
python3 stock_analysis_with_history.py --history --date 2026-04

# 只看最新10条
python3 stock_analysis_with_history.py --history --limit 10
```

每次运行新分析都会自动将成功获取价格的股票存入历史数据库 `stock_recommendation_history.json`，永久保存方便追踪。

## 输出格式

结果保存为 JSON：

```json
{
  "date": "2026-04-18 16:30",
  "results": [
    {
      "ticker": "NVDA",
      "name": "英伟达",
      "sector": "AI/半导体",
      "current_price": 800.00,
      "change_percent": 2.5,
      "market_cap": 2000000000000,
      "pe_ratio": 35.0,
      "timestamp": "2026-04-18T16:30:00"
    }
  ]
}
```

## 当前观察池

共 **22** 只股票，分布：
- AI/科技: 7 只
- 半导体: 6 只
- 生物医药: 7 只

详见 `stock_watchlist.json`。

## 定时计划

- **盘前**：北京时间 20:40（美股开盘前）更新
- **盘后**：北京时间 05:10（美股收盘后）更新

## 优化记录

2026-04-20:
- ✨ 新增历史推荐存储功能 `stock_analysis_with_history.py`
- 📋 永久保存每次推荐到中央数据库
- 🔍 支持按代码、板块、日期筛选查询历史
- 📊 自动迁移旧数据

2026-04-18:
- 拆分单文件为多个功能模块
- 增加限流处理（延迟请求）
- 增加备用数据源 Alpha Vantage
- 改进错误处理，单股票失败不影响整体
- 标准化 JSON 输出格式
- 添加本文档

---

## 📈 投资组合建议 ($10,000)

### 当前推荐股票

| 股票 | 代码 | 估算价格 | 仓位 | 投资逻辑 |
|------|------|---------|------|---------|
| 英伟达 | NVDA | ~$202 | 15% | AI GPU绝对龙头，长期持有 |
| 台积电 | TSM | ~$366 | 15% | AI芯片代工垄断，估值合理 |
| Palantir | PLTR | ~$65 | 12% | AI+大数据国防，订单增长 |
| 超威半导体 | AMD | ~$165 | 10% | MI300放量，竞争加剧 |
| Lam Research | LRCX | ~$720 | 10% | 半导体设备龙头 |
| ASML | ASML | ~$680 | 8% | 光刻机垄断，不可替代 |
| C3.ai | AI | ~$25 | 7% | 企业AI软件，估值低 |
| SoundHound | SOUN | ~$5 | 7% | 语音AI，高潜力 |
| Vertex | VRTX | ~$390 | 6% | 基因编辑稳健 |
| Moderna | MRNA | ~$55 | 5% | 疫苗+癌症，低估值 |
| 美光科技 | MU | ~$70 | 5% | 存储周期底部 |

### 投资策略
- 聚焦高增长赛道：AI/科技、半导体、生物医药
- 寻找5-10倍潜力股
- 严格止损，分散持仓
- 每日自动分析并推送推荐到微信

### 注意事项
- 价格数据需在券商App确认
- 建议分批建仓
- 长期持有为主
