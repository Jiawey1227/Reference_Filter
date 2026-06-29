# AI 文献相关性评分工具

一个基于 OpenAI 兼容嵌入接口的学术文献相关性评分工具。它会读取 Excel 中的参考文献列，计算每条文献与研究主题的语义相似度，并输出带 `score` 列的 Excel 文件。

## 功能

- 支持图形界面选择输入/输出 Excel 文件
- 支持 `ref`、`refs`、`Reference` 列名，不区分大小写
- 使用嵌入缓存减少重复请求
- 支持断点进度备份
- 可对 `Country/Region` 和 `Email` 信息进行颜色高亮标记
- 默认 API 地址为 `https://aihubmix.com/v1`，默认模型为 `text-embedding-3-small`

## 快速运行

### Windows 一键启动

```bat
git clone https://github.com/<your-name>/<repo-name>.git
cd <repo-name>
setup_and_run.bat
```

脚本会自动创建 `.venv` 虚拟环境、安装依赖并打开图形界面。GUI 不会自动读取本地密钥文件，请在界面的 `API Key` 输入框手动填写密钥。

### 手动运行

```bat
git clone https://github.com/<your-name>/<repo-name>.git
cd <repo-name>
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python gui.py
```

## 输入文件要求

输入文件必须是 Excel 文件，并至少包含以下列之一：

- `ref`
- `refs`
- `Reference`

可选列：

- `Country/Region`、`Country` 或 `Country Region`：用于区域高亮
- `Email`、`E-mail` 或 `Mail`：用于检查国家与邮箱域名是否匹配

## 输出说明

程序会生成一个新的 Excel 文件，并添加：

- `score`：0 到 1 之间的相关性分数，越接近 1 表示越相关

运行中可能生成的本地文件：

- `embedding_cache.pkl`：嵌入缓存
- `progress.xlsx`：进度备份
- `*_result.xlsx`：评分结果

这些文件已经加入 `.gitignore`，不建议上传到 GitHub。

## API Key

图形界面不会自动读取或保存 API Key。每次打开 GUI 后，请在 `API Key` 输入框中手动填写。

命令行模式仍然会读取项目目录下的 `key.txt`。如果只使用 GUI，可以不创建 `key.txt`。

## 发布到 GitHub

第一次发布可以按下面流程操作：

```bat
git init
git add .
git commit -m "Initial release"
git branch -M main
git remote add origin https://github.com/<your-name>/<repo-name>.git
git push -u origin main
```

发布前建议确认不会上传密钥、虚拟环境、缓存和 Excel 数据：

```bat
git status --short
git check-ignore -v key.txt ai_filter embedding_cache.pkl input.xlsx result.xlsx progress.xlsx
```

## 打包为 EXE

如需给不熟悉 Python 的用户分发可执行文件：

```bat
setup_and_run.bat
pip install pyinstaller
pyinstaller "AI 文献评分工具.spec" --clean --noconfirm
```

打包产物会生成在 `dist/` 目录，该目录默认不会上传到 GitHub。
