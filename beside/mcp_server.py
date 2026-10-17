"""Read-only MCP over stdio. Does not start collection or schedule the assistant."""
import argparse
import json
import sys
from pathlib import Path
from presence import read_presence

TOOLS = [
    {'name': 'get_presence', 'description': 'Read the latest local creative-app presence. Check stale and observed_at. This does not show the artwork or wake the assistant.',
     'inputSchema': {'type': 'object', 'properties': {}, 'additionalProperties': False},
     'annotations': {'readOnlyHint': True, 'destructiveHint': False, 'openWorldHint': False}},
    {'name': 'get_creative_session', 'description': 'Read approximate CSP/Blender foreground session and today totals, excluding recent no-input intervals. No scores or productivity judgments.',
     'inputSchema': {'type': 'object', 'properties': {}, 'additionalProperties': False},
     'annotations': {'readOnlyHint': True, 'destructiveHint': False, 'openWorldHint': False}},
]


def handle(message, data_dir):
    if not isinstance(message, dict) or message.get('jsonrpc') != '2.0' or not isinstance(message.get('method'), str):
        return {'jsonrpc': '2.0', 'id': None, 'error': {'code': -32600, 'message': 'Invalid Request'}}
    method = message['method']
    if 'id' not in message:
        return None
    rid = message['id']
    base = {'jsonrpc': '2.0', 'id': rid}
    if method == 'initialize':
        version = message.get('params', {}).get('protocolVersion')
        supported = {'2024-11-05', '2025-03-26', '2025-06-18', '2025-11-25'}
        return {**base, 'result': {'protocolVersion': version if version in supported else '2025-06-18',
                                  'capabilities': {'tools': {}}, 'serverInfo': {'name': 'beside', 'version': '0.1.0'},
                                  'instructions': 'Read-only metadata for companionship. Respect paused/stopped/stale. No artwork visibility. Collector does not imply assistant presence.'}}
    if method == 'ping':
        return {**base, 'result': {}}
    if method == 'tools/list':
        return {**base, 'result': {'tools': TOOLS}}
    if method == 'tools/call':
        params = message.get('params', {})
        if (not isinstance(params, dict) or params.get('name') not in {t['name'] for t in TOOLS}
                or params.get('arguments', {}) != {}):
            return {**base, 'error': {'code': -32602, 'message': 'Unknown tool or invalid arguments'}}
        result = read_presence(data_dir)
        if params['name'] == 'get_creative_session':
            result = {k: v for k, v in result.items() if k in {'state', 'stale', 'observed_at', 'age_seconds', 'session', 'local_date', 'today_foreground_seconds', 'meaning', 'reason'}}
        return {**base, 'result': {'content': [{'type': 'text', 'text': json.dumps(result, ensure_ascii=False)}], 'isError': False}}
    return {**base, 'error': {'code': -32601, 'message': 'Method not found'}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-dir', type=Path, default=Path(__file__).resolve().parent / 'data')
    args = parser.parse_args()
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        stream.reconfigure(encoding='utf-8')
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            if len(line) > 65536:
                raise ValueError('Message too large')
            message = json.loads(line)
            response = handle(message, args.data_dir)
        except (ValueError, TypeError, AttributeError):
            response = {'jsonrpc': '2.0', 'id': None, 'error': {'code': -32700, 'message': 'Parse error'}}
        if response is not None:
            print(json.dumps(response, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
