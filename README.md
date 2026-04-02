# Multi-agent 客服

基于 **LangGraph** 的多智能体客服系统：意图路由、千问（阿里云）+ 自建 MCP（知识库 + 工单），适合作为简历项目或二次扩展。

## 功能概览

- **编排**：单图内 router → 问答 / 工单 / 转人工，条件边与状态持久化（MemorySaver）
- **模型**：阿里云千问（qwen-plus），词向量可后续接 DashScope embedding 做 RAG
- **MCP**：自建知识库 FAQ、工单（查/建/改），国内直连、无需翻墙
- **API**：FastAPI，`POST /api/chat` 多轮对话

## 本地运行

### 1. 依赖

```bash
cd "c:\Resume Projects\Multi-agent"
pip install -r requirements.txt
```

### 2. 环境变量

复制 `.env.example` 为 `.env`，填写阿里云灵积 API Key：

```
DASHSCOPE_API_KEY=你的API_Key
```

获取地址：<https://dashscope.console.aliyun.com/>

### 3. 启动后端服务

**必须从项目根目录启动**（以便 `python -m mcp_servers.*` 能正确加载）：

```bash
cd "c:\Resume Projects\Multi-agent"
uvicorn app.main:app --reload
```

MCP 会由应用在启动时以 stdio 子进程方式自动拉起，无需单独启动。

后端服务运行在：http://localhost:8000

- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000

### 4. 打开前端页面（可选）

**方式一：直接打开**

双击 `frontend/index.html` 文件即可在浏览器中打开。

**方式二：使用 HTTP 服务器**

```bash
cd frontend
python -m http.server 8080
```

然后访问：http://localhost:8080

### 5. 测试 API

**使用 curl：**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d "{\"session_id\":\"s1\",\"message\":\"如何退货？\"}"
```

**使用 PowerShell：**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/chat" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"session_id":"s1","message":"如何退货？"}'
```

同一 `session_id` 下可连续发送多条消息，保持多轮对话上下文。

## 项目结构

```
Multi-agent/
├── app/
│   ├── main.py       # FastAPI 入口与 lifespan（MCP + 图初始化）
│   ├── chat.py       # POST /api/chat
│   ├── graph.py      # 状态、节点、边、get_graph(tools)
│   └── mcp_client.py # MCP 配置与 mcp_tools_context()
├── mcp_servers/
│   ├── knowledge_server.py  # search_faq
│   └── ticket_server.py    # get_ticket, create_ticket, update_ticket
├── scripts/
│   └── run_servers.py      # 可选：单独起两个 MCP 进程
├── requirements.txt
├── .env.example
├── frontend/
│   ├── index.html          # 前端聊天页面
│   └── README.md           # 前端使用说明
└── README.md
```

## 扩展说明

- **词向量与 RAG**：可在 `mcp_servers/knowledge_server.py` 中接入 DashScope `text-embedding-v1` + 向量库，将 FAQ 改为语义检索。
- **多轮后继续路由**：当前 qa_agent/ticket_agent 结束后直接 `__end__`；若希望多轮后再走 router，可将这两个节点的出口改为指向 `router`。

## 技术栈

- **编排框架**：LangGraph + LangChain
- **大模型**：阿里云 DashScope（qwen-max）
- **MCP 协议**：FastMCP + langchain-mcp-adapters
- **后端框架**：FastAPI + uvicorn
- **前端**：HTML5 + CSS3 + 原生 JavaScript（零依赖）
