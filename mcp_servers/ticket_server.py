from fastmcp import FastMCP

mcp = FastMCP("Ticket Server")

_tickets: dict[str, dict] = {}
_ticket_counter = 0


@mcp.tool
def get_ticket(ticket_id: str) -> str:
    t = _tickets.get(ticket_id.strip().upper())
    if not t:
        return f"未找到工单 {ticket_id}，请核对后重试。"
    return f"工单 {ticket_id}：标题「{t['title']}」，状态：{t['status']}，描述：{t['description']}"


@mcp.tool
def create_ticket(title: str, description: str) -> str:
    global _ticket_counter
    _ticket_counter += 1
    tid = f"T{_ticket_counter:06d}"
    _tickets[tid] = {
        "title": title.strip(),
        "description": description.strip(),
        "status": "待处理",
    }
    return f"工单已创建，编号：{tid}。请告知用户稍后可通过「查询工单 {tid}」查看进度。"


@mcp.tool
def update_ticket(ticket_id: str, status: str) -> str:
    tid = ticket_id.strip().upper()
    t = _tickets.get(tid)
    if not t:
        return f"未找到工单 {tid}。"
    t["status"] = status.strip()
    return f"工单 {tid} 状态已更新为：{t['status']}。"


if __name__ == "__main__":
    mcp.run()
