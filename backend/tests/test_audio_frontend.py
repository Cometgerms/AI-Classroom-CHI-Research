import asyncio
from dataclasses import replace
import math
import pytest
from app.runtime_config import load_config,audio_backend
from app.services.audio.models import AudioObservation
from app.services.audio.activity import SpeechActivity
from app.services.audio.simulation import SimAudioFrontEnd
from app.services.audio.xvf3800.parser import parse_doa,parse_energy
from app.services.audio.xvf3800.frontend import XVF3800AudioFrontEnd
from app.services.audio.xvf3800.audio import discover,write_stt_wav
from app.services.audio.factory import create_audio_frontend
from app.services.active_speaker import ActiveSpeakerFusion,CameraCalibration,PersonTrack

@pytest.mark.parametrize('payload', [
    (math.pi/2,0,math.pi,math.pi/4),
    'Device VID: 10374 PID: 26\nAEC_AZIMUTH_VALUES 1.570796 (90 deg) 0 (0 deg) 3.14159265 (180 deg) 0.785398 (45 deg)',
    'ReadCMD payload [1, 2, 3]\nAEC_AZIMUTH_VALUES: [1.570796, 0, 3.14159265, 0.785398]\nDone!'
])
def test_doa_parsing(payload):
    result=parse_doa(payload)
    assert result[0]==pytest.approx(90,abs=.001)
    assert result[3]==pytest.approx(45,abs=.001)

def test_offset_and_inversion():
    result=parse_doa([0,0,0,math.pi/3],offset=10,invert=True)
    assert result[3]==pytest.approx(-50)
    assert parse_doa([0,0,0,math.pi],offset=20)[3]==pytest.approx(-160)
    assert parse_doa([0,0,0,float('nan')])[3] is None

@pytest.mark.parametrize('payload',['AEC_SPENERGY_VALUES 1 2 3 4','AEC_SPENERGY_VALUES: [1e3, 0, 2.5, 4]'])
def test_energy_parse(payload): assert parse_energy(payload)[3]==4

@pytest.mark.parametrize('payload',['Error AEC_SPENERGY_VALUES 1 2 3 4','AEC_SPENERGY_VALUES 1 2 3',
                                    'AEC_SPENERGY_VALUES 1 2 -1 4','AEC_SPENERGY_VALUES 1 2 nan 4',
                                    'AEC_SPENERGY_VALUES 1 2 inf 4'])
def test_bad_energy_rejected(payload):
    with pytest.raises(ValueError):parse_energy(payload)

def test_speech_hysteresis_and_uncalibrated():
    detector=SpeechActivity(10,onset_ms=150,release_ms=400)
    assert not detector.process(20,0)
    assert not detector.process(20,.14)
    assert detector.process(20,.15)
    assert detector.process(0,.2)
    assert detector.process(0,.59)
    assert not detector.process(0,.6)
    assert not SpeechActivity().process(99999,0)
    with pytest.raises(ValueError): SpeechActivity(-1)

def test_noise_resets_onset():
    d=SpeechActivity(10)
    assert not d.process(20,0)
    assert not d.process(0,.1)
    assert not d.process(20,.15)
    assert not d.process(20,.2)
    assert d.process(20,.3)

class Control:
    disconnected=False
    def get_version(self): return '2.0.2'
    def get_doa(self):
        if self.disconnected: raise ConnectionError('unplugged')
        return [0,1,2,math.radians(52)]
    def get_speech_energy(self):
        if self.disconnected: raise ConnectionError('unplugged')
        return [0,1,2,20]
    def close(self): pass

class Audio:
    def start(self): self.running=True
    def stop(self): self.running=False
    def available(self): return getattr(self,'running',False)

@pytest.mark.asyncio
async def test_real_adapter_normalization_and_disconnect():
    config=load_config(environ={})['audio']
    config['speech_activity'].update(energy_threshold=10,onset_ms=0)
    control=Control();adapter=XVF3800AudioFrontEnd(control,Audio(),config)
    await adapter.start()
    observation=await adapter.poll()
    assert observation.speech_active
    assert observation.doa_degrees==pytest.approx(52)
    assert observation.doa_confidence is None
    assert len(adapter.diagnostics.azimuth_degrees)==4
    control.disconnected=True
    failed=await adapter.poll()
    assert not failed.speech_active and failed.doa_degrees is None and failed.error
    assert not (await adapter.status()).control_available
    await adapter.stop()
    assert not (await adapter.status()).running

@pytest.mark.asyncio
async def test_simulation_same_normalized_type():
    sim=SimAudioFrontEnd([AudioObservation(0,True,20,52,None,'auto_selected',True,'simulation',True)])
    await sim.start()
    item=await anext(sim.observations())
    assert isinstance(item,AudioObservation) and item.doa_degrees==52 and item.speech_active
    await sim.stop()

def calibrated():
    return CameraCalibration([{'image_x':0,'azimuth_deg':-90},{'image_x':.5,'azimuth_deg':0},{'image_x':1,'azimuth_deg':90}],True)

def audio(t=0,**kwargs):
    return replace(AudioObservation(t,True,20,52,None,'auto_selected',True,'simulation',True),**kwargs)

def tracks(t=0):
    return [PersonTrack('P1',(12+90)/180,t),PersonTrack('P2',(49+90)/180,t,'student'),PersonTrack('P3',(91+90)/180,t)]

def test_fusion_sustain():
    fusion=ActiveSpeakerFusion(calibrated())
    assert fusion.process(audio(),tracks()).track_id is None
    result=fusion.process(audio(.2),tracks(.2))
    assert result.track_id=='P2' and result.role=='student'
    assert result.doa_error_deg==pytest.approx(3)

@pytest.mark.parametrize('change',[{'speech_active':False},{'doa_degrees':None},{'audio_device_available':False},{'activity_calibrated':False}])
def test_fusion_no_speaker(change):
    fusion=ActiveSpeakerFusion(calibrated(),onset_ms=0)
    assert fusion.process(audio(**change),tracks()).track_id is None

def test_ambiguous_stale_and_uncalibrated():
    fusion=ActiveSpeakerFusion(calibrated(),onset_ms=0)
    people=[PersonTrack('P1',(50+90)/180,0),PersonTrack('P2',(54+90)/180,0)]
    assert fusion.process(audio(),people).track_id is None
    assert fusion.process(audio(10),tracks()).track_id is None
    calibration=calibrated();calibration.calibrated=False
    assert ActiveSpeakerFusion(calibration).process(audio(),tracks()).track_id is None

def test_circular_distance():
    calibration=CameraCalibration([{'image_x':0,'azimuth_deg':170},{'image_x':1,'azimuth_deg':190}],True)
    fusion=ActiveSpeakerFusion(calibration,onset_ms=0)
    result=fusion.process(audio(doa_degrees=-179),[PersonTrack('P1',.45,0)])
    assert result.track_id=='P1' and result.doa_error_deg==pytest.approx(2)

@pytest.mark.parametrize('system',['Darwin','Windows','Linux'])
def test_profiles_platform_parity(system):
    config=load_config(profile='simulation',environ={},system=system)
    assert config['agent']['model']=='qwen3:8b'
    assert config['agent']['backend']=='fake'
    assert isinstance(create_audio_frontend(config),SimAudioFrontEnd)
    hardware=load_config(profile='hardware-xvf',environ={},system=system)
    assert audio_backend(hardware)=='xvf3800'
    assert hardware['hardware']['camera']=='simulation'

class Devices:
    def __init__(self, devices): self.devices=devices
    def query_devices(self): return self.devices
    def query_hostapis(self,index): return {'name':'Test API'}
    def check_input_settings(self,**kwargs): self.checked=kwargs

def test_uac_discovers_actual_rate_and_reports_ambiguity():
    config=load_config(environ={})['audio']
    device={'name':'reSpeaker 3800','max_input_channels':2,'default_samplerate':16000,'hostapi':0}
    sd=Devices([device]);profile=discover(config,sd)
    assert profile.sample_rate==16000 and profile.channels==2
    sd=Devices([{**device,'default_samplerate':48000}])
    assert discover(config,sd).sample_rate==48000
    with pytest.raises(RuntimeError):discover(config,Devices([device,device]))
    with pytest.raises(RuntimeError):discover(config,Devices([]))
    assert discover({**config,'device_index':1},Devices([device,device])).device_index==1

@pytest.mark.optional_audio
@pytest.mark.asyncio
async def test_uac_to_stt_normalization(tmp_path):
    np=pytest.importorskip('numpy');pytest.importorskip('scipy')
    import wave
    class Capture(Audio):
        def capture(self,seconds):return np.ones((4800,2),dtype=np.float32)*.1,48000
    class STT:
        def transcribe(self,path):
            with wave.open(str(path)) as wav:
                assert (wav.getframerate(),wav.getnchannels(),wav.getsampwidth(),wav.getnframes())==(16000,1,2,1600)
            return 'normalized speech'
    adapter=XVF3800AudioFrontEnd(Control(),Capture(),load_config(environ={})['audio'])
    await adapter.start()
    assert await adapter.transcribe(STT(),.1)=='normalized speech'
    await adapter.stop()

def test_config_layering(tmp_path):
    import shutil
    from app.runtime_config import ROOT
    shutil.copytree(ROOT/'config',tmp_path/'config',ignore=shutil.ignore_patterns('._*','local.yaml'))
    (tmp_path/'config/local.yaml').write_text('audio:\n  poll_hz: 5\nagent:\n  backend: rule\n')
    result=load_config(tmp_path,profile='simulation',system='Windows',environ={'CLASSROOM_AUDIO__POLL_HZ':'15','AGENT_BACKEND':'fake'})
    assert result['audio']['poll_hz']==15 and result['agent']['backend']=='fake'
    assert result['stt']['acceleration']=='cuda'

@pytest.mark.asyncio
async def test_runtime_collects_simulation_without_room_authority_mutation():
    from app.services.audio.runtime import AudioRuntime
    from app.state_store import store
    revision=store.revision
    runtime=AudioRuntime(load_config(profile='simulation',environ={}))
    await runtime.start()
    await asyncio.sleep(.01)
    assert (await runtime.snapshot())['observation']['source']=='simulation'
    await runtime.stop()
    assert store.revision==revision

@pytest.mark.hardware_optional
@pytest.mark.asyncio
async def test_physical_xvf_reads():
    frontend=create_audio_frontend(load_config(profile='hardware-xvf'))
    await frontend.start()
    try:
        observation=await frontend.poll()
        assert (await frontend.status()).control_available
        assert observation.speech_energy is not None
    finally:await frontend.stop()

def test_explicit_simulation_overrides_local_hardware(tmp_path):
    import shutil
    from app.runtime_config import ROOT
    shutil.copytree(ROOT/'config',tmp_path/'config',ignore=shutil.ignore_patterns('._*','local.yaml'))
    (tmp_path/'config/local.yaml').write_text('hardware:\n  mode: hybrid\n  audio: xvf3800\nagent:\n  backend: ollama\n')
    config=load_config(tmp_path,profile='simulation',environ={})
    assert audio_backend(config)=='simulation' and config['agent']['backend']=='fake'

@pytest.mark.asyncio
async def test_simulation_has_no_optional_import_dependency(monkeypatch):
    import builtins
    original=builtins.__import__
    def reject(name,*args,**kwargs):
        if name.split('.')[0] in {'sounddevice','usb','libusb_package','torch','numpy','scipy'}:
            raise ImportError('Optional hardware library intentionally absent')
        return original(name,*args,**kwargs)
    monkeypatch.setattr(builtins,'__import__',reject)
    frontend=create_audio_frontend(load_config(profile='simulation',environ={}))
    await frontend.start()
    assert (await anext(frontend.observations())).source=='simulation'
    await frontend.stop()

def test_read_only_control_rejects_writes(tmp_path):
    from app.services.audio.xvf3800.control import XVF3800Control
    control=XVF3800Control(tmp_path)
    with pytest.raises(ValueError):control.read('REBOOT')

def test_acceleration_resolution_without_gpu():
    from types import SimpleNamespace
    from app.services.vision.factory import resolve_acceleration
    torch=SimpleNamespace(cuda=SimpleNamespace(is_available=lambda:False),backends=SimpleNamespace(mps=SimpleNamespace(is_available=lambda:False)))
    assert resolve_acceleration('auto',torch)==('cpu',None)
    assert resolve_acceleration('cuda',torch)[0]=='cpu'
    assert resolve_acceleration('mps',torch)[1]
