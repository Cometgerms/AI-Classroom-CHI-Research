"""Idempotent model bootstrap. Install Ollama separately using the platform guide."""
import argparse
import platform
import re
import shutil
import subprocess
import sys
from ai_common import ROOT, api, manifest

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--secondary', action='store_true', help='Also pull optional Ollama vision model')
    parser.add_argument('--perception', action='store_true', help='Download YOLO weights using this Python environment')
    args = parser.parse_args()
    print(f'Platform: {platform.system()} / {platform.machine()}', flush=True)
    results = []
    if not shutil.which('ollama'):
        print('FAIL Ollama CLI missing. See docs/SETUP_MAC.md or docs/SETUP_WINDOWS.md')
        return 1
    subprocess.run(['ollama', '--version'], check=True)
    try:
        server_version = api('version')['version']
        print(f'Ollama server: {server_version}')
        match = re.match(r'(\d+)\.(\d+)\.(\d+)', server_version)
        if args.secondary and (not match or tuple(map(int, match.groups())) < (0, 12, 7)):
            print('FAIL Qwen3-VL requires Ollama >= 0.12.7. Update using the platform guide.')
            return 1
        installed = {m['name'] for m in api('tags')['models']}
    except Exception as exc:
        print(f'FAIL Ollama server: {type(exc).__name__}. Start Ollama or run ollama serve.')
        return 1
    for spec in manifest().values():
        if spec['runtime'] != 'ollama' or not (spec['required'] or args.secondary):
            continue
        model = spec['model']
        if model not in installed:
            print(f'Downloading {model} from {spec["source"]} (~{spec["download_gb"]} GB); stored in Ollama cache, outside git.', flush=True)
            ok = subprocess.run(['ollama', 'pull', model]).returncode == 0
        else:
            print(f'Already installed: {model}')
            ok = True
        results.append(ok)
        print(f'{model}: {"PASS" if ok else "FAIL"}')
    if args.perception:
        try:
            from ultralytics import YOLO
            cache = ROOT / 'models' / 'vision'
            cache.mkdir(parents=True, exist_ok=True)
            for key in ('vision_detection', 'vision_pose'):
                name = manifest()[key]['model']
                print(f'Downloading/loading {name} in ignored models/vision', flush=True)
                YOLO(str(cache / name))
            results.append(True)
        except Exception as exc:
            print(f'Optional vision FAIL: {type(exc).__name__}: {exc}')
            # Optional dependency does not fail the core stack.
    print('Bootstrap ' + ('PASS' if all(results) else 'FAIL'))
    return 0 if all(results) else 1

if __name__ == '__main__':
    sys.exit(main())
