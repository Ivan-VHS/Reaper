# Reaper — 面向数据流的编程语言

<p align="center">
  <a href="https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml/badge.svg"></a>
  <img alt="Python 3.10+" src="https://img.shields.io/badge/reference-runtime-Python%203.10%2B-2563EB?style=flat-square">
  <img alt="C17" src="https://img.shields.io/badge/native-track-C17-DC2626?style=flat-square">
  <img alt="Apache 2.0" src="https://img.shields.io/badge/license-Apache--2.0-334155?style=flat-square">
</p>

**Reaper 是一门以可读语法和显式数据流为核心的表达式语言。** `::` 运算符将当前值传递给下一步操作。仓库包含 Python 参考解释器、开发中的原生 C17 核心，以及面向 Windows 的 Reaper Studio。

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

## 示例

```reaper
craft double(value) {
    yield value * 2
}
make numbers := [1, 2, 3, 4]
make answer := numbers :: map(double) :: sum()
emit "answer = " ++ text(answer)
```

## 功能

- **Python 参考运行时：** lexer、parser、解释器、CLI、REPL、模块、闭包、集合、资源跟踪、执行配额、可选字节码 VM、性能分析和哈希链审计。
- **Reaper Studio：** Windows 编辑器，支持检查、运行、调试、断点、变量和调用栈查看。
- **原生 C17：** lexer、表达式解析器、自有 AST、受检整数 IR 操作和有限 lowering。尚不是完整解释器；Python 仍是兼容性参考。
- **МОСТ：** REAPER 0.1 的精确俄语关键字别名，复用相同 parser/runtime，不另建语义或运行时。
- **QCS 1.0：** 独立硬件语法 frontend，提供源码位置、frame parser、Pratt 表达式和 JSON AST；不替代 `.rpr`，也不执行硬件操作。命令：`reaper-qcs check examples/qcs_irq.qcs`。
- **MOST 666 注册表：** 666 项 API 合约（147 项既有规格 + 519 项提案），含 source inventory 和验证器。这是规格目录，并非 666 个已实现函数。
- **系统与互操作：** Embedded C、MCU 配置和内存预算；可选 Pytyliki C ABI v1；66 个语言/toolchain 条目、14 个架构配置和已验证的 MOST 20×20 矩阵。

## 运行参考解释器

需要 Python 3.10+，运行时无需第三方依赖。

```bash
git clone https://github.com/Ivan-VHS/Reaper.git
cd Reaper
python -m reaper examples/flow.rpr
python -m reaper --check examples/flow.rpr
python -m reaper --engine vm examples/flow.rpr
python -m reaper --repl
python -m pip install -e .
python -m unittest discover -s tests -v
```

Windows 上运行 Studio：`python reaper_desktop.py`。

## 构建 C17 核心

需要 CMake 和支持 C17 的编译器。

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
ctest --test-dir build --output-on-failure
./build/reaper-c --tokens examples/hello.rpr
```

## 架构边界

证明原生语义对等之前，Python 仍是参考实现。托管堆只是 Python 分配器的记账层，不是物理分配器或 RSS 限制。原生 FFI 会在进程内运行可信 ABI 兼容代码。工具链发现只检查 `PATH`，不会安装编译器。МОСТ 名称解析到规范 REAPER 符号；QCS 解析不证明硬件契约。

## 文档

[Anatidae UI/UX](docs/UI_UX_SYSTEM.md) · [12 项动画原则](docs/DISNEY_MOTION_SYSTEM.md) · [语言](LANGUAGE.md) · [QCS frontend](docs/QCS_FRONTEND.md) · [MOST 666 注册表](docs/MOST_FUNCTIONS_666.md) · [МОСТ 规范](docs/MOST_LANGUAGE_SPEC.md) · [运行时](docs/RUNTIME_PLATFORM.md) · [工程标准](docs/UNIFIED_ENGINEERING_STANDARD.md)

[Windows 发布版](https://github.com/Ivan-VHS/Reaper/releases) · [桌面构建工作流](https://github.com/Ivan-VHS/Reaper/actions/workflows/desktop-build.yml)

## 许可证

[Apache License 2.0](LICENSE)
