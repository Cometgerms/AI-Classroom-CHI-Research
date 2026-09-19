"""Read-only wrapper over the pinned official Python host-control implementation."""
import hashlib
import importlib.util
from pathlib import Path
import threading

UPSTREAM='https://github.com/respeaker/reSpeaker_XVF3800_USB_4MIC_ARRAY'
COMMIT='a652fe79da3a292b25decc0e1e7f267d29bb0284'
# Filled from the pinned source during implementation; bootstrap verifies before loading.
SOURCE_SHA256='f886a40c085eae56b773c581294dd7b178eb358eced7c92060a63fab861da8f3'
READS={'VERSION','AEC_AZIMUTH_VALUES','AEC_SPENERGY_VALUES'}

class XVF3800Control:
    def __init__(self, vendor_dir, timeout_ms=100, device=None):
        self.vendor_dir=Path(vendor_dir)
        self.timeout_ms=timeout_ms
        self.device=device
        self.lock=threading.Lock()

    def connect(self):
        if self.device is not None: return
        path=self.vendor_dir/'xvf_host.py'
        if not path.is_file(): raise FileNotFoundError('Run scripts/bootstrap_xvf3800.py first')
        if hashlib.sha256(path.read_bytes()).hexdigest()!=SOURCE_SHA256:
            raise ValueError('XVF host source hash differs from pinned version')
        spec=importlib.util.spec_from_file_location('_classroom_xvf_host',path)
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.print=lambda *args,**kwargs: None # suppress upstream per-poll debug output
        # Use bundled libusb on both platforms, avoiding a hard-coded dylib path.
        devices=list(module.libusb_package.find(find_all=True,idVendor=0x2886,idProduct=0x001A) or [])
        if not devices: raise ConnectionError('XVF3800 control device absent or USB driver unavailable')
        if len(devices)!=1: raise ConnectionError('Multiple XVF3800 control devices; connect only one for V1')
        self.device=module.ReSpeaker(devices[0])
        self.device.TIMEOUT=self.timeout_ms

    def read(self, command):
        if command not in READS: raise ValueError('Only allowlisted read-only XVF telemetry is supported')
        with self.lock:
            self.connect()
            return self.device.read(command)

    def get_version(self):
        version=self.read('VERSION')
        if len(version)!=3 or any(type(v) is not int or not 0<=v<=255 for v in version):
            raise ValueError('Invalid firmware version')
        return '.'.join(map(str,version))

    def get_doa(self): return self.read('AEC_AZIMUTH_VALUES')
    def get_speech_energy(self): return self.read('AEC_SPENERGY_VALUES')
    def get_status(self):
        try: return {'available':True,'version':self.get_version()}
        except Exception as exc: return {'available':False,'error':str(exc)}

    def close(self):
        with self.lock:
            if self.device is not None:
                try: self.device.close()
                finally: self.device=None
