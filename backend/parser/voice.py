"""
backend/parser/voice.py — CS2 In-Demo Voice Extraction and Demuxing Engine.

Handles:
- Extracting raw Opus voice packets from CS2 .dem files via demoparser2.
- Demuxing and grouping packets by player SteamID and round tick boundaries.
- Generating pure-Python RFC 7845 Ogg Opus byte streams without external C dependencies.
- Transcoding to standard WAV via FFmpeg for clean audio export and analysis.
- Graceful detection and fallback when voice data is omitted (e.g. Valve GOTV/MM).
"""

from __future__ import annotations

import logging
import os
import struct
import subprocess
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import demoparser2

logger = logging.getLogger(__name__)

# Cache of parsed voice packets per demo file path to avoid redundant expensive re-parsing
_VOICE_CACHE: Dict[str, List[dict]] = {}


def _ogg_crc(data: bytes) -> int:
    """Calculate 32-bit Ogg CRC checksum per RFC 3533."""
    poly = 0x04C11DB7
    crc_table = []
    for i in range(256):
        curr = i << 24
        for _ in range(8):
            if curr & 0x80000000:
                curr = ((curr << 1) ^ poly) & 0xFFFFFFFF
            else:
                curr = (curr << 1) & 0xFFFFFFFF
        crc_table.append(curr)

    crc = 0
    for b in data:
        crc = ((crc << 8) & 0xFFFFFFFF) ^ crc_table[((crc >> 24) & 0xFF) ^ b]
    return crc


def make_ogg_page(serial: int, seq: int, granule: int, flags: int, packets: List[bytes]) -> bytes:
    """
    Construct a binary Ogg page with segment table and CRC32 header.
    flags: 0x02 = BOS, 0x00 = continuation/normal, 0x04 = EOS.
    """
    seg_table = bytearray()
    body = bytearray()
    for pkt in packets:
        plen = len(pkt)
        while plen >= 255:
            seg_table.append(255)
            plen -= 255
        seg_table.append(plen)
        body.extend(pkt)

    # 27-byte header: magic(4), ver(1), flags(1), granule(8), serial(4), seq(4), crc(4), num_segs(1)
    header = bytearray(
        struct.pack(
            "<4sBBqIIIB",
            b"OggS",
            0,
            flags,
            granule,
            serial,
            seq,
            0,  # placeholder CRC
            len(seg_table),
        )
    )
    header.extend(seg_table)

    # Compute CRC over full header + body
    checksum = _ogg_crc(bytes(header) + bytes(body))
    struct.pack_into("<I", header, 22, checksum)
    return bytes(header) + bytes(body)


def mux_opus_to_ogg(packets: List[bytes], serial: int = 1337) -> bytes:
    """
    Mux raw CS2 Opus voice frames into a valid RFC 7845 Ogg Opus byte stream.
    Each frame is assumed to be 20ms @ 48000 Hz mono (960 samples).
    """
    if not packets:
        return b""

    out = bytearray()

    # 1. Page 0: OpusHead (BOS, flag=0x02)
    # Magic(8), Version(1), Channels(1), Pre-skip(2), SampleRate(4), Gain(2), Mapping(1)
    opus_head = struct.pack("<8sBBHIhB", b"OpusHead", 1, 1, 0, 48000, 0, 0)
    out.extend(make_ogg_page(serial, 0, 0, 0x02, [opus_head]))

    # 2. Page 1: OpusTags (Comment Header, flag=0x00)
    vendor = b"demtoshka"
    opus_tags = struct.pack("<8sI", b"OpusTags", len(vendor)) + vendor + struct.pack("<I", 0)
    out.extend(make_ogg_page(serial, 1, 0, 0x00, [opus_tags]))

    # 3. Audio data pages (up to 50 packets per Ogg page)
    seq = 2
    granule = 0
    batch: List[bytes] = []

    for i, pkt in enumerate(packets):
        batch.append(pkt)
        granule += 960  # 20ms @ 48kHz = 960 samples per frame
        if len(batch) >= 50 or i == len(packets) - 1:
            flags = 0x04 if i == len(packets) - 1 else 0x00  # EOS on last page
            out.extend(make_ogg_page(serial, seq, granule, flags, batch))
            seq += 1
            batch = []

    return bytes(out)


def convert_ogg_to_wav(ogg_bytes: bytes) -> bytes:
    """Transcode Ogg Opus bytes to standard 48kHz 16-bit PCM WAV in-memory via FFmpeg."""
    if not ogg_bytes:
        return b""

    try:
        proc = subprocess.Popen(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", "pipe:0", "-f", "wav", "pipe:1"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = proc.communicate(input=ogg_bytes, timeout=15)
        if proc.returncode != 0:
            logger.error(f"FFmpeg audio conversion failed: {stderr.decode('utf-8', errors='replace')}")
            return b""
        return stdout
    except Exception as e:
        logger.error(f"Failed to transcode voice audio: {e}")
        return b""


def extract_raw_voice(demo_path: str) -> List[dict]:
    """
    Extract raw voice packets from demo file.
    Cached in memory to prevent repeatedly reading large demo files.
    """
    if not os.path.isfile(demo_path):
        return []

    if demo_path in _VOICE_CACHE:
        return _VOICE_CACHE[demo_path]

    try:
        parser = demoparser2.DemoParser(demo_path)
        packets = parser.parse_voice()
        if packets is None:
            packets = []
        _VOICE_CACHE[demo_path] = packets
        return packets
    except Exception as e:
        logger.warning(f"Failed to parse voice data from {demo_path}: {e}")
        _VOICE_CACHE[demo_path] = []
        return []


def check_demo_has_voice(demo_path: str) -> Tuple[bool, int, int]:
    """
    Check if the demo contains any voice data.
    Returns (has_voice, total_packet_count, unique_speakers_count).
    """
    packets = extract_raw_voice(demo_path)
    if not packets:
        return False, 0, 0

    speakers = set(p.get("steamid") for p in packets if p.get("steamid"))
    return True, len(packets), len(speakers)


@dataclass
class VoiceSpeechSegment:
    start_tick: int
    end_tick: int
    start_sec: float
    end_sec: float
    packet_count: int


@dataclass
class PlayerVoiceTrack:
    steamid: str
    packet_count: int
    segments: List[VoiceSpeechSegment]
    duration_sec: float


def get_round_voice_tracks(
    demo_path: str,
    start_tick: int,
    end_tick: int,
    tickrate: int = 128,
) -> Dict[str, PlayerVoiceTrack]:
    """
    Group voice packets by player SteamID within [start_tick, end_tick] of a round.
    Calculates contiguous speech segments (bursts separated by > 0.5s silence).
    """
    packets = extract_raw_voice(demo_path)
    if not packets:
        return {}

    round_packets = [p for p in packets if start_tick <= p.get("tick", 0) <= end_tick]
    if not round_packets:
        return {}

    # Group packets by string SteamID
    speaker_map: Dict[str, List[dict]] = {}
    for p in round_packets:
        sid = str(p.get("steamid", ""))
        if not sid or sid == "0":
            continue
        speaker_map.setdefault(sid, []).append(p)

    tracks: Dict[str, PlayerVoiceTrack] = {}
    silence_gap_ticks = int(0.5 * tickrate)

    for sid, spkts in speaker_map.items():
        spkts.sort(key=lambda x: x.get("tick", 0))

        # Detect speech segments
        segments: List[VoiceSpeechSegment] = []
        curr_start = spkts[0]["tick"]
        curr_last = spkts[0]["tick"]
        curr_count = 1

        for pkt in spkts[1:]:
            t = pkt["tick"]
            if t - curr_last > silence_gap_ticks:
                # Close segment
                s_sec = max(0.0, (curr_start - start_tick) / tickrate)
                e_sec = max(0.0, (curr_last - start_tick) / tickrate) + 0.05
                segments.append(
                    VoiceSpeechSegment(
                        start_tick=curr_start,
                        end_tick=curr_last,
                        start_sec=round(s_sec, 2),
                        end_sec=round(e_sec, 2),
                        packet_count=curr_count,
                    )
                )
                curr_start = t
                curr_last = t
                curr_count = 1
            else:
                curr_last = t
                curr_count += 1

        # Close final segment
        s_sec = max(0.0, (curr_start - start_tick) / tickrate)
        e_sec = max(0.0, (curr_last - start_tick) / tickrate) + 0.05
        segments.append(
            VoiceSpeechSegment(
                start_tick=curr_start,
                end_tick=curr_last,
                start_sec=round(s_sec, 2),
                end_sec=round(e_sec, 2),
                packet_count=curr_count,
            )
        )

        tracks[sid] = PlayerVoiceTrack(
            steamid=sid,
            packet_count=len(spkts),
            segments=segments,
            duration_sec=round(len(spkts) * 0.02, 2),  # each frame ~20ms
        )

    return tracks


def get_player_round_voice_audio(
    demo_path: str,
    steamid: str,
    start_tick: int,
    end_tick: int,
) -> bytes:
    """
    Extract all voice packets for a specific player during a round,
    and mux them into a single playable Ogg Opus byte stream.
    """
    packets = extract_raw_voice(demo_path)
    if not packets:
        return b""

    player_packets = [
        p["bytes"]
        for p in packets
        if str(p.get("steamid", "")) == str(steamid) and start_tick <= p.get("tick", 0) <= end_tick
    ]

    return mux_opus_to_ogg(player_packets)
