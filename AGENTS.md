# 仓库指南

## 项目结构

`
D:\work\ai-facebook/
+-- config/                # 配置文件
|   +-- settings.py        # .env + YAML 配置加载器
|   +-- rss_sources.yaml   # RSS 源列表 + AI 关键词评分规则
+-- src/                   # 应用源代码
|   +-- main.py            # 流水线编排入口
|   +-- fetch_news.py      # RSS 抓取、去重、评分排序
|   +-- summarize.py       # 文章原文提取 + LLM 中文摘要
|   +-- facebook_poster.py # Facebook Graph API 发布
|   +-- utils.py           # 日志、历史记录、日期解析
+-- work/                  # 运行时数据（已 gitignore）
|   +-- .env               # 敏感配置（API Key、Token）
|   +-- posted_urls.json   # 已发布 URL 去重记录
+-- outputs/logs/          # 每次运行的日志文件
+-- .venv/                 # Python 虚拟环境
+-- setup.ps1              # 一键安装脚本
+-- requirements.txt       # Python 依赖清单
`

## 构建、安装与运行

`powershell
# 一次性安装
.\setup.ps1                     # 创建虚拟环境、安装依赖、复制 .env 模板

# 激活虚拟环境
.venv\Scripts\Activate.ps1

# 运行完整流水线（RSS 抓取 -> LLM 摘要 -> Facebook 发布）
python src\main.py

# 安装或更新依赖
pip install -r requirements.txt
`

流水线以单次批处理方式运行。如需每日自动执行，在 Windows 任务计划程序中创建触发器，
指向 python src\main.py，起始目录设为项目根目录。

## 编码规范

- **Python 3.12+**，使用标准类型注解（list[dict]、str | None 等）
- **4 空格缩进**，不使用 Tab。软限制每行 100 字符。
- 每个 .py 文件顶部写 **模块文档字符串**（单行概括）。
- **导入顺序**：标准库 → 空行 → 第三方库 → 空行 → 本地模块。
- **命名规范**：函数和变量使用 snake_case，常量使用 UPPER_CASE，
  类名使用 PascalCase（本项目较少使用类）。
- 未配置格式化或静态检查工具；保持编辑风格与周围代码一致。

## 配置管理

敏感信息（API Key、Token）只放在 work/.env 文件中，禁止提交到版本控制。
config/settings.py 通过 python-dotenv 加载 .env 文件。
模板文件 .env.example 列出了所有必需变量。

YAML 配置文件（config/rss_sources.yaml）纳入 Git 管理，包含
RSS 源地址、关键词评分权重和运行时限制参数。

## 测试

本项目未配置正式测试框架，通过手动运行验证：

- RSS 抓取：python -c "from src import fetch_news; fetch_news.fetch_and_rank()"
- 完整流水线：python src\main.py（需要配置 API Key）
- 查看 outputs/logs/ 下的日志文件确认每次运行结果。

## 提交与合并请求规范

- 使用简洁的中文提交信息，描述本次改动内容。
- 说明涉及的功能或修复（无需绑定问题追踪系统）。
- 保持提交粒度小而聚焦。
- 提交前确认 work/.env 和 outputs/logs/ 未被暂存
  （已加入 .gitignore，但建议用 git status 确认）。

## Codex 代理操作说明

在本项目中工作时：

- 项目根目录为 D:\work\ai-facebook。运行 Python 命令前先激活虚拟环境。
- 所有大型二进制依赖（.venv、图片、归档等）必须放在项目目录之外，
  遵循全局 AGENTS.md 的依赖外置规则。
- 向 D:\work\ 写入文件或执行需要网络的 pip 安装时，
  使用 
equire_escalated 权限。
- 编辑 Python 文件时使用 shell here-string 或 apply_patch，
  保持 UTF-8 编码，确保行首无多余空格。
