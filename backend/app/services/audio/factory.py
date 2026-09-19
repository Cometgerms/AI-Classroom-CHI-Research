from pathlib import Path
from ...runtime_config import ROOT, audio_backend
from .simulation import SimAudioFrontEnd

def create_audio_frontend(config):
    selected=audio_backend(config)
    if selected=='simulation': return SimAudioFrontEnd(poll_hz=config['audio']['poll_hz'])
    if selected!='xvf3800': raise ValueError(f'Audio frontend {selected} is not implemented; choose simulation or xvf3800')
    from .xvf3800.frontend import XVF3800AudioFrontEnd
    from .xvf3800.control import XVF3800Control
    from .xvf3800.audio import PortAudioCapture
    options=config['xvf3800']
    if options['transport']!='usb' or options['host_control'] not in ('auto','python'):
        raise ValueError('V1 supports the official Python USB host-control path')
    vendor=Path(options['vendor_dir'])
    if not vendor.is_absolute(): vendor=ROOT/vendor
    return XVF3800AudioFrontEnd(XVF3800Control(vendor,options['usb_timeout_ms']),PortAudioCapture(config['audio']),config['audio'])
