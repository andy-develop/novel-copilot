---
name: novel-copilot
description: "长篇小说全自动写作助手：给一个开头自动成书。发散→评分→选择→写作→校验，循环不停。逻辑一致性守护 + 14种发散模式 + 自动方向选择 + 一致性门控。30万字不崩盘，死人不会复活，伏笔不会遗忘。"
version: 2.1.0
author: Hermes Agent
tags: [小说, 写作, 长篇, 逻辑一致性, 剧情发散, 角色管理, 世界观, 悬念, 翻页驱动]
trigger: 当用户要写小说、续写章节、检查设定矛盾、探索剧情分支时触发
---

# 长篇小说写作助手 (Novel Copilot)

超长篇小说（30万字+）的核心难题：**写到后面忘了前面**。本 skill 通过结构化状态追踪 + 逻辑校验 + 剧情发散 + **全自动写作引擎**，确保长篇不崩盘。

## 核心理念

> 写作是发散的，校验是收敛的。先发散，再校验，最后落笔。

## 项目结构

```
my-novel/
├── state/
│   ├── characters.yaml          # 角色状态库
│   ├── world.yaml               # 世界设定库
│   ├── threads.yaml             # 剧情线索库
│   ├── timeline.yaml            # 时间线
│   ├── rules.yaml               # 世界规则（不可违反的设定）
│   ├── arc-tracker.yaml         # 弧线追踪
│   ├── emotional-debts.yaml     # 情感债追踪
│   └── consistency-log.yaml     # 一致性校验日志
├── chapters/                    # 章节正文 ch{NNN}.md
├── outlines/                    # 弧线大纲 + 章节规划
├── automation-config.yaml       # 自动写作配置
└── novel-project.yaml           # 项目元信息
```

## 六大模块

### 模块一：角色状态库 (characters.yaml)
追踪角色当前状态，每次写到时自动校验。字段：`id, name, aliases, status(alive|dead|missing|sealed), death_chapter, death_cause, location, abilities, relationships, inventory, notes, last_appeared`。校验：死者无行动、物品唯一持有、能力增减有事件支撑、位置移动合理。

### 模块二：世界设定库 (world.yaml)
追踪地理、势力、能力体系。字段：`geography(id,name,type,location,status,destroyed_chapter), factions, power_system(name,ranks,rules)`。校验：已毁地点不再引用、势力变动有事件、能力使用不违反规则。

### 模块三：剧情线索库 (threads.yaml)
管理伏笔(planted)和收束(resolved)，防烂尾。字段：`id, description, planted_chapter/context, resolved_chapter/how, importance(major|minor|easter_egg), related_characters`。校验：major线索必须有推进、已resolved不重用、长期停滞触发遗忘警告。

### 模块四：时间线 (timeline.yaml)
按章节记录事件，防时间矛盾。字段：`chapter, events(timestamp, description, characters_involved, note)`。校验：角色不瞬移、时间流逝合理、回忆须标注。

### 模块五：世界规则 (rules.yaml)
**绝对不可违反的设定**。字段：`id, description, severity(hard|soft)`。hard 规则不可违反，soft 违反需合理理由。

### 模块六：剧情发散引擎
基于 14 种发散模式生成多个剧情方向。**核心原则：文似看山不喜平。**
- 14 种模式：D1线索咬合 | D2关系裂变 | D3禁区探索 | D4反转颠覆 | D5规则突变 | D6双线映照 | 🔑D7认知差悬念 | D8伪胜/败 | D9两难抉择 | 🔑D10倒计时压迫 | D11逆风孤战 | D12暗流涌动 | 🔑D13情感债回收 | D14渔线沉底
- 节奏模型：四层波浪+钩子链
- 详见 `references/divergence-patterns.md`、`references/auto-write-workflow.md`

## 模块七：自动写作引擎

> 执行协议：`references/auto-writing-execution-protocol.md` | 会话恢复：`references/session-resumption-playbook.md` | 有机冲刺：§7.10 + `references/volume-outline-guide.md`

核心循环：
```
开头/种子 → 初始化项目
LOOP: 读取状态 → 发散3-5方向 → 评分选择最优 → 写章节正文 → 更新状态 → 一致性门控 → 终止检查(否→继续)
```

- **7.1 方向评分**：7维加权评分(节奏适配25%/翻页驱动20%/线索推进15%/情感利用15%/一致性10%/新颖度10%/钩子5%) + 排雷规则 + 选择策略 → `references/scoring-and-selection.md`
- **7.2 一致性门控**：周期轻检/深审 + 重大事件/红灯/弧线切换触发 + 自动修复 → `references/scoring-and-selection.md`
- **7.3 循环详解**：读取→发散→评分→写作→更新→门控→终止，7步完整流程 → `references/scoring-and-selection.md`
- **7.4 节奏自调节**：张力检测(连续同钩/高张疲劳/低张拖沓) + 弧线自动推进 → `references/scoring-and-selection.md`
- **7.5 长线管理**：跨弧线衔接 + 卷间过渡 + 终局管理 → `references/scoring-and-selection.md`
- **7.x 设定体系**：体系化设定速查 → `references/setting-system-tracking.md`
- **7.7 实操陷阱**：19条验证陷阱（chapter-plan跳过、评分心算、状态不同步、YAML patch碰撞等）→ `references/auto-write-practical-tips.md`
- **7.8 状态同步**：会话恢复必做 + 过期检测信号 + 高频/批量更新策略 → `references/auto-write-practical-tips.md`
- **7.9 方向融合**：TOP1+TOP2融合策略 + 实战案例 + 节奏参数 → `references/scoring-and-selection.md`

**实操 Top 5 陷阱速记**：
1. **arc-tracker 每章必更新**，否则 rhythm 退化为空
2. **状态文件不会自动更新**，每5章强制回写 characters/threads/debts
3. **consistency_checker 报全绿可能是空文件**——先确认数据有意义
4. **阶段名必须与 automation-config 匹配**，否则 rhythm 返回空
5. **跨会话必须先同步再写作**——详见 `references/session-resumption-playbook.md`

### CLI 工具速查（v2.1 新增）

| 命令 | 用途 | 示例 |
|------|------|------|
| `commit_chapter.py` | 一键章后状态更新（替代4-6次patch） | `--dir . --chapter 42 --words 3500 --pattern "D5+D9" --hook 焦虑型 --tension 8` |
| `volume_transition.py` | 卷间机械状态重置+AI待办清单 | `--dir . --volume 5 --title "根" --first-chapter 71` |
| `auto_write.py wordcount` | 扫描全部章节统计中文字数 | `--dir . [--update]`（无--update仅打印） |
| `auto_write.py score --mode 3dim` | 3维简化评分(节奏40%/线索35%/安全25%) | `--d1 "D7,4,5,4"` |
| `consistency_checker.py --verbose` | 显示全部建议含已抑制的 | 默认抑制连续3次🟢建议 |

`commit_chapter.py` 高级用法：
- `--count-words chapters/ch042.md` 自动统计中文字数，覆盖 `--words`
- `--thread-advance "T015:developed,T018:resolved:42"` 批量推进/收束线索
- `--dry-run` 预览变更不写入

### 7.10 有机冲刺模式（大纲驱动）

当卷大纲足够详细时，跳过 CLI 直接有机选择方向，速度是脚本模式的2-3倍。

**前提**：✅6大种子(主线×1+谜题×2+抉择×2+情感×1) ✅弧线阶段表 ✅设定速查表 ✅前卷状态已完成过渡

**零CLI循环**：心算确认阶段→选择发散模式→write_file正文→并发patch状态→3章一次consistency_check

**与脚本模式切换**：卡住→回退CLI | 跨卷→必须CLI做过渡

详细指南：`references/volume-outline-guide.md`

冲刺模式可通过 automation-config.yaml 的 sprint 部分启用。设置 sprint.enabled: true 跳过 rhythm/score，consistency 间隔自动放宽。

### 7.6 与人工模式的切换

| 场景 | 操作 |
|------|------|
| 自动→人工 | 设 `mode: manual` 或说"暂停自动写作" |
| 人工→自动 | 设 `mode: auto` 或说"继续自动写作" |
| 单章接管 | 生成方向后说"这章我来选" |
| 一键全自动 | 初始化后说"全自动写完" |

---

## 使用流程

### 模式A：全自动写作
1. **会话恢复**：确认章节数与 novel-project.yaml 一致，不同步则先批量更新 → `references/session-resumption-playbook.md`
2. **初始化**：`auto_write.py init --name "书名" --dir ~/novels/my-novel --mode auto`
3. **提供开头**：AI 自动提取设定→填充状态→进入循环
4. **自动循环**：每章输出 📝完成/🎭模式/🎣钩子/📊进度/✅一致性
5. **章后提交**：`commit_chapter.py` 一键更新 novel-project/arc-tracker/threads/consistency-log（替代手动patch）
6. **中途干预**：随时"暂停"/"用D9"/"角色不该死"/"节奏太慢"/"跳到高潮"
7. **卷间过渡**：`volume_transition.py` 重置状态 + AI 手动完成大纲/角色/线索重写
8. **完成输出**：全书摘要 + 线索收束 + 一致性审计 + `wordcount --update` 精确字数

### 模式B：人机协作
1. **初始化**：`novel_state.py init --name "书名" --dir ~/novels/my-novel`
2. **写前校验**：`consistency_checker.py check ~/novels/my-novel`
3. **发散+评分**：AI 生成3-5方向含评分，你选方向，AI 写章节
4. **写后更新**：AI 自动提取事件→更新yaml→校验
5. **定期审查**：`consistency_checker.py audit ~/novels/my-novel`

---

## 关键陷阱

> 当前覆盖 15/70 种逻辑问题(21%)，完整分类见 `references/logic-consistency-taxonomy.md`

- **死人复活**：status=dead 角色不能再有行动/对话
- **物品凭空出现/消失**：inventory 追踪归属，转移须有事件
- **距离/时间矛盾**：移动时间须与距离/方式匹配
- **伏笔烂尾**：major 线索长期 resolved_chapter=null 会持续告警
- **修为/能力膨胀**：增长须符合 power_system.rules 的进阶速度
- **角色分裂**：同一角色矛盾性格会被 key_traits 比对标记

---

## 快速开始

### 全自动模式（推荐）
1. **初始化**：`python3 scripts/auto_write.py init --name "书名" --mode auto`
2. **提供开头**：告诉 AI "全自动写《书名》，开头如下：[开头内容]"
3. **AI 自动完成**：发散→选择→写作→校验，循环直至完成
4. **每章写完**：`commit_chapter.py --dir . --chapter N --count-words chapters/chNNN.md --pattern "D5" --hook 焦虑型 --tension 8`（一键更新所有状态文件）
5. **中途干预**：随时可以说"暂停"/"这一章我来选"/"节奏太慢"
6. **卷间过渡**：`volume_transition.py --dir . --volume N --title "卷名"`（机械重置+AI待办清单）
7. **字数校准**：`auto_write.py wordcount --dir . --update`（CJK精确统计）
8. **完成**：AI 输出全书摘要、线索收束报告、润色建议

### 人机协作模式
1. **新建项目**：`python3 scripts/novel_state.py init --name "书名"`
2. **填写设定**：编辑 state/ 下的 yaml 文件
3. **写每一章前**：运行 `consistency_checker.py check` 查看当前状态
4. **发散+评分**：让 AI 发散剧情（含自动评分），你选方向
5. **写完每章后**：让 AI 更新状态文件
6. **每10章**：运行 `consistency_checker.py audit` 做全局审查
