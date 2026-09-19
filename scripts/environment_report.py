"""Allowlisted machine facts only: no hostnames, usernames, serials or paths."""
import json
import platform
import re
import subprocess
from ai_common import api, save

def command(args):
    try:
        return subprocess.check_output(args,text=True,stderr=subprocess.DEVNULL,timeout=20).strip()
    except (OSError,subprocess.SubprocessError):
        return None

def collect():
    report=dict(os=platform.system(),os_version=platform.release(),architecture=platform.machine(),
        cpu=None,system_ram_bytes=None,gpu=None,gpu_memory_bytes=None,cuda_version=None,
        python_version=platform.python_version(),node_version=command(['node','--version']))
    if platform.system()=='Darwin':
        report['cpu']=command(['sysctl','-n','machdep.cpu.brand_string'])
        ram=command(['sysctl','-n','hw.memsize']);report['system_ram_bytes']=int(ram) if ram else None
        raw=command(['system_profiler','SPDisplaysDataType','-json'])
        if raw:
            devices=json.loads(raw).get('SPDisplaysDataType',[])
            report['gpu']=[d.get('sppci_model') for d in devices]
            report['gpu_memory_note']='Apple Silicon unified memory; shared with system RAM'
    elif platform.system()=='Windows':
        raw=command(['powershell','-NoProfile','-Command','@{cpu=(Get-CimInstance Win32_Processor | Select-Object -First 1 -ExpandProperty Name); ram=(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory} | ConvertTo-Json'])
        if raw:
            d=json.loads(raw);report.update(cpu=d['cpu'],system_ram_bytes=d['ram'])
    gpu=command(['nvidia-smi','--query-gpu=name,memory.total,driver_version','--format=csv,noheader,nounits'])
    if gpu:
        rows=[r.split(',') for r in gpu.splitlines()]
        report.update(gpu=[r[0].strip() for r in rows],gpu_memory_bytes=[int(r[1])*1024**2 for r in rows],gpu_driver=[r[2].strip() for r in rows])
        smi=command(['nvidia-smi']) or ''
        match=re.search(r'CUDA Version:\s*([\d.]+)',smi)
        report['cuda_version']=match.group(1) if match else None
        report['cuda_note']='Driver supported CUDA version, not proof of installed toolkit'
    try:
        report['ollama_version']=api('version')['version']
        report['installed_models']=[{k:m.get(k) for k in ('name','digest','size')} for m in api('tags')['models']]
    except Exception:
        report.update(ollama_version=None,installed_models=[])
    return report

if __name__=='__main__':
    report=collect()
    save('environment_report.json',report)
    save('environment_'+platform.system().lower()+'_'+platform.machine()+'.json',report)
    print(json.dumps(report,indent=2))
