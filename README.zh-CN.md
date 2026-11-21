# Reaper — 流式组合编程语言

Python 3.10+ · C17 原生开发线 · Windows Studio · Apache-2.0 · [CI](https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml)

Reaper 是表达式导向的数据流语言；`::` 将值传递给下一操作。Python 是当前参考解释器；C17 原生实现仍在开发中，尚不能完全替代 runtime。

## Studio 实际运行截图

<p align="center"><img src="assets/screenshots/reaper-studio.png" alt="Windows 中运行的 Reaper Studio" width="100%"></p>
<sub>Windows 11 实际应用截图，1920×1080。</sub>

| 模块 | 当前边界 |
|---|---|
| Python runtime | lexer、parser、解释器、CLI、REPL、模块、closures、quotas、audit |
| Reaper Studio | Windows 编辑器：check/run/debug、breakpoints、variables、call stack |
| Native C17 | lexer、表达式 parser、owned AST、checked IR、有限 lowering |
| МОСТ | 54 个精确俄语别名：21 个在参考子集中可执行，33 个保留 |
| QCS 1.0 | 独立硬件领域 parser 和 JSON AST；不执行硬件操作 |
| THESIS | 证据图；不会自动验证声明 |
| 注册表 | 813 个提案；666 个 API 合同；目录条目不代表已实现功能 |
| 联邦 | OPlague snapshots、VentuSample manifests、可选 Pytyliki C ABI |

运行：`python -m reaper examples/flow.rpr` · 检查：`python -m reaper --check examples/flow.rpr` · 测试：`python -m unittest discover -s tests -v`。

Studio：`python reaper_desktop.py`（Windows）。Native：CMake configure、build、CTest。

[功能矩阵](docs/FEATURES.md) · [语言](LANGUAGE.md) · [架构](docs/ARCHITECTURE.md) · [813 注册表](docs/REAPER_813_FEATURE_ARCHITECTURE.md) · [联邦](docs/PROJECT_FEDERATION_MATRIX.md) · [文档索引](docs/README.md)

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [Releases](https://github.com/Ivan-VHS/Reaper/releases) · [Apache-2.0](LICENSE)
