from contextlib import asynccontextmanager
from pathlib import Path
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.chat import router as chat_router
from app.graph import get_graph
from app.mcp_client import get_mcp_tools

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")


@asynccontextmanager
async def lifespan(app: FastAPI):
    tools = await get_mcp_tools()
    app.state.graph = get_graph(tools)
    yield


app = FastAPI(title="Multi-agent 客服", description="LangGraph + 千问 + 自建 MCP", lifespan=lifespan)

# 添加 CORS 中间件，允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)


@app.get("/")
def root():
    return {
        "project": "Multi-agent 客服",
        "docs": "/docs",
        "chat": "POST /api/chat",
        "body": {"session_id": "string", "message": "string"},
    }
