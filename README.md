# Git AI 代码贡献度分析器

一个用于本地演示的 Python 命令行工具。它读取 Git 提交历史与 diff 统计，按提交 trailer `AI-Assisted: yes` 标记 AI 辅助提交，并输出代码文件的增删行数、AI 辅助代码变更行数及占比，同时列出纳入统计的文件明细。

## 统计口径

- 仅统计常见源代码扩展名（如 `.py`、`.js`、`.java`、`.go`、`.cpp`、`.sql`）；README、图片及其他非代码文件不计入代码行数。
- AI 辅助代码变更行数 = 被标记为 `AI-Assisted: yes` 的提交中，代码文件的新增行数。
- AI 辅助代码占比 = AI 辅助代码新增行数 / 全部代码新增行数。
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

也可以标记使用的 AI 编码工具，报告会按工具汇总辅助代码新增行数：

```bash
git commit -m "feat: add parser" -m "AI-Assisted: yes" -m "AI-Tool: Codex"
```

工具名由提交者填写，例如 `Codex`、`Claude Code`、`Cursor` 或内部工具名。没有工具标签的 AI 辅助提交会归入“未注明”。工具名来自提交 trailer 或 `refs/notes/ai-tool`，程序不会自动推断。

已有提交也可以用单独的 Git notes ref 标记工具：

```bash
git notes --ref=ai-tool add -m "AI-Tool: Codex" <commit>
```

也可给已有提交追加 Git note（默认读取 `refs/notes/ai-assisted`）：

```bash
git notes --ref=ai-assisted add -m "AI-Assisted: yes" <commit>
```

在协作仓库中需按团队约定同步 notes，例如 `git push origin refs/notes/ai-assisted`。提交 trailer 与 notes 至少使用一种一致的标记方式。

## 输出字段

文本和 JSON 均包含仓库路径、时间范围、提交数、代码文件总新增/删除行数、AI 辅助提交数、AI 辅助新增/删除行数、占比、按文件汇总的变更明细及口径说明。合并提交默认排除，避免重复计算合并带来的变更。

## 面试时可以讨论的改进

1. 增加 IDE/Agent 埋点或 PR 元数据，减少依赖人工标记。
2. 对混合提交按文件或 diff hunk 标注，降低整次提交归类带来的误差。
3. 对接 CI 定期采集指标，并按仓库、团队、语言生成看板。
4. 处理 cherry-pick、rebase、notes 同步及重复提交等边界场景。
