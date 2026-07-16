#!/usr/bin/env python3
"""vintos_claude_shim.py — Aegis. Model-aware OpenAI->Claude proxy on 127.0.0.1, so grok chat jobs move to
non-reasoning Claude with grok fallback, while image/video/voice pass straight through to x.ai.

  POST /v1/chat/completions:
    - model contains imagine|image|video  -> forward RAW to api.x.ai (Claude can't do these)
    - else (text chat)                     -> non-reasoning Claude; on error/refusal/empty -> forward RAW to grok
  GET /health -> {"ok": true}

Keeps voice untouched (those scripts keep pointing at x.ai; only chat scripts get base-URL-swapped to here).
Run:      python3 vintos_claude_shim.py            (serves on 127.0.0.1:8599)
Install:  python3 vintos_claude_shim.py --install  (writes+enables systemd --user unit, starts, health-checks)
"""
import os, sys, json, time, urllib.request

HOST, PORT = "127.0.0.1", 8599
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
XAI_URL = "https://api.x.ai/v1/chat/completions"
CLAUDE_MODEL = "claude-opus-4-8"
LOG = "/tmp/vintos-claude-shim.log"

def _log(s):
    try:
        with open(LOG, "a") as f: f.write(time.strftime("%H:%M:%S ") + s + "\n")
    except Exception: pass

def _anthropic_key():
    k = os.environ.get("ANTHROPIC_API_KEY", "")
    if not k:
        try: k = open(os.path.expanduser("~/.vintos/anthropic-key")).read().strip()
        except Exception: k = ""
    return k

def _xai_key():
    k = os.environ.get("XAI_API_KEY", "")
    if not k:
        for p in ("~/.vintos/xai-key", "~/.vintos/grok-key"):
            try: k = open(os.path.expanduser(p)).read().strip(); break
            except Exception: pass
    return k

def claude_complete(messages, max_tokens):
    """Non-reasoning Claude. Returns assistant text, or None on error/refusal/empty."""
    key = _anthropic_key()
    if not key: return None
    sys_txt = "\n\n".join(m.get("content", "") for m in messages
                          if m.get("role") == "system" and isinstance(m.get("content"), str))
    conv = [{"role": m["role"], "content": m["content"]} for m in messages
            if m.get("role") in ("user", "assistant") and isinstance(m.get("content"), str)]
    if not conv:
        conv = [{"role": "user", "content": sys_txt or "."}]
    body = {"model": CLAUDE_MODEL, "max_tokens": int(max_tokens or 1024),
            "messages": conv, "thinking": {"type": "disabled"}}
    if sys_txt:
        body["system"] = [{"type": "text", "text": sys_txt, "cache_control": {"type": "ephemeral"}}]
    req = urllib.request.Request(ANTHROPIC_URL, data=json.dumps(body).encode(),
        headers={"content-type": "application/json", "anthropic-version": "2023-06-01", "x-api-key": key})
    try:
        d = json.loads(urllib.request.urlopen(req, timeout=180).read())
    except Exception as e:
        _log(f"claude error: {e}"); return None
    if d.get("type") == "error" or d.get("stop_reason") == "refusal":
        _log(f"claude refusal/error: {str(d)[:120]}"); return None
    text = "".join(b.get("text", "") for b in d.get("content", []) if b.get("type") == "text")
    return text or None

def forward_xai(raw):
    """Forward raw OpenAI-format bytes to real grok. Returns (status, body_bytes)."""
    key = _xai_key()
    req = urllib.request.Request(XAI_URL, data=raw,
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
    try:
        r = urllib.request.urlopen(req, timeout=300)
        return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:
        _log(f"xai error: {e}")
        return 502, json.dumps({"error": {"message": "shim: grok forward failed: " + str(e)}}).encode()

def openai_wrap(model, text):
    return json.dumps({
        "id": "chatcmpl-shim", "object": "chat.completion", "created": int(time.time()),
        "model": model, "choices": [{"index": 0, "message": {"role": "assistant", "content": text},
        "finish_reason": "stop"}], "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }).encode()

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _send(self, status, body):
        self.send_response(status); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        if self.path == "/health": self._send(200, b'{"ok": true}')
        else: self._send(404, b'{"error":"not found"}')
    def do_POST(self):
        raw = self.rfile.read(int(self.headers.get("Content-Length", 0) or 0))
        try:
            j = json.loads(raw or b"{}")
        except Exception:
            s, b = forward_xai(raw); return self._send(s, b)
        model = str(j.get("model", ""))
        # image/video generation -> straight to grok
        if any(t in model for t in ("imagine", "image", "video")):
            _log(f"passthrough {model}"); s, b = forward_xai(raw); return self._send(s, b)
        # text chat -> Claude, fallback grok
        text = claude_complete(j.get("messages", []), j.get("max_tokens"))
        if text:
            _log(f"claude ok ({model})"); return self._send(200, openai_wrap(model, text))
        _log(f"fallback->grok ({model})"); s, b = forward_xai(raw); return self._send(s, b)

UNIT = """[Unit]
Description=Vintos Claude shim (OpenAI->Claude proxy, grok fallback)
After=network.target

[Service]
ExecStart=/usr/bin/python3 %s
Restart=always
RestartSec=2
%s

[Install]
WantedBy=default.target
"""

def install():
    self_path = os.path.abspath(__file__)
    envline = ""
    xk = _xai_key()
    if os.environ.get("XAI_API_KEY"):
        envline = "Environment=XAI_API_KEY=" + os.environ["XAI_API_KEY"]
    ud = os.path.expanduser("~/.config/systemd/user")
    os.makedirs(ud, exist_ok=True)
    open(os.path.join(ud, "vintos-claude-shim.service"), "w").write(UNIT % (self_path, envline))
    os.system("systemctl --user daemon-reload")
    os.system("systemctl --user enable --now vintos-claude-shim")
    time.sleep(2)
    try:
        ok = urllib.request.urlopen(f"http://{HOST}:{PORT}/health", timeout=5).read()
        print("installed + running. health:", ok.decode())
    except Exception as e:
        print("installed, but health check failed:", e, "\n  check: journalctl --user -u vintos-claude-shim -e")
    print(f"anthropic key: {'found' if _anthropic_key() else 'MISSING'} | xai key: {'found' if xk else 'MISSING (fallback/passthrough will fail)'}")

if __name__ == "__main__":
    if "--install" in sys.argv:
        install()
    else:
        print(f"vintos-claude-shim on http://{HOST}:{PORT}  (log: {LOG})")
        ThreadingHTTPServer((HOST, PORT), H).serve_forever()
