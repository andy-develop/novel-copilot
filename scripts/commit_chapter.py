#!/usr/bin/env python3
"""
章节提交脚本 - 一键更新所有章节后状态文件
替代每次写完章节后的 4-6 次手动 patch 操作
"""

import argparse
import os
import re
import sys
from pathlib import Path

import yaml


def load_yaml(path):
    """Load YAML file, return empty dict if missing."""
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_yaml(path, data):
    """Save data to YAML file with proper Unicode handling."""
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def count_chinese_chars(filepath):
    """Count actual Chinese characters + CJK punctuation in a file."""
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
    return len(re.findall(
        r'[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff\u3000-\u303f\uff00-\uffef]', text
    ))


def parse_thread_advance(spec):
    """Parse --thread-advance value like 'T015:developed,T018:resolved:42'."""
    advances = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        tokens = part.split(":")
        tid = tokens[0]
        action = tokens[1] if len(tokens) > 1 else "developed"
        extra = tokens[2] if len(tokens) > 2 else None
        advances.append({"id": tid, "action": action, "extra": extra})
    return advances


def commit_chapter(args):
    project_dir = Path(args.dir)
    chapter = args.chapter
    words = args.words or 0
    pattern = args.pattern
    hook = args.hook
    tension = args.tension

    # Auto-discover chapter file when --count-words not provided
    if not args.count_words:
        auto_path = project_dir / "chapters" / f"ch{chapter:03d}.md"
        if auto_path.exists():
            args.count_words = str(auto_path)
            print(f"📖 自动发现章节文件: {auto_path}")

    # --count-words overrides --words
    if args.count_words:
        filepath = args.count_words
        if not os.path.isabs(filepath):
            filepath = str(project_dir / filepath)
        if os.path.exists(filepath):
            words = count_chinese_chars(filepath)
        else:
            print(f"⚠️  字数文件不存在: {filepath}，使用 --words 值 {words}")

    dry = args.dry_run
    changes = []

    # ── 1. novel-project.yaml ──
    proj_path = str(project_dir / "novel-project.yaml")
    proj = load_yaml(proj_path)
    if proj:
        meta = proj.setdefault("meta", {})
        old_ch = meta.get("current_chapter", 0)
        old_words = meta.get("current_words", 0)
        meta["current_chapter"] = chapter
        meta["current_words"] = (int(old_words) if old_words else 0) + words
        changes.append(f"novel-project.yaml: current_chapter {old_ch} → {chapter}")
        changes.append(f"novel-project.yaml: current_words {old_words} → {meta['current_words']} (+{words})")
        if not dry:
            save_yaml(proj_path, proj)
    else:
        print(f"⚠️  跳过 novel-project.yaml（未找到）")

    # ── 2. arc-tracker.yaml ──
    arc_path = str(project_dir / "state" / "arc-tracker.yaml")
    arc = load_yaml(arc_path)
    if arc:
        old_elapsed = arc.get("phase_chapters_elapsed", 0)
        arc["phase_chapters_elapsed"] = int(old_elapsed) + 1
        changes.append(f"arc-tracker.yaml: phase_chapters_elapsed {old_elapsed} → {arc['phase_chapters_elapsed']}")

        rp = arc.setdefault("recent_patterns", [])
        rp.append({"chapter": chapter, "method": pattern, "tension": tension})
        arc["recent_patterns"] = rp[-5:]
        changes.append(f"arc-tracker.yaml: recent_patterns += ch{chapter} {pattern} T{tension}")

        rh = arc.setdefault("recent_hooks", [])
        rh.append({"chapter": chapter, "type": hook})
        arc["recent_hooks"] = rh[-5:]
        changes.append(f"arc-tracker.yaml: recent_hooks += ch{chapter} {hook}")

        if not dry:
            save_yaml(arc_path, arc)
    else:
        print(f"⚠️  跳过 arc-tracker.yaml（未找到）")

    # ── 3. threads.yaml (optional) ──
    if args.thread_advance:
        thr_path = str(project_dir / "state" / "threads.yaml")
        thr = load_yaml(thr_path)
        if thr and "threads" in thr:
            advances = parse_thread_advance(args.thread_advance)
            for adv in advances:
                tid = adv["id"]
                thread = next((t for t in thr["threads"] if t.get("id") == tid), None)
                if not thread:
                    print(f"⚠️  线索 {tid} 未找到，跳过")
                    continue
                if adv["action"] == "developed":
                    devs = thread.setdefault("developments", [])
                    devs.append({"chapter": chapter, "event": "advanced"})
                    thread["developments"] = devs
                    changes.append(f"threads.yaml: {tid} developed at ch{chapter}")
                elif adv["action"] == "resolved":
                    ch_resolved = int(adv["extra"]) if adv["extra"] else chapter
                    thread["resolved_chapter"] = ch_resolved
                    thread["resolved_how"] = f"resolved in ch{ch_resolved}"
                    changes.append(f"threads.yaml: {tid} resolved at ch{ch_resolved}")
            if not dry:
                save_yaml(thr_path, thr)
        else:
            print(f"⚠️  跳过 threads.yaml（未找到或无 threads 列表）")

    # ── 4. consistency-log.yaml ──
    con_path = str(project_dir / "state" / "consistency-log.yaml")
    con = load_yaml(con_path)
    if con:
        # Get light_check_interval from automation-config
        auto_path = str(project_dir / "automation-config.yaml")
        auto_cfg = load_yaml(auto_path)
        interval = int(auto_cfg.get("consistency", {}).get("light_check_interval", 3)) if auto_cfg else 3

        old_last = con.get("last_check_chapter", 0)
        if chapter % interval == 0:
            con["last_check_chapter"] = chapter
            changes.append(f"consistency-log.yaml: last_check_chapter {old_last} → {chapter} (轻检到期)")
        else:
            changes.append(f"consistency-log.yaml: 轻检未到期 (ch{chapter} 非间隔{interval}的倍数)")

        if not dry:
            save_yaml(con_path, con)
    else:
        print(f"⚠️  跳过 consistency-log.yaml（未找到）")

    # ── Summary ──
    mode = "🔍 DRY RUN" if dry else "✅ COMMITTED"
    print(f"\n{'='*50}")
    print(f"{mode} — 第{chapter}章提交")
    print(f"{'='*50}")
    for c in changes:
        print(f"  {c}")
    print(f"{'='*50}\n")


def main():
    parser = argparse.ArgumentParser(
        description="章节提交：一键更新所有章节后状态文件"
    )
    parser.add_argument("--dir", required=True, help="小说项目目录")
    parser.add_argument("--chapter", type=int, required=True, help="章节号（设置为该值）")
    parser.add_argument("--title", default="", help="章节标题（仅用于记录）")
    parser.add_argument("--words", type=int, default=0, help="本章字数")
    parser.add_argument("--count-words", metavar="FILE",
                        help="从章节文件自动统计中文字数（覆盖 --words）")
    parser.add_argument("--pattern", default="", help="发散模式，如 D5+D9")
    parser.add_argument("--hook", default="", help="钩子类型，如 焦虑型")
    parser.add_argument("--tension", type=int, default=5, help="张力值 1-10")
    parser.add_argument("--thread-advance", default="",
                        help="线索推进，格式: T015:developed,T018:resolved:42")
    parser.add_argument("--dry-run", action="store_true", help="仅显示变更，不写入")
    args = parser.parse_args()

    # Validate: need either --words or --count-words
    if not args.words and not args.count_words:
        print("⚠️  请提供 --words 或 --count-words")

    commit_chapter(args)


if __name__ == "__main__":
    main()
