# Task Decomposer V2.0

基于 LangChain 的智能任务拆解系统，从模糊需求到可执行计划的完整工作流。

## 🎯 核心特性

- **结构化输出**: 统一的 Plan Schema，确保输出格式稳定
- **智能路由**: 自动判断需要澄清还是直接拆解
- **RAG 增强**: 结合知识库提供行业最佳实践
- **质量评估**: 自动评估计划质量并迭代改进
- **用户画像**: 跨会话记忆用户偏好和历史
- **Function Calling**: 支持工具调用（搜索、文档生成等）

## 📁 架构设计

```
task_decomposer/
├── schemas/           # Pydantic 数据模型
│   ├── plan.py       # 统一的 Plan Schema
│   └── request.py    # 请求/响应 Schema
│
├── prompts/          # 提示词模板
│   ├── decompose_prompts.py
│   ├── clarify_prompts.py
│   ├── evaluate_prompts.py
│   └── router_prompts.py
│
├── chains/           # LangChain 链路
│   ├── base.py       # Chain 基类
│   ├── decompose.py  # 任务拆解链
│   ├── clarify.py    # 澄清问题链
│   ├── evaluate.py   # 质量评估链
│   └── router.py     # 意图路由链
│
├── rag/              # RAG 模块
│   ├── ingest.py     # 文档加载/切分/嵌入
│   └── retriever.py  # 向量检索
│
├── memory/           # 记忆模块
│   ├── session_store.py   # 短期记忆（会话）
│   └── profile_store.py   # 长期记忆（用户画像）
│
├── tools/            # Function Calling 工具
│   ├── base.py
│   ├── search_tools.py
│   └── document_tools.py
│
├── orchestrator.py   # 主编排器
└── app.py           # FastAPI + CLI 入口
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install langchain langchain-openai langchain-community langchain-text-splitters
pip install chromadb python-dotenv pydantic
```

### 2. 配置环境变量

创建 `.env` 文件：

```env
SILICONFLOW_API_KEY=your_api_key_here
SILICONFLOW_API_BASE=https://api.siliconflow.cn/v1
SILICONFLOW_MODEL=deepseek-ai/DeepSeek-V3

ENABLE_RAG=true
VECTOR_STORE_PATH=./data/vector_store
KNOWLEDGE_BASE_PATH=./data/knowledge_base
```

### 3. 运行测试

```bash
cd backend
python test_task_decomposer_v2.py
```

### 4. 启动 API 服务

```bash
python task_decomposer/app.py
```

访问 http://localhost:8000/docs 查看 API 文档。

## 📚 使用示例

### Python SDK

```python
import asyncio
from task_decomposer.orchestrator import TaskDecomposerOrchestrator

async def main():
    orchestrator = TaskDecomposerOrchestrator(
        api_key="your_api_key",
        enable_rag=True
    )

    result = await orchestrator.decompose_task(
        goal="开发一个待办事项小程序",
        context="用于个人任务管理",
        constraints=["预算有限", "一周内上线"],
        user_id="user123",
        enable_evaluation=True
    )

    if result["status"] == "completed":
        plan = result["plan"]
        print(f"生成了 {len(plan.tasks)} 个任务")
        print(f"质量评分: {result['evaluation'].overall_score}")

asyncio.run(main())
```

### HTTP API

```bash
curl -X POST "http://localhost:8000/api/v2/decompose" \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "开发一个待办事项小程序",
    "context": "用于个人任务管理",
    "constraints": ["预算有限", "一周内上线"],
    "user_id": "user123",
    "enable_evaluation": true
  }'
```

### CLI 命令行

```bash
python task_decomposer/app.py decompose "开发一个待办事项小程序"
```

## 🔄 工作流程

```
用户输入
    ↓
[Router] 意图识别
    ↓
    ├─→ [Clarify] 生成澄清问题 → 用户回答 → 回到 Router
    │
    ├─→ [Decompose] 生成任务计划
    │           ↓
    │       [Evaluate] 质量评估
    │           ↓
    │       不合格 → 重写 → 再评估
    │           ↓
    │       合格 → 输出
    │
    └─→ [RAG Decompose] 检索知识 → 拆解 → ...
```

## 📦 核心组件说明

### 1. Plan Schema

统一的任务计划数据模型：

```python
{
  "goal": "用户目标",
  "context": "背景信息",
  "constraints": ["约束条件"],
  "assumptions": ["做出的假设"],
  "open_questions": [
    {"id": "Q1", "question": "问题", "critical": true}
  ],
  "milestones": [
    {"id": "M1", "title": "里程碑", "definition_of_done": "验收标准"}
  ],
  "tasks": [
    {
      "id": "T1",
      "title": "任务标题",
      "description": "详细描述",
      "estimate_hours": 4,
      "priority": "P1",
      "risk": "低",
      "depends_on": ["T0"],
      "definition_of_done": "验收标准"
    }
  ]
}
```

### 2. Chains

#### DecomposeChain
- **输入**: 用户目标 + 上下文 + 约束
- **输出**: PlanSchema
- **功能**: 生成结构化任务计划

#### ClarifyChain
- **输入**: 模糊的用户目标
- **输出**: 澄清问题列表
- **功能**: 识别信息缺口，生成关键问题

#### EvaluateChain
- **输入**: PlanSchema
- **输出**: 评分 + 问题列表
- **功能**: 评估计划质量，提供改进建议

#### RouterChain
- **输入**: 用户输入
- **输出**: 路由决策
- **功能**: 判断走哪条处理流程

### 3. RAG 模块

#### RAGIngestor
- 加载文档（txt, md, json）
- 智能切分（支持中文）
- 生成向量嵌入
- 持久化存储

#### RAGRetriever
- 向量相似度检索
- 阈值过滤
- 格式化输出

### 4. Memory 模块

#### SessionStore（短期）
- 存储单次会话状态
- 记录用户回答
- 保存计划版本

#### ProfileStore（长期）
- 用户偏好设置
- 历史任务记录
- 任务模板库

### 5. Tools

- **WebSearchTool**: 网络搜索
- **DocSearchTool**: 内部文档检索
- **CreateDocTool**: 生成文档
- **SendEmailTool**: 发送邮件

## 🎓 学习路径

按照这个顺序学习各个组件：

### Part A: 基础组件

**Day 3: 结构化输出 (Syntax)**
- 学习 `schemas/plan.py`
- 理解 Pydantic 模型设计
- 实现 `DecomposeChain`

**Day 4: 知识增强 (RAG)**
- 学习 `rag/ingest.py`
- 学习 `rag/retriever.py`
- 理解向量检索原理

**Day 5: 上下文记忆 (Memory)**
- 学习 `memory/session_store.py`
- 学习 `memory/profile_store.py`
- 理解 STM vs LTM

### Part B: 工作流

**Day 6: 路由 (Routing)**
- 学习 `chains/router.py`
- 理解意图分类

**Day 7: 并行编排 (Orchestrator)**
- 学习 `orchestrator.py`
- 理解多 Worker 协作

**Day 8: 质量评估 (Evaluator)**
- 学习 `chains/evaluate.py`
- 实现评估-重写循环

### Part C: Agent

**Day 9: ReAct 原理**
- 理解"思考-行动"循环
- 实现动态信息收集

**Day 10: Tools 集成**
- 学习 `tools/`
- 实现 Function Calling

## 🔧 配置选项

| 环境变量 | 默认值 | 说明 |
|---------|-------|------|
| `SILICONFLOW_API_KEY` | - | LLM API 密钥 |
| `SILICONFLOW_API_BASE` | `https://api.siliconflow.cn/v1` | API 基础 URL |
| `SILICONFLOW_MODEL` | `deepseek-ai/DeepSeek-V3` | 模型名称 |
| `ENABLE_RAG` | `true` | 是否启用 RAG |
| `VECTOR_STORE_PATH` | `./data/vector_store` | 向量存储路径 |
| `KNOWLEDGE_BASE_PATH` | `./data/knowledge_base` | 知识库路径 |

## 🐛 调试技巧

### 启用详细日志

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 查看中间结果

```python
# 查看路由结果
router_result = orchestrator._router_chain.run("用户输入")
print(f"意图: {router_result.intent}")

# 查看计划版本
session = SessionStore()
session.save_plan_version(plan, version="v1")
print(session.get_all_versions())
```

## 📊 性能优化

1. **批量处理**: 使用 `batch_run()` 处理多个任务
2. **缓存**: 启用向量存储缓存
3. **并行**: 多个 Chain 并行执行
4. **模型选择**: 简单任务用小模型

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License
