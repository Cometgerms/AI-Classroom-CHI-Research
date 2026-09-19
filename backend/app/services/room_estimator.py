"""One temporal semantic estimator for all normalized sources."""
from ..models import ActivityState, ActivityEstimate

class StateEstimator:
    def __init__(self,sustain_seconds=.5):
        self.sustain=sustain_seconds
        self.candidate=None;self.since=None;self.last=None
        self.confirmed=ActivityState.UNKNOWN

    def process(self,frame,speaker):
        t=frame.timestamp
        if self.last is not None and t<self.last: raise ValueError('Observations must be monotonic')
        self.last=t
        scene=frame.scene;audio=frame.audio
        activity=ActivityState.UNKNOWN
        evidence=[]
        if not audio.audio_device_available or not frame.vision.camera_available:
            evidence=['Perception unavailable']
        elif scene.program_audio and scene.hdmi_playback and not scene.instructor_speaking:
            activity=ActivityState.MEDIA_PLAYBACK;evidence=['Sustained HDMI playback','Program audio','Instructor silent']
        elif scene.instructor_speaking and scene.audience_speaking and not scene.instructor_yielded:
            activity=ActivityState.SIDE_CONVERSATION;evidence=['Overlapping speech','Instructor retains floor']
        elif audio.speech_active and speaker.track_id:
            if scene.student_at_front and speaker.role=='student':
                activity=ActivityState.STUDENT_PRESENTATION;evidence=['Student speaker at front','Presentation active']
            elif scene.turn_count>=3 and scene.audience_speaking:
                activity=ActivityState.DISCUSSION;evidence=['Repeated audience turn-taking']
            elif speaker.role=='student' and scene.instructor_yielded and not scene.instructor_speaking:
                activity=ActivityState.Q_AND_A;evidence=['Localized audience speaker','Instructor yielded floor','Speech sustained']
            elif speaker.role=='instructor' and scene.object_visible and scene.presenter_zone=='demo_zone':
                activity=ActivityState.DEMONSTRATION;evidence=['Instructor at demonstration zone','Object visible']
            elif speaker.role=='instructor' and scene.instructor_speaking:
                activity=ActivityState.LECTURE;evidence=['Localized instructor speech','Presentation active']
        if activity!=self.candidate:
            self.candidate,self.since=activity,t
        if t-self.since < self.sustain-1e-9:
            return ActivityEstimate(state=ActivityState.TRANSITION,confidence=.4,previous=self.confirmed,evidence=['Activity evidence changing'])
        previous=self.confirmed
        self.confirmed=activity
        return ActivityEstimate(state=activity,confidence=.94 if activity!=ActivityState.UNKNOWN else 0,
                                previous=previous if previous!=activity else None,evidence=evidence)
