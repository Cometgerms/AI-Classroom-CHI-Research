> CHI V1 scope: one instructor/TA participant and one facilitator, no students. Prioritize processed UAC audio, device AEC, speech activity and Whisper input. DoA and multi-person fusion remain optional; azimuth calibration must not block V1. Set audio.doa_enabled=false to skip DoA polling. A failed optional DoA read does not suppress successful energy/speech observations. See [study protocol](STUDY_V1.md).

# XVF3800 audio front end

**XVF3800 is the V1 canonical audio front end.** Simulation emits the same AudioObservation data class. Device-specific telemetry stays in services/audio/xvf3800; the room agent receives neither raw beam arrays nor USB command access.

## Contracts and lifecycle

`AudioFrontEnd.start()/stop()/status()` are async; `observations()` is an async iterator. `SimAudioFrontEnd` supports scripted normalized frames. `XVF3800AudioFrontEnd` combines two independently monitored interfaces:

- PortAudio/sounddevice UAC input: discover candidates by case-insensitive name and optional local host API; require exactly one match. Read the reported default sample rate/channels and validate with PortAudio, or validate explicit local settings. No unconditional 48 kHz assumption. Common firmware offers 16 kHz stereo; check actual device/firmware before choosing 48 kHz.
- Read-only persistent Python control object: VERSION, AEC_AZIMUTH_VALUES, AEC_SPENERGY_VALUES. Upstream pin `a652fe79da3a292b25decc0e1e7f267d29bb0284`, SHA-256 checked before importing. Official source downloaded to ignored vendor/xvf3800. No per-poll subprocess, parameter writes, shell, firmware flashing or agent-visible control tool.

FastAPI lifespan starts the selected audio adapter and serves `/api/audio` with normalized status, observation and fusion output. Polls target 10 Hz (configurable 1–20 Hz); slow polls are serialized and skip sleep rather than spawning overlapping work. The upstream API retries reads up to 100 times; each USB transfer is limited to 100 ms by default. A stalled read can therefore delay stop for roughly 11 seconds per command. This bounded upstream behavior needs measurement with attached hardware before reducing timeouts.

UAC callbacks keep a bounded in-memory queue. `transcribe(SpeechToText, seconds)` captures a fresh finite window, selects the configured processed channel, anti-alias resamples to mono 16 kHz PCM16, calls the existing STT interface and deletes its temporary WAV. The left channel (index 0) is the default processed channel; do not average two differently routed outputs. Verify firmware routing before changing it. `scripts/capture_xvf_stt.py --seconds 3` is an explicit microphone/STT smoke test. No audio is persisted by the normal telemetry loop.

On device/control loss, direction/energy become unavailable and speech activity resets. UAC and USB control availability are reported separately. No automatic simulation fallback is presented as real hardware. Control reconnect is attempted by subsequent polls; UAC disconnect recovery currently requires restarting the selected profile.

## Coordinates, activity and calibration

Upstream Python/CLI primary AEC azimuth values are radians, in beam order focused 1 / focused 2 / free-running / auto-selected. Native CLI degree annotations are ignored by the parser. All four beams are retained only in adapter diagnostics; normalized `doa_degrees` and `speech_energy` select the fourth beam. Firmware processed-selected DoA is not queried in this revision because its semantics differ across firmware versions. Missing/NaN direction becomes null; confidence is null because no calibrated firmware confidence was measured.

Room azimuth = `wrap(sign * degrees(firmware_radians) + azimuth_offset_deg)`, in [-180,180). `invert_azimuth` chooses sign. Room zero is the calibrated front/camera center; positive angle is toward increasing image x in the example calibration. These are software conventions, not an assertion about how the microphone is mounted. Calibration must map physical mounting to this frame.

`energy_threshold: null` means **uncalibrated**: report raw energy and a warning, and do not claim speech activity. Measure idle/noise and intended speech conditions, choose a local threshold, then test false positives/negatives. Above threshold for onset_ms (150 default) starts speech; below threshold for release_ms (400 default) ends it. Short interruptions reset candidate timers. Speech energy is not a perfect VAD. The classifier accepts an explicit Boolean activity signal if future firmware validates one. `speech_activity_backend: silero` explicitly enables the existing optional research detector; install research-vad requirements first. Ordinary V1 never imports it.

CameraCalibration interpolates locally measured normalized box-center x to room azimuth. Shared example points have `calibrated: false`. For a mapping crossing ±180°, store unwrapped consecutive angles (e.g. 170 to 190), then outputs wrap. Calibration assumes a fixed camera view; invalidate/recalibrate after a crop/PTZ/FOV change. DoA alone never determines depth or full room coordinates.

ActiveSpeakerFusion combines speech activity, available audio, calibration and fresh tracked people. It smooths direction circularly, matches angular tolerance, rejects near ties, and requires a sustained candidate. Silence, stale tracks, uncalibrated input or missing direction produce no active person. Track role is supplied separately, never guessed by the LLM or direction. Confidence is a geometric association score, not a calibrated probability. `AudioRuntime.update_people()` accepts existing normalized PersonTracker output and frame width; `update_tracks()` accepts already projected tracks.

## Integration boundary

Audio collection and fusion are runnable. The existing UI scenarios still own controlled activity labels and drive the agent through the existing delegation/validator. The audio collector deliberately does not mutate room state at 10 Hz or invoke an LLM; doing that would continually invalidate in-flight decisions and destroy controlled study parity. A calibrated camera capture/track producer and validated event-to-state projection are the next integration step. The synthetic latency benchmark exercises fusion → explicit scenario state → policy → simulated action, and labels this distinction. No automatic physical active-speaker-to-camera control is claimed.

## Configuration

Order: default.yaml → detected platform YAML → ignored local.yaml → explicit named launch profile → environment overrides. `CLASSROOM_AUDIO__POLL_HZ=5` illustrates nested overrides; legacy AGENT_BACKEND/OLLAMA_MODEL/OLLAMA_BASE_URL remain supported. Backend/.env is legacy compatibility, lower priority than real environment but above file configuration. Avoid keeping stale .env overrides when switching to local.yaml.

Profiles simulation / mac-local / windows-local / hardware-xvf share the application. Simulation forces simulated audio via hardware.mode; hardware profiles choose XVF audio plus simulated camera/projector/recorder. Shared agent default is Ollama; simulation profile selects FakeAgent. Study condition is a separate policy axis, never configured by platform. Unsupported real projector/camera/recorder adapters fail clearly rather than being silently simulated. Those extension points exist in config; implementations are intentionally deferred.

## Sources and physical verification

[Official host controls and beam ordering](https://github.com/respeaker/reSpeaker_XVF3800_USB_4MIC_ARRAY/blob/a652fe79da3a292b25decc0e1e7f267d29bb0284/host_control/README.md), [pinned Python implementation](https://github.com/respeaker/reSpeaker_XVF3800_USB_4MIC_ARRAY/blob/a652fe79da3a292b25decc0e1e7f267d29bb0284/python_control/xvf_host.py), [Seeed platform/driver/UAC guide](https://wiki.seeedstudio.com/respeaker_xvf3800_introduction/).

On this Mac no matching XVF UAC or USB control device was found. Package acquisition and disconnected behavior were verified; live DoA, energy thresholds, audio capture and hardware latency were not. Windows drivers and hardware are unverified. Non-hardware tests require neither USB libraries nor microphone/camera. Hardware tests are explicitly opt-in.

`hardware.audio` selects the sensing front end; participant AV audio-mode/voice-lift actions still use the simulated AV executor. They do not write XVF DSP settings. Vision factory resolves MPS/CUDA/CPU with an explicit fallback message and keeps the same nano model.
