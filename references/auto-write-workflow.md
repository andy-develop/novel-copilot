# 自动写作循环实操工作流

> 基于《代码纪元》10 章实际写作的验证记录

## 完整循环（每章执行）

```bash
# 1. 节奏分析
python3 scripts/auto_write.py rhythm --dir <项目目录>

# 2. AI 发散 + 评分（AI 心算7维分数后编码）
python3 scripts/auto_write.py score --dir <项目目录> \
  --d1 "D7+D10,5,5,4,4,3,5,5" \
  --d2 "D1,4,4,5,3,4,4,3" \
  --d3 "D8,3,5,3,5,3,3,5"

# 3. AI 选择方向 + 写章节正文
# --> write_file: chapters/chXXX.md

# 4. 更新项目元数据（章数/字数）
# --> patch: novel-project.yaml (current_chapter, current_words)

# 5. 更新弧线追踪（必须每章更新！）
# --> write_file: state/arc-tracker.yaml

# 6. 一致性门控判断
python3 scripts/auto_write.py gate --dir <项目目录>

# 7. 如触发，执行校验
python3 scripts/consistency_checker.py check <项目目录>
```

## 章节进度和检查点节奏

| 章节范围 | 弧线阶段 | 弧线追踪 current_phase | 建议 |
|----------|----------|----------------------|------|
| 1-4 | 起势 | `起势` | D3/D6/D12 为主，建立世界观和角色 |
| 5-6 | 升压前期 | `升压` | 引入 D7/D10 增加焦虑，倒计时启动 |
| 7-8 | 升压后期 | `升压` | D1 线索咬合，关键信息揭示 |
| 9-10 | 假高潮 | `假高潮` | D8 伪胜利——表面成功但危机暗藏 |
| 11-14 | 二次爬升 | `二次爬升` | D5/D9 规则突变+两难，真正的对抗 |
| 15-17 | 真高潮 | `真高潮` | D4/D9/D13 反转+抉择+情感回收 |
| 18-20 | 落幕 | `落幕` | D6/D13 余波+新悬念种子 |

## arc-tracker.yaml 维护规范

每章写完后必须更新以下字段：

```yaml
current_arc: N                    # 当前弧线编号
current_phase: "升压"              # 必须与 automation-config.yaml 的键匹配！
phase_start_chapter: N            # 当前阶段起始章
phase_chapters_elapsed: N         # 当前阶段已过章数
recent_patterns:                  # 保持最近5章
  - method: "D7+D10"             # 发散模式组合
    tension: 8                    # 张力值1-10
    chapter: N
recent_hooks:                     # 保持最近5章
  - type: "焦虑型"                # 钩子类型
    chapter: N
    content: "一句话摘要"
```

**命名约束**：`current_phase` 的值必须是 `automation-config.yaml` 中 `arc_phases` 的键之一，否则 `rhythm` 命令返回空的推荐列表。有效值：`起势`、`升压`、`假高潮`、`二次爬升`、`真高潮`、`落幕`。

## 状态回写时机

全自动模式中 AI 不会自动回写角色/线索/情感债状态。建议在以下节点强制回写：

- **每5章**：提取最近5章中的角色变化、线索推进、情感债变化，批量更新 yaml
- **弧线阶段切换**：从"升压"进入"假高潮"时，全面更新状态
- **深度审查点（每10章）**：运行 `consistency_checker.py audit`，同时做完整状态回写
