#!/usr/bin/env python3
"""
状态同步检测脚本 - 检测状态文件与正文的同步差距
用法: python3 auto_sync.py --dir <项目目录>
"""
import argparse, os, sys
from pathlib import Path
import yaml

def load_yaml(path):
    if not os.path.exists(path): return {}
    with open(path, "r", encoding="utf-8") as f: return yaml.safe_load(f) or {}

def check_sync(project_dir):
    pdir = Path(project_dir)
    proj = load_yaml(str(pdir / "novel-project.yaml"))
    current_ch = proj.get("meta", {}).get("current_chapter", 0)
    issues = []

    # 1. characters.yaml — last_appeared 落后
    chars = load_yaml(str(pdir / "state" / "characters.yaml"))
    chars_data = chars.get("characters", {})
    if isinstance(chars_data, dict): chars_list = list(chars_data.values())
    elif isinstance(chars_data, list): chars_list = chars_data
    else: chars_list = []
    stale_chars = []
    for c in chars_list:
        if not isinstance(c, dict): continue
        la = c.get("last_appeared", 0)
        if la == 0 or (current_ch - la > 5):
            stale_chars.append(f"{c.get('name', c.get('id', '?'))}(ch{la})")
    if stale_chars:
        issues.append(f"📋 characters.yaml: {len(stale_chars)}角色落后>5章或未更新: {', '.join(stale_chars[:5])}{'...' if len(stale_chars)>5 else ''}")

    # 2. threads.yaml — developments 最近条目落后
    thr = load_yaml(str(pdir / "state" / "threads.yaml"))
    threads = thr.get("threads", [])
    if isinstance(threads, dict): threads = list(threads.values())
    stale_threads = []
    for t in threads:
        if not isinstance(t, dict): continue
        devs = t.get("developments", [])
        last_dev_ch = 0
        if isinstance(devs, list) and devs:
            last_dev_ch = max((d.get("chapter", 0) if isinstance(d, dict) else 0) for d in devs)
        if last_dev_ch < current_ch - 5:
            stale_threads.append(f"{t.get('id', '?')}(最后ch{last_dev_ch})")
    if stale_threads:
        issues.append(f"🧵 threads.yaml: {len(stale_threads)}线索落后>5章: {', '.join(stale_threads[:5])}{'...' if len(stale_threads)>5 else ''}")

    # 3. arc-tracker.yaml — recent_patterns 最新条目落后
    arc = load_yaml(str(pdir / "state" / "arc-tracker.yaml"))
    rp = arc.get("recent_patterns", [])
    last_rp_ch = 0
    if rp:
        last_rp_ch = max((r.get("chapter", 0) if isinstance(r, dict) else 0) for r in rp)
    if last_rp_ch < current_ch - 2:
        issues.append(f"📈 arc-tracker.yaml: recent_patterns落后{current_ch - last_rp_ch}章(最后ch{last_rp_ch} / 当前ch{current_ch})")

    # 4. emotional-debts.yaml — 只有初始条目
    ed = load_yaml(str(pdir / "state" / "emotional-debts.yaml"))
    debts = ed.get("emotional_debts", ed.get("emotional-debts", []))
    if isinstance(debts, dict): debts = list(debts.values())
    if len(debts) <= 2:
        issues.append(f"💚 emotional-debts.yaml: 仅{len(debts)}条(可能缺少新情感债)")

    # 5. timeline.yaml — 最后记录章节落后
    tl = load_yaml(str(pdir / "state" / "timeline.yaml"))
    chapters = tl.get("chapters", [])
    last_tl_ch = 0
    if isinstance(chapters, list) and chapters:
        last_tl_ch = max((c.get("chapter", 0) if isinstance(c, dict) else 0) for c in chapters)
    if last_tl_ch < current_ch - 3:
        issues.append(f"⏱️ timeline.yaml: 落后{current_ch - last_tl_ch}章(最后ch{last_tl_ch} / 当前ch{current_ch})")

    # 6. Check actual chapter files vs current_ch
    chdir = pdir / "chapters"
    if chdir.exists():
        actual = len([f for f in os.listdir(chdir) if f.startswith("ch") and f.endswith(".md")])
        if actual < current_ch:
            issues.append(f"📁 chapters/: 实际{actual}章 vs novel-project记录{current_ch}章(差{current_ch - actual}章)")
        elif actual > current_ch:
            issues.append(f"📁 chapters/: 实际{actual}章 vs novel-project记录{current_ch}章(多了{actual - current_ch}章未提交)")

    return current_ch, issues

def main():
    parser = argparse.ArgumentParser(description="检测状态文件同步差距")
    parser.add_argument("--dir", required=True, help="项目目录")
    args = parser.parse_args()
    if not os.path.isdir(args.dir):
        print(f"❌ 目录不存在: {args.dir}"); sys.exit(1)
    current_ch, issues = check_sync(args.dir)
    print("=" * 50)
    print(f"📊 当前章节: {current_ch}")
    print("=" * 50)
    if issues:
        print(f"\n⚠️  发现 {len(issues)} 个同步问题:\n")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        print(f"\n💡 建议: 通读落后章节 → 批量更新状态文件 → consistency_checker 验证")
    else:
        print("\n✅ 所有状态文件已同步!")
    print()

if __name__ == "__main__":
    main()
