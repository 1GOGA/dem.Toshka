"""CLI utility for running a single test render (Stage G)."""

from __future__ import annotations

import argparse
import pathlib
import sys
import uuid

from backend.render.engine import RenderEngine
from backend.render.models import RenderTask


def main() -> int:
    parser = argparse.ArgumentParser(
        description="CS2 Highlights Studio — Single Clip Render CLI"
    )
    parser.add_argument(
        "--demo",
        type=pathlib.Path,
        default=pathlib.Path("tests/integration/fixtures/test.dem"),
        help="Path to .dem file",
    )
    parser.add_argument(
        "--start-tick",
        type=int,
        default=5822,
        help="Start tick of the clip (default: 5822)",
    )
    parser.add_argument(
        "--end-tick",
        type=int,
        default=7369,
        help="End tick of the clip (default: 7369)",
    )
    parser.add_argument(
        "--pov",
        type=str,
        default=None,
        help="POV player SteamID64 (optional)",
    )
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        default=pathlib.Path("renders/test_highlight.mp4"),
        help="Destination path for rendered MP4",
    )

    args = parser.parse_args()

    print(f"=== CS2 Highlights Studio — Video Render PoC ===")
    print(f"Demo file:    {args.demo}")
    print(f"Tick range:   {args.start_tick} - {args.end_tick}")
    print(f"POV SteamID:  {args.pov or 'Auto/Spectator'}")
    print(f"Destination:  {args.output}")

    engine = RenderEngine()
    task = RenderTask(
        task_id=f"test_{uuid.uuid4().hex[:6]}",
        demo_path=args.demo,
        start_tick=args.start_tick,
        end_tick=args.end_tick,
        pov_steam_id=args.pov,
        pov_name=None,
        output_path=args.output,
    )

    print(f"Estimated clip duration: {task.duration_seconds:.1f}s")
    print(f"Starting pipeline...")
    result = engine.render_clip(task)

    if result.success:
        print(f"\n[SUCCESS] Render completed!")
        print(f"Output MP4: {result.output_path}")
        print(f"Duration:   {result.duration_seconds:.2f}s")
        return 0
    else:
        print(f"\n[ERROR] Render failed:")
        print(f"Reason: {result.error_message}")
        if result.log_file and result.log_file.exists():
            print(f"Log:    {result.log_file}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

