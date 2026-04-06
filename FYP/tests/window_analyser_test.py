import pytest
from datetime import datetime, timezone, timedelta
from core.window_analyser import WindowAnalyser, CleanStretch, LinkedGroup

# --- Helpers ---

def make_results(flagged_times: list[str]) -> list[dict]:
    return [{"time_utc": t} for t in flagged_times]

def dt(time_str: str) -> datetime:
    return datetime.fromisoformat(f"2026-01-01T{time_str}").replace(tzinfo=timezone.utc)

TIME_BEGIN = "2026-01-01T10:00:00"
TIME_END   = "2026-01-01T10:10:00"


# --- WindowAnalyser init ---

def test_flagged_times_parsed():
    results = make_results(["2026-01-01T10:00:30+00:00", "2026-01-01T10:01:00+00:00"])
    analyser = WindowAnalyser(results, TIME_BEGIN, TIME_END)
    assert len(analyser.flagged) == 2

def test_empty_results():
    analyser = WindowAnalyser([], TIME_BEGIN, TIME_END)
    assert len(analyser.flagged) == 0


# --- clean_stretches ---

def test_all_clean_is_one_stretch():
    analyser = WindowAnalyser([], TIME_BEGIN, TIME_END)
    stretches = analyser.clean_stretches()
    assert len(stretches) == 1
    assert stretches[0].duration_seconds == 600

def test_all_flagged_no_stretches():
    flagged = [f"2026-01-01T10:00:{s:02d}+00:00" for s in range(60)]
    flagged += [f"2026-01-01T10:0{m}:{s:02d}+00:00" for m in range(1, 10) for s in range(60)]
    analyser = WindowAnalyser(make_results(flagged), TIME_BEGIN, TIME_END)
    # not necessarily empty since window extends to end, but duration should be minimal
    stretches = analyser.clean_stretches()
    total_clean = sum(s.duration_seconds for s in stretches)
    assert total_clean < 10

def test_stretch_sorted_by_duration_descending():
    # flag a short block in the middle to create two stretches
    flagged = [f"2026-01-01T10:05:{s:02d}+00:00" for s in range(60)]
    analyser = WindowAnalyser(make_results(flagged), TIME_BEGIN, TIME_END)
    stretches = analyser.clean_stretches()
    durations = [s.duration_seconds for s in stretches]
    assert durations == sorted(durations, reverse=True)

def test_stretch_start_end_consistency():
    analyser = WindowAnalyser([], TIME_BEGIN, TIME_END)
    for s in analyser.clean_stretches():
        assert s.end >= s.start
        assert s.duration_seconds == int((s.end - s.start).total_seconds()) or \
               s.duration_seconds == int((s.end - s.start).total_seconds()) + 1


# --- linked_groups ---

def test_no_results_no_groups():
    # all flagged = no clean stretches = no groups
    flagged = [f"2026-01-01T10:00:{s:02d}+00:00" for s in range(60)]
    analyser = WindowAnalyser(make_results(flagged), "2026-01-01T10:00:00", "2026-01-01T10:00:59")
    groups = analyser.linked_groups()
    assert groups == []

def test_all_clean_is_one_group():
    analyser = WindowAnalyser([], TIME_BEGIN, TIME_END)
    groups = analyser.linked_groups(gap_tolerance_seconds=30)
    assert len(groups) == 1

def test_gap_within_tolerance_merges_groups():
    # flag 10 seconds in the middle, gap of 10s should merge with tolerance=30
    flagged = [f"2026-01-01T10:05:{s:02d}+00:00" for s in range(10)]
    analyser = WindowAnalyser(make_results(flagged), TIME_BEGIN, TIME_END)
    groups = analyser.linked_groups(gap_tolerance_seconds=30)
    assert len(groups) == 1

def test_gap_outside_tolerance_splits_groups():
    # flag 60 seconds in middle, gap > tolerance should split
    flagged = [f"2026-01-01T10:05:{s:02d}+00:00" for s in range(60)]
    analyser = WindowAnalyser(make_results(flagged), TIME_BEGIN, TIME_END)
    groups = analyser.linked_groups(gap_tolerance_seconds=5)
    assert len(groups) == 2

def test_groups_sorted_by_total_clean_descending():
    flagged = [f"2026-01-01T10:05:{s:02d}+00:00" for s in range(60)]
    analyser = WindowAnalyser(make_results(flagged), TIME_BEGIN, TIME_END)
    groups = analyser.linked_groups(gap_tolerance_seconds=5)
    totals = [g.total_clean_seconds for g in groups]
    assert totals == sorted(totals, reverse=True)

def test_group_span_gte_clean():
    analyser = WindowAnalyser([], TIME_BEGIN, TIME_END)
    for g in analyser.linked_groups():
        assert g.total_span_seconds >= g.total_clean_seconds


# --- summary methods --- 
# Not testing string formatting in detail — fragile and low value.
# Just checking they return strings and don't crash.

def test_clean_stretches_summary_returns_string():
    analyser = WindowAnalyser([], TIME_BEGIN, TIME_END)
    result = analyser.clean_stretches_summary()
    assert isinstance(result, str)

def test_linked_groups_summary_returns_string():
    analyser = WindowAnalyser([], TIME_BEGIN, TIME_END)
    result = analyser.linked_groups_summary()
    assert isinstance(result, str)

def test_summaries_no_results_message():
    flagged = [f"2026-01-01T10:00:{s:02d}+00:00" for s in range(60)]
    analyser = WindowAnalyser(make_results(flagged), "2026-01-01T10:00:00", "2026-01-01T10:00:59")
    assert "No clean stretches found" in analyser.clean_stretches_summary()
    assert "No groups found" in analyser.linked_groups_summary()