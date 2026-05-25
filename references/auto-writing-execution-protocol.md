# 自动写作执行协议

> 这是 AI agent 执行全自动写作循环时的实际操作步骤。
> SKILL.md Module 7 定义了理论和算法，本文件定义执行动作序列。

## 自动写作循环 — Agent 执行步骤

### Step 0: 会话恢复（跨会话续写时必须执行）

> 当从新会话续写已有项目时（用户说"继续"），必须先同步状态，再进入写作循环。

```
1. git pull origin main  ← 先拉取最新代码（其他会话可能已推送新章节）
2. 读取 novel-project.yaml → 获取 current_chapter 和 current_words
2. 检查 state/arc-tracker.yaml → recent_patterns 和 recent_hooks 是否覆盖到 current_chapter
3. 检查 state/characters.yaml → last_appeared 字段是否接近 current_chapter（差距>3说明严重过期）
4. 检查 state/threads.yaml → developments 是否覆盖近5章（空数组=严重过期）
5. 检查 state/emotional-debts.yaml → 是否有近5章新增的情感债
6. 如发现任何状态文件严重落后 current_chapter：
   a. 通读最近未同步的章节（从最后有记录的章节到 current_chapter）
   b. 提取：角色位置/状态变化、线索推进、新情感债、弧线阶段变化
   c. 批量更新所有过期状态文件
   d. 更新 arc-tracker.yaml（补齐 recent_patterns 和 recent_hooks）
7. 确认 arc-tracker.current_phase 与 automation-config.yaml 的 arc_phases 键匹配
8. 运行 `auto_write.py rhythm` 确认状态同步后推荐正常
```

**为什么这一步必须做**：AI 写正文时不回写状态——这是设计，不是 bug（全自动模式中事件提取依赖 AI 理解正文后手动更新）。跨会话时不同步就写新章，节奏分析和评分会基于错误的状态做出糟糕的方向选择。

**检测信号**：如果 rhythm 输出的推荐模式为空，或 characters.yaml 中 last_appeared 全是 0，说明状态文件从未被更新过。

---

每一轮循环（写一章）的执行顺序：

### Step 1: 初始化项目

```bash
python3 scripts/auto_write.py init --name "书名" --dir ~/novels/name --mode auto
```

然后手动填充核心 state 文件：
- `novel-project.yaml` — 书名/类型/设定/冲突/目标字数
- `state/characters.yaml` — 初始角色（至少主角 + AI/系统 + 1个协作者 + 1个对手）
- `state/world.yaml` — 地点/势力/能力体系/世界规则
- `state/threads.yaml` — 初始线索（至少2-3条 major）
- `state/emotional-debts.yaml` — 初始情感债
- `state/arc-tracker.yaml` — 弧线起始状态

**创建 GitHub 仓库**（每本小说一个仓库）：
```bash
cd ~/novels/name
git init
gh repo create andy-develop/name --private --source=. --push
```
这样所有章节、状态文件、大纲都有版本控制和远程备份。

### Step 2: 节奏分析

```bash
cd ~/novels/name && python3 scripts/auto_write.py rhythm --latest-chapters 5
```

`--latest-chapters N` 指定分析最近N章的节奏（默认5，建议3-5）。`--dir` 参数可选，默认当前目录——可用 `cd` 进入项目目录后省略。

rhythm 和 score 可以在一条命令中串联执行以节省轮次：
```bash
cd ~/novels/code-epoch && python3 scripts/auto_write.py rhythm --latest-chapters 3 && python3 scripts/auto_write.py score --dir . --d1 "D3,5,4,3,3,5,4,4" --d2 "D6,4,3,3,5,5,3,3"
```

输出：当前阶段 + 推荐发散模式 + 张力检测 + 停滞线索 + 缺席角色

### Step 3: 方向评分

> ⚠️ **第1-2章特殊规则**：当 current_chapter ≤ 2 时，使用 SKILL.md §8.3 的开篇评分权重（翻页驱动35%+钩子强度25%），而非标准权重。详见 `references/scoring-and-selection.md` 的"第1-2章特殊评分规则"。
>
> ⚠️ **第3-10章特殊规则**：当 3 ≤ current_chapter ≤ 10 时，使用早期情绪保护评分约束（翻页驱动25%+情感利用20%），且有额外一票否决条件。详见 `references/scoring-and-selection.md` 的"第3-10章特殊评分规则"。

根据 rhythm 输出的推荐模式，构思 3-5 个候选方向，然后评分：

```bash
python3 scripts/auto_write.py score --dir ~/novels/name \
  --d1 "D7,5,5,3,4,5,4,4" \
  --d2 "D1,3,4,5,3,4,3,3" \
  --d3 "D12,4,3,2,2,5,5,3"
```

格式：`method,rhythm_fit,drive_intensity,thread_advancement,emotional_utilization,consistency_score,novelty,hook_strength`
每项 1-5 分。

**方向融合**：当最高分与次高分差距 < 0.5 时，融合两个方向的亮点通常优于单选。取最高分方向为主轴，从次高分方向抽取1个互补模式。标注格式 "D主+D副1+D副2"，最多融合3个模式。详见 SKILL.md 7.9。

### Step 4: 写章节正文

直接 write_file 到 `chapters/ch{NNN}.md`。

关键要点：
- 每章 2500-4000 字（avg_words_per_chapter ± 20%）
- 章末必须有钩子（5类：悬念/焦虑/认知/情感/好奇，连续2章不可同类型）
- 正文中的情节必须推进至少一条线索或一个角色状态
- 确保不违反 world.yaml 中的 hard 规则
- **叙事纪律（§9.1）**：前300字必须进入剧情；禁止超过200字纯设定段落；主角必须有主动目标
- **断章纪律（§9.2）**：不要在"事情解决了"的地方断章，在"事情正到最关键处"断章；大高潮超过5000字必须分拆为2-3章
- **早期情绪保护（§9.3）**：前10章不虐主——主角不能被剥夺核心能力、无法反击、连续被动

**高潮章节技巧：多视点轮转**。在灵魂合并、天空打开等关键场景，用 `---` 分隔线切换多个角色视角（赵恒远/守望/苏晚晴/王寄北），每人200-400字的独立段落。每个视角的认知水平不同，自然产生认知差张力。这本质是 D6（双线映照）的极致用法——多线同时映照同一事件。

### Step 4.5: 第1-2章冲击力审查（必做⚠️）

> 写完第1章和第2章后，**必须**执行冲击力审查。全部通过才能继续写第3章。

**审查清单**：

```
□ 开篇第一句/第一段是否有冲突/异常/紧迫感？
□ 读者在前300字内能否知道"这人想干什么"？
□ 前500字是否有至少一个"不对劲"的信号？
□ 章末钩子是否足够强——读者是否会"必须翻下一章"？
□ 如果撕掉最后一段，前面的内容是否还能留住读者？（检验内容本身的力量，而非仅靠钩子）
□ 情感锚点——读完后读者是否"在乎"主角的命运？
□ 是否有超过200字的纯设定/世界观说明段落？（判定标准：同时满足"无角色行动+无冲突+作者→读者信息流"的连续文段；不含角色对话中的设定讨论）
□ 张力曲线是否从头到尾单调？（必须至少有一个波峰波谷）
□ 第二章结尾张力是否≥第一章结尾张力？
□ 是否有"认知翻转"——读者在第二章是否发现第一章的理解是错的或不完整的？
```

**第一章死亡模式**（出现任一即重写）：
- ❌ 大段设定介绍（世界观、历史、能力体系说明文）
- ❌ 角色醒来照镜子式开头
- ❌ "一切都很正常"式开篇（正常=无聊）
- ❌ 无冲突的日常描写超过500字
- ❌ 章末无紧迫悬念

**第二章死亡模式**（出现任一即重写）：
- ❌ 退回解释第一章发生了什么
- ❌ 大段世界观补充
- ❌ 危机降温（第一章紧张，第二章突然安全了）
- ❌ 章末张力低于第一章

**审查不通过的处理**：
- 任何一项不通过 → 修改该章节后重新审查
- 连续两次审查不通过 → 重新发散第一章方向，从根源调整

### Step 4.6: 叙事纪律自检（每章必做⚠️）

> 写完每一章后，快速过一遍。与 Step 4.5 的冲击力审查不同，这是**全章通用**的叙事质量检查，适用于第3章到最后一章。

**自检清单**：
```
□ 前300字是否直接进入剧情？有无环境描写/背景回顾/情绪独白开篇？
□ 有无超过200字的纯设定/背景说明段落？（判定：同时满足"无角色行动+无冲突+作者→读者信息流"的连续文段）
□ 主角在本章是否有主动行动或明确的近期目标？
□ 本章内容删掉后，主线是否受损？（不受损=该删）
□ 断章位置是否在"事情正到最关键处"？还是"事情解决了"才断？
□ 如果本章是大高潮的一部分，是否被分拆为2-3章？（超过5000字的高潮必须分拆）
```

**常见问题快速修正**：
- 开篇300字是铺垫 → 直接砍掉，从第一个有动作/冲突的段落开始
- 超过200字的设定段落 → 找到本章中角色"需要用到这个设定"的场景，把设定信息融入对话或行动中
- 主角本章无主动行动 → 检查是否连续被动，超过2章被动必须在下章补上主动事件
- 断章位置太"圆满" → 找到情绪最高点，在那之前断开

### Step 4.7: 早期情绪审查（第10章写完时必做⚠️）

> 仅在 `current_chapter = 10` 时执行。检验前10章是否成功建立了读者对主角的认同。

**审查清单**：
```
□ 主角在前10章中是否有至少3次主动出击？
□ 主角是否遭遇过"无还手之力"的严重打压？（有=不合格，需补章修正或调整情感债）
□ 读者读到第10章时，是"在乎"主角还是"同情"主角？（在乎✅ 同情❌）
□ 主角是否从被动变主动了？（前5章可出现被动适应，但连续被动不超过2章；后5章应越来越主动，主动行动占比≥60%）
□ 前10章的整体情绪走向是否"低开高走"？（应该如此——起点可以有困难，但趋势必须是向上）
□ 是否有至少2个"主角小胜"的时刻？（即使很小——赢得一场对话、解决一个小问题）
□ 是否有超过3章的连续"低气压"无释放？（读者需要间歇性的爽感回报）
```

**审查不通过的处理**：
- 发现虐主问题 → 在第11-12章内安排主角主动反击+阶段性胜利，补偿读者情绪
- 发现主角缺乏能动性 → 在第11章安插主角的明确主动目标，并在12章完成
- 发现情绪持续低气压 → 在第11章安排一个小而确定的胜利（D8伪胜利也行）

### Step 5: 更新状态文件

**必须更新的文件**（每章后）：
- `novel-project.yaml` → current_chapter, current_words
- `state/arc-tracker.yaml` → 添加 recent_patterns 和 recent_hooks 条目

**按需更新的文件**（有变化时）：
- `state/characters.yaml` → 角色位置/状态/能力/关系/物品变化
- `state/threads.yaml` → 线索 planted/developed/resolved
- `state/timeline.yaml` → 重大时间线事件
- `state/world.yaml` → 地点毁灭/势力变化
- `state/emotional-debts.yaml` → 新增/清偿情感债

**批量更新捷径**：当状态落后多章时，用 write_file 全量重写 characters.yaml / threads.yaml 比 patch 逐条更高效且不易出遗漏。arc-tracker 用 patch 追加 recent_patterns/recent_hooks 即可。详见 SKILL.md 7.8 状态同步策略。

**并发 patch 提效**：多个独立的 patch 操作（如 novel-project.yaml + arc-tracker.yaml + threads.yaml + emotional-debts.yaml 对不同文件的更新）可以在同一个 function_calls 块中并发执行，不必串行等待。这大幅减少写作循环的轮次消耗。

**冲刺模式提效**：连续快速生成多章时，进一步优化——① rhythm + score 合并在一条 terminal 命令（`rhythm ... && score ...`）② 每章写完后将 3-4 个文件的 patch 放入同一个 function_calls 块并发 ③ consistency_check 间隔从"每章"放宽到"每 3-5 章或弧线阶段切换时" ④ 角色/线索状态更新频率降为每 2-3 章，但弧线阶段切换时必须全量更新。详见 `references/session-resumption-playbook.md` 场景四。

**进展追踪**：每3-5章输出一次进度汇总表（章号 | 标题 | 阶段 | 张力 | 核心事件），帮助用户快速了解进展和下一方向，也方便跨会话恢复时回顾。卷完结时输出完整汇总表（含阶段/线索/进度/开放问题），模板见 `references/session-resumption-playbook.md` 场景四。

### Step 6: 一致性门控

```bash
python3 scripts/auto_write.py gate --dir ~/novels/name
```

如果触发校验：
```bash
python3 scripts/consistency_checker.py check ~/novels/name   # 轻检
python3 scripts/consistency_checker.py audit ~/novels/name    # 深审
```

如发现错误 → 执行 Module 7.2 的自动修复策略 → 验证修复

### Step 6.5: Git 同步（每章必做⚠️）

> 每个小说项目是一个 GitHub 仓库。每章写完 + 状态更新 + 一致性校验后，自动 commit & push。

```bash
cd ~/novels/name
git add -A
git commit -m "ch{NNN}: {章节标题}"
git push origin main
```

**commit 消息格式**：
- 普通章：`ch001: 午夜来电`
- 卷完结：`ch030: 雷霆一击 [卷1完结]`
- 全书完结：`ch090: 新世界 [全书完结]`
- 纯状态更新（非写章）：`state: 同步characters+threads到ch045`

**注意**：
- commit 时机在 `commit_chapter.py` 之后、下一章开始之前
- 不要在写章中途 commit（章正文+状态更新应是一个原子提交）
- git push 失败不阻塞写作——下一章写完时重试即可

### Step 7: 终止检查

```bash
python3 scripts/auto_write.py terminate --dir ~/novels/name
```

未终止 → 回到 Step 2 继续下一章

## 弧线阶段与发散模式对应

| 阶段 | 推荐模式 | 钩子偏好 |
|------|---------|---------|
| 起势 | D3, D6, D12 | 好奇型、认知型 |
| 升压 | D1, D2, D7, D10, D12 | 焦虑型、悬念型 |
| 假高潮 | D8, D4(局部/结构级) | 认知型为主(揭示翻转)+情感型(释放余波) |
| 二次爬升 | D5, D7, D9, D10, D11 | 焦虑型、悬念型 |
| 真高潮 | D4, D8, D9, D13, D14 | 情感型、悬念型 |
| 落幕 | D6, D13 | 好奇型为主(指向下一弧线)+情感型(余波沉淀) |

> **假高潮的实操节奏**：假高潮不是"写了高潮再否定"——而是"真的给了一个情感回报，但立即揭示回报同时暴露了更深层问题"。例：天空打开了（情感回报）→ 膜开后门开了，门外有新威胁（回报同时暴露）。关键：读者的满足感必须是真实的，否则后续揭示无法构成张力，只会构成失望。假高潮的章数控制在2-3章——第1章情感释放，第2章发现翻转，第3章确认新威胁规模。

## 高效组合速查

| 组合 | 适用场景 |
|------|---------|
| D7+D10 | 最强焦虑——认知差+倒计时 |
| D5+D4 | 规则突变后反转 |
| D9+D13 | 两难中情感爆发 |
| D8+D12 | 伪胜利+暗流涌动 |
| D3+D12 | 禁区探索+不安感 |
| D14+D13 | 渔线拉起+情感回收 |

## 常见问题

**Q: chapter-plan.yaml 什么时候用？**
A: 人机协作模式（模式B）中每次发散后生成。全自动模式（模式A）中可跳过，直接写正文章节。

**Q: 状态更新是脚本还是手动？**
A: 目前是 agent 手动更新（patch/write_file）。auto_write.py 和 novel_state.py 只管初始化和查询，不自动从章节提取事件。事件提取依赖 AI 理解正文内容后更新对应 yaml。

**Q: 一致性门控的轻检间隔怎么调？**
A: 编辑 `automation-config.yaml` 中 `consistency.light_check_interval`，默认3章。高节奏（动作密集弧线）可改2，低节奏可改5。

**Q: 跨会话恢复时发现状态文件严重滞后怎么办？**
A: **先停止写作，用 `ls chapters/` 确认实际章节数**，然后逐一比对每个 state/*.yaml 是否跟上最新章节。重点检查：characters.yaml 的 last_appeared/location/condition，threads.yaml 的 developments 和 resolved 状态，arc-tracker.yaml 的 recent_patterns/hooks，emotional-debts.yaml 的 status。宁可多花5分钟同步，也不要在过期状态上写作——节奏分析和方向评分全部依赖状态文件的准确性。

**Q: threads.yaml 的 developments 字段 patch 报 "Found N matches" 怎么办？**
A: `developments: []` 在 threads.yaml 中出现多次，patch 时必须包含足够上下文使 old_string 唯一。最佳实践：包含相邻的 `importance`、`urgency`、`expected_resolve_by` 字段作为定位锚点。如果条目太相似，考虑用 write_file 重写整个条目。patch 后务必跑 consistency_checker 验证 YAML 未损坏。

**Q: 如何计算中文小说的字数？**
A: 中文字符≈3字节UTF-8，write_file 报告的 bytes_written 不能直接当字数。估算方式：章节数 × avg_words_per_chapter。不要求精确，但不要用字节数除以3——标点、换行、英文术语都会影响比例。

**Q: 从新会话续写时第一步做什么？**
A: 执行 Step 0（会话恢复）——读取 novel-project.yaml 确认进度，检查所有 state 文件是否严重落后 current_chapter，如果是则通读未同步章节、批量更新状态、补齐 arc-tracker，最后用 rhythm 命令确认同步正常。绝不跳过此步直接写作。详细操作步骤和YAML patch碰撞解法见 `references/session-resumption-playbook.md`。

**Q: 如何从"起势"过渡到"升压"？**
A: 在 arc-tracker.yaml 中更新 current_phase。通常在起势5章后、主角获得第一个明确目标和第一个对手时过渡。agent 判断时机，不需要脚本决定。

**Q: score 命令的方向数据格式？**
A: 严格8个字段：`method,rhythm_fit,drive_intensity,thread_advancement,emotional_utilization,consistency_score,novelty,hook_strength`。少于8个会被静默跳过并打印警告。注意 method 不算在7个维度内，所以总共8个逗号分隔值。

**Q: consistency_checker.py 的正确调用方式？**
A: `python3 scripts/consistency_checker.py check <项目目录绝对路径>`（如 `check /root/novels/code-epoch`）。不接受 `--chapter N` 标志，也不接受裸章节数字。它校验整个项目状态一致性而非单章。`audit` 同理：`consistency_checker.py audit <项目目录>`。

**Q: auto_write.py score 的正确调用方式？**
A: `python3 scripts/auto_write.py score --dir <项目目录> --d1 "D3,5,4,3,3,5,4,4" --d2 "D6,4,3,3,5,5,3,3"`。不接受自然语言描述的方向名。`--dir` 是必需参数。

---

## 卷间过渡协议（Volume Transition）

> 当一卷完结、下一卷开始时，不要直接"继续写下一章"。这是叙事的断代，需要结构性调整。

### 何时执行

判定条件（满足任一）：
- 上一卷弧线进入"落幕"阶段且主要线索已收束
- 用户明确说"开始第二卷"或"新一卷"
- arc-tracker 的 current_phase 为"落幕"且 phase_chapters_elapsed ≥ 3

### 执行步骤

```
1. 创建卷大纲
   write_file → outlines/volumeN-outline.md
   内容：核心冲突、关键种子（6个左右）、弧线阶段规划表

2. 重置 arc-tracker.yaml
   current_arc: N
   current_phase: "起势"
   phase_start_chapter: 新首章号
   phase_chapters_elapsed: 0
   保留 recent_patterns（供参考），清空过期 hooks

3. 封卷旧线索（threads.yaml）
   已收束线索精简为：id + description + resolved_chapter + status: resolved
   仍在活跃的线索保持完整，改 urgency + expected_resolve_by

4. 播种新线索（threads.yaml）
   至少6条新线索：1-2条核心主线 + 2-3条暗线 + 1条希望/情感线
   旧卷未收束线索延续到新卷

5. 演化角色状态（characters.yaml）
   全量重写：location/condition/abilities/relationships/key_traits/secrets
   角色在卷间成长必须体现。新增角色填完整档案

6. 重写情感债（emotional-debts.yaml）
   用 `write_file` 全量重写——与 characters.yaml 同理，卷间变化太大不适合 patch
   每卷至少2条新情感债。E001类未清偿核心债跨卷延续并可能升权
   旧债标记 paid/partially_paid，跨卷延续的债更新 description 反映新卷语境

7. 更新 novel-project.yaml
   current_volume, volume_title, premise, core_conflict 更新

8. 一致性确认
   consistency_checker.py check 确保零冲突再开始
```

### 实操要点

- 卷间过渡最适合 `write_file` 全量重写（characters/threads/arc-tracker/emotional-debts），因为变化太大。**emotional-debts.yaml 也要全量重写**——不是增量添加，因为旧债的 status/description/payback_condition 都需要在新卷语境下重新评估
- 旧卷 resolved 线索不要删除，保留精简版供跨卷引用
- recent_patterns 在卷间过渡时只保留最近1-2条作为参考，不要带着整个旧卷的 patterns 进入新卷——否则 rhythm 计算会被旧数据干扰
- 新卷起势前2章张力从 3-4 起步（不要从1——读者已有旧卷投资），第3章升到 5-6
- **有机冲刺模式**：当卷大纲（volume outline）足够详细（含6大种子+弧线阶段表），AI 可以跳过 CLI rhythm/score 命令，直接根据大纲和当前弧线位置有机选择方向。这在连续快速生成多章时特别有效——省掉每次 rhythm+score 的终端调用，直接由 AI 的叙事判断驱动。关键前提：大纲必须明确每个弧线阶段的核心事件和张力量级。4-5章后即使在大纲驱动下也应跑一次 consistency_check 确认
