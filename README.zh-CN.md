# Reaper — 流式组合编程语言

[CI](https://github.com/Ivan-VHS/Reaper/actions/workflows/ci.yml) · [Windows Studio 构建](https://github.com/Ivan-VHS/Reaper/actions/workflows/desktop-build.yml) · Python 3.10+ 参考运行时 · C17 原生开发线 · Windows Studio · Apache-2.0
**开发者：** [Ivan-VHS](https://github.com/Ivan-VHS)

Reaper 是表达式导向的数据流语言；操作符 `::` 将值传递给下一项操作。Python runtime 是当前可执行的兼容性参考实现。C17 原生实现仍在开发中，尚不能完全替代 Python runtime。

## Reaper Studio 实际运行截图

<p align="center"><img src="assets/screenshots/reaper-studio.png" alt="Windows 11 中运行的 Reaper Studio" width="100%"></p>
<sub>启用 Node.js 的 Studio 构建在 Windows 11 上的真实截图，1920×1080。</sub>

## 当前能力矩阵

| 模块 | 已实现范围与边界 |
|---|---|
| Python runtime | lexer、parser、解释器、CLI、REPL、模块、closures、quotas 和 audit |
| Reaper Studio | Windows IDE 基础：项目树、编辑器、语法高亮、行号、搜索、check/run 和调试器 |
| LSP | stdio 服务：增量 UTF-16 文档、parser/structure 诊断、completion、hover、symbols 和词法导航；按打开的文档工作，不提供跨文件类型推断 |
| DAP | stdio 调试适配器：启动、行断点、语句级单步、调用栈和局部变量 |
| 除法与分配 | 经检查的欧几里得除法、均衡工作分区和按比例分配 |
| Atomic-Quantum 133 | 133 个操作 ID；8 个经过审查的经典模拟内核；其余条目仅列入目录 | 最多 10 个量子比特的有界状态向量模型；不访问量子硬件 |
| NOO TAH | 官方 Node.js 集成：V8/libuv、ESM/CommonJS、核心 API、streams、workers、npm/npx、N-API 和 Inspector；Studio 支持 JS Run/Check/Debug/Stop 与 npm 命令 |
| 内置插件宿主 | 18 个内置服务，具有生命周期状态和有界 dispatch；Python 参考运行时 |
| Kora | 七个带 manifest 模块中的 66 个标准工具函数；三个用于 Cockos REAPER 的 Lua ReaScript |
| Native C17 | lexer、表达式 parser、owned AST、checked IR 和有限 lowering；尚未与 Python runtime 完全对等 |
| МОСТ | 54 个精确别名：当前参考子集中 21 个可执行，33 个仅作词法保留 |
| QCS 1.0 | 独立硬件领域 parser 和 JSON AST；不执行硬件操作 |
| THESIS | 类型化证据图；不会自动验证其中的声明 |
| 注册表 | 813 项功能提案、666 个 API 合同和 666 个保留词素；注册表条目不代表功能已完成 |
| 联邦集成 | OPlague snapshots、VentuSample manifests 和可选 Pytyliki C ABI |

## 界面动效与无障碍

Reaper Studio 将 **Reduce Motion** 与 **Eco / Low-CPU Visuals** 偏好设置独立于主题设置保存。启用后，保留的过渡不超过 80 ms，并抑制空间移动和非必要视觉效果。由于 Studio 目前没有音频传输或节拍源，**Sync to Transport / BPM** 保持禁用。详见 [界面动效规范](docs/UI_MOTION.md)。

## CODEX-66 IDE 工作台

Reaper Studio 新增原生 **CODEX-66** 功能目录，包含六组、每组十一项，可按 ID、名称、类别和成熟度搜索。按 **Ctrl+Space** 打开本地 REAPER 补全，按 **F12** 跳转到当前文档中的定义，使用 **Find references** 查找词法引用，按 **Ctrl+Shift+R** 在当前文档中重命名。**Ctrl+K** 打开命令面板。

目录会明确区分已实现、部分实现、计划中和不支持的项目。本地补全复用语言服务，并非云端 AI；引用查找和重命名仅作用于当前文档；解释器也不是操作系统级沙箱。详见 [CODEX-66 实现与能力边界](docs/CODEX_66_SHOWCASE.md)。

## REAPER 语言与调试服务

编辑器工具层提供 stdio 协议服务：

```sh
python -m reaper lsp
python -m reaper dap
```

安装入口为 `reaper-lsp` 和 `reaper-dap`。LSP 提供按文档增量更新的语言功能；DAP 用于调试 Reaper 程序。这些服务复用规范的 Python parser/runtime，并不意味着完整的 C17 对等、跨文件语义分析或已打包的 VS Code 客户端。

详细能力边界见 [REAPER IDE 架构](docs/REAPER_IDE.md)。

## NOO TAH — Node.js 运行时

NOO TAH 管理官方跨平台 Node.js 发行版，而不是重新实现其引擎。V8、libuv、核心模块、ESM/CommonJS、streams、workers、child processes、npm/npx、N-API 和 Inspector 均由所选 Node 发行版提供。

Reaper Studio 可识别 `.js`、`.mjs` 和 `.cjs` 项目，并提供 JS Run、JS Check、通过 Node Inspector 进行的 JS Debug、JS Stop、npm 命令和运行时诊断。Node Inspector 尚未映射到原生 DAP 调试器面板。

```sh
reaper-noo-tah version
reaper-noo-tah doctor
reaper-noo-tah run app.mjs
reaper-noo-tah check app.js
reaper-noo-tah npm run build
node --test tests/noo_tah/conformance.test.mjs
```

当前兼容性测试覆盖运行时元数据、ESM/CommonJS、文件 I/O、crypto、streams/backpressure、loopback HTTP/TCP、workers、child processes、DNS 和 event loop 顺序。CI 矩阵使用 Node 22 与 24，目标平台为 Windows、Linux 和 macOS。详见 [NOO TAH 架构](docs/NOO_TAH.md)。

## Kora 与 Cockos REAPER 应用

Kora 在 ZDORO、DILLY、BAPLAP、KALI、PYEMONT、LIUR 和 SRETUO 七个模块中提供 66 个标准工具函数。仓库还包含三个 Lua ReaScript：

- **Track Health Dashboard** — 只读项目和轨道诊断。
- **Prefix Selected Tracks** — 在一个可撤销操作中重命名所选轨道。
- **Marker and Region Report** — 在 ReaScript 控制台输出标记和区域列表。

在 Cockos REAPER 中打开 **Actions → Show action list → ReaScript → Load**，选择 `reaper_scripts/kora/` 中的脚本。这些脚本由 REAPER 自身托管，不是编译后的 VST/AU/CLAP 效果器，也不需要启动 Node.js 进程。详见 [Kora for REAPER](docs/KORA_REAPER.md)。

## Atomic-Quantum 133

Python 参考运行时提供 133 个稳定操作 ID，分为六类：状态、纠缠、测量、噪声/ECC、原子动力学以及算法/遥测。目前只有 8 个经过审查的内核提供有界、确定性的经典模拟；其余条目明确标记为 **catalogued-only**，不宣称已实现。状态向量模型最多支持 10 个量子比特，并验证振幅有限性与归一化，支持带 seed 的确定性测量。系统不会发现、校准或控制量子硬件；C17 路线也不代表量子硬件执行。详见 [Atomic-Quantum 133 合约](docs/ATOMIC_QUANTUM_133.md)。

## 运行、测试与构建

```sh
python -m reaper examples/flow.rpr
python -m reaper --check examples/flow.rpr
python -m reaper --engine vm examples/flow.rpr
python -m reaper --repl
python -m unittest discover -s tests -v
```

Windows Studio：`python reaper_desktop.py`。

C17 原生开发线：

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

示例：

```reaper
craft double(value) { yield value * 2 }
make result := [1, 2, 3] :: map(double) :: sum()
emit "result = " ++ text(result)
```

[IDE 666 合同](docs/IDE_666_IMPLEMENTATION.md) · [LSP/DAP](docs/REAPER_IDE.md) · [Node.js 集成](docs/NOO_TAH.md) · [Kora for REAPER](docs/KORA_REAPER.md) · [插件宿主](docs/PLUGINS.md) · [内部产品](docs/INTERNAL_PRODUCTS.md) · [功能](docs/FEATURES.md) · [语言](LANGUAGE.md) · [架构](docs/ARCHITECTURE.md) · [813 注册表](docs/REAPER_813_FEATURE_ARCHITECTURE.md) · [联邦](docs/PROJECT_FEDERATION_MATRIX.md) · [文档索引](docs/README.md)

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [Releases](https://github.com/Ivan-VHS/Reaper/releases) · [Apache-2.0](LICENSE)


## Motion Constitution v2026

跨项目界面规范见 [Motion Constitution v2026](docs/MOTION_CONSTITUTION_V2026.md)。它统一弹簧/快速缓动、0.4×–2.2× 动效缩放范围、Reduce Motion 优先级、主题一致性、2×2/焦点场景展示及真实 SVG/Canvas 遥测规则。[原生界面动效规范](docs/UI_MOTION.md)说明 Reaper Studio 当前提供的功能：有界 Tk 弹簧过渡、持久化无障碍偏好，以及本地 IDE/LSP/DAP 工具。CODEX-66 和本地语言服务不是云端 AI Agent，也不提供流式 AI Diff；规划中的展示面板不得描述为已交付功能。
