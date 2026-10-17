"""Read-only smoke test of the registered stdio command against live local state."""
import json
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
messages = [
    {'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {'protocolVersion': '2025-06-18', 'capabilities': {}, 'clientInfo': {'name': 'beside-live-check', 'version': '0.1'}}},
    {'jsonrpc': '2.0', 'method': 'notifications/initialized'},
    {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list'},
    {'jsonrpc': '2.0', 'id': 3, 'method': 'tools/call', 'params': {'name': 'get_presence', 'arguments': {}}},
]
p = subprocess.run([sys.executable, str(root / 'mcp_server.py')], input='\n'.join(map(json.dumps, messages))+'\n', capture_output=True, text=True, encoding='utf-8', timeout=10)
p.check_returncode()
replies = [json.loads(line) for line in p.stdout.splitlines()]
assert len(replies) == 3
assert len(replies[1]['result']['tools']) == 2
presence = json.loads(replies[2]['result']['content'][0]['text'])
assert presence['stale'] is False, presence
print(json.dumps({'transport': 'stdio', 'tools': 2, 'presence': presence}, ensure_ascii=False))
