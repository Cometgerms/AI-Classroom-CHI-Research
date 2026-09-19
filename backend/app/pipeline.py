"""Identical observation → fusion → estimator path for every runtime and replay."""
from .services.active_speaker import ActiveSpeakerFusion, CameraCalibration, ActiveSpeakerObservation
from .services.room_estimator import StateEstimator
from .models import ObservationState, SessionState
from .state_store import store
from .study_logger import logger

class ObservationPipeline:
    def __init__(self,config,calibration=None):
        self.fusion=ActiveSpeakerFusion(CameraCalibration(**(calibration or config['camera']['calibration'])),**config['fusion'])
        self.estimator=StateEstimator(**config['estimator'])
        self.states=[]
    async def consume(self,frame):
        speaker=self.fusion.process(frame.audio,frame.vision.tracks)
        # An explicitly assigned presenter can be followed without acoustic localization.
        # This is shared evidence logic, independent of runtime or study profile.
        presenters=[track for track in frame.vision.tracks if track.role in ('instructor','presenter')
                    and 0<=frame.timestamp-track.timestamp<=.5 and track.confidence>0]
        if (not speaker.track_id and len(presenters)==1 and frame.vision.camera_available
                and frame.audio.audio_device_available and frame.audio.speech_active
                and frame.scene.instructor_speaking and not frame.scene.audience_speaking):
            presenter=presenters[0]
            speaker=ActiveSpeakerObservation(presenter.track_id,'instructor',presenter.confidence)
        estimate=self.estimator.process(frame,speaker)
        scene=frame.scene
        observations=ObservationState(instructor_speaking=scene.instructor_speaking,student_speaking=scene.audience_speaking,
            active_speaker=speaker.track_id or 'unknown',speaker_location=scene.presenter_zone if speaker.role in ('instructor','presenter') else 'audience',
            transcript=scene.transcript,presentation_active=scene.presentation_active,program_audio=scene.program_audio,
            presenter_zone=scene.presenter_zone,presentation_source=scene.presentation_source,evidence=estimate.evidence)
        async with store.control_lock:
            old=await store.snapshot()
            changed=old.activity.state!=estimate.state or old.observations!=observations
            if changed:
                store.pending=None
                def update(state):
                    state.activity=estimate;state.observations=observations
                    state.session={'pre_class':SessionState.PRE_CLASS,'teaching':SessionState.ACTIVE,'post_class':SessionState.POST_CLASS}[scene.session_phase]
                    state.last_scenario='observation_stream'
                await store.mutate(update)
        self.states.append(estimate.state.value)
        logger.log('normalized_observation',frame=frame.model_dump(mode='json'),activity=estimate.state.value,active_speaker=speaker.track_id)
        return changed
