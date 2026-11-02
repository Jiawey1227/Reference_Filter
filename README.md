# Author Scope Screening — 学者研究范围筛选工具

本地运行的 React + FastAPI 工具，帮助 SME 根据文章内容初筛符合特刊范围的学者。推荐流程是：**先生成分数 → 人工确定上下限 → 直接继续 AI 审核 → 后续名单复用阈值**。

界面为英文。模型、批处理大小和请求间隔内置，无需用户配置。本版本连接 DashScope 北京地域；不支持直接使用其他地域的 API Key。工具不评价学术影响力，也不自动发送邀请。

## 1. Windows 首次安装（只需做一次）

### 第一步：安装 Python 和 Node.js

先安装下面两个软件，它们是工具运行需要的环境，不需要学习编程：

1. 打开 [Python 下载页](https://www.python.org/downloads/windows/)，安装 **Python 3.12 的 Windows 64 位版本**。如果安装界面有 **Add python.exe to PATH**，请勾选，然后点击 **Install Now**。
2. 打开 [Node.js 下载页](https://nodejs.org/en/download)，安装 **Node.js 24 的 Windows 安装包（.msi）**，使用默认选项完成安装。
3. 安装完成后，关闭之前打开的命令窗口。

### 第二步：下载并解压工具

1. 打开 [本项目 GitHub 页面](https://github.com/Jiawey1227/Reference_Filter)。
2. 点击绿色 **Code** 按钮，再点击 **Download ZIP**。
3. 下载完成后，右键 ZIP 文件，选择 **全部解压缩**。不要在压缩包里直接运行。
4. 打开解压后的文件夹，直到能看到 `README.md`、`requirements.txt` 和 `start_web_app.bat`。

建议把文件夹放到方便找到的位置，例如 `C:\Tools\Reference_Filter`。不需要安装 Git。

### 第三步：安装工具依赖

在刚才的文件夹内，点击资源管理器顶部的地址栏，输入 `cmd`，按回车。这会在正确的文件夹中打开命令提示符。

**依次复制下面四行，每次粘贴一行并按回车，等执行结束后再输入下一行：**

```bat
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
npm ci --prefix frontend
```

第一次会从网络下载依赖，可能需要几分钟。四条命令都完成且没有报错后，关闭此窗口即可。

- 如果提示找不到 `py`，重新打开命令窗口；仍不行时尝试将第一行改为 `python -m venv .venv`，确保使用的是已安装的 Python 3.12。
- 如果提示找不到 `npm`，检查 Node.js 是否安装成功，再重新打开命令窗口。
- 如果下载失败，请检查网络后重试失败的那一行，不必重新下载整个项目。

## 2. 每次使用：双击启动

1. 打开解压后的项目文件夹。
2. 双击 **start_web_app.bat**。
3. 程序会打开后端和前端两个命令窗口，并自动打开浏览器。
4. 等服务启动后，在浏览器中使用 **http://127.0.0.1:5173**。

如果浏览器暂时提示无法连接，等待几秒后刷新；如果没有自动打开，手动复制上述地址到浏览器即可。

**使用过程中保留后端和前端两个命令窗口，不要关闭。** 启动脚本自己的提示窗口可以关闭。使用结束、任务完成并下载结果后，关闭两个服务窗口即可停止程序。下次只需再次双击 `start_web_app.bat`，不需要重复安装。

若提示端口已被占用，先关闭之前启动的服务，再双击一次，避免重复启动。此脚本使用前端 **5173**、后端 **8000**；请使用本节地址，不要使用之前 Mac 测试的 5174 地址。

更新工具版本后，应在新版本文件夹重新执行第三步安装命令，再启动。Windows 启动流程尚需在实际 Windows 电脑上验证；当前开发测试环境为 Mac。

## 3. API Key 设置

在阿里云百炼（Model Studio）创建 **China (Beijing) / 华北2（北京）**地域的标准按量付费 API Key。不要使用阿里云 AccessKey 或 Coding Plan 专用密钥。

参考：[官方获取教程](https://www.alibabacloud.com/help/en/model-studio/get-api-key)。账号开通、验证和计费要求以控制台为准。

1. 将 Key 填入页面的 **Alibaba Cloud Model Studio API Key**。
2. 点击 **Test Connection**。
3. 可选点击 **Save API Key**，保存到系统凭据存储，Windows 使用系统凭据管理器，Mac 使用 Keychain。

保存后，刷新页面或重启后端仍可使用；输入框留空即可。输入新 Key 可临时覆盖，点击 Save API Key 才更新保存项。**Forget Saved Key** 删除保存项。系统可能请求凭据存储访问授权。

密钥不写入浏览器存储、项目文件或结果 Excel。API 调用可能产生费用，请勿公开密钥。

## 4. 准备 Excel

| 字段 | 要求与用途 |
|---|---|
| Email | 必填，每行非空；标识学者，不参与评分 |
| Article | 必填，每行非空；文章标题 |
| Keywords、Abstract | 可选；有内容时补充研究语义 |
| Affiliation | 可选；用于机构关键词高亮 |
| Name | 可选；原样保留 |
| Journal title、Country/Region、H Index、Total Citations 等 | 原样保留，不参与筛选判断 |

必填表头忽略大小写和首尾空格，不兼容旧 `ref / refs / Reference`。建议使用 `.xlsx`。每行独立处理，同一 Email 的多条记录不会自动汇总成作者级结论。

## 5. 首次使用：人工校准后继续审核

### 第一步：Generate Scores for Calibration

1. 点击 **Browse Files** 上传名单。
2. 选择 **1. Generate Scores for Calibration**（首次默认）。
3. 填写 **Target Research Scope**：建议包含特刊方向、研究子领域及明确边界。
4. 可选设置机构高亮，见下节。
5. 点击日志下方的 **Start Processing**。
6. 完成后点击 **Download Results**，人工检查分数与研究内容，确定上下限。

这一阶段只计算 embedding 相似度，Results 表仅追加 `score`；不按阈值分类、不调用 LLM 审核。

### 第二步：填写上下限，点击 Continue to AI Review

在原页面填写：

- **Out-of-scope Threshold (Lower)**：分数 ≤ 下限，按阈值判为不符合。
- **In-scope Threshold (Upper)**：分数 ≥ 上限，按阈值判为符合。
- 严格位于两者之间的记录交给 AI 审核。

阈值范围为 -1 到 1，下限必须小于上限。默认 0.25 / 0.35 只是起点，不代表概率，也不适用于所有主题。

点击 **Continue to AI Review** 即启动第二步：

- 不需要重新上传文件，也不需要再点 Start Processing。
- 自动使用第一步生成的评分文件、原始研究范围和机构高亮设置。
- 不重算 embedding，只审核边界区间。
- 自动保存本次研究范围和阈值到当前浏览器，供以后使用。

本地下载文件中的编辑不会自动同步到服务器。若修改了 Article、Keywords、Abstract 或研究范围，应重新生成分数。

完成后再次 **Download Results**，获取最终结果。AI 判断不明确、置信度不足或审核失败时保留人工复核建议；明确不相关且高置信度时排除。

### 后续名单：Screen a New List

下次打开同一浏览器地址，会恢复最近确认的一组范围和阈值，并默认选择 **3. Screen a New List**。上传新名单后点击 Start Processing，即重新计算分数，再按保存的阈值完成边界审核。

更换研究范围应重新校准。**Confirm & Save Thresholds** 可单独保存当前设置，但不会启动处理。不同浏览器、端口或 localhost / 127.0.0.1 地址的浏览器存储不共用。

### 后端重启后的恢复方式

任务列表保存在内存中，后端重启后无法直接 Continue。若已下载评分文件：

1. 选择 **2. Review Borderline Records**。
2. 上传含 `score` 列的评分文件，保持原始范围和研究内容不变。
3. 填写上下限，点击 **Start Processing**。

`score` 必须是 [-1,1] 内的有限数值。保留 Settings 工作表时，程序会检查原范围是否一致；不要仅通过修改 Settings 来复用不适用的分数。

## 6. Affiliation 绿色高亮

开启 **Highlight Matching Affiliations** 后，每行填写一个关键词，例如：

```text
cardiology
cardiovascular
vascular
```

匹配忽略大小写，采用子字符串包含规则，任意一词命中即可；不自动翻译或扩展同义词。例如 vascular 可以匹配 cardiovascular。

只将命中记录的 **Affiliation 单元格填充浅绿色**。未命中或为空不标色，不输出匹配状态列，也不影响研究判断或最终建议。三个运行模式均支持此功能。

## 7. 输出文件

| 工作表 | 内容 |
|---|---|
| Results | 原始输入列 + score；审核完成后再增加 final_decision、screening_reason |
| Details | 审核阶段的判断来源、置信度等，以 result_row 和 Email 关联主表 |
| Settings | 本次研究范围、阈值及机构高亮配置，每项记录一次 |

仅评分阶段不生成 Details。保留原始行顺序，不删除未通过记录；重复运行会更新工具结果列，而非重复追加。提供冻结表头、筛选、自动换行，分数显示四位小数但保留原始精度。

页面使用英文；当前结果中的部分分类标签和 AI 理由仍可能为中文。
