# 前端使用说明

## 快速开始

### 1. 启动后端服务

在项目根目录运行：

```bash
cd "c:\Resume Projects\Multi-agent"
uvicorn app.main:app --reload
```

### 2. 打开前端页面

直接双击 `frontend/index.html` 文件即可在浏览器中打开。

或者使用 Python 内置服务器：

```bash
cd frontend
python -m http.server 8080
```

然后在浏览器访问：http://localhost:8080

## 功能特性

✅ **现代化 UI 设计**
- 渐变紫色主题
- 流畅的动画效果
- 响应式布局

✅ **实时聊天**
- 用户消息气泡（右侧，紫色）
- AI 回复气泡（左侧，白色）
- 输入中指示器（三个跳动的小球）

✅ **会话管理**
- 可自定义 Session ID
- 同一 Session ID 保持多轮对话上下文
- 默认使用 "default" 作为 Session ID

✅ **错误处理**
- 网络错误提示
- API 错误显示
- 5 秒后自动消失

## 使用示例

1. **咨询问题**
   - 输入："如何退货？"
   - AI 会从知识库中检索答案

2. **创建工单**
   - 输入："我要创建一个工单，标题是测试问题"
   - AI 会调用 MCP 工具创建工单

3. **转人工客服**
   - 输入："转人工"
   - AI 会将你转接到人工客服节点

## 技术栈

- **HTML5 + CSS3** - 现代网页标准
- **原生 JavaScript** - 无需框架依赖
- **Fetch API** - 异步 HTTP 请求
- **Flexbox 布局** - 响应式设计

## 注意事项

⚠️ 确保后端服务已启动且运行在 `http://localhost:8000`
⚠️ 如果遇到跨域问题，请在后端添加 CORS 支持
⚠️ 建议使用 Chrome、Firefox、Edge 等现代浏览器
