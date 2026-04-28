#!/bin/bash
# auto-sync.sh — HealthPlanet API から health.json を更新し、GitHub Pages へデプロイ
#
# launchd (com.ueyama.health-sync) から毎朝呼ばれる。
# スマホからは SSH 経由で `launchctl kickstart -k gui/$UID/com.ueyama.health-sync` を叩けば即時実行。

set -uo pipefail

SOURCE_DIR="/Users/major/Documents/00_Shota-all/01_personal/Shota's website"
LOG_DIR="$HOME/Library/Logs/health-sync"
mkdir -p "$LOG_DIR"

TS() { date '+%Y-%m-%d %H:%M:%S'; }

echo "[$(TS)] === health auto-sync start ==="

# launchd は最小PATHしか持たないので明示
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

# 1. HealthPlanet API → health/data/health.json
echo "[$(TS)] step 1: pulling HealthPlanet API"
/usr/bin/python3 "$SOURCE_DIR/health/scripts/healthplanet_sync.py" --days 30
SYNC_EXIT=$?
echo "[$(TS)] sync exit: $SYNC_EXIT"

# 2. GitHub Pages へデプロイ（差分なければスキップ）
echo "[$(TS)] step 2: deploy to GitHub Pages"
/bin/bash "$SOURCE_DIR/deploy.sh"
DEPLOY_EXIT=$?
echo "[$(TS)] deploy exit: $DEPLOY_EXIT"

echo "[$(TS)] === done ==="
