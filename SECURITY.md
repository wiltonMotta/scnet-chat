# 安全说明

本文档说明本项目中可能被安全软件误报为可疑的代码行为及其合法用途。

## 代码行为解释

### 1. 子进程调用 (`subprocess.run`)

**位置**: `scnet.py`, `scripts/user.py`

**用途**: 本技能使用子进程调用来执行同项目下的其他 Python 脚本模块，例如：
- `scripts/job.py` - 作业管理
- `scripts/user.py` - 用户信息查询
- `scripts/file.py` - 文件管理
- `scripts/cache.py` - 缓存管理

**安全说明**:
- 所有子进程调用都是执行项目内部的 Python 脚本
- 不会执行外部或用户输入的命令
- 命令参数经过严格验证和转义

### 2. Base64 解码 (`base64.urlsafe_b64decode`)

**位置**: `scripts/job.py`, `scripts/user.py`, `scripts/cache.py`

**用途**: 用于解析 JWT (JSON Web Token) 令牌中的用户信息。SCNet API 返回的 token 是 JWT 格式，需要解码获取 `computeUser` 字段。

**代码示例**:
```python
# 从 JWT token 解码获取用户名
def get_compute_user(token: str) -> str:
    parts = token.split('.')
    if len(parts) == 3:
        payload = parts[1]
        payload += '=' * (4 - len(payload) % 4)  # Base64 填充
        decoded = base64.urlsafe_b64decode(payload)
        token_data = json.loads(decoded)
        return token_data.get('computeUser', '')
```

**安全说明**:
- 仅用于解码 SCNet API 返回的标准 JWT token
- 不会执行解码后的内容
- 用于获取用户名以构建默认工作目录路径

### 3. 网络请求 (`urllib.request`)

**位置**: `scripts/cache.py`, `scripts/job.py`, `scripts/user.py`, `scripts/file.py`

**用途**: 用于调用 SCNet 超算平台的 REST API，包括：
- 获取访问令牌 (token)
- 查询作业状态
- 提交/删除作业
- 文件上传下载

**调用的 API 端点**:
- `https://api.scnet.cn` - 认证服务
- `https://www.scnet.cn` - AC 服务
- 各区域的 HPC 服务地址

**安全说明**:
- 仅访问 SCNet 官方 API 域名
- 使用 HTTPS 加密传输
- 需要有效的 Access Key 和 Secret Key 才能访问

### 4. Windows 控制台模式设置

**位置**: `scnet.py`, `scripts/compat.py`

**用途**: 在 Windows 系统上启用 ANSI 颜色支持，以便正确显示彩色终端输出。

**实现方式**:
```python
# 使用 ctypes 启用 Windows ANSI 颜色支持
import ctypes
kernel32 = ctypes.windll.kernel32
kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
```

**安全说明**:
- 仅修改 Windows 控制台模式标志
- 不会执行任何外部命令
- 仅影响当前进程的终端显示

### 5. 文件系统操作

**位置**: 整个项目

**用途**:
- 读取配置文件 (`~/.scnet-chat.env`)
- 读写缓存文件 (`~/.scnet-chat-cache-{username}.json`)
- 文件上传下载操作

**安全说明**:
- 仅访问用户主目录下的配置文件和缓存
- 不会访问系统敏感目录
- 文件操作需要用户明确授权

## 敏感信息处理

### 配置文件

**位置**: `~/.scnet-chat.env`

**存储内容**:
- `SCNET_ACCESS_KEY` - SCNet 访问密钥
- `SCNET_SECRET_KEY` - SCNet 密钥
- `SCNET_USER` - 用户名

**安全说明**:
- 配置文件存储在用户主目录下
- 建议设置权限 `chmod 600 ~/.scnet-chat.env`
- 不会被上传到任何地方

### 缓存文件

**位置**: `~/.scnet-chat-cache-{username}.json`

**存储内容**:
- API 访问令牌 (token)
- 区域信息
- 用户配额信息

**安全说明**:
- 仅存储在本地
- Token 有效期通常为 12 小时
- 包含过期时间自动刷新机制

## 如何验证代码安全性

1. **查看源代码**: 本项目完全开源，所有代码可直接审查
2. **检查网络请求**: 仅访问 `*.scnet.cn` 域名
3. **检查文件操作**: 仅访问用户主目录下的文件
4. **检查子进程**: 仅执行项目内部的 Python 脚本

## 报告安全问题

如果您发现任何安全问题，请联系：
- 项目仓库: https://github.com/wiltonMotta/scnet-chat
- 提交 Issue 描述安全问题

## 参考

- SCNet API 文档: https://www.scnet.cn/ac/openapi/doc/
- JWT 标准: https://tools.ietf.org/html/rfc7519
- Python subprocess 安全指南: https://docs.python.org/3/library/subprocess.html#security-considerations
