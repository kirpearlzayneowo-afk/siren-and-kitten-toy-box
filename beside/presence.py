"""Minimal creative-app presence. No window text or input content is collected."""
from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

CREATIVE_APPS = {
    'clipstudiopaint.exe': 'CSP',
    'udmpaintex.exe': 'CSP',
    'udmpaintpro.exe': 'CSP',
    'blender.exe': 'Blender',
}
ALLOWED_APPS = {'CSP', 'Blender', 'other', None}
ALLOWED_STATES = {'active', 'idle', 'locked', 'unknown', 'paused', 'stopped'}
IDLE_SECONDS = 180
MAX_GAP_SECONDS = 12
STALE_SECONDS = 20
SESSION_GRACE_SECONDS = 30


def classify(executable: str) -> str:
    # Never return or persist the raw executable or path.
    return CREATIVE_APPS.get(executable.replace('\\', '/').rsplit('/', 1)[-1].lower(), 'other')


@dataclass(frozen=True)
class Observation:
    app: str | None
    state: str

    def __post_init__(self):
        if self.app not in ALLOWED_APPS or self.state not in ALLOWED_STATES:
            raise ValueError('Unrecognized presence category')


def iso(now: datetime) -> str:
    return now.isoformat(timespec='milliseconds')


def split_days(start: datetime, seconds: float):
    """Split a bounded monotonic interval at local wall-clock midnight."""
    remaining = seconds
    cursor = start
    while remaining > 0.000001:
        midnight = (cursor + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        part = min(remaining, (midnight - cursor).total_seconds())
        yield cursor.date().isoformat(), part
        remaining -= part
        cursor += timedelta(seconds=part)


class Tracker:
    def __init__(self, totals=None):
        self.totals = totals or {}
        self.previous = None
        self.session = None
        self.last_creative_mono = None

    def clear(self):
        self.totals = {}
        self.previous = None
        self.session = None
        self.last_creative_mono = None

    def update(self, observation: Observation, wall: datetime, mono: float):
        increments = []
        valid_interval = False
        elapsed = 0
        if self.previous:
            old_obs, old_wall, old_mono = self.previous
            elapsed = mono - old_mono
            wall_elapsed = (wall - old_wall).total_seconds()
            valid_interval = (0 < elapsed <= MAX_GAP_SECONDS and abs(wall_elapsed - elapsed) <= 2)
            if (valid_interval and old_obs.state == 'active' and observation.state == 'active'
                    and old_obs.app == observation.app and observation.app in {'CSP', 'Blender'}):
                for day, amount in split_days(old_wall, elapsed):
                    totals = self.totals.setdefault(day, {'CSP': 0.0, 'Blender': 0.0})
                    totals[observation.app] += amount
                    increments.append((day, observation.app, amount))

        if not valid_interval and self.previous:
            self.session = None
            self.last_creative_mono = None

        if observation.state == 'active' and observation.app in {'CSP', 'Blender'}:
            if (not self.session or self.session['app'] != observation.app
                    or self.last_creative_mono is None
                    or mono - self.last_creative_mono > SESSION_GRACE_SECONDS):
                self.session = {'app': observation.app, 'started_at': iso(wall), 'foreground_seconds': 0.0}
            if (valid_interval and self.previous and self.previous[0] == observation):
                self.session['foreground_seconds'] += elapsed
            self.last_creative_mono = mono
        elif observation.state in {'paused', 'locked', 'unknown', 'stopped', 'idle'}:
            self.session = None
            self.last_creative_mono = None

        cutoff = (wall.date() - timedelta(days=6)).isoformat()
        self.totals = {day: value for day, value in self.totals.items() if cutoff <= day <= wall.date().isoformat()}
        self.previous = (observation, wall, mono)
        return self.snapshot(observation, wall), increments

    def snapshot(self, observation, wall):
        session = None
        if self.session and observation.state == 'active' and observation.app == self.session['app']:
            session = {**self.session, 'foreground_seconds': round(self.session['foreground_seconds'], 1)}
        return {
            'schema': 'beside.presence.v1', 'observed_at': iso(wall),
            'app': observation.app, 'state': observation.state,
            'session': session, 'local_date': wall.date().isoformat(),
            'today_foreground_seconds': {
                app: round(self.totals.get(wall.date().isoformat(), {}).get(app, 0), 1)
                for app in ('CSP', 'Blender')
            },
            'meaning': 'Foreground app only; no artwork, window title, or input content. Idle means no recent input, not absence of creative work.',
        }


def atomic_json(target: Path, value):
    temp = target.with_suffix('.tmp')
    with temp.open('w', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False)
        stream.flush()
    os.replace(temp, target)


def read_presence(data_dir: Path, now=None):
    """Return a whitelisted view; never expose arbitrary stored JSON fields."""
    now = now or datetime.now().astimezone()
    try:
        raw = json.loads((data_dir / 'presence.json').read_text(encoding='utf-8'))
        if not isinstance(raw, dict):
            raise ValueError('Invalid snapshot object')
        stamp = datetime.fromisoformat(raw['observed_at'])
        if stamp.tzinfo is None or raw.get('schema') != 'beside.presence.v1':
            raise ValueError('Invalid snapshot')
        age = (now - stamp).total_seconds()
        stale = age < -2 or age > STALE_SECONDS
        state = raw.get('state')
        if state not in ALLOWED_STATES:
            raise ValueError('Invalid state')
        app = raw.get('app') if raw.get('app') in ALLOWED_APPS else None
        session = raw.get('session')
        safe_session = None
        if isinstance(session, dict) and session.get('app') in {'CSP', 'Blender'}:
            seconds = float(session.get('foreground_seconds', 0))
            started = datetime.fromisoformat(session['started_at'])
            if (math.isfinite(seconds) and seconds >= 0 and started.tzinfo is not None
                    and session['app'] == app and started <= stamp):
                safe_session = {'app': session['app'], 'started_at': iso(started), 'foreground_seconds': seconds}
        totals = {}
        for label in ('CSP', 'Blender'):
            amount = float(raw.get('today_foreground_seconds', {}).get(label, 0))
            if not math.isfinite(amount) or amount < 0:
                raise ValueError('Invalid duration')
            totals[label] = amount if raw.get('local_date') == now.date().isoformat() else 0
        return {
            'schema': 'beside.presence.v1', 'observed_at': iso(stamp),
            'age_seconds': round(max(0, age), 1), 'stale': stale,
            'state': 'stale' if stale else state,
            'app': app if not stale and state in {'active', 'idle'} else None,
            'session': safe_session if not stale and state == 'active' else None,
            'local_date': now.date().isoformat(), 'today_foreground_seconds': totals,
            'meaning': 'Sampled foreground app, not visible artwork. Idle only means no recent input. This tool does not wake or continuously run the assistant.',
        }
    except (OSError, ValueError, TypeError, KeyError, OverflowError, AttributeError):
        return {'schema': 'beside.presence.v1', 'state': 'unknown', 'app': None,
                'session': None, 'stale': True, 'reason': 'No valid recent collector snapshot.'}
