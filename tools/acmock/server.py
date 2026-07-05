"""Browser backend: a stdlib HTTP server + the per-frame driver loop.

  GET /          -> the canvas UI (webui/index.html)
  GET /events    -> Server-Sent Events stream of frame scenes (one per client)
  POST /event    -> a control interaction (checkbox/spinner/button) from the page

The driver loop runs on the main thread (serve() blocks); the HTTP server runs on
a background thread. Control events are queued by HTTP handler threads and drained
by the driver so app callbacks always run on the app's own thread.
"""

import json
import os
import queue
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

WEBUI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "webui", "index.html")


class ServerState(object):
    def __init__(self):
        self._clients = set()
        self._lock = threading.Lock()
        self._events = queue.Queue()
        self._last_scene = "{}"

    # client (SSE) registry
    def add_client(self):
        q = queue.Queue(maxsize=4)
        with self._lock:
            self._clients.add(q)
        q.put(self._last_scene)           # send the latest frame immediately
        return q

    def remove_client(self, q):
        with self._lock:
            self._clients.discard(q)

    def broadcast(self, scene_dict):
        data = json.dumps(scene_dict, default=str)
        self._last_scene = data
        with self._lock:
            clients = list(self._clients)
        for q in clients:
            try:
                q.put_nowait(data)
            except queue.Full:
                # Slow client: drop the oldest frame, keep the newest.
                try:
                    q.get_nowait()
                    q.put_nowait(data)
                except queue.Empty:
                    pass

    # control events (browser -> app)
    def push_event(self, ev):
        self._events.put(ev)

    def drain_events(self):
        out = []
        while True:
            try:
                out.append(self._events.get_nowait())
            except queue.Empty:
                break
        return out


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass                               # silence per-request logging

    @property
    def state(self):
        return self.server.state

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/":
            self._serve_index()
        elif path == "/events":
            self._serve_events()
        else:
            self.send_response(204)
            self.end_headers()

    def do_POST(self):
        if self.path != "/event":
            self.send_response(404)
            self.end_headers()
            return
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b"{}"
        try:
            ev = json.loads(body.decode("utf-8"))
            self.state.push_event(ev)
        except (ValueError, UnicodeDecodeError):
            pass
        self.send_response(204)
        self.end_headers()

    def _serve_index(self):
        try:
            with open(WEBUI, "rb") as fh:
                body = fh.read()
        except OSError:
            body = b"<h1>acmock: webui/index.html missing</h1>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_events(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        q = self.state.add_client()
        try:
            while True:
                try:
                    data = q.get(timeout=15)
                except queue.Empty:
                    self.wfile.write(b": keep-alive\n\n")   # comment ping
                    self.wfile.flush()
                    continue
                self.wfile.write(b"data: " + data.encode("utf-8") + b"\n\n")
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            self.state.remove_client(q)


def serve(rt, mod, drive_once, fps=30, port=8765):
    state = ServerState()
    httpd = ThreadingHTTPServer(("", port), _Handler)
    httpd.state = state
    httpd.daemon_threads = True
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()

    url = "http://localhost:%d" % port
    print("acmock: serving '%s' at %s  (Ctrl-C to stop)" % (rt.window.get("name") or "app", url),
          flush=True)

    interval = 1.0 / max(1, fps)
    start = time.perf_counter()
    last = start
    try:
        while True:
            now = time.perf_counter()
            dt = now - last
            last = now
            elapsed = now - start
            scene = drive_once(rt, mod, dt, elapsed, server=state)
            state.broadcast(scene)
            slack = interval - (time.perf_counter() - now)
            if slack > 0:
                time.sleep(slack)
    except KeyboardInterrupt:
        print("\nacmock: stopping.")
    finally:
        httpd.shutdown()
