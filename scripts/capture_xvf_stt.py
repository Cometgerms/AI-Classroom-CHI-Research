"""Explicit short UAC → processed channel → resampled WAV → SpeechToText smoke test."""
import argparse
import asyncio
from ai_common import ROOT
import sys
sys.path.insert(0,str(ROOT/'backend'))
from app.runtime_config import load_config
from app.services.audio.factory import create_audio_frontend
from check_ai_stack import whisper

async def run(seconds):
    frontend=create_audio_frontend(load_config(profile='hardware-xvf'))
    if not hasattr(frontend,'transcribe'): raise RuntimeError('Select XVF hardware audio in local config')
    await frontend.start()
    try:
        print(await frontend.transcribe(whisper(),seconds))
    finally: await frontend.stop()

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--seconds',type=float,default=3)
    args=parser.parse_args()
    asyncio.run(run(args.seconds))
