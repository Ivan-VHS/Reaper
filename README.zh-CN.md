
<p align="center"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme/hero-banner-dark.svg"><source media="(prefers-color-scheme: light)" srcset="assets/readme/hero-banner-light.svg"><img src="assets/readme/hero-banner-light.svg" alt="Reaper 系统编程语言与开发工作台" width="880"></picture></p>
<h1 align="center">Reaper — 系统编程语言与开发工作台</h1>
<p align="center"><strong>Flow-first 语言，提供 Python 参考运行时、CLI、Windows Studio、stdio LSP/DAP 服务，以及独立演进的部分 native C17 路径。</strong></p>
<p align="center"><a href="https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml"><img alt="Python CI" src="https://img.shields.io/github/actions/workflow/status/Ivan-VHS/Reaper/ci.yml?branch=main&style=flat-square&label=Python%20CI"></a> <a href="https://github.com/Ivan-VHS/Reaper/actions/workflows/desktop-build.yml"><img alt="Windows Studio" src="https://img.shields.io/github/actions/workflow/status/Ivan-VHS/Reaper/desktop-build.yml?branch=main&style=flat-square&label=Windows%20Studio"></a> <a href="LICENSE"><img alt="Apache-2.0" src="https://img.shields.io/github/license/Ivan-VHS/Reaper?style=flat-square"></a></p>

[快速开始](#快速开始) · [Revival 更新](#文档-revival-更新) · [视觉概览](#视觉概览) · [架构](#架构) · [文档索引](docs/README.md)

> **实现边界：**Python runtime 是可执行的兼容参考实现。Native C17 lexer/parser/IR/lowering 仅部分实现，并非完整编译器或通用机器码后端。Studio 仅支持 Windows。LSP/DAP 是本地 stdio 服务，不是托管 API。

## 快速开始

**环境要求：**Python 3.10+、Git。Studio 需要 Tkinter。仅构建部分 native 路径时才需要 CMake 3.16+ 和 C17 编译器。NOO TAH 可选 Node.js。

~~~sh
git clone https://github.com/Ivan-VHS/Reaper.git
cd Reaper
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m reaper --check examples/flow.rpr
python -m reaper examples/flow.rpr
~~~

启动 Windows Studio：

~~~sh
python reaper_desktop.py
~~~

运行测试：

~~~sh
python -m unittest discover -s tests -v
~~~

## 文档 Revival 更新

| 之前 | Revival 文档 |
|---|---|
| 单一静态横幅 | 浅色/深色主题匹配的 SVG Hero |
| Python runtime 与 native compiler 容易混淆 | 明确区分 Python 参考实现和部分 native C17 |
| Studio 截图与数据流程图混在一起 | 真实 Windows Studio 截屏与单独标注的流程示意图 |
| 功能描述过于笼统 | 明确服务、平台和语言工具的限制 |
| 导航冗长 | 主题索引、信息架构地图和发布规范 |

这是文档更新，**不代表新的 Reaper 语言版本或 Release**。功能成熟度以源代码、测试和 [FEATURES.md](docs/FEATURES.md) 为准。

## 当前实现

| 组件 | 当前能力 | 边界 |
|---|---|---|
| Python 参考运行时 | Lexer、parser、interpreter、scopes、values、quotas、CLI/REPL | 兼容性参考实现 |
| 静态分析 | check、Studio 和 LSP 中的保守 AST/type diagnostics | 仅静态分析，不执行源代码 |
| Studio | Windows 编辑器/调试器、命令面板、MCU 配置视图 | 没有实时设备检查器 |
| LSP | stdio、UTF-16 positions、本地诊断、completion、hover、symbols | 单文档；无跨文件类型推断 |
| DAP | Launch、行断点、语句级单步、stack 和 locals | 仅支持文档列出的运行时子集 |
| Native C17 | Lexer、表达式 parser、owned AST、checked i64 IR、有限 lowering | 部分实现，不具备完整语言一致性 |
| QCS / 硬件契约 | 语法验证和 checked MMIO descriptor API | 无物理映射或完整设备运行时 |
| NOO TAH | 可选的官方 Node.js 集成 | 运行 .rpr 不需要 Node.js |

## 视觉概览

<table><tr><td width="50%"><a href="assets/screenshots/reaper-studio.png"><img src="assets/screenshots/reaper-studio.png" alt="Reaper Studio 在 Windows 上运行的实际截屏" width="100%"></a><p><sub><strong>真实 Studio 截屏</strong> — Windows desktop，1920×1080。</sub></p></td><td width="50%"><img src="assets/readme/workflow.svg" alt="Reaper 源码、解析器、Python runtime 与开发服务流程图" width="100%"><p><sub><strong>架构示意图</strong> — 已实现的数据路径，不是 UI 截图。</sub></p></td></tr></table>

## 架构

~~~mermaid
flowchart LR
  A[.rpr source] --> B[Lexer 和 parser]
  B --> C[AST 与 source spans]
  C --> D[Python reference runtime]
  D --> E[CLI / REPL]
  D --> F[Windows Studio]
  D --> G[stdio LSP / DAP]
  C -. 部分路径 .-> H[Native C17 IR 和有限 lowering]
  I[可选 Node.js] --> J[NOO TAH adapter]
~~~

Native C17 被单独标注为部分实现，不与 Python 参考运行时等同。

## 配置与信任

项目没有托管 Web 服务、账户系统或根目录 .env。NOO TAH 支持以下可选路径变量：

| 变量 | 用途 |
|---|---|
| NOO_TAH_NODE | 指定 Node 可执行文件路径 |
| NOO_TAH_NPM_CLI | 指定 npm-cli.js 路径 |
| NOO_TAH_NPX_CLI | 指定 npx-cli.js 路径 |

常用开关包括 --check / --lint、--engine treewalk|vm、--allow-native-ffi，以及 --steps、--items、--text-length、--heap-bytes、--open-resources 等资源限制。FFI 默认关闭，必须显式启用。解释器不是 OS sandbox；仅运行可信程序和库。

## 仓库结构

| 路径 | 职责 |
|---|---|
| reaper/ | Python 语言前端、运行时与命令服务 |
| native/ / src/ | 部分 C17 实现和 native 契约 |
| examples/ | 可运行的 .rpr 程序 |
| tests/ | Runtime、parser、诊断与集成测试 |
| editors/vscode/ | 仅提供 VS Code 语法支持 |
| docs/ | 语言、编译器、运行时、IDE 和硬件契约 |
| assets/readme/ | 主题适配 Hero 和流程示意图 |
| .github/workflows/ | Python CI、Windows Studio 和集成工作流 |

## 验证与路线图

~~~sh
python -m unittest discover -s tests -v
python -m reaper --check examples/flow.rpr
git diff --check
~~~

修改 native 路径时还需运行 CMake/CTest。当前成熟度和阶段见 [架构](docs/ARCHITECTURE.md)、[功能矩阵](docs/FEATURES.md)、[Hardware Language](docs/HARDWARE_LANGUAGE.md)、[IDE contract](docs/REAPER_IDE.md) 与 [信息架构地图](docs/INFORMATION_ARCHITECTURE.md)。

## 参与开发

请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)、[README Visual Standard](docs/README_VISUAL_STANDARD.md) 和 [SECURITY.md](SECURITY.md)。Grammar、diagnostics、runtime quotas、LSP/DAP 和 native contracts 的改动应包含针对性回归测试。

## 许可证

[Apache-2.0](LICENSE)。
