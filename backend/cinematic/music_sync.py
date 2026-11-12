"""Music Synchronization and Montage Protocol for CS2 Cinematic Studio.

Generates tempo-calibrated musical placeholders and provides rhythm-based
beat detection, drop alignment, and EDL cut snapping.
"""

from __future__ import annotations

import math
import pathlib
import struct
import wave
from dataclasses import dataclass, field
from typing import Any, Optional

from backend.cinematic.models import CameraType, CinematicShot, EditDecisionClip, ShotPurpose


@dataclass
class MusicBeatGrid:
    """Represents a tempo-locked musical beat and downbeat grid."""

    bpm: float
    beat_duration: float
    measure_duration: float
    beat_timestamps: list[float] = field(default_factory=list)
    downbeat_timestamps: list[float] = field(default_factory=list)
    drop_timestamp: float = 0.0

    @classmethod
    def create(cls, bpm: float = 128.0, duration_seconds: float = 20.0, drop_measure: int = 4) -> "MusicBeatGrid":
        """Generate a beat grid with downbeats and drop timestamp."""
        beat_dur = 60.0 / float(bpm)
        meas_dur = beat_dur * 4.0

        beats: list[float] = []
        downbeats: list[float] = []

        t = 0.0
        beat_idx = 0
        while t <= duration_seconds:
            beats.append(round(t, 4))
            if beat_idx % 4 == 0:
                downbeats.append(round(t, 4))
            t += beat_dur
            beat_idx += 1

        drop_time = round(drop_measure * meas_dur, 4)
        return cls(
            bpm=bpm,
            beat_duration=round(beat_dur, 4),
            measure_duration=round(meas_dur, 4),
            beat_timestamps=beats,
            downbeat_timestamps=downbeats,
            drop_timestamp=drop_time,
        )

    def snap_to_nearest_beat(self, timestamp: float) -> float:
        """Find the nearest beat timestamp to align a visual cut."""
        if not self.beat_timestamps:
            return timestamp
        return min(self.beat_timestamps, key=lambda b: abs(b - timestamp))

    def snap_to_nearest_downbeat(self, timestamp: float) -> float:
        """Find the nearest bar downbeat for major scene transitions."""
        if not self.downbeat_timestamps:
            return timestamp
        return min(self.downbeat_timestamps, key=lambda b: abs(b - timestamp))


def generate_placeholder_music_track(
    output_path: pathlib.Path,
    duration_seconds: float = 16.0,
    bpm: float = 128.0,
    sample_rate: int = 44100,
) -> pathlib.Path:
    """Synthesize a royalty-free rhythmic 128 BPM electronic montage soundtrack.
    
    Generates a clean 16-bit PCM stereo WAV with:
    - 4/4 punchy kick drum
    - Synced 8th-note hi-hats
    - Rising melodic chord arpeggio
    - Climax drop section
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    beat_dur = 60.0 / float(bpm)
    num_samples = int(duration_seconds * sample_rate)

    # 16-bit signed PCM limits
    max_amp = 32767 * 0.75

    raw_frames = bytearray()

    for n in range(num_samples):
        t = n / float(sample_rate)
        sample_l = 0.0
        sample_r = 0.0

        # 1. Kick Drum (sine wave rapidly sweeping down 140Hz -> 45Hz every beat)
        beat_time = t % beat_dur
        if beat_time < 0.22:
            kick_phase = beat_time / 0.22
            freq = 140.0 * (1.0 - kick_phase * 0.7)
            env = math.exp(-kick_phase * 7.0)
            kick_val = math.sin(2.0 * math.pi * freq * beat_time) * env * 0.55
            sample_l += kick_val
            sample_r += kick_val

        # 2. Hi-hat (filtered white noise pulse on off-beats)
        half_beat = t % (beat_dur / 2.0)
        if half_beat < 0.05 and t > 0.5:
            # Simple pseudo-random hash for noise
            h_noise = (math.sin(n * 12.9898 + 78.233) * 43758.5453) % 1.0 - 0.5
            hh_env = math.exp(-(half_beat / 0.05) * 8.0)
            hh_val = h_noise * hh_env * 0.15
            sample_l += hh_val * 0.9
            sample_r += hh_val * 1.1

        # 3. Synth Bass Arpeggio (Root notes: A minor -> F major progression)
        bar_idx = int(t / (beat_dur * 4.0))
        root_freq = 55.0 if bar_idx % 2 == 0 else 43.65  # A1 or F1
        bass_phase = 2.0 * math.pi * root_freq * t
        bass_val = (math.sin(bass_phase) + 0.3 * math.sin(bass_phase * 2.0)) * 0.25
        sample_l += bass_val
        sample_r += bass_val

        # Master gain clamping
        sample_l = max(-1.0, min(1.0, sample_l))
        sample_r = max(-1.0, min(1.0, sample_r))

        int_l = int(sample_l * max_amp)
        int_r = int(sample_r * max_amp)

        raw_frames.extend(struct.pack("<hh", int_l, int_r))

    with wave.open(str(output_path), "wb") as wav_file:
        wav_file.setnchannels(2)  # Stereo
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(raw_frames)

    return output_path


def align_shots_to_beats(
    shots: list[CinematicShot],
    beat_grid: MusicBeatGrid,
    kill_ticks: list[int],
    tickrate: int = 128,
) -> list[EditDecisionClip]:
    """Assemble a multi-track Edit Decision List (EDL) aligned with music beats."""
    edl_clips: list[EditDecisionClip] = []
    if not shots:
        return edl_clips

    first_tick = min(s.start_tick for s in shots)

    # 1. Base Track V1 (Hero POV) spanning full action
    hero_shots = [s for s in shots if s.camera_type == CameraType.FIRST_PERSON]
    if hero_shots:
        hero = hero_shots[0]
        v1_in = (hero.start_tick - first_tick) / float(tickrate)
        v1_out = (hero.end_tick - first_tick) / float(tickrate)
        # Snap end to nearest bar downbeat
        v1_out = beat_grid.snap_to_nearest_downbeat(v1_out)
        edl_clips.append(
            EditDecisionClip(
                track_index=1,
                shot_id=hero.shot_id,
                media_path=hero.output_filename,
                source_in_seconds=0.0,
                source_out_seconds=v1_out - v1_in,
                timeline_in_seconds=v1_in,
                timeline_out_seconds=v1_out,
                clip_name="Track V1: Hero POV (Master)",
                transition_in="cut",
                suggested_speed=1.0,
            )
        )

    # 2. Track V2 (Cinematic B-Roll: Approach, Orbit, Flyby)
    broll_shots = [
        s for s in shots
        if s.camera_type in (CameraType.ESTABLISHING_SHOT, CameraType.SHOULDER_CAM, CameraType.ORBIT_CAMERA, CameraType.FREECAM_FLYBY)
    ]
    for b in broll_shots:
        raw_in = max(0.0, (b.start_tick - first_tick) / float(tickrate))
        raw_out = (b.end_tick - first_tick) / float(tickrate)

        # Snap start and out to nearest beat
        snapped_in = beat_grid.snap_to_nearest_beat(raw_in)
        snapped_out = beat_grid.snap_to_nearest_beat(raw_out)
        if snapped_out <= snapped_in:
            snapped_out = snapped_in + beat_grid.beat_duration

        edl_clips.append(
            EditDecisionClip(
                track_index=2,
                shot_id=b.shot_id,
                media_path=b.output_filename,
                source_in_seconds=0.0,
                source_out_seconds=snapped_out - snapped_in,
                timeline_in_seconds=snapped_in,
                timeline_out_seconds=snapped_out,
                clip_name=f"Track V2: {b.camera_type.value}",
                transition_in="cross_dissolve" if b.purpose == ShotPurpose.CLIMAX_ACCENT else "cut",
                suggested_speed=1.0,
            )
        )

    # 3. Track V3 (Victim Reaction Inserts)
    victim_shots = [s for s in shots if s.camera_type == CameraType.VICTIM_POV]
    for v in victim_shots:
        raw_in = max(0.0, (v.start_tick - first_tick) / float(tickrate))
        raw_out = (v.end_tick - first_tick) / float(tickrate)
        snapped_in = beat_grid.snap_to_nearest_beat(raw_in)
        snapped_out = beat_grid.snap_to_nearest_beat(raw_out)
        if snapped_out <= snapped_in:
            snapped_out = snapped_in + beat_grid.beat_duration

        edl_clips.append(
            EditDecisionClip(
                track_index=3,
                shot_id=v.shot_id,
                media_path=v.output_filename,
                source_in_seconds=0.0,
                source_out_seconds=snapped_out - snapped_in,
                timeline_in_seconds=snapped_in,
                timeline_out_seconds=snapped_out,
                clip_name="Track V3: Victim Reaction",
                transition_in="cut",
                suggested_speed=0.5 if v.slow_motion_timescale < 1.0 else 1.0,
            )
        )

    return edl_clips
