"""
tests/unit/test_voice_engine.py — Unit tests for Phase 3 Voice Timeline Engine.
"""

from __future__ import annotations

import os
import struct
import pytest
from backend.parser.voice import (
    _ogg_crc,
    make_ogg_page,
    mux_opus_to_ogg,
    convert_ogg_to_wav,
    check_demo_has_voice,
    get_round_voice_tracks,
    get_player_round_voice_audio,
)
from backend.storage.database import create_db_engine, get_session_factory, init_db
from backend.storage.models import DemoModel, PlayerModel, RoundModel
from backend.api.main import (
    get_demo_voice_status,
    get_round_voice_timeline,
    stream_player_round_voice,
    download_player_round_voice_wav,
)


def test_ogg_crc_and_page_generation():
    """Verify Ogg CRC algorithm and binary page header generation."""
    # Test vector: standard Ogg page with known CRC behavior
    serial = 42
    seq = 0
    granule = 0
    flags = 0x02  # BOS
    payload = [b"test_payload_123"]
    page = make_ogg_page(serial, seq, granule, flags, payload)

    assert page.startswith(b"OggS")
    assert page[4] == 0  # version 0
    assert page[5] == 0x02  # BOS flag
    # Check that CRC field (bytes 22..26) is non-zero
    crc_val = struct.unpack_from("<I", page, 22)[0]
    assert crc_val != 0


def test_mux_opus_to_ogg():
    """Verify muxing synthetic Opus frames into an RFC 7845 Ogg Opus byte stream."""
    # Create fake Opus frame (TOC byte 0x70 + 30 bytes of audio payload)
    fake_frame = bytes([0x70] + [0xAA] * 30)
    ogg_stream = mux_opus_to_ogg([fake_frame, fake_frame, fake_frame])

    assert len(ogg_stream) > 0
    assert ogg_stream.startswith(b"OggS")
    assert b"OpusHead" in ogg_stream
    assert b"OpusTags" in ogg_stream
    assert b"demtoshka" in ogg_stream


def test_convert_ogg_to_wav():
    """Verify transcoding Ogg Opus bytes to standard WAV."""
    demo_path = "demos/anubis1410.dem"
    if not os.path.isfile(demo_path):
        pytest.skip(f"Demo file not found at {demo_path}")

    # Extract real audio from speaker
    tracks = get_round_voice_tracks(demo_path, start_tick=1000, end_tick=15000)
    if not tracks:
        pytest.skip("No voice tracks found in tick range")

    first_sid = list(tracks.keys())[0]
    ogg_data = get_player_round_voice_audio(demo_path, first_sid, start_tick=1000, end_tick=15000)
    assert len(ogg_data) > 0

    wav_data = convert_ogg_to_wav(ogg_data)
    assert len(wav_data) > 44
    assert wav_data.startswith(b"RIFF")
    assert b"WAVE" in wav_data[:16]


def test_check_demo_has_voice_real_fixture():
    """Verify voice detection on real match demo."""
    demo_path = "demos/anubis1410.dem"
    if not os.path.isfile(demo_path):
        pytest.skip(f"Demo file not found at {demo_path}")

    has_voice, total_pkts, speakers = check_demo_has_voice(demo_path)
    assert has_voice is True
    assert total_pkts > 50000
    assert speakers == 10


def test_get_round_voice_tracks():
    """Verify round voice track segmentation and duration calculations."""
    demo_path = "demos/anubis1410.dem"
    if not os.path.isfile(demo_path):
        pytest.skip(f"Demo file not found at {demo_path}")

    tracks = get_round_voice_tracks(demo_path, start_tick=1000, end_tick=25000, tickrate=128)
    assert len(tracks) > 0

    for sid, track in tracks.items():
        assert track.packet_count > 0
        assert track.duration_sec > 0
        assert len(track.segments) > 0
        for seg in track.segments:
            assert seg.start_tick <= seg.end_tick
            assert seg.start_sec <= seg.end_sec
            assert seg.packet_count > 0


def test_voice_api_endpoints():
    """Verify FastAPI endpoints for voice status, round timeline, streaming and WAV download."""
    demo_path = "demos/anubis1410.dem"
    if not os.path.isfile(demo_path):
        pytest.skip(f"Demo file not found at {demo_path}")

    # Create temporary in-memory database
    engine = create_db_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = get_session_factory(engine)
    session = session_factory()

    try:
        # Seed test demo
        demo = DemoModel(
            file_path=os.path.abspath(demo_path),
            fingerprint="test_fp_voice_123",
            map_name="de_anubis",
            tickrate=128,
            schema_version="2.0.0",
        )
        session.add(demo)
        session.flush()

        # Seed round 1
        r1 = RoundModel(
            demo_id=demo.id,
            round_num=1,
            start_tick=1000,
            end_tick=10000,
            official_end_tick=10500,
        )
        session.add(r1)

        # Seed player
        p1 = PlayerModel(
            demo_id=demo.id,
            steam_id="76561199796084806",
            name="TopFragger",
            team="ct",
        )
        session.add(p1)
        session.commit()

        # 1. Voice Status Endpoint
        status_dto = get_demo_voice_status(demo_id=demo.id, db=session)
        assert status_dto.has_voice is True
        assert status_dto.total_packets > 0
        assert status_dto.unique_speakers == 10

        # 2. Round Voice Timeline Endpoint
        timeline_dto = get_round_voice_timeline(demo_id=demo.id, round_num=1, db=session)
        assert timeline_dto.has_voice is True
        assert timeline_dto.round_num == 1
        assert len(timeline_dto.tracks) > 0
        matching = next((t for t in timeline_dto.tracks if t.steamid == "76561199796084806"), None)
        if matching:
            assert matching.player_name == "TopFragger"
            assert matching.team == "ct"
            assert matching.stream_url.startswith(f"/api/demos/{demo.id}/rounds/1/voice/76561199796084806/stream")

        # 3. Stream Voice Endpoint
        stream_res = stream_player_round_voice(
            demo_id=demo.id,
            round_num=1,
            steamid="76561199796084806",
            db=session,
        )
        assert stream_res.media_type == "audio/ogg"
        assert len(stream_res.body) > 0
        assert stream_res.body.startswith(b"OggS")

        # 4. Download WAV Endpoint
        wav_res = download_player_round_voice_wav(
            demo_id=demo.id,
            round_num=1,
            steamid="76561199796084806",
            db=session,
        )
        assert wav_res.media_type == "audio/wav"
        assert len(wav_res.body) > 44
        assert wav_res.body.startswith(b"RIFF")

    finally:
        session.close()
