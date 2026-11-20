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

- **Python 参考运行时：** lexer、parser、解释器、CLI、REPL、模块、闭包、集合、资源跟踪、执行配额、可选字节码 VM、性能分析和哈希链审计；宿主注入的授权支持 HMAC 身份认证、作用域检查、有限 TTL 和撤销。
- **Reaper Studio：** Windows 编辑器，支持检查、运行、调试、断点、变量和调用栈查看。
- **原生 C17：** lexer、表达式解析器、自有 AST、受检整数 IR 操作和有限 lowering。尚不是完整解释器；Python 仍是兼容性参考。
- **МОСТ：** REAPER 0.1 的精确俄语关键字别名，复用相同 parser/runtime，不另建语义或运行时。
- **QCS 1.0：** 独立硬件语法 frontend，提供源码位置、frame parser、Pratt 表达式和 JSON AST；不替代 `.rpr`，也不执行硬件操作。命令：`reaper-qcs check examples/qcs_irq.qcs`。
- **THESIS 断言图：** 版本化断言、来源关联证据、时间与范围可比性检查、人工审核状态及追加式修订记录；不会自动判定断言为真（[设计说明](docs/THESIS_ASSERTION_GRAPH.md)）。
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

[THESIS 断言溯源图](docs/THESIS_ASSERTION_GRAPH.md)

[Anatidae UI/UX](docs/UI_UX_SYSTEM.md) · [12 项动画原则](docs/DISNEY_MOTION_SYSTEM.md) · [语言](LANGUAGE.md) · [QCS frontend](docs/QCS_FRONTEND.md) · [MOST 666 注册表](docs/MOST_FUNCTIONS_666.md) · [МОСТ 规范](docs/MOST_LANGUAGE_SPEC.md) · [运行时](docs/RUNTIME_PLATFORM.md) · [工程标准](docs/UNIFIED_ENGINEERING_STANDARD.md)


[治理与授权](docs/HUMAN_FIRST_GOVERNANCE.md) · [Anatidae 宪章](docs/ANATIDAE_CONSTITUTION.md) · [桌面设计系统](docs/ANATIDAE_DESKTOP_DESIGN_SYSTEM.md) · [UI/UX 架构](docs/UI_UX_ARCHITECTURE.md) · [12 项动效原则](docs/DISNEY_MOTION_SYSTEM.md) · [临床系统可靠性 CSR-120](docs/CLINICAL_SYSTEMS_CSR120.md) · [MOST 实现状态](docs/MOST_IMPLEMENTATION_STATUS.md) · [项目契约](docs/UNIFIED_PROJECT_CONTRACT.md)
[Windows 发布版](https://github.com/Ivan-VHS/Reaper/releases) · [桌面构建工作流](https://github.com/Ivan-VHS/Reaper/actions/workflows/desktop-build.yml)

## Anatidae 准则与语言保证

- **明确授权与可追责性：** 宿主注入的授权具有 HMAC 身份认证、作用域检查、有限有效期和撤销机制；审计记录使执行决策可检查。
- **有界执行：** 配额、资源记账和输入校验定义运行时边界。证明原生 C17 达到语义对等之前，Python 仍是兼容性参考实现。
- **单一规范语言契约：** МОСТ 别名共用 REAPER 规范符号、parser 和 runtime；QCS 是独立验证前端，不是硬件执行器。
- **如实标注实现状态：** MOST 666 注册表包含 147 项既有规格和 519 项提案，并不表示已有 666 个函数实现。原生 C17 lowering 仍不完整。
- **可信代码边界：** 进程内原生 FFI 会执行可信且 ABI 兼容的代码；它不是不可信扩展的沙箱。
- **无障碍工具与有目的的动效：** Studio 和编辑器集成应提供清晰的键盘与焦点行为、可读诊断、本地化及减少动态效果支持。动效应增强反馈，而不是遮蔽状态。

本准则用于指导工程决策，不会把路线图项目包装成已实现的运行时功能。

## 许可证

[Apache License 2.0](LICENSE)
