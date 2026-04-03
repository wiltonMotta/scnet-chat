---
name: scnet-chat
description: 通过自然语言交互管理 SCNet Chat 超算平台，支持区域切换、用户信息查询、账户余额查询、作业管理和文件管理。
license: MIT
clawhub:
  slug: scnet-chat
  repo: https://github.com/wiltonMotta/scnet-chat
  autoEnable: true
  version: 2.0.12
---

# SCNet Skill

通过自然语言交互，轻松管理 SCNet 超算平台的缓存、区域切换、用户信息查询、作业管理和文件管理。

## 功能概览

| 功能类别         | 支持的操作                                       |
| ---------------- | ------------------------------------------------ |
| **缓存管理**     | 自动初始化、自动刷新、手动刷新                   |
| **区域切换** | 支持用户已开通的区域之间切换                 |
| **用户信息**     | 查看账户信息、余额、存储配额、作业统计、机时查询 |
| **作业管理**     | 查询、提交、删除、查看队列、集群信息             |
| **文件管理**     | 列表、上传、下载、创建、删除、重命名、复制、移动 |

## 依赖安装

本 Skill 需要 Python 3.7+ 环境，依赖以下 Python 包：

> **Windows 用户注意**：在 Windows 环境下请使用 `python` 命令运行（`python3` 可能指向无效重定向器，导致脚本无输出）。

### 必需依赖

```bash
# 安装 aiohttp（用于异步并行查询，提升性能）
python -m pip install aiohttp
```

### 可选：使用虚拟环境（推荐）

```bash
# 创建虚拟环境
python -m venv ~/.scnet-chat-venv

# 激活虚拟环境
source ~/.scnet-chat-venv/bin/activate

# 安装依赖
pip install aiohttp

# 后续使用时需要激活虚拟环境
source ~/.scnet-chat-venv/bin/activate
python scnet.py "查询作业"
```

### 依赖说明

| 包名 | 版本要求 | 用途 |
|------|----------|------|
| `aiohttp` | >=3.7.0 | 异步 HTTP 客户端，用于并行 API 查询 |

**性能提升**：
- 安装 `aiohttp` 后，缓存初始化时间从 ~35秒 降至 ~15秒（提升 57%）
- 账户查询时间从 ~15秒 降至 ~5秒（提升 67%）
- 如未安装 `aiohttp`，将自动使用同步方式（功能正常但较慢）

## 配置方式

技能需要配置文件 `~/.scnet-chat.env`：

```bash
# SCNet 访问密钥
SCNET_ACCESS_KEY=your_access_key_here
SCNET_SECRET_KEY=your_secret_key_here
SCNET_USER=your_username_here

# 接口域名（可选）
SCNET_LOGIN_URL=https://api.scnet.cn
SCNET_AC_URL=https://www.scnet.cn
```

### 获取凭证

1. 登录 SCNet 平台: https://www.scnet.cn/ui/console/index.html#/personal/auth-manage
2. 进入个人中心 → 访问控制
3. 创建访问密钥，获取 Access Key 和 Secret Key

---

## 自然语言使用指南

### 通用调用方式

```bash
python scnet.py "自然语言命令"
```

### 1. 缓存管理

| 意图     | 自然语言示例                         | 说明                      |
| -------- | ------------------------------------ | ------------------------- |
| 刷新缓存 | `刷新缓存`、`初始化缓存`、`更新缓存` | 手动刷新 token 和缓存数据 |

缓存会在以下情况自动处理：

- **首次使用**：自动初始化缓存
- **缓存过期**（12小时）：自动刷新缓存

### 2. 区域切换

| 意图     | 自然语言示例                             |
| -------- | ---------------------------------------- |
| 切换中心 | `切换到昆山`、`切换到山东`、`切换到西安` |

**支持的区域**：

- 华东一区【昆山】- 关键词：昆山、华东一区
- 东北一区【哈尔滨】- 关键词：哈尔滨、东北
- 华东三区【乌镇】- 关键词：乌镇、华东三区
- 西北一区【西安】- 关键词：西安、西北
- 华北一区【雄衡】- 关键词：雄衡、华北
- 华东四区【山东】- 关键词：山东、华东四区
- 西南一区【四川】- 关键词：四川、西南
- 华南一区【广东】- 关键词：广东、华南、华南一区
- 核心节点【分区一】- 关键词：分区一、核心
- 核心节点【分区二】- 关键词：分区二
- 华中三区【武汉】- 关键词：武汉、华中

### 3. 用户信息查询

| 意图         | 自然语言示例                                 | 说明                     |
| ------------ | -------------------------------------------- | ------------------------ |
| 用户信息     | `查询用户`、`账户信息`、`我的信息`、`余额`   | 查看完整用户信息         |
| 作业统计     | `作业统计`、`统计信息`、`作业状态统计`       | 实时作业状态分布和核心数 |
| 机时查询     | `机时`、`剩余机时`、`已用机时`               | 查看本月机时使用情况     |

### 4. 作业管理

#### 4.1 查询作业

| 意图       | 自然语言示例                                   | 说明                                           |
| ---------- | ---------------------------------------------- | ---------------------------------------------- |
| 实时作业   | `查询作业`、`查看作业列表`、`运行中的作业`     | 查询当前作业                                   |
| 历史作业   | `历史作业`、`查询历史作业`、`已完成的作业`     | 查询历史记录                                   |
| 按状态筛选 | `查询运行中的作业`、`状态为失败的作业`         | 支持: 运行/排队/完成/失败/取消/超时/退出       |
| 按队列筛选 | `查询队列 debug 的作业`、`队列为 comp`         | 指定队列名                                     |
| 按名称筛选 | `查询作业名称 test`                            | 支持模糊匹配                                   |
| 分页查询   | `查询作业 第2页 每页20条`、`第二页 每页5条`    | 分页控制，支持中文数字（默认第1页，每页10条）  |
| 组作业查询 | `查询组作业`、`显示组所有成员作业`             | 展示组所有成员的作业              |
| 详细字段   | `查询作业 所有字段`、`查询详细作业信息`        | 返回所有字段信息                  |
| 按用户筛选 | `查询用户 zhangsan 的作业`                     | 筛选特定用户的作业                |
| 按区域筛选 | `查询区域ID 12345 的作业`                      | 筛选特定区域的作业                |
| 历史时间范围 | `历史作业 开始时间 2024-01-01 结束时间 2024-01-31` | 指定起止时间查询历史作业         |
| 实时时间范围 | `查询作业 开始时间 2024-01-01 结束时间 2024-01-31` | 指定起止时间查询实时作业         |
| 日期范围 | `查询从2024-01-01到2024-01-31的历史作业`         | 支持"从XXX到XXX"简写格式       |
| 最近N天(历史) | `历史作业 最近7天`、`最近三天的历史作业`    | 查询最近N天的历史作业，支持中文数字 |
| 最近N天(实时) | `查询最近3天的作业`                         | 查询最近N天的实时作业            |
| 作业详情   | `作业详情 123`、`查看作业 456`                 | 查看指定作业详情                  |

**⚠️ 重要说明：**

> **实时作业列表** 和 **历史作业列表** 这两个接口使用 AC 的 token（`clusterName` 为 `ac` 的 token），**查询结果是聚合了所有区域的信息**。这两个接口本身就是全区域聚合查询的接口，**不需要遍历每个区域**来获取全部作业列表。
>
> **技术细节：**
> - **实时作业接口**: `POST /ac/openapi/v2/jobs/monitor/page-list`
> - **历史作业接口**: `POST /ac/openapi/v2/jobs/history/page-list`
> - **Token 来源**: 缓存中 `clusterName` 为 `ac` 的 token
> - **域名**: `https://www.scnet.cn`（AC 服务地址）
>
> **使用建议：**
> - 如果需要查询所有区域的作业，**直接调用这两个接口一次即可**，无需遍历每个区域
> - 如果只需要特定区域的作业，使用 `区域ID` 参数进行筛选
>
> **对比说明：**
> | 接口类型 | Token 来源 | 查询范围 | 是否需要遍历 |
> | -------- | ---------- | -------- | ------------ |
> | 实时/历史作业列表 | AC (clusterName='ac') | 全区域聚合 | ❌ 不需要 |
> | 作业详情 | 当前区域 | 单个区域 | ✅ 已聚合 |
> | 队列查询 | 当前区域 | 单个区域 | ❌ 不需要 |
> | 集群信息 | 当前区域 | 单个区域 | ❌ 不需要 |
>
> **显示方式：**
> - 实时/历史作业列表查询结果会**按区域分组显示**，例如：
>   ```
>   ▶ 华东一区【昆山】 (10 条)
>   ──────────────────────────────────
>     1. 作业 110463064
>        名称: job-xxx
>        ...
>   
>   ▶ 华中三区【武汉】 (6 条)
>   ──────────────────────────────────
>     1. 作业 110463xxx
>        ...
>   ```

**作业状态参考**：

| 中文状态 | API代码 | 英文别名 | 说明 |
|----------|---------|----------|------|
| 运行 | statR | running | 作业正在运行中 |
| 排队 | statQ | queue/queued | 作业在队列中等待 |
| 完成 | statC | completed | 作业正常完成 |
| 失败 | statD | failed | 作业执行失败 |
| 取消 | statDE | cancelled | 作业被取消 |
| 超时 | statT | timeout | 作业运行超时 |
| 退出 | statE | exit | 作业异常退出 |
| 挂起 | statS | suspend | 作业被挂起 |
| 保留 | statH | hold | 作业被保留 |
| 等待 | statW | wait | 作业等待中 |
| 节点异常 | statN | nodefail | 节点故障导致 |
| 重新运行 | statRQ | rerun | 作业重新运行 |

**智能识别示例**：
- `查询历史作业，状态为失败` → 自动识别为 statD
- `查询作业，每页5条，显示第二页` → 中文"第二页"自动转为 page=2
- `查询最近三天的历史作业` → 中文"三天"自动转为 days=3
- `查询从2026-04-01到2026-04-03的历史作业` → 自动填充时间为 00:00:00 和 23:59:59

#### 4.2 提交作业

| 意图           | 自然语言示例                                                | 说明                    |
| -------------- | ----------------------------------------------------------- | ----------------------- |
| 提交作业帮助   | `如何提交作业`、`提交作业帮助`、`作业有哪些参数`            | 显示提交作业帮助信息    |
| 带参数提交     | `提交作业 --cmd "sleep 100" --queue debug`                  | 直接指定参数提交        |
| 指定中心提交   | `在昆山提交作业 sleep 60`、`在山东提交作业 hostname`        | 自动切换中心并提交      |
| 简洁格式       | `提交作业 sleep 900`、`以 sleep 900 提交作业`               | 自动提取命令            |

**提交作业帮助**：

```bash
# 查看提交作业帮助
python scnet.py "如何提交作业"
python scnet.py "提交作业帮助"
python scnet.py "作业有哪些参数"
```

**支持的参数**（参考 [API 文档](https://www.scnet.cn/ac/openapi/doc/2.0/api/jobmanager/job.html)）：

| 参数 | 说明 | 示例 |
|------|------|------|
| `cmd` | 执行的命令（必填） | `sleep 100`, `mpirun -np 4 ./app` |
| `--queue` | 队列名称 | `comp`, `debug`, `normal` |
| `--nnode` | 节点数量 | `1`, `2`, `4` |
| `--work-dir` | 工作目录 | `/public/home/user/work` |
| `--job-name` | 作业名称 | `my-job-001` |
| `--wall-time` | 最大运行时间 | `01:00:00`, `24:00:00` |
| `--nproc` | 总核心数 | `4`, `8`, `16` |
| `--ppn` | 每节点核心数 | `4`, `8` |
| `--ngpu` | GPU卡数/节点 | `1`, `2` |
| `--ndcu` | DCU卡数/节点 | `1`, `2` |
| `--job-mem` | 每个节点内存 | `16GB`, `32GB` |
| `--exclusive` | 是否独占节点 | `1`（独占）|
| `--std-out` | 标准输出文件路径 | `/path/out.%j` |
| `--std-err` | 标准错误文件路径 | `/path/err.%j` |

**提交作业示例**：

```bash
# 简单命令
python scnet.py "提交作业 sleep 900"

# 指定队列和运行时间
python scnet.py "提交作业 sleep 900 --queue comp --wall-time 00:30:00"

# 在指定中心提交作业
python scnet.py "在昆山提交作业 hostname"
python scnet.py "在山东提交作业 mpirun -np 4 ./myapp"

# MPI 并行作业
python scnet.py "提交作业 mpirun -np 8 ./myapp --queue normal --nnode 2 --job-name test-mpi"

# GPU 作业
python scnet.py "提交作业 ./gpu_program --queue gpu --ngpu 1 --job-mem 16GB"

# 完整参数示例
python scnet.py "提交作业 --cmd './myapp' --queue comp --nnode 2 --ppn 8 --wall-time 12:00:00 --job-name production-run"
```

#### 4.3 删除作业

| 意图     | 自然语言示例                                   |
| -------- | ---------------------------------------------- |
| 删除作业 | `删除作业 123`、`取消作业 456`、`终止作业 789` |

#### 4.4 队列和集群信息

| 意图     | 自然语言示例                       |
| -------- | ---------------------------------- |
| 查询队列 | `查询队列`、`可用队列`、`队列列表` |
| 集群信息 | `集群信息`、`调度器信息`           |

### 5. 文件管理

#### 5.1 文件列表

| 意图         | 自然语言示例                                   |
| ------------ | ---------------------------------------------- |
| 查看文件列表 | `文件列表`、`查看文件`、`ls /public/home/user` |

#### 5.2 上传下载

| 意图     | 自然语言示例                                |
| -------- | ------------------------------------------- |
| 上传文件 | `上传文件 ./test.txt 到 /public/home/user/` |
| 下载文件 | `下载文件 /public/home/user/test.txt 到 ./` |

#### 5.3 文件操作

| 意图     | 自然语言示例                                              |
| -------- | --------------------------------------------------------- |
| 创建目录 | `创建目录 /public/home/user/newdir`、`mkdir /work/test`   |
| 创建文件 | `创建文件 /public/home/user/test.txt`、`touch file`       |
| 删除文件 | `删除文件 /public/home/user/test.txt`、`rm /work/old.txt` |
| 重命名   | `重命名 /old/name.txt 为 newname.txt`                     |
| 复制文件 | `复制文件 /src/file.txt 到 /dst/`                         |
| 移动文件 | `移动文件 /src/file.txt 到 /dst/`                         |
| 检查存在 | `检查文件 /public/home/user/file.txt`                     |

---

## 使用示例

### 命令行直接调用

```bash
# 缓存管理
python scnet.py "刷新缓存"

# 区域切换
python scnet.py "切换到山东"
python scnet.py "切换到西安"

# 用户信息查询
python scnet.py "查询用户"
python scnet.py "我的账户信息"
python scnet.py "作业统计"
python scnet.py "机时"

# 作业管理 - 查询（基础）
# ⚠️ 注意：实时作业列表和历史作业列表是全区域聚合查询，一次调用返回所有区域的作业
python scnet.py "查询作业"                      # 查询所有区域的实时作业
python scnet.py "查看运行中的作业"              # 查询所有区域运行中的作业
python scnet.py "历史作业"                      # 查询所有区域的历史作业
python scnet.py "作业详情 12345"                # 查询特定作业详情（需指定区域）

# 作业管理 - 查询（高级筛选）
python scnet.py "查询作业 第2页 每页20条"
python scnet.py "查询队列 debug 的作业 所有字段"
python scnet.py "查询用户 zhangsan 的作业"
python scnet.py "查询组作业"
python scnet.py "查询区域ID 12345 的作业"       # 筛选特定区域的作业

# 作业管理 - 历史作业查询（高级用法）
python scnet.py "历史作业 开始时间 2024-01-01 00:00:00 结束时间 2024-01-31 23:59:59"
python scnet.py "历史作业 最近7天"
python scnet.py "查询最近三天的历史作业"                    # 中文数字支持
python scnet.py "查询从2026-04-01到2026-04-03的历史作业"   # 简写日期范围
python scnet.py "查询历史作业，每页5条，显示第二页"         # 中文页码
python scnet.py "查询历史作业，状态为失败"                  # 中文状态筛选
python scnet.py "查询历史作业，队列为comp，每页10条"

# 作业管理 - 实时作业查询（高级用法）
python scnet.py "查询作业 开始时间 2024-01-01 00:00:00 结束时间 2024-01-31 23:59:59"
python scnet.py "查询最近3天的作业"
python scnet.py "查询运行中的作业，每页5条"
python scnet.py "查询作业，状态为排队，显示第2页"

# 作业管理 - 提交和删除
python scnet.py "提交作业"
python scnet.py "提交作业 --cmd 'mpirun -np 4 ./myapp' --queue normal"
python scnet.py "删除作业 12345"

# 作业管理 - 队列和集群
python scnet.py "查询队列"
python scnet.py "集群信息"

# 文件管理 - 列表和上传下载
python scnet.py "文件列表"
python scnet.py "查看文件 /public/home/user"
python scnet.py "上传文件 ./data.txt 到 /public/home/user/"
python scnet.py "下载文件 /public/home/user/result.txt 到 ./"

# 文件管理 - 创建和删除
python scnet.py "创建目录 /public/home/user/workspace"
python scnet.py "创建文件 /public/home/user/hello.txt"
python scnet.py "删除文件 /public/home/user/old.txt"

# 文件管理 - 复制移动和重命名
python scnet.py "复制文件 /src/data.txt 到 /dst/"
python scnet.py "移动文件 /src/data.txt 到 /dst/"
python scnet.py "重命名 /old/name.txt 为 newname.txt"

# 帮助
python scnet.py "帮助"
```

### 交互式使用

```bash
python scnet.py

SCNet Skill | 输入自然语言命令，或 'help' 查看帮助

> 查询作业
[显示实时作业列表]

> 提交作业帮助
[显示作业提交帮助信息]

> 提交作业 sleep 100 --queue comp
[提交作业到 comp 队列]

> 切换到山东
✓ 已切换到 华东四区【山东】

```

---

## 架构说明

本 Skill 采用**统一入口架构**：

- **`scnet.py`** 是**唯一推荐的入口**，支持自然语言交互
- **`scripts/*.py`** 是内部实现细节，不推荐直接调用

### 为什么不推荐直接调用底层脚本？

1. **自然语言更方便** - 无需记忆复杂的命令参数
2. **维护更稳定** - 内部实现可能变更，自然语言接口保持稳定
3. **体验更一致** - 所有操作都通过同一种方式完成

---

## 底层脚本（内部实现）

> ⚠️ **注意**：以下脚本为内部实现，仅用于开发调试，不推荐日常使用。

### 作业管理 (scripts/job.py)

```bash
# 查询实时作业
python scripts/job.py

# 查询历史作业
python scripts/job.py --history

# 查询作业详情
python scripts/job.py --job-id 123

# 提交作业（带参数）
python scripts/job.py --submit --cmd "sleep 100" --queue debug

# 删除作业
python scripts/job.py --delete --job-id 123

# 查询队列
python scripts/job.py --queues

# 查询集群信息
python scripts/job.py --cluster-info
```

### 文件管理 (scripts/file.py)

```bash
# 列出文件
python scripts/file.py --list [路径]

# 上传文件
python scripts/file.py --upload <本地文件> <远程目录>

# 下载文件
python scripts/file.py --download <远程文件> <本地目录>

# 创建目录
python scripts/file.py --mkdir <路径>

# 创建空文件
python scripts/file.py --touch <路径>

# 删除文件
python scripts/file.py --delete <路径>

# 重命名
python scripts/file.py --rename <原路径> <新名称>

# 复制文件
python scripts/file.py --copy <源> <目标>

# 移动文件
python scripts/file.py --move <源> <目标>
```

### 用户信息 (scripts/user.py)

```bash
# 查询用户信息（内部实现，不推荐直接调用）
python scripts/user.py
```

---

## 文件说明

| 文件               | 说明                                                  |
| ------------------ | ----------------------------------------------------- |
| `scnet.py`         | **主入口文件（推荐）**，支持自然语言意图识别和命令路由 |
| `scripts/cache.py` | 内部模块：缓存管理，处理 token 获取和缓存刷新          |
| `scripts/job.py`   | 内部模块：作业管理，支持查询、提交、删除作业           |
| `scripts/file.py`  | 内部模块：文件管理，支持上传、下载、文件操作           |
| `scripts/user.py`  | 内部模块：用户信息查询，显示账户和配额信息             |

### 架构原则

- **统一入口**：所有操作通过 `scnet.py` 的自然语言接口完成
- **内部隔离**：`scripts/*.py` 作为内部实现，不保证向后兼容
- **文档优先**：SKILL.md 只描述自然语言用法，不维护底层脚本参数文档

---

## 注意事项

1. **首次使用**：需要先配置 `~/.scnet-chat.env` 文件
2. **依赖安装**：建议安装 `aiohttp` 以获得最佳性能（缓存初始化快 57%，账户查询快 67%）
3. **缓存管理**：缓存过期（12小时）会自动刷新，也可手动刷新
4. **作业提交**：使用自然语言提交作业，如需帮助可输入"提交作业帮助"查看详细用法和参数说明
5. **文件操作**：上传下载大文件时可能需要较长时间
6. **切换中心**：切换区域后，后续操作将针对该中心执行
7. **配置文件权限**：建议设置 `chmod 600 ~/.scnet-chat.env`
