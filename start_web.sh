#!/bin/bash
cd /home/admin/github/stock-market-pro

# Kill old v1 if running
kill $(cat web_app.pid 2>/dev/null) 2>/dev/null || true

# Start v2 dashboard
nohup python3 web_app_v2.py > web_app_v2.log 2>&1 &
echo $! > web_app_v2.pid
echo "Stock Market Pro v2 started with pid $(cat web_app_v2.pid) on port 8765"
