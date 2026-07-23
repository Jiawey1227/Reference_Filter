# AI 文献相关性评分工具

这是一个基于 OpenAI 兼容接口的学术文献相关性评分工具。软件通过图形界面读取用户选择的 Excel 文件，计算文献与研究主题的语义相似度，并输出带 `score`、LLM scope 筛选结果和国家/邮箱高亮标记的 Excel 文件。

## 功能

- 通过 GUI 手动选择输入和输出 Excel 文件
- 支持 `ref`、`refs`、`Reference` 列名，不区分大小写
- 支持仅生成 embedding 分数，便于先观察分数分布
- 支持基于已有 `score` 列单独运行 LLM 筛选
- 支持完整运行 embedding + LLM
- 使用本地 embedding 缓存减少重复请求，默认最多保留最近使用的 50000 条
- 可对 `Country/Region` 和 `Email` 信息进行颜色高亮标记
- 支持切换不同 OpenAI 兼容 API 服务商

## 项目结构

```text
.
├── main.py          # 核心评分、LLM 筛选、Excel 高亮逻辑
├── gui.py           # 图形界面入口
├── requirements.txt # Python 依赖
├── cache/           # 运行时缓存
├── .venv/           # 本地虚拟环境
└── README.md
```

用户输入文件和输出文件不固定放在项目目录中，请在 GUI 中手动选择。

## 使用说明

### 1. 启动软件

如果使用已经打包好的版本，双击：

```text
AI文献评分工具.exe
```

如果从源码运行：

```bat
.\.venv\Scripts\activate
python gui.py
```

### 2. 选择输入和输出文件

- 输入文件：选择需要评分的 Excel 文件
- 输出文件：选择结果保存位置
- 输入 Excel 必须包含 `ref`、`refs` 或 `Reference` 列

可选列：

- `Country/Region`、`Country` 或 `Country Region`：用于国家/区域高亮
- `Email`、`E-mail` 或 `Mail`：用于检查国家与邮箱域名是否匹配

### 3. 填写 API 配置

- `API Key`：填写你的 API 密钥
- `Base URL`：填写 API 服务商提供的接口地址
- `Embedding模型`：用于计算语义相似度
- `LLM筛选模型`：用于判断文献是否符合研究主题范围

软件会把这些配置保存到本地 `app_config.json`，下次打开会自动加载，避免每次重复输入。

### 4. 填写研究主题

在“研究主题”文本框中填写 special issue、research scope 或 topic。

主题写得越清楚，embedding 分数和 LLM 筛选结果通常越稳定。建议写成几行清晰的研究方向，而不是只写一个很短的关键词。

### 5. 推荐两阶段运行流程

#### 第一步：仅生成 embedding 分数

选择：

```text
仅生成 embedding 分数
```

这一步只计算 `score`，不会运行 LLM。完成后先查看输出 Excel 里的 `score` 分布。

#### 第二步：仅运行 LLM 筛选

选择第一步生成的结果文件作为输入文件，然后选择：

```text
仅运行 LLM（使用已有 score）
```

这一步会跳过 embedding，只使用已有 `score` 列进行 LLM 筛选。

建议根据第一步的分数分布设置：

- `LLM最低分`
- `LLM最高分`

例如：

```text
LLM最低分：0.25
LLM最高分：0.35
```

表示只让 LLM 检查 `0.25 < score < 0.35` 的边界文献。

### 6. 输出结果说明

程序会生成一个新的 Excel 文件，并添加：

- `score`：0 到 1 之间的相似度分数
- `scope_decision`：scope 筛选结论
- `scope_confidence`：筛选置信度
- `exclude`：是否建议排除
- `screening_reason`：筛选原因

运行中可能生成：

- `cache/embedding_cache.pkl`：embedding 缓存，默认最多保留最近使用的 50000 条
- `progress.xlsx`：进度备份，写入输出文件所在目录

## 切换不同 API 服务商 Guide

本软件支持 OpenAI 兼容格式的 API。切换 API 服务商时，通常只需要修改三个地方：`API Key`、`Base URL` 和模型名称。

### 1. API Key

填写新服务商提供的 API Key。

示例：

```text
sk-xxxxxxxxxxxxxxxx
```

如果 API Key 前面带有 `Bearer `，软件会自动处理，一般也可以直接粘贴。

### 2. Base URL

填写服务商提供的 OpenAI-compatible API 地址。

常见格式：

```text
https://api.openai.com/v1
https://your-provider.com/v1
https://xxx.xxx.com/v1
```

注意：

- Base URL 通常以 `/v1` 结尾
- 不要填写聊天网页地址
- 不要填写文档页面地址
- 必须是 API endpoint

### 3. 模型名称

需要分别设置两个模型。

#### Embedding 模型

用于计算文献和主题的相似度。

常见示例：

```text
text-embedding-3-small
text-embedding-3-large
```

#### LLM 筛选模型

用于判断低分或边界文献是否属于研究主题范围。

常见示例：

```text
gpt-4o-mini
gpt-4o
```

如果使用第三方 API，请填写该服务商实际支持的模型名称。

### 4. 切换 API 的推荐步骤

1. 打开软件
2. 替换 `API Key`
3. 替换 `Base URL`
4. 替换 `Embedding模型`
5. 替换 `LLM筛选模型`
6. 点击“测试连接”
7. 测试成功后再开始处理 Excel

### 5. 常见问题

#### 测试连接失败

请检查：

- API Key 是否正确
- Base URL 是否以 `/v1` 结尾
- 当前服务商是否支持填写的 embedding 模型
- 网络是否能访问该服务商
- 余额或额度是否充足

#### Embedding 可以运行，但 LLM 阶段失败

通常说明 Embedding 模型名称正确，但 LLM 筛选模型名称不正确，或服务商不支持该聊天模型。

请更换 `LLM筛选模型`。

#### LLM 可以运行，但 embedding 阶段失败

通常说明 LLM 模型可用，但 Embedding 模型名称不正确，或服务商不支持 embedding 接口。

请更换 `Embedding模型`。

#### 换 API 后仍然使用旧配置

软件会保存配置到本地：

```text
app_config.json
```

如果想完全重置配置，可以关闭软件后删除这个文件，再重新打开软件填写配置。

## 小结

切换 API 服务商时，最重要的是确认该服务商同时支持 embedding 接口和 chat/LLM 接口，并且模型名称要填写服务商文档中真实可用的名称。

很多报错不是 API Key 错，而是 Base URL 正确但模型名不支持。推荐每次切换 API 后先点击“测试连接”，确认 embedding 接口可用，再用少量 Excel 数据试跑完整流程。

## GitHub 上传注意事项

不要提交本地密钥、缓存、虚拟环境、打包产物和 Excel 数据文件。

这些文件已加入 `.gitignore`：

```text
.venv/
app_config.json
cache/
build/
dist/
*.zip
*.xlsx
```

如果需要分发可执行文件，建议将 `AI文献评分工具.zip` 上传到 GitHub Release，而不是提交到源码仓库。
