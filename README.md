# AI 文献相关性评分工具

一个基于 OpenAI 兼容接口的学术文献相关性评分工具。程序读取用户在 GUI 中选择的 Excel 文件，计算参考文献与研究主题的语义相似度，并输出带 `score`、scope 筛选结果和高亮标记的 Excel 文件。

## 功能

- 通过 Tkinter GUI 手动选择输入和输出 Excel 文件
- 支持 `ref`、`refs`、`Reference` 列名，不区分大小写
- 使用 embedding 缓存减少重复请求
- 支持仅生成 embedding 分数，便于先观察分数分布
- 支持对低分文献进行 LLM scope 筛选
- 可对 `Country/Region` 和 `Email` 信息进行颜色高亮标记
- 默认 API 地址为 `https://aihubmix.com/v1`
- 默认 embedding 模型为 `text-embedding-3-small`

## 项目结构

```text
.
├── main.py                  # 核心评分、LLM 筛选、Excel 高亮逻辑
├── gui.py                   # Tkinter 图形界面
├── requirements.txt         # Python 依赖
├── key.example.txt          # API Key 示例文件
├── AI 文献评分工具.spec      # PyInstaller 打包配置
├── cache/                   # 运行时缓存，默认不提交
├── .venv/                   # 本地虚拟环境，默认不提交
└── README.md
```

用户输入文件和输出文件不固定放在项目目录中，请在 GUI 中手动选择。

## 运行方式

创建并激活虚拟环境：

```bat
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

启动图形界面：

```bat
python gui.py
```

命令行模式也可用，但必须显式传入输入、输出和主题：

```bat
python main.py --input "path\to\input.xlsx" --output "path\to\output.xlsx" --topic "research topic"
```

常用两阶段流程：

```bat
python main.py --input "path\to\input.xlsx" --output "path\to\embedding_result.xlsx" --topic "research topic" --embedding-only
python main.py --input "path\to\embedding_result.xlsx" --output "path\to\llm_result.xlsx" --topic "research topic" --llm-only
```

GUI 中也可以选择对应模式：

- `仅生成 embedding 分数`：只生成 `score` 列，不运行 LLM
- `仅运行 LLM（使用已有 score）`：输入文件必须已有 `score` 列，不重新运行 embedding
- `完整运行`：一次性运行 embedding 和 LLM

## 输入文件要求

输入文件必须是 Excel 文件，并至少包含以下列名之一：

- `ref`
- `refs`
- `Reference`

可选列：

- `Country/Region`、`Country` 或 `Country Region`：用于区域高亮
- `Email`、`E-mail` 或 `Mail`：用于检查国家与邮箱域名是否匹配

## 输出说明

程序会生成一个新的 Excel 文件，并添加：

- `score`：0 到 1 之间的相似度分数
- `scope_decision`：scope 筛选结论
- `scope_confidence`：筛选置信度
- `exclude`：是否建议排除
- `screening_reason`：筛选原因

运行中可能生成：

- `cache/embedding_cache.pkl`：embedding 缓存，默认最多保留最近使用的 50000 条
- `progress.xlsx`：进度备份，写入输出文件所在目录

这些运行时文件不建议提交到 Git。

## API Key

GUI 会把 API Key、Base URL 和模型配置保存到本地 `app_config.json`，下次打开时会自动加载，避免每次重复输入。

命令行模式会优先使用 `--api-key`，如果未提供，则读取项目根目录的 `key.txt`。

`key.txt`、`app_config.json`、`.env` 等本地配置文件已加入 `.gitignore`。这些文件可以留在本机使用，但不要提交真实密钥。

## 打包

项目保留 `AI 文献评分工具.spec` 作为 PyInstaller 配置。如果需要打包为 exe，可在激活 `.venv` 后手动运行：

```bat
pip install pyinstaller
pyinstaller "AI 文献评分工具.spec" --clean --noconfirm
```

打包产物会生成在 `build/` 和 `dist/` 中，这两个目录默认不提交。
