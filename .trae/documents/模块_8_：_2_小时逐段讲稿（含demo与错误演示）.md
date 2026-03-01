# 模块8：2小时逐段讲稿（每段含可运行 Demo + 讲解要点 + 常见错误演示）

> 总时长：120min。建议投屏 + 现场跑代码。默认用 **OpenAI 兼容接口**（如 SiliconFlow/OneAPI/自建网关）。

---

## 课前准备（开场前 5min，学员照抄即可）

### 1) 安装依赖

```bash
# Python 3.10+ 推荐
pip install -U langchain langchain-core langchain-openai langchain-community pydantic python-dotenv
```

### 2) 配置环境变量（以 SiliconFlow 为例）

```bash
export OPENAI_API_KEY="你的key"
export OPENAI_BASE_URL="https://api.siliconflow.cn/v1"
```

> 注意：不同版本的 `ChatOpenAI` 参数名略有差异，下面 Demo 都会给出「两种写法二选一」，保证能跑通。

---

## 0. 开场与目标（0:00 - 0:08 / 8min）

### 讲稿（你要说什么）
- 今天我们做一件工程化升级：把“写 prompt 直接请求”变成**可组合、可复用、可测试**的链路。
- 两小时结束你至少能做到：
  1) 用消息与模板构造对话
  2) 用 LCEL（`|`）把 Prompt/LLM/Parser 串起来
  3) 用 Pydantic Parser 拿到可用的结构化结果

### Demo（确认依赖能 import）

```python
# demo_00_env_check.py
from langchain_openai import ChatOpenAI
print("ChatOpenAI imported OK")
```

### 常见错误演示
- `ModuleNotFoundError: langchain_openai`：没装 `langchain-openai`
- `ImportError`：版本混装；建议 `pip install -U langchain-core langchain-openai`

---

## 1. Messages 心智模型（0:08 - 0:23 / 15min）

### 讲稿
- LangChain 的“对话”不是字符串拼接，而是**带角色的消息列表**。
- System：规则/身份/输出约束；Human：用户输入；AI：模型输出（也能当 few-shot 示例）。
- 核心：多轮对话 = 消息列表不断追加；System 必须放第一条。

### Demo（最小消息调用）

```python
# demo_01_messages.py
import os
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

MODEL = "deepseek-ai/DeepSeek-V3"

# 写法A（较新版本常见）
llm = ChatOpenAI(
    model=MODEL,
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
    temperature=0.2,
)

# 写法B（部分版本）
# llm = ChatOpenAI(
#     model=MODEL,
#     openai_api_key=os.getenv("OPENAI_API_KEY"),
#     openai_api_base=os.getenv("OPENAI_BASE_URL"),
#     temperature=0.2,
# )

messages = [
    SystemMessage(content="你是严谨的技术助教，只用3条要点回答。"),
    HumanMessage(content="解释一下 LangChain 的 message 列表是什么。"),
]

resp = llm.invoke(messages)
print(resp.content)
```

### 讲解要点（边跑边讲）
- 传入 `messages` 时，模型能明确区分“规则”和“问题”。
- System 放第一条，规则影响更稳。

### 常见错误演示
1) **System 放错位置**（规则变弱）
```python
messages = [HumanMessage(content="..."), SystemMessage(content="...规则...")]
```
修复：System 永远第一条。

2) **把所有内容塞进 human**（后期难维护）
- 修复：把“规则”搬到 system，把“数据/问题”放 human。

互动检查（30秒）：
- 让学员用一句话说出：System/Human/AI 的职责。

---

## 2. ChatPromptTemplate（0:23 - 0:43 / 20min）

### 讲稿
- Prompt 模板的意义：**复用、可读、可测试**。
- `from_messages` 最适合多角色；`invoke(vars)` 会返回**消息列表**。

### Demo（模板注入 + 打印生成的消息）

```python
# demo_02_prompt_template.py
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一位{role}，输出必须是3条要点。"),
    ("human", "请帮我完成：{task}")
])

msgs = prompt.invoke({"role": "项目经理", "task": "把学习 LangChain 拆成可执行步骤"})
print(type(msgs))
for m in msgs:
    print(m.type, ":", m.content)
```

### Demo（模板 + LLM 跑起来）

```python
# demo_02b_prompt_plus_llm.py
import os
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

llm = ChatOpenAI(
    model="deepseek-ai/DeepSeek-V3",
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
    temperature=0.3,
)

chain = prompt | llm | StrOutputParser()
print(chain.invoke({"role": "技术负责人", "task": "解释 LCEL 的好处"}))
```

### 常见错误演示
1) **漏传变量**（直接报错）
```python
prompt.invoke({"role": "项目经理"})
```
修复：模板里每个 `{变量}` 都要提供。

2) **大括号冲突**（你想让模型输出 JSON 示例，里面也有 `{}`）
- 修复：用 `{{` `}}` 转义，或把 JSON 示例放代码块。

---

## 3. LLM 初始化（含 OpenAI 兼容代理） （0:43 - 0:55 / 12min）

### 讲稿
- 国内很多服务兼容 OpenAI 协议：核心就是 **base_url**。
- 结构化输出要稳：`temperature` 调低。

### Demo（两种参数写法二选一）

```python
# demo_03_llm_init.py
import os
from langchain_openai import ChatOpenAI

MODEL = "deepseek-ai/DeepSeek-V3"

# 写法A
llm = ChatOpenAI(
    model=MODEL,
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
    temperature=0.2,
)

# 写法B
# llm = ChatOpenAI(
#     model=MODEL,
#     openai_api_key=os.getenv("OPENAI_API_KEY"),
#     openai_api_base=os.getenv("OPENAI_BASE_URL"),
#     temperature=0.2,
# )

print(llm.invoke("用一句话解释 temperature 的作用").content)
```

### 常见错误演示
- `401 Unauthorized`：Key 没配/不对。
- `404`：base_url 少了 `/v1` 或路径不对。
- 参数名不认：换 A/B 写法。

---

## 4. OutputParser + Pydantic：把文本变成对象（0:55 - 1:20 / 25min）

### 讲稿
- 工程要的是“可被程序消费”的输出，不是“看起来像”。
- 用 Schema + format instructions 强约束。

### Demo（严格结构化输出）

```python
# demo_04_pydantic_parser.py
import os
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

class TaskItem(BaseModel):
    title: str = Field(description="任务标题")
    hours: float = Field(description="预估工时")
    priority: str = Field(description="优先级：P0/P1/P2")

parser = PydanticOutputParser(pydantic_object=TaskItem)
fmt = parser.get_format_instructions()

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是项目拆解助手。只输出符合要求的JSON。{format_instructions}"),
    ("human", "将这个需求拆成一条任务：{req}")
])

llm = ChatOpenAI(
    model="deepseek-ai/DeepSeek-V3",
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
    temperature=0.1,
)

chain = prompt | llm | parser
result = chain.invoke({"req": "实现一个登录页（含表单校验）", "format_instructions": fmt})
print(result)
print(type(result))
```

### 常见错误演示（重点 5min）

1) **忘了把 format_instructions 喂进 prompt**
```python
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是项目拆解助手。"),
    ("human", "{req}")
])
```
修复：system 加 `{format_instructions}`，invoke 时传入变量。

2) **输出被包在 ```json 代码块** 导致解析失败
- 复现方法：把 system 改成“可以使用 Markdown”。
- 修复：system 写死“不要 Markdown、不解释、只输出 JSON”。

3) **字段类型不对**（hours 输出成“3小时”）
- 修复：system 强化 `hours 必须是 number`；必要时做二次纠正链。

### 兜底 Demo（去掉 code fence 的最简实现）

```python
# demo_04b_strip_code_fence.py
import json

def strip_code_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        # 去掉首行 ``` 或 ```json
        first_newline = text.find("\n")
        if first_newline != -1:
            text = text[first_newline+1:]
        if text.endswith("```"):
            text = text[:-3]
    return text.strip()

raw = """```json
{"title":"任务","hours":3,"priority":"P1"}
```"""
print(json.loads(strip_code_fence(raw)))
```

---

## 5. Runnable + LCEL：用 | 串联组件（1:20 - 1:40 / 20min）

### 讲稿
- LangChain 把 Prompt/LLM/Parser 都抽象成 Runnable。
- 所以能像管道一样：`prompt | llm | parser`。
- 统一接口：`invoke / batch / stream`。

### Demo（invoke + batch + stream）

```python
# demo_05_lcel_invoke_batch_stream.py
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

llm = ChatOpenAI(
    model="deepseek-ai/DeepSeek-V3",
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
    temperature=0.3,
)

prompt = ChatPromptTemplate.from_template("用一句话解释：{concept}")
chain = prompt | llm | StrOutputParser()

print("invoke:", chain.invoke({"concept": "Runnable"}))
print("batch:", chain.batch([
    {"concept": "LCEL"},
    {"concept": "OutputParser"},
]))

print("stream:")
for chunk in (prompt | llm).stream({"concept": "为什么要用消息列表"}):
    content = getattr(chunk, "content", str(chunk))
    print(content, end="")
print()
```

### 常见错误演示
- `chain.invoke("xxx")` 报错：模板需要 dict 输入。
- stream 打印“对象很怪”：取 `.content`，不同版本 chunk 类型略有差异。

---

## 6. RunnablePassthrough：输入透传 + 字段组装（1:40 - 1:55 / 15min）

### 讲稿
- 真实项目常见：
  - 原始 question 要保留
  - 同时生成 style/context/constraints 等字段
- 用 `RunnablePassthrough` 透传原始输入，再用映射组装。

### Demo（拆字段再进 prompt）

```python
# demo_06_passthrough_mapping.py
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

llm = ChatOpenAI(
    model="deepseek-ai/DeepSeek-V3",
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
    temperature=0.2,
)

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是技术助教，回答要简洁。"),
    ("human", "问题：{question}\n回答风格：{style}")
])

chain = {
    "question": RunnablePassthrough(),
    "style": RunnableLambda(lambda q: "用3条要点")
} | prompt | llm | StrOutputParser()

print(chain.invoke("LangChain 的 Runnable 是什么？"))
```

### 常见错误演示
- 字典里直接放普通函数而不是 Runnable：应包一层 `RunnableLambda`。
- prompt 字段名对不上：`{question}`/`{style}` 必须和 mapping key 一致。

---

## 7. RunnableParallel：并行生成多种结果（1:55 - 2:10 / 15min）

### 讲稿
- 一个输入同时要摘要、关键词、建议：用并行链更清晰。
- 输出是 dict：`{"summary":...,"keywords":...}`。

### Demo（并行跑两条链）

```python
# demo_07_parallel.py
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel

llm = ChatOpenAI(
    model="deepseek-ai/DeepSeek-V3",
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
    temperature=0.3,
)

summary_chain = ChatPromptTemplate.from_template("用一句话总结：{text}") | llm | StrOutputParser()
keyword_chain = ChatPromptTemplate.from_template("给出3个关键词（用逗号分隔）：{text}") | llm | StrOutputParser()

parallel = RunnableParallel(summary=summary_chain, keywords=keyword_chain)

out = parallel.invoke({"text": "LangChain 让大模型调用变成可组合的工程链路。"})
print(out)
```

### 常见错误演示
- 误以为返回 list：实际返回 dict。
- 并行太多触发限流：减少并行/改 batch/做重试退避。

---

## 8. 收尾小项目：Goal → Task Decomposer（2:10 - 2:18 / 8min）

### 讲稿
- 用今天学的东西做一个完整链：输入 goal，输出结构化任务列表。
- 这是“任务拆解器/编排器”的最小雏形。

### Demo（任务列表 Schema）

```python
# demo_08_mini_project.py
import os
from typing import List
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

class Task(BaseModel):
    title: str
    hours: float
    why: str = Field(description="为什么要做")

class Plan(BaseModel):
    tasks: List[Task]

parser = PydanticOutputParser(pydantic_object=Plan)
fmt = parser.get_format_instructions()

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是资深项目经理，只输出JSON。{format_instructions}"),
    ("human", "目标：{goal}\n约束：总工时不超过{max_hours}小时。")
])

llm = ChatOpenAI(
    model="deepseek-ai/DeepSeek-V3",
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
    temperature=0.1,
)

chain = prompt | llm | parser
plan = chain.invoke({
    "goal": "做一个可用的个人博客网站",
    "max_hours": 16,
    "format_instructions": fmt
})
print(plan)
```

### 常见错误演示
- 约束不生效（超时长）：
  - system 增强：“严格遵守 max_hours，总和必须 <= max_hours”
  - 或解析后做校验/二次修正

---

## 9. 总结与作业（2:18 - 2:20 / 2min）

### 课堂总结（你要说的 3 句）
1) 对话 = Messages 列表（System 规则第一）
2) Prompt 模板 + LCEL 管道让调用可组合
3) Parser/Schema 让输出可被程序可靠消费

### 作业（任选其一）
- A：把 demo_08 扩展成“任务 → 里程碑 → 风险”的并行输出（RunnableParallel）。
- B：做一个鲁棒解析器：去 code fence + 修复单引号 + 补全缺失括号（任选 2 个）。

---

## 讲师小抄：节奏控制
- 学员卡在 Key/base_url：先讲 `demo_02_prompt_template.py`（不调用模型也能讲清楚），再回头解决网络/Key。
- 结构化输出不稳：
  - `temperature` 降到 0~0.1
  - system 强化“只输出 JSON、不要 markdown、不要解释”
  - 用 `strip_code_fence` 做兜底

