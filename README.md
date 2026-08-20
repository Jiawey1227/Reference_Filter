# AI 文献评分工具

本项目是一个本地运行的 AI 学术文献相关性评分工具。应用通过 Web 界面上传 Excel 文件，后端计算文献与研究主题的 embedding 相似度，并对边界低分文献进行 LLM scope 筛选，最后输出带评分、筛选结果和国家/邮箱高亮标记的 Excel 文件。

## 固定 AI 配置

Web 工作流固定使用 Qwen / DashScope，不在界面中提供模型修改入口。

```text
Base URL: https://dashscope-intl.aliyuncs.com/compatible-mode/v1
Embedding Model: text-embedding-v4
LLM Model: qwen3.6-flash
Embedding request limit: 10 texts/request
```

用户只需要提供一个 DashScope-compatible API Key。这个 Key 同时用于 embedding 和 LLM 请求。

## 项目结构

```text
backend/
  app.py          # FastAPI routes
  jobs.py         # background job state and execution
  config.py       # fixed provider info
frontend/
  src/            # React + Vite + TypeScript UI
main.py           # scoring, LLM screening, Excel highlighting
requirements.txt  # Python dependencies
```

## 安装依赖

Python 后端：

```bat
.\.venv\Scripts\activate
pip install -r requirements.txt
```

前端：

```bat
cd frontend
npm install
```

## 启动

后端：

```bat
.\.venv\Scripts\activate
uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
```

前端：

```bat
cd frontend
npm run dev
```

然后打开：

```text
http://localhost:5173
```

## 使用流程

1. 在 Web 界面填写 DashScope API Key。
2. 点击“测试连接”，确认固定 Qwen embedding 接口可用。
3. 上传包含 `ref`、`refs` 或 `Reference` 列的 Excel 文件。
4. 选择运行模式：
   - 完整运行：生成 embedding 分数并执行 LLM scope 筛选
   - 仅 embedding：只生成 `score`
   - 仅 LLM：使用输入文件已有 `score` 列执行 LLM scope 筛选
5. 设置 LLM 分数区间，例如 `0.25 < score < 0.35`。
6. 输入研究主题。
7. 点击“开始处理”，等待进度完成。
8. 完成后点击“下载结果”。

## 输出列

常见输出列包括：

```text
score
scope_decision
scope_confidence
exclude
screening_reason
```

完整运行和仅 LLM 模式完成后，后端会继续执行国家/邮箱高亮逻辑。

## 缓存说明

Embedding 缓存会按 provider/model/text 隔离。换成 Qwen `text-embedding-v4` 后，旧模型生成的缓存不会被复用，避免相似度分数污染。

默认 Qwen 缓存文件：

```text
cache/embedding_cache_qwen_text-embedding-v4.pkl
```

## 运行时文件

以下为本地运行产物，不应提交到 Git：

```text
cache/
runtime/
app_config.json
*.xlsx
*_result.xlsx
```
