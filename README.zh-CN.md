# Reaper — 面向数据流的编程语言

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

**Reaper 是一种表达式导向语言，强调清晰语法和显式数据流。** 运算符 `|>` 将左侧值传递给后续操作。仓库目前包含 Python 参考解释器，以及正在开发的原生 C17 实现。

## 示例

```reaper
craft double(value) {
    yield value * 2
}
make numbers := [1, 2, 3, 4]
make answer := numbers |> map(double) |> sum()
emit "answer = " ++ text(answer)
```

## 当前实现

- **Python 参考运行时：** Python 3.10+、树遍历解释器、词法分析器、解析器、运行时、CLI 和标准库测试。
- **语言核心：** Unicode 标识符、注释、字符串、函数与闭包、递归、不可变绑定 `make`、通过显式 `change` 修改的 `vary`、条件、循环和数据流组合。
- **内置操作与诊断：** 集合操作、显式类型转换、带源码位置的词法/解析/运行时错误，以及执行配额。
- **原生 C17 路线：** lexer、表达式解析器和自有 AST、经过验证的整数 Canonical IR、受检常量折叠、有限 AST-to-IR lowering、CLI bring-up 模式和 C 测试。
- **MOST 路线：** 已文档化的语言词汇和分阶段实现规范。

C 实现目前还不是完整解释器。完整声明与代码块、类型检查、intent 解析、ownership 分析、原生代码生成和 WASM 尚未实现。在运行时与 CLI 达到经过验证的兼容性之前，Python 仍是参考实现。

## 截图

当前项目是语言与运行时工程，并非图形桌面应用。仓库尚无经过验证的实时终端截图，因此已移除示意终端图片，不将其冒充为真实截屏。可通过下方示例命令查看实际输出。

## 运行 Python 解释器

要求 Python 3.10 或更新版本；运行时不依赖第三方软件包。

```bash
git clone https://github.com/Ivan-VHS/Reaper.git
cd Reaper
python -m reaper examples/hello.rpr
python -m reaper examples/flow.rpr
python -m reaper --check examples/flow.rpr
python -m unittest discover -s tests -v
```

以 editable 模式安装 CLI：

```bash
python -m pip install -e .
reaper examples/hello.rpr
```

## 构建原生 C17 核心

要求 CMake 和支持 C17 的编译器。

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
ctest --test-dir build --output-on-failure
./build/reaper-c --tokens examples/hello.rpr
./build/reaper-c --evolution-status
```

当前原生可执行文件提供已实现的 bring-up 与分析功能，并非 Python 解释器的完整替代品。

## 设计与安全边界

程序经过词法分析、AST 解析，并由受限解释器执行。控制台副作用通过 `emit`、`say` 和 `ask` 等操作显式表达。普通表达式不会自动获得文件系统、网络、时钟、进程、shell 或硬件访问权限。

默认配额包括 1,000,000 个执行步骤、256 层嵌套调用、100,000 个集合元素和 1,000,000 个文本拼接字符。这些是资源限制，**不是安全沙箱**。不要认为运行不可信程序时主机环境已被隔离。

## 文档

- [语言参考](LANGUAGE.md)
- [REAPER/MOST 统一架构](docs/REAPER_UNIFIED_ARCHITECTURE.md)
- [架构](docs/ARCHITECTURE.md)
- [MOST 语言规范](docs/MOST_LANGUAGE_SPEC.md)
- [C 迁移计划](docs/C_MIGRATION.md)
- [示例](examples/) · [测试](tests/)

## CI 与许可证

GitHub Actions 测试 Python 3.10、3.11 和 3.12，运行单元测试、检查示例并执行 flow 示例。原生 C 核心另有 CMake/CTest 测试。

[Apache License 2.0](LICENSE)。

> 千里之行，始于足下。
