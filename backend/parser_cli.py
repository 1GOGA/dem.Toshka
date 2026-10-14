"""CLI entry point for the CS2 demo parser.

Usage:
    python -m backend.parser_cli PATH_TO_DEMO.dem [--output results.json] [--player STEAMID]

Options:
    PATH_TO_DEMO.dem    Path to the .dem file to parse.
    --output PATH       Write full JSON output to PATH (optional).
    --player STEAMID    Filter summary to a specific player's kills (optional).
    --verbose           Enable verbose Awpy logging.
    --version           Show parser/schema version and exit.

Exit codes:
    0  — success
    1  — invalid path / extension / file too small
    2  — Awpy/demoparser2 parse error
    3  — unexpected error
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from backend.parser.models import SCHEMA_VERSION


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m backend.parser_cli",
        description="CS2 Highlights Studio — demo parser CLI (Awpy 2.0.2)",
    )
    p.add_argument("demo", nargs="?", help="Path to the .dem file")
    p.add_argument("--output", "-o", metavar="PATH", help="Save full JSON to this path")
    p.add_argument("--player", "-p", metavar="STEAMID", help="Filter kills to this SteamID")
    p.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    p.add_argument(
        "--version",
        action="version",
        version=f"CS2 Highlights Studio parser — schema v{SCHEMA_VERSION}, Awpy 2.0.2",
    )
    return p


def _print_summary(result, player_filter: str | None) -> None:
    """Print a human-readable summary to stdout."""
    from backend.parser.models import ParsedDemo  # local import for test isolation

    print("=" * 60)
    print(f"  Map:       {result.map_name or 'unknown'}")
    print(f"  Tickrate:  {result.tickrate}")
    print(f"  Rounds:    {len(result.rounds)}")
    print(f"  Players:   {len(result.players)}")
    print(f"  Kills:     {len(result.kills)}")
    print(f"  Schema:    v{result.schema_version}")
    print("=" * 60)

    # Players table
    if result.players:
        print("\nPLAYERS:")
        print(f"  {'Name':<24} {'SteamID':<20} Team")
        print(f"  {'-'*24} {'-'*20} ----")
        for p in result.players:
            sid = p.steam_id or "(bot/unknown)"
            team = p.team or "?"
            print(f"  {p.name:<24} {sid:<20} {team}")

    # Kill summary
    kills_to_show = result.kills
    if player_filter:
        kills_to_show = [
            k for k in result.kills
            if k.attacker_steam_id == player_filter
        ]
        print(f"\nKILLS by {player_filter} ({len(kills_to_show)} total):")
    else:
        print(f"\nKILLS (first 20 of {len(result.kills)}):")
        kills_to_show = kills_to_show[:20]

    if kills_to_show:
        print(f"  {'Tick':>8}  {'Rnd':>4}  {'Attacker':<20} {'Victim':<20} {'Weapon':<16} HS  NK  TK")
        print(f"  {'-'*8}  {'-'*4}  {'-'*20} {'-'*20} {'-'*16} --  --  --")
        for k in kills_to_show:
            rnd = str(k.round_num) if k.round_num is not None else "?"
            att = (k.attacker_name or "unknown")[:20]
            vic = (k.victim_name or "unknown")[:20]
            wpn = (k.weapon or "unknown")[:16]
            hs = "Y" if k.headshot else "N" if k.headshot is not None else "?"
            nk = "Y" if k.is_suicide else "N"
            tk = "Y" if k.is_teamkill else "N"
            print(f"  {k.tick:>8}  {rnd:>4}  {att:<20} {vic:<20} {wpn:<16} {hs:<3} {nk:<3} {tk}")
    else:
        print("  (no kills to display)")

    # Rounds summary
    if result.rounds:
        print(f"\nROUNDS (first 5 of {len(result.rounds)}):")
        print(f"  {'Rnd':>4}  {'Start':>8}  {'End':>8}  Winner  Bomb site")
        print(f"  {'-'*4}  {'-'*8}  {'-'*8}  ------  ---------")
        for r in result.rounds[:5]:
            site = r.bomb_site or "-"
            winner = r.winner or "?"
            print(f"  {r.round_num:>4}  {r.start_tick:>8}  {r.end_tick:>8}  {winner:<6}  {site}")

    print()


def main(argv: list[str] | None = None) -> int:
    """CLI entry point.  Returns an exit code."""
    args = _build_arg_parser().parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s: %(message)s",
    )

    if args.demo is None:
        print("ERROR: No demo path provided. Use --help for usage.", file=sys.stderr)
        return 1

    demo_path = Path(args.demo)

    # ---- Validate & parse ----
    from backend.parser.errors import DemoParseError, InvalidDemoPathError
    from backend.parser.ingestion import ingest
    from backend.parser.serializer import save_json

    try:
        result = ingest(demo_path)
    except InvalidDemoPathError as exc:
        print(f"ERROR (invalid path): {exc}", file=sys.stderr)
        return 1
    except DemoParseError as exc:
        print(f"ERROR (parse failed): {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"ERROR (unexpected): {exc}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 3

    # ---- Print summary ----
    _print_summary(result, player_filter=args.player)

    # ---- Optional JSON output ----
    if args.output:
        out_path = Path(args.output)
        try:
            save_json(result, out_path)
            print(f"JSON saved to: {out_path}")
        except OSError as exc:
            print(f"ERROR: Could not write output file: {exc}", file=sys.stderr)
            return 3

    return 0


if __name__ == "__main__":
    sys.exit(main())
