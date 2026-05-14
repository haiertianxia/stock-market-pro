# 美股潜力股分析工具 — 架构设计

版本：v1.0 | 日期：2026-05-14 | Mermaid 图表

---

## 一、项目概述

美股潜力股分析工具，每日盘前盘后自动更新股票池价格和基本面数据，筛选 5-10 倍潜力股。聚焦三大赛道：AI/科技、半导体、生物医药。

---

## 二、系统架构

```mermaid
C4Container
    Person(user, "投资者")
    System_Boundary(s, "美股分析工具") {
        Container(web, "Web UI", "Python", "Flask/FastAPI")
        Container(core, "核心分析引擎", "Python", "数据获取+筛选")
        ContainerDb(cache, "缓存", "JSON文件", "本地存储")
    }
    System_Ext(yf, "Yahoo Finance API", "yfinance")

    Rel(user, web, "HTTPS")
    Rel(web, core, "调用")
    Rel(core, yf, "数据获取")
    Rel(core, cache, "缓存")
    Rel(cache, web, "读取")
```

---

## 三、核心数据流

```mermaid
flowchart LR
    A["main.py 定时运行"] --> B["yfinance 获取行情数据"]
    B --> C["基本面筛选 PE/ROE/增长率"]
    C --> D["赛道分类 AI/半导体/生物医药"]
    D --> E["潜力评级 5-10x bagger"]
    E --> F["生成分析报告 JSON"]
    F --> G["web_app.py 提供 Web 界面"]
    G --> H["用户查看"]
```

---

## 四、核心文件

| 文件 | 说明 |
|------|------|
| main.py | 数据获取 + 筛选逻辑 |
| web_app.py | Web 界面 |
| scripts/ | 定时任务 |
| SKILL.md | OpenClaw skill 格式 |

---

## 五、部署

```bash
./start_web.sh
python main.py  # 手动运行分析
```
