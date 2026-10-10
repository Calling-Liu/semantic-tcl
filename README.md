# semantic-tcl

`semantic-tcl` 是基于 Semantica `v0.7.0` 的工程知识库增强版本，重点面向大型 Java/Kotlin/Android 项目。

本项目不是重新声明 Semantica 的原创归属。原始项目、协议和上游更新来源如下：

- 原项目：https://github.com/semantica-agi/semantica
- 当前 Fork：https://github.com/Calling-Liu/semantic-tcl
- 基线 Tag：`v0.7.0`
- 当前版本：`0.7.0+tcl.5`
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
- Explorer 简体中文界面与中英文切换。

命令入口：

```text
semantica-project-kb
```

## 文档导航

- [Explorer 前端六大 Tab 使用指南](docs/explorer-ui-guide.zh-CN.md)：说明知识探索、分析、决策、知识加工、管理和本体中心，以及每个子页面的用途、使用方式和限制。
- [官方架构说明](docs/architecture.md)：了解 Semantica 的核心模块和分层结构。
- [Explorer 启动说明](docs/explorer-setup.md)：了解 Explorer 的标准启动参数和接口。

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
D:\project\semantic\dist\semantica-0.7.0+tcl.5-py3-none-any.whl
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

重复构建前建议删除旧的 Python 构建目录，避免 Wheel 混入历史前端哈希资源：

```powershell
Remove-Item D:\project\semantic\build -Recurse -Force -ErrorAction SilentlyContinue
```

### 3.3 安装本地 Wheel

```powershell
uv venv --clear .venv --python 3.12

uv pip install --python .venv\Scripts\python.exe `
  "semantica[explorer,project-kb] @ file:///D:/project/semantic/dist/semantica-0.7.0+tcl.5-py3-none-any.whl"

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
0.7.0+tcl.5
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

首次构建还会生成：

```text
D:\knowledge-bases\ai-launcher\project-kb.json
D:\knowledge-bases\ai-launcher\update-state.json
```

- `project-kb.json` 保存仓库路径、Revision、根符号和图谱深度。
- `update-state.json` 保存上一次成功更新的 Commit 和输入摘要。

## 5. 更新知识库

### 5.1 手动更新

代码提交到新的 Commit 后，不需要重新填写 `--repo`、`--roots` 等参数：

```powershell
D:\project\semantic\.venv\Scripts\semantica-project-kb.exe update `
  --output D:\knowledge-bases\ai-launcher
```

更新程序会读取首次构建保存的 `project-kb.json`，检查：

- `--revision` 当前解析到的 Git Commit 是否变化。
- 项目内正式决策文件是否变化。
- Agent 决策 inbox 是否变化。
- 根符号和图谱深度配置是否变化。

如果没有变化，结果为：

```json
{
  "status": "skipped",
  "reason": "Git revision and decision inputs are unchanged"
}
```

需要无条件重建时：

```powershell
D:\project\semantic\.venv\Scripts\semantica-project-kb.exe update `
  --output D:\knowledge-bases\ai-launcher `
  --force
```

知识库只读取 Git Snapshot。工作区修改尚未形成 Commit 时，`HEAD` 不变，代码事实不会更新。

### 5.2 自动监听更新

启动持续监听：

```powershell
D:\project\semantic\.venv\Scripts\semantica-project-kb.exe watch `
  --output D:\knowledge-bases\ai-launcher `
  --interval 5
```

监听器每 5 秒检查一次：

- Git `HEAD` 或指定 Revision。
- `.semantica/decisions/` 中已提交的决策。
- `decision-inbox/` 中 Agent 新生成的候选决策。

检测到变化后自动执行与 `update` 相同的构建和发布流程。

停止监听：

```text
Ctrl+C
```

验证一次自动更新但不常驻：

```powershell
D:\project\semantic\.venv\Scripts\semantica-project-kb.exe watch `
  --output D:\knowledge-bases\ai-launcher `
  --once
```

### 5.3 自动更新的发布安全

- SQLite Snapshot 在事务中构建，抽取失败会回滚。
- Context Graph 先写临时文件并重新加载验证。
- 只有全部步骤成功后才更新 `artifacts/current.json` 和 `update-state.json`。
- 更新失败时，MCP 和 Explorer 可以继续使用上一次成功发布。

### 5.4 使用 Windows 任务计划定时更新

如果不希望保持 `watch` 终端，可以创建定时任务，定期执行：

```powershell
$exe = "D:\project\semantic\.venv\Scripts\semantica-project-kb.exe"
$args = "update --output D:\knowledge-bases\ai-launcher"

$action = New-ScheduledTaskAction -Execute $exe -Argument $args
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) `
  -RepetitionInterval (New-TimeSpan -Minutes 5)

Register-ScheduledTask `
  -TaskName "Update ai-launcher knowledge base" `
  -Action $action `
  -Trigger $trigger
```

删除任务：

```powershell
Unregister-ScheduledTask -TaskName "Update ai-launcher knowledge base"
```

## 6. 决策记录与 Agent 自动更新

代码结构可以通过解析器自动确认，但“为什么这样设计”不能让 Agent 无审核地写成事实。因此决策采用两级模型：

```text
Agent proposal -> pending inbox -> 人工确认 -> 项目 Git 决策记录
```

### 6.1 初始化项目决策目录

```powershell
D:\project\semantic\.venv\Scripts\semantica-project-kb.exe decision-template `
  --repo F:\project\ailauncherNew\temp\ai-launcher
```

生成：

```text
F:\project\ailauncherNew\temp\ai-launcher\.semantica\decisions\decision-template.yaml
```

项目正式决策文件应放在：

```text
.semantica/decisions/*.yaml
```

并与代码一起进行 Code Review 和 Git Commit。

### 6.2 手工新增候选决策

```powershell
D:\project\semantic\.venv\Scripts\semantica-project-kb.exe decision-propose `
  --output D:\knowledge-bases\ai-launcher `
  --id bounded-render-worker `
  --question "渲染任务为什么需要有界队列？" `
  --solution "使用有界线程池和明确的拒绝策略" `
  --rationale "无界任务会增加线程、内存和调度压力" `
  --affected JsthoController LogicExecutor `
  --alternative "每个任务创建独立线程" `
  --constraint "不能阻塞主线程"
```

候选文件保存到：

```text
D:\knowledge-bases\ai-launcher\decision-inbox\bounded-render-worker.yaml
```

状态固定为：

```yaml
review_status: pending
created_by: agent
```

如果 `watch` 正在运行，候选决策会自动进入知识库；否则手动执行 `update`。

查询决策：

```powershell
D:\project\semantic\.venv\Scripts\semantica-project-kb.exe decisions `
  --output D:\knowledge-bases\ai-launcher
```

只查询待审核决策：

```powershell
D:\project\semantic\.venv\Scripts\semantica-project-kb.exe decisions `
  --output D:\knowledge-bases\ai-launcher `
  --review-status pending
```

### 6.3 由 Agent 自动生成候选决策

MCP 默认是只读的。需要允许 Agent 写入候选 inbox 时，注册 MCP 时显式添加：

```powershell
codex mcp add ai-launcher-kb -- `
  D:\project\semantic\.venv\Scripts\semantica-project-kb.exe `
  mcp `
  --output D:\knowledge-bases\ai-launcher `
  --allow-decision-proposals
```

此时新增 MCP 工具：

```text
propose_decision_candidate
```

可以对 Agent 说：

```text
请把这次线程池设计记录成候选决策，状态保持 pending，不要自动确认。
```

Agent 只会写入 `decision-inbox`。它不能通过该工具把决策标记为 `confirmed`，也不会自动修改项目 Git 历史。

### 6.4 人工确认候选决策

```powershell
D:\project\semantic\.venv\Scripts\semantica-project-kb.exe decision-accept `
  --output D:\knowledge-bases\ai-launcher `
  --repo F:\project\ailauncherNew\temp\ai-launcher `
  bounded-render-worker
```

该命令会把候选复制到项目工作树：

```text
.semantica/decisions/bounded-render-worker.yaml
```

并将：

```yaml
review_status: confirmed
```

接下来仍需人工完成：

```powershell
cd F:\project\ailauncherNew\temp\ai-launcher
git diff -- .semantica\decisions\bounded-render-worker.yaml
git add .semantica\decisions\bounded-render-worker.yaml
git commit -m "docs(decision): record bounded render worker strategy"
```

Commit 后，`watch` 或下一次 `update` 会把来源从 `agent_inbox` 升级为 `project_git`。

### 6.5 为什么不允许 Agent 自动确认

- Agent 可能把推断当成历史事实。
- 决策可能涉及兼容性、性能和产品约束。
- 正式决策需要责任人和 Code Review。
- Git 中的决策文件才是长期权威来源；Semantica 图和 SQLite 可以重建。

## 7. 查询知识库

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

## 8. 接入 Codex MCP

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
list_decisions
```

默认注册方式保持只读。如果希望 Agent 自动生成 `pending` 决策候选，使用第 6.3 节的显式授权参数。

## 9. 启动 Explorer

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

### 9.1 Explorer 中文界面

Explorer 默认使用简体中文，左侧底部的语言按钮可以切换到英文。选择会保存在浏览器 `localStorage` 中。

已汉化范围：

- 首页和系统状态。
- 左侧主导航。
- 一级 Workspace 标题和主要 Tab。
- 知识探索搜索、视图模式、工具栏和加载状态。
- 图谱效果、邻域、图例和时间上下文面板。
- 节点 Inspector、内容预览、操作、路径追踪和来源信息。
- 错误边界与重试提示。
- Analyze 下的推理和 SPARQL 页面。
- Decisions 列表、筛选、因果链和空状态。
- Enrich 下的导入导出、差异合并、实体消歧和 Registry。
- Manage 下的 PROV-O 溯源、KG Overview 和 Ontology Summary。
- Ontology Hub 的 Registry、Editor、Versions、Alignments、Health、SHACL 和 Proposal Review。
- AgentMemory 和 Vocabulary Browser 的操作文案与空状态。

以下工程事实刻意不翻译：

- Java/Kotlin 类名、方法名、包名和签名。
- 文件路径、节点 ID、URI、属性原始键。
- `calls`、`declared_in`、`implements`、`extends`、`protects` 等关系类型。
- SPARQL、SHACL、OWL、SKOS、PROV-O 等标准名称。

例如，界面按钮 `Edge Labels` 显示为“关系标签”，但关系线上的实际值仍显示 `calls` 或 `declared_in`。这样可以避免中文长文本在线上拥挤，也保留与源码、API 和导出数据的一致性。

中文字体回退顺序包含：

```text
PingFang SC
Microsoft YaHei
Noto Sans CJK SC
```

代码、ID 和关系类型继续使用等宽字体。

后端返回的原始异常详情可能仍为英文。界面固定操作文案使用中文，但不会改写 API 的原始错误内容，便于排查和搜索上游问题。

## 10. TSD 和受保护源码

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

## 11. ai-launcher 实测结果

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
- 无变化 `update` 正确跳过。
- Agent 候选决策可以写入 inbox。
- `watch --once` 可以自动将候选决策入库为 `pending`。
- 显式授权的 MCP 可以调用 `propose_decision_candidate`。
- Agent 候选测试未修改 `ai-launcher` 业务仓库。

## 12. 当前能力边界

- Java 使用 Javalang，提供类型、方法和基础静态调用。
- Kotlin 当前使用确定性声明解析，支持包、类型和方法定位，不承诺完整调用图。
- 反射、字符串注册、依赖注入和运行时分发可能显示为 `UNRESOLVED`。
- 不自动把 Commit 文本推断成已确认历史决策。
- Agent 可以自动生成 `pending` 候选，但正式决策必须人工确认并进入项目 Git。
- Explorer 只展示根符号局部图；完整事实保存在 SQLite。
- 运行时执行路径需要日志、Tracing 或设备证据补充。

## 13. 同步上游

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

## 14. 开发与发布建议

- 功能修改提交到独立分支。
- Wheel 通过 GitHub Release 发布，不直接提交到 Git。
- Release 附带源码 Commit、Wheel SHA256 和测试结果。
- 保留 `upstream` 远程，持续跟踪原项目安全和兼容性更新。
- 前端依赖升级单独评估，不盲目执行 `npm audit fix`。
