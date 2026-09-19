from dataclasses import dataclass

@dataclass(frozen=True)
class BeamTelemetry:
    # Order is fixed by upstream: focused 1, focused 2, free-running, auto-selected.
    azimuth_degrees: tuple[float | None, ...]
    speech_energy: tuple[float, ...]
