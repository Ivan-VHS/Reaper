# Reaper

Reaper 是一款面向编译器工具、嵌入式软件和硬件相关程序的系统编程语言与本地开发工作台。

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

<picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme/dashboard.svg"><img src="assets/readme/dashboard-light.svg" alt="Reaper 语言与开发工具" width="100%"></picture>

[![CI](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/Reaper/ci.yml?branch=main&style=flat-square&label=CI)](https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml) [![Apache-2.0](https://img.shields.io/github/license/Ivan-VHS/Reaper?style=flat-square)](LICENSE)

**状态：**已提供 Python 参考运行时、CLI/REPL、Windows Studio 基础、stdio LSP/DAP 服务及部分原生 C17 路线。原生编译器功能对等和特权硬件服务尚未完成。

## 组件

- Reaper 源语言、词法/语法分析器、参考运行时和诊断。
- Neural Contract System v1：版本化模型、数据端口、推理准入、受控学习、联邦、安全、来源和输出行为契约。参考策略模型已实现；不宣称已实现神经网络执行/训练或 C17 原生一致性。
- CLI、REPL、Windows Studio 基础、LSP 与 DAP 服务。
- 实验性 C17 原生实现；当前尚未与参考运行时功能对等。
- NOO TAH 将 JavaScript 执行交给官方 Node.js 运行时。
- Jora 项目脚手架和能力组合；目录中的应用包仍是规范，不是可安装的编辑器。

文档：[Neural Contract System](docs/NEURAL_CONTRACT_SYSTEM.md) · [功能](docs/FEATURES.md) · [架构](docs/ARCHITECTURE.md) · [Hardware Language](docs/HARDWARE_LANGUAGE.md) · [Jora 工厂](docs/JORA_APPLICATION_FACTORY.md) · [Studio](docs/REAPER_IDE.md) · [NOO TAH](docs/NOO_TAH.md)。

## 快速开始

要求：参考运行时使用 Python 3.10–3.12；可选兼容性测试使用 Node.js 22/24；Windows Studio 需要 Tkinter；原生路线需要 CMake 3.16+ 和 C17 编译器。

```sh
python -m venv .venv
python -m pip install -e .
python -m reaper --check examples/flow.rpr
python -m reaper examples/flow.rpr
```

启动 Studio 或 REPL：

```sh
python reaper_desktop.py
python -m reaper --repl
```

参考运行时测试：

```sh
python -m unittest discover -s tests -v
```

## 架构与状态

.rpr 参考运行时、部分 C17 原生实现、开发工具和外部运行时适配器是不同的工作路线。目录条目或计划不代表功能已经实现。

- [实现路线图](docs/IMPLEMENTATION_ROADMAP.md)
- [Kora 标准库助手](docs/KORA.md)
- [文档索引](docs/README.md)
- [生态共享标准](https://github.com/Ivan-VHS/DAK/blob/main/docs/SHARED_STANDARDS.md)

[贡献指南](CONTRIBUTING.md) · [安全策略](SECURITY.md) · [Apache-2.0 许可证](LICENSE)
