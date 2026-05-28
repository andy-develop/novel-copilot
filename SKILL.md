---
name: novel-copilot
description: "长篇小说全自动写作助手：给一个开头自动成书。发散→评分→选择→写作→校验，循环不停。逻辑一致性守护 + 14种发散模式 + 自动方向选择 + 一致性门控 + 叙事纪律(300字入局/高潮分拆) + 读者情绪管理(前10章不虐主) + 爽度引擎(六大爽型/三步构建/密度规则/旁观者三层) + 画面感引擎(镜头语言/感官五重/动作微分解/环境投射/物件象征/声画对位) + 快节奏四原则(零废段/场景快切/对话角力/行动代心理)。30万字不崩盘，死人不会复活，伏笔不会遗忘，每章都有爽点和画面。"
version: 3.0.0
author: Hermes Agent
tags: [小说, 写作, 长篇, 逻辑一致性, 剧情发散, 角色管理, 世界观, 悬念, 翻页驱动, 叙事纪律, 读者情绪, 爽度, 画面感, 快节奏]
trigger: 当用户要写小说、续写章节、检查设定矛盾、探索剧情分支时触发
related_skills: []
---

# 长篇小说写作助手 (Novel Copilot)

超长篇小说（30万字+）的核心难题：**写到后面忘了前面**。本 skill 通过结构化状态追踪 + 逻辑校验 + 剧情发散 + **全自动写作引擎** + **叙事纪律引擎**，确保长篇不崩盘、不注水、不让读者弃书。

## 核心理念

> 写作是发散的，校验是收敛的。先发散，再校验，最后落笔。

**叙事三优先级**（冲突时高优先级不可妥协）：
- **P0 = 节奏 + 爽度 + 画面感** — 读者留不留得住、爽不爽、记不记得住，全靠这三条
- **P1 = 一致性 + 散文质量** — 不崩盘、不啰嗦
- **P2 = 大纲 + 字数 + 状态文件** — 工具而非枷锁

> 当 P0 与 P2 冲突时（如大纲要求铺垫但铺垫会拖慢节奏），**节奏爽感优先**，调整大纲而非牺牲节奏。

## 项目结构

> **每个小说项目 = 一个 GitHub 仓库**（默认 `andy-develop/书名`，private）。初始化时自动创建，每章写完自动 commit & push。

```
my-novel/                        # ← GitHub 仓库 andy-develop/my-novel
├── .git/                        # Git 版本控制
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

## 十大模块

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

#### 6.1 发散去重（防雷同）

> **问题**：AI 反复用同 2-3 种模式 → 章节雷同 → 读者疲劳。

**规则**：
1. **窗口检查**：生成方向前扫描最近 5 章的 `divergence_pattern`，最近 3 章用过的模式**禁止**作为主模式
2. **多样性下限**：10 章窗口内须用 ≥6 种模式，低于 = 强制注入未使用模式
3. **组合新鲜度**：相同模式组合 8 章内不可重复
4. **评分惩罚**：模式在最近 5 章每出现一次，新奇度 -1
5. **Stale 检测**：连续 3 章共享主模式 → 下一章必须用未使用池

**未使用池注入**：10 章内 >4 种模式未使用 → 下次必须包含 ≥1 个未使用方向

#### 6.2 世界观格局升级引擎

> **问题**：主角"升级"但世界不变——数字变大，格局没变，读者不再在乎。

**核心原则**：每次升级必须扩展主角对世界的认知边界，世界本身要变大。

**四层格局**（主角必须逐层推进）：

| 层级 | 范围 | 变化 | 示例 |
|------|------|------|------|
| **T1 街头** | 本地生存 | 身体能力、个人盟友 | "我出拳更重了" → 街头帮派战 |
| **T2 城市** | 势力政治 | 社会地位、资源调动、政治阵营 | "公会听我的了" → 城市级权力洗牌 |
| **T3 国家/体系** | 制度真相 | 发现隐藏规则、改写游戏 | "排名系统是用来压制我们的" → 国家阴谋 |
| **T4 世界/宇宙** | 现实本质 | 世界规则崩塌/重塑、存在级赌注 | "神在害怕我们" → 现实级对抗 |

**升级规则**：
1. 同一格局不可停留超过 15 章，必须有格局跨越事件
2. 每次跨越须有**红色药丸时刻**：信息发现让主角看到旧世界只是更大世界的子集
3. **能力升级不带格局扩展 = 浪费**：新能力必须解锁新层级冲突，不是在旧层级赢得更快
4. 旧敌人变无关，不反复纠缠：T1 反派到 T3 不应是威胁
5. 格格不可回退：进入 T3 后冲突不可退缩回 T2

**每卷格局规划**：卷一 T1→T2 / 卷二 T2→T3 / 卷三 T3→T4

**升级后自检**：
```
□ 这次升级改变的是主角「在乎什么」，不仅是「多强」？
□ 是否解锁了之前不存在的冲突层级？
□ T1 版主角能否理解这个冲突？（不能 = 好）
```

## 模块七：自动写作引擎

> 执行协议：`references/auto-writing-execution-protocol.md` | 会话恢复：`references/session-resumption-playbook.md` | 有机冲刺：§7.10 + `references/volume-outline-guide.md`

核心循环：
```
开头/种子 → 初始化项目
LOOP: 读取状态 → 发散3-5方向 → 评分选择最优 → 写章节正文 → 更新状态 → 一致性门控 → Git同步 → 终止检查(否→继续)
```

- **7.1 方向评分**：7维加权评分(节奏适配25%/翻页驱动20%/线索推进15%/情感利用15%/一致性10%/新颖度10%/钩子5%) + 排雷规则 + 选择策略 → `references/scoring-and-selection.md`
- **7.2 一致性门控**：周期轻检/深审 + 重大事件/红灯/弧线切换触发 + 自动修复 → `references/scoring-and-selection.md`
- **7.3 循环详解**：读取→发散→评分→写作→更新→门控→Git同步→终止，8步完整流程 → `references/scoring-and-selection.md`
- **7.4 节奏自调节**：张力检测(连续同钩/高张疲劳/低张拖沓) + 弧线自动推进 → `references/scoring-and-selection.md`
- **7.5 长线管理**：跨弧线衔接 + 卷间过渡 + 终局管理 → `references/scoring-and-selection.md`
- **7.x 设定体系**：体系化设定速查 → `references/setting-system-tracking.md`
- **7.7 实操陷阱**：24条验证陷阱（含v2.1 commit_chapter工作流、字数统计、YAML引号嵌套等）→ `references/auto-write-practical-tips.md`
- **7.8 状态同步**：会话恢复必做 + 过期检测信号 + 高频/批量更新策略 → `references/auto-write-practical-tips.md`
- **7.9 方向融合**：TOP1+TOP2融合策略 + 实战案例 + 节奏参数 → `references/scoring-and-selection.md`
- **7.x 规则一致性审计**：修改规则后的跨文件一致性检查清单 → `references/rule-consistency-audit-checklist.md`

**实操 Top 7 陷阱速记**：
1. **arc-tracker 每章必更新**，否则 rhythm 退化为空
2. **状态文件不会自动更新**，每5章强制回写 characters/threads/debts
3. **consistency_checker 报全绿可能是空文件**——先确认数据有意义
4. **阶段名必须与 automation-config 匹配**，否则 rhythm 返回空
5. **跨会话必须先同步再写作**——详见 `references/session-resumption-playbook.md`
6. **commit_chapter 不自动切换弧线阶段**——跨越阶段时必须手动 patch arc-tracker.yaml 的 current_phase/phase_start_chapter/phase_chapters_elapsed
7. **consistency_checker 无 --deep 参数**——`check` 自动按章节号决定深浅，`audit` 做全局审查
8. **consistency_checker 兼容 dict/list 两种 YAML 格式**(v2.1.2+)——characters.yaml 和 relationships 字段无需特定格式
9. **章节文件名必须零填充**——`ch080.md` 不是 `ch80.md`，`write_file` 路径务必用 `ch{NNN}.md` 三位格式
10. **commit_chapter.py 自动发现章节文件**(v2.2+)--省略`--count-words`时自动按`--chapter`拼接`chapters/chNNN.md`路径
11. **consistency_checker 同规则折叠**(v2.2+)--同类🟢建议>5条自动折叠为一行汇总（`--verbose`查看全部）
12. **auto_sync.py 同步检测**(v2.2+)--`auto_sync.py --dir <项目>`一键检测characters/threads/arc-tracker/timeline/debts落后情况
13. **每章写完必须 git commit & push**(v2.4+)——commit 消息格式 `ch{NNN}: 标题`，卷完结加 `[卷完结]`，全书完结加 `[全书完结]`
14. **跨会话恢复先 git pull**(v2.4+)——其他会话可能已推送新章节，不 pull 就写会产生冲突
15. **每章前300字必须有冲突/行动**(v2.5+)——参见 §9.1 叙事克制，环境描写、背景回顾开篇都是违规
16. **大高潮超过5000字必须分拆**(v2.5+)——参见 §9.2，一口气写完高潮是叙事资产浪费
17. **前10章主角被动反应不超2章连续**(v2.5+)——参见 §9.3 能动性原则，2章连续被动必须下章补主动，3章连续一票否决
18. **commit_chapter.py --thread-advance 对不存在的线索ID静默跳过**——显示"⚠️ 线索 XXX 未找到，跳过"但不报错。提交前确认线索ID与threads.yaml一致；含"+"号的复合线索名会被跳过（parser局限）
19. **volume_transition.py 只做机械重置，不创建大纲/角色/线索**——后续8步手动清单见§7.5.1，遗漏任何一步都会导致新卷写作卡壳

### CLI 工具速查（v2.1 新增）

| 命令 | 用途 | 示例 |
|------|------|------|
| `commit_chapter.py` | 一键章后状态更新（替代4-6次patch） | `--dir . --chapter 42 --words 3500 --pattern "D5+D9" --hook 焦虑型 --tension 8` |
| `volume_transition.py` | 卷间机械状态重置+AI待办清单 | `--dir . --volume 5 --title "根" --first-chapter 71` |
| `auto_write.py wordcount` | 扫描全部章节统计中文字数 | `--dir . [--update]`（无--update仅打印） |
| `auto_write.py score --mode 3dim` | 3维简化评分(节奏40%/线索35%/安全25%) | `--d1 "D7,4,5,4"` |
| `consistency_checker.py --verbose` | 显示全部建议含已抑制的 | 默认抑制连续3次🟢建议+同规则>5条折叠 |
| `auto_sync.py --dir .` | 检测状态文件同步差距 | 输出characters/threads/arc-tracker/timeline落后章数 |

`commit_chapter.py` 高级用法：
- `--count-words chapters/ch042.md` 自动统计中文字数，覆盖 `--words`（v2.2+：省略此参数时自动按`--chapter`拼接路径）
- `--thread-advance "T015:developed,T018:resolved:42"` 批量推进/收束线索
- `--dry-run` 预览变更不写入

### 7.10 有机冲刺模式（大纲驱动）

当卷大纲足够详细时，跳过 CLI 直接有机选择方向，速度是脚本模式的2-3倍。

**前提**：✅6大种子(主线×1+谜题×2+抉择×2+情感×1) ✅弧线阶段表 ✅设定速查表 ✅前卷状态已完成过渡

**零CLI循环（v2.2 commit_chapter 驱动）**：

> ⚠️ **核心原则：用户说"继续"=不间断冲刺。不要暂停问问题、不要输出统计表、不要确认。写就完了。**

```
1. 心算确认阶段 → 选择发散模式
2. write_file: 写章节正文 ch{NNN}.md（路径必须三位零填充！ch080.md ✅ ch80.md ❌）
3. commit_chapter.py --dir DIR --chapter N --title "标题" \
     --pattern "D5+D9" --hook 焦虑型 --tension 8 \
     [--thread-advance "T015:developed"]
   ↑ --count-words 已省略，v2.2+自动拼接 chapters/chNNN.md
4. 每3-5章: consistency_checker.py check DIR
5. 每5章: patch characters.yaml + emotional-debts.yaml
6. 每3-5章批量 git push: git add -A && git commit -m "ch{NNN}-{MMM}: 标题批" && git push origin main
   ↑ 批量提交比逐章push更高效。commit消息可用范围或最终章号标注
   ↑ 单章commit格式：ch{NNN}: 标题；批量：ch{NNN}-ch{MMM}: 批次提交
7. 继续下一章（不停顿、不问用户）
```
实测：90章连续写作，零手动patch，零一致性冲突

**冲刺模式字数管理**：连续冲刺10+章时字数会在1500-4500之间波动。稳定方法：
- 大纲每章标注预估字数（如"本章3000字+关键场景"）
- 每5章用 `auto_write.py wordcount --dir <目录>` 校准
- 字数缩水严重时在下一章方向中加入细节类模式（D6双线映照/D13情感回收）

**批量写作优化**（实测效率提升2-3倍）：连续冲刺时，可一次 invoke 2-3个 `write_file`（ch080/ch081/ch082），然后用一次 `commit_chapter.py` 逐章提交，最后批量 `git push`。减少上下文切换开销，但注意：
- 批量写作会降低每章的断章自检质量，高风险章节（高潮/反转/角色死亡）仍应单章写
- 批量 git push 的 commit 消息用范围格式：`ch080-ch082: 批次提交`

**与脚本模式切换**：卡住→回退CLI | 跨卷→必须CLI做过渡

**卷完结流程**：
1. `consistency_checker.py audit <目录>` 全局审查
2. `auto_write.py wordcount --dir <目录> --update` 精确字数
3. 检查 threads.yaml 全部 major 线索已 resolved
4. patch arc-tracker.yaml current_phase 为最终阶段
5. 输出完本统计表（章节/字数/线索收束/冲突数）

详细指南：`references/volume-outline-guide.md`

冲刺模式可通过 automation-config.yaml 的 sprint 部分启用。设置 sprint.enabled: true 跳过 rhythm/score，consistency 间隔自动放宽。

### 7.5.1 卷间过渡完整清单

> `volume_transition.py` 只做机械重置（arc-tracker/consistency-log/novel-project），以下手动步骤 **必须全部完成** 才能开始新卷写作：

```
1. ☐ 创建卷大纲 outlines/volumeN-outline.md
   - 六大种子（主线×1 + 谜题×2 + 抉择×2 + 情感×1）
   - 弧线阶段规划表（阶段|章节范围|核心事件|张力|发散模式）
   - 前5-10章逐章规划（模式/核心/钩子/张力）

2. ☐ 全量重写 characters.yaml
   - 保留存活角色（更新 last_appeared/condition/abilities/relationships）
   - 新增本卷新角色（每个至少: id/name/status/abilities/power_level/relationships/key_traits）
   - 移除不再出场的角色或标记 status=absent
   - 每个 relationship 标注 since_chapter

3. ☐ 全量重写 threads.yaml
   - 封卷旧线索：status=resolved, payoff_chapter=实际收束章节
   - 播种新线索：至少3条 active（1 main + 1 puzzle + 1 character_arc）
   - 每条新线索必须有 planted_chapter/last_updated_chapter/key_points
   - 保留旧线索（status=resolved）供一致性校验回溯

4. ☐ 全量重写 emotional-debts.yaml
   - 结转未偿还的旧债（status=outstanding/partially_paid）
   - 播种新情感债（每卷至少2-3条）

5. ☐ 更新 world.yaml
   - 新增本卷场景（每个至少: id/name/type/location_type/description/atmosphere/danger_level）
   - 新增世界规则（如有新设定的硬规则）
   - 保留旧场景（可能跨卷复用）

6. ☐ 更新 timeline.yaml
   - 添加卷分界标记（chapter=上卷末/下卷首, event="卷N→卷N+1过渡"）
   - 清空本卷事件区（写作中更新）

7. ☐ 一致性确认
   - 运行 consistency_checker.py check 确认无硬冲突
   - 确认 arc-tracker.current_phase 与 automation-config 匹配

8. ☐ Git 提交
   - git add -A && git commit -m "state: 卷N→卷N+1过渡+状态文件全量更新 [卷N+1准备]"
   - git push origin main
```

**常见遗漏**：忘记更新 `since_chapter` 字段→关系时间线错乱；新线索缺 `key_points`→后续章节推进无锚点；world.yaml 缺 `danger_level`→禁区探索模式无参考基线。

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

## 模块八：开篇冲击力引擎（第1-2章专用）

> **铁律：读者给一本新小说的耐心只有两章。**

第一章必须同时完成三件事：**即刻冲突**（开篇就有危机/异常）、**角色锚定**（5分钟知主角是谁）、**悬念炸弹**（章末读者无法不追问）。

第二章任务：**冲突升级 + 情感投资 + 认知翻转 + 次级悬念**。

第1-2章评分权重调整：翻页驱动35%/钩子强度25%。一票否决：翻页驱动≤2、钩子强度≤2、前500字无冲突、零爽点。

> 完整规则：死亡模式/评分公式/写后审查清单/5种钩子模板 → `references/opening-impact-engine.md`

---

## 模块九：叙事纪律与读者情绪管理

### 9.1 叙事克制（全章通用）

- **300字入局**：每章前300字必须进入冲突/行动，禁止环境描写/背景回顾开篇。
- **背景融入**：禁止超过200字的纯设定段落。用"主角需要这个设定"的场景引入，而非"作者想告诉读者"。
- **目标驱动**：主角从第一章起必须有近期目标。3章内无主动行动 → 补上主动目标。

### 9.2 断章与高潮控制

- **在该断的地方断**：好章结尾是"事情正到最关键处"，不是"事情解决了"。断章黄金位置：决策前/真相前/冲突前/不安信息刚出现/角色踏入危险不知情。
- **大高潮分拆**：超过5000字→分拆为2-3章（高潮前夜→高潮爆发→高潮余波）。
- **断章自检**：读者感觉"好吧"非"然后呢？"→失败。好的断章让读者带着1-2个未解问题离开。

### 9.3 早期情绪保护（前10章）

**前10章不虐主**。红线：彻底击败无反击/剥夺核心能力/严重羞辱无反击/重要盟友死亡。连续2章被动→下章必须主动（第3章被动=一票否决）。

前10章主动行动占比≥60%。爽度密度加倍（每2章≥1中爽点）。第10章必做情绪审查。

> 完整规则：300字入局/背景融入判定标准/高潮分拆节奏表/10章情绪审查清单 → `references/narrative-discipline.md`

---

## 模块十：爽度引擎 + 画面感引擎

### 10.1 快节奏四原则

| 原则 | 规则 | 违规检测 |
|------|------|---------|
| **零废段** | 每段至少完成：推进剧情/制造冲突/揭示信息/创造爽点 | 删掉不影响主线=废段 |
| **场景快切** | 场景切换不超过3句过渡 | 超过3句=压缩 |
| **对话即角力** | 每句对话推进信息/施压/反击/暴露弱点。纯寒暄≤2句 | 超过3句纯寒暄=砍 |
| **行动代心理** | 用行动和对话展现内心。心理独白>150字且无冲突穿插=违规 | 拆散分布到行动中 |

### 10.2 爽度引擎

**六大爽型**（每5章≥3种）：装逼打脸/逆风翻盘/智商碾压/实力碾压/夺宝抢机缘/人心归附

**密度规则**：每3章≥1中爽点 | 每5章≥1大爽点 | 弧线高潮章≥1极爽点 | 连续2章零爽→违规告警（3章零爽=一票否决）

**爽点三步**：压制/困境（憋气）→ 转折/蓄力（合理翻盘，有伏笔支撑）→ 释放/碾压（快准狠，2段内完成）

**旁观者三层**（大爽点≥2层）：①直接对手崩溃/恐惧 ②同级旁观者震惊/重新评估 ③高手/前辈动容/忌惮

### 10.3 画面感引擎

**六大技法**：

| 技法 | 核心 |
|------|------|
| 镜头语言 | 远景/中景/特写/推/拉/跟拍，重要场景「远→中→特」切换 |
| 感官五重 | 重要场景≥3种感官，高潮5种全满。禁用「他很害怕」→ 用身体/感官说情绪 |
| 动作微分解 | 关键动作拆成1-3秒慢动作，适用一招制敌/关键反转/死亡瞬间 |
| 环境投射 | 用天气/光线/空间说情绪。压迫→低矮天花板，觉醒→光线涌入 |
| 物件象征 | 关键物件走完三阶段：首次出现（功能引入）→再次出现（叠加情感）→最终出现（封印使命） |
| 声画对位 | 声音和画面矛盾时张力最大。身后人声鼎沸，他只听见心跳 |

### 10.4 爽度+画面感联合规则

- **铁律一**：爽点必须有画面（≥2种技法呈现）。「他一拳打倒对手」=新闻，不是小说。
- **铁律二**：画面必须服务叙事。删掉后爽感不减的描写=废画面。
- **冲突优先级**：爽度 > 画面感 > 文笔修饰

### 10.5 每章自检

```
□ 【爽度密度】3章内≥1中爽？5章内≥1大爽？
□ 【三步构建】压制→转折→释放完整？
□ 【旁观者】大爽点≥2层旁观者反应？
□ 【类型轮换】近5章类型有变化？（不可连3次同类型）
□ 【镜头】「远→中→特」或「特→中→远」镜头流程？
□ 【感官】重要场景≥3种感官？高潮5种？
□ 【环境】环境描写服务情绪？删掉后受损？
□ 【物件】关键物件重复出现并叠加含义？
```

> 完整技法：六大爽型详细写法要点/反模式、六种镜头类型含示例、感官五重对比表、动作微分解示例、环境情绪投射表、物件象征三阶段写法、声画对位示例 → `references/satisfaction-cinema-details.md`

---

## 关键陷阱

**逻辑类**：死人复活/物品凭空出现/距离时间矛盾/伏笔烂尾/能力膨胀/角色分裂。→ `references/logic-consistency-taxonomy.md`

**爽度类**：假压制真装逼/天降翻盘/打脸拖沓/爽点单调/旁观者缺失。→ `references/satisfaction-cinema-details.md` §10.2

**画面感类**：告诉代替画面/全程中景/废画面/微分解过度/感官单一。→ `references/satisfaction-cinema-details.md` §10.3

---

## 快速开始

### 全自动模式（推荐）
1. **初始化**：`python3 scripts/auto_write.py init --name "书名" --mode auto`
2. **创建 GitHub 仓库**（注意顺序）：
   ```bash
   cd ~/novels/书名
   git init
   git config user.email "xxx@xxx.com" && git config user.name "name"  # 新环境必须
   git add -A && git commit -m "init: 项目初始化"                      # 必须先有commit
   git branch -m main                                                  # 确保分支名main
   gh repo create andy-develop/书名 --private --source=. --push       # 创建远程+关联+推送
   ```
   如果 `gh repo create` 失败，可手动：创建远程仓库 → `git remote set-url origin https://USER:TOKEN@github.com/USER/书名.git` → `git push -u origin main`
3. **提供开头**：告诉 AI "全自动写《书名》，开头如下：[开头内容]"
4. **AI 自动完成**：发散→选择→写作→校验→Git同步，循环直至完成
5. **每章写完**：`commit_chapter.py` 一键更新状态 + `git add -A && git commit -m "ch{NNN}: 标题" && git push origin main`
6. **中途干预**：随时可以说"暂停"/"这一章我来选"/"节奏太慢"
7. **卷间过渡**：`volume_transition.py` 重置状态 + AI 手动完成大纲/角色/线索重写 + git push
8. **字数校准**：`auto_write.py wordcount --dir . --update`（CJK精确统计）
9. **完成**：AI 输出全书摘要、线索收束报告、润色建议 + 最终 git push `[全书完结]`

### 人机协作模式
1. **新建项目**：`python3 scripts/novel_state.py init --name "书名" --dir ~/novels/书名`
2. **创建 GitHub 仓库**：`cd ~/novels/书名 && git init && gh repo create andy-develop/书名 --private --source=. --push`
3. **填写设定**：编辑 state/ 下的 yaml 文件
4. **写每一章前**：运行 `consistency_checker.py check` 查看当前状态
5. **发散+评分**：让 AI 发散剧情（含自动评分），你选方向，AI 写章节
6. **写完每章后**：让 AI 更新状态文件 + git commit & push
7. **每10章**：运行 `consistency_checker.py audit` 做全局审查
