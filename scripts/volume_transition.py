#!/usr/bin/env python3
"""
卷间过渡 - 自动化状态重置（AI 负责创意部分，本脚本负责机械重置）
用法: python3 scripts/volume_transition.py --dir ~/novels/my-novel --volume 5 --title "根" --first-chapter 71
"""

import sys
import argparse
import yaml
from pathlib import Path


def load_yaml(path):
    if not Path(path).exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_yaml(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def diff_line(label, old, new):
    print(f"  {label}: {old} → {new}")


def print_checklist(volume):
    print(f"\n{'='*60}")
    print("📋 卷间过渡 — AI 手动操作清单")
    print(f"{'='*60}")
    checklist = [
        f"创建卷大纲 (outlines/volume{volume}-outline.md)",
        "全量重写 characters.yaml",
        "全量重写 threads.yaml (封卷旧线索 + 播种新线索)",
        "全量重写 emotional-debts.yaml",
        "一致性确认 (consistency_checker.py check)",
    ]
    for item in checklist:
        print(f"  ☐ {item}")
    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(description="卷间过渡 - 状态重置")
    parser.add_argument("--dir", required=True, help="小说项目目录")
    parser.add_argument("--volume", type=int, required=True, help="新卷号")
    parser.add_argument("--title", default=None, help="卷标题（默认: 第N卷）")
    parser.add_argument("--first-chapter", type=int, default=None, help="新卷首章号（默认: current_chapter+1）")
    parser.add_argument("--dry-run", action="store_true", help="仅显示变更，不写入文件")
    args = parser.parse_args()

    project_dir = Path(args.dir)
    if not project_dir.exists():
        print(f"❌ 目录不存在: {project_dir}")
        sys.exit(1)

    title = args.title or f"第{args.volume}卷"

    # Load files
    project = load_yaml(project_dir / "novel-project.yaml")
    arc_tracker = load_yaml(project_dir / "state" / "arc-tracker.yaml")
    consistency_log = load_yaml(project_dir / "state" / "consistency-log.yaml")

    meta = project.get("meta", {})
    current_chapter = int(meta.get("current_chapter", 0) or 0)
    first_chapter = args.first_chapter if args.first_chapter is not None else current_chapter + 1

    # ──────── arc-tracker.yaml ────────
    old_arc = arc_tracker.get("current_arc", "?")
    old_phase = arc_tracker.get("current_phase", "?")
    old_phase_start = arc_tracker.get("phase_start_chapter", "?")
    old_phase_elapsed = arc_tracker.get("phase_chapters_elapsed", "?")
    old_end_ch = current_chapter

    new_arc = args.volume
    new_phase = "起势"
    new_phase_start = first_chapter
    new_phase_elapsed = 0

    recent_patterns = arc_tracker.get("recent_patterns", [])
    recent_hooks = arc_tracker.get("recent_hooks", [])

    print(f"\n{'='*60}")
    print(f"🔄 卷间过渡: 第{old_arc}卷 → 第{new_arc}卷「{title}」")
    print(f"{'='*60}")

    print(f"\n📄 state/arc-tracker.yaml")
    diff_line("current_arc", old_arc, new_arc)
    diff_line("current_phase", old_phase, new_phase)
    diff_line("phase_start_chapter", old_phase_start, new_phase_start)
    diff_line("phase_chapters_elapsed", old_phase_elapsed, new_phase_elapsed)
    diff_line("last_volume_end_chapter", "(new)", old_end_ch)
    diff_line("recent_patterns", f"[{len(recent_patterns)}项]", f"[{min(2, len(recent_patterns))}项]")
    diff_line("recent_hooks", f"[{len(recent_hooks)}项]", f"[{min(2, len(recent_hooks))}项]")

    # ──────── novel-project.yaml ────────
    old_volume = meta.get("current_volume", "?")
    old_vol_title = meta.get("volume_title", "?")

    print(f"\n📄 novel-project.yaml")
    diff_line("meta.current_volume", old_volume, new_arc)
    diff_line("meta.volume_title", old_vol_title, title)

    # ──────── consistency-log.yaml ────────
    old_last_check = consistency_log.get("last_check_chapter", "?")
    old_last_audit = consistency_log.get("last_audit_chapter", "?")

    print(f"\n📄 state/consistency-log.yaml")
    diff_line("last_check_chapter", old_last_check, 0)
    diff_line("last_audit_chapter", old_last_audit, 0)
    print(f"  + volume_boundary: volume {old_arc}→{new_arc} at chapter {old_end_ch}")

    # ──────── Write changes ────────
    if args.dry_run:
        print(f"\n🔒 DRY RUN — 未写入任何文件")
    else:
        # arc-tracker
        arc_tracker["current_arc"] = new_arc
        arc_tracker["current_phase"] = new_phase
        arc_tracker["phase_start_chapter"] = new_phase_start
        arc_tracker["phase_chapters_elapsed"] = new_phase_elapsed
        arc_tracker["last_volume_end_chapter"] = old_end_ch
        arc_tracker["recent_patterns"] = recent_patterns[-2:] if recent_patterns else []
        arc_tracker["recent_hooks"] = recent_hooks[-2:] if recent_hooks else []
        save_yaml(str(project_dir / "state" / "arc-tracker.yaml"), arc_tracker)

        # novel-project
        project.setdefault("meta", {})["current_volume"] = new_arc
        project["meta"]["volume_title"] = title
        save_yaml(str(project_dir / "novel-project.yaml"), project)

        # consistency-log
        checks = consistency_log.get("checks", [])
        checks.append({"type": "volume_boundary", "from_volume": old_arc, "to_volume": new_arc, "at_chapter": old_end_ch})
        consistency_log["checks"] = checks
        consistency_log["last_check_chapter"] = 0
        consistency_log["last_audit_chapter"] = 0
        save_yaml(str(project_dir / "state" / "consistency-log.yaml"), consistency_log)

        print(f"\n✅ 状态已写入 — 第{new_arc}卷「{title}」准备就绪")

    print_checklist(new_arc)


if __name__ == "__main__":
    main()
