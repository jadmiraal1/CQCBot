import json
import glob
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from arduino.app_utils import App

HOST = "0.0.0.0"
PORT = 8766
CAMERA_INDEXES = range(0, 6)

camera = None
camera_source = None
camera_lock = threading.Lock()
last_error = ""
last_probe = []

INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CameraTest</title>
  <style>
    :root {
      color-scheme: dark;
      font-family: Arial, sans-serif;
      background: #101417;
      color: #eef5f7;
    }
    body {
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
    }
    main {
      width: min(94vw, 860px);
      display: grid;
      gap: 14px;
    }
    h1 {
      margin: 0;
      font-size: 28px;
    }
    .viewer {
      border: 1px solid #38494f;
      border-radius: 8px;
      background: #182125;
      overflow: hidden;
      aspect-ratio: 16 / 9;
      display: grid;
      place-items: center;
    }
    img {
      width: 100%;
      height: 100%;
      object-fit: contain;
      background: #050708;
    }
    .status {
      min-height: 24px;
      color: #b8cbd3;
      font-family: Consolas, monospace;
    }
    button {
      width: fit-content;
      border: 1px solid #536970;
      border-radius: 6px;
      padding: 8px 12px;
      background: #203039;
      color: #eef5f7;
      cursor: pointer;
    }
  </style>
</head>
<body>
  <main>
    <h1>CameraTest</h1>
    <section class="viewer">
      <img id="stream" src="/stream.mjpg" alt="USB camera stream">
    </section>
    <button id="reload" type="button">Reconnect</button>
    <p id="status" class="status">Starting camera...</p>
  </main>
  <script>
    const statusEl = document.getElementById("status");
    const streamEl = document.getElementById("stream");
    const reloadEl = document.getElementById("reload");

    async function pollStatus() {
      try {
        const response = await fetch("/api/status", { cache: "no-store" });
        const payload = await response.json();
        statusEl.textContent = payload.ok ? payload.message : `Error: ${payload.error}`;
      } catch (error) {
        statusEl.textContent = `Network error: ${error}`;
      }
    }

    reloadEl.addEventListener("click", () => {
      streamEl.src = `/stream.mjpg?t=${Date.now()}`;
      pollStatus();
    });

    pollStatus();
    setInterval(pollStatus, 1000);
  </script>
</body>
</html>
"""


class CameraHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(INDEX_HTML.encode("utf-8"))
            return

        if self.path.startswith("/api/status"):
            self.write_json(camera_status())
            return

        if self.path.startswith("/stream.mjpg"):
            self.stream_camera()
            return

        self.send_response(404)
        self.end_headers()

    def stream_camera(self):
        self.send_response(200)
        self.send_header("Age", "0")
        self.send_header("Cache-Control", "no-cache, private")
        self.send_header("Pragma", "no-cache")
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
        self.end_headers()

        while True:
            frame = read_jpeg_frame()
            if frame is None:
                time.sleep(0.2)
                continue

            try:
                self.wfile.write(b"--frame\r\n")
                self.wfile.write(b"Content-Type: image/jpeg\r\n")
                self.wfile.write(f"Content-Length: {len(frame)}\r\n\r\n".encode("ascii"))
                self.wfile.write(frame)
                self.wfile.write(b"\r\n")
            except (BrokenPipeError, ConnectionResetError):
                break

    def write_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def get_cv2():
    try:
        import cv2
        return cv2
    except Exception as error:
        set_error(f"OpenCV import failed: {error}")
        return None


def open_camera():
    global camera, camera_source, last_probe

    cv2 = get_cv2()
    if cv2 is None:
        return None

    with camera_lock:
        if camera is not None and camera.isOpened():
            return camera

        candidates = list_video_devices() + list(CAMERA_INDEXES)
        last_probe = [str(candidate) for candidate in candidates]

        for candidate in candidates:
            capture = cv2.VideoCapture(candidate)
            capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            capture.set(cv2.CAP_PROP_FPS, 15)

            if capture.isOpened() and has_readable_frame(capture):
                camera = capture
                camera_source = candidate
                set_error("")
                return camera

            capture.release()

        camera = None
        camera_source = None
        set_error("No camera opened. Tried: " + ", ".join(last_probe))
        return None


def read_jpeg_frame():
    cv2 = get_cv2()
    capture = open_camera()
    if cv2 is None or capture is None:
        return None

    with camera_lock:
        ok, frame = capture.read()

    if not ok:
        set_error("Camera opened, but no frame was returned")
        return None

    ok, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
    if not ok:
        set_error("Failed to encode camera frame")
        return None

    set_error("")
    return encoded.tobytes()


def camera_status():
    capture = open_camera()
    if capture is None:
        return {
            "ok": False,
            "error": last_error or "Camera is not available",
            "tried": last_probe,
        }

    width = int(capture.get(get_cv2().CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(get_cv2().CAP_PROP_FRAME_HEIGHT))
    return {"ok": True, "message": f"Camera {camera_source} streaming at {width}x{height}"}


def list_video_devices():
    devices = sorted(glob.glob("/dev/video*"))
    # The UNO Q exposes Qualcomm codec devices as /dev/video0 and /dev/video1.
    # Prefer later nodes first, where USB webcams usually appear.
    return sorted(devices, key=video_device_sort_key)


def video_device_sort_key(path):
    try:
        number = int(path.replace("/dev/video", ""))
    except ValueError:
        number = 0
    return (number < 2, number)


def has_readable_frame(capture):
    for _ in range(8):
        ok, frame = capture.read()
        if ok and frame is not None:
            return True
        time.sleep(0.05)
    return False


def set_error(message):
    global last_error
    last_error = message


def start_server():
    server = ThreadingHTTPServer((HOST, PORT), CameraHandler)
    print(f"CameraTest listening on http://{HOST}:{PORT}")
    server.serve_forever()


threading.Thread(target=start_server, daemon=True).start()


def loop():
    time.sleep(1)


App.run(user_loop=loop)
