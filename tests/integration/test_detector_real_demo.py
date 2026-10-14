"""Integration tests — Highlight Detector on real CS2 demo (de_nuke).

Requires tests/integration/fixtures/test.dem to be present.
Run with:
    .venv\\Scripts\\pytest tests/integration/test_detector_real_demo.py -v

Verifications:
  - At least 1 highlight found
  - No highlight clip crosses round boundary (official_end_tick)
  - All clip_start_tick >= round.start_tick
  - All IDs are unique (deduplication works)
  - Stats printed to stdout
"""

from __future__ import annotations

import pathlib
import pytest

from backend.parser.adapter import parse_demo
from backend.detector.highlight_detector import detect_highlights
from backend.detector.models import DetectorSettings, HighlightType


FIXTURE_PATH = pathlib.Path(__file__).parent / "fixtures" / "test.dem"


def skip_if_no_fixture():
    if not FIXTURE_PATH.exists():
        pytest.skip(f"Fixture demo not found: {FIXTURE_PATH}")


@pytest.fixture(scope="module")
def parsed_demo():
    skip_if_no_fixture()
    return parse_demo(FIXTURE_PATH)


@pytest.fixture(scope="module")
def highlights(parsed_demo):
    return detect_highlights(parsed_demo)


@pytest.fixture(scope="module")
def round_map(parsed_demo):
    return {r.round_num: r for r in parsed_demo.rounds}


# ---------------------------------------------------------------------------
# Basic sanity
# ---------------------------------------------------------------------------


class TestHighlightBasics:
    def test_at_least_one_highlight_found(self, highlights):
        assert len(highlights) > 0, "Expected at least 1 highlight on de_nuke demo"

    def test_highlights_are_sorted_by_round_then_tick(self, highlights):
        for i in range(len(highlights) - 1):
            a = highlights[i]
            b = highlights[i + 1]
            assert (a.round_num, a.kill_start_tick) <= (b.round_num, b.kill_start_tick), (
                f"Highlights not sorted: {a.id} before {b.id}"
            )

    def test_all_ids_unique(self, highlights):
        ids = [h.id for h in highlights]
        assert len(ids) == len(set(ids)), f"Duplicate IDs: {[id for id in ids if ids.count(id) > 1]}"

    def test_highlight_types_valid(self, highlights):
        valid_types = set(HighlightType)
        for h in highlights:
            assert h.highlight_type in valid_types

    def test_kill_count_positive(self, highlights):
        for h in highlights:
            assert h.kill_count >= 1


# ---------------------------------------------------------------------------
# Round boundary invariants
# ---------------------------------------------------------------------------


class TestRoundBoundaryInvariants:
    def test_clip_start_gte_round_start(self, highlights, round_map):
        for h in highlights:
            r = round_map[h.round_num]
            assert h.clip_start_tick >= r.start_tick, (
                f"Highlight {h.id}: clip_start {h.clip_start_tick} < round_start {r.start_tick}"
            )

    def test_clip_end_lte_round_official_end(self, highlights, round_map):
        for h in highlights:
            r = round_map[h.round_num]
            upper = r.official_end_tick if r.official_end_tick is not None else r.end_tick
            assert h.clip_end_tick <= upper, (
                f"Highlight {h.id}: clip_end {h.clip_end_tick} > round upper {upper}"
            )

    def test_kill_start_lte_kill_end(self, highlights):
        for h in highlights:
            assert h.kill_start_tick <= h.kill_end_tick, (
                f"Highlight {h.id}: kill_start {h.kill_start_tick} > kill_end {h.kill_end_tick}"
            )

    def test_clip_start_lte_clip_end(self, highlights):
        for h in highlights:
            assert h.clip_start_tick <= h.clip_end_tick, (
                f"Highlight {h.id}: clip_start {h.clip_start_tick} > clip_end {h.clip_end_tick}"
            )


# ---------------------------------------------------------------------------
# Heuristic flags
# ---------------------------------------------------------------------------


class TestHeuristicFlags:
    def test_multikill_is_not_heuristic(self, highlights):
        for h in highlights:
            if h.highlight_type in (
                HighlightType.KILL,
                HighlightType.MULTIKILL_2K,
                HighlightType.MULTIKILL_3K,
                HighlightType.MULTIKILL_4K,
                HighlightType.ACE,
            ):
                assert not h.is_heuristic, f"{h.id} should not be heuristic"

    def test_clutch_candidates_are_heuristic(self, highlights):
        for h in highlights:
            if h.highlight_type == HighlightType.CLUTCH_CANDIDATE:
                assert h.is_heuristic, f"{h.id} clutch should be heuristic"


# ---------------------------------------------------------------------------
# Multikill hierarchy
# ---------------------------------------------------------------------------


class TestMultikillHierarchy:
    def test_ace_kill_count_gte_5(self, highlights):
        for h in highlights:
            if h.highlight_type == HighlightType.ACE:
                assert h.kill_count >= 5

    def test_4k_kill_count_is_4(self, highlights):
        for h in highlights:
            if h.highlight_type == HighlightType.MULTIKILL_4K:
                assert h.kill_count == 4

    def test_3k_kill_count_is_3(self, highlights):
        for h in highlights:
            if h.highlight_type == HighlightType.MULTIKILL_3K:
                assert h.kill_count == 3

    def test_2k_kill_count_is_2(self, highlights):
        for h in highlights:
            if h.highlight_type == HighlightType.MULTIKILL_2K:
                assert h.kill_count == 2


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------


class TestTagsOnRealDemo:
    def test_tags_are_subset_of_known(self, highlights):
        known_tags = {"headshot", "wallbang", "noscope", "thru_smoke", "blind"}
        for h in highlights:
            unknown = set(h.tags) - known_tags
            assert not unknown, f"Unknown tags in {h.id}: {unknown}"

    def test_tags_are_sorted(self, highlights):
        for h in highlights:
            assert h.tags == sorted(h.tags), f"Tags not sorted in {h.id}: {h.tags}"


# ---------------------------------------------------------------------------
# Stats printout (always shown in verbose mode)
# ---------------------------------------------------------------------------


class TestStatsPrintout:
    def test_print_summary(self, highlights, parsed_demo, capsys):
        """Print summary stats — acts as a smoke test and useful diagnostic."""
        from collections import Counter
        type_counts = Counter(h.highlight_type.value for h in highlights)
        total = len(highlights)

        print(f"\n=== Highlight Detector Results ({parsed_demo.map_name}) ===")
        print(f"Total highlights: {total}")
        for hl_type, count in sorted(type_counts.items()):
            print(f"  {hl_type}: {count}")

        # Multikills
        multi = [h for h in highlights if h.highlight_type not in (
            HighlightType.KILL, HighlightType.CLUTCH_CANDIDATE
        )]
        print(f"Multikill sequences (2K+): {len(multi)}")

        clutches = [h for h in highlights if h.highlight_type == HighlightType.CLUTCH_CANDIDATE]
        print(f"Clutch candidates (heuristic): {len(clutches)}")

        # Sample top highlights
        print("\nSample highlights (first 10):")
        for h in highlights[:10]:
            tags_str = ", ".join(h.tags) if h.tags else "-"
            print(
                f"  R{h.round_num:02d} | {h.highlight_type.value:<20} | "
                f"kills={h.kill_count} | pov={h.pov_name!r} | tags=[{tags_str}] | "
                f"ticks={h.clip_start_tick}–{h.clip_end_tick}"
            )

        # Assert that something was actually found
        assert total > 0
