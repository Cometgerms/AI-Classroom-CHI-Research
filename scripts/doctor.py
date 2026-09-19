"""Read-only capability report. No automatic microphone recording or camera opening."""
import argparse
import asyncio
import importlib.util
import json
import platform
import sys
from pathlib import Path
from ai_common import ROOT,api,save
from environment_report import collect
sys.path.insert(0,str(ROOT/'backend'))
from app.runtime_config import load_config
from app.services.audio.xvf3800.audio import discover
from app.services.audio.xvf3800.control import XVF3800Control
from app.services.audio.xvf3800.parser import parse_doa,parse_energy
from check_ai_stack import whisper

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--profile',default=None)
    parser.add_argument('--probe-camera',action='store_true',help='Open candidate camera devices briefly; may request OS permission')
    args=parser.parse_args()
    config=load_config(profile=args.profile)
    results={}
    def probe(name,fn):
        try:
            detail=fn(); ok=True
        except Exception as exc: detail=type(exc).__name__+': '+str(exc);ok=False
        results[name]={'status':'PASS' if ok else 'UNAVAILABLE','detail':detail}
        print(f'  {name:28} {results[name]["status"]} {detail}')
        return ok
    print('Agentic Classroom Developer Doctor')
    facts=collect()
    print(f"Platform: {facts['os']} {facts['architecture']}; RAM {facts['system_ram_bytes']}")
    print(f"GPU: {facts['gpu']}; GPU memory: {facts['gpu_memory_bytes']}; driver CUDA: {facts['cuda_version']}")
    def accel(name):
        import torch
        available=torch.backends.mps.is_available() if name=='MPS' else torch.cuda.is_available()
        if not available: raise RuntimeError('not available in this interpreter')
        return True
    probe('MPS',lambda:accel('MPS'));probe('CUDA',lambda:accel('CUDA'))
    ollama=probe('Ollama',lambda:api('version',timeout=3)['version'])
    def model():
        tags={m['name'] for m in api('tags',timeout=3)['models']}
        if config['agent']['model'] not in tags: raise RuntimeError('required model absent')
        return config['agent']['model']
    model_ok=probe('Qwen3 model',model)
    def stt():
        import subprocess
        instance=whisper()
        if not instance.model.is_file(): raise FileNotFoundError('Whisper small.en weights absent')
        subprocess.run([str(instance.executable),'--help'],check=True,capture_output=True,timeout=10)
        return 'whisper.cpp + model present (run stack check for inference)'
    stt_ok=probe('Whisper',stt)
    def audio_devices():
        import sounddevice as sd
        # Device names are displayed locally; not persisted in machine reports.
        return [d['name'] for d in sd.query_devices() if d['max_input_channels']>0]
    probe('Audio input devices',audio_devices)
    def uac():
        profile=discover(config['audio'])
        return {'sample_rate':profile.sample_rate,'channels':profile.channels}
    uac_ok=probe('XVF UAC',uac)
    vendor=Path(config['xvf3800']['vendor_dir'])
    if not vendor.is_absolute(): vendor=ROOT/vendor
    control=XVF3800Control(vendor)
    try:
        control_ok=probe('XVF control VERSION',control.get_version)
        doa_ok=probe('XVF DoA',lambda:parse_doa(control.get_doa()))
        energy_ok=probe('XVF speech energy',lambda:parse_energy(control.get_speech_energy()))
    finally: control.close()
    def enumerate_cameras():
        import subprocess
        if platform.system()=='Darwin':
            result=subprocess.check_output(['system_profiler','SPCameraDataType','-json'],text=True,timeout=20)
            count=len(json.loads(result).get('SPCameraDataType',[]))
        elif platform.system()=='Windows':
            result=subprocess.check_output(['powershell','-NoProfile','-Command',
                '@(Get-PnpDevice -PresentOnly | Where-Object {$_.Class -in "Camera","Image"}).Count'],text=True,timeout=20)
            count=int(result.strip())
        else:
            count=len(list(Path('/dev').glob('video*')))
        if not count: raise RuntimeError('No camera device enumerated')
        return f'{count} camera device(s); stream access not tested'
    probe('Camera enumeration',enumerate_cameras)
    camera_ok=False
    if args.probe_camera:
        def cameras():
            import cv2
            found=[]
            for index in range(5):
                capture=cv2.VideoCapture(index)
                try:
                    if capture.isOpened() and capture.read()[0]: found.append(index)
                finally: capture.release()
            if not found: raise RuntimeError('No readable camera in probed candidates')
            return f'{len(found)} readable camera(s); indices are not persisted'
        camera_ok=probe('Camera capture',cameras)
    else:
        results['Camera capture']={'status':'NOT_TESTED','detail':'Use --probe-camera to test access; camera enumeration is backend-dependent'}
        print('  Camera capture               NOT_TESTED (use --probe-camera)')
    def yolo():
        if importlib.util.find_spec('ultralytics') is None: raise RuntimeError('Ultralytics absent')
        if not (ROOT/'models/vision/yolo26n.pt').is_file(): raise RuntimeError('YOLO nano weights absent')
        return 'package + weights present; run stack check for inference'
    yolo_ok=probe('Person tracking',yolo)
    core=all(importlib.util.find_spec(name) for name in ('fastapi','pydantic','yaml','httpx','uvicorn'))
    calibrated=config['audio']['speech_activity']['energy_threshold'] is not None
    audio_ready=uac_ok and energy_ok and calibrated  # DoA is optional for instructor-only V1.
    readiness={'Simulation basic':bool(core),'Simulation AI':bool(core and ollama and model_ok),
        'XVF hybrid':bool(core and audio_ready and stt_ok),
        'Full hardware':False}  # Physical output adapters are not implemented.
    if not calibrated: print('  Speech threshold             NEEDS_CALIBRATION (local.yaml)')
    print('Ready (prerequisites; not proof of a live end-to-end pipeline):')
    for name,ok in readiness.items(): print(f'  {name:28} {"READY" if ok else "NOT READY"}')
    # Persist only statuses/readiness and allowlisted environment facts. No device names/paths/errors.
    save('doctor_'+platform.system().lower()+'_'+platform.machine()+'.json',
         {'environment':facts,'checks':{k:v['status'] for k,v in results.items()},'ready':readiness})
    return 0 if core else 1

if __name__=='__main__':sys.exit(main())
