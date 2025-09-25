import argparse
from dataclasses import dataclass
from datetime import date, timedelta

TITLE = "# Fluent Python (2e) Pair Read Checklist"
DEFAULT_NAMES = ("Bob", "Carlos")
DEFAULT_OUT_FILE = "fluency.md"


@dataclass
class Config:
    start_date: date
    total_chapters: int = 21
    chapters_per_week: int = 2
    participants: tuple[str, ...] = DEFAULT_NAMES
    outfile: str | None = None


def week_span(d: date) -> str:
    end = d + timedelta(days=6)
    return f"{d.strftime('%b %d')}–{end.strftime('%b %d, %Y')}"


def generate_md(cfg: Config) -> str:
    weeks = []
    week = 1
    current = cfg.start_date

    for ch in range(1, cfg.total_chapters + 1, cfg.chapters_per_week):
        end_ch = min(ch + cfg.chapters_per_week - 1, cfg.total_chapters)
        weeks.append((week, current, ch, end_ch))
        week += 1
        current += timedelta(weeks=1)

    lines = []
    lines.append(TITLE)
    lines.append(
        f"_Start: {cfg.start_date.isoformat()} · Chapters: {cfg.total_chapters} · Pace: {cfg.chapters_per_week}/week_"
    )
    lines.append("")

    for wk, start, ch_from, ch_to in weeks:
        span = week_span(start)
        chapter_label = (
            f"Chapter {ch_from}" if ch_from == ch_to else f"Chapters {ch_from}–{ch_to}"
        )
        lines.extend(
            [
                f"## Week {wk} · {span}",
                "",
                f"- [ ] Read **{chapter_label}**",
            ]
        )

        per_person_checks = [
            "Shared ≥1 tip/notes here",
            "Posted ≥1 related update on social media (e.g. LinkedIn)",
            "Opened/updated GitHub issue with weekly takeaways",
        ]

        for who in cfg.participants:
            lines.extend([f"- [ ] {item} — **{who}**" for item in per_person_checks])

        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def next_monday(today: date | None = None) -> date:
    if today is None:
        today = date.today()
    days_until_mon = (0 - today.weekday() + 7) % 7 or 7
    return today + timedelta(days=days_until_mon)


def parse_date(s: str) -> date:
    return date.fromisoformat(s)


def main():
    default_start = next_monday()
    p = argparse.ArgumentParser(
        description="Generate a Markdown checklist for a pair read of Fluent Python (2e)."
    )
    p.add_argument(
        "--start",
        type=parse_date,
        default=next_monday().isoformat(),
        help=f"Start date (YYYY-MM-DD). Default: next Monday ({default_start.isoformat()})",
    )
    p.add_argument(
        "--chapters", type=int, default=21, help="Total chapters. Default: 21"
    )
    p.add_argument(
        "--per-week", type=int, default=2, help="Chapters per week. Default: 2"
    )
    p.add_argument(
        "--participants",
        nargs="+",
        default=list(DEFAULT_NAMES),
        help=f"Participant names. Default: {' '.join(DEFAULT_NAMES)}",
    )
    p.add_argument(
        "-o",
        "--outfile",
        default=DEFAULT_OUT_FILE,
        help="Write to file instead of stdout.",
    )
    args = p.parse_args()

    cfg = Config(
        start_date=args.start,
        total_chapters=args.chapters,
        chapters_per_week=args.per_week,
        participants=tuple(args.participants),
        outfile=args.outfile,
    )
    md = generate_md(cfg)
    with open(cfg.outfile, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"Wrote {cfg.outfile} 🎉")


if __name__ == "__main__":
    main()
