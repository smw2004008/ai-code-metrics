#!/usr/bin/env python3
"""Explainable Git-based estimate of AI-assisted code changes."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


TRAILER = "ai-assisted"
NOTES_REF = "refs/notes/ai-assisted"


@dataclass
class CommitStats:
    commit: str
    subject: str
    ai_assisted: bool
    additions: int
    deletions: int


def git(repo: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout


def marked_by_trailer(message: str) -> bool:
    for line in message.splitlines():
        key, sep, value = line.partition(":")
        if sep and key.strip().lower() == TRAILER and value.strip().lower() in {
            "yes", "true", "1", "ai", "assisted"
        }:
            return True
    return False


def marked_by_note(repo: Path, commit: str) -> bool:
    note = git(repo, "notes", f"--ref={NOTES_REF}", "show", commit, check=False)
    return marked_by_trailer(note)


def parse_numstat(raw: str) -> tuple[int, int]:
    additions = deletions = 0
    for line in raw.splitlines():
        fields = line.split("\t", 2)
        if len(fields) < 3:
            continue
        # Binary entries use '-' instead of a line count.
        if fields[0].isdigit():
            additions += int(fields[0])
        if fields[1].isdigit():
            deletions += int(fields[1])
    return additions, deletions


def collect(repo: Path, since: str | None, until: str | None) -> list[CommitStats]:
    args = ["log", "--no-merges", "--format=%H%x1f%s%x1f%B%x1e"]
    if since:
        args.append(f"--since={since}")
    if until:
        args.append(f"--until={until}")
    records = git(repo, *args).split("\x1e")
    output: list[CommitStats] = []
    for record in records:
        record = record.strip("\r\n")
        if not record:
            continue
        parts = record.split("\x1f", 2)
        if len(parts) != 3:
            continue
        commit, subject, body = parts
        additions, deletions = parse_numstat(
            git(repo, "show", "--format=", "--numstat", "--no-renames", commit)
        )
        output.append(
            CommitStats(
                commit=commit,
                subject=subject,
                ai_assisted=marked_by_trailer(body) or marked_by_note(repo, commit),
                additions=additions,
                deletions=deletions,
            )
        )
    return output


def summarize(repo: Path, commits: list[CommitStats], since: str | None, until: str | None) -> dict:
    total_add = sum(item.additions for item in commits)
    total_del = sum(item.deletions for item in commits)
    ai_commits = [item for item in commits if item.ai_assisted]
    ai_add = sum(item.additions for item in ai_commits)
    ai_del = sum(item.deletions for item in ai_commits)
    return {
        "repository": str(repo.resolve()),
        "since": since,
        "until": until,
        "commit_count": len(commits),
        "total_additions": total_add,
        "total_deletions": total_del,
        "ai_assisted_commit_count": len(ai_commits),
        "ai_assisted_additions": ai_add,
        "ai_assisted_deletions": ai_del,
        "ai_assisted_addition_ratio": round(ai_add / total_add, 4) if total_add else 0.0,
        "methodology": (
            "AI-assisted commits are identified by the AI-Assisted: yes trailer or "
            "refs/notes/ai-assisted. All additions in a marked commit are counted; "
            "this estimates assisted changes and does not identify AI-written lines."
        ),
        "commits": [asdict(item) for item in commits],
    }


def render_text(report: dict) -> str:
    ratio = report["ai_assisted_addition_ratio"] * 100
    return "\n".join(
        [
            f"仓库：{report['repository']}",
            f"时间范围：{report['since'] or '全部'} 至 {report['until'] or '现在'}",
            f"提交数：{report['commit_count']}",
            f"总新增/删除行：{report['total_additions']} / {report['total_deletions']}",
            f"AI 辅助提交数：{report['ai_assisted_commit_count']}",
            f"AI 辅助新增/删除行：{report['ai_assisted_additions']} / {report['ai_assisted_deletions']}",
            f"AI 辅助新增行占比：{ratio:.2f}%",
            f"口径：{report['methodology']}",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Git 仓库路径，默认当前目录")
    parser.add_argument("--since", help='起始时间，例如 "30 days ago" 或 2026-01-01')
    parser.add_argument("--until", help='结束时间，例如 "yesterday" 或 2026-02-01')
    parser.add_argument("--format", choices=("text", "json"), default="text")
    options = parser.parse_args()
    repo = Path(options.repo).expanduser()
    try:
        git(repo, "rev-parse", "--show-toplevel")
        report = summarize(repo, collect(repo, options.since, options.until), options.since, options.until)
    except (RuntimeError, OSError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    if options.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
