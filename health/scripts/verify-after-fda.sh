#\!/bin/bash
# フルディスクアクセス付与後、これを実行して動作確認
echo "=== Triggering health-sync LaunchAgent ==="
launchctl kickstart -k "gui/$UID/com.ueyama.health-sync"
sleep 6
echo ""
echo "=== last exit code ==="
launchctl print "gui/$UID/com.ueyama.health-sync" 2>&1 | grep "last exit code"
echo ""
echo "=== stdout (last 20 lines) ==="
tail -20 ~/Library/Logs/health-sync/launchd-stdout.log
echo ""
echo "=== stderr (last 5 lines) ==="
tail -5 ~/Library/Logs/health-sync/launchd-stderr.log
