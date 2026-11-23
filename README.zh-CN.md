# Reaper — flow-first 编程语言与 Studio

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

<p align="center"><img src="assets/readme/dashboard.svg" alt="Reaper 项目概览" width="100%"></p>

[源代码仓库](https://github.com/Ivan-VHS/Reaper) · [Python CI](.github/workflows/ci.yml) · [Windows Studio 构建](.github/workflows/desktop-build.yml) · [Node.js 兼容性](.github/workflows/noo-tah.yml) · [文档索引](docs/README.md) · [Apache-2.0](LICENSE)

## Studio 实际截屏

<p align="center"><a href="assets/screenshots/reaper-studio.png"><img src="assets/screenshots/reaper-studio.png" alt="Reaper 在 Windows 上运行的实际截屏" width="100%"></a></p>
<p align="center"><sub>1920×1080 · 点击图片查看原始 PNG 文件。</sub></p>

这是由本仓库 README 截图工作流从 Windows 上真实运行的 Reaper Studio 窗口截取的画面。横幅和流程图是原创 SVG 插图，并非软件截图。

### 架构一览

<p align="center"><img src="assets/readme/workflow.svg" alt="Reaper implemented data flow" width="100%"></p>

实际流程：`.rpr` 源码 → lexer 与 parser → Python 参考运行时 → CLI、Studio、LSP 和 DAP。


[![Python CI](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/Reaper/ci.yml?branch=main&label=Python%20CI)](https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml)  [![Live Studio capture](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/Reaper/readme-screenshots.yml?branch=main&label=Live%20Studio%20capture)](https://github.com/Ivan-VHS/Reaper/actions/workflows/readme-screenshots.yml)  [![License](https://img.shields.io/github/license/Ivan-VHS/Reaper)](LICENSE)


> **项目范围：** Reaper 是一款本地编程语言、解释器、开发工具集合以及 Windows 桌面 IDE。它不是托管的 Web Demo，也不是生产 Web 服务。Python 是当前可执行的兼容性参考实现；原生 C17 路线仍为部分实现。文档已于 **2026-11-22** 对照 `main` 分支核对。

## 项目用途与实现状态

Reaper 是一种表达式导向语言，运算符 `::` 会将值传递给下一步操作。项目包含 Python 参考运行时、CLI/REPL、Windows Studio、stdio LSP/DAP 服务，以及通过 NOO TAH 对官方 Node.js 发行版的可选集成。

目标读者包括语言和工具链开发者、应用工程师、QA、教育工作者及代码审查者，他们需要试验 Reaper 源文件并检查语言服务合同。

### 已实现的组件

| 组件 | 当前范围 | 明确边界 |
|---|---|---|
| Python Runtime | lexer、parser、interpreter、CLI、REPL、模块、闭包、配额与审计日志 | 当前可执行参考实现 |
| Reaper Studio | Windows IDE 基础：项目树、编辑器、语法着色、搜索、check/run 与 debugger | 本地桌面应用 |
| LSP | stdio JSON-RPC、诊断、补全、hover、符号、词法导航和文档格式化 | 每个已打开文档独立；不提供跨文件类型推断 |
| Toolchain 清单 | 通过 PATH 查找编译器、构建工具、解析器、格式化工具、调试器和 WASM 运行时，并固定 SHA-256 | 仅执行路径查找与哈希；不会运行找到的程序 |
| DAP | stdio 调试适配器、行断点、单步、堆栈和局部变量 | 语句边界调试；仅适用于可信本地程序 |
| NOO TAH | 管理官方 Node.js 运行时、项目/进程、npm/npx 和 Inspector | Node/V8/libuv 由上游 Node 提供 |
| Native C17 | lexer、表达式 parser、owned AST、checked IR 和有限 lowering | 正在开发的部分实现；不等于 Python Runtime |
| QCS / Embedded | 独立硬件领域 parser、JSON AST 和有界嵌入式辅助工具 | 参考/分析工具，不执行硬件操作 |
| Kora | 七个清单模块中的可选标准库辅助函数 | 与 Reaper 语言运行时分离 |

目录和注册表可能包含提案或预留条目。出现在目录中不代表该功能已在运行时实现。成熟度和边界见 [Features](docs/FEATURES.md)、[REAPER IDE](docs/REAPER_IDE.md)、[NOO TAH](docs/NOO_TAH.md) 和 [Kora helpers](docs/KORA.md)。

下图是 Windows Studio 的实际桌面截屏，不是浏览器 Playground。


## 快速开始

### 环境要求

- Python **3.10 或更高版本**。CI 当前测试 Python 3.10、3.11 和 3.12。
- Studio 图形界面需要 Tkinter（通常包含在标准 Python 发行版中；某些精简 Linux Python 包会将其拆分）。
- Git。
- 只有在构建部分原生路线时才需要 CMake **3.16+** 和 C17 编译器。
- NOO TAH 的 Node.js 是可选项。兼容性工作流测试 Node.js **22 和 24**；运行 Reaper `.rpr` 程序并不需要它。

Python 包在 `pyproject.toml` 中声明 `setuptools>=68` 为构建系统要求，但没有声明第三方运行时依赖列表。

### 安装 Python 参考运行时

```sh
python -m venv .venv
# 激活环境：
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Linux / macOS:       source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

### 运行程序并打开 Studio

```sh
python -m reaper --check examples/flow.rpr
python -m reaper examples/flow.rpr
python -m reaper --repl
python reaper_desktop.py
```

完成 editable installation 后，还可使用 `reaper`、`reaper-studio` 和 `reaper-toolchain` 入口命令。

本地工具清单与 SHA-256 lock 创建不会运行所发现的程序：

```sh
reaper-toolchain --output toolchain-inventory.json
```

### 运行测试

```sh
python -m compileall -q reaper tests
python -m unittest discover -s tests -v
```

首次安装可能从包索引下载已声明的构建后端；此后程序在本地运行。应用没有 HTTP 端口、浏览器 URL、数据库 seed 步骤或独立 Mock Server。

### 可选的 Native C17 路线

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DREAPER_BUILD_TESTS=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

该构建验证当前原生编译器子集及其测试。它不会替代 Python Runtime，也不代表完整语言兼容性。

### 可选的 NOO TAH / Node.js 检查

安装官方 Node.js 发行版，并将 `node` 加入 `PATH`，然后运行：

```sh
reaper-noo-tah version
reaper-noo-tah doctor
reaper-noo-tah check app.mjs
reaper-noo-tah run app.mjs
reaper-noo-tah npm run build
```

这些命令操作所选的本地 Node 项目。如果项目本身启动 HTTP Server，端口由该项目控制；Reaper 自身不提供 Web Preview URL。

## 可复现工作流、示例与数据

仓库中的示例是本地源程序，不是来自实时 API 的响应：

- `examples/flow.rpr` 是基础语言 Smoke 示例。
- `examples/device_audit.rpr` 演示只读审计流程，运行后会生成带版本号的 JSON 报告。
- `tests/` 包含 parser、runtime、语言服务、debugger、注册表和集成测试。
- NOO TAH 一致性测试覆盖 Node built-ins、ESM/CommonJS、streams、workers、child processes 和 loopback HTTP/TCP，不依赖公共测试服务。

可按以下场景验证：

1. **仅检查语法：**`python -m reaper --check examples/flow.rpr`；检查语法但不运行程序。
2. **运行示例：**`python -m reaper examples/flow.rpr`；检查输出结果。
3. **替代执行引擎：**`python -m reaper --engine vm examples/flow.rpr`；与默认 tree-walk 引擎比较。
4. **交互式提示符：**`python -m reaper --repl`；退出后当前内存会话结束。
5. **LSP 服务：**`python -m reaper lsp`；从 stdin 读取带帧的 JSON-RPC，并将协议消息写入 stdout。
6. **DAP 服务：**`python -m reaper dap`；使用可信本地程序进行启动和语句级调试。
7. **Node 兼容性：**`node --test tests/noo_tah/conformance.test.mjs`；测试使用 loopback networking 和 Node built-ins。

CLI 设有明确的资源限制：默认最多一百万个执行步骤、100,000 个集合元素、一百万个文本字符、64 MiB managed heap，以及同时打开 64 个 managed files。可通过文档化 CLI 参数修改这些值。它们是解释器保护措施，不是操作系统级 Sandbox。

运行时状态存在于进程内及操作者选择的文件中。可选的 `--audit-log PATH` 会追加本地 hash-chained 执行日志；`--verify-audit-log PATH` 用于校验日志。关闭进程会结束当前内存会话，但不会删除源文件或日志。项目没有浏览器 localStorage、sessionStorage、IndexedDB 或 Cookie 状态。

## 配置、环境与信任边界

仓库根目录没有 `.env.example`、Docker Compose Web Stack、托管账号系统、Demo 登录、CORS 策略或应用 HTTPS 配置。Python Runtime 不需要 Node.js。NOO TAH 有三个已文档化的环境变量覆盖项：

| 变量 | 用途 | 默认值 / 行为 |
|---|---|---|
| `NOO_TAH_NODE` | Node 可执行文件路径 | 否则在 `PATH` 中查找 `node` |
| `NOO_TAH_NPM_CLI` | 显式指定 `npm-cli.js` 路径 | 否则在所选 Node 安装附近的常见路径中查找 |
| `NOO_TAH_NPX_CLI` | 显式指定 `npx-cli.js` 路径 | 否则在所选 Node 安装附近的常见路径中查找 |

这些值是可执行文件路径，不是秘密。不要将 credentials 存入 source control。找不到 Node 时会提示 `Node.js not found`；找不到 npm/npx CLI 时会指出需要设置的覆盖变量。

其他重要开关：

- `--check` / `--lint` 只解析程序，不执行。
- `--engine treewalk|vm` 选择 Runtime Engine。
- `--allow-native-ffi` 显式允许加载原生 C ABI；仅使用可信库。
- `--steps`、`--items`、`--text-length`、`--heap-bytes` 和 `--open-resources` 设置资源限制。

语言解释器不是 OS Sandbox。DAP 会启动可信本地文件；FFI 允许执行原生代码；npm 包安装和 lifecycle scripts 会以当前用户权限执行第三方代码。不要仅仅因为某个程序或包出现在 Demo 中就运行未知代码。

LSP 和 DAP 通过标准输入/输出使用 Content-Length framed JSON-RPC，并非托管 HTTP API。显式请求时，Node Inspector 可以开放本地调试端点；该端点属于所选 Node 进程，而不是公开的 Reaper Web Stand。

## Studio 操作与快捷键

Windows Studio 编辑器通过标准语言服务提供本地源码导航：

| 快捷键 / 操作 | 行为 |
|---|---|
| `Ctrl+Space` | 为 Reaper 关键字、内置函数和当前文档符号提供本地补全 |
| `F12` | 跳转到当前文档中的声明 |
| Find references | 查找当前文档中的词法标识符出现位置 |
| `Ctrl+Shift+R` | 确认后重命名当前文档中的词法匹配项 |
| `Ctrl+K` | 打开命令面板 |
| `Ctrl+Alt+K` | 打开 CODEX-66 能力目录 |

这些操作仅限当前文档，不提供跨文件语义重构。Conditional breakpoints、evaluate、step-out、完整类型推断以及云端 AI 助手均未被声明为已实现。

## 架构与仓库目录

```text
Reaper source (.rpr)
  -> Python lexer / parser / runtime
  -> CLI, REPL or Studio
  -> optional LSP / DAP stdio services

JavaScript project
  -> NOO TAH process manager
  -> official Node.js (V8, libuv, npm, Inspector)

Native C17 track
  -> lexer / parser / AST / IR / limited lowering
```

| 路径 | 内容 |
|---|---|
| `reaper/` | Python 参考运行时、CLI、Studio、语言/调试服务和 NOO TAH |
| `reaper/kora/` | Kora 标准库辅助函数 |
| `src/`、`include/` | 部分原生 C17 路线 |
| `tests/` | Python、协议、运行时和原生测试 |
| `examples/` | 本地 `.rpr` 示例程序 |
| `docs/` | 语言、IDE、架构和功能边界文档 |
| `editors/` | 编辑器支持与协议说明 |
| `.github/workflows/` | CI、原生/桌面构建和 Node 兼容性 |

该项目没有被拆分为已部署的 frontend、backend 和 Mock API。浏览器兼容性、浏览器存储、公共端口、CORS 和 HTTPS 不适用于 Reaper Runtime 本身。

## CI、桌面产物与回滚

- [Reaper CI](.github/workflows/ci.yml) 测试 Python 3.10/3.11/3.12，并验证示例与合同。
- [NOO TAH 兼容性](.github/workflows/noo-tah.yml) 在 Windows、Linux 和 macOS 上测试 Node 22 和 24。
- 原生 C17 路线单独构建和测试。
- [Desktop build](.github/workflows/desktop-build.yml) 将 Windows Studio 打包为 `Reaper-Studio-windows-x64.zip`。匹配 `v*` 的 Git Tag 会触发 Release 发布。

Workflow Artifact 是可下载的构建结果，不是在线托管 IDE。回滚已分发桌面版本时，使用此前带标签的 GitHub Release。没有需要回滚的在线 Web 服务。构建日志和测试诊断可在 GitHub Actions 查看。

## 故障排查

| 现象 | 检查方法 |
|---|---|
| 找不到 `python -m reaper` | 激活虚拟环境，或从仓库根目录运行 |
| Studio 无法打开 | 检查所安装的 Python 是否包含 Tkinter |
| 找不到 Node | 安装 Node.js，或通过 `NOO_TAH_NODE` 指定可执行文件路径 |
| 找不到 npm/npx | 设置 `NOO_TAH_NPM_CLI` 或 `NOO_TAH_NPX_CLI` |
| Node 项目构建失败 | 运行 `reaper-noo-tah doctor`，并检查 Node/npm 输出；lifecycle scripts 可能执行第三方代码 |
| 原生 C 测试失败 | 检查 CMake 3.16+、C17 编译器和完整 CTest 输出 |
| LSP/DAP 输出格式异常 | stdout 只用于协议帧；应用日志应写入 stderr |

## 已知限制、贡献与许可证

Python 仍是当前可执行的兼容性参考实现。Native C17 parsing/lowering 仅部分实现。LSP symbols/references/rename 是词法级且仅限当前文档；DAP stepping 以语句为粒度；IDE 不是 OS Sandbox。NOO TAH 将 JavaScript 行为交给官方 Node，而不是自行重实现 V8。

仓库的贡献流程、变更验证和 Pull Request 要求见 [CONTRIBUTING.md](CONTRIBUTING.md)。请通过 [GitHub Issues](https://github.com/Ivan-VHS/Reaper/issues) 或 Pull Request 提交改进。附上可复现的 `.rpr` 示例、Python/Node/compiler 版本以及准确命令和输出。运行 Python 测试；修改原生路线时还应运行 CMake/CTest。

许可证：[Apache-2.0](LICENSE)。

## README 与 66 条规则的对应关系

根据真实的本地开发工具产品，对 Web Stand 规则进行映射：

| 规则范围 | README 覆盖内容 |
|---|---|
| 1–11 · 用途与边界 | 说明语言/IDE 的目标、读者、可执行与部分实现路线、本地范围和没有托管 Demo |
| 12–22 · 快速开始 | 提供准确的 Python 安装、CLI、Studio、测试、原生 C17 和可选 Node 命令 |
| 23–33 · 配置与访问 | 记录三个真实的 NOO TAH 路径覆盖项、CLI 开关和信任边界；不虚构 credentials 或 `.env` |
| 34–44 · 数据与行为 | 本地示例、测试场景、执行配额、审计日志生命周期、仅 loopback 的一致性测试和调试限制 |
| 45–55 · 架构与构建 | 列出包、原生源码、示例、测试、服务和 CI 产物 |
| 56–66 · 运维与支持 | 链接构建/发布工作流，说明产物回滚、诊断、已知限制、贡献方式和许可证 |

**Reaper 没有公开的 Web Playground URL。** Studio 截图和可下载 Windows Artifact 不等于在线 Web Stand。

## 统一报告封装

可以将 JSON 输出包装为通用的 ivan-vhs.report.v1 元数据格式，同时保留 Reaper 的原始结果：

    python tools/report_envelope.py --tool reaper --version VERSION < result.json

请参阅 docs/REPORT_ENVELOPE.md 和 schemas/ivan-vhs.report.v1.schema.json。该封装保留工具数据并记录结果限制。


## 文档导航图

请从[文档索引](docs/README.md)进入，并使用[信息架构图](docs/INFORMATION_ARCHITECTURE.md)浏览语言、编译器、Runtime、Studio 和集成主题集群。主题入口链接到详细契约；实现状态仍以源代码、测试和 Schema 为准。


## Mora 桌面集成

Reaper Studio 可从统一的 Mora 工作空间启动。Mora 提供应用目录和启动主题；Reaper 保留自己的编辑器、运行时、调试器和原生窗口。请参阅 [Mora 集成说明](docs/MORA_DESKTOP_INTEGRATION.md) 和 [DuckOS 工作空间契约](https://github.com/Ivan-VHS/DuckOS/blob/main/docs/MORA_DESKTOP.md)。
