# 会话恢复与连续写作操作手册

> 从"继续"到下一章完成的完整操作序列，含常见踩点。

## 场景一：跨会话续写（用户说"继续"）

### 1. 诊断状态漂移

```bash
# 读取进度
cat ~/novels/NAME/novel-project.yaml | grep current_chapter

# 检查 arc-tracker 完整性
cat ~/novels/NAME/state/arc-tracker.yaml

# 快速检查 characters 是否过期（last_appeared << current_chapter？）
grep last_appeared ~/novels/NAME/state/characters.yaml
```

**漂移判断标准**：
- `characters.yaml` 中 `last_appeared` 全部 ≤上次同步章节 → 全量重写
- `threads.yaml` 中 `developments` 为空 → 全量重写
- `arc-tracker.yaml` 中 `recent_patterns` 末尾章节 < `current_chapter-1` → patch 补齐
- 漂移 ≤3 章 → patch 逐条更新
- 漂移 >3 章 → write_file 全量重写更高效

### 2. 全量重写状态文件的顺序

1. **novel-project.yaml** — 更新 current_chapter, current_words
2. **characters.yaml** — 全量重写（加入所有新角色，更新位置/状态/能力/关系）
3. **threads.yaml** — 全量重写（加入新线索，补 developments，更新 resolved）
4. **emotional-debts.yaml** — 全量重写（新增/部分清偿/完全清偿）
5. **arc-tracker.yaml** — patch 追加 recent_patterns + recent_hooks（+更新 current_phase 如已切换）

### 3. 写完后一次性 patch arc-tracker

```
patch arc-tracker: 追加 recent_patterns 条目
patch arc-tracker: 追加 recent_hooks 条目
patch arc-tracker: 更新 phase_chapters_elapsed
```

### 4. 验证

```bash
python3 scripts/auto_write.py rhythm --dir ~/novels/NAME
# 确认输出有推荐模式（非空）且阶段正确
```

## 场景二：同会话连续写作（章→章循环）

每章完成后的标准操作序列（5步）：

```
1. patch novel-project.yaml (current_chapter, current_words)
2. patch arc-tracker.yaml (追加 recent_patterns + recent_hooks + phase_chapters_elapsed++)
3. 按需 patch characters/threads/emotional-debts
4. gate → check/audit（如触发）
5. rhythm → score → 写下一章
```

**省力技巧**：
- steps 3 中角色位置/状态更新用 patch（通常只改 2-3 个角色）
- 新增角色时用 patch 在 characters 列表末尾追加
- 线索推进用 patch，只改 developments 数组和相关字段
- 新线索用 patch 在 threads 列表末尾追加
- 弧线阶段切换：三项一起改（current_phase + phase_start_chapter + phase_chapters_elapsed=1）

## 常见 YAML patch 碰撞及解法

| 碰撞字段 | 出现位置 | 解法 |
|-----------|----------|------|
| `developments: []` | 每条线索都有 | 附带线索 id 行做上下文 |
| `resolved_chapter: null` | 每条未完成线索 | 附带 importance 行做上下文 |
| `relationships: []` | 每个角色 | 用角色 id 行做上下文 |
| `last_appeared: N` | 每个角色 | 用角色 id 或 name 行做上下文 |

**通用原则**：patch 的 old_string 必须包含一个在整个文件中唯一的锚点行（通常是 `id:` 行），然后扩展到需要替换的范围。

## 方向融合实操

当 score 输出建议合并 TOP2（差距 <0.5）时：

1. 取 #1 方向的主模式
2. 从 #2 方向抽取1个互补模式（不同类型的——如果#1是认知型，#2选情感型）
3. 必要时从 #3 再抽1个（最多3模式融合）
4. 标注示例：`D5+D9+D11`（规则突变+两难抉择+逆风孤战）
5. 在章节正文中让3个模式依次或交织出现，不要机械地各占1/3

**融合效果**：在二次爬升和真高潮阶段，融合方向比单选产生更丰富的叙事层次。单模式方向容易产生"一种调子连奏"的感觉。

## 场景三：上下文压缩后恢复

> 会话过长时 Hermes 会自动压缩早期对话为摘要。摘要保留了 Active State / Key Decisions / Completed Actions 等关键信息，但不是逐字记录。

### 恢复步骤

1. **阅读 compaction 摘要**中的 Active Task + Active State + Key Decisions 区域
2. **验证 ground truth**：`read_file` 关键 yaml 文件（novel-project.yaml、arc-tracker.yaml），比对摘要中的章数/阶段/字数
3. **如一致**：直接进入写作循环（摘要已经包含足够上下文）
4. **如不一致**：以 yaml 文件为准，用 会话恢复 场景一的流程重新同步
5. **丢失的上下文**：角色对话语气、用户偏好、临时决策可能被压缩丢失——通过 `session_search` 查找原始对话补充

### 特别注意

- compaction 摘要中的"Completed Actions"列表可能被截断，只保留最近的 N 项
- 摘要中的字数/章数是快照，可能比 yaml 文件旧——始终以 yaml 为准
- 如果摘要提到"用户尚未回应"某个问题，不要重新提问——用户的新消息"继续"已经是回应

## 场景四：连续冲刺模式（5+ 章快速生成）

> 用户说"继续"且不干预时，可以进入冲刺模式——最大化每轮工具调用的产出。

### 冲刺模式优化

| 环节 | 常规模式 | 冲刺模式 |
|------|---------|---------|
| rhythm + score | 分两步执行 | 合并在一条 `terminal` 命令中（`&&` 串联） |
| 状态文件更新 | 逐个 patch 串行 | 同一 `function_calls` 块中 3-4 个文件并发 patch |
| consistency_check | 每章执行 | 每 3-5 章执行一次（或弧线阶段切换时执行） |
| 进度汇报 | 每章输出 | 每卷完结时输出汇总表 |
| 卷间过渡 | 单独会话 | 同一冲刺内完成（写完落幕→立即过渡→写起新卷） |

**冲刺模式内的卷间过渡**：用户说"继续"且当前卷已落幕时，不需要暂停——在同一冲刺流中执行完整的卷间过渡协议（大纲→全量重写状态→一致性确认），然后直接开始新卷第一章。过渡本身约需 3-4 轮工具调用（write_file 大纲 + write_file characters/threads/emotional-debts/arc-tracker + patch novel-project + consistency_check），完成后立即进入 rhythm+score 循环。

### 冲刺模式中的状态文件优先级

每章必须更新（不允许跳过）：
- `novel-project.yaml` — current_chapter / current_words
- `arc-tracker.yaml` — recent_patterns / phase / elapsed

每 2-3 章更新（或剧情剧变时即时更新）：
- `threads.yaml` — major 线索 developments + resolved
- `characters.yaml` — 位置/状态/能力变化

每 5 章或弧线阶段切换时更新：
- `emotional-debts.yaml`
- `world.yaml`（如有变化）

### 卷完成输出模板

每卷完结时，输出以下汇总表帮助用户回顾和跨会话恢复：

```
**📊 第N卷《标题》完成！🎉**

| 阶段 | 章节 | 核心事件 |
|------|------|----------|
| 起势 | chX-Y | ... |
| 升压 | chX-Y | ... |
| ... | ... | ... |

**🔑 核心发现/揭示：**
- ...

**📈 进度：** X章 / ~X字 / 目标X字（X%）

**🔓 开放线索（下一卷需推进）：**
- T0xx: ...
```

## 节奏缓冲的正确理解

rhythm 输出"建议插入1章缓冲"**不等于"降温或加水"**。正确理解：

| 错误理解 | 正确理解 |
|----------|----------|
| 降低张力，加无关描写 | 换张力的形式：从焦虑型→认知型/情感型 |
| 停止主线推进 | 推进暗线/配角视角/世界观揭示 |
| 让读者"休息" | 给读者"消化"——把已爆发的信息用角色反应、世界观拓展来沉淀 |

**适合"缓冲"章的高效模式**：
- D6+D12：双线映照+暗流涌动（视角转换，不降张力）
- D12+D13：暗流涌动+情感债回收（深沉但持续推进）
- D6+D13：双线映照+情感债回收（情感沉淀）

## 一致性检查器的已知无害告警

consistency_checker 的 `S_性格锚点` 告警（"角色 X 缺少 key_traits 设定"）在全自动写作中几乎每次都会出现——因为 auto-write 循环优先更新 action/location/condition/abilities，很少回填 key_traits。这些告警是🟢级（仅供参考），不影响逻辑一致性。如需消除，在每卷过渡时的 characters.yaml 全量重写中补充 key_traits 字段即可（每个角色 3-5 个性格关键词），但非必要。
