"""From repo root: python -m backend --profile simulation-basic."""
import argparse
import os
import sys
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('--profile',choices=['simulation-basic','simulation-ai','hybrid','hardware','study','simulation','mac-local','windows-local','hardware-xvf'])
parser.add_argument('--port',type=int,default=8000)
args=parser.parse_args()
if args.profile: os.environ['CLASSROOM_PROFILE']=args.profile
sys.path.insert(0,str(Path(__file__).resolve().parent))
import uvicorn
uvicorn.run('app.main:app',host='127.0.0.1',port=args.port)
