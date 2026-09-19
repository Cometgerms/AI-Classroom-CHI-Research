"""Small standard-library helpers; these scripts do not import optional ML packages."""
import json
import os
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434').rstrip('/')

def manifest():
    # JSON is a YAML 1.2 subset, so no YAML dependency is needed to bootstrap.
    return json.loads((ROOT / 'config/models.yaml').read_text())

def api(path, payload=None, timeout=180):
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(BASE_URL + '/api/' + path, data=data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.load(response)

def chat(model, prompt, **kwargs):
    return api('chat', {'model': model, 'stream': False, 'think': False,
        'options': {'temperature': 0, 'num_ctx': 8192},
        'messages': [{'role': 'user', 'content': prompt}], **kwargs})

def save(name, value):
    dest = ROOT / 'artifacts' / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(value, indent=2) + '\n')
