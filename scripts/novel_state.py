#!/usr/bin/env python3
"""
小说状态引擎 - 初始化/查询/更新小说项目状态
"""

import sys
import os
import yaml
import shutil
from pathlib import Path
from datetime import datetime

SKILL_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = SKILL_DIR / "templates"


def load_yaml(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_yaml(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def cmd_init(args):
    """初始化小说项目"""
    name = args.get("name", "我的小说")
    base_dir = args.get("dir", os.path.join(os.getcwd(), name))
    project_dir = Path(base_dir)
    
    if project_dir.exists() and any(project_dir.iterdir()):
        print(f"错误: 目录已存在且不为空: {project_dir}")
        sys.exit(1)
    
    # 创建目录结构
    (project_dir / "state").mkdir(parents=True)
    (project_dir / "chapters").mkdir(parents=True)
    (project_dir / "outlines").mkdir(parents=True)
    
    # 复制模板
    templates = {
        "novel-project.yaml": project_dir / "novel-project.yaml",
        "characters.yaml": project_dir / "state" / "characters.yaml",
        "world.yaml": project_dir / "state" / "world.yaml",
        "threads.yaml": project_dir / "state" / "threads.yaml",
        "timeline.yaml": project_dir / "state" / "timeline.yaml",
    }
    
    for tmpl_name, dest in templates.items():
        src = TEMPLATES_DIR / tmpl_name
        if src.exists():
            shutil.copy2(src, dest)
        else:
            # 生成空模板
            save_yaml(str(dest), {})
    
    # 填入项目名
    project_data = load_yaml(str(project_dir / "novel-project.yaml"))
    project_data.setdefault("meta", {})["title"] = name
    project_data["meta"]["created_at"] = datetime.now().strftime("%Y-%m-%d")
    save_yaml(str(project_dir / "novel-project.yaml"), project_data)
    
    print(f"✅ 小说项目 '{name}' 初始化完成！")
    print(f"   目录: {project_dir}")
    print(f"\n下一步:")
    print(f"  1. 编辑 state/characters.yaml 添加角色")
    print(f"  2. 编辑 state/world.yaml 设置世界观")
    print(f"  3. 编辑 state/threads.yaml 添加初始线索")
    print(f"  4. 开始写作！")


def cmd_list(args):
    """列出项目状态概览"""
    project_dir = Path(args.get("dir", "."))
    project = load_yaml(project_dir / "novel-project.yaml")
    characters = load_yaml(project_dir / "state" / "characters.yaml").get("characters", [])
    threads = load_yaml(project_dir / "state" / "threads.yaml").get("threads", [])
    
    meta = project.get("meta", {})
    print(f"\n📖 《{meta.get('title', '未命名')}》")
    print(f"   进度: 第{meta.get('current_chapter', 0)}章 / {meta.get('current_words', 0)}字")
    print(f"   目标: {meta.get('target_words', '?')}字")
    
    # 角色状态
    alive = sum(1 for c in characters if c.get("status") == "alive")
    dead = sum(1 for c in characters if c.get("status") == "dead")
    missing = sum(1 for c in characters if c.get("status") == "missing")
    print(f"\n👤 角色: {len(characters)}人 (存活{alive} | 死亡{dead} | 失踪{missing})")
    
    if dead:
        print("   💀 已故:", ", ".join(c["name"] for c in characters if c.get("status") == "dead"))
    if missing:
        print("   ❓ 失踪:", ", ".join(c["name"] for c in characters if c.get("status") == "missing"))
    
    # 线索
    planted = sum(1 for t in threads if t.get("resolved_chapter") is None)
    resolved = sum(1 for t in threads if t.get("resolved_chapter") is not None)
    major_open = sum(1 for t in threads if t.get("importance") == "major" and t.get("resolved_chapter") is None)
    print(f"\n🧵 线索: {len(threads)}条 (未收束{planted} | 已收束{resolved})")
    if major_open:
        print(f"   ⚠️ 重要未收束: {major_open}条")
    
    # 长期未推进线索
    current_ch = int(meta.get("current_chapter", 0) or 0)
    stale = [t for t in threads if t.get("resolved_chapter") is None 
             and current_ch - int(t.get("planted_chapter", 0) or 0) > 20
             and t.get("importance") == "major"]
    if stale:
        print("   🕰️ 长期未推进:")
        for t in stale:
            print(f"      - {t.get('description', '?')[:40]}... (种下于第{t.get('planted_chapter', '?')}章)")


def cmd_character(args):
    """角色相关操作"""
    project_dir = Path(args.get("dir", "."))
    state_file = project_dir / "state" / "characters.yaml"
    data = load_yaml(str(state_file))
    characters = data.get("characters", [])
    
    action = args.get("action", "list")
    
    if action == "list":
        if not characters:
            print("角色库为空")
            return
        print(f"\n👤 角色列表 ({len(characters)}人)")
        print("-" * 50)
        for c in characters:
            status_icon = {"alive": "🟢", "dead": "💀", "missing": "❓", "sealed": "🔒"}.get(c.get("status", ""), "❔")
            print(f"  {status_icon} {c.get('name', '?')} [{c.get('id', '?')}]")
            print(f"     状态: {c.get('status', '?')} | 位置: {c.get('location', '未知')} | 最后出场: 第{c.get('last_appeared', '?')}章")
            if c.get("key_traits"):
                print(f"     性格: {', '.join(c['key_traits'][:3])}")
    
    elif action == "add":
        new_char = {
            "id": args.get("id", ""),
            "name": args.get("name", ""),
            "aliases": args.get("aliases", []),
            "status": "alive",
            "death_chapter": None,
            "death_cause": None,
            "death_witnesses": [],
            "is_truly_dead": True,
            "location": args.get("location", ""),
            "condition": "normal",
            "condition_note": "",
            "abilities": args.get("abilities", []),
            "power_level": args.get("power_level", ""),
            "power_changes": [],
            "relationships": [],
            "inventory": [],
            "inventory_history": [],
            "key_traits": args.get("key_traits", []),
            "speech_pattern": args.get("speech_pattern", ""),
            "secrets": [],
            "first_appeared": args.get("chapter", 0),
            "last_appeared": args.get("chapter", 0),
            "total_appearances": 1,
            "notes": "",
        }
        characters.append(new_char)
        data["characters"] = characters
        save_yaml(str(state_file), data)
        print(f"✅ 角色 '{new_char['name']}' 已添加")
    
    elif action == "kill":
        char_id = args.get("id", "")
        chapter = args.get("chapter", 0)
        cause = args.get("cause", "")
        for c in characters:
            if c["id"] == char_id:
                c["status"] = "dead"
                c["death_chapter"] = chapter
                c["death_cause"] = cause
                c["is_truly_dead"] = True
                data["characters"] = characters
                save_yaml(str(state_file), data)
                print(f"💀 角色 '{c['name']}' 在第{chapter}章死亡 ({cause})")
                return
        print(f"错误: 找不到角色 '{char_id}'")


def cmd_threads(args):
    """线索相关操作"""
    project_dir = Path(args.get("dir", "."))
    state_file = project_dir / "state" / "threads.yaml"
    data = load_yaml(str(state_file))
    threads = data.get("threads", [])
    
    action = args.get("action", "list")
    
    if action == "list":
        if not threads:
            print("线索库为空")
            return
        print(f"\n🧵 线索列表 ({len(threads)}条)")
        print("-" * 50)
        for t in threads:
            resolved = "✅" if t.get("resolved_chapter") else "⏳"
            importance = {"major": "🔴", "minor": "🟡", "easter_egg": "🟣"}.get(t.get("importance", ""), "⚪")
            print(f"  {resolved} {importance} {t.get('description', '?')[:40]}...")
            print(f"     种下: 第{t.get('planted_chapter', '?')}章" + 
                  (f" | 收束: 第{t['resolved_chapter']}章" if t.get("resolved_chapter") else ""))
    
    elif action == "add":
        new_thread = {
            "id": args.get("id", ""),
            "description": args.get("description", ""),
            "category": args.get("category", ""),
            "planted_chapter": args.get("chapter", 0),
            "planted_context": args.get("context", ""),
            "planted_by": args.get("characters", []),
            "developments": [],
            "resolved_chapter": None,
            "resolved_how": "",
            "importance": args.get("importance", "minor"),
            "urgency": args.get("urgency", "normal"),
            "expected_resolve_by": args.get("expected_resolve_by", None),
            "related_threads": [],
            "related_characters": args.get("characters", []),
            "notes": "",
        }
        threads.append(new_thread)
        data["threads"] = threads
        save_yaml(str(state_file), data)
        print(f"✅ 线索已种下: {new_thread['description'][:30]}...")
    
    elif action == "resolve":
        thread_id = args.get("id", "")
        chapter = args.get("chapter", 0)
        how = args.get("how", "")
        for t in threads:
            if t["id"] == thread_id:
                t["resolved_chapter"] = chapter
                t["resolved_how"] = how
                data["threads"] = threads
                save_yaml(str(state_file), data)
                print(f"✅ 线索 '{t['description'][:30]}...' 在第{chapter}章收束")
                return
        print(f"错误: 找不到线索 '{thread_id}'")


def main():
    if len(sys.argv) < 2:
        print("小说状态引擎 - 用法:")
        print("  init   --name 名字 --dir 目录    初始化小说项目")
        print("  list   --dir 目录                查看项目概览")
        print("  char   --dir 目录 --action list  角色操作")
        print("  thread --dir 目录 --action list  线索操作")
        sys.exit(0)
    
    command = sys.argv[1]
    
    # 解析参数
    args = {}
    i = 2
    while i < len(sys.argv):
        if sys.argv[i].startswith("--"):
            key = sys.argv[i][2:]
            if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith("--"):
                args[key] = sys.argv[i + 1]
                i += 2
            else:
                args[key] = True
                i += 1
        else:
            i += 1
    
    if command == "init":
        cmd_init(args)
    elif command == "list":
        cmd_list(args)
    elif command in ("char", "character"):
        cmd_character(args)
    elif command == "thread":
        cmd_threads(args)
    else:
        print(f"未知命令: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
