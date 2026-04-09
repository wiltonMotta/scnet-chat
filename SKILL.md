---
name: scnet-chat
description: 通过自然语言交互管理 SCNet Chat 超算平台。
  Use when: 用户需要查询/管理 SCNet 超算平台资源，包括查询作业、提交作业、管理文件、查看账户信息、切换区域等。
  触发关键词：scnet、超算、作业、作业管理、文件管理、账户、余额、查询余额、机时、集群、队列、上传、下载、重命名、区域切换、昆山、山东、西安等。
metadata:
  openclaw:
    requires:
      env:
        - SCNET_ACCESS_KEY
        - SCNET_SECRET_KEY
        - SCNET_USER
      bins:
        - python3
        - python
license: MIT
clawhub:
  slug: scnet-chat
  repo: https://github.com/wiltonMotta/scnet-chat
  autoEnable: true
  version: 2.1.2
---

# SCNet Chat 技能

通过自然语言交互管理 SCNet 超算平台资源。

## When to Run

- 用户提到 SCNet、超算、作业管理、文件管理等关键词
- 用户需要查询作业、提交作业、删除作业
- 用户需要上传/下载/管理远程文件
- 用户需要查看账户信息、余额、机时
- 用户需要切换计算区域（昆山、山东、西安等）

## Workflow

1. **确定用户意图**：识别用户是想查询作业、管理文件、查看账户信息还是切换区域
2. **检查配置**：确保 `~/.scnet-chat.env` 文件存在且包含必要的环境变量
3. **执行命令**（根据操作系统选择正确的启动脚本）：
   - **macOS/Linux**: `{baseDir}/scripts/run "自然语言命令"`
   - **Windows**: `{baseDir}/scripts/run.bat "自然语言命令"`
4. **返回结果**：将执行结果格式化后返回给用户

> **说明**：`scripts/run` 和 `scripts/run.bat` 是跨平台包装脚本，会自动检测并使用正确的 Python 解释器（macOS/Linux 优先使用 `python3`，Windows 优先使用 `python`）。

### 常用命令示例

**macOS/Linux:**
```bash
# 查询作业
# 作业管理 - 查询（基础）
# ⚠️ 注意：实时作业列表和历史作业列表是全区域聚合查询，一次调用返回所有区域的作业
{baseDir}/scripts/run "查询作业"                      # 查询所有区域的实时作业
{baseDir}/scripts/run "查看运行中的作业"              # 查询所有区域运行中的作业
{baseDir}/scripts/run "历史作业"                      # 查询所有区域的历史作业
{baseDir}/scripts/run "作业详情 12345"                # 查询特定作业详情（需指定区域）

# 作业管理 - 查询（高级筛选）
{baseDir}/scripts/run "查询作业 第2页 每页20条"
{baseDir}/scripts/run "查询队列 debug 的作业 所有字段"
{baseDir}/scripts/run "查询用户 zhangsan 的作业"
{baseDir}/scripts/run "查询组作业"
{baseDir}/scripts/run "查询区域ID 12345 的作业"       # 筛选特定区域的作业

# 作业管理 - 历史作业查询（高级用法）
{baseDir}/scripts/run "历史作业 开始时间 2024-01-01 00:00:00 结束时间 2024-01-31 23:59:59"
{baseDir}/scripts/run "历史作业 最近7天"
{baseDir}/scripts/run "查询最近三天的历史作业"                    # 中文数字支持
{baseDir}/scripts/run "查询从2026-04-01到2026-04-03的历史作业"   # 简写日期范围
{baseDir}/scripts/run "查询历史作业，每页5条，显示第二页"         # 中文页码
{baseDir}/scripts/run "查询历史作业，状态为失败"                  # 中文状态筛选
{baseDir}/scripts/run "查询历史作业，队列为comp，每页10条"

# 作业管理 - 实时作业查询（高级用法）
{baseDir}/scripts/run "查询作业 开始时间 2024-01-01 00:00:00 结束时间 2024-01-31 23:59:59"
{baseDir}/scripts/run "查询最近3天的作业"
{baseDir}/scripts/run "查询运行中的作业，每页5条"
{baseDir}/scripts/run "查询作业，状态为排队，显示第2页"

# 提交作业
{baseDir}/scripts/run "提交作业 sleep 900" # 简单命令
{baseDir}/scripts/run "提交作业 启动命令 sleep 900 队列 comp 核心数 2  运行时间 12:00:00 作业名称 production-run1 " # 复杂命令

#提交作业帮助
{baseDir}/scripts/run "如何提交作业"
{baseDir}/scripts/run "提交作业帮助"
{baseDir}/scripts/run "作业有哪些参数"

# 删除作业
{baseDir}/scripts/run "删除作业 12345"

# 作业管理 - 队列和集群
{baseDir}/scripts/run "查询队列"
{baseDir}/scripts/run "集群信息"

# 文件管理 - 列表和上传下载
{baseDir}/scripts/run "文件列表"
{baseDir}/scripts/run "查看文件 /public/home/user"
{baseDir}/scripts/run "上传文件 ./data 到 /public/home/user/"
{baseDir}/scripts/run "下载文件 /public/home/user/data 到 ./"

# 文件管理 - 创建和删除
{baseDir}/scripts/run "创建目录 /public/home/user/workspace"
{baseDir}/scripts/run "创建文件 /public/home/user/data"
{baseDir}/scripts/run "删除文件 /public/home/user/data"

# 文件管理 - 复制移动和重命名
{baseDir}/scripts/run "复制文件 /src/data 到 /dst/"
{baseDir}/scripts/run "移动文件 /src/data 到 /dst/"
{baseDir}/scripts/run "重命名 /old/data 为 data1"
{baseDir}/scripts/run "检查文件 /public/home/user/file"

# 账户信息
{baseDir}/scripts/run "查询余额"
{baseDir}/scripts/run "查询用户"
{baseDir}/scripts/run "作业统计"
{baseDir}/scripts/run "机时"

# 区域切换
{baseDir}/scripts/run "切换到山东"
{baseDir}/scripts/run "切换到西安"

# 缓存管理
{baseDir}/scripts/run "刷新缓存"

# 帮助
{baseDir}/scripts/run "帮助"
```

**Windows:**
```bash
# 查询作业
# 作业管理 - 查询（基础）
# ⚠️ 注意：实时作业列表和历史作业列表是全区域聚合查询，一次调用返回所有区域的作业
{baseDir}/scripts/run.bat "查询作业"                      # 查询所有区域的实时作业
{baseDir}/scripts/run.bat "查看运行中的作业"              # 查询所有区域运行中的作业
{baseDir}/scripts/run.bat "历史作业"                      # 查询所有区域的历史作业
{baseDir}/scripts/run.bat "作业详情 12345"                # 查询特定作业详情（需指定区域）

# 作业管理 - 查询（高级筛选）
{baseDir}/scripts/run.bat "查询作业 第2页 每页20条"
{baseDir}/scripts/run.bat "查询队列 debug 的作业 所有字段"
{baseDir}/scripts/run.bat "查询用户 zhangsan 的作业"
{baseDir}/scripts/run.bat "查询组作业"
{baseDir}/scripts/run.bat "查询区域ID 12345 的作业"       # 筛选特定区域的作业

# 作业管理 - 历史作业查询（高级用法）
{baseDir}/scripts/run.bat "历史作业 开始时间 2024-01-01 00:00:00 结束时间 2024-01-31 23:59:59"
{baseDir}/scripts/run.bat "历史作业 最近7天"
{baseDir}/scripts/run.bat "查询最近三天的历史作业"                    # 中文数字支持
{baseDir}/scripts/run.bat "查询从2026-04-01到2026-04-03的历史作业"   # 简写日期范围
{baseDir}/scripts/run.bat "查询历史作业，每页5条，显示第二页"         # 中文页码
{baseDir}/scripts/run.bat "查询历史作业，状态为失败"                  # 中文状态筛选
{baseDir}/scripts/run.bat "查询历史作业，队列为comp，每页10条"

# 作业管理 - 实时作业查询（高级用法）
{baseDir}/scripts/run.bat "查询作业 开始时间 2024-01-01 00:00:00 结束时间 2024-01-31 23:59:59"
{baseDir}/scripts/run.bat "查询最近3天的作业"
{baseDir}/scripts/run.bat "查询运行中的作业，每页5条"
{baseDir}/scripts/run.bat "查询作业，状态为排队，显示第2页"

# 提交作业
{baseDir}/scripts/run.bat "提交作业 sleep 900" # 简单命令
{baseDir}/scripts/run.bat "在昆山提交作业 sleep 900 队列：comp 运行时间：00:30:00" # 指定区域，队列和运行时间

#提交作业帮助
{baseDir}/scripts/run.bat "如何提交作业"
{baseDir}/scripts/run.bat "提交作业帮助"
{baseDir}/scripts/run.bat "作业有哪些参数"

# 删除作业
{baseDir}/scripts/run.bat "删除作业 12345"

# 作业管理 - 队列和集群
{baseDir}/scripts/run.bat "查询队列"
{baseDir}/scripts/run.bat "集群信息"

# 文件管理 - 列表和上传下载
{baseDir}/scripts/run.bat "文件列表"
{baseDir}/scripts/run.bat "查看文件 /public/home/user"
{baseDir}/scripts/run.bat "上传文件 ./data 到 /public/home/user/"
{baseDir}/scripts/run.bat "下载文件 /public/home/user/data 到 ./"

# 文件管理 - 创建和删除
{baseDir}/scripts/run.bat "创建目录 /public/home/user/workspace"
{baseDir}/scripts/run.bat "创建文件 /public/home/user/data"
{baseDir}/scripts/run.bat "删除文件 /public/home/user/data"

# 文件管理 - 复制移动和重命名
{baseDir}/scripts/run.bat "复制文件 /src/data 到 /dst/"
{baseDir}/scripts/run.bat "移动文件 /src/data 到 /dst/"
{baseDir}/scripts/run.bat "重命名 /old/data 为 data1"
{baseDir}/scripts/run.bat "检查文件 /public/home/user/file"

# 账户信息
{baseDir}/scripts/run.bat "查询余额"
{baseDir}/scripts/run.bat "查询用户"
{baseDir}/scripts/run.bat "作业统计"
{baseDir}/scripts/run.bat "机时"

# 区域切换
{baseDir}/scripts/run.bat "切换到山东"
{baseDir}/scripts/run.bat "切换到西安"

# 缓存管理
{baseDir}/scripts/run.bat "刷新缓存"

# 帮助
{baseDir}/scripts/run.bat "帮助"
```

## Output Format

- 作业查询结果按区域分组显示
- 账户信息以表格形式展示
- 文件操作结果简洁明了
- 错误信息包含具体原因
- 根据用户当前操作给出3个下一步操作的预测问题

## 配置说明

首次使用需要在 `~/.scnet-chat.env` 配置：

```bash
SCNET_ACCESS_KEY=your_access_key
SCNET_SECRET_KEY=your_secret_key
SCNET_USER=your_username
```

获取凭证：https://www.scnet.cn/ui/console/index.html#/personal/auth-manage

## 依赖安装

```bash
pip install aiohttp
```
