# Reaper — 面向数据流的编程语言

<p align="center">
  <a href="https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml/badge.svg"></a>
  <img alt="Python 3.10+" src="https://img.shields.io/badge/reference-runtime-Python%203.10%2B-2563EB?style=flat-square">
  <img alt="C17" src="https://img.shields.io/badge/native-track-C17-DC2626?style=flat-square">
  <img alt="Apache 2.0" src="https://img.shields.io/badge/license-Apache--2.0-334155?style=flat-square">
</p>

**Reaper 是一门以可读语法和显式数据流为核心的表达式语言。** `::` 运算符将当前值传递给下一步操作。仓库包含 Python 参考解释器、正在开发的原生 C17 核心，以及面向 Windows 的 Reaper Studio。

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

## 语言示例

```reaper
craft double(value) {
    yield value * 2
}
make numbers := [1, 2, 3, 4]
make answer := numbers :: map(double) :: sum()
emit "answer = " ++ text(answer)
```

## Studio 预览

<p align="center"><img src="assets/reaper-terminal-preview.svg" alt="Reaper 命令行会话示意预览" width="100%"></p>
<sub>根据仓库示例渲染的预期输出，并非真实运行的终端或桌面截图。尚未提交 Reaper Studio 实机截图。</sub>

## 已实现功能

- **参考运行时：** Python 3.10+、词法分析器、解析器、tree-walking 解释器、CLI、REPL 和标准库测试。
- **语言核心：** Unicode 标识符、函数/闭包、递归、不可变 `make`、通过显式 `change` 修改的 `vary`、条件、迭代和数据流组合。
- **集合与度量：** map/filter/fold/reduce、排序、切片、展平、UTF-8 工具、向量范数/距离、投影、二次型和几何运算。
- **模块与资源：** `.rpr` 导入/导出、依赖图、循环诊断、资源账本、LIFO 区域、有界文件句柄及确定性清理。
- **执行与审计：** 可选 Python 字节码 VM、执行配额、JSON、性能分析和哈希链审计日志。
- **Reaper Studio：** Windows 编辑器，支持打开/保存、检查、运行、断点、单步/继续/停止、变量查看和调用栈。
- **Embedded C 与互操作：** 项目脚手架、MCU 配置检查、内存预算，以及连接可信库的可选 C ABI（包括 Pytyliki ABI v1）。
- **扩展系统：** 本地 Polyglot；666 个保留词元；66 个语言/工具链配置；14 个架构配置；MOST 20×20 矩阵含 400 个已定义投影，并配有已实现的完整性验证器（投影并非 400 项可执行语言功能）。
- **МОСТ：** REAPER 0.1 的精确俄语关键字别名。它复用同一 parser、AST 和 runtime；Python 参考实现执行有限子集，C17 词法分析器提供 REAPER 规范关键字名称。没有独立语法、形态分析器、类型系统或运行时。

原生 C17 路线包含词法分析器、表达式解析器、自有 AST、经过检查的整数 IR 运算、有限 lowering、优化器测试和初始 CLI，**尚不是完整解释器**。自举 lexer/parser 仍处于分阶段 bootstrap。

## 运行参考解释器

需要 Python 3.10+，运行时无需第三方依赖。

```bash
git clone https://github.com/Ivan-VHS/Reaper.git
cd Reaper
python -m reaper examples/hello.rpr
python -m reaper examples/flow.rpr
python -m reaper --check examples/flow.rpr
python -m reaper --engine vm examples/flow.rpr
python -m reaper --repl
python -m unittest discover -s tests -v
```

使用 `python -m pip install -e .` 安装 CLI。在 Windows 上运行 Studio：`python reaper_desktop.py`。

## 构建原生 C17 核心

需要 CMake 和支持 C17 的编译器。

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
ctest --test-dir build --output-on-failure
./build/reaper-c --tokens examples/hello.rpr
```

## 项目演进与边界

语言初始基础于 2026 年 11 月 17 日提交，包含词法分析器、解析器、解释器和 CLI。之后 main 分支加入模块、执行限制、VM、Studio、Polyglot、Embedded C、部分 C17/自举路线和经验证的 MOST 20×20 架构矩阵。

托管堆只是基于 Python 分配器的记账层，不是物理分配器或 RSS 限制。原生 FFI 需显式启用，并会在进程内加载可执行代码；只使用可信且 ABI 兼容的库。工具链发现只检查 `PATH`，不会安装编译器。证明原生功能对等之前，Python 仍是参考实现。

## 文档与下载

[语言说明](LANGUAGE.md) · [运行时平台](docs/RUNTIME_PLATFORM.md) · [自举计划](docs/SELF_HOSTING_BOOTSTRAP.md) · [词元目录](docs/TOKEN_CATALOG.md) · [Embedded C](docs/EMBEDDED_C_WORKBENCH.md) · [MOST 矩阵](docs/MOST_400_COMBINATORIAL_MATRIX.md) · [工程标准](docs/UNIFIED_ENGINEERING_STANDARD.md) · [МОСТ 别名规范](docs/MOST_LANGUAGE_SPEC.md) · [66 条俄语可读性规则](docs/MOST_RUSSIAN_66_RULES.md)

[Windows 发布版](https://github.com/Ivan-VHS/Reaper/releases) · [桌面构建工作流](https://github.com/Ivan-VHS/Reaper/actions/workflows/desktop-build.yml)

## 许可证

[Apache License 2.0](LICENSE)