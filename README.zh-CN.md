<p align="center">[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)</p>

<h1 align="center"><strong>⚙️ Reaper — 系统语言与开发工作台</strong></h1>

[![CI](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/Reaper/ci.yml?branch=main&label=CI)](https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml) [![Native C17](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/Reaper/native-c.yml?branch=main&label=Native%20C17)](https://github.com/Ivan-VHS/Reaper/actions/workflows/native-c.yml) [![Apache-2.0](https://img.shields.io/github/license/Ivan-VHS/Reaper)](LICENSE)

> **显式契约、类型化流程，以及带源码定位的诊断。**

**项目状态:** Alpha · 参考运行时可用 · 原生 C17 路线尚未完整 · **版本:** Python package 0.1.0 · Native CMake track 0.2.0 · **License:** [Apache-2.0](LICENSE) · **README 标准:** Psychoporter 666 v1.0 · **审阅日期:** 2026-11-25 · UTC · **Source:** [Ivan-VHS/Reaper](https://github.com/Ivan-VHS/Reaper)

<p align="center"><img src="assets/reaper-hero.svg" alt="Reaper — 系统语言与开发工作台 — project overview" width="100%"></p>
<p align="center"><a href="assets/screenshots/reaper-studio.png"><img src="assets/screenshots/reaper-studio.png" alt="Reaper — 系统语言与开发工作台 — application screenshot" width="100%"></a></p>

## 快速导航

[🚀 Demo: Studio screenshot](assets/screenshots/reaper-studio.png) · [Documentation](docs/README.md) · [Source repository](https://github.com/Ivan-VHS/Reaper) · [Issues](https://github.com/Ivan-VHS/Reaper/issues)

## 目标与范围

Reaper 是系统编程语言与本地开发工作台。Python 参考运行时、CLI/REPL、LSP/DAP 服务和 Windows Studio 基础，与实验性原生 C17 编译器路线相互独立。原生功能对等和特权硬件服务尚未完成。

## 功能

- .rpr 源语言、词法/语法分析器、参考解释器和结构化诊断。
- CLI、REPL、Windows Studio 基础，以及基于 stdio 的 LSP/DAP 服务。
- 参考运行时中的静态检查和资源配额；仅检查模式不会执行源代码。
- 原生 C17 路线包含词法分析、解析、拥有型 AST、受检 IR、常量折叠和有限 lowering。
- 经过检查的 MMIO 描述符与 ABI 契约只是接口，不是物理映射器或设备驱动。
- Jora 脚手架、Kora 助手，以及具有明确信任边界的可选生态集成。

## 架构与数据流

~~~mermaid
flowchart TB
  S[".rpr source"] --> P["Lexer / parser"]
  P --> V["Reference runtime"]
  V --> C["CLI / REPL"]
  V --> L["stdio LSP / DAP"]
  S --> N["Native C17 track — partial"]
  N --> I["Checked IR / limited lowering"]
  H["Hardware contracts"] --> A["Checked ABI descriptors"]
  A -.-> X["No implicit device access"]
~~~

Source code, schemas, build files, tests and CI are the evidence for implemented behavior. Roadmap entries and catalogue records describe plans or inventories, not shipped functionality.

## 环境要求

参考运行时和包工具需要 Python 3.10+；原生路线需要 CMake 3.16+ 和 C17 编译器；可选兼容性检查需要 Node.js 22/24；Windows Studio 图形界面需要 Tkinter。

## 构建

~~~sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python -m reaper --check examples/flow.rpr
python -m reaper examples/flow.rpr
~~~

### Native C17 track

~~~sh
cmake -S . -B build -DREAPER_BUILD_TESTS=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
~~~

The Python reference runtime and native C17 track are separate implementation tracks; passing tests in one does not establish feature parity in the other.

## 首次检查

~~~sh
python -m reaper --check examples/flow.rpr
python -m reaper --repl
~~~

--check 命令会在执行前进行静态验证。Windows PowerShell 使用 .venv\Scripts\Activate.ps1 激活环境。

## 运行

After installation, the package exposes the reaper-studio GUI script when Tkinter is installed; language and debug services are separate stdio processes.

## 接口

| Surface | Contract / entry point | Boundary |
|---|---|---|
| CLI / REPL | `reaper` | Source checking, execution and interactive mode. |
| Language service | `reaper-lsp / stdio` | Document-local diagnostics, completion and navigation subset. |
| Debug adapter | `reaper-dap / stdio` | Implemented breakpoint and step subset. |
| Native ABI | `reaper_ffi / reaper_system / reaper_dabi64_desktop` | Versioned C interfaces; native compiler parity remains partial. |

若仓库中没有版本化实现和测试，则不将 REST/GraphQL、WebSocket、OAuth、云部署或 Cookie 机制描述为现有功能。

## 安全与信任边界

参考运行时采用有界资源控制和显式能力契约。MMIO API 会验证描述符与访问策略，但不会映射物理设备。LSP/DAP 使用本地 stdio 传输；文档所述运行时不包含托管 REST 服务、OAuth 提供商或云控制平面。

Security reporting: [SECURITY.md](SECURITY.md). Do not publish secrets, device identifiers or private logs in public issues.

## 质量验证

~~~sh
python -m unittest discover -s tests -v

cmake -S . -B build -DREAPER_BUILD_TESTS=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
~~~

测试范围由已注册的 CTest/unittest 目标和工作流定义。没有公开报告时，不声明覆盖率百分比、模糊测试结果或负载测试报告。

## 性能证据

参考运行时和部分原生路线尚未发布稳定的跨机器延迟或内存占用指标。比较时应记录编译器、目标平台、构建模式和输入数据。

## 兼容性

参考包支持 Python 3.10+；原生 C17 路线使用 CMake 和主机 C17 编译器。Windows Studio 需要 Tkinter。平台和编译器对等性应按目标分别验证。

## 文档与生态

- [Features and maturity](docs/FEATURES.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Hardware language](docs/HARDWARE_LANGUAGE.md)
- [Implementation roadmap](docs/IMPLEMENTATION_ROADMAP.md)
- [Studio and IDE](docs/REAPER_IDE.md)
- [Psychoporter 666](docs/PSYCHOPORTER_666.md)
- [Documentation index](docs/README.md)

功能矩阵和实现路线图明确区分已交付的参考运行时行为、部分原生工作和未来硬件能力。

Cross-project integrations use documented versioned interfaces and explicit adapters. An optional adapter does not grant another project runtime or hardware privileges.

## 参与贡献

修改代码或契约前请阅读 CONTRIBUTING.md。保持改动可审查，添加确定性测试，并按贡献指南使用 Conventional Commits。

## 许可证与法律说明

本项目依据 [Apache-2.0](LICENSE) 许可。软件按许可条款以“按现状”方式提供。第三方项目名称与商标归其各自权利人所有。

This repository documents local software interfaces. Hosted-service terms, cookie consent, OAuth and CORS are not applicable to the runtime surfaces described above unless a separate hosted component is introduced and documented.

---

<p align="center"><sub>Psychoporter 666 README Standard v1.0 · Ivan-VHS · 2026-11-25 · UTC</sub></p>