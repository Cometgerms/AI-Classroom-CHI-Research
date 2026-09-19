"""Small, user-facing action feed; deliberately independent of research event logs."""
from collections import deque
from datetime import datetime, timezone
from uuid import uuid4

TARGETS={'instructor':'Presenter','presenter':'Presenter','wide':'Wide','demo_zone':'Demo area'}
SOURCES={'presentation':'Instructor laptop','room_pc':'Room PC','camera':'Camera / program','blank':'Blank'}
AUDIO={'lecture':'Presentation','media':'Media','mute':'Muted','discussion':'Discussion'}
LAYOUTS={'slides_plus_instructor':'Slides + presenter','demo_primary':'Demonstration','media_primary':'Media','wide':'Wide','q_and_a':'Conversation'}
FIELDS={'camera_focus':('camera_target','target'),'camera_set_follow':('camera_mode','enabled'),
        'display_set_source':('display_source','source'),'audio_set_mode':('audio_mode','mode'),
        'recording_set_layout':('recording_layout','layout')}
events=deque(maxlen=20)

def action_label(action):
    t,a=action.tool,action.args
    if t=='camera_focus': return 'Camera → '+TARGETS.get(a['target'],'Other framing')
    if t=='camera_set_follow': return 'Follow presenter '+('on' if a['enabled'] else 'off')
    if t=='display_set_source': return 'Display → '+SOURCES[a['source']]
    if t=='audio_set_mode': return 'Audio → '+AUDIO[a['mode']]
    if t=='recording_set_layout': return 'Program layout → '+LAYOUTS[a['layout']]
    if t=='recording_start': return 'Recording started'
    if t=='recording_stop': return 'Recording stopped'
    return 'Audio updated'

def record_action(action,before,after,actor,simulated):
    if before==after: return
    field,argument=FIELDS.get(action.tool,(None,None))
    inverse=None
    if simulated and field:
        previous=getattr(before,field)
        if action.tool=='camera_set_follow': previous=previous=='follow'
        inverse={'tool':action.tool,'args':{argument:previous}}
    restore=None
    expected=None
    if simulated and action.tool in ('camera_focus','camera_set_follow'):
        restore=[{'tool':'camera_focus','args':{'target':before.camera_target}},
                 {'tool':'camera_set_follow','args':{'enabled':before.camera_mode=='follow'}}]
        expected={'camera_target':after.camera_target,'camera_mode':after.camera_mode}
        # A semantic instructor alias is equivalent to presenter during follow.
    events.appendleft({'id':str(uuid4()),'time':datetime.now(timezone.utc).isoformat(),
        'label':action_label(action),'actor':actor,'inverse':inverse,'field':field,
        'after':getattr(after,field) if field else None,'restore':restore,'expected':expected})

def public_events():
    return [{k:event[k] for k in ('id','time','label','actor')} | {'canUndo':bool(index==0 and event['inverse'])}
            for index,event in enumerate(events)]
