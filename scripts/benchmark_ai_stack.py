"""One lightweight run per machine; no optimization or accuracy claims."""
import argparse
import base64
import json
import platform
import sys
import time
import urllib.request
import wave
from pathlib import Path
from ai_common import ROOT, BASE_URL, api, chat, save
from check_ai_stack import TOOL, SCHEMA, image_message, whisper


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--image', help='Representative local image; omitted means YOLO benchmark is skipped')
    parser.add_argument('--audio', help='Local mono 16 kHz WAV; defaults to upstream JFK sample')
    args=parser.parse_args()
    report={'machine':platform.system()+'_'+platform.machine(),'method':'Single run; cold means model unloaded, OS file cache not cleared. No accuracy measurement.','results':{}}
    def measure(name,fn):
        try:
            report['results'][name]={'status':'PASS',**fn()}
        except Exception as exc:
            report['results'][name]={'status':'FAIL','error':type(exc).__name__}
        print(name,report['results'][name],flush=True)
    def language():
        api('generate',{'model':'qwen3:8b','keep_alive':0})
        payload={'model':'qwen3:8b','think':False,'stream':True,'options':{'temperature':0,'num_predict':100,'num_ctx':8192},
            'messages':[{'role':'user','content':'Explain in two short sentences why classroom AV actions need human override.'}]}
        start=time.perf_counter();first=None;final=None
        req=urllib.request.Request(BASE_URL+'/api/chat',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=180) as stream:
            for line in stream:
                event=json.loads(line)
                if first is None and event.get('message',{}).get('content'):
                    first=time.perf_counter()-start
                if event.get('done'):
                    final=event
        assert final and first is not None
        elapsed=time.perf_counter()-start
        start=time.perf_counter()
        tool=chat('qwen3:8b','Call camera_focus with target instructor.',tools=[TOOL])
        assert tool['message'].get('tool_calls')
        return {'cold_request_seconds':elapsed,'model_load_seconds':final['load_duration']/1e9,
            'first_token_seconds':first,'tokens_per_second':final['eval_count']/(final['eval_duration']/1e9),
            'structured_tool_call_seconds':time.perf_counter()-start}
    measure('qwen3:8b',language)
    def vision_language():
        start=time.perf_counter()
        messages=image_message()
        if args.image:
            messages[0]['images']=[base64.b64encode(Path(args.image).read_bytes()).decode()]
            messages[0]['content']='Classify classroom activity as LECTURE or UNKNOWN. Use UNKNOWN without classroom evidence.'
        result=chat('qwen3-vl:2b-instruct','',messages=messages,format=SCHEMA)
        activity=json.loads(result['message']['content'])['activity']
        assert activity in ('LECTURE','UNKNOWN')
        return {'one_frame_seconds':time.perf_counter()-start,'activity':activity,
                'fixture':'provided image' if args.image else 'synthetic blank frame; schema/ingestion only'}
    measure('qwen3-vl:2b-instruct',vision_language)
    def speech():
        path=args.audio or ROOT/'vendor/whisper.cpp/samples/jfk.wav'
        with wave.open(str(path)) as wav:
            duration=wav.getnframes()/wav.getframerate()
        start=time.perf_counter();text=whisper().transcribe(path);elapsed=time.perf_counter()-start
        assert text
        return {'seconds':elapsed,'audio_seconds':duration,'real_time_factor':elapsed/duration,'includes_model_load':True}
    measure('whisper_small.en',speech)
    def vision():
        import cv2
        from app.services.vision import UltralyticsPeople
        frame=cv2.imread(args.image)
        if frame is None:
            raise ValueError('Cannot read image')
        adapter=UltralyticsPeople(ROOT/'models/vision/yolo26n.pt')
        observations=adapter.detect(frame)
        start=time.perf_counter()
        for _ in range(10):
            adapter.detect(frame)
        elapsed=time.perf_counter()-start
        return {'fps':10/elapsed,'iterations':10,'device':'cpu','people_detected':len(observations),'frame_dimensions':list(frame.shape),'note':'warm frame inference, excludes video decode; provided image'}
    if args.image:
        measure('yolo26n',vision)
    else:
        report['results']['yolo26n']={'status':'SKIPPED','reason':'Provide --image; no classroom image assumed'}
    save('benchmark_'+report['machine'].lower()+'.json',report)

if __name__=='__main__':
    main()
