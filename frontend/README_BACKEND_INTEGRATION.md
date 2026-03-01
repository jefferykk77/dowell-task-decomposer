# 前端与后端 task_decomposer 对齐文档

## 📋 概述

前端已完成与后端 `task_decomposer` V2.0 模块的对齐工作，实现了基于 LangChain 架构的智能任务拆解功能。

## ✅ 已完成的工作

### 1. 类型定义对齐 ([`src/types/task.ts`](src/types/task.ts))

#### 新增类型（与后端完全对齐）
- `PriorityLevel` - 任务优先级枚举 (P0-P3)
- `RiskLevel` - 风险等级枚举 (低/中/高)
- `ConstraintSchema` - 约束条件结构
- `OpenQuestionSchema` - 澄清问题结构
- `MilestoneSchema` - 里程碑结构
- `TaskSchema` - 任务节点结构
- `PlanSchema` - 完整计划结构
- `PlanMetadata` - 计划元数据
- `EvaluateOutput` - 评估输出结构
- `RouterOutput` - 路由输出结构

#### API 接口类型
- `DecomposeRequest` - 任务拆解请求
- `DecomposeResponse` - 任务拆解响应
- `ClarifyRequest` - 澄清问题请求
- `ClarifyResponse` - 澄清问题响应

### 2. API 客户端更新 ([`src/api/task.ts`](src/api/task.ts))

#### 核心功能
```typescript
// 主拆解接口
taskApi.decompose(data: DecomposeRequest)

// 澄清问题接口
taskApi.clarify(data: ClarifyRequest)

// 用户画像接口
taskApi.getUserProfile(userId: string)
taskApi.updatePreferences(userId, preferences)

// 工具列表
taskApi.listTools()

// 健康检查
taskApi.healthCheck()
```

#### 配置
- **Base URL**: `http://localhost:8000`
- **Timeout**: 120秒（AI处理需要更长时间）
- **拦截器**: 请求/响应日志记录

### 3. 数据转换器 ([`src/utils/transformer.ts`](src/utils/transformer.ts))

#### 核心转换函数
```typescript
// 统一转换函数（自动识别 V1/V2 格式）
transformToTree(data: any): YearNode

// V2 后端响应转换
transformPlanSchemaToYearNode(plan: PlanSchema): YearNode
transformPlanToTree(plan: PlanSchema): PlanNode

// 类型守卫
isV2Response(response: any): boolean
isLegacyResponse(response: any): boolean
```

#### 兼容性
- ✅ 支持 V2 后端（`PlanSchema` 格式）
- ✅ 兼容 V1 后端（旧格式）
- ✅ 自动格式检测与转换

### 4. 表单组件更新 ([`src/components/TaskForm.tsx`](src/components/TaskForm.tsx))

#### 对齐后端的字段
- **核心目标** (`goal`) - 必填
- **背景信息** (`context`) - 可选
- **约束条件** (`constraints`) - 数组格式
  - 时间约束（截止日期）
  - 预算约束
  - 技术栈约束
  - 时间投入约束
  - 优先级偏好
  - 风险容忍度

#### 高级选项
- 优先级选择（速度/平衡/质量）
- 风险容忍度（低/中/高）
- 每周投入时间

### 5. 应用主逻辑更新 ([`src/App.tsx`](src/App.tsx))

#### 新增功能
1. **多状态处理**
   - `need_clarification` - 需要澄清时显示问题
   - `completed` - 正常完成并显示结果
   - `error` - 错误处理

2. **质量评估展示**
   - 总体评分显示
   - 问题列表展示
   - 改进建议展示
   - AI 智能提示

3. **版本标识**
   - 标题显示 "V2.0 - LangChain 架构"
   - 路由信息日志输出

## 🔌 后端 API 端点

### 基础 URL
```
http://localhost:8000
```

### 可用端点

#### 1. 任务拆解
```http
POST /api/v2/decompose
Content-Type: application/json

{
  "goal": "开发一个待办事项小程序",
  "context": "用于个人任务管理",
  "constraints": ["预算有限", "一周内上线"],
  "enable_evaluation": true
}
```

#### 2. 澄清问题
```http
POST /api/v2/clarify
Content-Type: application/json

{
  "goal": "开发小程序",
  "context": "用于任务管理"
}
```

#### 3. 用户画像
```http
GET /api/v2/profile/{user_id}
```

#### 4. 更新偏好
```http
POST /api/v2/preferences
Content-Type: application/json

{
  "user_id": "user123",
  "preferences": {
    "output_format": "detailed"
  }
}
```

#### 5. 工具列表
```http
GET /api/v2/tools
```

#### 6. 健康检查
```http
GET /health
```

## 📊 数据流

```
用户输入 (TaskForm)
    ↓
DecomposeRequest
    ↓
API Client (taskApi.decompose)
    ↓
Backend: /api/v2/decompose
    ↓
DecomposeResponse
    ├─ need_clarification → 显示澄清问题
    ├─ error → 显示错误信息
    └─ completed → 转换数据
        ↓
    Transformer (transformToTree)
        ↓
    YearNode
        ↓
    视图展示 (YearView / GanttView)
```

## 🎨 UI 功能

### 质量评估展示
当后端返回评估数据时，前端会显示：
- 总体评分（0-100）
- 问题数量
- 通过/未通过状态
- 改进建议列表

### AI 智能提示
根据评估结果自动显示提示：
- 评分 < 60: 红色提示（关键问题）
- 评分 60-80: 黄色提示（需要改进）
- 评分 >= 90: 蓝色提示（优秀）

## 🚀 启动说明

### 1. 启动后端
```bash
cd backend
python task_decomposer/app.py
```

服务将在 `http://localhost:8000` 启动

### 2. 启动前端
```bash
cd frontend
npm install
npm run dev
```

前端将在 `http://localhost:5173` 启动

### 3. 访问应用
打开浏览器访问 `http://localhost:5173`

## 🔧 配置说明

### 环境变量（后端）
创建 `backend/.env` 文件：
```env
SILICONFLOW_API_KEY=your_api_key_here
SILICONFLOW_API_BASE=https://api.siliconflow.cn/v1
SILICONFLOW_MODEL=deepseek-ai/DeepSeek-V3
ENABLE_RAG=true
VECTOR_STORE_PATH=./data/vector_store
KNOWLEDGE_BASE_PATH=./data/knowledge_base
```

### 前端配置
API 基础 URL 在 `src/api/task.ts` 中配置：
```typescript
const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 120000,
});
```

## 📝 待实现功能

以下功能前端已预留接口，待后端实现：

1. **任务变更影响评估**
   - 前端: `assessImpact()` 函数已定义
   - 后端: 需要实现 `/api/v2/assess-impact` 端点

2. **用户画像完整功能**
   - 前端: 接口已调用
   - 后端: 需要完善记忆存储实现

3. **澄清问题多轮交互**
   - 前端: 基础支持已实现
   - 后端: 需要实现会话管理

## 🐛 故障排查

### 问题 1: CORS 错误
**解决方案**: 后端已配置 CORS 允许所有来源

### 问题 2: 连接超时
**原因**: AI 处理时间较长
**解决**: 前端已设置 120 秒超时

### 问题 3: 响应格式不匹配
**原因**: 后端返回格式与预期不符
**解决**: 检查后端日志，确认返回的是 `PlanSchema` 格式

## 📚 相关文档

- [后端 README](../backend/task_decomposer/README.md)
- [Plan Schema 定义](../backend/task_decomposer/schemas/plan.py)
- [API 文档](http://localhost:8000/docs) (FastAPI Swagger UI)

## 🎯 总结

前端已成功与后端 `task_decomposer` V2.0 对齐，主要成果：

✅ 类型定义完全对齐
✅ API 接口完整对接
✅ 数据转换智能兼容
✅ UI 组件适配新格式
✅ 质量评估功能展示
✅ 错误处理机制完善

系统现在支持完整的 LangChain 工作流，从路由到澄清到拆解到评估，全链路打通。
