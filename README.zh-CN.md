# Reaper — 系统语言与开发工作台

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

[![CI](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/Reaper/ci.yml?branch=main&label=CI)](https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml) [![Native C17](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/Reaper/native-c.yml?branch=main&label=Native%20C17)](https://github.com/Ivan-VHS/Reaper/actions/workflows/native-c.yml) [![Apache-2.0](https://img.shields.io/github/license/Ivan-VHS/Reaper)](LICENSE)

> **Flow-first 语法、显式契约，以及保留源码上下文的诊断。**

**项目记录：** Alpha · Python 参考运行时可用 · 原生 C17 编译器路线部分实现 · Python package 0.1.0 · CMake track 0.2.0 · Apache-2.0 · **文档审核：** 2026-11-27 UTC

<p align="center"><img src="assets/reaper-hero.svg" alt="Reaper 系统语言与开发工作台概览" width="100%"></p>
<p align="center"><a href="assets/screenshots/reaper-studio.png"><img src="assets/screenshots/reaper-studio.png" alt="Reaper Studio 截图" width="100%"></a></p>

## 项目用途与范围

Reaper 是一款系统编程语言和本地开发工作台。当前实现分为两个独立方向：Python 参考运行时和实验性的原生 C17 实现。原生路线尚未达到参考运行时的功能对等。Windows Studio、LSP/DAP 服务和外部适配器属于独立的开发工具接口。

## 语言示例

`.rpr` 语言采用 flow-first 表达式和 `::` 运算符：左侧值作为第一个参数传递给右侧函数。

~~~reaper
craft double(value) {
    yield value * 2
}

make values := [1, 2, 3]
make result := values :: map(double) :: sum()
emit "result = " ++ text(result)
~~~

安装参考运行时后，可运行仓库中的示例：

~~~sh
python -m venv .venv
python -m pip install -e .
python -m reaper --check examples/flow.rpr
python -m reaper examples/flow.rpr
~~~

## 已实现内容

- **参考语言运行时：** lexer、parser、AST 解释器、CLI/REPL、结构化诊断和有界执行。
- **Canonical IR 与 VM：** 可选的 Python bytecode VM 在 Canonical IR 上执行；默认兼容路径仍为树遍历执行。
- **模块系统：** 版本化 `.rpr` 导入/导出、隔离作用域、导出缓存、依赖图检查和循环诊断。
- **静态分析：** 对现有 AST 子集进行保守类型推断。模块和宿主边界的未知值仍为 `Any`；这还不是完整且可靠的类型系统。
- **资源核算：** heap/打开文件配额、执行上限和确定性清理。这些是运行时防护措施，不是针对恶意程序的安全沙箱。
- **原生 C17 路线：** 部分 lexer/parser、自有 AST、受检 IR、优化器和有限 lowering。Scalar AOT 子集可为已安装的 GCC/Clang 兼容工具链生成 C17；目前不具备参考运行时的完整功能。
- **架构注册表：** 覆盖九个层级的 66 个稳定架构概念，支持精确查询和有界依赖图验证。
- **开发工具：** Windows Studio 基础、stdio LSP/DAP 服务、Kora 辅助库和可选 NOO TAH 集成。NOO TAH 将 JavaScript 执行委托给官方 Node.js 运行时。
- **产品组合：** 参考运行时提供 18 个进程内产品服务。Jora 目录包和 framework 描述不会自动成为可安装应用。

Embedded 工作台可创建和检查 MCU 参考项目，并调用用户自行安装的工具链。它不提供内置固件烧录或实时硬件调试。MMIO 描述符通过宿主提供的总线进行验证，不会映射物理内存。

## 构建与测试

要求：参考运行时需要 Python 3.10+；原生路线需要 CMake 3.16+ 和 C17 编译器；可选兼容性测试需要 Node.js 22/24；Windows Studio GUI 需要 Tkinter。

~~~sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DREAPER_BUILD_TESTS=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
~~~

CTest 会运行原生 C 测试；检测到 Python 解释器时，也会运行额外的参考运行时和仓库验证测试。

启动 REPL 或已安装的 Studio：

~~~sh
python -m reaper --repl
reaper-studio
~~~

## 集成与信任边界

- OPlague 设备快照以版本化 JSON 导入，并进行离线比较。
- Pytyliki C ABI 调用必须显式启用，并由调用方选择可信且 ABI 兼容的库。
- VentuSample 通过 manifest 交换素材包：Reaper 只读取声明的元数据，不修改 WAV 资产。
- OCTA-8 联邦记录对等契约，不会创建中心运行时或授予额外权限。

文件系统、进程、网络、时钟、shell 和原生库等副作用必须保持显式或 opt-in。原生 FFI 会在当前进程中执行代码，因此只能加载可信库。

## 文档

- [功能](docs/FEATURES.md) · [架构](docs/ARCHITECTURE.md)
- [原生编译器](docs/NATIVE_COMPILER.md) · [硬件语言](docs/HARDWARE_LANGUAGE.md)
- [运行时限制](docs/RUNTIME_PLATFORM.md) · [Kora 辅助库](docs/KORA.md)
- [Studio 与 IDE](docs/REAPER_IDE.md) · [Jora 工厂](docs/JORA_APPLICATION_FACTORY.md)
- [实现路线图](docs/IMPLEMENTATION_ROADMAP.md) · [文档索引](docs/README.md)
- [HARVEST Reaper 集成](docs/HARVEST_REAPER_INTEGRATION.md)
- [生态共享标准](https://github.com/Ivan-VHS/DAK/blob/main/docs/SHARED_STANDARDS.md)

## 贡献与许可证

修改语言语义、编译器阶段或公共契约前，请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。保持改动可审查，并添加确定性测试。安全问题请参阅 [SECURITY.md](SECURITY.md)。

本项目采用 [Apache-2.0](LICENSE) 许可证。第三方项目名称和商标归其各自权利人所有。

---
<p align="center"><sub>Reaper · README 审核 2026-11-27 UTC</sub></p>
