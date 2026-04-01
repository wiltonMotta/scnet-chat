#!/usr/bin/env python3
"""
SCNet Skill - 统一入口
支持自然语言交互管理 SCNet 超算平台

使用方法:
    python scnet.py "用户对话内容"
    
示例:
    python scnet.py "查询作业"
    python scnet.py "提交作业 --cmd 'sleep 100' --queue debug"
    python scnet.py "删除作业 123"
    python scnet.py "查看文件列表 /public/home/user"
"""

import sys
import os
import re
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Windows 终端兼容处理（避免 GBK 编码下 UnicodeEncodeError 崩溃）
if sys.platform == "win32":
    # 启用 ANSI 颜色支持（Windows 10+）
    os.system("")
    # 强制 stdout/stderr 使用 utf-8，无法编码的字符用替换符代替
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

# 添加 scripts 目录到路径
SCRIPTS_DIR = Path(__file__).parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

# 导入配置
from config import CACHE_PATH, CONFIG_PATH

# 导入配置文件
from config import AppTimeout, CACHE_PATH

# 导入底层模块
from cache import switch_default_cluster, CacheManager, ConfigManager, Logger, CacheInitializer


class Colors:
    """终端颜色代码"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


class IntentRecognizer:
    """意图识别器 - 支持自然语言理解"""
    
    # 计算中心映射
    CLUSTERS = {
        "昆山": "华东一区【昆山】", "华东一区": "华东一区【昆山】",
        "哈尔滨": "东北一区【哈尔滨】", "东北": "东北一区【哈尔滨】",
        "乌镇": "华东三区【乌镇】", "华东三区": "华东三区【乌镇】",
        "西安": "西北一区【西安】", "西北": "西北一区【西安】",
        "雄衡": "华北一区【雄衡】", "华北": "华北一区【雄衡】",
        "山东": "华东四区【山东】", "华东四区": "华东四区【山东】",
        "四川": "西南一区【四川】", "西南": "西南一区【四川】",
        "广东": "华南一区【广东】", "华南": "华南一区【广东】", "华南一区": "华南一区【广东】",
        "分区一": "核心节点【分区一】", "核心": "核心节点【分区一】",
        "分区二": "核心节点【分区二】",
        "武汉": "华中三区【武汉】", "华中": "华中三区【武汉】",
    }
    
    # 作业状态映射
    JOB_STATUS = {
        "running": ["运行", "running", "执行中"],
        "queue": ["排队", "queue", "等待"],
        "completed": ["完成", "completed", "结束"],
        "exit": ["退出", "exit", "失败"],
    }
    
    def recognize(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """
        识别用户意图并提取参数
        
        Returns:
            (intent, params) - intent 为意图类型，params 为提取的参数
        """
        text_lower = text.strip().lower()
        params = {"raw": text}
        
        # ========== 缓存管理 ==========
        if any(k in text_lower for k in ["刷新缓存", "初始化缓存", "更新缓存", "reload cache", "刷新全部缓存", "刷新所有缓存"]):
            return "cache_refresh", params
            
        # ========== 数据中心切换 ==========
        # 检查是否包含提交作业关键词（如"在山东提交作业"应优先处理提交）
        is_job_submit = any(k in text_lower for k in ["提交作业", "提交任务", "submit job", "run job", "运行作业"])
        
        if not is_job_submit:
            for key, name in self.CLUSTERS.items():
                if key in text_lower:
                    params["cluster_name"] = name
                    return "switch_cluster", params
        
        # ========== 用户信息查询 ==========
        if any(k in text_lower for k in ["用户信息", "我的信息", "账户信息", "余额", "我是谁", "user info", "查询用户"]):
            return "user_info", params
        
        # 查询作业统计信息
        if any(k in text_lower for k in ["作业统计", "统计信息", "作业状态统计", "job stats", "job statistics"]):
            return "job_stats", params
        
        # 查询机时
        if any(k in text_lower for k in ["机时", "剩余机时", "已用机时", "walltime", "机时信息"]):
            return "walltime", params
            
        # ========== 作业管理 ==========
        # 提交作业帮助（必须在提交作业之前检查）
        if any(k in text_lower for k in ["如何提交作业", "提交作业帮助", "作业提交帮助", "作业有哪些参数", "job submit help", "how to submit job", "我要提交作业"]):
            return "job_submit_help", params
            
        # 提交作业（支持 "在[中心]提交作业" 格式）
        if is_job_submit:
            params.update(self._extract_job_params(text))
            # 检查是否指定了计算中心
            for key, name in self.CLUSTERS.items():
                if key in text_lower:
                    params["cluster_name"] = name
                    break
            return "job_submit", params
            
        # 删除作业
        if any(k in text_lower for k in ["删除作业", "取消作业", "终止作业", "杀掉作业", "delete job", "kill job"]):
            params["job_id"] = self._extract_job_id(text)
            return "job_delete", params
            
        # 查询队列
        if any(k in text_lower for k in ["查询队列", "可用队列", "队列列表", "queues", "queue list"]):
            return "job_queues", params
            
        # 集群信息
        if any(k in text_lower for k in ["集群信息", "调度器信息", "cluster info", "scheduler info"]):
            return "cluster_info", params
            
        # 作业详情
        if any(k in text_lower for k in ["作业详情", "查看作业", "job detail"]):
            params["job_id"] = self._extract_job_id(text)
            if params["job_id"]:
                return "job_detail", params
            
        # 历史作业查询
        if any(k in text_lower for k in ["历史作业", "历史任务", "history jobs", "completed jobs"]):
            params.update(self._extract_job_filter_params(text))
            return "job_history", params
            
        # ========== 文件管理 ==========
        # 文件列表
        if any(k in text_lower for k in ["文件列表", "查看文件", "list files", "ls ", "目录内容"]):
            params["path"] = self._extract_path(text)
            return "file_list", params
            
        # 上传文件
        if any(k in text_lower for k in ["上传文件", "upload file", "上传"]):
            local_path, remote_path = self._extract_upload_paths(text)
            params["local_path"] = local_path
            params["remote_path"] = remote_path
            return "file_upload", params
            
        # 下载文件
        if any(k in text_lower for k in ["下载文件", "download file", "下载"]):
            remote_path, local_path = self._extract_download_paths(text)
            params["remote_path"] = remote_path
            params["local_path"] = local_path
            return "file_download", params
            
        # 创建目录
        if any(k in text_lower for k in ["创建目录", "新建目录", "mkdir", "make dir"]):
            params["path"] = self._extract_path(text)
            return "file_mkdir", params
            
        # 创建文件
        if any(k in text_lower for k in ["创建文件", "新建文件", "touch file", "新建空文件"]):
            params["path"] = self._extract_path(text)
            return "file_touch", params
            
        # 复制文件（放在删除之前检查）
        if any(k in text_lower for k in ["复制文件", "拷贝文件", "copy file", "cp "]):
            src, dst = self._extract_copy_params(text)
            params["src"] = src
            params["dst"] = dst
            return "file_copy", params
            
        # 删除文件
        if any(k in text_lower for k in ["删除文件", "删除目录", "remove file", "delete file"]) or \
           text_lower.startswith("rm ") or " rm " in text_lower:
            params["path"] = self._extract_path(text)
            return "file_delete", params
            
        # 重命名文件
        if any(k in text_lower for k in ["重命名", "改名", "rename"]):
            old_path, new_name = self._extract_rename_params(text)
            params["old_path"] = old_path
            params["new_name"] = new_name
            return "file_rename", params
            
        # 移动文件
        if any(k in text_lower for k in ["移动文件", "剪切文件", "move file", "mv "]):
            src, dst = self._extract_copy_params(text)
            params["src"] = src
            params["dst"] = dst
            return "file_move", params
            
        # 检查文件存在
        if any(k in text_lower for k in ["检查文件", "文件存在", "exists", "file exists"]):
            params["path"] = self._extract_path(text)
            return "file_exists", params
            
        # 实时作业查询（放在文件管理之后，避免路径中的"job"被误识别）
        # 使用更严格的匹配：必须是完整的词，且不是文件路径的一部分
        job_keywords = ["作业", "任务", "jobs"]
        if any(k in text_lower for k in job_keywords) or \
           (" job " in text_lower or text_lower.startswith("job ") or text_lower.endswith(" job")):
            params.update(self._extract_job_filter_params(text))
            return "job_list", params
            
        # ========== 帮助 ==========
        if any(k in text_lower for k in ["帮助", "help", "怎么用", "使用说明"]):
            return "help", params
            
        return "unknown", params
    
    def _extract_job_id(self, text: str) -> Optional[str]:
        """从文本中提取作业ID"""
        # 匹配数字ID
        patterns = [
            r'作业[\s]*([0-9]+)',  # 作业 123
            r'job[\s]*([0-9]+)',   # job 123
            r'#([0-9]+)',          # #123
            r'\b([0-9]{3,})\b',    # 至少3位数字
        ]
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return match.group(1)
        return None
    
    def _extract_path(self, text: str) -> Optional[str]:
        """从文本中提取路径"""
        # 匹配 Linux 风格路径
        patterns = [
            r'(/[\w\-/\.]+)',           # /public/home/user
            r'路径[\s]*([\w\-/\.]+)',    # 路径 /xxx
            r'path[\s]*([\w\-/\.]+)',    # path /xxx
            r'到[\s]*(/[\w\-/\.]+)',     # 到 /xxx
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                path = match.group(1)
                # 确保路径以 / 开头
                if path.startswith('/'):
                    return path
        return None
    
    def _extract_upload_paths(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """提取上传的本地路径和远程路径"""
        local_path = None
        remote_path = None
        
        # 匹配 "上传 xxx 到 xxx" 或 "upload xxx to xxx"
        # 支持完整路径
        text_lower = text.lower()
        
        # 首先尝试匹配完整格式：上传 <本地路径> 到 <远程路径>
        patterns = [
            r'上传[\s]+([A-Za-z]:[\w\-/.\\\\]+|[/~\.][\w\-/.]+|[\w\-]+/[\w\-/.]+)[\s]+到[\s]+(/[\w\-/.]*)',
            r'upload[\s]+([A-Za-z]:[\w\-/.\\\\]+|[/~\.][\w\-/.]+|[\w\-]+/[\w\-/.]+)[\s]+to[\s]+(/[\w\-/.]*)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                local_path = match.group(1)
                remote_path = match.group(2)
                return local_path, remote_path
        
        # 单独提取本地路径和远程路径
        local_path = self._extract_local_path(text)
        
        # 提取远程路径（查找"到"后面的路径）
        remote_match = re.search(r'到[\s]+(/[\w\-/.]+)', text)
        if remote_match:
            remote_path = remote_match.group(1)
        
        return local_path, remote_path
    
    def _extract_download_paths(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """提取下载的远程路径和本地路径"""
        remote_path = None
        local_path = None
        
        # 匹配 "下载 xxx 到 xxx" 或 "download xxx to xxx"
        # 第一个路径是远程路径（服务器端），第二个是本地路径
        text_lower = text.lower()
        
        # 尝试匹配完整格式
        patterns = [
            r'下载[\s]+(/[\w\-/.]+)[\s]+到[\s]+([A-Za-z]:[\w\-/.\\\\]+|/~[\w\-/.]+|/[\w\-/.]+)',
            r'download[\s]+(/[\w\-/.]+)[\s]+to[\s]+([A-Za-z]:[\w\-/.\\\\]+|/~[\w\-/.]+|/[\w\-/.]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                remote_path = match.group(1)
                local_path = match.group(2)
                return remote_path, local_path
        
        # 备用：查找 "到" 分隔的两个路径
        # 查找所有绝对路径
        all_paths = re.findall(r'(/[\w\-/.]+)', text)
        if len(all_paths) >= 2:
            # 第一个是远程路径，第二个是本地路径
            remote_path = all_paths[0]
            local_path = all_paths[1]
            return remote_path, local_path
        
        # 单独提取
        remote_path = self._extract_path(text)
        local_path = self._extract_local_path(text)
        return remote_path, local_path
    
    def _extract_local_path(self, text: str) -> Optional[str]:
        """提取本地路径"""
        # 匹配 ./ 或 ~/ 或 / 开头的完整路径
        patterns = [
            r'([A-Za-z]:[/\\][\w\-/.\\]+)',  # Windows 路径 C:/xxx 或 C:\xxx
            r'(/[\w\-/.]+(?:/[\w\-/.]+)*)',   # Unix 绝对路径 /xxx/yyy
            r'(\./[\w\-/.]+)',               # ./xxx
            r'(~/[\w\-/.]+)',                # ~/xxx
            r'本地[\s]*([\w\-/.]+)',          # 本地 xxx
            r'local[\s]*([\w\-/.]+)',         # local xxx
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None
    
    def _extract_rename_params(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """提取重命名参数"""
        old_path = None
        new_name = None
        
        patterns = [
            r'重命名[\s]*(/[\w\-/.]+)[\s]*为[\s]*([\w\-/.]+)',
            r'改名[\s]*(/[\w\-/.]+)[\s]*为[\s]*([\w\-/.]+)',
            r'rename[\s]*(/[\w\-/.]+)[\s]*to[\s]*([\w\-/.]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                old_path = match.group(1)
                new_name = match.group(2)
                return old_path, new_name
        
        old_path = self._extract_path(text)
        return old_path, new_name
    
    def _extract_copy_params(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """提取复制/移动参数"""
        src = None
        dst = None
        
        patterns = [
            r'复制[\s]*(/[\w\-/.]+)[\s]*到[\s]*(/[\w\-/.]*)',
            r'移动[\s]*(/[\w\-/.]+)[\s]*到[\s]*(/[\w\-/.]*)',
            r'copy[\s]*(/[\w\-/.]+)[\s]*to[\s]*(/[\w\-/.]*)',
            r'move[\s]*(/[\w\-/.]+)[\s]*to[\s]*(/[\w\-/.]*)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                src = match.group(1)
                dst = match.group(2)
                return src, dst
        
        # 尝试提取两个路径
        paths = re.findall(r'(/[\w\-/.]+)', text)
        if len(paths) >= 2:
            return paths[0], paths[1]
        elif len(paths) == 1:
            return paths[0], None
        return None, None
    
    def _extract_job_params(self, text: str) -> Dict[str, Any]:
        """提取作业提交参数"""
        params = {}
        
        # 提取命令
        cmd_match = re.search(r'--cmd[\s]*["\']?([^"\']+)["\']?', text)
        if cmd_match:
            params["cmd"] = cmd_match.group(1).strip()
        elif '运行' in text or '执行' in text:
            # 尝试提取引号中的命令
            cmd_match = re.search(r'["\']([^"\']+)["\']', text)
            if cmd_match:
                params["cmd"] = cmd_match.group(1).strip()
        elif '以' in text and '提交' in text:
            # 匹配 "以 xxx 提交作业" 格式
            cmd_match = re.search(r'以\s*(.+?)\s*提交', text)
            if cmd_match:
                params["cmd"] = cmd_match.group(1).strip()
        else:
            # 匹配 "提交作业 xxx" 格式（xxx 作为命令）
            # 移除计算中心名称后再提取命令
            text_clean = text
            for key in self.CLUSTERS.keys():
                text_clean = text_clean.replace(key, '')
            cmd_match = re.search(r'提交作业\s+(.+)', text_clean)
            if cmd_match:
                params["cmd"] = cmd_match.group(1).strip()
        
        # 提取队列
        queue_match = re.search(r'--queue[\s]*([\w]+)', text)
        if queue_match:
            params["queue"] = queue_match.group(1)
        else:
            # 匹配 "队列 xxx" 或 "queue xxx"
            queue_match = re.search(r'队列[\s]+([\w]+)', text)
            if queue_match:
                params["queue"] = queue_match.group(1)
        
        # 提取工作目录
        workdir_match = re.search(r'--work-dir[\s]*["\']?(/[\w\-/\.]+)["\']?', text)
        if workdir_match:
            params["work_dir"] = workdir_match.group(1)
        else:
            workdir_match = re.search(r'工作目录[\s]*["\']?(/[\w\-/\.]+)["\']?', text)
            if workdir_match:
                params["work_dir"] = workdir_match.group(1)
        
        # 提取节点数
        nnode_match = re.search(r'--nnode[\s]*(\d+)', text)
        if nnode_match:
            params["nnode"] = nnode_match.group(1)
        else:
            nnode_match = re.search(r'(\d+)[\s]*个?节点', text)
            if nnode_match:
                params["nnode"] = nnode_match.group(1)
        
        # 提取作业名
        name_match = re.search(r'--job-name[\s]*["\']?([^"\']+)["\']?', text)
        if name_match:
            params["job_name"] = name_match.group(1)
        
        # 提取运行时间
        walltime_match = re.search(r'--wall-time[\s]*["\']?([\d:]+)["\']?', text)
        if walltime_match:
            params["wall_time"] = walltime_match.group(1)
        else:
            walltime_match = re.search(r'(\d+)[\s]*小时', text)
            if walltime_match:
                params["wall_time"] = f"{walltime_match.group(1)}:00:00"
        
        return params
    
    def _extract_job_filter_params(self, text: str) -> Dict[str, Any]:
        """提取作业筛选参数"""
        params = {}
        
        # 状态筛选
        for status_code, keywords in self.JOB_STATUS.items():
            for keyword in keywords:
                if keyword in text.lower():
                    params["status"] = status_code
                    break
        
        # 队列筛选
        queue_match = re.search(r'队列[\s]+([\w]+)', text)
        if queue_match:
            params["queue"] = queue_match.group(1)
        
        # 作业名筛选
        name_match = re.search(r'名称[\s]*["\']?([^"\']+)["\']?', text)
        if name_match:
            params["job_name"] = name_match.group(1)
        
        # 最近N天
        days_match = re.search(r'最近[\s]*(\d+)[\s]*天', text)
        if days_match:
            params["days"] = int(days_match.group(1))
        
        return params


# ============ 处理函数 ============

# 从配置文件导入超时时间
TIMEOUT_QUICK = AppTimeout.QUICK
TIMEOUT_NORMAL = AppTimeout.NORMAL
TIMEOUT_COMPLEX = AppTimeout.COMPLEX
TIMEOUT_TRANSFER = AppTimeout.TRANSFER

def run_subprocess(cmd: List[str], timeout: int = None, capture: bool = True) -> str:
    """运行子进程命令"""
    import subprocess
    # 默认使用普通超时
    if timeout is None:
        timeout = TIMEOUT_NORMAL
        
    try:
        if capture:
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                encoding='utf-8', errors='replace',
                timeout=timeout
            )
            output = result.stdout or ""
            if result.stderr and result.returncode != 0:
                output += f"\n{result.stderr}" if output else result.stderr
            if not output:
                output = "执行完成"
            return output
        else:
            subprocess.run(cmd, timeout=timeout)
            return ""
    except subprocess.TimeoutExpired:
        return f"执行超时（超过 {timeout} 秒）"
    except Exception as e:
        return f"执行错误: {e}"


def check_config_exists() -> bool:
    """检查配置文件是否存在"""
    from config import CONFIG_PATH
    return CONFIG_PATH.exists()


def check_cache_exists() -> bool:
    """检查缓存文件是否存在"""
    from config import CACHE_PATH
    return CACHE_PATH.exists()


def ensure_cache_initialized() -> Tuple[bool, str]:
    """
    确保缓存已初始化
    
    Returns:
        (success, message) - success 为 True 表示缓存可用，False 表示需要用户手动初始化
    """
    # 1. 检查配置文件
    if not check_config_exists():
        config_path = CONFIG_PATH
        msg = f"""
{Colors.RED}✗ 配置文件不存在: {config_path}{Colors.END}

请创建配置文件，步骤如下：

1. 登录 SCNet 平台获取 Access Key 和 Secret Key:
   https://www.scnet.cn/ui/console/index.html#/personal/auth-manage

2. 创建配置文件:
   {Colors.CYAN}cat > {config_path} << 'EOF'
# SCNet Chat 配置文件
SCNET_LOGIN_URL=https://api.scnet.cn
SCNET_AC_URL=https://www.scnet.cn
SCNET_ACCESS_KEY=your_access_key_here
SCNET_SECRET_KEY=your_secret_key_here
SCNET_USER=your_username_here
SCNET_LOG_ENABLED=0
EOF{Colors.END}

3. 设置权限:
   {Colors.CYAN}chmod 600 {config_path}{Colors.END}

4. 初始化缓存:
   {Colors.CYAN}python {SCRIPTS_DIR}/cache.py{Colors.END}
"""
        return False, msg
    
    # 2. 检查缓存文件
    if not check_cache_exists():
        msg = f"""
{Colors.YELLOW}⚠ 缓存文件不存在{Colors.END}

正在自动初始化缓存...
"""
        return False, msg
    
    return True, ""


def handle_cache_refresh(params=None) -> str:
    """处理缓存刷新"""
    params = params or {}
    raw_text = params.get("raw", "")
    
    # 检查是否包含"全部"或"所有"关键词
    refresh_all = any(k in raw_text.lower() for k in ["全部", "所有", "all", "完整"])
    
    try:
        # 使用 CacheInitializer 来初始化缓存
        initializer = CacheInitializer(only_default=not refresh_all)
        success = initializer.run()
        if success:
            if refresh_all:
                return "✓ 所有计算中心缓存刷新成功"
            return "✓ 默认计算中心缓存刷新成功\n  (使用 \"刷新全部缓存\" 可刷新所有计算中心)"
        return "缓存刷新失败"
    except FileNotFoundError as e:
        return f"错误：{e}"
    except ValueError as e:
        return f"配置错误：{e}"
    except Exception as e:
        return f"错误：{e}"


def handle_switch_cluster(cluster_name: str) -> str:
    """处理切换数据中心"""
    if not cluster_name:
        return "错误：未指定计算中心"
    
    try:
        success = switch_default_cluster(cluster_name)
        if success:
            # 切换成功后，显示当前计算中心的账户信息
            result_msg = f"✓ 已切换到 {cluster_name}\n"
            user_info = handle_user_info()
            return result_msg + "\n" + user_info
        return f"切换失败"
    except Exception as e:
        return f"错误：{e}"


def handle_user_info() -> str:
    """处理用户信息查询"""
    return run_subprocess([sys.executable, str(SCRIPTS_DIR / "user.py")], timeout=TIMEOUT_QUICK)


def handle_job_stats(params: Dict[str, Any]) -> str:
    """处理作业统计信息查询"""
    return run_subprocess([sys.executable, str(SCRIPTS_DIR / "user.py"), "--stats"], timeout=TIMEOUT_NORMAL)


def handle_walltime(params: Dict[str, Any]) -> str:
    """处理机时查询"""
    return run_subprocess([sys.executable, str(SCRIPTS_DIR / "user.py"), "--walltime"], timeout=TIMEOUT_QUICK)


def handle_job_list(params: Dict[str, Any]) -> str:
    """处理实时作业查询"""
    cmd = [sys.executable, str(SCRIPTS_DIR / "job.py")]
    
    # 添加筛选参数
    if params.get("status"):
        cmd.extend(["--status", params["status"]])
    if params.get("queue"):
        cmd.extend(["--queue", params["queue"]])
    if params.get("job_name"):
        cmd.extend(["--job-name", params["job_name"]])
    
    return run_subprocess(cmd, timeout=TIMEOUT_NORMAL)


def handle_job_history(params: Dict[str, Any]) -> str:
    """处理历史作业查询"""
    cmd = [sys.executable, str(SCRIPTS_DIR / "job.py"), "--history"]
    
    # 添加筛选参数
    if params.get("status"):
        cmd.extend(["--status", params["status"]])
    if params.get("queue"):
        cmd.extend(["--queue", params["queue"]])
    if params.get("job_name"):
        cmd.extend(["--job-name", params["job_name"]])
    if params.get("days"):
        cmd.extend(["--days", str(params["days"])])
    
    return run_subprocess(cmd, timeout=TIMEOUT_NORMAL)


def handle_job_detail(params: Dict[str, Any]) -> str:
    """处理作业详情查询"""
    job_id = params.get("job_id")
    if not job_id:
        return "错误：请指定作业ID，例如：查询作业详情 123"
    
    cmd = [sys.executable, str(SCRIPTS_DIR / "job.py"), "--job-id", job_id]
    return run_subprocess(cmd, timeout=TIMEOUT_NORMAL)


def handle_job_submit(params: Dict[str, Any]) -> str:
    """处理作业提交"""
    # 检查是否提供了命令
    if not params.get("cmd"):
        return handle_job_submit_help()
    
    # 如果指定了计算中心，先切换
    cluster_name = params.get("cluster_name")
    if cluster_name:
        result = handle_switch_cluster(cluster_name)
        # 切换失败时返回错误
        if "错误" in result or "失败" in result:
            return result
    
    # 如果没有指定队列，从缓存获取默认队列
    if not params.get("queue"):
        try:
            import json
            with open(CACHE_PATH, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            clusters = cache.get('clusters', [])
            default_cluster = None
            for cluster in clusters:
                if cluster.get('default'):
                    default_cluster = cluster
                    break
            if default_cluster:
                job_managers = default_cluster.get('JobManagers', [])
                if job_managers:
                    queues = job_managers[0].get('queues', [])
                    if queues:
                        params['queue'] = queues[0].get('queueName', '')
        except Exception:
            pass
    
    # 检查队列是否为空
    if not params.get("queue"):
        return f"错误：未指定队列，且无法从缓存获取默认队列。\n请使用 --queue 参数指定队列，或先刷新缓存获取可用队列。\n查询可用队列：python scnet.py \"查询队列\""
    
    cmd = [sys.executable, str(SCRIPTS_DIR / "job.py"), "--submit"]
    
    # 添加参数
    if params.get("cmd"):
        cmd.extend(["--cmd", params["cmd"]])
    if params.get("queue"):
        cmd.extend(["--queue", params["queue"]])
    if params.get("work_dir"):
        cmd.extend(["--work-dir", params["work_dir"]])
    if params.get("nnode"):
        cmd.extend(["--nnode", params["nnode"]])
    if params.get("job_name"):
        cmd.extend(["--job-name", params["job_name"]])
    if params.get("wall_time"):
        cmd.extend(["--wall-time", params["wall_time"]])
    
    return run_subprocess(cmd, timeout=TIMEOUT_COMPLEX)


def handle_job_submit_help() -> str:
    """显示作业提交帮助信息"""
    help_text = f"""
{Colors.BOLD}{Colors.CYAN}作业提交帮助{Colors.END}

{Colors.BOLD}基本语法:{Colors.END}
  提交作业 <命令> [--参数 值]...

{Colors.BOLD}常用示例:{Colors.END}
  {Colors.GREEN}提交作业 sleep 900{Colors.END}
    提交一个运行 sleep 900 的作业
  
  {Colors.GREEN}提交作业 --cmd "sleep 100" --queue comp{Colors.END}
    指定队列提交作业
  
  {Colors.GREEN}在山东提交作业 hostname{Colors.END}
    在指定计算中心提交作业
  
  {Colors.GREEN}提交作业 mpirun -np 4 ./myapp --queue normal --nnode 2{Colors.END}
    多节点并行作业

{Colors.BOLD}支持的参数:{Colors.END}

  {Colors.YELLOW}必填参数:{Colors.END}
    cmd          执行的命令（也可直接跟在"提交作业"后）
  
  {Colors.YELLOW}常用可选参数:{Colors.END}
    --queue      队列名称（如 comp, debug, normal）
    --nnode      节点数量（默认 1）
    --work-dir   工作目录（默认 /public/home/<用户名>）
    --job-name   作业名称（默认自动生成）
    --wall-time  最大运行时间（默认 24:00:00，格式 HH:MM:SS）
  
  {Colors.YELLOW}资源参数:{Colors.END}
    --nproc      总核心数
    --ppn        每节点核心数
    --ngpu       GPU卡数/节点
    --ndcu       DCU卡数/节点
    --job-mem    每个节点内存（MB/GB）
    --exclusive  是否独占节点（1=独占）
  
  {Colors.YELLOW}输出参数:{Colors.END}
    --std-out    标准输出文件路径
    --std-err    标准错误文件路径

{Colors.BOLD}提交前准备:{Colors.END}
  1. 确保已在正确的计算中心（使用"切换到<中心名>"）
  2. 查询可用队列（使用"查询队列"）
  3. 确认工作目录存在且有权限

{Colors.BOLD}相关命令:{Colors.END}
  {Colors.CYAN}查询队列{Colors.END}     查看可用队列
  {Colors.CYAN}查询作业{Colors.END}     查看已提交作业状态
  {Colors.CYAN}删除作业 <ID>{Colors.END} 取消或删除作业
"""
    return help_text


def handle_job_delete(params: Dict[str, Any]) -> str:
    """处理作业删除"""
    job_id = params.get("job_id")
    if not job_id:
        return "错误：请指定作业ID，例如：删除作业 123"
    
    cmd = [sys.executable, str(SCRIPTS_DIR / "job.py"), "--delete", "--job-id", job_id]
    return run_subprocess(cmd, timeout=TIMEOUT_COMPLEX)


def handle_job_queues() -> str:
    """处理队列查询"""
    cmd = [sys.executable, str(SCRIPTS_DIR / "job.py"), "--queues"]
    return run_subprocess(cmd, timeout=TIMEOUT_NORMAL)


def handle_cluster_info() -> str:
    """处理集群信息查询"""
    cmd = [sys.executable, str(SCRIPTS_DIR / "job.py"), "--cluster-info"]
    return run_subprocess(cmd, timeout=TIMEOUT_QUICK)


def handle_file_list(params: Dict[str, Any]) -> str:
    """处理文件列表查询"""
    cmd = [sys.executable, str(SCRIPTS_DIR / "file.py"), "--list"]
    
    path = params.get("path")
    if path:
        cmd.append(path)
    
    return run_subprocess(cmd, timeout=TIMEOUT_QUICK)


def handle_file_upload(params: Dict[str, Any]) -> str:
    """处理文件上传"""
    local_path = params.get("local_path")
    remote_path = params.get("remote_path")
    
    if local_path and remote_path:
        cmd = [sys.executable, str(SCRIPTS_DIR / "file.py"), "--upload", local_path, remote_path]
        return run_subprocess(cmd, timeout=TIMEOUT_TRANSFER)
    else:
        return "请指定本地文件路径和远程目标路径\n用法: 上传文件 <本地文件> <远程目录>\n或: python scripts/file.py --upload <本地文件> <远程目录>"


def handle_file_download(params: Dict[str, Any]) -> str:
    """处理文件下载"""
    remote_path = params.get("remote_path")
    local_path = params.get("local_path")
    
    if remote_path and local_path:
        cmd = [sys.executable, str(SCRIPTS_DIR / "file.py"), "--download", remote_path, local_path]
        return run_subprocess(cmd, timeout=TIMEOUT_TRANSFER)
    else:
        return "请指定远程文件路径和本地目标路径\n用法: 下载文件 <远程文件> <本地目录>\n或: python scripts/file.py --download <远程文件> <本地目录>"


def handle_file_mkdir(params: Dict[str, Any]) -> str:
    """处理创建目录"""
    path = params.get("path")
    if not path:
        return "错误：请指定目录路径"
    
    cmd = [sys.executable, str(SCRIPTS_DIR / "file.py"), "--mkdir", path]
    return run_subprocess(cmd, timeout=TIMEOUT_NORMAL)


def handle_file_touch(params: Dict[str, Any]) -> str:
    """处理创建空文件"""
    path = params.get("path")
    if not path:
        return "错误：请指定文件路径"
    
    cmd = [sys.executable, str(SCRIPTS_DIR / "file.py"), "--touch", path]
    return run_subprocess(cmd, timeout=TIMEOUT_NORMAL)


def handle_file_delete(params: Dict[str, Any]) -> str:
    """处理删除文件"""
    path = params.get("path")
    if not path:
        return "错误：请指定文件路径"
    
    cmd = [sys.executable, str(SCRIPTS_DIR / "file.py"), "--delete", path]
    return run_subprocess(cmd, timeout=TIMEOUT_NORMAL)


def handle_file_rename(params: Dict[str, Any]) -> str:
    """处理重命名文件"""
    old_path = params.get("old_path")
    new_name = params.get("new_name")
    
    if not old_path or not new_name:
        return "错误：请指定原文件路径和新名称\n用法: 重命名 <原路径> 为 <新名称>"
    
    cmd = [sys.executable, str(SCRIPTS_DIR / "file.py"), "--rename", old_path, new_name]
    return run_subprocess(cmd, timeout=TIMEOUT_NORMAL)


def handle_file_copy(params: Dict[str, Any]) -> str:
    """处理复制文件"""
    src = params.get("src")
    dst = params.get("dst")
    
    if not src or not dst:
        return "错误：请指定源文件和目标路径\n用法: 复制文件 <源文件> 到 <目标目录>"
    
    cmd = [sys.executable, str(SCRIPTS_DIR / "file.py"), "--copy", src, dst]
    return run_subprocess(cmd, timeout=TIMEOUT_NORMAL)


def handle_file_move(params: Dict[str, Any]) -> str:
    """处理移动文件"""
    src = params.get("src")
    dst = params.get("dst")
    
    if not src or not dst:
        return "错误：请指定源文件和目标路径\n用法: 移动文件 <源文件> 到 <目标目录>"
    
    cmd = [sys.executable, str(SCRIPTS_DIR / "file.py"), "--move", src, dst]
    return run_subprocess(cmd, timeout=TIMEOUT_NORMAL)


def handle_file_exists(params: Dict[str, Any]) -> str:
    """处理检查文件存在"""
    path = params.get("path")
    if not path:
        return "错误：请指定文件路径"
    
    cmd = [sys.executable, str(SCRIPTS_DIR / "file.py"), "--exists", path]
    return run_subprocess(cmd, timeout=TIMEOUT_QUICK)


def print_help():
    """打印帮助信息"""
    help_text = f"""
{Colors.BOLD}{Colors.CYAN}SCNet Skill - 自然语言命令帮助{Colors.END}

{Colors.BOLD}1. 缓存管理{Colors.END}
   • 刷新缓存 / 初始化缓存

{Colors.BOLD}2. 数据中心切换{Colors.END}
   • 切换到 [计算中心]
     可选: 昆山、山东、西安、四川、武汉、哈尔滨、分区一、分区二等

{Colors.BOLD}3. 用户信息查询{Colors.END}
   • 查询用户 / 账户信息 / 我的信息
   • 作业统计 / 统计信息 - 查询实时作业统计
   • 机时 / 剩余机时 / 已用机时 - 查询机时使用情况

{Colors.BOLD}4. 作业管理{Colors.END}
   • 查询作业 / 实时作业列表
   • 历史作业 / 查询历史作业
   • 提交作业 / 提交新任务 [--cmd "命令" --queue 队列名]
   • 删除作业 [作业ID] / 取消作业 [作业ID]
   • 作业详情 [作业ID]
   • 查询队列 / 可用队列
   • 集群信息 / 调度器信息

{Colors.BOLD}5. 文件管理{Colors.END}
   • 文件列表 [路径] / 查看文件 [路径]
   • 上传文件 <本地文件> 到 <远程目录>
   • 下载文件 <远程文件> 到 <本地目录>
   • 创建目录 <路径>
   • 创建文件 <路径>
   • 删除文件 <路径>
   • 重命名 <原路径> 为 <新名称>
   • 复制文件 <源文件> 到 <目标目录>
   • 移动文件 <源文件> 到 <目标目录>

{Colors.BOLD}使用示例:{Colors.END}
   python scnet.py "查询作业"
   python scnet.py "提交作业 --cmd 'sleep 100' --queue debug"
   python scnet.py "删除作业 123"
   python scnet.py "查看文件列表 /public/home/user"
"""
    print(help_text)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='SCNet Skill - 自然语言交互管理 SCNet 超算平台',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python scnet.py "查询作业"
  python scnet.py "提交作业 --cmd 'sleep 100' --queue debug"
  python scnet.py "删除作业 123"
  python scnet.py "查看文件列表 /public/home/user"
  python scnet.py "上传文件 ./test.txt 到 /public/home/user/"

注意: 如果命令包含以 -- 开头的参数，需要用引号包裹整个命令
        """
    )
    parser.add_argument('text', nargs='?', help='自然语言命令')
    # 捕获所有剩余参数（处理 --work-dir 等参数）
    parser.add_argument('remainder', nargs=argparse.REMAINDER, help=argparse.SUPPRESS)
    args = parser.parse_args()
    
    # 合并 text 和 remainder（处理 -- 开头的参数）
    if args.text:
        text = args.text
        if args.remainder:
            # 去掉 remainder 中的 '--' 标记，合并参数
            remainder = ' '.join(args.remainder)
            text = text + ' ' + remainder
    else:
        print("SCNet Skill | 输入自然语言命令，或 'quit' 退出，'help' 查看帮助")
        text = input("\n> ").strip()
        if text.lower() in ["quit", "exit", "q"]:
            return
        if text.lower() in ["help", "帮助", "?"]:
            print_help()
            return
    
    # 识别意图
    recognizer = IntentRecognizer()
    intent, params = recognizer.recognize(text)
    
    # 路由到对应处理函数
    handlers = {
        "cache_refresh": handle_cache_refresh,
        "switch_cluster": lambda p: handle_switch_cluster(p.get("cluster_name", "")),
        "user_info": lambda p: handle_user_info(),
        "job_stats": handle_job_stats,
        "walltime": handle_walltime,
        "job_list": handle_job_list,
        "job_history": handle_job_history,
        "job_detail": handle_job_detail,
        "job_submit": handle_job_submit,
        "job_submit_help": lambda p: handle_job_submit_help(),
        "job_delete": handle_job_delete,
        "job_queues": lambda p: handle_job_queues(),
        "cluster_info": lambda p: handle_cluster_info(),
        "file_list": handle_file_list,
        "file_upload": handle_file_upload,
        "file_download": handle_file_download,
        "file_mkdir": handle_file_mkdir,
        "file_touch": handle_file_touch,
        "file_delete": handle_file_delete,
        "file_rename": handle_file_rename,
        "file_copy": handle_file_copy,
        "file_move": handle_file_move,
        "file_exists": handle_file_exists,
        "help": lambda p: print_help(),
    }
    
    # 对于需要缓存的命令，先检查配置和缓存
    intents_requiring_cache = [
        "user_info", "job_list", "job_history", "job_detail", 
        "job_submit", "job_delete", "job_queues", "cluster_info",
        "file_list", "file_upload", "file_download", "file_mkdir",
        "file_touch", "file_delete", "file_rename", "file_copy", "file_move"
    ]
    
    if intent in intents_requiring_cache:
        cache_ok, msg = ensure_cache_initialized()
        if not cache_ok:
            print(msg)
            # 如果是缓存不存在但配置存在，尝试自动初始化
            if check_config_exists() and not check_cache_exists():
                result = handle_cache_refresh()
                print(result)
            return
    
    if intent in handlers:
        result = handlers[intent](params)
        if result:
            print(result)
        else:
            print(f"{Colors.YELLOW}命令执行完成，但没有输出结果{Colors.END}")
    else:
        print(f"{Colors.YELLOW}未能理解的命令: {text}{Colors.END}")
        print()
        print_help()


if __name__ == "__main__":
    main()
