import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from arduino.app_utils import App, Bridge

HOST = "0.0.0.0"
PORT = 8765
PHYSICAL_RIGHT_SIDE_TRIM = 1.25
PHYSICAL_LEFT_SIDE_TRIM = 1.0

INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>LaptopMovement</title>
  <style>
    :root {
      color-scheme: dark;
      font-family: Arial, sans-serif;
      background: #11181c;
      color: #eef7fb;
    }
    body {
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
    }
    main {
      width: min(92vw, 560px);
      display: grid;
      gap: 18px;
    }
    h1 {
      margin: 0;
      font-size: 28px;
    }
    .panel {
      border: 1px solid #34464f;
      border-radius: 8px;
      padding: 18px;
      background: #172228;
    }
    .keys {
      display: grid;
      grid-template-columns: repeat(3, 74px);
      gap: 10px;
      justify-content: center;
      margin: 14px 0;
    }
    .key {
      height: 64px;
      border: 1px solid #4d6570;
      border-radius: 8px;
      display: grid;
      place-items: center;
      font-size: 28px;
      font-weight: 700;
      background: #203039;
      user-select: none;
    }
    .key.active {
      background: #13b8c8;
      color: #061215;
      border-color: #6ff0fb;
    }
    .wide {
      grid-column: 1 / 4;
      width: 100%;
    }
    label {
      display: grid;
      gap: 8px;
      font-size: 14px;
      color: #b8cbd3;
    }
    input[type="range"] {
      width: 100%;
    }
    .status {
      min-height: 24px;
      color: #9ee8ef;
      font-family: Consolas, monospace;
    }
  </style>
</head>
<body>
  <main>
    <h1>LaptopMovement</h1>
    <section class="panel">
      <div class="keys">
        <div></div><div id="key-w" class="key">W</div><div></div>
        <div id="key-a" class="key">A</div><div id="key-s" class="key">S</div><div id="key-d" class="key">D</div>
        <div id="key-space" class="key wide">SPACE</div>
      </div>
      <label>
        Speed <span id="speed-label">160</span>
        <input id="speed" type="range" min="80" max="200" value="160">
      </label>
      <p id="status" class="status">Stopped</p>
    </section>
  </main>
  <script>
    const pressed = new Set();
    const statusEl = document.getElementById("status");
    const speedEl = document.getElementById("speed");
    const speedLabel = document.getElementById("speed-label");
    let lastCommand = "";

    function setKeyVisuals() {
      for (const key of ["w", "a", "s", "d"]) {
        document.getElementById(`key-${key}`).classList.toggle("active", pressed.has(key));
      }
      document.getElementById("key-space").classList.toggle("active", pressed.has(" "));
    }

    function commandFromKeys() {
      if (pressed.has(" ")) return [0, 0, "stop"];
      const speed = Number(speedEl.value);
      let left = 0;
      let right = 0;
      if (pressed.has("w")) {
        left += speed;
        right += speed;
      }
      if (pressed.has("s")) {
        left -= speed;
        right -= speed;
      }
      if (pressed.has("a")) {
        left += speed;
        right -= speed;
      }
      if (pressed.has("d")) {
        left -= speed;
        right += speed;
      }
      left = Math.max(-255, Math.min(255, left));
      right = Math.max(-255, Math.min(255, right));
      return [left, right, `left=${left} right=${right}`];
    }

    async function sendCommand(force = false) {
      const [left, right, label] = commandFromKeys();
      const command = `${left},${right}`;
      if (!force && command === lastCommand) return;
      lastCommand = command;
      setKeyVisuals();
      statusEl.textContent = `Sending ${label}`;
      try {
        const response = await fetch(`/api/drive?left=${left}&right=${right}`, { cache: "no-store" });
        const payload = await response.json();
        statusEl.textContent = payload.ok ? `OK ${payload.result || label}` : `Error: ${payload.error}`;
      } catch (error) {
        statusEl.textContent = `Network error: ${error}`;
      }
    }

    window.addEventListener("keydown", (event) => {
      const key = event.key.toLowerCase();
      if (["w", "a", "s", "d", " "].includes(key)) {
        event.preventDefault();
        pressed.add(key);
        sendCommand();
      }
    });

    window.addEventListener("keyup", (event) => {
      const key = event.key.toLowerCase();
      if (["w", "a", "s", "d", " "].includes(key)) {
        event.preventDefault();
        pressed.delete(key);
        sendCommand();
      }
    });

    speedEl.addEventListener("input", () => {
      speedLabel.textContent = speedEl.value;
      sendCommand(true);
    });

    setInterval(() => sendCommand(true), 250);
    window.addEventListener("blur", () => {
      pressed.clear();
      sendCommand(true);
    });
  </script>
</body>
</html>
"""


class MovementHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(INDEX_HTML.encode("utf-8"))
            return

        if parsed.path == "/api/drive":
            query = parse_qs(parsed.query)
            try:
                left = read_speed(query, "left")
                right = read_speed(query, "right")
                # The wiring maps the app's left command to the rover's
                # physical right side, and right command to physical left.
                actual_left = apply_trim(left, PHYSICAL_RIGHT_SIDE_TRIM)
                actual_right = apply_trim(right, PHYSICAL_LEFT_SIDE_TRIM)
                result = Bridge.call("drive", f"{actual_left},{actual_right}")
                self.write_json({
                    "ok": True,
                    "left": left,
                    "right": right,
                    "actualLeft": actual_left,
                    "actualRight": actual_right,
                    "result": str(result),
                })
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


def read_speed(query, name):
    value = int(query.get(name, ["0"])[0])
    return max(-255, min(255, value))


def apply_trim(speed, trim):
    value = round(speed * trim)
    return max(-255, min(255, value))


def start_server():
    server = ThreadingHTTPServer((HOST, PORT), MovementHandler)
    print(f"LaptopMovement listening on http://{HOST}:{PORT}")
    server.serve_forever()


threading.Thread(target=start_server, daemon=True).start()


def loop():
    time.sleep(1)


App.run(user_loop=loop)
