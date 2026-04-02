import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    knowledge_proc = subprocess.Popen(
        [sys.executable, "-m", "mcp_servers.knowledge_server"],
        cwd=str(ROOT),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    ticket_proc = subprocess.Popen(
        [sys.executable, "-m", "mcp_servers.ticket_server"],
        cwd=str(ROOT),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    print("MCP 服务已启动（knowledge + ticket）。关闭本窗口或 Ctrl+C 将结束两个进程。")
    try:
        knowledge_proc.wait()
        ticket_proc.wait()
    except KeyboardInterrupt:
        knowledge_proc.terminate()
        ticket_proc.terminate()
        knowledge_proc.wait()
        ticket_proc.wait()


if __name__ == "__main__":
    main()
