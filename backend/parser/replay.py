"""2D Tactical Replay Data Extractor for CS2 Highlights Studio.

Extracts real world player coordinates, health, team sides, and kill events
from Awpy dem.ticks and dem.kills for a specific round, downsampling to an optimal
playback rate for responsive 2D vector radar replay.
"""

from __future__ import annotations

import logging
import pathlib
from typing import Any, Optional

logger = logging.getLogger("demtoshka.replay")

# Official CS2 Map Overview Calibration Data (Valve Source 2 Standard)
# Coordinate transform:
# pixel_x = (X - pos_x) / scale
# pixel_y = (pos_y - Y) / scale
MAP_CALIBRATIONS: dict[str, dict[str, Any]] = {
    "de_dust2": {
        "pos_x": -2476.0,
        "pos_y": 3239.0,
        "scale": 4.4,
        "split_z": None,
        "levels": ["main"],
        "radar_file": "de_dust2.png",
    },
    "de_mirage": {
        "pos_x": -3230.0,
        "pos_y": 1713.0,
        "scale": 5.0,
        "split_z": None,
        "levels": ["main"],
        "radar_file": "de_mirage.png",
    },
    "de_inferno": {
        "pos_x": -2087.0,
        "pos_y": 3870.0,
        "scale": 4.9,
        "split_z": None,
        "levels": ["main"],
        "radar_file": "de_inferno.png",
    },
    "de_nuke": {
        "pos_x": -3453.0,
        "pos_y": 2887.0,
        "scale": 7.0,
        "split_z": -400.0,
        "levels": ["upper", "lower"],
        "radar_file": "de_nuke.png",
        "radar_file_lower": "de_nuke_lower.png",
    },
    "de_ancient": {
        "pos_x": -2953.0,
        "pos_y": 2164.0,
        "scale": 5.0,
        "split_z": None,
        "levels": ["main"],
        "radar_file": "de_ancient.png",
    },
    "de_anubis": {
        "pos_x": -2796.0,
        "pos_y": 3328.0,
        "scale": 5.22,
        "split_z": None,
        "levels": ["main"],
        "radar_file": "de_anubis.png",
    },
    "de_vertigo": {
        "pos_x": -3168.0,
        "pos_y": 1762.0,
        "scale": 4.0,
        "split_z": 11700.0,
        "levels": ["upper", "lower"],
        "radar_file": "de_vertigo.png",
        "radar_file_lower": "de_vertigo_lower.png",
    },
    "de_overpass": {
        "pos_x": -4831.0,
        "pos_y": 1781.0,
        "scale": 5.2,
        "split_z": None,
        "levels": ["main"],
        "radar_file": "de_overpass.png",
    },
    "cs_office": {
        "pos_x": -1838.0,
        "pos_y": 1858.0,
        "scale": 4.1,
        "split_z": None,
        "levels": ["main"],
        "radar_file": "cs_office.png",
    },
    "cs_italy": {
        "pos_x": -2647.0,
        "pos_y": 2592.0,
        "scale": 4.6,
        "split_z": None,
        "levels": ["main"],
        "radar_file": "cs_italy.png",
    },
    "de_train": {
        "pos_x": -2308.0,
        "pos_y": 2078.0,
        "scale": 4.08,
        "split_z": -100.0,
        "levels": ["upper", "lower"],
        "radar_file": "de_train.png",
        "radar_file_lower": "de_train_lower.png",
    },
}

DEFAULT_CALIBRATION = {
    "pos_x": -3000.0,
    "pos_y": 3000.0,
    "scale": 6.0,
    "split_z": None,
    "levels": ["main"],
    "radar_file": None,
}

# In-memory high performance caches
_DEMO_OBJ_CACHE: dict[str, Any] = {}
_REPLAY_DATA_CACHE: dict[tuple[str, int, int], dict[str, Any]] = {}


def world_to_radar_percent(
    x: float,
    y: float,
    map_name: str = "de_nuke",
) -> tuple[float, float]:
    """Convert world 3D coordinates (X, Y) into radar coordinates (0%..100%)."""
    norm_map = (map_name or "de_nuke").lower().replace(".vpk", "")
    cal = MAP_CALIBRATIONS.get(norm_map, DEFAULT_CALIBRATION)

    pos_x = cal["pos_x"]
    pos_y = cal["pos_y"]
    scale = cal["scale"]

    pixel_x = (x - pos_x) / scale
    pixel_y = (pos_y - y) / scale

    # Map radar image standard resolution 1024x1024
    pct_x = max(2.0, min(98.0, (pixel_x / 1024.0) * 100.0))
    pct_y = max(2.0, min(98.0, (pixel_y / 1024.0) * 100.0))
    return round(pct_x, 2), round(pct_y, 2)


def extract_round_replay_data(
    demo_path: pathlib.Path,
    round_num: int,
    step_ticks: int = 16,
) -> dict[str, Any]:
    """Extract round replay frames and kill markers from demo file using Awpy.

    Downsamples tick frames by `step_ticks` (default 16 ~ 8 frames/second at 128 tickrate).
    """
    cache_key = (str(demo_path.resolve()), round_num, step_ticks)
    if cache_key in _REPLAY_DATA_CACHE:
        return _REPLAY_DATA_CACHE[cache_key]

    from awpy.demo import Demo

    if not demo_path.is_file():
        raise FileNotFoundError(f"Demo file not found at {demo_path}")

    demo_key = str(demo_path.resolve())
    if demo_key not in _DEMO_OBJ_CACHE:
        dem = Demo(demo_key)
        dem.parse()
        _DEMO_OBJ_CACHE[demo_key] = dem
    else:
        dem = _DEMO_OBJ_CACHE[demo_key]

    map_name = (dem.header.get("map_name") or "de_nuke").lower()
    tickrate = dem.tickrate or 128

    # 1. Filter ticks for this round
    ticks_df = dem.ticks.filter(dem.ticks["round_num"] == round_num)
    if len(ticks_df) == 0:
        return {
            "round_num": round_num,
            "map_name": map_name,
            "tickrate": tickrate,
            "start_tick": 0,
            "end_tick": 0,
            "frames": [],
            "kills": [],
            "players": {},
        }

    start_tick = int(ticks_df["tick"].min())
    end_tick = int(ticks_df["tick"].max())

    # Build player metadata dictionary
    players_dict: dict[str, dict[str, Any]] = {}
    player_rows = (
        ticks_df.select(["name", "steamid", "side"]).unique(subset=["steamid"]).to_dicts()
    )
    for p in player_rows:
        sid = str(p.get("steamid") or "")
        if sid:
            players_dict[sid] = {
                "steam_id": sid,
                "name": str(p.get("name") or "Player"),
                "side": str(p.get("side") or "ct").lower(),
            }

    # 2. Extract downsampled tick frames
    unique_ticks = sorted(ticks_df["tick"].unique().to_list())
    selected_ticks = unique_ticks[::step_ticks]
    if unique_ticks and unique_ticks[-1] not in selected_ticks:
        selected_ticks.append(unique_ticks[-1])

    frames_list: list[dict[str, Any]] = []

    cal = MAP_CALIBRATIONS.get(map_name, DEFAULT_CALIBRATION)
    split_z = cal.get("split_z")

    # Fast group-by tick
    downsampled_df = ticks_df.filter(ticks_df["tick"].is_in(selected_ticks))
    for row in downsampled_df.to_dicts():
        t = int(row["tick"])
        sid = str(row.get("steamid") or "")
        x = float(row.get("X") or 0.0)
        y = float(row.get("Y") or 0.0)
        z = float(row.get("Z") or 0.0)
        hp = float(row.get("health") or 0.0)
        side = str(row.get("side") or "ct").lower()
        place = str(row.get("place") or "")

        pct_x, pct_y = world_to_radar_percent(x, y, map_name)
        level = "lower" if (split_z is not None and z < split_z) else "upper"

        # Find or create frame
        if not frames_list or frames_list[-1]["tick"] != t:
            frames_list.append({"tick": t, "players": []})

        frames_list[-1]["players"].append({
            "steam_id": sid,
            "name": row.get("name") or players_dict.get(sid, {}).get("name", "Player"),
            "side": side,
            "health": hp,
            "x": pct_x,
            "y": pct_y,
            "world_z": z,
            "level": level,
            "place": place,
            "is_alive": hp > 0,
        })

    # 3. Extract kills in this round
    kills_list: list[dict[str, Any]] = []
    round_kills = dem.kills.filter(dem.kills["round_num"] == round_num)
    for k in round_kills.to_dicts():
        atk_x, atk_y = world_to_radar_percent(
            float(k.get("attacker_X") or 0.0), float(k.get("attacker_Y") or 0.0), map_name
        )
        vic_x, vic_y = world_to_radar_percent(
            float(k.get("victim_X") or 0.0), float(k.get("victim_Y") or 0.0), map_name
        )
        kills_list.append({
            "tick": int(k.get("tick") or 0),
            "attacker_name": str(k.get("attacker_name") or "Attacker"),
            "attacker_steam_id": str(k.get("attacker_steamid") or ""),
            "attacker_side": str(k.get("attacker_side") or "ct").lower(),
            "attacker_x": atk_x,
            "attacker_y": atk_y,
            "victim_name": str(k.get("victim_name") or "Victim"),
            "victim_steam_id": str(k.get("victim_steamid") or ""),
            "victim_side": str(k.get("victim_side") or "t").lower(),
            "victim_x": vic_x,
            "victim_y": vic_y,
            "weapon": str(k.get("weapon") or "weapon_rifle"),
            "headshot": bool(k.get("headshot")),
        })

    cal = MAP_CALIBRATIONS.get(map_name, DEFAULT_CALIBRATION)
    res = {
        "round_num": round_num,
        "map_name": map_name,
        "tickrate": tickrate,
        "start_tick": start_tick,
        "end_tick": end_tick,
        "radar_file": cal.get("radar_file"),
        "radar_file_lower": cal.get("radar_file_lower"),
        "levels": cal.get("levels", ["main"]),
        "frames": frames_list,
        "kills": kills_list,
        "players": players_dict,
    }
    _REPLAY_DATA_CACHE[cache_key] = res
    return res


def get_highlights_radar_coords(
    demo_path: pathlib.Path,
    highlights: list[Any],
    map_name: str,
) -> dict[str, dict[str, Any]]:
    """Look up real killer and victim radar percentage coordinates for a list of highlights."""
    if not demo_path.is_file():
        return {}

    demo_key = str(demo_path.resolve())
    if demo_key not in _DEMO_OBJ_CACHE:
        try:
            from awpy.demo import Demo

            dem = Demo(demo_key)
            dem.parse()
            _DEMO_OBJ_CACHE[demo_key] = dem
        except Exception as e:
            logger.warning("Could not parse demo for radar coordinates: %s", e)
            return {}
    else:
        dem = _DEMO_OBJ_CACHE[demo_key]

    cal = MAP_CALIBRATIONS.get(map_name, DEFAULT_CALIBRATION)
    split_z = cal.get("split_z")

    try:
        kills_df = dem.kills
        kills_records = kills_df.to_dicts()
    except Exception:
        return {}

    coords_map: dict[str, dict[str, Any]] = {}
    for h in highlights:
        h_id = getattr(h, "id", None)
        h_round = getattr(h, "round_num", None)
        h_steam = getattr(h, "pov_steam_id", None)
        h_start = getattr(h, "kill_start_tick", None)

        matched_kill = None
        for k in kills_records:
            if k.get("round_num") == h_round:
                k_tick = k.get("tick")
                k_steam = str(k.get("attacker_steamid") or "")
                if (h_steam and k_steam == str(h_steam)) or (
                    h_start and abs(int(k_tick or 0) - int(h_start)) < 16
                ):
                    matched_kill = k
                    break

        if matched_kill:
            atk_x = float(matched_kill.get("attacker_X") or 0.0)
            atk_y = float(matched_kill.get("attacker_Y") or 0.0)
            atk_z = float(matched_kill.get("attacker_Z") or 0.0)
            vic_x = float(matched_kill.get("victim_X") or 0.0)
            vic_y = float(matched_kill.get("victim_Y") or 0.0)

            rx, ry = world_to_radar_percent(atk_x, atk_y, map_name)
            vrx, vry = world_to_radar_percent(vic_x, vic_y, map_name)
            lvl = "lower" if (split_z is not None and atk_z < split_z) else "upper"

            coords_map[h_id] = {
                "radar_x": rx,
                "radar_y": ry,
                "victim_radar_x": vrx,
                "victim_radar_y": vry,
                "radar_level": lvl,
            }

    return coords_map


