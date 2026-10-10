# Semantica Explorer 前端使用指南

本文说明 `semantic-tcl` Explorer 左侧六个主 Tab 及其子页面的实际用途。

适用版本：`0.7.0+tcl.5`

## 1. 先理解 Explorer 的数据边界

Explorer 打开的是一个已经生成的 `Context Graph`。它适合查询、浏览、审计和少量人工加工，但不等同于项目知识库构建器。

对于 Java、Kotlin 或 Android 项目：

- 源码解析、Git Snapshot、SQLite 事实索引和增量更新由 `semantica-project-kb` 或项目自己的知识库脚本完成。
- Explorer 展示的是加载到当前进程中的图谱。
- 页面里的导入、合并、推理写入等操作通常先修改当前内存图谱。
- 需要长期保存的修改，应经过导出、审核和正式发布流程，不能只依赖浏览器会话。

## 2. 六个主 Tab 总览

| 主 Tab | 主要用途 | 代码知识库常用程度 |
| --- | --- | --- |
| 知识探索 | 搜索节点、查看关系、浏览词汇和 Agent Memory | 高 |
| 分析 | 使用 SPARQL 查询真实图谱，或手工测试推理规则 | 高 |
| 决策 | 查看架构决策、选择方案、设计理由和证据链 | 高 |
| 知识加工 | 导入导出、实体合并、重复实体检测和会话审计 | 中 |
| 管理 | 查看血缘、图谱规模和本体摘要 | 中 |
| 本体中心 | 管理 RDF、OWL、SKOS 和 SHACL 本体 | 按需 |

## 3. 知识探索

### 3.1 Semantica Explorer

这是主要的图谱浏览页面，用于：

- 按 ID、名称或文本搜索节点。
- 查看类、方法、模块、Decision 和 Evidence 等节点。
- 查看 `calls`、`declares`、`affects`、`evidenced_by` 等关系。
- 查看节点属性、来源信息和相邻节点。
- 查找两个节点之间的路径。
- 对局部子图进行筛选和可视化审计。

代码知识库中最常用的是精确搜索符号，然后围绕目标节点查看局部关系。完整方法级图谱通常很大，不建议一次加载或展开所有节点。

### 3.2 Memories

只有后端启用 Agent Memory 能力时，这个子页面才会出现。

它用于浏览和编辑规范化的 Agent Memory 文档，例如：

- 长期工作约束。
- 已确认的项目惯例。
- Agent 可以跨会话复用的上下文。

它不是代码事实索引，也不应代替 Decision、Git Evidence 或正式工程文档。

### 3.3 Vocabulary Browser

用于浏览 SKOS Vocabulary 和 Concept Scheme，包括：

- 词汇体系。
- 上位概念与下位概念。
- 首选名称、别名和定义。
- 概念之间的语义关系。

普通 Java 代码图谱没有导入 SKOS 词汇时，这个页面可能为空。

## 4. 分析

### 4.1 推理实验室

推理实验室对手工输入的 Facts 和 Rules 进行前向推理。

事实格式：

```text
predicate(subject, object)
```

例如：

```text
calls(executeLogic, getOrCompile)
calls(getOrCompile, compileLogic)
```

规则必须完整写在一行，变量必须以 `?` 开头：

```text
IF calls(?a, ?b) AND calls(?b, ?c) THEN transitively_calls(?a, ?c)
```

推理结果：

```text
transitively_calls(executeLogic, compileLogic)
```

注意：

- `X`、`Y` 会被当成普通常量，不是变量。
- 当前推理实验室不会自动把整个项目图谱转换成 Facts。
- Facts 是用户提供的逻辑断言，除非它们来自确定性代码索引，否则不能直接视为代码事实。
- 打开“写入图谱”后，二元推理结果会作为关系写入当前内存图谱。建议先关闭该选项预览结果。
- 当前回退推理器是单轮匹配，不会在同一次请求中反复使用刚推导出的新事实。

### 4.2 SPARQL 查询

SPARQL 直接查询当前加载的真实图谱，比推理实验室更适合代码知识库。

常用命名空间：

```sparql
PREFIX ent: <http://semantica.local/entity/>
PREFIX prop: <http://semantica.local/prop/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
```

查询所有关系类型及数量：

```sparql
SELECT ?predicate (COUNT(*) AS ?count)
WHERE {
  ?source ?predicate ?target
  FILTER(STRSTARTS(STR(?predicate), "http://semantica.local/prop/"))
}
GROUP BY ?predicate
ORDER BY DESC(?count)
```

查询某个方法直接调用的目标：

```sparql
PREFIX prop: <http://semantica.local/prop/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?target ?label
WHERE {
  <http://semantica.local/entity/java:example.Class#method()> prop:calls ?target .
  OPTIONAL { ?target rdfs:label ?label }
}
```

Explorer 只允许 `SELECT`、`ASK`、`CONSTRUCT` 和 `DESCRIBE`，不允许通过 SPARQL 修改图谱。

## 5. 决策

决策页面展示图谱中的 `decision` 和 `architecture_decision` 节点。

项目知识库字段会映射为：

| 项目知识库字段 | 决策页面字段 |
| --- | --- |
| `question` | Scenario / 决策问题 |
| `rationale` | Reasoning / 设计理由 |
| `content` 或 `chosen_solution` | Outcome / 选择方案 |
| `confidence_score` | Confidence |
| `review_status` | 审核状态 |
| `decision_status` | 当前状态 |

选择一条决策后，可以查看：

- 当时需要解决的问题。
- 最终采用的方案。
- 为什么采用该方案。
- 审核状态和置信度。
- 受影响的类、方法或模块。
- 关联的 Git Commit、文档或其他 Evidence。

页面为空通常表示当前图谱没有 Decision 记录，不代表前端加载失败。不要为了填充页面而生成没有证据的历史决策。

## 6. 知识加工

### 6.1 导入与导出

支持：

- 导入 JSON 或 CSV 节点与关系。
- 将当前图谱导出为 JSON 或 CSV。

JSON 更适合保存完整图属性；CSV 更适合电子表格分析。导入操作修改当前 Explorer 会话，不会自动更新项目的 SQLite 事实索引或 Git Snapshot。

### 6.2 差异与合并

用于指定：

- Primary Node ID：保留的规范节点。
- Duplicate Node ID：需要合并并移除的重复节点。

合并时会把重复节点的关系重定向到主节点。当前字段对比区域仍是示例预览，真正执行的是节点合并接口。

### 6.3 实体消歧

按相似度查找疑似重复实体：

- 调整 Similarity Threshold。
- 扫描疑似重复节点对。
- 人工确认后合并。
- 忽略误报候选。

相似不代表相同。Java 重载方法、同名类和不同模块中的同名符号不能仅凭名称自动合并。

### 6.4 操作注册表

记录当前浏览器会话中的操作，例如：

- Import。
- Export。
- Merge。
- Add Node / Add Edge。
- Infer。
- Delete。
- Vocabulary Import。

这是前端会话审计日志，不是长期持久化的企业审计数据库。刷新页面或清理注册表后记录可能消失。

## 7. 管理

### 7.1 PROV-O 血缘

输入完整节点 ID，查看它的来源和关联链。

例如：

```text
decision:layout-listener-anr:2026-08-19
```

页面支持：

- `1 hop`：默认模式，只显示直接关系，适合日常阅读。
- `2 hop`：显示两层完整子图，适合进一步影响分析。
- 导出 JSON 或 Markdown 血缘报告。

节点按图距离分层布局。大图会自动缩放到画布内，使用鼠标滚轮或左下角缩放按钮查看局部。

如果没有配置独立 Provenance Store，Explorer 会回退到 Context Graph 关系遍历。这种结果可以说明节点之间的图关系，但不等同于完整的构建过程审计。

### 7.2 知识图谱概览

显示：

- 节点总数。
- 关系总数。
- 图谱密度。
- 节点类型分布。
- 关系类型分布。
- 连接数最多的节点。

它适合检查知识库是否成功加载，以及 `class`、`method`、`module`、`evidence`、`calls` 等数据是否存在。

当前 Top Connected Nodes 和部分前端分布统计最多读取前 500 个节点和前 2000 条边。大型代码图谱中，总节点数和总关系数来自统计接口，但排行榜可能只代表局部数据。

### 7.3 本体概览

只读展示已加载的 SKOS Concept Scheme 和概念树。

它不是 Java 类结构页面。没有导入 `.ttl`、`.rdf` 或 SKOS Vocabulary 时，显示为空是正常的。

## 8. 本体中心

本体中心面向 RDF、OWL、SKOS 和 SHACL 治理。普通代码事实图谱可以暂不使用。

### 8.1 Registry

本体注册表，用于导入、登记、选择和管理 Ontology 文件及其基本信息。

### 8.2 Editor

浏览和编辑 Ontology Entity，例如 Class、Property、Label、Comment 和关系定义。

### 8.3 Versions

查看本体版本、版本变化和评审信息，用于管理本体的演进过程。

### 8.4 Alignments

建立不同本体或词汇体系之间的概念映射，例如等价、相近、上位或下位关系。

### 8.5 Health

检查本体质量问题，例如缺少 Label、定义不完整、悬空引用或结构异常，并可跳转到 Editor 修复。

### 8.6 SHACL

生成、编辑和验证 SHACL Turtle，用约束规则检查 RDF 数据是否符合本体要求。

## 9. 项目知识库推荐使用顺序

对于 AtomicService、Launcher 或其他代码知识库，推荐顺序是：

1. 在“知识探索”中搜索目标类、方法、模块或 Decision。
2. 使用图谱局部关系判断直接调用、声明和影响范围。
3. 使用“分析 → SPARQL”执行精确结构化查询。
4. 使用“决策”查看设计理由和 Evidence。
5. 使用“管理 → PROV-O 血缘”查看某个节点的上下游关系。
6. 只有需要人工清洗时才使用“知识加工”。
7. 只有建设正式术语体系时才使用“本体中心”。

## 10. 哪些操作会长期保存

| 操作 | 默认是否长期保存 |
| --- | --- |
| 搜索、过滤、SPARQL 查询 | 否，只读操作 |
| 推理预览 | 否 |
| 推理写入图谱 | 只修改当前图谱会话，需后续导出和发布 |
| 导入、实体合并 | 只修改当前图谱会话，需后续导出和发布 |
| Registry 操作日志 | 否，默认是前端会话日志 |
| 项目知识库构建或增量更新 | 是，按项目发布流程生成新 Snapshot |
| 提交 Decision YAML 并重建知识库 | 是，可进入 Git、SQLite 和 Context Graph |

项目事实的权威来源仍应是 Git、正式文档、审核后的 Decision Record 和可重复执行的知识库构建流程。
