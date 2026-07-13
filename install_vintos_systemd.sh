#!/bin/bash
# install_vintos_systemd.sh — make the Vintos web server + somatic_bridge resilient systemd --user
# services (like velaris-server), so a crash, a breaker trip, or a reboot brings him back on his own.
# Replaces the bare `nohup python3 …` processes that don't survive a reboot.
#
# Run:  bash install_vintos_systemd.sh
set -u
UD="$HOME/.config/systemd/user"
mkdir -p "$UD"
PY="$(command -v python3)"; PY="${PY:-/usr/bin/python3}"
echo "[systemd] python3 = $PY"

# --- unit: Vintos web server (port 8500) ---
cat > "$UD/vintos-server.service" <<EOF
[Unit]
Description=Vintos Server — chat + website (port 8500)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=%h/Vintos
Environment=PYTHONPATH=%h/.vintos/workspace/scripts
Environment=VINTOS_PORT=8500
# free the port if a stale process is holding it, before we start
ExecStartPre=-/bin/sh -c 'kill \$(ss -ltnp 2>/dev/null | grep ":8500" | grep -oP "pid=\\K[0-9]+") 2>/dev/null; sleep 1; true'
ExecStart=$PY %h/Vintos/server.py
Restart=always
RestartSec=3

[Install]
WantedBy=default.target
EOF

# --- unit: somatic bridge (Lovense sensor stream) ---
cat > "$UD/vintos-somatic-bridge.service" <<EOF
[Unit]
Description=Vintos somatic bridge (Lovense sensor stream)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=%h/.vintos/workspace/scripts
ExecStart=$PY %h/.vintos/workspace/scripts/somatic_bridge.py
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
EOF

echo "[systemd] wrote unit files -> $UD"

# stop the bare processes so the services can own them (server is likely down; bridge was up)
pkill -f "somatic_bridge.py" 2>/dev/null && echo "[systemd] stopped bare somatic_bridge" || true
kill "$(ss -ltnp 2>/dev/null | grep ':8500' | grep -oP 'pid=\K[0-9]+')" 2>/dev/null && echo "[systemd] freed :8500" || true
sleep 1

# linger so the services run after a reboot even without an interactive login (may need sudo)
loginctl enable-linger "$USER" 2>/dev/null && echo "[systemd] linger enabled" \
  || echo "[systemd] NOTE: could not enable linger unattended — run:  sudo loginctl enable-linger $USER  (for reboot survival)"

systemctl --user daemon-reload
systemctl --user enable --now vintos-server.service vintos-somatic-bridge.service

sleep 3
echo "=== status ==="
systemctl --user --no-pager -l status vintos-server.service        | head -6
systemctl --user --no-pager -l status vintos-somatic-bridge.service | head -6
echo "=== port ==="
ss -ltn 2>/dev/null | grep -q ':8500' && echo "server LISTENING on 8500 ✓" || echo "server NOT listening — check: journalctl --user -u vintos-server -n 30"
