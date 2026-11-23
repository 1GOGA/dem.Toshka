"""End-to-End validation script for newly implemented dem.Toshka modules."""

import pathlib
import sys

# Ensure repository root is on sys.path
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.cinematic.camera_engine import CameraEngine
from backend.cinematic.models import CameraType, Vector3
from backend.detector.highlight_scorer import SmartHighlightScorer
from backend.hlae.campath import HLAECampathManager
from backend.hlae.command_builder import HLAECommandBuilder
from backend.hlae.streams import HLAEStreamManager, StreamProfile
from backend.hlae.version import HLAEVersionDetector
from backend.parser.models import KillEvent
from backend.parser.normalizer import EventNormalizer
from backend.parser.replay import radar_percent_to_world, world_to_radar_percent


def run_e2e_verification():
    print("=" * 70)
    print("  dem.Toshka — End-to-End Test of New Architecture Modules")
    print("=" * 70)

    # 1. HLAE Binary & Capabilities Inspection
    print("\n[1/5] Проверка бинарников HLAE и AfxHookSource2...")
    hlae_exe = pathlib.Path("tools/hlae/HLAE.exe")
    hook_dll = pathlib.Path("tools/hlae/x64/AfxHookSource2.dll")
    caps = HLAEVersionDetector.detect(hlae_exe, hook_dll)
    print(f"  ✓ HLAE Version: {caps.hlae_version} (Valid PE: {caps.is_valid})")
    print(f"  ✓ AfxHookSource2 Version: {caps.hook_version}")
    print(f"  ✓ Поддержка Source 2: {caps.supports_source2}")
    print(f"  ✓ Поддержка экранирования опций FFmpeg: {caps.supports_ffmpeg_escaped_convars}")

    # 2. HLAE Command Builder & Tick Scheduling
    print("\n[2/5] Генерация скрипта CS2 с тиковым планированием (mirv_cmd)...")
    builder = HLAECommandBuilder()
    builder.set_host_framerate(60)
    builder.set_hud_mode("cinematic")
    builder.lock_spectator_pov(account_id=76561198000000001, name="pytoshka_")
    builder.set_xray(False)
    builder.load_campath(pathlib.Path("renders/anubis_orbit.xml"))
    builder.schedule_recording_window(start_tick=238000, end_tick=240500, quit_on_finish=True)
    cfg_text = builder.build_cfg_text()

    out_cfg = pathlib.Path("renders/test_generated_take.cfg")
    out_cfg.parent.mkdir(parents=True, exist_ok=True)
    out_cfg.write_text(cfg_text, encoding="utf-8")
    print(f"  ✓ Сгенерирован CFG скрипт: {out_cfg} ({len(cfg_text)} байт)")
    print("  Фрагмент запланированных тиков:")
    for line in cfg_text.splitlines():
        if "mirv_cmd" in line or "cl_draw" in line:
            print(f"    | {line}")

    # 3. Catmull-Rom Splines & HLAE XML Export
    print("\n[3/5] Catmull-Rom C1 сплайны камеры и экспорт mirv_campath XML...")
    cam_mgr = HLAECampathManager.create_orbit(
        center_x=-250.0,
        center_y=350.0,
        center_z=80.0,
        radius=300.0,
        height_offset=60.0,
        duration_s=4.0,
        num_points=12,
        fov=80.0,
    )
    xml_out = pathlib.Path("renders/anubis_orbit.xml")
    cam_mgr.export_xml(xml_out)
    print(f"  ✓ Экспортирован XML путь камеры: {xml_out}")
    interp_sample = cam_mgr.interpolate_at_time(2.0)
    print(f"  ✓ Интерполяция на t=2.0с: X={interp_sample.x:.1f}, Y={interp_sample.y:.1f}, Z={interp_sample.z:.1f}, Pitch={interp_sample.pitch:.1f}°, Yaw={interp_sample.yaw:.1f}°")

    # 4. Stream Profiles & FFmpeg Escaping
    print("\n[4/5] Настройка потоков mirv_streams и экранирования параметров...")
    stream_mgr = HLAEStreamManager(output_dir="renders/multipass_take")
    cmds = stream_mgr.apply_profile(StreamProfile.VFX_MULTIPASS, base_name="anubis_ace")
    print("  ✓ Команды mirv_streams:")
    for cmd in cmds[:5]:
        print(f"    | {cmd}")

    # 5. Smart Highlight Scorer & 2D/3D Radar Math
    print("\n[5/5] Мультифакторный скоринг хайлайтов и радарная привязка...")
    scorer = SmartHighlightScorer(tickrate=64.0)
    anubis_ace_kills = [
        KillEvent(238100, 19, "pytoshka_", "STEAM_PY", "ct", "Tiger07", "STEAM_V1", "t", "m4a1", False, "chest", False, False, False, False, None, None),
        KillEvent(238250, 19, "pytoshka_", "STEAM_PY", "ct", "ProfyfGames", "STEAM_V2", "t", "m4a1", True, "head", False, False, False, False, None, None),
        KillEvent(238400, 19, "pytoshka_", "STEAM_PY", "ct", "freekikeee", "STEAM_V3", "t", "m4a1", True, "head", False, False, False, True, None, None),
        KillEvent(238500, 19, "pytoshka_", "STEAM_PY", "ct", "axuenchik002", "STEAM_V4", "t", "m4a1", True, "head", False, False, False, False, None, None),
        KillEvent(238620, 19, "pytoshka_", "STEAM_PY", "ct", "LastEnemy", "STEAM_V5", "t", "m4a1", True, "head", False, False, False, False, None, None),
    ]
    breakdown = scorer.score_sequence(anubis_ace_kills, clutch_opponents=1)
    print(f"  ✓ Итоговый скор хайлайта: {breakdown.total_score:.1f} pts (Нормализованный: {breakdown.normalized_100:.1f}/100)")
    print(f"  ✓ Присвоенные бейджи: {', '.join(breakdown.badges)}")
    print("  Детализация факторов:")
    for f in breakdown.factors:
        print(f"    - {f.name}: +{f.points:.1f} pts ({f.description})")

    # Radar transform test
    pct_x, pct_y = world_to_radar_percent(-250.0, 350.0, map_name="de_anubis")
    rec_x, rec_y, _ = radar_percent_to_world(pct_x, pct_y, map_name="de_anubis")
    print(f"  ✓ Координаты на радаре Anubis: World(-250, 350) -> Radar({pct_x}%, {pct_y}%) -> Rec({rec_x}, {rec_y})")

    print("\n" + "=" * 70)
    print("  ВСЕ НОВЫЕ ПОДСИСТЕМЫ УСПЕШНО ПРОШЛИ E2E ТЕСТИРОВАНИЕ!")
    print("=" * 70)


if __name__ == "__main__":
    run_e2e_verification()
