import http.client
import json
import re
import subprocess
import sys
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from presence import Observation, Tracker, atomic_json, classify, read_presence
from collector import Collector, make_server

START = datetime(2026, 10, 18, 12, tzinfo=timezone(timedelta(hours=8)))
CSP = Observation('CSP', 'active')


class TrackerTests(unittest.TestCase):
    def test_categories(self):
        self.assertEqual(classify(r'C:\private\UDMPaintEX.exe'), 'CSP')
        self.assertEqual(classify('BLENDER.exe'), 'Blender')
        self.assertEqual(classify(r'C:\private\secret.exe'), 'other')

    def test_active_and_switch(self):
        t = Tracker()
        t.update(CSP, START, 0)
        p, _ = t.update(CSP, START + timedelta(seconds=5), 5)
        self.assertEqual(p['session']['foreground_seconds'], 5)
        p, _ = t.update(Observation('other', 'active'), START + timedelta(seconds=10), 10)
        self.assertIsNone(p['session'])
        p, _ = t.update(CSP, START + timedelta(seconds=15), 15)
        self.assertEqual(p['session']['foreground_seconds'], 5)
        self.assertEqual(p['today_foreground_seconds']['CSP'], 5)

    def test_idle_and_pause_reset_session(self):
        for state in ('idle', 'paused', 'locked', 'unknown', 'stopped'):
            with self.subTest(state=state):
                t = Tracker()
                t.update(CSP, START, 0)
                t.update(CSP, START + timedelta(seconds=5), 5)
                t.update(Observation(None, state), START + timedelta(seconds=10), 10)
                p, _ = t.update(CSP, START + timedelta(seconds=15), 15)
                self.assertEqual(p['session']['foreground_seconds'], 0)
                self.assertEqual(p['today_foreground_seconds']['CSP'], 5)

    def test_sleep_and_clock_jump_not_counted(self):
        for wall_seconds, mono in ((600, 600), (-60, 5), (600, 5), (5, -1)):
            t = Tracker()
            t.update(CSP, START, 0)
            p, changes = t.update(CSP, START + timedelta(seconds=wall_seconds), mono)
            self.assertEqual(changes, [])
            self.assertEqual(p['session']['foreground_seconds'], 0)

    def test_midnight_and_retention(self):
        t = Tracker({'2026-10-01': {'CSP': 123}})
        start = START.replace(hour=23, minute=59, second=58)
        t.update(CSP, start, 0)
        _, changes = t.update(CSP, start + timedelta(seconds=5), 5)
        self.assertEqual(changes, [('2026-10-18', 'CSP', 2), ('2026-10-19', 'CSP', 3)])
        self.assertNotIn('2026-10-01', t.totals)


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def snapshot(self):
        return Tracker().update(CSP, START, 0)[0]

    def test_stale_cannot_claim_presence(self):
        atomic_json(self.path / 'presence.json', self.snapshot())
        p = read_presence(self.path, START + timedelta(seconds=21))
        self.assertTrue(p['stale'])
        self.assertIsNone(p['app'])
        self.assertIsNone(p['session'])

    def test_privacy_whitelist(self):
        raw = self.snapshot()
        raw['secret_window_title'] = 'SECRET'
        raw['session']['file'] = 'SECRET'
        atomic_json(self.path / 'presence.json', raw)
        self.assertNotIn('SECRET', json.dumps(read_presence(self.path, START)))

    def test_bad_snapshot_fails_closed(self):
        for raw in ([], {}, {'schema': 'beside.presence.v1', 'observed_at': START.isoformat(), 'state': 'active', 'today_foreground_seconds': []}):
            atomic_json(self.path / 'presence.json', raw)
            p = read_presence(self.path, START)
            self.assertTrue(p['stale'])
            self.assertIsNone(p['app'])

    def test_mcp_stdio(self):
        atomic_json(self.path / 'presence.json', Tracker().update(CSP, datetime.now().astimezone(), 0)[0])
        messages = [
            {'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {'protocolVersion': '2025-06-18'}},
            {'jsonrpc': '2.0', 'method': 'notifications/initialized'},
            {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list'},
            {'jsonrpc': '2.0', 'id': 3, 'method': 'tools/call', 'params': {'name': 'get_presence', 'arguments': {}}},
            {'jsonrpc': '2.0', 'id': 4, 'method': 'tools/call', 'params': {'name': 'get_creative_session', 'arguments': {}}},
            {'jsonrpc': '2.0', 'id': 5, 'method': 'tools/call', 'params': {'name': 'get_presence', 'arguments': {'path': 'not-allowed'}}},
        ]
        p = subprocess.run([sys.executable, str(Path(__file__).parent / 'mcp_server.py'), '--data-dir', str(self.path)], input='\n'.join(map(json.dumps, messages))+'\n', capture_output=True, text=True, encoding='utf-8', timeout=10)
        self.assertEqual(p.returncode, 0, p.stderr)
        replies = [json.loads(line) for line in p.stdout.splitlines()]
        self.assertEqual(len(replies), 5)
        self.assertEqual(replies[0]['result']['protocolVersion'], '2025-06-18')
        self.assertEqual(len(replies[1]['result']['tools']), 2)
        self.assertEqual(json.loads(replies[2]['result']['content'][0]['text'])['app'], 'CSP')
        self.assertIn('session', json.loads(replies[3]['result']['content'][0]['text']))
        self.assertEqual(replies[4]['error']['code'], -32602)


class ControlTests(unittest.TestCase):
    def test_panel_and_pause_persistence(self):
        with tempfile.TemporaryDirectory() as temp:
            class Source:
                def sample(self):
                    return CSP
            c = Collector(Path(temp), Source())
            server = make_server(c, 0)
            port = server.server_address[1]
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            def request(method, path, headers=None):
                connection = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
                connection.request(method, path, headers={'Host': '127.0.0.1:0', **(headers or {})})
                response = connection.getresponse()
                value = (response.status, response.read().decode())
                connection.close()
                return value
            try:
                self.assertTrue(c.paused)
                status, page = request('GET', '/')
                self.assertEqual(status, 200)
                token = re.search(r"const token='([^']+)'", page)[1]
                self.assertEqual(request('POST', '/resume')[0], 403)
                self.assertEqual(request('GET', '/', {'Host': 'evil.example'})[0], 403)
                self.assertEqual(request('POST', '/resume', {'X-Beside-Token': token, 'Origin': 'http://evil.example'})[0], 403)
                self.assertEqual(request('POST', '/resume', {'X-Beside-Token': token})[0], 200)
                self.assertFalse(c.paused)
                self.assertEqual(request('POST', '/pause', {'X-Beside-Token': token})[0], 200)
                self.assertTrue(c.paused)
                self.assertEqual(request('POST', '/clear', {'X-Beside-Token': token})[0], 200)
                self.assertEqual(c.tracker.totals, {})
            finally:
                server.shutdown()
                server.server_close()
                c.close()
            again = Collector(Path(temp), Source())
            self.assertTrue(again.paused)
            again.close()


if __name__ == '__main__':
    unittest.main(verbosity=2)
