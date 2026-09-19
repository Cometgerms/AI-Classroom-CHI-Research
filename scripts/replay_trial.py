"""Export a recorded JSONL trial or replay an exported normalized tape over localhost API."""
import argparse
import json
from pathlib import Path
import httpx

parser=argparse.ArgumentParser()
parser.add_argument('path',type=Path)
parser.add_argument('--from-log',action='store_true',help='Extract last runtime_run_started tape from JSONL')
parser.add_argument('--output',type=Path,help='Write tape instead of executing replay')
parser.add_argument('--realtime',action='store_true')
args=parser.parse_args()
if args.from_log:
    tape=None
    for line in args.path.read_text().splitlines():
        event=json.loads(line)
        if event.get('event')=='runtime_run_started': tape=event.get('recording',event.get('payload',{}).get('recording'))
    if tape is None: parser.error('No recorded trial in this log')
else: tape=json.loads(args.path.read_text())
if args.output: args.output.write_text(json.dumps(tape,indent=2)+'\n')
else:
    response=httpx.post('http://localhost:8000/api/replay',params={'realtime':str(args.realtime).lower()},json=tape,timeout=900)
    response.raise_for_status()
    print(json.dumps(response.json(),indent=2))
