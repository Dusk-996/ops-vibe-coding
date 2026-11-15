# 复用验证与图稿发布检查记录

记录日期为 2026-11-15，目标环境为 Windows。方法论采用范围和验收条件见 [复用验收计划](../plans/2026-11-15-reuse-acceptance.md)。

## 复用验证状态

本轮方法论采用验证状态为 `NOT_VERIFIED`。[执行任务](../plans/2026-11-15-reuse-tasks.md) 中 N、E、Q 任务尚未勾选，仓库内尚无可追溯的实际采用报告，忽略目录 `.scratch/reuse-validation/` 也尚不存在。

Windows Codex CLI 0.169.0 的文档与 Skill 阶段采用、V-01 至 V-09 场景均待实际执行并补充证据。完整 TDD、应用构建、浏览器 E2E、部署与恢复，以及其他系统和运行时的适用性均为 `NOT_VERIFIED`。

## 本次发布检查

本次检查覆盖文档发布清单、Git 历史、总图结构与导出和仓库可见性。远端提交一致性在最终推送后核对并记入交付说明。

| 检查项 | 状态 | 依据 |
|---|---|---|
| 当前文档基线 | PASS | `d01b8f9` 纳入 32 个待提交文件，保留原 13 个提交和 MIT 作者声明 |
| 凭据与文件范围 | PASS | 当前工作区及历史的明显凭据模式扫描未命中；`.scratch/` 被 Git 忽略 |
| 相对文件链接 | PASS | 补齐本记录后，Markdown 相对文件目标均存在；锚点需另行核对 |
| 新总图结构与导出 | PASS | skill 的 `validate-drawio.py` 通过；draw.io 重新读取源文件并导出 SVG，原生文本共 77 处，未依赖外部资源 |
| 新总图语义与本地显示 | PASS | 对照 Full Track 复核 S01–S14 与主要回退路径；查看 800px 宽度 PNG，修复了底部回线标签与 S13 获批文字的拥挤问题 |
| GitHub 仓库属性 | PASS | API 确认 `Dusk-996/ops-vibe-coding` 为独立私有库，默认分支为 `main` |
| GitHub 页面目视验收 | NOT_VERIFIED | 浏览器控制工具无法可靠识别当前 URL，停止了 UI 操作；SVG 另做本地显示宽度检查 |

## 交互图检查

检查对象为 [现有 Archify HTML](../ops-vibe-coding-workflow.html)，当前工作区文件的 SHA-256 为 `5a65e07d42db6b00ca8370d823c9587dce7ea434c4f04936e3518757f7063140`。

| 检查项 | 状态 | 实测结果 |
|---|---|---|
| Archify `check` | PASS_WITH_WARNING | 9 项结构检查通过，存在 1 项视口高度警告 |
| Archify `browser-check` 加载 | PASS | Chrome 成功加载并完成 6 组视口与主题测量 |
| 可读性、Viewer 控件布局与主题 | PASS | 专用浏览器检查结果通过 |
| 视口容纳 | FAIL | 页面高度为 2001–2161px，旧 HTML 尚无 Reader fit 声明，6 组测量均报告纵向溢出 |
| 搜索与缩放交互 | NOT_VERIFIED | 专用检查未执行搜索输入和缩放点击，浏览器 UI 操作受工具阻断 |

综合自动化浏览器检查结果为 `FAIL`。原 HTML 及旧检查记录保留；本次原始输出保存在忽略目录 `.scratch/archify-check/`，重新执行时应生成新的回执。
