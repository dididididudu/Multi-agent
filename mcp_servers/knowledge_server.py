from fastmcp import FastMCP

mcp = FastMCP("Knowledge FAQ Server")

FAQ_LIST = [
    {"q": "如何退货", "a": "请在订单页面点击「申请退货」，选择原因并提交。我们会在 1-3 个工作日内审核。"},
    {"q": "退款多久到账", "a": "退款审核通过后，一般 3-7 个工作日原路返回至您的支付账户。"},
    {"q": "如何联系客服", "a": "您可以在本对话中直接输入问题，或输入「转人工」接入人工客服。"},
    {"q": "配送时间", "a": "一般情况下下单后 24 小时内发货，国内 3-5 个工作日送达。"},
    {"q": "修改收货地址", "a": "未发货前可在「我的订单」中点击订单修改收货地址；已发货需联系客服处理。"},
]


@mcp.tool
def search_faq(query: str) -> str:
    query_lower = query.strip().lower()
    if not query_lower:
        return "未找到相关解答，建议转人工客服。"
    best = None
    best_score = 0
    for item in FAQ_LIST:
        q = item["q"].lower()
        score = sum(1 for c in query_lower if c in q) + (1 if any(w in q for w in query_lower.split()) else 0)
        if q in query_lower or query_lower in q:
            score += 10
        if score > best_score:
            best_score = score
            best = item
    if best and best_score > 0:
        return best["a"]
    return "未找到相关解答，建议转人工客服或输入「转人工」。"


if __name__ == "__main__":
    mcp.run()
