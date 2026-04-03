#!/usr/bin/env python3
"""
SCNet 文件管理工具

支持文件列表查询、创建文件夹、创建文件、上传下载、删除、复制/移动、重命名等操作。

使用方法:
    python scripts/file.py --list [路径]              # 列出文件
    python scripts/file.py --mkdir <路径>            # 创建文件夹
    python scripts/file.py --touch <路径>            # 创建空文件
    python scripts/file.py --upload <本地> <远程>    # 上传文件
    python scripts/file.py --download <远程> <本地>  # 下载文件
    python scripts/file.py --delete <路径>           # 删除文件/文件夹
    python scripts/file.py --rename <路径> <新名称>  # 重命名
    python scripts/file.py --copy <源> <目标>        # 复制文件
    python scripts/file.py --move <源> <目标>        # 移动文件
    python scripts/file.py --exists <路径>           # 检查文件是否存在
"""

import json
import sys
import ssl
import time
import urllib.request
import urllib.error
import urllib.parse
import argparse
import os
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# Windows 终端兼容处理
import compat

# 导入配置文件
from config import (
    CONFIG_PATH, CACHE_PATH, get_cache_path, CACHE_MAX_AGE,
    FileTimeout, CACHE_INITIALIZER_TIMEOUT
)

# 从 utils 导入通用功能
from utils import Colors, print_header, print_section, print_item, print_success, print_warning, print_error, load_cache

# SSL 上下文
SSL_CONTEXT = ssl.create_default_context()


def _unused_load_cache(auto_init: bool = True) -> Optional[Dict[str, Any]]:
    """
    加载缓存文件
    
    Args:
        auto_init: 缓存不存在或过期时是否自动初始化
    
    Returns:
        缓存数据，如果加载失败则返回 None
    """
    cache_path = get_cache_path()
    # 检查缓存文件是否存在
    if not cache_path.exists():
        print_warning(f"缓存文件不存在: {cache_path}")
        
        if auto_init:
            print(f"{Colors.CYAN}正在自动初始化缓存...{Colors.END}")
            if _refresh_cache():
                # 重新加载缓存
                try:
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except Exception as e:
                    print_error(f"加载新缓存失败: {e}")
                    return None
            else:
                print_error("自动初始化缓存失败")
                return None
        else:
            print(f"\n请先运行缓存初始化命令:")
            print(f"  python scripts/cache.py")
            return None
    
    # 加载缓存文件
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            cache = json.load(f)
    except json.JSONDecodeError as e:
        print_error(f"缓存文件解析失败: {e}")
        if auto_init:
            print(f"{Colors.CYAN}正在自动刷新缓存...{Colors.END}")
            if _refresh_cache():
                # 重新加载缓存
                try:
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except Exception as e2:
                    print_error(f"加载新缓存失败: {e2}")
                    return None
            else:
                print_error("自动刷新缓存失败")
                return None
        return None
    except Exception as e:
        print_error(f"读取缓存文件失败: {e}")
        if auto_init:
            print(f"{Colors.CYAN}正在自动刷新缓存...{Colors.END}")
            if _refresh_cache():
                # 重新加载缓存
                try:
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except Exception as e2:
                    print_error(f"加载新缓存失败: {e2}")
                    return None
            else:
                print_error("自动刷新缓存失败")
                return None
        return None
    
    # 检查缓存是否过期（token 有效期通常为 12 小时）
    meta = cache.get('_meta', {})
    updated_at = meta.get('updated_at', 0)
    current_time = int(time.time())
    
    if current_time - updated_at > CACHE_MAX_AGE:
        print_warning(f"缓存已过期（上次更新: {datetime.fromtimestamp(updated_at).strftime('%Y-%m-%d %H:%M:%S')}）")
        
        if auto_init:
            print(f"{Colors.CYAN}正在自动刷新缓存...{Colors.END}")
            if _refresh_cache():
                # 重新加载缓存
                try:
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except Exception as e:
                    print_error(f"加载新缓存失败: {e}")
                    return None
            else:
                print_warning("自动刷新缓存失败，尝试使用现有缓存")
                # 即使刷新失败，也返回现有缓存（可能还能用）
                return cache
        else:
            print(f"\n请手动刷新缓存:")
            print(f"  python scripts/cache.py")
            # 返回过期缓存（可能还能用）
            return cache
    
    return cache


def _refresh_cache() -> bool:
    """
    调用 cache.py 刷新缓存
    
    Returns:
        True 表示刷新成功，False 表示刷新失败
    """
    try:
        # 获取 scripts 目录路径
        scripts_dir = Path(__file__).parent
        cache_script = scripts_dir / "cache.py"
        
        if not cache_script.exists():
            print_error(f"缓存脚本不存在: {cache_script}")
            return False
        
        # 运行缓存初始化脚本
        # 超时设置为子查询超时总和
        result = subprocess.run(
            [sys.executable, str(cache_script)],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=CACHE_INITIALIZER_TIMEOUT
        )
        
        if result.returncode == 0:
            print_success("缓存刷新成功")
            return True
        else:
            print_error(f"缓存刷新失败: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print_error("缓存刷新超时（超过 2 分钟）")
        return False
    except Exception as e:
        print_error(f"缓存刷新异常: {e}")
        return False


def get_default_cluster(cache: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """获取默认区域"""
    clusters = cache.get('clusters', [])
    for cluster in clusters:
        if cluster.get('default') is True:
            return cluster
    for cluster in clusters:
        if cluster.get('clusterName') != 'ac':
            return cluster
    return None


def get_efile_url(cluster: Dict[str, Any]) -> Optional[str]:
    """从集群信息中获取可用的 efileUrl（文件服务地址）"""
    efile_urls = cluster.get('efileUrls', [])
    for url_info in efile_urls:
        if str(url_info.get('enable', '')).lower() == 'true':
            url = url_info.get('url', '')
            # 确保 URL 以 /efile 结尾
            if url and not url.endswith('/efile'):
                url = url.rstrip('/') + '/efile'
            return url
    return None


def get_home_path(cluster: Dict[str, Any]) -> Optional[str]:
    """获取用户家目录路径"""
    user_info = cluster.get('clusterUserInfo', {})
    return user_info.get('homePath')


class FileAPI:
    """文件管理 API 客户端"""
    
    # 从配置文件导入超时时间
    TIMEOUT_LIST_FILES = FileTimeout.LIST_FILES
    TIMEOUT_CHECK_EXISTS = FileTimeout.CHECK_EXISTS
    TIMEOUT_CREATE_FOLDER = FileTimeout.CREATE_FOLDER
    TIMEOUT_CREATE_FILE = FileTimeout.CREATE_FILE
    TIMEOUT_UPLOAD_FILE = FileTimeout.UPLOAD_FILE
    TIMEOUT_DOWNLOAD_FILE = FileTimeout.DOWNLOAD_FILE
    TIMEOUT_DELETE_FILE = FileTimeout.DELETE_FILE
    TIMEOUT_RENAME_FILE = FileTimeout.RENAME_FILE
    TIMEOUT_COPY_FILE = FileTimeout.COPY_FILE
    TIMEOUT_MOVE_FILE = FileTimeout.MOVE_FILE
    
    # 兼容性保留
    TIMEOUT_QUICK = FileTimeout.QUICK
    TIMEOUT_NORMAL = FileTimeout.NORMAL
    TIMEOUT_TRANSFER = FileTimeout.TRANSFER
    
    def __init__(self, cluster: Dict[str, Any]):
        self.cluster = cluster
        self.token = cluster.get('token', '')
        self.efile_url = get_efile_url(cluster)
        self.home_path = get_home_path(cluster)
        self.cluster_name = cluster.get('clusterName', '')
    
    def _make_request(self, url: str, headers: Dict[str, str], 
                      data: Optional[bytes] = None, 
                      params: Optional[Dict] = None,
                      method: str = 'GET',
                      timeout: int = None) -> Optional[Dict[str, Any]]:
        """发起 HTTP 请求"""
        # 默认使用普通超时
        if timeout is None:
            timeout = self.TIMEOUT_NORMAL
            
        try:
            # 构建完整 URL（包含查询参数）
            if params:
                query_string = urllib.parse.urlencode(params)
                url = f"{url}?{query_string}"
            
            req = urllib.request.Request(
                url,
                data=data,
                headers=headers,
                method=method
            )
            
            with urllib.request.urlopen(req, context=SSL_CONTEXT, timeout=timeout) as response:
                response_body = response.read().decode('utf-8')
                return json.loads(response_body)
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            try:
                return json.loads(error_body)
            except:
                return {"code": str(e.code), "msg": error_body}
        except Exception as e:
            return {"code": "-1", "msg": str(e)}
    
    def list_files(self, path: Optional[str] = None, limit: int = 100, start: int = 0) -> Tuple[Optional[List[Dict]], int, str]:
        """
        查询文件列表
        GET /efile/openapi/v2/file/list
        
        Returns: (file_list, total_count, error_message)
        """
        if not self.efile_url:
            return None, 0, "文件服务不可用"
        
        url = f"{self.efile_url}/openapi/v2/file/list"
        headers = {"token": self.token, "Content-Type": "application/json"}
        params = {"limit": limit, "start": start, "order": "asc", "orderBy": "name"}
        if path:
            params["path"] = path
        
        result = self._make_request(url, headers, params=params, timeout=self.TIMEOUT_LIST_FILES)
        
        if result and result.get("code") == "0":
            data = result.get("data", {})
            return data.get("fileList", []), data.get("total", 0), ""
        else:
            return None, 0, result.get("msg", "查询失败")
    
    def check_exists(self, path: str) -> Tuple[bool, str]:
        """
        检查文件/文件夹是否存在
        POST /efile/openapi/v2/file/exist
        
        Returns: (exists, error_message)
        """
        if not self.efile_url:
            return False, "文件服务不可用"
        
        url = f"{self.efile_url}/openapi/v2/file/exist"
        headers = {"token": self.token, "Content-Type": "application/x-www-form-urlencoded"}
        payload = {"path": path}
        data = urllib.parse.urlencode(payload).encode('utf-8')
        
        result = self._make_request(url, headers, data=data, method='POST', timeout=self.TIMEOUT_CHECK_EXISTS)
        
        if result and result.get("code") == "0":
            return result.get("data", {}).get("exist", False), ""
        else:
            return False, result.get("msg", "检查失败")
    
    def create_folder(self, path: str, create_parents: bool = True) -> Tuple[bool, str]:
        """
        创建文件夹
        POST /efile/openapi/v2/file/mkdir
        
        Returns: (success, message)
        """
        if not self.efile_url:
            return False, "文件服务不可用"
        
        url = f"{self.efile_url}/openapi/v2/file/mkdir"
        headers = {"token": self.token, "Content-Type": "application/json"}
        params = {"path": path, "createParents": str(create_parents).lower()}
        
        result = self._make_request(url, headers, params=params, method='POST', timeout=self.TIMEOUT_CREATE_FOLDER)
        
        if result and result.get("code") == "0":
            return True, "创建成功"
        elif result and result.get("code") == "911021":
            return True, "文件夹已存在"
        else:
            return False, result.get("msg", "创建失败")
    
    def create_file(self, file_path: str) -> Tuple[bool, str]:
        """
        创建空文件
        POST /efile/openapi/v2/file/touch
        
        Returns: (success, message)
        """
        if not self.efile_url:
            return False, "文件服务不可用"
        
        url = f"{self.efile_url}/openapi/v2/file/touch"
        headers = {"token": self.token, "Content-Type": "application/x-www-form-urlencoded"}
        payload = {"fileAbsolutePath": file_path}
        data = urllib.parse.urlencode(payload).encode('utf-8')
        
        result = self._make_request(url, headers, data=data, method='POST', timeout=self.TIMEOUT_CREATE_FILE)
        
        if result and result.get("code") == "0":
            return True, "创建成功"
        elif result and result.get("code") == "911021":
            return True, "文件已存在"
        else:
            return False, result.get("msg", "创建失败")
    
    def upload_file(self, local_path: str, remote_path: str, cover: str = "cover") -> Tuple[bool, str]:
        """
        上传文件（普通上传，适合小文件 < 100MB）
        POST /efile/openapi/v2/file/upload
        
        Returns: (success, message)
        """
        if not self.efile_url:
            return False, "文件服务不可用"
        
        if not os.path.exists(local_path):
            return False, f"本地文件不存在: {local_path}"
        
        url = f"{self.efile_url}/openapi/v2/file/upload"
        
        try:
            import mimetypes
            boundary = '----WebKitFormBoundary' + os.urandom(16).hex()
            
            filename = os.path.basename(local_path)
            mime_type = mimetypes.guess_type(local_path)[0] or 'application/octet-stream'
            
            # 构建 multipart/form-data
            with open(local_path, 'rb') as f:
                file_content = f.read()
            
            body = (
                f'------{boundary}\r\n'
                f'Content-Disposition: form-data; name="path"\r\n\r\n'
                f'{remote_path}\r\n'
                f'------{boundary}\r\n'
                f'Content-Disposition: form-data; name="cover"\r\n\r\n'
                f'{cover}\r\n'
                f'------{boundary}\r\n'
                f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
                f'Content-Type: {mime_type}\r\n\r\n'
            ).encode('utf-8')
            
            body += file_content + f'\r\n------{boundary}--\r\n'.encode('utf-8')
            
            headers = {
                "token": self.token,
                "Content-Type": f"multipart/form-data; boundary=----{boundary}"
            }
            
            req = urllib.request.Request(url, data=body, headers=headers, method='POST')
            
            with urllib.request.urlopen(req, context=SSL_CONTEXT, timeout=self.TIMEOUT_UPLOAD_FILE) as response:
                response_body = response.read().decode('utf-8')
                result = json.loads(response_body)
                
                if result.get("code") == "0":
                    return True, "上传成功"
                else:
                    return False, result.get("msg", "上传失败")
        except Exception as e:
            return False, f"上传失败: {str(e)}"
    
    def download_file(self, remote_path: str, local_path: str) -> Tuple[bool, str]:
        """
        下载文件
        GET /efile/openapi/v2/file/download
        
        Returns: (success, message)
        """
        if not self.efile_url:
            return False, "文件服务不可用"
        
        url = f"{self.efile_url}/openapi/v2/file/download"
        headers = {"token": self.token, "Content-Type": "application/json"}
        params = {"path": remote_path}
        
        try:
            query_string = urllib.parse.urlencode(params)
            full_url = f"{url}?{query_string}"
            
            req = urllib.request.Request(full_url, headers=headers, method='GET')
            
            # 处理目标路径：如果是目录，使用远程文件名
            target_path = local_path
            if os.path.isdir(local_path):
                # 从远程路径提取文件名
                remote_filename = os.path.basename(remote_path)
                target_path = os.path.join(local_path, remote_filename)
            
            # 确保本地目录存在
            os.makedirs(os.path.dirname(target_path) or '.', exist_ok=True)
            
            with urllib.request.urlopen(req, context=SSL_CONTEXT, timeout=self.TIMEOUT_DOWNLOAD_FILE) as response:
                with open(target_path, 'wb') as f:
                    while True:
                        chunk = response.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
                return True, f"下载成功: {target_path}"
        except Exception as e:
            return False, f"下载失败: {str(e)}"
    
    def delete_file(self, path: str, recursive: bool = False) -> Tuple[bool, str]:
        """
        删除文件/文件夹
        POST /efile/openapi/v2/file/remove
        
        Returns: (success, message)
        """
        if not self.efile_url:
            return False, "文件服务不可用"
        
        url = f"{self.efile_url}/openapi/v2/file/remove"
        headers = {"token": self.token, "Content-Type": "application/json"}
        params = {"paths": path, "recursive": str(recursive).lower()}
        
        result = self._make_request(url, headers, params=params, method='POST', timeout=self.TIMEOUT_DELETE_FILE)
        
        if result and result.get("code") == "0":
            return True, "删除成功"
        else:
            return False, result.get("msg", "删除失败")
    
    def rename_file(self, file_path: str, new_name: str) -> Tuple[bool, str]:
        """
        重命名文件
        POST /efile/openapi/v2/file/rename
        
        Returns: (success, message)
        """
        if not self.efile_url:
            return False, "文件服务不可用"
        
        url = f"{self.efile_url}/openapi/v2/file/rename"
        headers = {"token": self.token, "Content-Type": "application/x-www-form-urlencoded"}
        payload = {"fileAbsolutePath": file_path, "newName": new_name}
        data = urllib.parse.urlencode(payload).encode('utf-8')
        
        result = self._make_request(url, headers, data=data, method='POST', timeout=self.TIMEOUT_RENAME_FILE)
        
        if result and result.get("code") == "0":
            return True, "重命名成功"
        else:
            return False, result.get("msg", "重命名失败")
    
    def copy_file(self, source_paths: List[str], target_path: str, cover: str = "cover") -> Tuple[bool, str]:
        """
        复制文件
        POST /efile/openapi/v2/file/copy
        
        Returns: (success, message)
        """
        if not self.efile_url:
            return False, "文件服务不可用"
        
        url = f"{self.efile_url}/openapi/v2/file/copy"
        headers = {"token": self.token, "Content-Type": "application/x-www-form-urlencoded"}
        payload = {
            "sourcePaths": ",".join(source_paths),
            "targetPath": target_path,
            "cover": cover
        }
        data = urllib.parse.urlencode(payload).encode('utf-8')
        
        result = self._make_request(url, headers, data=data, method='POST', timeout=self.TIMEOUT_COPY_FILE)
        
        if result and result.get("code") == "0":
            return True, "复制成功"
        else:
            return False, result.get("msg", "复制失败")
    
    def move_file(self, source_paths: List[str], target_path: str, cover: str = "cover") -> Tuple[bool, str]:
        """
        移动文件
        POST /efile/openapi/v2/file/move
        
        Returns: (success, message)
        """
        if not self.efile_url:
            return False, "文件服务不可用"
        
        url = f"{self.efile_url}/openapi/v2/file/move"
        headers = {"token": self.token, "Content-Type": "application/x-www-form-urlencoded"}
        payload = {
            "sourcePaths": ",".join(source_paths),
            "targetPath": target_path,
            "cover": cover
        }
        data = urllib.parse.urlencode(payload).encode('utf-8')
        
        result = self._make_request(url, headers, data=data, method='POST', timeout=self.TIMEOUT_MOVE_FILE)
        
        if result and result.get("code") == "0":
            return True, "移动成功"
        else:
            return False, result.get("msg", "移动失败")


def format_file_size(size: int) -> str:
    """格式化文件大小"""
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.1f} GB"


def format_time(timestamp: int) -> str:
    """格式化时间戳"""
    from datetime import datetime
    try:
        return datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')
    except:
        return "未知"


def display_file_list(files: List[Dict], total: int, path: str):
    """显示文件列表"""
    if not files:
        print_warning(f"目录为空: {path}")
        return
    
    print_section(f"📁 文件列表: {path or '家目录'} (共 {total} 项)")
    
    # 分离文件夹和文件
    dirs = [f for f in files if f.get('isDirectory')]
    files_only = [f for f in files if not f.get('isDirectory')]
    
    # 显示文件夹
    for item in sorted(dirs, key=lambda x: x.get('name', '')):
        name = item.get('name', '未知')
        mtime = format_time(item.get('mtime', 0))
        print(f"  {Colors.CYAN}📁 {name}/{Colors.END} {Colors.DIM}(修改: {mtime}){Colors.END}")
    
    # 显示文件
    for item in sorted(files_only, key=lambda x: x.get('name', '')):
        name = item.get('name', '未知')
        size = format_file_size(item.get('size', 0))
        mtime = format_time(item.get('mtime', 0))
        print(f"  📄 {name} {Colors.GREEN}{size}{Colors.END} {Colors.DIM}(修改: {mtime}){Colors.END}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='SCNet 文件管理工具 - 管理远程文件',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python scripts/file.py --list                          # 列出家目录文件
  python scripts/file.py --list /public/home/user        # 列出指定目录
  python scripts/file.py --mkdir /public/home/user/test  # 创建文件夹
  python scripts/file.py --touch /public/home/user/a.txt # 创建空文件
  python scripts/file.py --upload ./local.txt /remote/   # 上传文件
  python scripts/file.py --download /remote/file.txt ./  # 下载文件
  python scripts/file.py --delete /remote/file.txt       # 删除文件
  python scripts/file.py --rename /old.txt new.txt       # 重命名
  python scripts/file.py --copy /src.txt /dst/           # 复制文件
  python scripts/file.py --move /src.txt /dst/           # 移动文件
  python scripts/file.py --exists /remote/file.txt       # 检查文件是否存在
        """
    )
    
    # 操作类型
    parser.add_argument('--list', action='store_true', help='列出文件列表')
    parser.add_argument('--mkdir', action='store_true', help='创建文件夹')
    parser.add_argument('--touch', action='store_true', help='创建空文件')
    parser.add_argument('--upload', action='store_true', help='上传文件')
    parser.add_argument('--download', action='store_true', help='下载文件')
    parser.add_argument('--delete', action='store_true', help='删除文件/文件夹')
    parser.add_argument('--rename', action='store_true', help='重命名文件')
    parser.add_argument('--copy', action='store_true', help='复制文件')
    parser.add_argument('--move', action='store_true', help='移动文件')
    parser.add_argument('--exists', action='store_true', help='检查文件是否存在')
    
    # 路径参数
    parser.add_argument('path', nargs='?', help='文件/目录路径')
    parser.add_argument('dest', nargs='?', help='目标路径（用于 rename/copy/move）')
    
    # 其他参数
    parser.add_argument('--recursive', '-r', action='store_true', help='递归删除目录')
    parser.add_argument('--limit', type=int, default=100, help='列表返回数量限制')
    parser.add_argument('--start', type=int, default=0, help='列表起始位置')
    
    args = parser.parse_args()
    
    # 加载缓存
    cache = load_cache(auto_init=False)
    if not cache:
        sys.exit(1)
    
    # 获取默认区域
    cluster = get_default_cluster(cache)
    if not cluster:
        print_error("未找到默认区域")
        sys.exit(1)
    
    # 创建 API 客户端
    api = FileAPI(cluster)
    
    if not api.efile_url:
        print_error("当前区域未配置文件服务")
        sys.exit(1)
    
    # 打印标题
    print_header(f"文件管理 - {api.cluster_name}")
    print_item("家目录", api.home_path or "未知")
    print_item("当前路径", args.path or api.home_path or "/")
    
    # 处理各种操作
    if args.list:
        path = args.path or api.home_path
        files, total, error = api.list_files(path, limit=args.limit, start=args.start)
        if error:
            print_error(f"查询失败: {error}")
            sys.exit(1)
        display_file_list(files, total, path)
    
    elif args.mkdir:
        if not args.path:
            print_error("请指定要创建的目录路径")
            sys.exit(1)
        success, message = api.create_folder(args.path)
        if success:
            print_success(message)
        else:
            print_error(message)
            sys.exit(1)
    
    elif args.touch:
        if not args.path:
            print_error("请指定要创建的文件路径")
            sys.exit(1)
        success, message = api.create_file(args.path)
        if success:
            print_success(message)
        else:
            print_error(message)
            sys.exit(1)
    
    elif args.upload:
        if not args.path or not args.dest:
            print_error("请指定本地文件路径和远程目标路径")
            print("用法: --upload <本地文件> <远程目录>")
            sys.exit(1)
        success, message = api.upload_file(args.path, args.dest)
        if success:
            print_success(message)
        else:
            print_error(message)
            sys.exit(1)
    
    elif args.download:
        if not args.path or not args.dest:
            print_error("请指定远程文件路径和本地目标路径")
            print("用法: --download <远程文件> <本地目录>")
            sys.exit(1)
        success, message = api.download_file(args.path, args.dest)
        if success:
            print_success(message)
        else:
            print_error(message)
            sys.exit(1)
    
    elif args.delete:
        if not args.path:
            print_error("请指定要删除的文件/目录路径")
            sys.exit(1)
        
        # 执行删除
        success, message = api.delete_file(args.path, recursive=args.recursive)
        if success:
            print_success(message)
        else:
            print_error(message)
            sys.exit(1)
    
    elif args.rename:
        if not args.path or not args.dest:
            print_error("请指定原文件路径和新名称")
            print("用法: --rename <文件路径> <新名称>")
            sys.exit(1)
        success, message = api.rename_file(args.path, args.dest)
        if success:
            print_success(message)
        else:
            print_error(message)
            sys.exit(1)
    
    elif args.copy:
        if not args.path or not args.dest:
            print_error("请指定源文件路径和目标路径")
            print("用法: --copy <源文件> <目标目录>")
            sys.exit(1)
        success, message = api.copy_file([args.path], args.dest)
        if success:
            print_success(message)
        else:
            print_error(message)
            sys.exit(1)
    
    elif args.move:
        if not args.path or not args.dest:
            print_error("请指定源文件路径和目标路径")
            print("用法: --move <源文件> <目标目录>")
            sys.exit(1)
        success, message = api.move_file([args.path], args.dest)
        if success:
            print_success(message)
        else:
            print_error(message)
            sys.exit(1)
    
    elif args.exists:
        if not args.path:
            print_error("请指定要检查的文件路径")
            sys.exit(1)
        exists, error = api.check_exists(args.path)
        if error:
            print_error(f"检查失败: {error}")
            sys.exit(1)
        if exists:
            print_success(f"文件存在: {args.path}")
        else:
            print_warning(f"文件不存在: {args.path}")
    
    else:
        # 默认列出文件
        path = args.path or api.home_path
        files, total, error = api.list_files(path, limit=args.limit, start=args.start)
        if error:
            print_error(f"查询失败: {error}")
            sys.exit(1)
        display_file_list(files, total, path)
    
    # 底部提示
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 70}{Colors.END}")
    print(f"  提示: 使用 {Colors.YELLOW}python scripts/cache.py --switch \"中心名称\"{Colors.END} 切换区域")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 70}{Colors.END}\n")


if __name__ == "__main__":
    main()
