# 快速启动指南

## 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

## 配置环境变量

编辑 `.env` 文件，填入你的 API Key：

```env
SILICONFLOW_API_KEY=your-api-key-here
SILICONFLOW_MODEL=deepseek-ai/DeepSeek-V3
ENABLE_RAG=true
```

## 测试运行

```bash
# 测试 LangChain + RAG 功能
python test_langchain_rag.py

# 启动服务
python -m app.main
```

## 访问 API

服务启动后访问：
- API 文档：http://127.0.0.1:8000/docs
- 健康检查：http://127.0.0.1:8000/

## 2-Step RAG 工作流程

```
任务请求
    ↓
Step 1: RAG 检索相关上下文（知识库）
    ↓
Step 2: LLM 基于增强的 Prompt 生成任务分解
    ↓
返回结果
```

## 默认知识库

系统内置 10 条最佳实践：
- 任务拆解原则（SMART）
- 时间规划方法（番茄工作法、时间块）
- 学习方法论（费曼学习法、刻意练习）
- OKR 目标设定
- 技能学习阶段
- 防止拖延策略
- 项目管理要素
- 学习路径设计
- 周计划制定要点
- 技术项目开发流程

## 配置说明

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| ENABLE_RAG | true | 是否启用 RAG |
| RAG_TOP_K | 5 | 检索返回数量 |
| RAG_SCORE_THRESHOLD | 0.3 | 相似度阈值 |
| VECTOR_STORE_PATH | backend/data/vector_store | 向量存储路径 |

## 故障排查

### RAG 初始化失败
```bash
# 检查向量存储目录是否存在
ls backend/data/vector_store

# 如果不存在，会在首次运行时自动创建
```

### 嵌入模型下载失败
```bash
# 手动下载 HuggingFace 模型
pip install huggingface_hub
huggingface-cli download shibing624/text2vec-base-chinese
```

### API 调用失败
```bash
# 检查 API Key 是否正确
cat .env | grep SILICONFLOW_API_KEY

# 测试 API 连接
python test_langchain_rag.py
```

## 🆕 Task Decomposer V2.0 架构

恭喜！后端代码已经按照任务拆解器最佳实践进行了全面重构。

### 新架构特点

```
task_decomposer/
├── schemas/           # 统一的数据模型 (Plan Schema)
├── prompts/          # 提示词模板
├── chains/           # LangChain 链路
│   ├── decompose.py  # 任务拆解
│   ├── clarify.py    # 澄清问题
│   ├── evaluate.py   # 质量评估
│   └── router.py     # 意图路由
├── rag/              # RAG 模块 (ingest + retriever)
├── memory/           # 记忆模块 (session + profile)
├── tools/            # Function Calling 工具
├── orchestrator.py   # 主编排器
└── app.py           # API 入口
```

### 快速测试新架构

```bash
# 运行测试套件
python test_task_decomposer_v2.py

# 启动新的 API 服务
cd task_decomposer
python app.py

# 或使用 CLI
python app.py decompose "开发一个待办事项小程序"
```

### 核心功能

- ✅ **智能路由**: 自动判断需要澄清还是直接拆解
- ✅ **质量评估**: 自动评估计划质量并迭代改进
- ✅ **RAG 增强**: 结合知识库提供最佳实践
- ✅ **用户画像**: 跨会话记忆用户偏好
- ✅ **Function Tools**: 支持搜索、文档生成等工具

### 使用示例

```python
from task_decomposer.orchestrator import TaskDecomposerOrchestrator

orchestrator = TaskDecomposerOrchestrator(
    api_key="your_api_key",
    enable_rag=True
)

result = await orchestrator.decompose_task(
    goal="开发一个待办事项小程序",
    constraints=["预算有限", "一周内上线"]
)

if result["status"] == "completed":
    plan = result["plan"]
    print(f"✓ 生成了 {len(plan.tasks)} 个任务")
```

### 学习路径

详见 [task_decomposer/README.md](task_decomposer/README.md)

1. **Week 1**: 基础组件 (Schema, DecomposeChain, ClarifyChain)
2. **Week 2**: 高级功能 (RAG, Memory, EvaluateChain)
3. **Week 3**: 工作流集成 (Router, Orchestrator, Tools)

---

## 更多信息

- **V2.0 详细文档**: [task_decomposer/README.md](task_decomposer/README.md)
- **旧版文档**: [LANGCHAIN_RAG_README.md](LANGCHAIN_RAG_README.md)
- **改造总结**: [MIGRATION_SUMMARY.md](MIGRATION_SUMMARY.md)
