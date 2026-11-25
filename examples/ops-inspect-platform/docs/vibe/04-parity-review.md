# 原型一致性审查报告（Prototype Parity Review）

**门禁结论：** `PASS_WITH_NOTES`

**后续动作：** `PASS_WITH_NOTES：已通过 P4a 验收并进入 P4b 后端实现（注：无自动化无头浏览器环境，由源码静态核对 + 生产构建 + 人类本机浏览器实机逐页点验共同证实）`

## 审查范围与基准

- **已批准的原型**：`docs/vibe/01-prototype/index.html`（Rev 4：极简工程克制风格 C + Refactoring UI，静态目标登记导入与主动巡检检测分离）
- **批准证据**：用户已于 P1 审查原型 Rev 4 并批准放行，于 P4a 在本机真实浏览器逐页点验并明确批准全部优化项（`approve p4a`）
- **React 实现**：`frontend/src/`（React 18 + Vite 6，生产构建锁定 `VITE_USE_MOCK=false`，开发态无后端时自动启用 `localPreviewAdapter.js`）
- **版本或修订**：当前本地 `demo/frontend` 源码（`vite build` 43 modules，`dist/assets/index-*.js` 230.47 kB）
- **已审查的路由和流程**：
  1. 顶栏导航与身份登录/切换（`#/servers` ↔ `#/schedule`）
  2. 页面 1（`#/servers`）：5 张汇总 KPI、多维筛选（主机名/IP、类型、厂商、采集方式、仅看异常）、主机列表、登记/编辑弹窗、CSV/JSON 批量导入预检与提交、CSV/JSON 导出、单台检测与全量巡检、删除二次确认
  3. 页面 2（`#/schedule`）：定时规则开关、4×6/2×6 网格弹层时间选择器、多发件箱加密存档与切换、收件人校验、手动立即推送二次确认预览、发送记录列表+右侧抽屉、全量操作审计列表+右侧抽屉、`.md` 报告导出
- **视口**：桌面宽屏（用户本机浏览器实机点验；源码含 `1120px` / `1024px` 响应式断点，移动端小屏未做自动化测试，记为非阻断 `NOT_VERIFIED`）
- **已批准的例外**：P4a 验收期间由用户明确提出的 6 项生产 UI 优化（详见“已批准变更”节，均归类为 `APPROVED_CHANGE` 而非未授权偏差）

---

## 覆盖矩阵

| 原型页面/状态 | React 路由/状态 | 视觉一致性 | 交互一致性 | 证据 |
|---|---|---|---|---|
| 视觉令牌（颜色/字号/字体/圆角/阴影） | `frontend/src/styles/app.css:1-120` | `MATCH` | `MATCH` | 对比 `01-prototype/index.html:9-49` 与 `app.css:7-56`，全部 `:root` CSS 变量（`--canvas #f8fafc`、`--ink-900 #0f172a`、`--ok #047857`、`--crit #b91c1c`、`--font-sans`、`--font-mono`、正文 `15px`、控件 `14px`）1:1 保留，无任何组件库洗平 |
| 顶栏导航与身份控制 | `App.jsx:463-542` | `APPROVED_CHANGE` | `APPROVED_CHANGE` | 保留品牌区与双页 Hash 导航；按用户要求移除顶栏数字胶囊、简化页签为“服务器巡检 / 定时推送”，真实后端模式切换为标准“账号/密码”登录弹窗（`LoginModal.jsx`），登录后仅显用户名不显角色后缀 |
| 全局操作反馈通知 | `ToastCard.jsx` + `App.jsx:79-88,557` | `APPROVED_CHANGE` | `APPROVED_CHANGE` | 由原型顶部整行横幅升级为右上角悬浮通知卡片（10 秒自动隐藏 + 悬停暂停 + 运维人话文案 + 淡灰追踪号角标） |
| 页面 1：页头与 5 卡片 KPI | `ServersPage.jsx:115-161` | `APPROVED_CHANGE` | `MATCH` | 保留 5 列 KPI 结构与状态配色；按用户要求移除冗长副标题，并将主按钮归位至列表卡片头与筛选栏右侧 |
| 页面 1：筛选与操作工具栏 | `ServersPage.jsx:163-260` | `APPROVED_CHANGE` | `APPROVED_CHANGE` | 全站原生 `<select>` 100% 替换为自定义 `CustomSelect.jsx`（静态检索 0 个渲染 `<select>`）；`立即全量巡检` 放卡片头右侧，`批量导入` / 合并 `导出 ▾` / `+ 添加服务器` 置于筛选行右侧 |
| 页面 1：主机列表与状态标签 | `ServersPage.jsx:262-355` | `MATCH` | `MATCH` | 8 列结构（主机名/IP、种类·厂商、采集方式、内存、CPU 进度条、状态徽章、最后检测时间、单台检测/编辑/删除）与空态提示完整还原；检测中禁用按钮并展示加载文案 |
| 弹窗 1：登记/编辑目标服务器 | `ServerModal.jsx:1-188` | `APPROVED_CHANGE` | `MATCH` | 仅录静态资产与 SSH 凭据别名（绝不手填内存/CPU），条件显隐 SSH 面板；内部下拉框升级为 `CustomSelect` |
| 弹窗 2：CSV/JSON 批量导入 | `ImportModal.jsx` + `App.jsx:309-337` | `APPROVED_CHANGE` | `MATCH` | 保留下载 CSV 模板、上传预检、重名策略（跳过/覆盖）与待检测初始态；策略下拉升级为 `CustomSelect` |
| 弹窗 3：删除与推送二次确认 | `ConfirmModal.jsx:1-45` + `ReportView.jsx` | `APPROVED_CHANGE` | `MATCH` | 删除目标保留确认与“取消不发请求”；推送确认预览按用户要求去 Markdown 源码化，改为纯 React 渲染的总—分结构卡片/表格 |
| 页面 2：定时规则与 4×6/2×6 时间选择器 | `SchedulePage.jsx:161-225` + `TimePicker.jsx:1-120` | `MATCH` | `MATCH` | 完整保留 24 小时 + 每 5 分网格弹层及 5 组常用班次快捷按钮、点击外部关闭、收件人邮箱格式校验 |
| 页面 2：发件人邮箱（多账号加密存档） | `SchedulePage.jsx:179-200` + `SmtpConfigModal.jsx` | `APPROVED_CHANGE` | `APPROVED_CHANGE` | 在原型只读 SMTP 模式框基础上，按用户要求扩展为“多发件箱加密存档 + 下拉一键热切换（免重输授权码）” |
| 页面 2：发送记录与全量审计 | `SchedulePage.jsx:262-470` + `MailDrawer.jsx` + `AuditDrawer.jsx` | `APPROVED_CHANGE` | `APPROVED_CHANGE` | 按用户要求由卡片平铺升级为单行表格列表 + 点击打开右侧滑出详情抽屉（`ReportView` 渲染总—分报告、一键复制 `op_id`） |
| 响应式小屏断点（`<768px`） | `styles/app.css` 媒体查询 | `NOT_VERIFIED` | `NOT_VERIFIED` | 本项目定位为桌面运维后台且无自动化浏览器测试环境，小屏移动端未实测（非阻断） |

---

## 阻断问题

- 无。

---

## 主要问题

- 无。

---

## 次要问题

- 无（未发现未经批准的实现偏差或组件库洗平）。

---

## 已批准变更（`APPROVED_CHANGE`）

全部 6 项均在 P4a / P4b 实机验收对话中由用户明确提出或确认：
1. **消除全站原生 `<select>`**：封装统一 `CustomSelect.jsx` 覆盖筛选栏、表单弹窗、导入策略与发件箱切换。
2. **报告与推送预览去 Markdown 源码化**：通过 `ReportView.jsx` 将总—分报告渲染为可视化总览 KPI 与异常主机明细表。
3. **发送记录与审计改“单行列表 + 右侧抽屉”**：使用 `MailDrawer.jsx` / `AuditDrawer.jsx`，避免大段正文撑爆页面。
4. **通知栏改右上角悬浮卡片**：`ToastCard.jsx` 支持 10 秒自动隐藏、悬停暂停、运维人话文案与淡灰追踪号。
5. **页面 1 信息架构与登录简化**：移除副标题与顶栏数字胶囊、合并导出下拉、操作按钮归位，登录采用标准“账号/密码”且登录后仅显用户名。
6. **页面 2 升级模式 2 多发件箱管理**：新增 `SmtpConfigModal.jsx` 与下拉热切换，后端 Fernet 加密存库。

---

## 未验证项

1. **无头自动化浏览器截图与 DOM 断言**：本机无浏览器自动化测试环境（按用户规则跳过），由人类在本机 Chrome/Edge 启动 `http://127.0.0.1:5173/` 逐页实机操作验收替代，不伪造自动化截图。
2. **移动端窄屏（`<768px`）排版**：非本内部运维台目标 viewport，未做实机验证。

---

## 证据

- **截图**：无（未启用自动化浏览器截图；用户已在本机浏览器实机点验并上传过 3 张现场截图反馈优化并最终确认通过）。
- **静态代码与样式核对**：
  - `Select-String -Path frontend/src/**/*.jsx -Pattern '<select\b'` → **0 个原生 `<select>` 渲染标签**（仅 `CustomSelect.jsx:4` 注释命中）。
  - `docs/vibe/01-prototype/index.html:9-49` vs `frontend/src/styles/app.css:7-56` 视觉变量 100% 一致。
- **命令及最新结果**：
  - `npm --prefix demo/frontend run build` → **`✓ 43 modules transformed. ✓ built in 503ms`**（`dist/index.html` 0.42 kB、`dist/assets/index-DHTpgNpi.css` 22.34 kB、`dist/assets/index-Brz7JFZL.js` 230.47 kB，0 错误）。

---

## 门禁结论依据

React 前端 100% 保留了已批准原型 Rev 4 的风格 C 视觉语言与全部核心交互流程，无任何组件库洗平，全站 0 原生 `<select>`，生产构建通过；所有相对原型的结构演进均有明确的人类验收批准记录（`APPROVED_CHANGE`），0 个未授权偏差（`DEVIATION`）。受限于无自动化浏览器测试环境，采用源码静态核对 + 生产构建 + 人类本机浏览器实机点验作为组合证据，因此门禁结论为 **`PASS_WITH_NOTES`**，满足进入后续阶段条件。
