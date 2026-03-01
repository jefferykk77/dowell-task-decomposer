# LangChain 框架 + 2-Step RAG 改造说明

## 改造概述

后端已从直接使用 OpenAI SDK 改造为使用 **LangChain 框架**，并实现了 **2-Step RAG（检索增强生成）** 功能。

## 架构变化

### 改造前
```
用户请求 → DecomposerService → OpenAI API → 返回结果
```

### 改造后（2-Step RAG）
```
用户请求 → DecomposerService
    ↓
    ├─→ Step 1: RAG 检索
    │   ├─ 构建查询（任务标题 + 上下文）
    │   ├─ 向量检索（FAISS + Embeddings）
    │   └─ 获取相关上下文
    ↓
    ├─→ Step 2: LLM 生成
    │   ├─ 构建 Prompt（用户上下文 + RAG 上下文）
    │   ├─ LangChain Chain 调用
    │   └─ 解析并返回结果
    ↓
返回结果
```

## 新增文件

### 1. [app/services/rag_service.py](app/services/rag_service.py)
RAG 服务模块，提供：
- 向量存储管理（FAISS）
- 文档嵌入和检索
- 知识库创建和加载
- 默认知识库（包含任务管理、学习方法等最佳实践）

### 2. [backend/.env.example](backend/.env.example)
新增配置项示例文件

## 修改文件

### 1. [app/services/decomposer.py](app/services/decomposer.py)
- ✅ 使用 LangChain 的 `ChatOpenAI` 替代直接调用 OpenAI API
- ✅ 使用 `ChatPromptTemplate` 和 `LLMChain` 构建提示链
- ✅ 实现 `_ai_decompose_with_rag()` 方法，集成 2-Step RAG
- ✅ 新增 `_build_rag_query()` 构建检索查询
- ✅ 增强 `_build_enhanced_prompt()` 将 RAG 上下文注入 Prompt

### 2. [app/core/config.py](app/core/config.py)
新增配置项：
```python
# LangChain 配置
LANGCHAIN_TRACING_V2
LANGCHAIN_API_KEY
LANGCHAIN_PROJECT

# RAG 配置
ENABLE_RAG                # 是否启用 RAG
RAG_TOP_K                # 检索返回数量（默认 5）
RAG_SCORE_THRESHOLD      # 相似度阈值（默认 0.3）
VECTOR_STORE_PATH        # 向量存储路径
EMBEDDING_MODEL          # 嵌入模型
```

### 3. [requirements.txt](requirements.txt)
新增依赖：
```
langchain==0.1.0
langchain-openai==0.0.2
langchain-community==0.0.10
chromadb==0.4.22
faiss-cpu==1.7.4
sentence-transformers==2.3.1
tiktoken==0.5.2
```

## 2-Step RAG 工作原理

### Step 1: RAG 检索（拆解前）
在任务拆解前，先根据任务信息检索相关知识：

1. **构建查询**：结合任务标题、长期目标、完成标准等
2. **向量检索**：在知识库中检索最相关的 K 个文档
3. **获取上下文**：返回格式化的相关知识

```python
# 代码示例（decomposer.py:136-156）
rag_context = ""
if self._rag_enabled and self._rag_service:
    query = self._build_rag_query(title, goal_context, current_context)
    rag_context = self._rag_service.retrieve_context_as_string(
        query=query,
        top_k=settings.RAG_TOP_K,
        score_threshold=settings.RAG_SCORE_THRESHOLD
    )
```

### Step 2: LLM 生成（拆解）
将 RAG 检索到的上下文注入 Prompt，增强 LLM 理解：

```python
# 代码示例（decomposer.py:284-291）
if rag_context:
    prompt = f"""{prompt}

{rag_context}

请参考以上相关知识库中的最佳实践来制定任务拆解方案。
"""
```

## 默认知识库内容

系统内置了 10 条最佳实践知识：

1. **任务拆解原则** - SMART 原则、任务分解、里程碑设置
2. **时间规划最佳实践** - 黄金时间、番茄工作法、时间块管理
3. **学习方法论** - 费曼学习法、刻意练习、间隔重复
4. **OKR 方法** - 目标与关键结果设定
5. **技能学习阶段** - 了解、模仿、实践、深入、精通
6. **防止拖延策略** - 两分钟原则、五分钟启动法
7. **项目管理要素** - 范围、时间、质量、风险、沟通管理
8. **学习路径设计** - 目标明确、评估现状、资源选择
9. **周计划制定要点** - 回顾、重点、缓冲、每日仪式
10. **技术项目开发流程** - 需求分析、技术选型、迭代开发

## 安装和使用

### 1. 安装依赖
```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量
复制 `.env.example` 为 `.env` 并填写配置：

```bash
# 必填：硅基流动 API Key（用于 LLM）
SILICONFLOW_API_KEY=your-key

# 可选：启用/禁用 RAG（默认启用）
ENABLE_RAG=true
```

### 3. 启动服务
```bash
python -m app.main
```

首次启动时，系统会自动：
1. 创建默认知识库
2. 生成向量嵌入
3. 保存向量存储到 `backend/data/vector_store`

## 关键优势

### 1. 更好的任务理解
- RAG 提供领域知识（任务管理、学习方法等）
- LLM 基于最佳实践生成更专业的拆解方案

### 2. 框架化架构
- LangChain 提供标准化接口
- 易于扩展和替换 LLM 提供商
- 支持提示词模板复用

### 3. 知识可扩展
- 可以轻松添加新的知识文档
- 支持持久化向量存储
- 可配置的检索参数

### 4. 向后兼容
- 保留规则分解作为回退方案
- 可以通过配置禁用 RAG
- API 接口保持不变

## 配置参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `ENABLE_RAG` | `true` | 是否启用 RAG 功能 |
| `RAG_TOP_K` | `5` | 检索返回的最相关文档数量 |
| `RAG_SCORE_THRESHOLD` | `0.3` | 相似度阈值（0-1），低于此值的结果被过滤 |
| `EMBEDDING_MODEL` | `shibing624/text2vec-base-chinese` | 嵌入模型（支持中文） |
| `VECTOR_STORE_PATH` | `backend/data/vector_store` | 向量存储保存路径 |

## 扩展知识库

### 添加自定义知识

```python
from app.services.rag_service import get_rag_service

rag = get_rag_service()

# 添加新文档
texts = [
    "你的自定义知识1",
    "你的自定义知识2"
]

metadata = [
    {"category": "custom", "title": "知识1"},
    {"category": "custom", "title": "知识2"}
]

rag.add_documents(texts, metadata)

# 保存
rag.save_vector_store("path/to/save")
```

## 故障排查

### Q: RAG 检索失败或返回空结果
A: 检查以下项：
1. `ENABLE_RAG=true` 是否设置
2. 向量存储文件是否存在
3. 嵌入模型是否正确下载（首次使用会下载模型）

### Q: LangChain 初始化失败
A: 确保安装了所有依赖：
```bash
pip install langchain langchain-openai langchain-community
```

### Q: 使用哪个 API Key？
A: 推荐使用硅基流动（SILICONFLOW_API_KEY）：
- 支持多种模型（DeepSeek-V3、Qwen 等）
- 价格更优
- 国内访问稳定

## 性能考虑

- **首次启动**：需要下载嵌入模型（~400MB）和构建向量索引
- **后续启动**：直接加载向量存储，速度快
- **RAG 检索**：通常在 100ms 内完成（取决于文档数量）
- **LLM 生成**：取决于模型和任务复杂度

## 下一步优化建议

1. **向量数据库**：可升级到 Chroma/Pinecone（支持更大规模）
2. **混合检索**：结合关键词检索和向量检索
3. **知识库更新**：支持在线添加和删除文档
4. **多轮对话**：结合 LangChain Memory 实现对话历史
5. **流式输出**：使用 LangChain StreamingToken 优化用户体验

## 相关文档

- [LangChain 官方文档](https://python.langchain.com/)
- [FAISS 向量检索](https://github.com/facebookresearch/faiss)
- [Sentence Transformers](https://www.sbert.net/)
