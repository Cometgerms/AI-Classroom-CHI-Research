"""Platform-independent layered config; no hardware libraries imported here."""
from copy import deepcopy
from pathlib import Path
import os
import platform
import yaml

ROOT = Path(__file__).resolve().parents[2]
PROFILES = ('simulation-basic','simulation-ai','hybrid','hardware','study','simulation','mac-local','windows-local','hardware-xvf')
ALIASES = {'simulation':'simulation-basic','mac-local':'hybrid','windows-local':'hybrid','hardware-xvf':'hybrid'}

def merge(base, override):
    result = deepcopy(base)
    for key, value in override.items():
        result[key] = merge(result[key], value) if isinstance(value, dict) and isinstance(result.get(key), dict) else deepcopy(value)
    return result

def load_config(root=ROOT, profile=None, environ=None, system=None):
    env = os.environ if environ is None else environ
    root = Path(root)
    platform_name = {'Darwin':'macos','Windows':'windows','Linux':'linux'}.get(system or platform.system(), 'linux')
    def read(path):
        if not path.is_file(): return {}
        value = yaml.safe_load(path.read_text()) or {}
        if not isinstance(value, dict): raise ValueError(f'Expected config mapping: {path.name}')
        return value
    config = merge(read(root/'config/default.yaml'), read(root/f'config/platform/{platform_name}.yaml'))
    config = merge(config, read(root/'config/local.yaml'))
    selected = profile or env.get('CLASSROOM_PROFILE') or config['runtime']['profile']
    if selected:
        if selected not in PROFILES: raise ValueError('Unknown developer profile')
        original = selected
        selected = ALIASES.get(selected,selected)
        config = merge(config, read(root/f'config/profiles/{selected}.yaml'))
        if original in ('mac-local','windows-local','hardware-xvf'):
            config['hardware']['audio']='xvf3800'
    # CLASSROOM_AUDIO__POLL_HZ=10 etc; all scalar/list/mapping values parsed as YAML.
    for name, value in env.items():
        if not name.startswith('CLASSROOM_') or name == 'CLASSROOM_PROFILE': continue
        parts = name[len('CLASSROOM_'):].lower().split('__')
        if len(parts)<2: continue
        target = config
        for key in parts[:-1]: target = target.setdefault(key,{})
        target[parts[-1]] = yaml.safe_load(value)
    for name, path in {'AGENT_BACKEND':('agent','backend'),'OLLAMA_MODEL':('agent','model'),'OLLAMA_BASE_URL':('agent','base_url')}.items():
        if name in env: config[path[0]][path[1]] = env[name]
    if config['hardware']['mode'] not in ('simulation','hybrid','real'): raise ValueError('Invalid hardware mode')
    if not 1 <= config['audio']['poll_hz'] <= 20: raise ValueError('audio.poll_hz must be 1–20')
    if config['audio']['speech_activity_backend'] not in ('xvf','silero'): raise ValueError('Unknown speech activity backend')
    allowed={'audio':{'auto','simulation','xvf3800'},'camera':{'simulation','real'},
             'projector':{'simulation','pjlink'},'recorder':{'simulation','obs'},
             'camera_control':{'simulation','ptz'},'audio_output':{'simulation','real'}}
    for name, choices in allowed.items():
        if config['hardware'][name] not in choices: raise ValueError(f'Unknown {name} adapter')
    current=config['runtime']['profile']
    if current in ('simulation-basic','simulation-ai','study'):
        if any(config['hardware'][name]!='simulation' for name in allowed):
            raise ValueError('Simulation/study profiles require simulated adapters; use hybrid for hardware')
    if current=='simulation-basic' and config['agent']['backend'] not in ('fake','rule'):
        raise ValueError('simulation-basic requires a deterministic agent; clear AGENT_BACKEND override')
    if current=='simulation-ai':
        if config['agent']['backend']!='ollama': raise ValueError('simulation-ai requires Ollama; clear AGENT_BACKEND override')
        config['agent']['strict']=True
    return config

def audio_backend(config):
    if config['hardware']['mode']=='simulation': return 'simulation'
    chosen=config['hardware'].get('audio','auto')
    return config['audio']['frontend'] if chosen=='auto' else chosen
