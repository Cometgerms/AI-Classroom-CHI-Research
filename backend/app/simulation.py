"""Data-driven sensor timelines. No semantic activity labels in ordinary scenarios."""
from pathlib import Path
import yaml
from .runtime_config import ROOT, merge
from .observations import ObservationFrame

DIRECTORY=ROOT/'config/scenarios'
def catalog(): return sorted(p.stem for p in DIRECTORY.glob('*.yaml') if not p.name.startswith('._'))
def load_scenario(name):
    name={'lecture':'lecture_start','reset':'lecture_start'}.get(name,name)
    if name not in catalog(): raise KeyError(name)
    data=yaml.safe_load((DIRECTORY/f'{name}.yaml').read_text())
    if data['version']!=1: raise ValueError('Unsupported scenario version')
    return data

def frames(data):
    tick=data['tick_seconds'];duration=data['duration']
    if not .02<=tick<=1 or not 0<duration<=600: raise ValueError('Invalid timeline bounds')
    events=data['events']
    if not events or events[0]['at']!=0 or any(a['at']>b['at'] for a,b in zip(events,events[1:])):
        raise ValueError('Timeline must start at zero and be ordered')
    current={};index=0
    for step in range(round(duration/tick)+1):
        t=round(step*tick,6)
        while index<len(events) and events[index]['at']<=t:
            current=merge(current,events[index]);index+=1
        yield ObservationFrame.model_validate(dict(timestamp=t,
            audio=dict(timestamp=t,source='simulation',**current.get('audio',{})),
            vision=dict(timestamp=t,source='simulation',camera_available=current.get('camera_available',True),
                        tracks=[dict(timestamp=t,**track) for track in current.get('tracks',[])]),scene=current.get('scene',{})))
