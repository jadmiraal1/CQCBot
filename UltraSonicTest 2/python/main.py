import json
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from arduino.app_utils import App, Bridge

HOST = "0.0.0.0"
PORT = 8767

INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>UltraSonicTest</title>
  <style>
    :root {
      color-scheme: dark;
      font-family: Arial, sans-serif;
      background: #101417;
      color: #edf6f2;
    }
    body {
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
    }
    main {
      width: min(92vw, 520px);
      display: grid;
      gap: 16px;
    }
    h1 {
      margin: 0;
      font-size: 28px;
    }
    .panel {
      border: 1px solid #35464b;
      border-radius: 8px;
      padding: 18px;
      background: #182125;
    }
    .distance {
      display: flex;
      align-items: baseline;
      gap: 10px;
      margin: 12px 0;
    }
    .value {
      font-size: 72px;
      line-height: 1;
      font-weight: 700;
      color: #7ee2b8;
    }
    .unit {
      color: #b8c8c2;
      font-size: 22px;
    }
    .sub {
      min-height: 24px;
      color: #b8c8c2;
      font-family: Consolas, monospace;
    }
    .bar {
      height: 12px;
      border-radius: 999px;
      background: #293438;
      overflow: hidden;
    }
    .fill {
      height: 100%;
      width: 0%;
      background: #7ee2b8;
      transition: width 140ms ease;
    }
  </style>
</head>
<body>
  <main>
    <h1>UltraSonicTest</h1>
    <section class="panel">
      <div class="distance">
        <span id="cm" class="value">--</span>
        <span class="unit">cm</span>
      </div>
      <div class="bar"><div id="fill" class="fill"></div></div>
      <p id="sub" class="sub">Waiting for first reading...</p>
    </section>
  </main>
  <script>
    const cmEl = document.getElementById("cm");
    const subEl = document.getElementById("sub");
    const fillEl = document.getElementById("fill");

    async function pollDistance() {
      try {
        const response = await fetch("/api/distance", { cache: "no-store" });
        const payload = await response.json();
        if (!payload.ok) {
          cmEl.textContent = "--";
          subEl.textContent = payload.error || "No echo";
          fillEl.style.width = "0%";
          return;
        }

        cmEl.textContent = payload.cm.toFixed(1);
        subEl.textContent = `${payload.inches.toFixed(1)} in`;
        fillEl.style.width = `${Math.max(0, Math.min(100, (payload.cm / 200) * 100))}%`;
      } catch (error) {
        cmEl.textContent = "--";
        subEl.textContent = `Network error: ${error}`;
        fillEl.style.width = "0%";
      }
    }

    pollDistance();
    setInterval(pollDistance, 200);
  </script>
</body>
</html>
"""


class UltraSonicHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(INDEX_HTML.encode("utf-8"))
            return

        if self.path == "/api/distance":
            try:
                result = str(Bridge.call("readDistance", ""))
                payload = parse_distance(result)
                self.write_json(payload)
            except Exception as error:
                self.write_json({"ok": False, "error": str(error)}, status=500)
            return

        self.send_response(404)
        self.end_headers()

    def write_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def parse_distance(result):
    match = re.search(r"cm=([0-9.]+)\s+in=([0-9.]+)", result)
    if not match:
        return {"ok": False, "error": result}

    return {
        "ok": True,
        "cm": float(match.group(1)),
        "inches": float(match.group(2)),
        "raw": result,
    }


def start_server():
    server = ThreadingHTTPServer((HOST, PORT), UltraSonicHandler)
    print(f"UltraSonicTest listening on http://{HOST}:{PORT}")
    server.serve_forever()


threading.Thread(target=start_server, daemon=True).start()


def loop():
    time.sleep(1)


App.run(user_loop=loop)
