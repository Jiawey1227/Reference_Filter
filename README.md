# Author Scope Screening — 学者研究范围筛选工具

本地运行的 React + FastAPI 工具，帮助 SME 根据文章内容初筛符合特刊范围的学者。推荐流程是：**先生成分数 → 人工确定上下限 → 直接继续 AI 审核 → 后续名单复用阈值**。

界面为英文。模型、批处理大小和请求间隔内置，无需用户配置。本版本连接 DashScope 北京地域；不支持直接使用其他地域的 API Key。工具不评价学术影响力，也不自动发送邀请。

## 1. Windows 下载与安装（无需编程环境）

本分支提供 Windows x64 测试发行版。**无需安装 Python、Node.js 或 Git，也不需要输入命令。** AI 筛选仍需联网，并使用自己的 DashScope API Key。

### 下载软件

1. 登录 GitHub，打开 [Windows 构建列表](https://github.com/Jiawey1227/Reference_Filter/actions/workflows/windows-distribution.yml)。
2. 选择 `distribution` 分支上最近一次绿色勾选、构建成功的任务。
3. 在页面底部 **Artifacts** 点击 **AuthorScopeScreening-Windows-x64** 下载。
4. 将下载的 ZIP **全部解压缩**，里面提供以下两种版本，选择一种即可。

首个已通过构建的测试包：[下载页面](https://github.com/Jiawey1227/Reference_Filter/actions/runs/41381760136)。Artifacts 下载通常需要登录，且有保存期限；当前尚未发布正式 GitHub Release。

### 方式 A：安装版（推荐）

1. 双击 **AuthorScopeScreening-Windows-x64-Setup.exe**。
2. 按安装向导完成安装。
3. 双击桌面或开始菜单中的 **Author Scope Screening** 图标。

### 方式 B：便携版（免安装）

1. 将 **AuthorScopeScreening-Windows-x64-portable.zip** 再次全部解压缩。
2. 打开解压后的 **AuthorScopeScreening** 文件夹。
3. 双击 **AuthorScopeScreening.exe**。

不要在 ZIP 内直接运行，也不要只把 EXE 单独拖出来；它需要与同目录的配套文件一起保留。

当前为**未签名测试版**，Windows 或单位安全软件可能提示检查发布者。请按所在机构的软件使用规定处理，勿关闭安全软件。Windows 自动构建和打包启动检查已通过，实际筛选、密钥保存与安装升级仍需在用户电脑上验证。

## 2. 双击启动与日常使用

启动后会出现一个小窗口，浏览器会自动打开操作页面。

- 浏览器没有打开：点击启动窗口中的 **Open Application**。
- 使用过程中：保留启动窗口，不需要命令窗口。
- 再次打开页面：点击 **Open Application**，或再次双击软件图标。
- 使用结束：先下载结果，再点击 **Exit Application** 或关闭启动窗口。
- 仅关闭浏览器不会退出后台服务；如果任务正在运行，退出时会询问是否中断。

请使用启动窗口显示的网址。软件优先使用 `http://127.0.0.1:8765`，端口被占用时自动换用可用端口；**不需要手动启动前后端，也不要使用源码测试时的 5173 / 5174 地址。**

### 更新与数据保存

更新前退出正在运行的软件。安装版运行新版安装包；便携版解压到新文件夹后启动。当前没有自动更新功能。

- 上传文件、结果、缓存和日志：`%LOCALAPPDATA%\AuthorScopeScreening`。可将此路径粘贴到资源管理器地址栏打开。
- API Key：Windows 系统凭据管理器。
- 最近确认的范围和阈值：当前浏览器存储；更换浏览器或端口后可能需要重新填写。
- 任务列表：退出或重启后不会恢复，请提前下载结果。

替换软件文件不会主动删除用户数据。卸载也不会自动清除用户数据目录或保存的 API Key；如需删除密钥，请先使用软件中的 **Forget Saved Key**。

这是独立 `distribution` 发布分支，应用源码与 `main` 分开维护。需要从源码运行的开发者可查看 [main 分支 README](https://github.com/Jiawey1227/Reference_Filter/tree/main#readme)；构建说明见 [distribution/README.md](distribution/README.md)。

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
