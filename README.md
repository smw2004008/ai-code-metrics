# Git AI 代码贡献度分析器

一个用于本地演示的 Python 命令行工具。它读取 Git 提交历史与 diff 统计，按提交 trailer `AI-Assisted: yes` 标记 AI 辅助提交，并输出提交数、增删行数、AI 辅助变更行数及占比。

## 统计口径

- AI 辅助变更行数 = 被标记为 `AI-Assisted: yes` 的提交中新增行数。
- AI 辅助代码占比 = AI 辅助新增行数 / 全部新增行数。
- 这是基于提交自我标记的“AI 辅助变更”估算，不等同于逐行识别 AI 生成代码。一个提交同时包含人工和 AI 修改时，当前版本会将该提交全部新增行计入 AI 辅助部分；报告会明确提示这一限制。
- 二进制文件和重命名只按 Git `--numstat` 返回的行数统计；无法计行的二进制变更不会进入行数分母。

## 使用

需要 Python 3.9+ 和 Git。无需安装第三方依赖。

```bash
python ai_code_metrics.py --repo . --since "30 days ago" --format text
python ai_code_metrics.py --repo . --since 2026-01-01 --until 2026-02-01 --format json
```

标记 AI 辅助提交：

```bash
git commit -m "feat: add parser" -m "AI-Assisted: yes"
```

也可给已有提交追加 Git note（默认读取 `refs/notes/ai-assisted`）：

```bash
git notes --ref=ai-assisted add -m "AI-Assisted: yes" <commit>
```

在协作仓库中需按团队约定同步 notes，例如 `git push origin refs/notes/ai-assisted`。提交 trailer 与 notes 至少使用一种一致的标记方式。

## 输出字段

文本和 JSON 均包含仓库路径、时间范围、提交数、总新增/删除行数、AI 辅助提交数、AI 辅助新增/删除行数、占比及口径说明。合并提交默认排除，避免重复计算合并带来的变更。

## 面试时可以讨论的改进

1. 增加 IDE/Agent 埋点或 PR 元数据，减少依赖人工标记。
2. 对混合提交按文件或 diff hunk 标注，降低整次提交归类带来的误差。
3. 对接 CI 定期采集指标，并按仓库、团队、语言生成看板。
4. 处理 cherry-pick、rebase、notes 同步及重复提交等边界场景。
