"""Run actual local inference, not just import/weight-presence checks."""
import argparse
import base64
import json
import os
from pathlib import Path
import platform
import sys
import time
from ai_common import ROOT, api, chat, save
sys.path.insert(0, str(ROOT / 'backend'))

TOOL = {'type':'function', 'function':{'name':'camera_focus', 'description':'Frame a named classroom target',
    'parameters':{'type':'object','properties':{'target':{'type':'string','enum':['instructor','wide']}},'required':['target']}}}
SCHEMA = {'type':'object','properties':{'activity':{'type':'string','enum':['LECTURE','UNKNOWN']}},'required':['activity'],'additionalProperties':False}

def image_message():
    # Tiny deterministic fixture: verifies image ingestion/schema, not classroom accuracy.
    import struct, zlib
    def chunk(kind, data):
        return struct.pack('!I',len(data))+kind+data+struct.pack('!I',zlib.crc32(kind+data)&0xffffffff)
    png = b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',64,64,8,2,0,0,0))
    png += chunk(b'IDAT',zlib.compress((b'\x00'+b'\xff\xff\xff'*64)*64))+chunk(b'IEND',b'')
    return [{'role':'user','content':'Classify classroom activity in this image as LECTURE or UNKNOWN. A blank image is UNKNOWN.', 'images':[base64.b64encode(png).decode()]}]

def check_room():
    r=chat('qwen3:8b','Reply with exactly READY.')
    assert 'READY' in r['message']['content'].upper(), 'Chat answer missing READY'
    r=chat('qwen3:8b','Return JSON activity LECTURE.',format=SCHEMA)
    assert json.loads(r['message']['content']) == {'activity':'LECTURE'}
    r=chat('qwen3:8b','Call camera_focus now with target instructor.', tools=[TOOL])
    calls=r['message'].get('tool_calls',[])
    assert any(c['function']['name']=='camera_focus' and c['function']['arguments']=={'target':'instructor'} for c in calls), 'No valid tool call'
    return 'chat + structured JSON + typed tool call'

def check_vision_language():
    r=chat('qwen3-vl:2b-instruct','',messages=image_message(),format=SCHEMA)
    assert json.loads(r['message']['content']) == {'activity':'UNKNOWN'}
    return 'image input + structured classification (blank fixture; not accuracy validation)'

def whisper():
    from app.services.stt import WhisperCppSpeechToText
    exe=Path(os.environ.get('WHISPER_CPP_BIN', ROOT/'vendor/whisper.cpp/build/bin'/('Release/whisper-cli.exe' if os.name=='nt' else 'whisper-cli')))
    model=Path(os.environ.get('WHISPER_MODEL', ROOT/'models/whisper/ggml-small.en.bin'))
    return WhisperCppSpeechToText(exe,model)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--skip-ollama',action='store_true')
    args=parser.parse_args()
    results=[]
    def run(name, fn, required=False):
        start=time.perf_counter()
        try:
            detail=fn()
            status='PASS'
        except Exception as exc:
            status,detail='FAIL',type(exc).__name__
            print(f'{name}: {status} ({exc})',flush=True)
        else:
            print(f'{name}: {status} ({detail})',flush=True)
        results.append(dict(component=name,status=status,detail=detail,required=required,seconds=round(time.perf_counter()-start,3)))
    if not args.skip_ollama:
        run('Ollama',lambda:api('version')['version'],True)
        run('qwen3:8b',check_room,True)
        run('qwen3-vl:2b-instruct',check_vision_language)
    def stt_binary():
        import subprocess
        subprocess.run([str(whisper().executable),'--help'],check=True,capture_output=True,timeout=15)
        return 'CLI launched'
    run('whisper.cpp',stt_binary)
    def stt_model():
        text=whisper().transcribe(ROOT/'vendor/whisper.cpp/samples/jfk.wav')
        assert 'country' in text.lower(), 'Sample transcript mismatch'
        return 'small.en transcribed upstream JFK sample'
    run('small.en',stt_model)
    def vad():
        from app.services.vad import SileroVoiceActivityDetector
        detector=SileroVoiceActivityDetector()
        assert detector.process([0.0]*512)==[]
        import wave, struct
        sample=ROOT/'vendor/whisper.cpp/samples/jfk.wav'
        if not sample.is_file():
            return 'independent silence inference; speech fixture unavailable'
        with wave.open(str(sample)) as wav:
            raw=wav.readframes(wav.getnframes())
        values=[x/32768 for x in struct.unpack('<'+'h'*(len(raw)//2),raw)]
        values += [0.0]*16000
        kinds=set()
        for offset in range(0,len(values)-511,512):
            kinds.update(e.kind for e in detector.process(values[offset:offset+512]))
        assert {'speech_started','speech_active','speech_ended'} <= kinds
        return 'silence plus all three speech events on upstream JFK sample'
    run('Silero',vad)
    run('Ultralytics',lambda:__import__('ultralytics').__version__)
    def yolo(pose=False):
        import numpy as np
        from app.services.vision import UltralyticsPeople, UltralyticsPose
        weights=ROOT/'models/vision'/('yolo26n-pose.pt' if pose else 'yolo26n.pt')
        if not weights.is_file():
            raise FileNotFoundError('Run bootstrap_models.py --perception')
        adapter=(UltralyticsPose if pose else UltralyticsPeople)(weights)
        result=(adapter.estimate if pose else adapter.track)(np.zeros((480,640,3),dtype=np.uint8))
        assert isinstance(result,list)
        return 'loaded weights + blank-frame inference'
    run('yolo26n',yolo)
    run('yolo26n-pose',lambda:yolo(True))
    results.append(dict(component='ODAS',status='SKIPPED',required=False,detail='Native adapter and microphone calibration deferred'))
    print('ODAS: SKIPPED (see platform setup guide)')
    save('ai_stack_'+platform.system().lower()+'_'+platform.machine()+'.json',results)
    return int(any(r['status']=='FAIL' and r['required'] for r in results))

if __name__=='__main__':
    sys.exit(main())
