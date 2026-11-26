# ⚙️ Reaper — 系统语言与开发工作台

<p align="center">[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)</p>

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

源码、架构模式、构建配置、测试和 CI 是已实现行为的依据。路线图和目录仅描述计划或清单，不代表已交付功能。

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

### 原生 C17 开发路线

~~~sh
cmake -S . -B build -DREAPER_BUILD_TESTS=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
~~~

Python 参考运行时与原生 C17 开发路线是两条独立的实现路径；其中一条路径通过测试，并不代表另一条路径已达到功能对等。

## 首次检查

~~~sh
python -m reaper --check examples/flow.rpr
python -m reaper --repl
~~~

--check 命令会在执行前进行静态验证。Windows PowerShell 使用 .venv\Scripts\Activate.ps1 激活环境。

## 运行

安装后，若系统提供 Tkinter，软件包会提供 `reaper-studio` 图形界面脚本；语言服务与调试服务通过独立的 stdio 进程运行。

## 接口

| 接口 | 契约 / 入口 | 能力边界 |
|---|---|---|
| CLI / REPL | `reaper` | 源码检查、执行和交互模式。 |
| 语言服务 | `reaper-lsp / stdio` | 文档级诊断、补全及已支持的导航功能。 |
| 调试适配器 | `reaper-dap / stdio` | 已实现的断点与单步调试子集。 |
| Native ABI | `reaper_ffi / reaper_system / reaper_dabi64_desktop` | 版本化 C 接口；原生编译器的功能对等尚未完成。 |

若仓库中没有版本化实现和测试，则不将 REST/GraphQL、WebSocket、OAuth、云部署或 Cookie 机制描述为现有功能。

## 安全与信任边界

参考运行时采用有界资源控制和显式能力契约。MMIO API 会验证描述符与访问策略，但不会映射物理设备。LSP/DAP 使用本地 stdio 传输；文档所述运行时不包含托管 REST 服务、OAuth 提供商或云控制平面。

安全策略：[SECURITY.md](SECURITY.md)。请勿在公开问题中发布密钥、设备标识符或私人日志。

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

- [功能与成熟度](docs/FEATURES.md)
- [架构](docs/ARCHITECTURE.md)
- [硬件契约语言](docs/HARDWARE_LANGUAGE.md)
- [实现路线图](docs/IMPLEMENTATION_ROADMAP.md)
- [Studio 与 IDE](docs/REAPER_IDE.md)
- [Psychoporter 666](docs/PSYCHOPORTER_666.md)
- [文档索引](docs/README.md)

功能矩阵和实现路线图明确区分已交付的参考运行时行为、部分原生工作和未来硬件能力。

跨项目集成使用有文档说明的版本化接口和显式适配器。可选适配器不会授予其他项目运行时权限或硬件访问权限。

## 参与贡献

修改代码或契约前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。保持改动可审查，添加确定性测试，并按贡献指南使用 Conventional Commits。

## 许可证与法律说明

本项目依据 [Apache-2.0](LICENSE) 许可。软件按许可条款以“按现状”方式提供。第三方项目名称与商标归其各自权利人所有。

本仓库记录的是本地软件接口。除非另行引入并记录托管服务，否则云服务条款、Cookie 同意、OAuth 和 CORS 均不适用于上述本地运行组件。

---

<p align="center"><sub>Psychoporter 666 README Standard v1.0 · Ivan-VHS · 2026-11-25 · UTC</sub></p>
