"""Local collector with an explicit browser control panel; Python stdlib only."""
from __future__ import annotations

import argparse
import hmac
import json
import secrets
import signal
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from presence import Observation, Tracker, atomic_json, read_presence
from windows_source import WindowsSource

DEFAULT_DATA = Path(__file__).resolve().parent / 'data'


class Collector:
    def __init__(self, data_dir, source):
        self.data_dir = data_dir
        data_dir.mkdir(parents=True, exist_ok=True)
        self.source = source
        self.lock = threading.RLock()
        self.stop = threading.Event()
        self.db = sqlite3.connect(data_dir / 'durations.db', check_same_thread=False)
        self.db.execute('CREATE TABLE IF NOT EXISTS totals (day TEXT, app TEXT, seconds REAL, PRIMARY KEY(day,app))')
        self.db.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
        day = datetime.now().astimezone().date()
        self.db.execute('DELETE FROM totals WHERE day < ? OR day > ?', ((day - timedelta(days=6)).isoformat(), day.isoformat()))
        self.db.commit()
        totals = {}
        for date, app, seconds in self.db.execute('SELECT day,app,seconds FROM totals'):
            if app in {'CSP', 'Blender'}:
                totals.setdefault(date, {'CSP': 0.0, 'Blender': 0.0})[app] = seconds
        self.tracker = Tracker(totals)
        self.pruned_day = day
        row = self.db.execute("SELECT value FROM settings WHERE key='paused'").fetchone()
        self.paused = row is None or row[0] != 'false'
        self.publish(Observation(None, 'paused' if self.paused else 'unknown'))

    def publish(self, observation):
        wall = datetime.now().astimezone()
        snapshot, increments = self.tracker.update(observation, wall, time.monotonic())
        if increments:
            for day, app, amount in increments:
                self.db.execute('INSERT INTO totals VALUES (?,?,?) ON CONFLICT(day,app) DO UPDATE SET seconds=seconds+excluded.seconds', (day, app, amount))
        if increments or self.pruned_day != wall.date():
            self.db.execute('DELETE FROM totals WHERE day < ? OR day > ?', ((wall.date() - timedelta(days=6)).isoformat(), wall.date().isoformat()))
            self.db.commit()
            self.pruned_day = wall.date()
        atomic_json(self.data_dir / 'presence.json', snapshot)

    def run(self):
        while not self.stop.is_set():
            with self.lock:
                paused = self.paused
            observation = Observation(None, 'paused') if paused else self.source.sample()
            with self.lock:
                self.publish(Observation(None, 'paused') if self.paused else observation)
            self.stop.wait(5)

    def control(self, action):
        with self.lock:
            if action in {'pause', 'resume'}:
                self.paused = action == 'pause'
                self.db.execute("INSERT INTO settings VALUES ('paused',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", ('true' if self.paused else 'false',))
                self.db.commit()
                self.publish(Observation(None, 'paused' if self.paused else 'unknown'))
            elif action == 'clear':
                # Explicit control-panel operation; clears only this tool's aggregates.
                self.paused = True
                self.db.execute('DELETE FROM totals')
                self.db.execute("INSERT INTO settings VALUES ('paused','true') ON CONFLICT(key) DO UPDATE SET value='true'")
                self.db.commit()
                self.tracker.clear()
                self.publish(Observation(None, 'paused'))
            elif action == 'stop':
                self.stop.set()
                self.publish(Observation(None, 'stopped'))
            else:
                raise ValueError('Unknown control action')

    def close(self):
        with self.lock:
            self.publish(Observation(None, 'stopped'))
            self.db.close()


def make_server(collector, port):
    token = secrets.token_urlsafe(32)
    allowed = {f'127.0.0.1:{port}', f'localhost:{port}'}
    panel = (Path(__file__).parent / 'panel.html').read_text(encoding='utf-8').replace('__TOKEN__', token)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # No access telemetry or raw request content in logs.

        def allowed_origin(self):
            host = self.headers.get('Host', '')
            origin = self.headers.get('Origin')
            return host in allowed and (origin is None or origin in {f'http://{h}' for h in allowed})

        def reply(self, status, value, mime='application/json; charset=utf-8'):
            data = value.encode('utf-8') if isinstance(value, str) else json.dumps(value, ensure_ascii=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('X-Frame-Options', 'DENY')
            self.send_header('Content-Security-Policy', "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if not self.allowed_origin():
                return self.reply(403, {'error': 'Local panel only'})
            if self.path == '/':
                return self.reply(200, panel, 'text/html; charset=utf-8')
            if self.path == '/presence':
                return self.reply(200, read_presence(collector.data_dir))
            return self.reply(404, {'error': 'Not found'})

        def do_POST(self):
            if not self.allowed_origin() or not hmac.compare_digest(self.headers.get('X-Beside-Token', ''), token):
                return self.reply(403, {'error': 'Panel authorization required'})
            if self.path not in {'/pause', '/resume', '/stop', '/clear'}:
                return self.reply(404, {'error': 'Not found'})
            collector.control(self.path[1:])
            self.reply(200, {'ok': True})

    class Server(ThreadingHTTPServer):
        daemon_threads = True
        allow_reuse_address = False

    return Server(('127.0.0.1', port), Handler)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-dir', type=Path, default=DEFAULT_DATA)
    parser.add_argument('--port', type=int, default=3212)
    args = parser.parse_args()
    source = WindowsSource()
    # Cross-process Windows mutex prevents a second collector from altering live data.
    import ctypes
    from ctypes import wintypes
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
    kernel.CreateMutexW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    mutex = kernel.CreateMutexW(None, False, f'Local\\SirenKittenBeside-{args.port}')
    if not mutex or ctypes.get_last_error() == 183:
        if mutex:
            kernel.CloseHandle(mutex)
        raise SystemExit('Beside is already running, or the local mutex is unavailable.')
    collector = None
    server = None
    worker = None
    web = None
    try:
        # Port ownership checked before opening the production store.
        import socket
        with socket.socket() as probe:
            probe.bind(('127.0.0.1', args.port))
        collector = Collector(args.data_dir.resolve(), source)
        server = make_server(collector, args.port)
        web = threading.Thread(target=server.serve_forever, daemon=True)
        worker = threading.Thread(target=collector.run, daemon=True)
        web.start()
        worker.start()
        signal.signal(signal.SIGINT, lambda *_: collector.stop.set())
        signal.signal(signal.SIGTERM, lambda *_: collector.stop.set())
        while not collector.stop.wait(0.5):
            if not worker.is_alive() or not web.is_alive():
                raise RuntimeError('A collector component stopped unexpectedly.')
    finally:
        if collector:
            collector.stop.set()
        if worker:
            worker.join(timeout=8)
        if server and web:
            server.shutdown()
        if server:
            server.server_close()
        if collector:
            collector.close()
        kernel.CloseHandle(mutex)


if __name__ == '__main__':
    main()
