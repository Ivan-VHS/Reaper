# Reaper — 面向数据流的编程语言

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

**Reaper 是一种表达式导向语言，强调清晰语法和显式数据流。** 运算符 `::` 将左侧值传递给后续操作。仓库目前包含 Python 参考解释器，以及正在开发的原生 C17 实现。

## 示例

```reaper
craft double(value) {
    yield value * 2
}
make numbers := [1, 2, 3, 4]
make answer := numbers :: map(double) :: sum()
emit "answer = " ++ text(answer)
```

## 666 个符号词元目录

Reaper 包含一个规范的 666 项符号词汇表：每个词素由允许字母表 `: ; [ { ] } + = _ - *` 中的三个字符组成，不含数字且保持唯一。Python 与原生 C 词法分析器会识别这些保留码；可用 `reaper --catalog`、`reaper --catalog-group memory` 或 `reaper --catalog-token ':::'` 查看。保留词汇尚不代表对应操作已可执行。参见[令牌目录](docs/TOKEN_CATALOG.md)。

## 当前实现

- **Python 参考运行时：** Python 3.10+、树遍历解释器、词法分析器、解析器、运行时、CLI 和标准库测试。
- **语言核心：** Unicode 标识符、注释、字符串、函数与闭包、递归、不可变绑定 `make`、通过显式 `change` 修改的 `vary`、条件、循环和数据流组合。
- **内置操作与诊断：** 集合操作、显式类型转换、带源码位置的词法/解析/运行时错误，以及执行配额。
- **原生 C17 路线：** lexer、表达式解析器和自有 AST、经过验证的整数 Canonical IR、支持 signed i64 加减乘除的受检常量折叠（拒绝溢出与除零）、有限 AST-to-IR lowering、CLI bring-up 模式和 C 测试。
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

## 原生桌面应用

**Reaper Studio** 是基于现有 Python 参考运行时的 Windows x64 桌面工作台：编辑 `.rpr` 文件、打开和保存源代码、语法检查、运行程序并查看输出与错误。C17 核心仍在独立开发中；目前不宣称 C 运行时已完全兼容。

- [Windows x64 Releases](https://github.com/Ivan-VHS/Reaper/releases)
- [桌面构建工作流与 CI 工件](https://github.com/Ivan-VHS/Reaper/actions/workflows/desktop-build.yml)
- [最新构建运行](https://github.com/Ivan-VHS/Reaper/actions/workflows/desktop-build.yml?query=branch%3Amain)

成功运行会上传 `Reaper-Studio-windows-x64.zip`；`v*` 标签会发布 GitHub Release。Windows + Python 3.10+ 源码启动命令：`python reaper_desktop.py`。

## 多语言沉浸学习系统

Reaper 的 Python 参考实现现已加入本地优先的语言学习子系统：多语言档案、离线文本与字幕库、带上下文的短语卡片、间隔重复、每日自适应计划、可理解度估算、学习记录和 JSON 导出。

```sh
reaper polyglot init English --native Russian --level A0 --minutes 45
reaper polyglot content add lesson.srt --kind dialogue --level A1
reaper polyglot phrase add "Could you say that again?" --translation "能再说一遍吗？" --context "礼貌地请求对方重复"
reaper polyglot plan
reaper polyglot review
reaper polyglot report
```

数据保存在本地 SQLite 数据库中。

语言档案还会保存文字系统默认/覆盖设置、声调语言指导、发音重点和临时罗马化辅助。短语卡片支持个人例句及由学习者提供的可选词频排名；学习报告会显示粗略的累计练习阶段。这些只是学习辅助信息，并非语言水平预测。70–90% 区间只是根据已复习短语卡片估算的词元覆盖率，并非自动理解测试。媒体播放、语音识别/合成、自动翻译和 AI 发音评分尚未实现。详见[多语言沉浸学习指南](docs/POLYGLOT_IMMERSION.md)。

## 设计与安全边界

程序经过词法分析、AST 解析，并由受限解释器执行。控制台副作用通过 `emit`、`say` 和 `ask` 等操作显式表达。普通表达式不会自动获得文件系统、网络、时钟、进程、shell 或硬件访问权限。

默认配额包括 1,000,000 个执行步骤、256 层嵌套调用、100,000 个集合元素和 1,000,000 个文本拼接字符。这些是资源限制，**不是安全沙箱**。不要认为运行不可信程序时主机环境已被隔离。

## 自举前端：已验证的部分实现

Reaper 已开始执行由 Reaper 自身编写的前端逻辑，但**目前还不是自举编译器**。

- **Stage 0 词法分析器：** selfhost/lexer.rpr 扫描当前支持的、以 ASCII 为主的词法子集，并生成带源码位置的 token 记录。与 Python lexer 的 Unicode 标识符兼容性仍待完成。
- **Stage 1 Pratt 表达式解析器：** selfhost/parser.rpr 解析字面量、名称、一元与分组表达式、列表、函数调用、索引和中缀运算符。优先级表包含流运算符 :: 和右结合的幂运算符（**）。
- **参考实现：** Python parser 和 AST 仍是兼容性基准。Reaper 编写的解析器返回阶段性的数组表示；声明与语句语法以及规范 AST 一致性尚未实现。

运行专项 bootstrap 测试：

~~~bash
python -m unittest discover -s tests -p 'test_self_hosting.py' -v
~~~

参见 [自举阶段契约](docs/SELF_HOSTING_BOOTSTRAP.md)、[Reaper 编写的解析器](selfhost/parser.rpr) 和 [Reaper 编写的词法分析器](selfhost/lexer.rpr)。功能只在测试覆盖的范围内视为已实现；仅有源文件并不代表阶段完成。

## 文档

- [语言参考](LANGUAGE.md)
- [多语言沉浸学习系统](docs/POLYGLOT_IMMERSION.md)
- [REAPER/MOST 统一架构](docs/REAPER_UNIFIED_ARCHITECTURE.md)
- [架构](docs/ARCHITECTURE.md)
- [MOST 语言规范](docs/MOST_LANGUAGE_SPEC.md)
- [C 迁移计划](docs/C_MIGRATION.md)
- [示例](examples/) · [测试](tests/)

## CI 与许可证

GitHub Actions 测试 Python 3.10、3.11 和 3.12，运行单元测试、检查示例并执行 flow 示例。原生 C 核心另有 CMake/CTest 测试。

[Apache License 2.0](LICENSE)。

> 千里之行，始于足下。


## Canonical IR 中经过检查的整数运算

原生 IR 支持 i64 加法、减法、乘法和除法。只有两个操作数均为常量时才执行常量折叠；signed i64 溢出、除零和 INT64_MIN / -1 会返回诊断。Fixed-point 流程限制为 1–64 次迭代，并在每次转换前后验证 IR。这是 IR 层能力，不代表 C 前端或运行时已达到完整功能对等。


## 项目生态

本仓库属于由三个独立项目组成的协作体系。Reaper 负责编程语言、运行时与工作流编排；OPlague 负责只读 Windows 设备清单和驱动程序包检查；Pytyliki 负责基于 C11 的处理器、内存与数值计算核心。 See the [3 × 3 项目协作矩阵](https://github.com/Ivan-VHS/Reaper/blob/main/docs/PROJECT_FEDERATION_MATRIX.md) for the 3 × 3 cross-product, implemented interfaces, data directions and safety boundaries.

- [Reaper — 编程语言、运行时与工作流编排](https://github.com/Ivan-VHS/Reaper/blob/main/README.zh-CN.md) · [integration contract](https://github.com/Ivan-VHS/Reaper/blob/main/docs/FEDERATED_INTEGRATION.md)
- [OPlague — 只读 Windows 设备清单与驱动程序包检查](https://github.com/Ivan-VHS/OPlague/blob/main/README.zh-CN.md) · [integration contract](https://github.com/Ivan-VHS/OPlague/blob/main/docs/FEDERATED_INTEGRATION.md)
- [Pytyliki — C11 处理器、内存与数值计算核心](https://github.com/Ivan-VHS/Pytyliki/blob/main/README.zh-CN.md) · [integration contract](https://github.com/Ivan-VHS/Pytyliki/blob/main/docs/FEDERATED_INTEGRATION.md)
