# AI 开发篇教学设计

## 模块8：LangChain 基础

### 知识点讲解

#### 1. Messages 心智模型

LangChain 使用消息列表来与大语言模型交互，每种消息类型有明确的角色定位：

| 消息类型 | 角色 | 典型用途 |
|---------|------|---------|
| `SystemMessage` | 系统提示词 | 设定 AI 的身份、规则、输出格式要求 |
| `HumanMessage` | 用户输入 | 用户的提问、指令、任务描述 |
| `AIMessage` | AI 回复 | 模型的输出（也可用作 few-shot 示例） |

**核心理解**：多轮对话 = 消息列表的不断追加

```
[system] → [human, ai] → [human, ai] → [human, ai]
   ↓           ↓            ↓            ↓
设定规则    第一轮       第二轮       第三轮
```

---

#### 2. ChatPromptTemplate（变量注入）

```python
from langchain.prompts import ChatPromptTemplate

# 方式一：from_messages（推荐）
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一位{role}，擅长{skill}"),
    ("human", "请帮我完成：{task}")
])

# 方式二：从模板字符串构建
template = ChatPromptTemplate.from_template(
    "将以下目标拆解为任务：{goal}"
)

# 调用时注入变量
messages = prompt.invoke({"role": "项目经理", "skill": "任务拆解", "task": "学习 Python"})
```

---

#### 3. ChatOpenAI（模型配置）

```python
from langchain_openai import ChatOpenAI

# 标准 OpenAI
llm = ChatOpenAI(
    model="gpt-4",
    api_key="sk-xxx",
    temperature=0.7
)

# 兼容 OpenAI 格式的第三方服务（如 SiliconFlow）
llm = ChatOpenAI(
    model="deepseek-ai/DeepSeek-V3",
    openai_api_key="your-api-key",
    openai_api_base="https://api.siliconflow.cn/v1",  # 关键：自定义 base_url
    temperature=0.3
)

# 运行方式
response = llm.invoke("你好")      # 同步调用
response = llm.batch(["你好", "再见"])  # 批量调用
for chunk in llm.stream("讲个故事"):   # 流式输出
    print(chunk.content, end="")
```

---

#### 4. OutputParser（结构化输出）

LLM 输出通常是字符串，需要解析为结构化数据：

```python
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

# 1. 定义输出 Schema
class TaskSchema(BaseModel):
    title: str = Field(description="任务标题")
    hours: float = Field(description="预估工时")
    priority: str = Field(description="优先级：P0/P1/P2")

# 2. 创建 Parser
parser = PydanticOutputParser(pydantic_object=TaskSchema)

# 3. 获取格式指令
format_instructions = parser.get_format_instructions()
# 输出类似："The output should be formatted as a JSON instance..."

# 4. 放入 Prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", "输出 JSON 格式任务\n{format_instructions}"),
    ("human", "{task}")
])

# 5. 解析输出
chain = prompt | llm | parser
result = chain.invoke({"task": "写一个登录页面", "format_instructions": format_instructions})
# result 是 TaskSchema 实例，可直接访问 result.title
```

---

#### 5. Runnable 统一接口

所有 LangChain 组件都实现 `Runnable` 接口，统一调用方式：

```python
# 所有组件都支持这三种调用方式
component.invoke(input_data)      # 单次调用
component.batch([input1, input2]) # 批量调用
component.stream(input_data)      # 流式调用
```

---

#### 6. LCEL（LangChain Expression Language）

用 `|` 管道符串联组件，形成链：

```python
# 最小链
chain = prompt | llm | parser

# 等价于
# messages = prompt.invoke(input)
# ai_response = llm.invoke(messages)
# result = parser.invoke(ai_response)
```

---

#### 7. 并行与透传

```python
from langchain.runnables import RunnablePassthrough, RunnableParallel

# RunnablePassthrough：透传输入
chain = {
    "context": retriever | (lambda docs: "\n".join(d.page_content for d in docs)),
    "question": RunnablePassthrough()  # 原样传入
} | prompt | llm | parser

# RunnableParallel：并行执行
chain = RunnableParallel(
    summary=summary_chain,    # 并行运行
    keywords=keyword_chain    # 同时运行
)
```

---

### 在本项目中的使用

#### 1. 消息模板的使用位置

**文件**：[chains/base.py:49-65](../backend/task_decomposer/chains/base.py)

```python
def _build_chain(self, system_prompt: str, user_prompt_template: str):
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),      # 系统角色设定
        ("human", user_prompt_template) # 用户输入模板
    ])
    self._chain = LLMChain(llm=self._llm, prompt=prompt_template)
```

**数据流向**：
```
system_prompt（如 DECOMPOSE_SYSTEM_PROMPT）
    ↓
user_prompt_template（带 {goal} 等变量）
    ↓
ChatPromptTemplate.from_messages() → List[Message]
    ↓
LLMChain.run(input={...}) → AI 响应字符串
```

---

#### 2. LLM 初始化（SiliconFlow 代理）

**文件**：[orchestrator.py:54-60](../backend/task_decomposer/orchestrator.py)

```python
from langchain_openai import ChatOpenAI

self._llm = ChatOpenAI(
    model="deepseek-ai/DeepSeek-V3",           # 使用 DeepSeek 模型
    openai_api_key=api_key,                     # 从配置读取
    openai_api_base="https://api.siliconflow.cn/v1",  # ← 关键：中转服务
    temperature=0.3                              # 低温度，保证输出稳定
)
```

**教学点**：很多国内服务（SiliconFlow、OneAPI）兼容 OpenAI 接口，只需改 `base_url`。

---

#### 3. 自定义 OutputParser

**文件**：[chains/base.py:67-115](../backend/task_decomposer/chains/base.py)

项目没有用 PydanticOutputParser，而是自己实现了 `_parse_json_response()`：

```python
def _parse_json_response(self, response: str) -> Dict[str, Any]:
    # 1. 清理 Markdown 标记
    content = re.sub(r'^```json\s*', '', content.strip())
    content = re.sub(r'\s*```$', '', content.strip())

    # 2. 修复常见 JSON 错误（中文引号、单引号、尾随逗号）
    content = self._repair_json(content)

    # 3. 修复截断的 JSON（补全括号）
    content = self._fix_truncated_json(content)

    # 4. 解析
    return json.loads(content)
```

**为什么这样设计**：LLM 输出 JSON 不稳定，需要鲁棒的修复逻辑。

---

#### 4. 链路的实际调用

**文件**：[chains/decompose.py:118-125](../backend/task_decomposer/chains/decompose.py)

```python
# 方式一：使用 LLMChain（旧版）
if self._chain:
    response = self._chain.run(input=enhanced_prompt)

# 方式二：直接调用 LLM（回退）
elif self._llm:
    response = self._llm.invoke(enhanced_prompt).content
```

**版本说明**：项目使用旧版 `LLMChain`，新版 LangChain 推荐用 LCEL：
```python
# 新版写法（教学时推荐）
chain = prompt | llm | parser
response = chain.invoke({"goal": "学习 Python"})
```

---

## 模块9：RAG 检索增强生成

### 知识点讲解

#### 核心理念

RAG = **检索** + **生成**，让 LLM 基于外部知识回答，减少幻觉。

```
用户问题
    ↓
【检索阶段】在知识库中找相关文档 → 得到 topK 个片段
    ↓
【生成阶段】将问题+片段一起塞给 LLM → 生成答案
```

---

#### 流水线一：Ingest（知识库构建）

```
原始文档
    ↓
【Loader】加载为 Document 对象
    ↓
【Splitter】切分成小块（chunk_size=500, overlap=50）
    ↓
【Embedding】向量化（文本 → 1536维向量）
    ↓
【VectorStore】存入向量数据库
```

**代码模板**：
```python
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

# 1. 加载
loader = TextLoader("knowledge.txt")
documents = loader.load()

# 2. 切分
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""]
)
splits = splitter.split_documents(documents)

# 3. 嵌入
embeddings = OpenAIEmbeddings(base_url="https://api.siliconflow.cn/v1")

# 4. 存储
vectorstore = Chroma.from_documents(
    documents=splits,
    embedding=embeddings,
    persist_directory="./chroma_db"
)
vectorstore.persist()  # 持久化到磁盘
```

---

#### 流水线二：Query（检索与生成）

```
用户问题
    ↓
【Embedding】问题向量化
    ↓
【Similarity Search】在向量库中找最相似的 topK 个 chunk
    ↓
【Filter】根据 score_threshold 过滤
    ↓
【Assemble】组装成 Prompt：问题 + 检索到的上下文
    ↓
【LLM】生成答案
```

**代码模板**：
```python
# 1. 加载向量库
vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embeddings
)

# 2. 检索
results = vectorstore.similarity_search_with_score(
    query="如何学习 Python？",
    k=3  # 返回前 3 个
)

# 3. 过滤（Chroma 用距离，越小越相似）
threshold = 0.5
filtered = [(doc, score) for doc, score in results if score <= threshold]

# 4. 组装上下文
context = "\n\n".join([doc.page_content for doc, _ in filtered])

# 5. 生成
prompt = f"""根据以下知识回答问题：

知识：
{context}

问题：{query}
"""
answer = llm.invoke(prompt).content
```

---

#### 关键参数调优

| 参数 | 作用 | 调优建议 |
|-----|------|---------|
| `chunk_size` | 每块大小 | 太小 → 语义不完整；太大 → 检索不精准。推荐 300-800 |
| `chunk_overlap` | 块之间重叠 | 保证上下文连贯，推荐 10%-20% |
| `top_k` | 返回几个结果 | 推荐 3-5，太多会稀释注意力 |
| `score_threshold` | 相似度阈值 | Chroma 用距离，推荐 0.3-0.6；需要实测调优 |

---

### 在本项目中的使用

#### 1. Ingest 实现

**文件**：[rag/ingest.py:24-58](../backend/task_decomposer/rag/ingest.py)

```python
class RAGIngestor:
    def __init__(self, embedding_model, chunk_size=500, chunk_overlap=50):
        # 中文友好的切分器
        self._text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""]
        )
```

**一站式入口**：[ingest.py:176-215](../backend/task_decomposer/rag/ingest.py)

```python
def ingest_and_store(self, source: str, source_type: str = "file"):
    # 1. 加载文档
    if source_type == "file":
        documents = self.load_text_file(source)

    # 2. 切分
    splits = self.split_documents(documents)

    # 3. 创建向量存储
    vector_store = Chroma.from_documents(
        documents=splits,
        embedding=self._embedding_model,
        persist_directory=self._vector_store_path
    )

    return vector_store
```

---

#### 2. Retriever 实现

**文件**：[rag/retriever.py:76-120](../backend/task_decomposer/rag/retriever.py)

```python
def retrieve(self, query: str, top_k: int = None, score_threshold: float = None):
    # 相似度搜索
    results = self._vector_store.similarity_search_with_score(query, k=top_k)

    # 根据阈值过滤
    threshold = score_threshold or self._score_threshold
    if threshold > 0:
        filtered_results = [
            (doc, score) for doc, score in results
            if score <= threshold  # Chroma：距离越小越相似
        ]
        return [doc for doc, _ in filtered_results]
```

**可解释检索**：[retriever.py:189-213](../backend/task_decomposer/rag/retriever.py)

```python
def retrieve_with_metadata(self, query: str) -> List[Dict[str, Any]]:
    """返回包含元数据的结果，便于调试和展示"""
    docs = self.retrieve(query, top_k)

    results = []
    for doc in docs:
        results.append({
            "content": doc.page_content,   # 检索到的内容
            "metadata": doc.metadata       # 来源、章节等信息
        })
    return results
```

**教学点**：返回 metadata 让用户知道"答案从哪来"，增加可信度。

---

#### 3. RAG 集成到链路

**文件**：[chains/base.py:321-359](../backend/task_decomposer/chains/base.py)

```python
def _enhance_prompt_with_rag(self, base_prompt: str, query: str, top_k: int = 3):
    if not self._enable_rag:
        return base_prompt

    # 检索相关上下文
    rag_context = self._rag_service.retrieve_context_as_string(query=query, top_k=top_k)

    if rag_context:
        return f"""{base_prompt}

**相关知识库参考**：
{rag_context}

请参考以上最佳实践来完成任务。
"""

    return base_prompt
```

**在任务拆解中的调用**：[chains/decompose.py:96-101](../backend/task_decomposer/chains/decompose.py)

```python
# RAG 增强
enhanced_prompt = self._enhance_prompt_with_rag(
    base_prompt,    # 原始提示词
    query=rag_query or goal  # 检索查询
)
```

---

## 模块10：提示词工程

### 知识点讲解

提示词不是"写得好"就行，要**工程可维护**：

| 维度 | 说明 |
|-----|------|
| **结构化输出** | 输出格式固定，最好直接对应 Pydantic Schema |
| **变量管理** | 明确哪些是变量，使用模板注入 |
| **版本管理** | 提示词需要版本控制，A/B 测试 |
| **测试覆盖** | 边界条件作为 few-shot 示例 |

---

### 在本项目中的使用

#### 1. Prompt Registry 设计

项目将提示词按功能分类存放在 `prompts/` 目录：

```
prompts/
├── __init__.py           # 统一导出
├── decompose_prompts.py  # 任务拆解
├── clarify_prompts.py    # 澄清问题
├── evaluate_prompts.py   # 质量评估
└── router_prompts.py     # 意图路由
```

**统一导出**：[prompts/__init__.py](../backend/task_decomposer/prompts/__init__.py)

```python
from .decompose_prompts import DECOMPOSE_SYSTEM_PROMPT, build_decompose_prompt
from .clarify_prompts import CLARIFY_SYSTEM_PROMPT, build_clarify_prompt
from .evaluate_prompts import EVALUATE_SYSTEM_PROMPT
from .router_prompts import ROUTER_SYSTEM_PROMPT
```

---

#### 2. 任务拆解 Prompt（输出结构稳定）

**文件**：[prompts/decompose_prompts.py:5-20](../backend/task_decomposer/prompts/decompose_prompts.py)

```python
DECOMPOSE_SYSTEM_PROMPT = """你是一位资深的项目经理和任务拆解专家...

输出要求：
- 必须严格输出符合 Schema 的纯 JSON 格式
- 不要包含任何 Markdown 标记（如 ```json）
- 确保所有属性名都使用双引号
"""
```

**JSON Schema 要求**：[decompose_prompts.py:56-134](../backend/task_decomposer/prompts/decompose_prompts.py)

```python
请严格按照以下 JSON Schema 输出：
{
  "goal": "用户目标",
  "constraints": [{"type": "time", "description": "描述", "value": "值"}],
  "assumptions": ["假设1", "假设2"],
  "open_questions": [{"id": "Q1", "question": "问题", "critical": true}],
  "milestones": [{"id": "M1", "title": "标题", ...}],
  "tasks": [{"id": "T1", "level": "month", ...}]
}
```

**教学点**：Prompt 中直接写明 Schema，让 LLM 输出稳定格式。

---

#### 3. Few-shot 示例 = 边界条件库

```python
# 示例：在 clarify_prompts.py 中
CLARIFY_EXAMPLES = """
用户输入："做个网站"
输出问题：["网站类型是什么？", "目标用户是谁？", "预算多少？"]

用户输入："3个月学习 Python"
输出问题：["当前编程基础？", "每天可用时间？"]
"""
```

**教学点**：Few-shot 不是"越多越好"，是覆盖"边界条件"。

---

## 模块11：智能编排

### 知识点讲解

智能编排 = **状态机** + **管线**，决定下一步做什么。

```
                    ┌─────────────┐
                    │  用户输入   │
                    └──────┬──────┘
                           ↓
                   ┌───────────────┐
                   │  意图路由     │ ← 需要澄清？还是直接拆解？
                   └───┬───────┬───┘
                       │       │
              需要澄清 │       │ 直接拆解
                       ↓       ↓
              ┌────────────┐  ┌────────────┐
              │ 生成问题   │  │ 生成计划   │
              └────────────┘  └─────┬──────┘
                                     ↓
                              ┌─────────────┐
                              │  质量评估   │ ← 达标吗？
                              └───┬────┬────┘
                                  │    │
                             不达标 │    │ 达标
                                  ↓    ↓
                           ┌────────────┐
                           │ 迭代优化   │ ← 最多 N 轮
                           └─────┬──────┘
                                 ↓
                           ┌────────────┐
                           │  输出结果  │
                           └────────────┘
```

**工程要点**：
1. **迭代上限**：防止死循环和成本失控
2. **失败兜底**：评估不稳定时的降级策略
3. **可观测性**：每步输出 trace，便于调试

---

### 在本项目中的使用

#### 1. 意图路由

**文件**：[orchestrator.py:182-187](../backend/task_decomposer/orchestrator.py)

```python
router_result = self._router_chain.run(
    user_input=f"{goal}\n{context}",
    on_event=on_event
)

# router_result.intent 可能是：
# - "clarify"：信息不足，需要问用户
# - "decompose"：信息充足，直接拆解
```

**分支逻辑**：[orchestrator.py:191-214](../backend/task_decomposer/orchestrator.py)

```python
if router_result.intent == RouterChain.INTENT_CLARIFY:
    # 澄清分支
    clarify_result = self._clarify_chain.run(goal=goal, context=context)
    return {"status": "need_clarification", "questions": clarify_result.questions}
else:
    # 拆解分支（继续往下走）
```

---

#### 2. 质量评估 + 迭代优化

**文件**：[orchestrator.py:237-254](../backend/task_decomposer/orchestrator.py)

```python
# 评估阶段
eval_result = self._evaluate_chain.run(plan=plan)

# 迭代条件：评分低 或 明确要求重写
if eval_result.rewrite_needed or eval_result.overall_score < 80:
    print("尝试改进计划...")
    plan, eval_result = self._evaluate_chain.evaluate_and_rewrite(
        plan=plan,
        decompose_chain=self._decompose_chain
    )
    session.save_plan_version(plan, version="v2")  # 保存新版本
```

---

#### 3. 可观测性（on_event 回调）

**文件**：[orchestrator.py:157-169](../backend/task_decomposer/orchestrator.py)

```python
def emit(event_type: str, data: Optional[Dict] = None):
    payload = {
        "type": event_type,          # "router_start", "decompose_result" 等
        "ts": datetime.utcnow().isoformat()
    }
    if data:
        payload["data"] = data
    on_event(payload)  # 传给前端展示进度

# 调用示例
emit("router_start", {})
emit("decompose_result", {"tasks": 25, "milestones": 4})
```

**教学点**：前端可以实时显示"正在路由 → 正在拆解 → 正在评估"。

---

## 模块12：记忆系统

### 知识点讲解

| 类型 | 作用范围 | 存储内容 | 更新策略 |
|-----|---------|---------|---------|
| **会话记忆** | 单次任务 | 对话上下文、临时约束、计划版本 | 每轮写入，任务结束清空 |
| **用户画像** | 跨会话 | 稳定偏好、领域背景、格式习惯 | 仅在高置信度时更新 |

**读/写时机**：
```
                ┌─────────────┐
                │  用户请求   │
                └──────┬──────┘
                       ↓
         ┌─────────────────────────┐
         │ 读：会话记忆 + 用户画像  │ ← 拼接到 prompt
         └─────────────────────────┘
                       ↓
                 ┌──────────┐
                 │ 执行链路  │
                 └─────┬────┘
                       ↓
         ┌─────────────────────────┐
         │ 写：更新会话 + 画像（可选）│
         └─────────────────────────┘
```

---

### 在本项目中的使用

#### 1. 会话记忆（短期）

**文件**：[memory/session_store.py:11-34](../backend/task_decomposer/memory/session_store.py)

```python
class SessionStore:
    def __init__(self):
        self._data = {
            "goal": "",
            "context": "",
            "constraints": [],      # 约束条件
            "answers": {},          # 用户回答
            "iterations": [],       # 历史计划版本
            "current_step": "start" # 当前在哪个阶段
        }
```

**使用位置**：[orchestrator.py:174-217](../backend/task_decomposer/orchestrator.py)

```python
# 初始化会话
session = SessionStore()
session.set_goal(goal)
session.set_context(context)

# 保存计划版本（迭代时）
session.save_plan_version(plan, version="v1")
session.save_plan_version(improved_plan, version="v2")
```

---

#### 2. 用户画像（长期）

**使用位置**：[orchestrator.py:257-264](../backend/task_decomposer/orchestrator.py)

```python
if user_id:  # 仅在明确有 user_id 时写入
    profile = ProfileStore(user_id)
    profile.add_history(
        goal=goal,
        plan=plan,
        tags=constraints or []
    )
```

**教学点**：长期记忆需要"高置信度"才写入，避免污染画像。

---

#### 3. 读/写时机总结

| 动作 | 时机 | 代码位置 |
|-----|------|---------|
| **读会话** | 任务开始时 | orchestrator.py:174 |
| **读画像** | 任务拆解前（隐含） | 暂未显式实现 |
| **写会话** | 每次迭代后 | orchestrator.py:234, 254 |
| **写画像** | 任务完成后 | orchestrator.py:257-264 |

---

## 附录：课堂产物清单

### 模块8 产物
- [ ] 一个最小链：`prompt | llm | parser`
- [ ] 并行调用：`RunnableParallel`
- [ ] 流式输出：`llm.stream()`

### 模块9 产物
- [ ] Ingest 流水线：加载 → 切分 → 嵌入 → 存储
- [ ] Query 流水线：检索 → 过滤 → 组装 → 生成
- [ ] 可解释检索：返回 metadata

### 模块10 产物
- [ ] 新增一个 prompt 并在链中替换生效
- [ ] Few-shot 示例覆盖边界条件

### 模块11 产物
- [ ] 完整 orchestrator：路由 → 拆解 → 评估 → 输出
- [ ] 迭代优化逻辑

### 模块12 产物
- [ ] 会话记忆读写
- [ ] 用户画像更新（高置信度）
