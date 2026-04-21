#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
迁移现有的每日分析JSON文件到历史推荐数据库
"""

import json
import os
import glob
from datetime import datetime

HISTORY_FILE = "/home/admin/.openclaw/workspace/skills/stock-market-pro/scripts/stock_recommendation_history.json"

def load_existing_daily_files():
    """查找所有现有的每日分析文件"""
    pattern = "/home/admin/.openclaw/workspace/stock_analysis_*.json"
    files = glob.glob(pattern)
    results = []
    
    for f in files:
        try:
            with open(f, 'r') as f_in:
                data = json.load(f_in)
                date_str = data.get('date', '').split()[0]
                for stock in data.get('results', []):
                    if stock.get('current_price') is not None:
                        # 确保有date字段
                        if 'date' not in stock:
                            stock['date'] = date_str
                        if 'timestamp' not in stock:
                            # 从文件名提取日期
                            # filename: stock_analysis_20260418.json → 2026-04-18
                            basename = os.path.basename(f)
                            if '20' in basename:
                                yyyymmdd = basename.replace('stock_analysis_', '').replace('.json', '')
                                if len(yyyymmdd) == 8:
                                    yyyy = yyyymmdd[:4]
                                    mm = yyyymmdd[4:6]
                                    dd = yyyymmdd[6:8]
                                    iso_date = f"{yyyy}-{mm}-{dd}T12:00:00"
                                    stock['timestamp'] = iso_date
                                    if not date_str:
                                        stock['date'] = f"{yyyy}-{mm}-{dd}"
                            else:
                                stock['timestamp'] = datetime.now().isoformat()
                                if not date_str:
                                    stock['date'] = datetime.now().strftime('%Y-%m-%d')
                        results.append(stock)
        except Exception as e:
            print(f"Skipping {f}: {e}")
    
    return results

def migrate():
    """迁移所有现有数据"""
    # 创建空历史文件如果不存在
    if not os.path.exists(HISTORY_FILE):
        empty_history = {
            "history": [],
            "last_updated": None,
            "total_recommendations": 0
        }
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(empty_history, f, indent=2, ensure_ascii=False)
    
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        current_history = json.load(f)
    
    existing = load_existing_daily_files()
    print(f"Found {len(existing)} recommendations in existing daily files")
    
    if not existing:
        print("Nothing to migrate")
        return
    
    # 添加所有现有条目，分配ID
    next_id = len(current_history['history']) + 1
    for entry in existing:
        entry['id'] = next_id
        next_id += 1
        current_history['history'].append(entry)
    
    current_history['last_updated'] = datetime.now().isoformat()
    current_history['total_recommendations'] = len(current_history['history'])
    
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(current_history, f, indent=2, ensure_ascii=False)
    
    print(f"Migration complete! Now history has {current_history['total_recommendations']} total recommendations")

if __name__ == "__main__":
    migrate()
