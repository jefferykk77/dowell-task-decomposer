   # 🎯 Dowell Task Decomposer

   基于 LangChain 架构的 AI 任务拆解器，智能规划你的项目从目标到每日执行。

   [![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
   [![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
   [![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://react.dev)
   [![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6.svg)](https://www.typescriptlang.org)

   ## ✨ 功能特性

   - 🤖 **AI 智能拆解** - 基于 LangChain + DeepSeek-V3，将大目标拆解为可执行的任务
   - 📅 **时间层级视图** - 年/月/周/日四级视图，清晰展示项目时间线
   - 📊 **甘特图展示** - 直观的进度管理，支持拖拽调整
   - 🔍 **RAG 知识增强** - 内置最佳实践知识库，提供智能建议
   - 🎯 **质量评估** - AI 自动评估计划质量并给出改进建议
   - 📱 **响应式设计** - 完美适配桌面和移动端

   ## 🚀 快速开始

   ### 1. 克隆项目

   ```bash
   git clone https://github.com/jefferykk77/dowell-task-decomposer.git
   cd dowell-task-decomposer
 ```

 ### 2. 配置 API Key ⚠️                                                                                                                                                                                           

 重要：你需要先配置自己的 API Key 才能使用 AI 功能

 编辑 backend/.env 文件：

 ```env
   # SiliconFlow API Key (必填)
   # 获取地址：https://cloud.siliconflow.cn/
   SILICONFLOW_API_KEY=your-api-key -here

   # 模型配置
   SILICONFLOW_MODEL=deepseek-ai/DeepSeek-V3

   # OpenAI 配置（可选）
   OPENAI_API_KEY=your-openai-key-h ere
   OPENAI_MODEL=gpt-3.5-turbo

   # RAG 配置
   ENABLE_RAG=true
   RAG_TOP_K=5
   RAG_SCORE_THRESHOLD=0.3

   # 其他配置
   DEBUG=true
   HOST=0.0.0.0
   PORT=8000
 ```

 ### 3. 启动后端

 ```bash
   cd backend

   # 安装依赖
   pip install -r requirements.txt

   # 启动服务
   python -m uvicorn app.main:app --reload
 ```

 后端服务将在 http://localhost:8000 运行

 ### 4. 启动前端

 ```bash
   cd frontend

   # 安装依赖
   npm install

   # 启动开发服务器
   npm run dev
 ```

 前端将在 http://localhost:5173 运行（或系统分配的其他端口）

 ### 5. 访问应用

 打开浏览器访问前端地址，输入你的目标，点击"开始 AI 解析"即可！

 🏗️ 技术栈                                                                                                                                                                                                        

 ### 后端

 - FastAPI - 高性能 Python Web 框架                                                                                                                                                                                 - LangChain - LLM 应用开发框架
 - DeepSeek-V3 - SiliconFlow 提供的大语言模型
 - RAG - 检索增强生成技术

 ### 前端

 - React 18 - 用户界面库
 - TypeScript - 类型安全
 - Vite - 构建工具
 - Tailwind CSS - 原子化 CSS 框架

 🐛 常见问题

 Q: 前端显示 "Failed to fetch"
 A: 检查后端是否已启动，以及 CORS 配置是否正确

 Q: AI 解析无响应
 A: 检查 .env 中的 SILICONFLOW_API_KEY 是否正确                                                                                                                                                                    
 📄 许可证

 MIT License

 ─────────────────────────────────────────────────────────────────────────

 Made with ❤️ by Jeffery                                               
