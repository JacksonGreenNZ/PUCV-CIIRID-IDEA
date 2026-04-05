# core/window_analyser.py

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone


@dataclass
class CleanStretch:
    start: datetime
    end: datetime
    duration_seconds: int


@dataclass
class LinkedGroup:
    stretches: list[CleanStretch] = field(default_factory=list)
    gaps_seconds: list[int] = field(default_factory=list)

    @property
    def start(self) -> datetime:
        return self.stretches[0].start

    @property
    def end(self) -> datetime:
        return self.stretches[-1].end

    @property
    def total_clean_seconds(self) -> int:
        return sum(s.duration_seconds for s in self.stretches)

    @property
    def total_span_seconds(self) -> int:
        return int((self.end - self.start).total_seconds())

    @property
    def max_gap_seconds(self) -> int:
        return max(self.gaps_seconds) if self.gaps_seconds else 0


class WindowAnalyser:
    def __init__(self, results, time_begin: str, time_end: str):
        self.flagged = {
            datetime.fromisoformat(r['time_utc']).replace(tzinfo=timezone.utc)
            for r in results
        }
        self.time_begin = datetime.fromisoformat(time_begin).replace(tzinfo=timezone.utc)
        self.time_end = datetime.fromisoformat(time_end).replace(tzinfo=timezone.utc)

    def clean_stretches(self) -> list[CleanStretch]:
        stretches = []
        current_start = None
        t = self.time_begin

        while t <= self.time_end:
            if t not in self.flagged:
                if current_start is None:
                    current_start = t
            else:
                if current_start is not None:
                    stretches.append(CleanStretch(
                        start=current_start,
                        end=t - timedelta(seconds=1),
                        duration_seconds=int((t - current_start).total_seconds())
                    ))
                    current_start = None
            t += timedelta(seconds=1)

        if current_start is not None:
            stretches.append(CleanStretch(
                start=current_start,
                end=self.time_end,
                duration_seconds=int((self.time_end - current_start).total_seconds())
            ))

        return sorted(stretches, key=lambda s: s.duration_seconds, reverse=True)

    def linked_groups(self, gap_tolerance_seconds: int = 30) -> list[LinkedGroup]:
        stretches = sorted(self.clean_stretches(), key=lambda s: s.start)
        if not stretches:
            return []

        groups = []
        current_group = LinkedGroup(stretches=[stretches[0]])

        for i in range(1, len(stretches)):
            prev = current_group.stretches[-1]
            curr = stretches[i]
            gap = int((curr.start - prev.end).total_seconds())

            if gap <= gap_tolerance_seconds:
                current_group.stretches.append(curr)
                current_group.gaps_seconds.append(gap)
            else:
                groups.append(current_group)
                current_group = LinkedGroup(stretches=[curr])

        groups.append(current_group)
        return sorted(groups, key=lambda g: g.total_clean_seconds, reverse=True)

    def clean_stretches_summary(self, gap_tolerance_seconds: int = 30) -> str:
        stretches = self.clean_stretches()
        lines = ["=== Clean Stretches ==="]
        if not stretches:
            lines.append("  No clean stretches found.")
        else:
            for i, s in enumerate(stretches, 1):
                lines.append(f"  {i}. {s.start.strftime('%H:%M:%S')} - "
                            f"{s.end.strftime('%H:%M:%S')}  "
                            f"({s.duration_seconds}s)")
        return "\n".join(lines)

    def linked_groups_summary(self, gap_tolerance_seconds: int = 30) -> str:
        groups = self.linked_groups(gap_tolerance_seconds)
        lines = [f"=== Linked Groups (gap tolerance: {gap_tolerance_seconds}s) ==="]
        if not groups:
            lines.append("  No groups found.")
        else:
            for i, g in enumerate(groups, 1):
                gap_str = f", gaps: {g.gaps_seconds}" if g.gaps_seconds else ""
                lines.append(f"  Group {i}: {g.start.strftime('%H:%M:%S')} - "
                            f"{g.end.strftime('%H:%M:%S')}  "
                            f"(clean: {g.total_clean_seconds}s, "
                            f"span: {g.total_span_seconds}s{gap_str})")
        return "\n".join(lines)