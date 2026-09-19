"""Acquire exact official Python host source; probe hardware without changing firmware."""
import argparse
import hashlib
import platform
from pathlib import Path
import sys
import urllib.request
from ai_common import ROOT
sys.path.insert(0,str(ROOT/'backend'))
from app.services.audio.xvf3800.control import COMMIT, SOURCE_SHA256, UPSTREAM, XVF3800Control
from app.services.audio.xvf3800.parser import parse_doa,parse_energy

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--download-only',action='store_true')
    parser.add_argument('--vendor-dir',type=Path,default=ROOT/'vendor/xvf3800')
    args=parser.parse_args()
    print(f'XVF3800 bootstrap: {platform.system()} {platform.machine()}\nUpstream {UPSTREAM}\nCommit {COMMIT}')
    destination=args.vendor_dir/'xvf_host.py'
    if not destination.is_file():
        print('Downloading pinned official Python host-control source (no opaque binaries).')
        url=f'https://raw.githubusercontent.com/respeaker/reSpeaker_XVF3800_USB_4MIC_ARRAY/{COMMIT}/python_control/xvf_host.py'
        with urllib.request.urlopen(url,timeout=30) as response: data=response.read()
        if hashlib.sha256(data).hexdigest()!=SOURCE_SHA256: raise ValueError('Upstream source hash mismatch')
        args.vendor_dir.mkdir(parents=True,exist_ok=True)
        destination.write_bytes(data)
    elif hashlib.sha256(destination.read_bytes()).hexdigest()!=SOURCE_SHA256:
        raise ValueError('Existing vendor source differs; refusing to overwrite it')
    print('Host source: PASS (pinned checksum verified)')
    if args.download_only: return 0
    control=XVF3800Control(args.vendor_dir)
    passed=True
    try:
        for label,probe in [('VERSION',control.get_version),('DoA',lambda:parse_doa(control.get_doa())),
                            ('Speech energy',lambda:parse_energy(control.get_speech_energy()))]:
            try: print(f'{label}: PASS {probe()}')
            except Exception as exc:
                passed=False;print(f'{label}: UNAVAILABLE ({type(exc).__name__}: {exc})')
    finally: control.close()
    if not passed:
        print('Install config/audio-requirements.txt in the active Python environment. Connect the XVF data USB port.\n'
              'Windows: check vendor control-interface WinUSB driver separately from UAC. macOS: check libusb and microphone permission.\n'
              'See platform guides. Simulation is ready without hardware: python -m backend --profile simulation')
    return 0 if passed else 2

if __name__=='__main__': sys.exit(main())
