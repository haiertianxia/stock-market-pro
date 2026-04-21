#!/bin/bash
cd /home/admin/github/stock-market-pro
nohup python web_app.py > web_app.log 2>&1 &
echo $! > web_app.pid
echo "Web server started with pid $(cat web_app.pid) on port 8765"
