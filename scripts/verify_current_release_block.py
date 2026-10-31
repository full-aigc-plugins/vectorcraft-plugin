#!/usr/bin/env python3
"""Assert that archived release evidence cannot qualify the current candidate."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
candidate = json.loads((ROOT / 'plugin.json').read_text())['version']
bundle = json.loads((ROOT / 'docs/release-evidence.json').read_text())
if candidate == bundle['pluginVersion']:
    raise SystemExit('release evidence now claims the current version; run the real six-layer gate')
result = subprocess.run(
    [sys.executable, '-I', '-B', str(ROOT / 'scripts/release_gate.py'), '--require', 'development'],
    cwd=ROOT, capture_output=True, text=True, check=False,
)
try:
    status = json.loads(result.stdout)
except json.JSONDecodeError as error:
    raise SystemExit(f'release gate did not return a readable status: {error}') from error
if result.returncode != 1 or status['publishable']['development'] is not False:
    raise SystemExit('archived release evidence must not qualify the current candidate')
if not any(layer.get('reason') == 'release_evidence_changed' for layer in status['layers'].values()):
    raise SystemExit('release gate refusal lacks the expected stale-evidence reason')
print(json.dumps({'result': 'PASS', 'currentVersion': candidate, 'archivedVersion': bundle['pluginVersion'], 'developmentPublishable': False}))
