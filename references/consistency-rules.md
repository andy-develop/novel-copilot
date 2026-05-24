# 逻辑一致性规则手册

## 🔴 硬冲突（绝对不可出现）

### R1: 死者行动
- `status=dead` 且 `is_truly_dead=true` 的角色不可有任何行动/对话
- **例外**：回忆、幻觉、梦境、他人转述——必须明确标注非实时
- **校验方式**：扫描新章节中出现的所有角色名/别名，与 characters.yaml 的 status 交叉检查

### R2: 世界规则违反
- `severity=hard` 的规则不可在任何情况下违反
- 除非在 `rules.yaml` 的 `special_cases` 中预先声明
- **校验方式**：每条 hard 规则编写对应的检查逻辑

### R3: 物品双重持有
- 同一物品不能同时出现在两个角色的 inventory 中
- 物品转移必须在 `inventory_history` 中记录
- **校验方式**：扫描所有角色的 inventory，检查 item_id 重复

### R4: 地理瞬移
- 角色位置变化必须符合距离/时间规则
- `distance_to` 中的时间是最短用时，实际只能更长
- **例外**：传送阵、飞行（需有对应能力）、空间法术
- **校验方式**：比较角色 `last_appeared` 章节的位置与当前位置

## 🟡 软警告（需要合理解释）

### W1: 遗忘伏笔
- `importance=major` 且 `planted_chapter` 距当前章节超过 30 章
- `planted` 但从未 `developments` 推进
- **建议**：在近期章节中给予线索一个推进（哪怕是小进展）

### W2: 角色长期缺席
- 角色最后出场距当前超过 20 章，但并无"离开/失踪"设定
- **建议**：安排一个提及或短暂出场，保持存在感

### W3: 修为暴涨
- 修为增长违反 `power_system.rules` 中的正常速度
- **需要**：给出特殊际遇/奇遇/机缘的合理理由

### W4: 性格偏移
- 角色行为与 `key_traits` 矛盾
- **需要**：有充分的事件驱动角色转变（不能凭空变性格）

### W5: 势力空转
- 加入势力的角色长期无势力相关事件
- **建议**：安排势力内部互动

## 🟢 提示建议

### S1: 钩子检查
- 上一章结尾的 hook 是否在本章得到了回应？

### S2: POV 一致性
- 本章视角角色不知道的信息不能出现在叙事中
- 除非明确切换视角

### S3: 闭环检查
- 每个场景应有入有出，角色不应无故消失

## 冲突处理优先级

1. 硬冲突 → 必须修改，不可绕过
2. 软警告 → 可选择修改或补充理由
3. 提示建议 → 仅供参考，可忽略

---

## 覆盖率现状与增强路线

> 完整 70 项分类见 `references/logic-consistency-taxonomy.md`

### 当前覆盖：15/70（21%）

已覆盖项：
- **角色层**：C1死者行动、C3能力矛盾、C5关系矛盾、C9角色膨胀
- **信息层**：I1视角泄漏
- **时间层**：T1地理瞬移
- **物理层**：P1物品双重持有
- **社会层**：S1势力矛盾
- **叙事层**：N1视角泄漏、N6场景断裂
- **世界规则层**：W1超自然体系矛盾、W3规则例外无据、W5地理矛盾
- **结构层**：St4伏笔烂尾、St7悬钩未兑现

### 最大盲区（0%覆盖）

- **因果层**（Ca1-Ca6）：全部未覆盖——因果链断裂、事件效果消失、反向因果、机械降神等
- **情感/动机层**（E1-E7）：全部未覆盖——动机缺失、情感转变跳步、价值观矛盾等

### 三层增强路线

| 层次 | 覆盖目标 | 方式 | 优先问题 |
|------|---------|------|---------|
| **第一层** | 15→30 (43%) | 加字段+检查函数（与R1-R4同构） | P2伤害、I2信息传播、Ca5反向因果、T4年龄、C4背景 |
| **第二层** | 30→52 (74%) | 结构化圈可疑点+LLM判断 | C8心理断裂、Ca3事件效果、E3情感遗忘、E5价值观 |
| **第三层** | 52→70 (100%) | LLM章节级语义审查 | E1动机缺失、Ca4连锁反应、N3风格不统一等 |

### 第一层待加字段清单

```yaml
# characters.yaml 新增
physical_traits: [{trait, description, chapter_established}]  # C2 外貌矛盾
backstory_facts: [key_facts]                                  # C4 背景矛盾
injuries: [{type, chapter, recovery_chapters, status}]        # P2 伤害持续
birth_year: null                                              # T4 年龄计算
knowledge: [{event_id, since_chapter, source}]                # I2/I3 信息传播
emotional_state: {current, since_chapter, cause}              # C8 心理状态

# novel-project.yaml 或独立 state/events.yaml 新增
major_events: [{event, chapter, expected_effects, resolved}]  # Ca3 事件效果
backstory_claims: [{fact, chapter_claimed, conflicts_with}]   # Ca5 反向因果

# threads.yaml secrets 增强
clearance_level: restricted                                    # I4 保密等级
known_by: [character_ids]                                     # I4 知情者列表

# timeline.yaml 增强
storyline: ""                                                 # St1/T2 多线对齐
```
