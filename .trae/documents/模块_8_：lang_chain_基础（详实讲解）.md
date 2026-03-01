# 模块8：LangChain 基础（详实完整讲解）

> 目标：把「调用大模型」这件事，从“手写 prompt + 直接请求”升级为**可组合、可复用、可测试**的工程化链路。

---

## 0. 你要掌握的全局图

LangChain 的核心不是“某个 API”，而是一套**把输入 → 组织成消息 → 调用模型 → 解析输出 → 组装成链**的工程范式。

最小闭环长这样：

```
（结构化需求）→ Prompt(模板) → LLM(模型) → Parser(解析) → 结构化结果
```

用 LCEL 管道表达就是：

```python
chain = prompt | llm | parser
result = chain.invoke(input_dict)
```

后面所有内容，其实都是在解释：
- prompt 是怎么构造“消息”的
- llm 是怎么配置“模型”的
- parser 是怎么保证“结果可用”的
- runnable 是怎么让“组件统一调用”的

---

## 1. Messages 心智模型：对话 = 消息列表

### 1.1 三种消息类型的角色分工

- **SystemMessage**：
  - 定义“规则/身份/输出要求”
  - 类似“项目的技术规范 + 代码风格指南”
- **HumanMessage**：
  - 用户真实输入：问题、指令、任务描述
- **AIMessage**：
  - 模型输出
  - 也可以拿来当 few-shot 示例（把示例对话当成历史消息塞进去）

### 1.2 为什么要用消息列表，而不是拼字符串？

因为多轮对话不是一段文本，而是一个**有角色、有顺序、有上下文堆叠**的结构：

```
[system] → [human, ai] → [human, ai] → [human, ai]
```

#### 常见坑
- System 放错位置：系统消息必须在最前，否则“规则”影响会变弱
- 把所有内容都塞到 human：会导致“规则”和“数据”混在一起，难维护

---

## 2. ChatPromptTemplate：变量注入 = Prompt 工程化

Prompt 模板的意义：
- **可复用**：模板定义一次，多个输入复用
- **可测试**：同一模板喂不同变量做回归
- **可读性**：把“固定规则”和“可变数据”分离

### 2.1 from_messages：最常用（推荐）

```python
from langchain.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一位{role}，擅长{skill}"),
    ("human", "请帮我完成：{task}")
])

messages = prompt.invoke({
    "role": "项目经理",
    "skill": "任务拆解",
    "task": "学习 Python"
})
```

#### 关键理解
- `from_messages([...])` 做了两件事：
  1) 规定消息顺序与角色
  2) 定义变量占位符 `{role}`、`{skill}`、`{task}`
- `prompt.invoke(vars)` 的结果不是字符串，而是**消息列表（List[Message]）**，可以直接喂给 Chat 模型。

### 2.2 from_template：单段模板也能用

```python
template = ChatPromptTemplate.from_template(
    "将以下目标拆解为任务：{goal}"
)
```

适合简单场景，但一旦涉及多轮/多角色，一般还是 `from_messages` 更清晰。

#### 常见坑
- 变量漏传：模板里用了 `{goal}`，invoke 时却没给，会直接报错
- 变量命名混乱：建议统一命名，例如 `goal/context/constraints/style` 等

---

## 3. ChatOpenAI：模型配置（兼容 OpenAI 的服务都能接）

### 3.1 标准 OpenAI

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="gpt-4",
    api_key="sk-xxx",
    temperature=0.7
)
```

### 3.2 第三方兼容 OpenAI 接口（例如 SiliconFlow）

```python
llm = ChatOpenAI(
    model="deepseek-ai/DeepSeek-V3",
    openai_api_key="your-api-key",
    openai_api_base="https://api.siliconflow.cn/v1",
    temperature=0.3
)
```

#### 参数怎么选？
- **model**：决定能力与价格
- **temperature**：决定稳定性（结构化输出建议低一些，如 0.0~0.3）
- **openai_api_base**：把请求“路由”到兼容服务

### 3.3 三种调用方式（工程上很常用）

```python
response = llm.invoke("你好")
responses = llm.batch(["你好", "再见"])
for chunk in llm.stream("讲个故事"):
    print(chunk.content, end="")
```

#### 什么时候用哪个？
- `invoke`：默认、易调试
- `batch`：吞吐高（批处理任务，比如批量摘要、批量评估）
- `stream`：前端需要“打字机效果”或长输出想边生成边展示

---

## 4. OutputParser：把“文本”变成“结构化数据”

LLM 输出默认是字符串，但工程上我们更想要：
- JSON
- 类/对象
- 可校验的字段

### 4.1 用 PydanticOutputParser 强约束输出

```python
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

class TaskSchema(BaseModel):
    title: str = Field(description="任务标题")
    hours: float = Field(description="预估工时")
    priority: str = Field(description="优先级：P0/P1/P2")

parser = PydanticOutputParser(pydantic_object=TaskSchema)
format_instructions = parser.get_format_instructions()

prompt = ChatPromptTemplate.from_messages([
    ("system", "输出 JSON 格式任务\n{format_instructions}"),
    ("human", "{task}")
])

chain = prompt | llm | parser
result = chain.invoke({
    "task": "写一个登录页面",
    "format_instructions": format_instructions
})
```

#### 这里最关键的 2 句话
1) **Schema 定义**决定你最终拿到的数据形状
2) **format_instructions 必须喂进 prompt**，否则模型不知道你要什么格式

### 4.2 结构化输出为何仍然会失败？

现实里常见情况：
- 模型输出包了 ```json 代码块
- 用了中文引号、单引号
- 末尾多了逗号
- 输出被截断（没闭合括号）

因此很多项目会做“鲁棒解析”：
- 清理 markdown
- 修复常见 JSON 错误
- 截断补全
- 再 `json.loads`

（这也是你在真实项目里经常要补的工程化能力点。）

---

## 5. Runnable：统一接口（invoke / batch / stream）

LangChain 的所有组件（Prompt、LLM、Parser、Retriever…）都尽量统一成 `Runnable`，好处是：
- 任何组件都能：单次调用、批量调用、流式调用
- 任何组件都能组合进链路

统一调用协议：

```python
component.invoke(input_data)
component.batch([input1, input2])
component.stream(input_data)
```

---

## 6. LCEL：LangChain Expression Language（用 | 串联组件）

### 6.1 为什么 LCEL 比“手写流程”更好？

手写流程（伪代码）：
1) prompt 生成消息
2) llm 调用
3) parser 解析

LCEL 用一行表达：

```python
chain = prompt | llm | parser
```

#### 背后的工程收益
- 链路变得“可读”和“可组合”（像 Unix pipeline）
- 更容易插入日志/评估/重试
- 更容易做并行分支和路由

---

## 7. 并行与透传：让链路像“数据流图”一样组织

### 7.1 RunnablePassthrough：把原始输入原样传下去

典型场景：你要同时构造多个字段：
- context：从检索器拿到
- question：原样透传

```python
from langchain.runnables import RunnablePassthrough

chain = {
    "context": retriever | (lambda docs: "\n".join(d.page_content for d in docs)),
    "question": RunnablePassthrough(),
} | prompt | llm | parser
```

### 7.2 RunnableParallel：并行跑多个子链

```python
from langchain.runnables import RunnableParallel

chain = RunnableParallel(
    summary=summary_chain,
    keywords=keyword_chain,
)
```

#### 什么时候需要并行？
- 你要同时产出“摘要 + 关键词 + 评分 + 建议”
- 你要做多路召回（多检索器）再融合

---

## 8. 在项目里的落地方式（把概念对上真实代码）

> 这一节的目标：让你能把“课堂概念”映射到“工程实现”。

### 8.1 Prompt 组装位置：system + human
- system：放规则
- human：放变量模板

数据流可理解为：

```
system_prompt
  ↓
user_prompt_template (含 {goal} 等变量)
  ↓
ChatPromptTemplate.from_messages → List[Message]
  ↓
模型调用 → 字符串
```

### 8.2 模型初始化：通过 base_url 接入兼容服务
- 国内很多服务兼容 OpenAI 协议：只要换 `openai_api_base` 即可
- 结构化输出建议低温度（更稳定）

### 8.3 输出解析：不要迷信“模型一定输出合法 JSON”
- 真实项目常做“修复 + 解析”
- 这是让 AI 系统**稳定可用**的关键工程点之一

---

## 9. 课堂练习（建议按这个顺序做）

### 练习 A：最小链（必做）
- 目标：跑通 `prompt | llm | parser`
- 输出：一个符合 schema 的对象

### 练习 B：流式输出（必做）
- 目标：用 `llm.stream()` 做打字机输出

### 练习 C：并行链（加分）
- 目标：`RunnableParallel` 同时输出 summary 和 keywords

### 练习 D：鲁棒解析（加分）
- 目标：故意让模型输出带 ```json 或单引号，然后写修复逻辑解析成功

---

## 10. 常见排错清单（非常实用）

1) **变量没注入**：模板里 `{goal}`，invoke 没传 `goal`
2) **system 放错**：system 不在第一条消息，规则不稳
3) **parser 失败**：先打印原始输出，再决定是“提示词约束”还是“修复逻辑”
4) **stream 输出为空**：注意 chunk 是对象，要取 `chunk.content`
5) **结构化不稳**：
   - 降温度
   - system 明确写“只输出 JSON，不要 Markdown”
   - 加 schema / format_instructions

---

如果你愿意，我也可以按你的课时安排，把以上内容进一步拆成：
- 课堂讲解稿（逐页讲）
- 板书/口播要点
- 练习题 + 标准答案
- 常见错题与调试演示脚本

