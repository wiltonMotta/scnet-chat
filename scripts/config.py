#!/usr/bin/env python3
"""
SCNet Chat 全局配置文件

集中管理所有路径、超时时间等常量设置
"""

from pathlib import Path
import os

# =============================================================================
# 路径配置
# =============================================================================

def _get_cache_path() -> Path:
    """获取缓存文件路径，根据用户名区分不同用户的缓存"""
    # 从环境变量或配置文件读取用户名
    username = os.environ.get('SCNET_USER', '')
    
    # 如果环境变量没有设置，尝试从配置文件读取
    if not username:
        config_path = Path.home() / ".scnet-chat.env"
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('SCNET_USER='):
                            username = line.split('=', 1)[1].strip()
                            break
            except Exception:
                pass
    
    # 构建缓存文件名
    if username:
        cache_filename = f".scnet-chat-cache-{username}.json"
    else:
        cache_filename = ".scnet-chat-cache.json"
    
    return Path.home() / cache_filename

# 缓存文件路径（~/.scnet-chat-cache-{username}.json）
CACHE_PATH = _get_cache_path()

# 配置文件路径（~/.scnet-chat.env）
CONFIG_PATH = Path.home() / ".scnet-chat.env"

# =============================================================================
# 缓存过期时间（秒）
# =============================================================================

EXPIRY_PARASTORS = 3600  # 1小时
EXPIRY_WALLTIME = 3600   # 1小时
CACHE_MAX_AGE = 12 * 3600  # 12小时（token有效期）

# =============================================================================
# API 超时时间（秒）
# 基于实测响应时间 × 1.5，最小5秒保护
# =============================================================================

# APIManager 超时 (cache.py)
class APITimeout:
    """API 请求超时时间"""
    # 各方法独立超时时间
    GET_TOKENS = 5          # 获取访问凭证
    GET_CENTER_INFO = 5     # 获取授权区域信息
    GET_USER_INFO = 5       # 获取用户信息
    GET_CLUSTER_INFO = 5    # 获取集群信息
    GET_USER_QUEUES = 5     # 获取用户队列
    GET_USER_QUOTA = 5      # 获取用户配额
    GET_USED_TIME = 5       # 获取已用机时
    
    # 兼容性保留
    QUICK = 5
    NORMAL = 5
    COMPLEX = 5

# JobAPI 超时 (job.py)
class JobTimeout:
    """作业管理 API 超时时间"""
    QUERY_REALTIME_JOBS = 5       # 查询实时作业
    QUERY_REALTIME_JOB_DETAIL = 15 # 作业详情查询
    QUERY_HISTORY_JOBS = 5        # 查询历史作业
    QUERY_HISTORY_JOB_DETAIL = 5  # 历史作业详情
    DELETE_JOB = 15               # 删除作业
    SUBMIT_JOB = 30               # 提交作业
    USER_QUEUES = 5               # 用户队列
    CLUSTER_INFO = 5              # 集群信息
    
    # 兼容性保留
    QUICK = 5
    NORMAL = 5
    COMPLEX = 5
    SUBMIT_OLD = 60

# ClusterAPI 超时 (user.py)
class ClusterTimeout:
    """集群查询 API 超时时间"""
    QUERY_JOB_STATE = 5       # 查询作业状态统计
    QUERY_CORE_STATE = 5      # 查询CPU核心状态
    QUERY_QUEUE_JOBS = 5      # 查询队列作业统计
    
    # 兼容性保留
    QUICK = 5
    NORMAL = 5

# FileAPI 超时 (file.py)
class FileTimeout:
    """文件管理 API 超时时间"""
    LIST_FILES = 5            # 文件列表
    CHECK_EXISTS = 5          # 检查存在
    CREATE_FOLDER = 5         # 创建目录
    CREATE_FILE = 5           # 创建文件
    UPLOAD_FILE = 600         # 上传文件（大文件传输）
    DOWNLOAD_FILE = 600       # 下载文件（大文件传输）
    DELETE_FILE = 5           # 删除文件
    RENAME_FILE = 5           # 重命名
    COPY_FILE = 5             # 复制文件
    MOVE_FILE = 5             # 移动文件
    
    # 兼容性保留
    QUICK = 5
    NORMAL = 5
    TRANSFER = 600

# =============================================================================
# 顶层超时时间 (scnet.py)
# =============================================================================

class AppTimeout:
    """应用层超时时间"""
    QUICK = 10      # 快速操作：用户/集群信息查询 (聚合)
    NORMAL = 15     # 普通操作：作业/文件列表查询 (聚合)
    COMPLEX = 60    # 复杂操作：作业提交/删除、缓存刷新
    TRANSFER = 60   # 文件传输：上传/下载

# =============================================================================
# 其他常量
# =============================================================================

# 异步并发控制
ASYNC_CONCURRENCY_LIMIT = 3  # 信号量限制并发数

# 缓存初始化超时（子查询超时总和）
CACHE_INITIALIZER_TIMEOUT = 35

# 默认作业参数
DEFAULT_JOB_NNODE = '1'
DEFAULT_JOB_WALL_TIME = '24:00:00'
DEFAULT_JOB_APPNAME = 'BASE'
DEFAULT_SUBMIT_TYPE = 'cmd'

# SSL 上下文设置
SSL_VERIFY_MODE = True  # 是否验证 SSL 证书（生产环境应为 True）
