# 自动写作实操陷阱与状态同步策略

> 从 SKILL.md §7.7、§7.8 提取的详细参考内容。以下来自 v2.0 的实际写作验证——设计时想的和实际跑的差距很大。

---

## 7.7 自动写作实操须知

**核心事实：AI 是整个循环的编排者，脚本只是决策辅助。**

自动写作循环不是 `auto_write.py` 驱动的——脚本是**查询工具**，AI agent 才是循环引擎。实际流程是：

```
AI 每章循环:
1. terminal: rhythm → 获取当前节奏推荐
2. AI 发散 → 生成候选方向 + 心算评分
3. terminal: score → 评分验证（AI 把心算分数编码为 CLI 参数）
4. AI 选定方向 → 直接写章节正文（不经过 chapter-plan.yaml）
5. patch/write_file: 更新 novel-project.yaml（章数/字数）
6. write_file: 更新 arc-tracker.yaml（阶段/模式/钩子）
7. terminal: gate → 判断是否触发一致性校验
8. terminal: consistency_checker → 如触发则执行
9. 继续下一章
```

**实操陷阱**：

| 陷阱 | 描述 | 解决 |
|------|------|------|
| chapter-plan.yaml 跳过 | 实际写作中 AI 从方向选择直接跳到正文，不写 chapter-plan.yaml。多一步中间文件反而拖慢节奏 | 可接受。chapter-plan 是半自动模式的产物，全自动模式中 AI 自带规划能力 |
| 评分是 AI 心算 | `score` 命令的输入是 AI 自己编排的——AI 先用叙事上下文判断7维分数，再编码为逗号分隔参数。脚本只做加权求和和排雷 | 这是正确用法。评分公式统一权重，排雷规则自动化——人工部分是AI的优势 |
| arc-tracker 需每章更新 | 弧线追踪、近期模式、钩子类型必须每章手动更新，否则 rhythm 命令的推荐会退化为空 | **每章写完后必须更新 arc-tracker.yaml**，这是最容易被遗漏的步骤 |
| 状态文件（characters/threads/emotional-debts）不会自动更新 | 10章写完后 characters.yaml 和 threads.yaml 仍停留在第一章的状态——AI 写正文但没有回写状态变动 | 全自动模式中应在每5章或弧线阶段切换时强制做一次状态提取+回写 |
| consistency_checker 对空状态文件报全绿 | 初始模板只有 example 角色，checker 报"未发现冲突"但实际是因为状态文件里没写东西 | 写完初始设定后先跑一次 check 确认数据有意义 |
| rhythm 命令对自定义阶段名返回空 | 如果 arc-tracker 的 current_phase 不在 automation-config.yaml 的 arc_phases 字典里（如"起势→升压过渡"），推荐模式列表为空 | 阶段命名必须与 automation-config.yaml 的 arc_phases 键严格匹配 |
| 写作速度瓶颈 | 每章 3000-4000 字的正文生成是最耗时的环节，脚本查询几乎零耗时 | 这是预期行为。创意写作本身不可自动化，脚本的价值在于结构化决策 |
| 跨会话状态漂移 | 上一个会话写了10章但没做最终状态回写，下一个会话恢复时状态文件还停在第1章 | **每个会话结束前必须强制做一次完整状态同步**（角色/线索/情感债/时间线/弧线追踪）。新会话开始时也要先验证状态文件与实际章节数一致再开始写作 |
| YAML patching developments字段 | threads.yaml中多个条目有相同的`developments: []`，patch时old_string不够唯一会报"Found N matches" | 必须包含足够的上下文（如相邻的`importance`、`urgency`、`expected_resolve_by`字段）使old_string唯一。或改用完整条目重写策略 |
| YAML缩进断裂 | patch在`planted_context`后直接插入列表项但漏了`developments:`键，导致YAML解析失败 | patch后立即用consistency_checker验证；如果YAML解析失败，先read_file定位错误行号再修复。列表项必须出现在其父键之下 |
| 中文小说字数统计 | write_file写入中文字符后byte数远大于字数，current_words无法通过文件大小验证 | current_words用中文字符数（约等于章节数×avg_words_per_chapter），不要求精确。中文字符≈3字节UTF-8 |
| 跨会话状态全面漂移 | 会话重置后，characters/threads/arc-tracker 可能落后 current_chapter 多章（如10章写完但状态停在1章）| 进入写作循环前必须执行 Step 0 会话恢复；落后>3章时用 write_file 全量重写状态文件比逐条 patch 更高效 |
| YAML patch 碰撞 | threads.yaml 中 `developments: []` 等通用字段在多条线索中重复出现，patch 仅凭 `old_string` 无法唯一定位 | patch 时附带前后2-3行的上下文（如 id 行或 description 开头），确保 old_string 在文件中唯一 |
| resolved 字段残留 | 用 patch 替换 developments 内容后，旧线索底部的 `resolved_chapter: null` / `resolved_how: null` 可能未被替换，导致同一线索同时有新旧两套 resolved 字段 | 替换 resolved 值时把整个 `resolved_chapter` + `resolved_how` 块一起替换，或在 patch 后 read_file 目视检查重复字段 |
| 节奏建议"插缓冲"但故事在悬崖上 | rhythm 输出说"连续N章高张力建议缓冲"，但如果上一章末是27分钟倒计时之类的硬悬念，强行缓冲会让读者断裂 | 缓冲≠降温——切换视角/双线/暗流涌动(D12)可以在保持悬念的同时给张力换一种形式。用 D6+D12 或 D12+D13 做"暴风眼中的喘息" |
| consistency_checker CLI 参数 | `consistency_checker.py` 不接受 `--chapter N` 或裸数字做参数。尝试 `check --chapter 19`、`check 19` 均报错 | 正确用法：`consistency_checker.py check <项目目录绝对路径>`（如 `check /root/novels/code-epoch`）。它校验的是整个项目的状态一致性，不针对单章。`audit` 同理：`consistency_checker.py audit <项目目录>` |
| auto_write.py score CLI 格式 | score 不接受自然语言描述的方向名（如 `--directions "D3正常推进天空"`） | 正确格式：`auto_write.py score --dir <项目目录> --d1 "D3,5,4,3,3,5,4,4" --d2 "D6,4,3,3,5,5,3,3"`。每项 = 发散模式,节奏适配,驱动强度,线索推进,情感利用,一致性安全,新颖度,钩子强度（共8项逗号分隔，7维评分各1-5） |
| 阶段切换忘重置 chapters_elapsed | 从二次爬升→真高潮时更新了 current_phase 和 phase_start_chapter，但忘把 phase_chapters_elapsed 归 1 | 每次弧线阶段切换的三项必须一起改：current_phase、phase_start_chapter=新章节号、phase_chapters_elapsed=1 |
| YAML patch 缩进断裂（列表项） | patch 替换 `- id: aegis` 时 new_string 前缀用了4空格缩进（`    - id:`）导致 YAML 解析为嵌套列表而非顶层列表项 | YAML 列表项的 `- ` 必须与同级的其他列表项缩进一致。characters.yaml 和 emotional-debts.yaml 的顶层列表项用2空格缩进（`  - id:`）。patch 前先 read_file 查看相邻行的缩进级别，patch 后必须用 consistency_checker 验证 YAML 完整性 |
| 方向融合比单选更有效 | 实操中最高分和次高分差距常 <0.15，单选不如融合 | 取最高分方向的主模式 + 次高分方向1个互补模式，标注 "D主+D副"。融合方向在二次爬升和真高潮阶段尤其有效——复杂叙事需要多驱动 |
| 软告警"逾期待收束"可能是误报 | consistency_checker 报线索"超过预期收束章节"，但某些"线索"只是场景/设定（如荒地、外墙），不需要主动收束 | 在 threads.yaml 中，区分「事件型线索」（需要 planted→developed→resolved 完整弧线）和「设定型线索」（仅作世界观补充，resolved_chapter 可设为 null）。设定型线索的 urgency 应设 low 或备注 `type: setting` |
| 线索描述要及时更新 | threads.yaml 的 description 字段仍停留在最初种下时的措辞，但线索已发生重大转折，导致 context compaction 后 AI 根据 description 误判线索当前状态 | **每5章或线索发生重大转折时，更新 description 字段反映当前状态**（如"T015: 7.83Hz SOS"→"T015: 晨觉醒降级完成+1.7Hz=维度心跳"）。developments 太长时也需精简——只保留最近3-4个关键转折，删除早期琐碎条目 |
| 卷间 characters.yaml 必须全量重写 | 卷间过渡时角色位置/状态/能力/关系全面变化，用 patch 逐条更新极易遗漏或产生缩进错误 | 卷间过渡时用 `write_file` 全量重写 characters.yaml，不要 patch。这是卷间过渡协议中"演化角色状态"步骤的正确执行方式 |
| 卷内5章强制同步characters+debts | 有机冲刺中逐章 patch threads/arc-tracker 但 characters 和 emotional-debts 容易被遗忘——它们的变化较慢但积累后偏差很大 | 每5章强制 patch 更新 characters.yaml 的 condition_note/abilities/power_level 和 emotional-debts.yaml 的 status/paid_amount。在 consistency_check（每3章）之后顺带做5章同步最省力 |
| 频率/设定体系需要专门追踪 | 长篇中常出现体系化的设定（如频率谱、能力等级、组织架构），散落在各章正文中，跨会话恢复时极难完整回忆 | 在 world.yaml 或专门的 references 文件中维护设定体系速查表。格式：频率→含义→首次出现章→持有者。每卷完结时更新一次 |
| 连续冲刺模式下节奏控制 | 用户说"继续"后连续写5+章，逐章跑 consistency_check 太慢 | **冲刺模式**：① rhythm+score 合并在一条 terminal 命令中 ② 写完章节后将 3-4 个独立文件的 patch 放在同一个 function_calls 块并发执行 ③ consistency_check 间隔可放宽到每 3-5 章一次（非每章）④ 每卷完结时输出进度汇总表 |
| 有机冲刺模式（大纲驱动） | 卷大纲足够详细时，逐章跑 rhythm+score CLI 是不必要的开销 | 当 volume outline 含6大种子+弧线阶段表时，AI 可跳过 CLI 直接有机选择方向。详见 §7.10 和 `references/volume-outline-guide.md` |
| 上下文压缩后恢复 | 会话过长触发的 context compaction 会把早期对话压缩为摘要，但摘要包含完整的状态信息（进度/阶段/线索/角色）| 依赖 compaction 摘要中的"Active State"和"Key Decisions"恢复上下文，然后验证 state/*.yaml 文件与摘要一致。如果 compaction 摘要是唯一来源且与 yaml 文件有冲突，以 yaml 文件为准——它们是 ground truth |
| 跨会话状态漂移 | 新会话中"继续"写作时，状态文件可能比 novel-project 中的 current_chapter 落后5+章——arc-tracker 停在旧阶段、characters 的 last_appeared 全是 0、threads 的 developments 为空 | **必须先执行 Step 0 会话恢复**：通读未同步的章节→提取事件→批量更新 yaml→确认 rhythm 正常，再进入写作循环。跳过此步会导致节奏分析和方向评分基于错误状态 |
| 方向融合实操 | score 命令输出建议"合并 TOP2"时，AI 需要手动构思融合方向——脚本不生成融合方案 | 融合策略：取 TOP1 的核心驱动 + TOP2 的情感/线索维度，构成一个复合模式标签（如 D11+D5+D9），在 arc-tracker 的 recent_patterns 中记录完整复合标签 |

---

## 7.8 状态同步策略（跨会话必读）

> 状态过期是全自动写作的头号问题。AI 写正文时不回写状态——这是设计限制。以下策略来自实战验证。

**会话恢复（每次新会话续写时必须执行）**：

详见 `references/auto-writing-execution-protocol.md` 的 Step 0。核心流程：读 novel-project.yaml → 检查所有 state 文件是否落后 current_chapter → 如落后则通读未同步章节 → 批量更新 → rhythm 确认同步正常。**绝不跳过此步直接写作。**

**过期检测信号**：
- characters.yaml 中 `last_appeared` 全是 0 或差距 > 5章
- threads.yaml 中 developments 数组为空或最近条目 < current_chapter - 5
- arc-tracker.yaml 的 recent_patterns 最新条目 < current_chapter - 2
- emotional-debts.yaml 只有初始条目没有新条目
- rhythm 输出推荐模式为空（current_phase 不匹配的信号）

**高频更新 vs 批量更新**：

| 文件 | 更新频率 | 说明 |
|------|---------|------|
| novel-project.yaml | 每章 | 必须同步章数和字数 |
| arc-tracker.yaml | 每章 | 必须同步模式/钩子/阶段 |
| characters.yaml | 每2-3章或角色状态剧变时 | 位置/状态/关系变化；每5章强制全量回写 |
| threads.yaml | 每章（developments追加）或每3章批量 | 关键线索推进立即追加；每5章强制检查覆盖 |
| emotional-debts.yaml | 每5章或新情感债产生时 | 比角色/线索低频但不可忽略 |
| timeline.yaml | 每章（重大事件） | 地点毁灭、角色死亡、势力剧变必须即时 |

**批量更新模板**：当状态落后 N 章时，通读 N 章内容后一次性执行：
1. write_file characters.yaml 全量更新（比 patch 逐条更可靠）
2. patch threads.yaml 追加 developments 条目
3. patch arc-tracker.yaml 补齐 recent_patterns 和 recent_hooks
4. patch emotional-debts.yaml 追加新债/更新已付
5. 一致性检查确认数据有意义
