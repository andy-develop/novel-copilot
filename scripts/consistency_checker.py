#!/usr/bin/env python3
"""长篇小说逻辑一致性校验器 - 含重复建议抑制"""

import argparse, os, sys
import yaml
from pathlib import Path

def load_yaml(path):
    if not os.path.exists(path): return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def save_yaml(path, data):
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

class ConsistencyChecker:
    def __init__(self, project_dir):
        self.project_dir = Path(project_dir)
        self.state_dir = self.project_dir / "state"
        self.characters = load_yaml(self.state_dir / "characters.yaml").get("characters", [])
        self.world = load_yaml(self.state_dir / "world.yaml")
        self.threads = load_yaml(self.state_dir / "threads.yaml").get("threads", [])
        self.timeline = load_yaml(self.state_dir / "timeline.yaml")
        self.project = load_yaml(self.project_dir / "novel-project.yaml")
        self.errors, self.warnings, self.suggestions = [], [], []
        self.log_path = self.project_dir / "consistency-log.yaml"
        self.current_chapter = int(self.project.get("meta", {}).get("current_chapter", 0) or 0)

    def check_all(self):
        self.check_dead_character_actions()
        self.check_world_rule_violations()
        self.check_item_duplication()
        self.check_location_consistency()
        self.check_forgotten_threads()
        self.check_absent_characters()
        self.check_power_progression()
        self.check_character_traits()
        return {"errors": self.errors, "warnings": self.warnings, "suggestions": self.suggestions}

    def check_dead_character_actions(self):
        for c in self.characters:
            if c.get("status") == "dead" and c.get("is_truly_dead", True):
                la, dc = c.get("last_appeared"), c.get("death_chapter")
                if la and dc and int(la or 0) > int(dc or 0):
                    self.errors.append({"rule": "R1_死者行动",
                        "message": f"🔴 '{c['name']}' 第{dc}章死亡，第{la}章仍有活动", "severity": "hard"})

    def check_world_rule_violations(self):
        for rule in self.world.get("rules", []):
            if rule.get("severity") != "hard": continue
            desc, rid = rule.get("description", ""), rule.get("id", "")
            if "复活" in desc or "resurrection" in rid:
                for c in self.characters:
                    if c.get("status") == "dead" and not c.get("is_truly_dead", True):
                        ok = any(s.get("planted_chapter", 0) < c.get("death_chapter", 999)
                                 for s in c.get("secrets", []))
                        if not ok:
                            self.errors.append({"rule": "R2_世界规则",
                                "message": f"🔴 '{c['name']}' 死后未死但缺少伏笔", "severity": "hard"})
            if "速度" in desc or "突破" in desc or "修为" in desc:
                for c in self.characters:
                    for _ in c.get("power_changes", []):
                        if "至少" in desc:
                            self.warnings.append({"rule": "W3_修为暴涨",
                                "message": f"🟡 '{c['name']}' 修为变化需确认：{desc}", "severity": "soft"})

    def check_item_duplication(self):
        owned = {}
        for item in self.world.get("items", []):
            owner = item.get("current_owner", "")
            if owner:
                n = item["name"]
                if n in owned and owned[n] != owner:
                    self.errors.append({"rule": "R3_物品双重持有",
                        "message": f"🔴 物品 '{n}' 同时被 '{owned[n]}' 和 '{owner}' 持有", "severity": "hard"})
                owned[n] = owner
        ci = {}
        for c in self.characters:
            for n in c.get("inventory", []):
                if n in ci and ci[n] != c["name"]:
                    self.errors.append({"rule": "R3_物品双重持有",
                        "message": f"🔴 物品 '{n}' 同时在 '{ci[n]}' 和 '{c['name']}' 背包中", "severity": "hard"})
                ci[n] = c["name"]

    def check_location_consistency(self):
        for c in self.characters:
            if c.get("status") != "alive": continue
            lc = int(c.get("last_appeared", 0) or 0)
            if lc == 0 or lc >= self.current_chapter: continue
            loc = c.get("location", "")
            for g in self.world.get("geography", []):
                if g.get("name") == loc and g.get("status") == "destroyed":
                    dc = int(g.get("destroyed_chapter", 0) or 0)
                    if dc and lc > dc:
                        self.errors.append({"rule": "R4_地理矛盾",
                            "message": f"🔴 '{c['name']}' 位于 '{loc}'，该地第{dc}章已毁", "severity": "hard"})

    def check_forgotten_threads(self):
        for t in self.threads:
            if t.get("resolved_chapter") is not None or t.get("importance") != "major": continue
            planted = int(t.get("planted_chapter", 0) or 0)
            devs = t.get("developments", []) or []
            gap = self.current_chapter - planted
            desc = t.get("description", "")[:30]
            if gap > 30 and not devs:
                self.warnings.append({"rule": "W1_遗忘伏笔",
                    "message": f"🟡 重要线索 '{desc}...' 已{gap}章无推进", "severity": "soft"})
            elif gap > 50 and not devs:
                self.errors.append({"rule": "W1_遗忘伏笔",
                    "message": f"🔴 重要线索 '{desc}...' {gap}章零推进，烂尾风险", "severity": "hard"})
            exp = t.get("expected_resolve_by")
            if exp and self.current_chapter > exp:
                self.warnings.append({"rule": "W1_逾期待收束",
                    "message": f"🟡 线索 '{desc}...' 超预期收束章节({exp})", "severity": "soft"})

    def check_absent_characters(self):
        for c in self.characters:
            if c.get("status") != "alive": continue
            last = int(c.get("last_appeared", 0) or 0)
            if last and self.current_chapter - last > 20:
                self.warnings.append({"rule": "W2_角色缺席",
                    "message": f"🟡 '{c['name']}' 已{self.current_chapter - last}章未出场", "severity": "soft"})

    def check_power_progression(self):
        hard_time = [r for r in self.world.get("power_system", {}).get("rules", [])
                     if r.get("severity") == "hard" and ("年" in r.get("description", "") or "时间" in r.get("description", ""))]
        if not hard_time: return
        for c in self.characters:
            for ch in c.get("power_changes", []):
                for r in hard_time:
                    self.warnings.append({"rule": "W3_修为检查",
                        "message": f"🟡 '{c['name']}' 修为需确认：{ch}，规则：{r['description']}", "severity": "soft"})

    def check_character_traits(self):
        for c in self.characters:
            if not c.get("key_traits"):
                self.suggestions.append({"rule": "S_性格锚点", "entity": c.get("id", c["name"]),
                    "message": f"🟢 '{c['name']}' 缺少 key_traits，建议补充以防性格偏移"})

    # ── 深度审计 ──
    def audit(self):
        self.check_all()
        self._audit_thread_coverage()
        self._audit_relationship_symmetry()
        self._audit_pacing()
        return {"errors": self.errors, "warnings": self.warnings, "suggestions": self.suggestions}

    def _audit_thread_coverage(self):
        if not self.threads: return
        total = len(self.threads)
        res = sum(1 for t in self.threads if t.get("resolved_chapter") is not None)
        maj = sum(1 for t in self.threads if t.get("importance") == "major")
        maj_r = sum(1 for t in self.threads if t.get("importance") == "major" and t.get("resolved_chapter"))
        self.suggestions.append({"rule": "S_线索覆盖", "entity": "all",
            "message": f"🟢 线索：总计{total}条，已收束{res}条；重要{maj}条，已收束{maj_r}条"})

    def _audit_relationship_symmetry(self):
        for c in self.characters:
            for rel in c.get("relationships", []):
                tid = rel.get("target", "")
                target = next((x for x in self.characters if x.get("id") == tid), None)
                if not target:
                    self.warnings.append({"rule": "W_关系悬空",
                        "message": f"🟡 '{c['name']}' 与 '{tid}' 有关系但角色不在库", "severity": "soft"})
                    continue
                rev = next((r for r in target.get("relationships", []) if r.get("target") == c.get("id")), None)
                if not rev:
                    self.suggestions.append({"rule": "S_关系对称", "entity": f"{c.get('id', c['name'])}→{tid}",
                        "message": f"🟢 '{c['name']}' →'{rel['type']}'→ '{target['name']}'，反向未设定"})

    def _audit_pacing(self):
        chapters = self.timeline.get("chapters", [])
        if len(chapters) < 3: return
        low = 0
        for ch in chapters:
            cnt = len(ch.get("events", []))
            num = ch.get("chapter", 0)
            low = low + 1 if cnt == 0 else 0
            if low >= 5:
                self.warnings.append({"rule": "W_节奏拖沓",
                    "message": f"🟡 第{num-low+1}-{num}章连续{low}章无事件", "severity": "soft"})

    # ── 重复建议抑制 ──
    def load_seen(self):
        return load_yaml(self.log_path).get("seen_suggestions", {})

    def update_seen(self, seen):
        """更新 seen_suggestions: 增量计数，持久化到 consistency-log.yaml"""
        for s in self.suggestions:
            rule, entity = s["rule"], s.get("entity", "")
            seen.setdefault(rule, {})
            if entity in seen[rule]:
                seen[rule][entity]["count"] = seen[rule][entity].get("count", 0) + 1
                seen[rule][entity]["last_seen_chapter"] = self.current_chapter
            else:
                seen[rule][entity] = {"count": 1, "first_seen_chapter": self.current_chapter,
                                      "last_seen_chapter": self.current_chapter}
        log = load_yaml(self.log_path)
        log["seen_suggestions"] = seen
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        save_yaml(str(self.log_path), log)
        return seen

    def apply_suppression(self, seen, threshold=3):
        """标记重复≥threshold次的🟢建议为 _suppressed，返回 summary"""
        for s in self.suggestions:
            entry = seen.get(s["rule"], {}).get(s.get("entity", ""), {})
            if entry.get("count", 0) >= threshold:
                s["_suppressed"] = True
        rule_counts = {}
        for s in self.suggestions:
            if s.get("_suppressed"):
                rule_counts[s["rule"]] = rule_counts.get(s["rule"], 0) + 1
        total = sum(rule_counts.values())
        parts = [f"{r}×{c}" for r, c in rule_counts.items()]
        summary = f"🟢 {total} suggestions suppressed (seen {threshold}+ times): {', '.join(parts)}" if total else ""
        visible = [s for s in self.suggestions if not s.get("_suppressed")]
        return visible, total, summary


def print_report(result, verbose=False):
    errors, warnings = result.get("errors", []), result.get("warnings", [])
    all_suggestions, summary = result.get("suggestions", []), result.get("suppressed_summary", "")

    print("\n" + "=" * 60 + "\n📋 逻辑一致性校验报告\n" + "=" * 60)

    if errors:
        print(f"\n🔴 硬冲突 ({len(errors)} 项)\n" + "-" * 40)
        for e in errors: print(f"  [{e['rule']}] {e['message']}")

    if warnings:
        print(f"\n🟡 软警告 ({len(warnings)} 项)\n" + "-" * 40)
        for w in warnings: print(f"  [{w['rule']}] {w['message']}")

    shown = all_suggestions if verbose else [s for s in all_suggestions if not s.get("_suppressed")]
    if shown:
        extra = ", 含已抑制" if verbose and summary else ""
        print(f"\n🟢 提示建议 ({len(shown)} 项{extra})\n" + "-" * 40)
        for s in shown:
            tag = " [suppressed]" if s.get("_suppressed") else ""
            print(f"  [{s['rule']}] {s['message']}{tag}")

    if summary and not verbose: print(f"  {summary}")
    if not errors and not warnings: print("\n✅ 未发现逻辑冲突，状态正常！")

    print(f"\n{'=' * 60}\n汇总: 🔴 {len(errors)} | 🟡 {len(warnings)} | 🟢 {len(all_suggestions)}\n" + "=" * 60 + "\n")
    return len(errors)


def main():
    parser = argparse.ArgumentParser(description="长篇小说逻辑一致性校验器")
    parser.add_argument("command", choices=["check", "audit"], help="check=快速校验, audit=深度审查")
    parser.add_argument("project_dir", help="项目目录")
    parser.add_argument("--verbose", action="store_true", help="显示全部建议（含已被抑制的）")
    args = parser.parse_args()
    if not os.path.isdir(args.project_dir):
        print(f"错误: 目录不存在: {args.project_dir}"); sys.exit(1)

    checker = ConsistencyChecker(args.project_dir)
    seen = checker.load_seen()
    result = checker.check_all() if args.command == "check" else checker.audit()

    seen = checker.update_seen(seen)
    visible, sup_count, summary = checker.apply_suppression(seen)
    result["suggestions"] = checker.suggestions  # 含 _suppressed 标记
    result["suppressed_summary"] = summary

    error_count = print_report(result, verbose=args.verbose)
    sys.exit(1 if error_count > 0 else 0)


if __name__ == "__main__":
    main()
