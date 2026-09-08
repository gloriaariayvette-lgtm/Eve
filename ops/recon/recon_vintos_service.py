#!/usr/bin/env python3
"""recon_vintos_service.py — Aegis, READ-ONLY. How is the Vintos server (server.py, :8500) launched, and where
does its stdout/log go? So we get the exact restart command + log path — no guessing on the live box."""
import subprocess, os
HOME = os.path.expanduser("~")
def sh(cmd):
    try: return subprocess.run(["bash", "-lc", cmd], capture_output=True, text=True, timeout=15).stdout.strip() or "(none)"
    except Exception as e: return f"(err {e})"

print("=== running process for server.py / :8500 ===")
print(sh("ps -eo pid,ppid,cmd | grep -E 'server\\.py|uvicorn.*850|:8500' | grep -v grep | head -20"))
print("\n=== :8500 listener ===")
print(sh("ss -ltnp 2>/dev/null | grep ':8500' || echo '(need sudo to see pid, or not listening)'"))
print("\n=== systemd units mentioning vintos (system + user) ===")
print(sh("systemctl list-units --all --type=service 2>/dev/null | grep -i vintos; "
         "systemctl --user list-units --all --type=service 2>/dev/null | grep -i vintos; "
         "ls -1 /etc/systemd/system/*vintos* ~/.config/systemd/user/*vintos* 2>/dev/null"))
print("\n=== start/run scripts in ~/Vintos ===")
print(sh("ls -1 ~/Vintos/*.sh ~/Vintos/start* ~/Vintos/run* ~/Vintos/*.service 2>/dev/null | head"))
print("\n=== candidate log files (newest first) ===")
print(sh("ls -lt /tmp/*vintos* ~/Vintos/*.log ~/Vintos/nohup.out ~/.vintos/*.log /tmp/server*.log 2>/dev/null | head -15"))
print("\n=== crontab launch hints (@reboot / server.py / 8500) ===")
print(sh("crontab -l 2>/dev/null | grep -iE 'server\\.py|8500|reboot|uvicorn' | head"))
