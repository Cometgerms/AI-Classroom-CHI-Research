"""Calibrated energy threshold with onset/release hysteresis; not a perfect VAD."""
import math

class SpeechActivity:
    def __init__(self, energy_threshold=None, onset_ms=150, release_ms=400):
        if energy_threshold is not None and (not math.isfinite(energy_threshold) or energy_threshold<0):
            raise ValueError('Energy threshold must be a nonnegative finite value or null')
        if min(onset_ms, release_ms)<0: raise ValueError('Invalid activity timing')
        self.threshold, self.onset, self.release=energy_threshold,onset_ms/1000,release_ms/1000
        self.reset()

    def reset(self):
        self.active=False
        self.candidate=None
        self.since=None
        self.last=None

    def process(self, energy, timestamp, explicit_vad=None):
        if not math.isfinite(timestamp) or (self.last is not None and timestamp<self.last):
            raise ValueError('Expected finite monotonic timestamp')
        self.last=timestamp
        if explicit_vad is not None and type(explicit_vad) is not bool: raise ValueError('VAD must be bool')
        if explicit_vad is None and (self.threshold is None or energy is None):
            self.reset()
            return False
        if energy is not None and (not math.isfinite(energy) or energy<0):
            self.reset()
            raise ValueError('Invalid speech energy')
        high=explicit_vad if explicit_vad is not None else energy>self.threshold
        if high==self.active:
            self.candidate=self.since=None
        else:
            if self.candidate!=high:
                self.candidate,self.since=high,timestamp
            delay=self.onset if high else self.release
            if timestamp-self.since >= delay-1e-9:
                self.active=high
                self.candidate=self.since=None
        return self.active
