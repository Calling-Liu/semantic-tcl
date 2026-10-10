import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

export type Locale = "zh-CN" | "en-US";

const ZH_CN: Record<string, string> = {
  "Connecting…": "正在连接…",
  "System Online": "系统在线",
  "Backend Unreachable": "后端不可用",
  "Knowledge Explorer": "知识探索",
  "Graph and vocabulary browsing": "浏览知识图谱与词汇体系",
  "Analyze": "分析",
  "Query and inspect the dataset": "查询并分析当前数据集",
  "Decisions": "决策",
  "Decision chains and precedent review": "查看决策链与历史依据",
  "Enrich": "知识加工",
  "Import, export, and merge workflows": "导入、导出与合并工作流",
  "Manage": "管理",
  "Lineage and governance tooling": "溯源与治理工具",
  "Ontology Hub": "本体中心",
  "Schema governance, registry, and vocabulary management": "模式治理、注册表与词汇管理",
  "Workspace": "工作区",
  "Loading workspace…": "正在加载工作区…",
  "Knowledge nodes": "知识节点",
  "Relationships mapped": "已映射关系",
  "Graph modes": "图谱模式",
  "Dataset online": "数据集在线",
  "Ready to explore": "等待探索",
  "Live": "实时",
  "Ready": "就绪",
  "Active": "运行中",
  "Standby": "待机",
  "Workspaces": "工作区",
  "Primary Workspace": "主要工作区",
  "Semantica Explorer": "图谱探索",
  "Full graph, grouped communities, focused neighborhoods, and distance intelligence — all in one canvas.": "在同一画布中查看完整图谱、聚合社区、焦点邻域和距离分析。",
  "Vocabulary": "词汇体系",
  "Schemes and terms": "概念体系与术语",
  "Inference and queries": "推理与查询",
  "Chains and precedents": "决策链与历史依据",
  "Import and resolve": "导入与实体消歧",
  "Lineage and ontology": "溯源与本体治理",
  "Intelligence Layer": "智能能力",
  "Distance Heatmap": "距离热力图",
  "Focused Neighborhood": "焦点邻域",
  "Grouped Communities": "社区聚合",
  "Trace Causal Path": "追踪因果路径",
  "Provenance Audit": "溯源审计",
  "Provenance Dossier": "溯源档案",
  "Discard the unapplied Markdown draft and leave this resource?": "放弃尚未应用的 Markdown 草稿并离开当前资源吗？",
  "Open Semantica Explorer": "打开知识探索",
  "Product category": "产品类别",
  "Navigate knowledge": "让知识网络",
  "like a living system.": "像生命一样可探索。",
  "Semantica turns dense knowledge graphs into a navigable command center — discovery, reasoning, provenance, distance intelligence, and decision context, all in one interface.": "Semantica 将复杂知识图谱转化为可操作的探索中心，在一个界面中完成发现、推理、溯源、距离分析和决策理解。",
  "Knowledge graph preview": "知识图谱预览",
  "distance heatmap · focused view · causal path": "距离热力图 · 焦点视图 · 因果路径",
  "Entity Dossier": "实体档案",
  "Distance band": "距离分层",
  "Near": "近邻",
  "Path coherence": "路径一致性",
  "Provenance": "溯源",
  "Audited": "已审计",
  "Temporal Evidence": "时间证据",
  "66% coverage": "覆盖率 66%",
  "System status": "系统状态",
  "Intelligence capabilities": "智能能力",
  "Explore the knowledge graph": "探索知识图谱",
  "Explore": "探索",
  "Graph Studio": "图谱工作台",
  "Memory Browser": "记忆浏览",
  "Browse and edit canonical AgentMemory documents.": "浏览和编辑标准 AgentMemory 文档。",
  "Browse the graph and switch views without leaving the workspace.": "在当前工作区内浏览图谱并切换视图。",
  "Memories": "记忆",
  "Vocabulary Browser": "词汇浏览",
  "Query the active graph and test inference rules.": "查询当前图谱并验证推理规则。",
  "Reasoning Engine": "推理引擎",
  "SPARQL Query": "SPARQL 查询",
  "Reasoning Playground": "推理实验室",
  "SPARQL Querying": "SPARQL 查询",
  "Inspect decision chains, causal context, and precedent matches.": "查看决策链、因果上下文和历史匹配。",
  "Decision Intelligence": "决策智能",
  "Import, export, reconcile, and audit graph entities.": "导入、导出、合并并审计图谱实体。",
  "Knowledge Audit": "知识审计",
  "Import and Export": "导入与导出",
  "Diff and Merge": "差异与合并",
  "Entity Resolution": "实体消歧",
  "Registry": "注册表",
  "Load, browse, edit, and govern ontologies and vocabularies.": "加载、浏览、编辑并治理本体与词汇体系。",
  "Schema Governance": "模式治理",
  "Review provenance, lineage, ontology, and governance context.": "查看溯源、血缘、本体和治理上下文。",
  "Graph Governance": "图谱治理",
  "PROV-O Lineage": "PROV-O 溯源",
  "KG Overview": "知识图谱概览",
  "Ontology Summary": "本体概览",
  "Search command, node, or concept": "搜索命令、节点或概念",
  "Search graph nodes": "搜索图谱节点",
  "Search for the current query": "执行当前搜索",
  "Search": "搜索",
  "Search suggestions": "搜索建议",
  "Node colors": "节点颜色",
  "Graph view mode": "图谱视图模式",
  "Full Graph": "完整图谱",
  "Return to the full graph context": "返回完整图谱上下文",
  "Grouped View": "聚合视图",
  "Compress dense structure into detected communities": "将密集结构压缩为检测到的社区",
  "Focus": "聚焦",
  "Inspect the selected node in a focused local graph": "在局部图中聚焦查看所选节点",
  "Zoom In": "放大",
  "Zoom in (or scroll up on the canvas)": "放大（或在画布上向上滚动）",
  "Zoom in": "放大",
  "Zoom Out": "缩小",
  "Zoom out (or scroll down on the canvas)": "缩小（或在画布上向下滚动）",
  "Zoom out": "缩小",
  "Fit": "适配画布",
  "Reset the camera to fit the whole graph": "重置视图以显示完整图谱",
  "Fit view": "适配视图",
  "Pause": "暂停",
  "Run": "运行",
  "Toggle the layout worker": "启动或暂停布局计算",
  "Collapse": "收起",
  "Hide lower-priority fanout around the selected node": "隐藏所选节点周围优先级较低的分支",
  "Expand": "展开",
  "Restore the collapsed local neighborhood": "恢复已收起的局部邻域",
  "Reload": "重新加载",
  "Reload graph data": "重新加载图谱数据",
  "Heatmap": "热力图",
  "Distance heatmap active (click to toggle off)": "距离热力图已启用（点击关闭）",
  "Color nodes by hop distance from selected node": "按与所选节点的跳数距离着色",
  "Structural": "结构距离",
  "Color edges by structural (hop) distance": "按结构跳数距离为关系着色",
  "Semantic": "语义相似度",
  "Color edges by semantic similarity to selected node": "按与所选节点的语义相似度为关系着色",
  "Ego Mode": "中心视图",
  "Show depth-of-field fading around the selected node": "显示围绕所选节点的层级衰减效果",
  "Camera": "视图",
  "Layout": "布局",
  "Local": "局部",
  "Distance": "距离",
  "Analysis": "分析",
  "Utility": "工具",
  "Effects": "效果",
  "Neighbors": "邻居",
  "Temporal": "时间",
  "Legend": "图例",
  "Open exploration effects controls": "打开探索效果设置",
  "Toggle neighborhood panel": "打开或关闭邻域面板",
  "Toggle temporal context panel": "打开或关闭时间上下文面板",
  "Path Pulse": "路径脉冲",
  "Animated pulse on the active selected path.": "在当前选中路径上显示动画脉冲。",
  "Path Flow": "路径流向",
  "Directional flow accents along the active selected path.": "沿当前选中路径显示方向流动效果。",
  "Neighborhood Lens": "邻域透镜",
  "Local emphasis around the hovered or selected node.": "突出显示悬停或选中节点的局部邻域。",
  "Temporal Emphasis": "时间强调",
  "Subtle glow around temporally relevant nodes in the active time window.": "在当前时间窗口内突出具有时间相关性的节点。",
  "Semantic Regions": "语义区域",
  "Quiet semantic hulls around the strongest visible topic clusters.": "为主要可见主题簇显示低干扰语义边界。",
  "Contours": "密度轮廓",
  "Low-contrast density halos around the strongest visible anchors.": "在主要可见锚点周围显示低对比度密度轮廓。",
  "Edge Labels": "关系标签",
  "Draw the relationship type on graph edges. Off restores label-free edges on dense graphs.": "在关系线上显示原始关系类型；关闭后密集图谱不显示关系文字。",
  "Regions Summary": "区域摘要",
  "Keep the regions and signals summary visible in the Effects panel.": "在效果面板中持续显示区域与信号摘要。",
  "Directed Pathfinding": "有向路径分析",
  "Compare the traced path against a strict local directed shortest path.": "将追踪路径与局部有向最短路径进行比较。",
  "Community Regions": "社区区域",
  "Detect stable Louvain communities for orientation and scene grouping.": "检测稳定的 Louvain 社区，用于定位和场景分组。",
  "Centrality Ranking": "中心性排名",
  "Rank the strongest graph anchors for labels, regions, and navigation.": "对主要图谱锚点进行排名，用于标签、区域和导航。",
  "On": "开",
  "Off": "关",
  "Waiting for graph runtime": "等待图谱运行时",
  "Toggle semantic legend": "打开或关闭语义图例",
  "Neighborhood": "邻域",
  "Temporal Context": "时间上下文",
  "No time selected": "未选择时间",
  "Current scrubber state": "当前时间轴状态",
  "Current": "当前",
  "Bounds": "范围",
  "Active nodes": "活跃节点",
  "Pause Evolution": "暂停时间演化",
  "Play Evolution": "播放时间演化",
  "Temporal Scrubber": "时间轴",
  "Confidence Decay": "置信度衰减",
  "Semantic Sim.": "语义相似度",
  "Path Coherence": "路径一致性",
  "Bottleneck": "瓶颈节点",
  "No path found between the selected nodes.": "所选节点之间未找到路径。",
  "Total weight:": "总权重：",
  "Search for a node or click one in the canvas to inspect its properties.": "搜索节点，或在画布中点击节点以查看其属性。",
  "Selection": "当前选择",
  "Selected item is not directly inspectable in the current graph.": "当前图谱中无法直接查看所选项目。",
  "Use Focus to resolve this grouped selection to its canonical node.": "使用“聚焦”将聚合项定位到其标准节点。",
  "Grouped Selection": "聚合选择",
  "Entity": "实体",
  "This grouped item stays display-level until you explicitly enter Focused mode.": "该聚合项仅用于展示；进入聚焦模式后才能查看实际节点。",
  "Content": "内容",
  "Actions": "操作",
  "Run Link Prediction": "运行关系预测",
  "Running…": "运行中…",
  "Optional candidate type filter, e.g. disease": "可选候选类型，例如 disease",
  "Trace Path": "追踪路径",
  "Target node ID": "目标节点 ID",
  "Candidate Links": "候选关系",
  "Computing candidate links…": "正在计算候选关系…",
  "Run link prediction to surface likely next-hop relationships.": "运行关系预测以发现可能的下一跳关系。",
  "Source Attribution": "来源信息",
  "No explicit attribution metadata was found on this node.": "该节点没有明确的来源元数据。",
  "No additional properties are attached to this node.": "该节点没有附加属性。",
  "Preview": "预览",
  "Source": "源码",
  "Copy": "复制",
  "Copied": "已复制",
  "Edit": "编辑",
  "Cancel": "取消",
  "Apply": "应用",
  "Applying…": "正在应用…",
  "Loading…": "正在加载…",
  "Reload latest": "加载最新内容",
  "Copy raw content": "复制原始内容",
  "Content view mode": "内容查看模式",
  "Markdown source": "Markdown 源码",
  "No content available for this node.": "该节点没有可用内容。",
  "Provenance JSON": "溯源 JSON",
  "Provenance MD": "溯源 Markdown",
  "Choose a target or click a candidate prediction to prepare a path trace.": "选择目标节点，或点击候选关系以准备路径追踪。",
  "Forward Chaining": "正向链式推理",
  "Inference Engine": "推理引擎",
  "Quick Templates": "快速模板",
  "Facts": "事实",
  "One fact per line using": "每行输入一条事实，格式为",
  "form.": "形式。",
  "Rules": "规则",
  "Use": "使用",
  "syntax. Falls back to internal matcher if the reasoning server is unavailable.": "语法。如果推理服务不可用，将回退到内置匹配器。",
  "Write inferred facts to graph": "将推理结果写入图谱",
  "Inferred binary facts are added as edges": "推导出的二元事实将作为关系写入图谱",
  "Run Reasoning": "运行推理",
  "Inference Results": "推理结果",
  "Ready to reason": "等待推理",
  "Enter facts and rules on the left, then click Run Reasoning to see inferred statements here.": "在左侧输入事实和规则，然后点击“运行推理”查看结果。",
  "Reasoning complete": "推理完成",
  "No new facts were inferred from the current rule set and facts.": "当前规则和事实没有推导出新的事实。",
  "graph updated": "图谱已更新",
  "preview only": "仅预览",
  "Reasoning failed": "推理失败",
  "Reset to defaults": "恢复默认值",
  "Run Query": "运行查询",
  "Run a query": "等待查询",
  "Write SPARQL above or pick a template, then click Run Query to see results here.": "在上方输入 SPARQL 或选择模板，然后点击“运行查询”查看结果。",
  "No results": "无结果",
  "The query returned 0 rows. Try a broader query or check your data.": "查询返回 0 行。请尝试扩大查询范围或检查数据。",
  "Templates:": "模板：",
  "Copy query": "复制查询",
  "Copied!": "已复制！",
  "Network error — could not reach the SPARQL endpoint.": "网络错误，无法连接 SPARQL 端点。",
  "Filter by ID, category, outcome…": "按 ID、类别或结果筛选…",
  "No decisions": "暂无决策",
  "No matches": "没有匹配项",
  "No decisions available in the graph.": "图谱中暂无决策记录。",
  "Adjust your filter.": "请调整筛选条件。",
  "Decision Record": "决策记录",
  "Causal Chain": "因果链",
  "No decision selected": "未选择决策",
  "Select a decision from the list to inspect its causal chain and metadata.": "从列表中选择决策，以查看其因果链和元数据。",
  "No chain steps": "没有因果步骤",
  "No causal chain steps were found for this decision.": "该决策没有找到因果链步骤。",
  "Agent memories": "Agent 记忆",
  "Refresh memories": "刷新记忆",
  "Apply or cancel the current draft before refreshing": "刷新前请先应用或取消当前草稿",
  "Empty memory": "空记忆",
  "Load more memories": "加载更多记忆",
  "Load more": "加载更多",
  "No AgentMemory items are available.": "暂无 AgentMemory 记录。",
  "Selected memory": "已选记忆",
  "Loading memories…": "正在加载记忆…",
  "Discard the unapplied Markdown draft and open another memory?": "放弃尚未应用的 Markdown 草稿并打开另一条记忆吗？",
  "Import & Export": "导入与导出",
  "Ingest new graph datasets or extract the current knowledge base.": "导入新的图谱数据集，或导出当前知识库。",
  "Import Entities & Relations": "导入实体与关系",
  "Drag & drop or click to browse": "拖放文件，或点击选择文件",
  "or": "或",
  "Upload to Graph": "上传到图谱",
  "Uploading…": "正在上传…",
  "Export Graph Snapshot": "导出图谱快照",
  "Format": "格式",
  "What's included": "包含内容",
  "Full graph snapshot: all node properties, edge weights, entity metadata and semantic groups in a standardized JSON payload.": "完整图谱快照：以标准 JSON 格式包含全部节点属性、关系权重、实体元数据和语义分组。",
  "Flattened CSV: nodes and edges as rows. Complex nested properties are stringified. Best for spreadsheet analysis.": "扁平化 CSV：节点和关系按行输出，复杂嵌套属性转为字符串，适合表格分析。",
  "Download Export": "下载导出文件",
  "Preparing…": "正在准备…",
  "Entity Diff & Merge": "实体差异与合并",
  "Compare suspected duplicates side-by-side and reconcile them into a single canonical entity.": "并排比较疑似重复实体，并合并为一个标准实体。",
  "Primary Node ID (keep)": "主节点 ID（保留）",
  "Duplicate Node ID (remove)": "重复节点 ID（移除）",
  "Sample preview": "示例预览",
  "Field": "字段",
  "Primary (keep)": "主实体（保留）",
  "Duplicate (remove)": "重复实体（移除）",
  "Confirm Merge": "确认合并",
  "Merging…": "正在合并…",
  "Detect and merge duplicate entities in the knowledge graph": "检测并合并知识图谱中的重复实体",
  "Similarity Threshold": "相似度阈值",
  "More results (0.50)": "更多结果（0.50）",
  "Fewer, higher confidence (0.99)": "更少但置信度更高（0.99）",
  "Run Dedup Scan": "运行去重扫描",
  "Scanning…": "正在扫描…",
  "Clear all": "全部清除",
  "Merge": "合并",
  "Dismiss": "忽略",
  "Document Registry": "文档注册表",
  "Clear all events": "清除全部事件",
  "Expand details": "展开详情",
  "Collapse details": "收起详情",
  "PROV-O Lineage Viewer": "PROV-O 溯源查看器",
  "Enter a Node ID in the toolbar above and click Trace to view its W3C PROV-O lineage diagram.": "在上方工具栏输入节点 ID，然后点击“追踪”查看 W3C PROV-O 溯源图。",
  "Enter Node ID…": "输入节点 ID…",
  "Trace": "追踪",
  "Export JSON": "导出 JSON",
  "Export MD": "导出 Markdown",
  "Node/edge counts, type distributions, and top connected nodes": "节点与关系数量、类型分布和高连接节点",
  "Node Type Breakdown": "节点类型分布",
  "Edge Type Breakdown": "关系类型分布",
  "Top Connected Nodes (by degree)": "高连接节点（按度数）",
  "No data — load the graph first.": "暂无数据，请先加载图谱。",
  "Edge type breakdown requires the stats endpoint to return edge_types.": "关系类型分布需要统计接口返回 edge_types。",
  "Open Full Browser": "打开完整浏览器",
  "No vocabulary schemes loaded": "尚未加载词汇体系",
  "Alternative Labels": "其他标签",
  "Click a concept in the tree to view its properties.": "点击概念树中的项目以查看属性。",
  "No concept selected": "未选择概念",
  "Drop here…": "拖放到此处…",
  "Import Vocabulary": "导入 Vocabulary",
  "Import Successful!": "导入成功！",
  "Editor": "编辑器",
  "Versions": "版本",
  "Alignments": "对齐",
  "Health": "质量",
  "All": "全部",
  "Classes": "类",
  "Concepts": "概念",
  "Entity Search": "实体搜索",
  "Search ontologies by name, URI, or namespace…": "按名称、URI 或命名空间搜索 Ontology…",
  "Loading registry…": "正在加载注册表…",
  "No ontologies loaded yet": "尚未加载 Ontology",
  "Import from a URL, upload a file, or create a new ontology to get started. Click": "可以通过 URL、上传文件或新建 Ontology 开始使用。点击",
  "above.": "即可。",
  "Load Ontology": "加载 Ontology",
  "No ontologies match your search": "没有匹配的 Ontology",
  "Try a different search term or clear the filter.": "请尝试其他搜索词或清除筛选条件。",
  "Description": "说明",
  "Properties": "属性",
  "Loaded at": "加载时间",
  "Source URL": "来源 URL",
  "Tags": "标签",
  "Version": "版本",
  "Disable": "停用",
  "Enable": "启用",
  "Disabled": "已停用",
  "Re-fetch from source URL": "从来源 URL 重新获取",
  "Remove from registry": "从注册表移除",
  "Ontology refreshed": "Ontology 已刷新",
  "Removed from registry": "已从注册表移除",
  "From Text": "从文本创建",
  "From Data": "从数据创建",
  "From Scratch": "从零创建",
  "Ontology URL": "Ontology URL",
  "Format override": "指定格式",
  "Auto-detect": "自动检测",
  "Custom display name": "自定义显示名称",
  "Leave blank to use ontology title": "留空则使用 Ontology 标题",
  "Display Name *": "显示名称 *",
  "Namespace URI *": "命名空间 URI *",
  "Optional description": "可选说明",
  "Tags (comma-separated)": "标签（逗号分隔）",
  "Sample Data (JSON or CSV)": "示例数据（JSON 或 CSV）",
  "Schema Requirements (natural language)": "Schema 要求（自然语言）",
  "Fetch Preview": "获取预览",
  "Estimated triples": "预计 triples 数量",
  "Ontology loaded successfully": "Ontology 加载成功",
  "Ontology created and opened in the Registry": "Ontology 已创建并在 Registry 中打开",
  "Versions & Change Proposals": "版本与变更提案",
  "Ontology URI": "Ontology URI",
  "Compare Versions": "比较版本",
  "Compare": "比较",
  "Comparing...": "正在比较…",
  "No versions found": "未找到版本",
  "No proposals found": "未找到提案",
  "Proposal Details": "提案详情",
  "Proposal approved": "提案已批准",
  "Proposal rejected": "提案已拒绝",
  "Proposal published": "提案已发布",
  "Cross-ontology mappings": "跨 Ontology 映射",
  "Mappings": "映射",
  "Suggestions": "建议",
  "Pairwise alignment matrix": "成对对齐矩阵",
  "Recorded alignments": "已记录的对齐",
  "No alignments recorded yet.": "尚未记录对齐。",
  "Click a relation badge to load it into the editor below.": "点击关系标签，将其加载到下方编辑器。",
  "Create or update alignment": "创建或更新对齐",
  "Source entity URI": "源实体 URI",
  "Target entity URI": "目标实体 URI",
  "Relation": "关系",
  "Provenance note": "溯源说明",
  "Reviewer": "审核人",
  "Source ontology": "源 Ontology",
  "Target ontology": "目标 Ontology",
  "Any ontology": "任意 Ontology",
  "Suggest alignments": "生成对齐建议",
  "Run suggestions to review ranked candidate mappings.": "运行建议以查看排序后的候选映射。",
  "Remove alignment": "移除对齐",
  "Quality and governance signals": "质量与治理指标",
  "Ontology": "Ontology",
  "Total health score": "总体质量评分",
  "Actionable issues": "可处理问题",
  "No actionable issues reported for this ontology.": "该 Ontology 没有报告可处理问题。",
  "Select an ontology to compute health signals.": "选择 Ontology 以计算质量指标。",
  "Generate, edit, and validate shapes": "生成、编辑并验证 Shapes",
  "Generate or edit SHACL Turtle, then run validation.": "生成或编辑 SHACL Turtle，然后运行验证。",
  "Shape library": "Shape 库",
  "No shapes generated yet.": "尚未生成 Shapes。",
  "Turtle shape editor": "Turtle Shape 编辑器",
  "Validation report": "验证报告",
  "No validation violations returned.": "没有返回验证违规项。",
  "View all": "查看全部",
  "Click to load this shape into the editor": "点击将该 Shape 加载到编辑器",
  "Loading proposal...": "正在加载提案…",
  "No changes detected": "未检测到变更",
  "No comments yet": "暂无评论",
  "Add a comment...": "添加评论…",
  "Active ontology": "当前 Ontology",
  "Select ontology...": "选择 Ontology…",
  "Loading ontology structure…": "正在加载 Ontology 结构…",
  "This ontology has no editable classes or properties.": "该 Ontology 没有可编辑的类或属性。",
  "Ontology Details": "Ontology 详情",
  "Class Details": "类详情",
  "Property Details": "属性详情",
  "Relationship Details": "关系详情",
  "External Term Details": "外部术语详情",
  "Visual editor changes": "可视化编辑器变更",
  "Saving...": "正在保存…",
  "Propose": "提交提案",
  "Search classes, properties, concepts…": "搜索类、属性或概念…",
  "Not found": "未找到",
  "Definition": "定义",
  "Domain": "Domain",
  "Range": "Range",
  "Instances": "实例",
  "Source Ontology": "来源 Ontology",
  "Superclasses / Broader": "父类 / Broader",
  "Subclasses / Narrower": "子类 / Narrower",
  "Concept Scheme": "Concept Scheme",
  "Search labels and definitions…": "搜索标签和定义…",
  "No matching concepts": "没有匹配的概念",
  "No concepts in this scheme": "该 Scheme 中没有概念",
  "Loading concepts…": "正在加载概念…",
  "Concept Detail": "概念详情",
  "Editorial Note": "编辑说明",
  "Scope Note": "范围说明",
  "Preparing graph session": "正在准备图谱会话",
  "Loading nodes": "正在加载节点",
  "Loading relationships": "正在加载关系",
  "Computing node styling": "正在计算节点样式",
  "Hydrating graph scene": "正在构建图谱场景",
  "Stabilizing layout": "正在稳定布局",
  "Graph ready": "图谱已就绪",
  "Prepare": "准备",
  "Nodes": "节点",
  "Relations": "关系",
  "Styling": "样式",
  "Scene": "场景",
  "Stage": "阶段",
  "Persisted layout": "持久化布局",
  "Preserved layout": "保留布局",
  "Runtime layout": "运行时布局",
  "Bootstrapping": "初始化",
  "Settling": "收敛中",
  "Interactive": "可交互",
  "Stable": "已稳定",
  "Fallback": "回退模式",
  "Working through this stage": "正在处理当前阶段",
  "in current stage": "当前阶段",
  "Applying semantic color, sizing, and structural styling": "正在应用语义颜色、尺寸和结构样式",
  "Preparing renderer and hydrating graph scene": "正在准备渲染器并构建图谱场景",
  "Settling runtime layout": "正在稳定运行时布局",
  "Something went wrong in this view.": "当前视图发生错误。",
  "An unexpected problem occurred while rendering this workspace. Your data is safe, but this view cannot be displayed.": "渲染当前工作区时发生异常。数据不会丢失，但当前视图无法显示。",
  "This view continues to encounter a critical error. Please switch to another workspace or reload the page to restore functionality.": "当前视图持续发生严重错误。请切换到其他工作区，或重新加载页面。",
  "Try Again": "重试",
  "Reload Application": "重新加载应用",
  "Language": "语言",
  "Switch to English": "切换到英文",
  "Switch to Chinese": "切换到中文",
};

type I18nContextValue = {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  tr: (source: string) => string;
};

const I18nContext = createContext<I18nContextValue>({
  locale: "en-US",
  setLocale: () => {},
  tr: (source) => source,
});

const ENGLISH_BY_CHINESE = new Map(
  Object.entries(ZH_CN).map(([english, chinese]) => [chinese, english]),
);
const ORIGINAL_TEXT = new WeakMap<Text, string>();
const ORIGINAL_ATTRIBUTES = new WeakMap<Element, Map<string, string>>();
const TRANSLATABLE_ATTRIBUTES = ["placeholder", "title", "aria-label"] as const;
const AUTO_TRANSLATE_EXCLUDE = [
  "code",
  "pre",
  "canvas",
  "script",
  "style",
  "[data-i18n='off']",
  ".mono",
  ".explore-color-legend-name",
  ".explore-search-suggestion-type",
].join(",");

function isExcluded(element: Element | null) {
  return Boolean(element?.closest(AUTO_TRANSLATE_EXCLUDE));
}

function translateTextNode(node: Text, locale: Locale) {
  if (isExcluded(node.parentElement)) return;
  const current = node.nodeValue ?? "";
  let original = ORIGINAL_TEXT.get(node);
  if (original == null) {
    const trimmed = current.trim();
    const reverse = ENGLISH_BY_CHINESE.get(trimmed);
    const translated = translate(trimmed, "zh-CN");
    if (reverse) {
      const leading = current.slice(0, current.indexOf(trimmed));
      const trailing = current.slice(current.indexOf(trimmed) + trimmed.length);
      original = `${leading}${reverse}${trailing}`;
    } else if (translated !== trimmed) {
      original = current;
    } else {
      return;
    }
    ORIGINAL_TEXT.set(node, original);
  }
  if (locale === "en-US") {
    if (current !== original) node.nodeValue = original;
    return;
  }
  const trimmed = original.trim();
  if (!trimmed) return;
  const translated = translate(trimmed, "zh-CN");
  if (translated === trimmed) return;
  const leading = original.slice(0, original.indexOf(trimmed));
  const trailing = original.slice(original.indexOf(trimmed) + trimmed.length);
  const next = `${leading}${translated}${trailing}`;
  if (current !== next) node.nodeValue = next;
}

function translateAttributes(element: Element, locale: Locale) {
  if (isExcluded(element)) return;
  let originals = ORIGINAL_ATTRIBUTES.get(element);
  if (!originals) {
    originals = new Map<string, string>();
    ORIGINAL_ATTRIBUTES.set(element, originals);
  }
  for (const attribute of TRANSLATABLE_ATTRIBUTES) {
    const current = element.getAttribute(attribute);
    if (current == null) continue;
    if (!originals.has(attribute)) {
      const reverse = ENGLISH_BY_CHINESE.get(current);
      const translated = translate(current, "zh-CN");
      if (reverse) originals.set(attribute, reverse);
      else if (translated !== current) originals.set(attribute, current);
      else continue;
    }
    const original = originals.get(attribute) ?? current;
    const next = locale === "zh-CN" ? translate(original, "zh-CN") : original;
    if (current !== next) element.setAttribute(attribute, next);
  }
}

function translateSubtree(root: Node, locale: Locale) {
  if (root.nodeType === Node.TEXT_NODE) {
    translateTextNode(root as Text, locale);
    return;
  }
  if (!(root instanceof Element)) return;
  translateAttributes(root, locale);
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT);
  let current = walker.nextNode();
  while (current) {
    if (current.nodeType === Node.TEXT_NODE) translateTextNode(current as Text, locale);
    else translateAttributes(current as Element, locale);
    current = walker.nextNode();
  }
}

export function translate(source: string, locale?: Locale) {
  const resolvedLocale = locale ?? (
    typeof window === "undefined"
      ? "en-US"
      : window.localStorage.getItem("semantica-locale") === "en-US"
        ? "en-US"
        : "zh-CN"
  );
  if (resolvedLocale !== "zh-CN") return source;
  const loadingNodes = source.match(/^Loading nodes ([\d,]+)(?: of ([\d,]+))?$/);
  if (loadingNodes) {
    return loadingNodes[2]
      ? `正在加载节点 ${loadingNodes[1]} / ${loadingNodes[2]}`
      : `正在加载节点 ${loadingNodes[1]}`;
  }
  const loadingEdges = source.match(/^Loading edges ([\d,]+)(?: of ([\d,]+))?$/);
  if (loadingEdges) {
    return loadingEdges[2]
      ? `正在加载关系 ${loadingEdges[1]} / ${loadingEdges[2]}`
      : `正在加载关系 ${loadingEdges[1]}`;
  }
  return ZH_CN[source] ?? source;
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocale] = useState<Locale>(() => {
    const saved = window.localStorage.getItem("semantica-locale");
    return saved === "en-US" ? "en-US" : "zh-CN";
  });

  useEffect(() => {
    window.localStorage.setItem("semantica-locale", locale);
    document.documentElement.lang = locale;
    translateSubtree(document.body, locale);
    const observer = new MutationObserver((mutations) => {
      for (const mutation of mutations) {
        if (mutation.type === "characterData") {
          translateTextNode(mutation.target as Text, locale);
        } else if (mutation.type === "attributes") {
          translateAttributes(mutation.target as Element, locale);
        } else {
          mutation.addedNodes.forEach((node) => translateSubtree(node, locale));
        }
      }
    });
    observer.observe(document.body, {
      subtree: true,
      childList: true,
      characterData: true,
      attributes: true,
      attributeFilter: [...TRANSLATABLE_ATTRIBUTES],
    });
    return () => observer.disconnect();
  }, [locale]);

  const value = useMemo<I18nContextValue>(() => ({
    locale,
    setLocale,
    tr: (source) => translate(source, locale),
  }), [locale]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  return useContext(I18nContext);
}
