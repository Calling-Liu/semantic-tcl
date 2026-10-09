# semantic-tcl

`semantic-tcl` 是基于 Semantica `v0.7.0` 的工程知识库增强版本，重点面向大型 Java/Kotlin/Android 项目。

本项目不是重新声明 Semantica 的原创归属。原始项目、协议和上游更新来源如下：

- 原项目：https://github.com/semantica-agi/semantica
- 当前 Fork：https://github.com/Calling-Liu/semantic-tcl
- 基线 Tag：`v0.7.0`
- 当前版本：`0.7.0+tcl.1`
- License：MIT，保留原项目 License 和历史提交

## 这个版本增加了什么

在原 Semantica 的 Context Graph、Explorer、Provenance 和决策能力之上，本 Fork 增加了 Git 原生项目知识库工具：

- 从不可变 Git Commit 读取源码，不直接依赖工作目录内容。
- 可处理工作树被 TSD 等机制加密、但 Git Object 中保留明文的项目。
- Java 类型、方法和基础静态调用关系。
- Kotlin 类型和方法声明关系。
- Gradle 模块及模块依赖。
- AIDL 接口和方法。
- Android Manifest 组件注册。
- ProGuard/R8 Keep 规则。
- SQLite 完整事实索引。
- Semantica Context Graph 局部审计图。
- 只读 MCP 查询服务。
- Explorer 可视化。

命令入口：

```text
semantica-project-kb
```

## 环境要求

推荐环境：

```text
Windows 10/11
Git
Python 3.12
Node.js 20+
npm
uv
Codex CLI，可选
```

如果访问 GitHub、npm 或 Python 包仓库需要代理，可以设置：

```powershell
$env:HTTP_PROXY = "http://127.0.0.1:7897"
$env:HTTPS_PROXY = "http://127.0.0.1:7897"
```

## 1. 克隆源码

```powershell
git clone https://github.com/Calling-Liu/semantic-tcl.git D:\project\semantic
cd D:\project\semantic
git checkout atomicservice-v0.7.0
```

配置上游仓库，便于后续同步官方更新：

```powershell
git remote add upstream https://github.com/semantica-agi/semantica.git
git fetch upstream --tags
```

如果 `upstream` 已存在，无需重复添加。

## 2. 一键本地编译

执行：

```powershell
cd D:\project\semantic
scripts\build-local.ps1
```

需要代理时：

```powershell
scripts\build-local.ps1 -Proxy "http://127.0.0.1:7897"
```

脚本会完成：

1. `npm ci` 安装 Explorer 锁定依赖。
2. `npm run build` 编译 Explorer 前端到 `semantica/static`。
3. 创建 Python 3.12 构建环境 `.build-venv`。
4. 本地构建 Wheel。
5. 创建干净运行环境 `.venv`。
6. 安装本地 Wheel 及 `explorer`、`project-kb` 依赖。
7. 验证版本和 `semantica-project-kb` 命令。
8. 输出 Wheel SHA256。

生成产物：

```text
D:\project\semantic\dist\semantica-0.7.0+tcl.1-py3-none-any.whl
```

## 3. 手工编译步骤

如果不使用脚本，可以逐步执行。

### 3.1 编译 Explorer

```powershell
cd D:\project\semantic\explorer
npm ci
npm run build
```

前端产物写入：

```text
D:\project\semantic\semantica\static
```

### 3.2 构建 Python Wheel

```powershell
cd D:\project\semantic

uv venv .build-venv --python 3.12
uv pip install --python .build-venv\Scripts\python.exe `
  build setuptools==84.0.0 wheel==0.48.0

.build-venv\Scripts\python.exe -m build --wheel --no-isolation
```

### 3.3 安装本地 Wheel

```powershell
uv venv --clear .venv --python 3.12

uv pip install --python .venv\Scripts\python.exe `
  "semantica[explorer,project-kb] @ file:///D:/project/semantic/dist/semantica-0.7.0+tcl.1-py3-none-any.whl"

uv pip install --python .venv\Scripts\python.exe pytest
```

验证：

```powershell
.venv\Scripts\python.exe -c `
  "import semantica; print(semantica.__version__, semantica.__file__)"

.venv\Scripts\semantica-project-kb.exe --help
```

版本应为：

```text
0.7.0+tcl.1
```

## 4. 为项目创建知识库

下面以项目 `F:\project\ailauncherNew\temp\ai-launcher` 为例。

知识库建议放在目标项目外部，避免污染业务仓库：

```powershell
cd D:\project\semantic

.venv\Scripts\semantica-project-kb.exe build `
  --repo F:\project\ailauncherNew\temp\ai-launcher `
  --output D:\knowledge-bases\ai-launcher `
  --name ai-launcher `
  --revision HEAD `
  --roots JsthoController JsonDocumentHost LogicExecutor `
  --depth 3
```

参数说明：

| 参数 | 说明 |
| --- | --- |
| `--repo` | 目标 Git 仓库路径 |
| `--output` | SQLite、Graph 和 Manifest 输出目录 |
| `--name` | 项目名称 |
| `--revision` | Commit、Tag 或分支，默认 `HEAD` |
| `--roots` | Explorer 局部图的核心符号 |
| `--depth` | 从根符号向下展开的静态关系深度 |

生成目录：

```text
D:\knowledge-bases\ai-launcher\
├── project_kb.sqlite3
└── artifacts\
    ├── current.json
    └── <commit-sha>\
        ├── context_graph.json
        └── manifest.json
```

其中：

- `project_kb.sqlite3` 保存完整工程事实。
- `context_graph.json` 保存围绕根符号的可视化子图。
- `manifest.json` 保存 Snapshot、摘要和图谱统计。
- `current.json` 指向当前成功发布。

## 5. 查询知识库

### 项目摘要

```powershell
.venv\Scripts\semantica-project-kb.exe summary `
  --output D:\knowledge-bases\ai-launcher
```

### 查找符号

```powershell
.venv\Scripts\semantica-project-kb.exe find `
  --output D:\knowledge-bases\ai-launcher `
  JsthoController
```

### 影响分析

```powershell
.venv\Scripts\semantica-project-kb.exe impact `
  --output D:\knowledge-bases\ai-launcher `
  JsonDocumentHost
```

返回关系会明确区分：

- `STATIC`：Java 静态解析关系。
- `DECLARED`：Gradle、AIDL、Manifest 或 ProGuard 声明关系。
- `RESOLVED`：目标符号已确定。
- `UNRESOLVED`：存在引用，但不能可靠确定目标。

静态可达不等于设备上的真实运行路径。

## 6. 接入 Codex MCP

注册知识库：

```powershell
codex mcp add ai-launcher-kb -- `
  D:\project\semantic\.venv\Scripts\semantica-project-kb.exe `
  mcp `
  --output D:\knowledge-bases\ai-launcher
```

重新打开 Codex 会话，输入：

```text
/mcp
```

确认存在：

```text
ai-launcher-kb
```

之后直接用自然语言提问：

```text
请使用 ai-launcher-kb 查询 JsthoController 的定义和方法。
请使用 ai-launcher-kb 分析 JsonDocumentHost 的静态影响。
请使用 ai-launcher-kb 返回项目模块和语言统计。
```

MCP 工具：

```text
project_summary
find_symbol
analyze_impact
```

## 7. 启动 Explorer

读取当前 Manifest：

```powershell
$current = Get-Content D:\knowledge-bases\ai-launcher\artifacts\current.json | ConvertFrom-Json
$manifest = Get-Content $current.manifest | ConvertFrom-Json
$graph = $manifest.graph_path
```

启动：

```powershell
$env:PYTHONUTF8 = "1"
$env:SEMANTICA_ALLOW_ANONYMOUS = "true"

D:\project\semantic\.venv\Scripts\semantica-explorer.exe `
  --graph $graph `
  --host 127.0.0.1 `
  --port 8765
```

浏览器访问：

```text
http://127.0.0.1:8765
```

匿名模式只适合绑定 `127.0.0.1` 的本地开发，不要暴露到局域网或公网。

## 8. TSD 和受保护源码

项目知识库读取：

```text
Git Commit / Tag / Branch -> Git Object -> 明文解析
```

它不会把工作目录中的 `%TSD-Header-###%` 密文当作源码。

注意：

- 默认只分析已提交到 Git 的内容。
- 工作区未提交修改不会进入 `HEAD` Snapshot。
- 需要分析未提交修改时，先提交到临时分支，或指定一个已存在的 Commit。
- 知识库输出目录中包含符号、关系和源码路径，应按源码安全策略保护。

## 9. ai-launcher 实测结果

验证仓库：

```text
F:\project\ailauncherNew\temp\ai-launcher
Commit：730dd15fa8e4453eba5656f760bf03d83178b6ca
```

使用根符号：

```text
JsthoController
JsonDocumentHost
LogicExecutor
```

实测结果：

| 指标 | 数量 |
| --- | ---: |
| 模块 | 17 |
| Java 文件 | 494 |
| Kotlin 文件 | 76 |
| 符号 | 5261 |
| 工程实体 | 197 |
| 关系 | 18459 |
| AIDL 接口 | 2 |
| AIDL 方法 | 38 |
| Explorer 节点 | 298 |
| Explorer 边 | 196 |

本机完整构建约 10 秒。该时间只用于说明当前测试规模，不作为其他机器的性能承诺。

已验证：

- TSD 工作树不影响 Git Object 解析。
- `summary` 正常。
- Java `JsthoController` 查询正常。
- Kotlin `JsonDocumentHost` 查询正常。
- `impact` 正常。
- Context Graph 保存和加载正常。
- stdio MCP 正常。
- Explorer 正常加载。

## 10. 当前能力边界

- Java 使用 Javalang，提供类型、方法和基础静态调用。
- Kotlin 当前使用确定性声明解析，支持包、类型和方法定位，不承诺完整调用图。
- 反射、字符串注册、依赖注入和运行时分发可能显示为 `UNRESOLVED`。
- 当前不自动提取历史架构决策；决策记录应由项目自行评审和维护。
- Explorer 只展示根符号局部图；完整事实保存在 SQLite。
- 运行时执行路径需要日志、Tracing 或设备证据补充。

## 11. 同步上游

```powershell
cd D:\project\semantic
git fetch upstream --tags
git checkout atomicservice-v0.7.0
git merge upstream/main
```

不要在未验证兼容性的情况下直接覆盖本地版本。合并后至少执行：

```powershell
scripts\build-local.ps1
.venv\Scripts\python.exe -m pytest tests\project_kb -q
```

再使用一个真实项目重新构建知识库。

## 12. 开发与发布建议

- 功能修改提交到独立分支。
- Wheel 通过 GitHub Release 发布，不直接提交到 Git。
- Release 附带源码 Commit、Wheel SHA256 和测试结果。
- 保留 `upstream` 远程，持续跟踪原项目安全和兼容性更新。
- 前端依赖升级单独评估，不盲目执行 `npm audit fix`。
