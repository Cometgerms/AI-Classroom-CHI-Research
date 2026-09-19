"""Telemetry overhead and normalized state-change→simulated action, kept separate."""
import argparse
import asyncio
from dataclasses import replace
import platform
import statistics
import sys
import tempfile
import time
from pathlib import Path
from ai_common import ROOT,save
sys.path.insert(0,str(ROOT/'backend'))
from app.runtime_config import load_config
from app.services.audio.factory import create_audio_frontend
from app.services.audio.models import AudioObservation
from app.services.active_speaker import ActiveSpeakerFusion,CameraCalibration,PersonTrack
from app.config import settings
from app.models import RoomState,Condition,ActivityState
from app.state_store import store
from app.study_logger import logger
from app.orchestrator import orchestrator

async def run(hardware=False):
    report={}
    if hardware:
        frontend=create_audio_frontend(load_config(profile='hardware-xvf'))
        await frontend.start()
        try:
            times=[]
            for _ in range(20):
                observation=await frontend.poll()
                if not frontend.control_available: raise RuntimeError(observation.error)
                times.append(frontend.telemetry_latency_ms)
                await asyncio.sleep(.1)
            report['xvf_telemetry']={'status':'PASS','median_ms':statistics.median(times),'max_ms':max(times),'samples':len(times)}
        except Exception as exc: report['xvf_telemetry']={'status':'UNAVAILABLE','error':type(exc).__name__}
        finally: await frontend.stop()
    else: report['xvf_telemetry']={'status':'SKIPPED','reason':'Use --hardware with an attached XVF'}
    # Explicit synthetic replay, not claimed as physical capture-to-action latency.
    settings.agent_backend='fake'
    store.state=RoomState(condition=Condition.AUTONOMOUS)
    config=load_config(profile='simulation')
    calibration=CameraCalibration(config['camera']['calibration']['points'],calibrated=True)
    fusion=ActiveSpeakerFusion(calibration,onset_ms=0)
    now=time.monotonic()
    audio=AudioObservation(now,True,1,52,None,'auto_selected',True,'simulation',True)
    result=fusion.process(audio,[PersonTrack('student_3',(49+90)/180,now,'student')])
    assert result.track_id=='student_3'
    # Scripted floor yield is supplied by fixture, not inferred from azimuth.
    store.state.observations.active_speaker=result.track_id
    store.state.activity.state=ActivityState.Q_AND_A
    with tempfile.TemporaryDirectory() as temp:
        logger.path=Path(temp)/'events.jsonl'
        await orchestrator.evaluate()
    assert store.state.devices.camera_target=='student_3'
    report['simulated_state_change_to_action']={'status':'PASS','milliseconds':(time.monotonic()-now)*1000,
        'backend':'fake','note':'synthetic fusion + explicit Q&A state + policy + simulated execution; excludes audio capture and real camera latency'}
    save('xvf_benchmark_'+platform.system().lower()+'_'+platform.machine()+'.json',report)
    print(report)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--hardware',action='store_true')
    asyncio.run(run(parser.parse_args().hardware))
