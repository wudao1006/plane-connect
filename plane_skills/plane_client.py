#!/usr/bin/env python3
"""
Plane API Client for Skills System
Lightweight client used by the plane-sync skill runtime.
"""

import json
import os
import requests
import time
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pathlib import Path


class PlaneClient:
    """简化的Plane API客户端，用于Skills系统"""

    def __init__(self, base_url: str, api_key: str, workspace_slug: str, cache_manager=None, cache_dir: str = None):
        """
        初始化Plane客户端

        Args:
            base_url: Plane实例的基础URL
            api_key: Plane API密钥
            workspace_slug: 工作空间标识符
            cache_manager: 缓存管理器实例
            cache_dir: 缓存目录路径（如果没有cache_manager）
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.workspace_slug = workspace_slug
        self.cache_manager = cache_manager

        # 设置请求头
        self.headers = {
            'X-API-Key': api_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        # 缓存设置
        if cache_manager:
            # 使用传入的缓存管理器
            pass
        else:
            # 使用简单的文件缓存
            self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / '.plane_skills_cache'
            self.cache_dir.mkdir(exist_ok=True)
            self.user_cache_file = self.cache_dir / 'user_info.json'
            # 用户信息缓存
            self._user_cache = {}
            self._load_user_cache()

        # 重试配置
        self.max_retries = 3
        self.retry_delay = 1  # 秒

        # 设置日志器
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def _load_user_cache(self):
        """加载用户信息缓存"""
        try:
            if self.user_cache_file.exists():
                with open(self.user_cache_file, 'r', encoding='utf-8') as f:
                    self._user_cache = json.load(f)
                self.logger.debug(f"已加载用户缓存: {len(self._user_cache)} 个用户")
        except Exception as e:
            self.logger.warning(f"加载用户缓存失败: {e}")
            self._user_cache = {}

    def _save_user_cache(self):
        """保存用户信息缓存"""
        try:
            with open(self.user_cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._user_cache, f, ensure_ascii=False, indent=2)
            self.logger.debug(f"已保存用户缓存: {len(self._user_cache)} 个用户")
        except Exception as e:
            self.logger.error(f"保存用户缓存失败: {e}")

    def _make_request(self, endpoint: str, params: Dict = None, method: str = 'GET',
                     data: Dict = None, retry_count: int = 0) -> Dict:
        """
        发送API请求，包含重试机制

        Args:
            endpoint: API端点
            params: 查询参数
            method: HTTP方法
            data: 请求数据
            retry_count: 重试次数

        Returns:
            API响应数据
        """
        url = f"{self.base_url}/api/v1/workspaces/{self.workspace_slug}/{endpoint}"

        try:
            self.logger.debug(f"发送API请求: {method} {url}")
            if params:
                self.logger.debug(f"请求参数: {params}")
            if data:
                self.logger.debug(f"请求数据: {data}")

            # 发送请求
            if method.upper() == 'GET':
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=self.headers, params=params,
                                       json=data, timeout=30)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=self.headers, params=params,
                                      json=data, timeout=30)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=self.headers, params=params, timeout=30)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")

            # 处理响应状态码
            if response.status_code == 200:
                self.logger.debug(f"API请求成功: {url}")
                return response.json()
            elif response.status_code == 201:
                self.logger.debug(f"API创建成功: {url}")
                return response.json()
            elif response.status_code == 204:
                self.logger.debug(f"API删除成功: {url}")
                return {}
            elif response.status_code == 401:
                self.logger.error("API认证失败：请检查API密钥是否正确")
                raise requests.exceptions.HTTPError("API认证失败")
            elif response.status_code == 403:
                self.logger.error("API权限不足：请检查API密钥权限")
                raise requests.exceptions.HTTPError("API权限不足")
            elif response.status_code == 404:
                self.logger.error(f"API端点不存在: {url}")
                raise requests.exceptions.HTTPError("API端点不存在")
            elif response.status_code == 429:
                # API限流，等待后重试
                if retry_count < self.max_retries:
                    wait_time = self.retry_delay * (2 ** retry_count)  # 指数退避
                    self.logger.warning(f"API限流，{wait_time}秒后重试 (第{retry_count + 1}次)")
                    time.sleep(wait_time)
                    return self._make_request(endpoint, params, method, data, retry_count + 1)
                else:
                    self.logger.error("API限流，重试次数已达上限")
                    raise requests.exceptions.HTTPError("API限流")
            else:
                response.raise_for_status()

        except requests.exceptions.Timeout:
            if retry_count < self.max_retries:
                wait_time = self.retry_delay * (retry_count + 1)
                self.logger.warning(f"请求超时，{wait_time}秒后重试 (第{retry_count + 1}次)")
                time.sleep(wait_time)
                return self._make_request(endpoint, params, method, data, retry_count + 1)
            else:
                self.logger.error(f"请求超时，重试次数已达上限: {url}")
                raise

        except requests.exceptions.ConnectionError as e:
            if retry_count < self.max_retries:
                wait_time = self.retry_delay * (retry_count + 1)
                self.logger.warning(f"连接错误，{wait_time}秒后重试 (第{retry_count + 1}次): {e}")
                time.sleep(wait_time)
                return self._make_request(endpoint, params, method, data, retry_count + 1)
            else:
                self.logger.error(f"连接失败，重试次数已达上限: {e}")
                raise

        except requests.exceptions.RequestException as e:
            self.logger.error(f"API请求失败: {e}")
            raise

        return {}

    def get_user_info(self, user_id: str, force_refresh: bool = False) -> Optional[Dict]:
        """
        获取用户信息，支持缓存

        Args:
            user_id: 用户ID
            force_refresh: 是否强制刷新缓存

        Returns:
            用户信息字典
        """
        # 使用cache_manager或简单缓存
        if self.cache_manager:
            if not force_refresh:
                try:
                    from .cache_manager import CacheType
                    cached_user = self.cache_manager.get(CacheType.USER_INFO, user_id)
                    if cached_user:
                        return cached_user
                except:
                    pass
        else:
            # 检查简单缓存
            if not force_refresh and hasattr(self, '_user_cache') and user_id in self._user_cache:
                cache_time = self._user_cache[user_id].get('_cached_at')
                if cache_time:
                    # 缓存1小时
                    cache_age = time.time() - cache_time
                    if cache_age < 3600:
                        self.logger.debug(f"使用缓存的用户信息: {user_id}")
                        return self._user_cache[user_id]

        try:
            # 从API获取用户信息
            user_data = self._make_request(f"members/{user_id}/")
            if user_data:
                # 保存到缓存
                if self.cache_manager:
                    try:
                        from .cache_manager import CacheType
                        self.cache_manager.set(CacheType.USER_INFO, user_id, user_data)
                    except:
                        pass
                else:
                    # 简单缓存
                    if hasattr(self, '_user_cache'):
                        user_data['_cached_at'] = time.time()
                        self._user_cache[user_id] = user_data
                        self._save_user_cache()

                self.logger.debug(f"已缓存用户信息: {user_id}")
                return user_data
        except Exception as e:
            self.logger.error(f"获取用户信息失败 {user_id}: {e}")
            # 如果API失败，尝试返回缓存的数据
            if hasattr(self, '_user_cache') and user_id in self._user_cache:
                self.logger.warning(f"API失败，使用过期缓存: {user_id}")
                return self._user_cache[user_id]

        return None

    def get_current_user(self) -> Optional[Dict]:
        """获取当前用户信息"""
        try:
            return self._make_request("me/")
        except Exception as e:
            self.logger.error(f"获取当前用户信息失败: {e}")
            return None

    def list_projects(self, page_size: int = 100) -> List[Dict]:
        """
        获取项目列表

        Args:
            page_size: 每页项目数量

        Returns:
            项目列表
        """
        try:
            projects = []
            page = 1

            while True:
                params = {
                    'per_page': page_size,
                    'page': page
                }

                response = self._make_request("projects/", params=params)

                if not response or 'results' not in response:
                    break

                page_projects = response['results']
                if not page_projects:
                    break

                projects.extend(page_projects)

                # 检查是否还有更多页面
                if not response.get('next'):
                    break

                page += 1

            self.logger.info(f"获取到 {len(projects)} 个项目")
            return projects

        except Exception as e:
            self.logger.error(f"获取项目列表失败: {e}")
            return []

    def get_project(self, project_id: str) -> Optional[Dict]:
        """
        获取单个项目信息

        Args:
            project_id: 项目ID

        Returns:
            项目信息
        """
        try:
            return self._make_request(f"projects/{project_id}/")
        except Exception as e:
            self.logger.error(f"获取项目信息失败 {project_id}: {e}")
            return None

    def list_project_issues(self, project_id: str, assignee: str = None,
                           state: str = None, page_size: int = 100) -> List[Dict]:
        """
        获取项目的任务列表

        Args:
            project_id: 项目ID
            assignee: 负责人筛选
            state: 状态筛选
            page_size: 每页任务数量

        Returns:
            任务列表
        """
        try:
            issues = []
            page = 1

            while True:
                params = {
                    'per_page': page_size,
                    'page': page,
                    'expand': 'assignees,labels,state,priority'
                }

                if assignee:
                    params['assignees'] = assignee
                if state:
                    params['state'] = state

                response = self._make_request(f"projects/{project_id}/issues/", params=params)

                if not response or 'results' not in response:
                    break

                page_issues = response['results']
                if not page_issues:
                    break

                issues.extend(page_issues)

                # 检查是否还有更多页面
                if not response.get('next'):
                    break

                page += 1

            self.logger.info(f"项目 {project_id} 获取到 {len(issues)} 个任务")
            return issues

        except Exception as e:
            self.logger.error(f"获取项目任务失败 {project_id}: {e}")
            return []

    def get_issue(self, project_id: str, issue_id: str) -> Optional[Dict]:
        """
        获取单个任务信息

        Args:
            project_id: 项目ID
            issue_id: 任务ID

        Returns:
            任务信息
        """
        try:
            params = {'expand': 'assignees,labels,state,priority'}
            return self._make_request(f"projects/{project_id}/issues/{issue_id}/", params=params)
        except Exception as e:
            self.logger.error(f"获取任务信息失败 {project_id}/{issue_id}: {e}")
            return None

    def create_issue(self, project_id: str, issue_data: Dict) -> Optional[Dict]:
        """
        创建新任务

        Args:
            project_id: 项目ID
            issue_data: 任务数据

        Returns:
            创建的任务信息
        """
        try:
            return self._make_request(f"projects/{project_id}/issues/",
                                    method='POST', data=issue_data)
        except Exception as e:
            self.logger.error(f"创建任务失败 {project_id}: {e}")
            return None

    def update_issue(self, project_id: str, issue_id: str, issue_data: Dict) -> Optional[Dict]:
        """
        更新任务

        Args:
            project_id: 项目ID
            issue_id: 任务ID
            issue_data: 更新的任务数据

        Returns:
            更新后的任务信息
        """
        try:
            return self._make_request(f"projects/{project_id}/issues/{issue_id}/",
                                    method='PUT', data=issue_data)
        except Exception as e:
            self.logger.error(f"更新任务失败 {project_id}/{issue_id}: {e}")
            return None

    def list_workspace_members(self) -> List[Dict]:
        """
        获取工作空间成员列表

        Returns:
            成员列表
        """
        try:
            response = self._make_request("members/")
            if isinstance(response, dict):
                return response.get("results", [])
            if isinstance(response, list):
                return response
            return []
        except Exception as e:
            self.logger.error(f"获取工作空间成员失败: {e}")
            return []

    def find_user_by_email_or_name(self, query: str) -> Optional[str]:
        """
        根据邮箱或名称查找用户ID。

        Args:
            query: 邮箱、display_name、username 或 name

        Returns:
            用户ID，未找到返回None
        """
        if not query:
            return None

        q = query.strip().lower()
        members = self.list_workspace_members()
        if not members:
            return None

        # 先做精确匹配
        for member in members:
            if not isinstance(member, dict):
                continue

            candidates = [
                member.get("email", ""),
                member.get("display_name", ""),
                member.get("username", ""),
                member.get("name", ""),
            ]
            if any(str(value).strip().lower() == q for value in candidates if value):
                return member.get("id")

        # 再做包含匹配
        for member in members:
            if not isinstance(member, dict):
                continue

            candidates = [
                member.get("email", ""),
                member.get("display_name", ""),
                member.get("username", ""),
                member.get("name", ""),
            ]
            if any(q in str(value).strip().lower() for value in candidates if value):
                return member.get("id")

        return None

    def search_issues(self, query: str, project_ids: List[str] = None) -> List[Dict]:
        """
        搜索任务

        Args:
            query: 搜索关键词
            project_ids: 限制搜索的项目ID列表

        Returns:
            搜索结果
        """
        try:
            params = {
                'search': query,
                'expand': 'assignees,labels,state,priority'
            }

            if project_ids:
                params['project'] = ','.join(project_ids)

            response = self._make_request("search/issues/", params=params)
            return response.get('results', []) if response else []

        except Exception as e:
            self.logger.error(f"搜索任务失败: {e}")
            return []

    def get_project_states(self, project_id: str) -> List[Dict]:
        """
        获取项目的状态列表

        Args:
            project_id: 项目ID

        Returns:
            状态列表
        """
        try:
            return self._make_request(f"projects/{project_id}/states/")
        except Exception as e:
            self.logger.error(f"获取项目状态失败 {project_id}: {e}")
            return []

    def get_project_labels(self, project_id: str) -> List[Dict]:
        """
        获取项目的标签列表

        Args:
            project_id: 项目ID

        Returns:
            标签列表
        """
        try:
            return self._make_request(f"projects/{project_id}/issue-labels/")
        except Exception as e:
            self.logger.error(f"获取项目标签失败 {project_id}: {e}")
            return []

    def test_connection(self) -> bool:
        """
        测试API连接

        Returns:
            连接是否成功
        """
        try:
            response = self.get_current_user()
            return response is not None
        except Exception as e:
            self.logger.error(f"连接测试失败: {e}")
            return False

    def get_workspace_info(self) -> Optional[Dict]:
        """
        获取工作空间信息

        Returns:
            工作空间信息
        """
        try:
            # 通过获取当前用户信息来验证工作空间
            user_info = self.get_current_user()
            if user_info:
                return {
                    'workspace_slug': self.workspace_slug,
                    'base_url': self.base_url,
                    'user': user_info
                }
        except Exception as e:
            self.logger.error(f"获取工作空间信息失败: {e}")

        return None

    def clear_cache(self):
        """清除所有缓存"""
        try:
            self._user_cache = {}
            if self.user_cache_file.exists():
                self.user_cache_file.unlink()
            self.logger.info("缓存已清除")
        except Exception as e:
            self.logger.error(f"清除缓存失败: {e}")


def create_client_from_env(cache_dir: str = None) -> Optional[PlaneClient]:
    """
    从环境变量创建PlaneClient实例

    Args:
        cache_dir: 缓存目录路径

    Returns:
        PlaneClient实例或None
    """
    base_url = os.getenv('PLANE_BASE_URL')
    api_key = os.getenv('PLANE_API_KEY')
    workspace_slug = os.getenv('PLANE_WORKSPACE_SLUG')

    if not all([base_url, api_key, workspace_slug]):
        logging.error("缺少必要的环境变量: PLANE_BASE_URL, PLANE_API_KEY, PLANE_WORKSPACE_SLUG")
        return None

    return PlaneClient(base_url, api_key, workspace_slug, cache_dir)


if __name__ == "__main__":
    # 测试代码
    import logging
    logging.basicConfig(level=logging.INFO)

    # 从环境变量创建客户端
    client = create_client_from_env()
    if client:
        # 测试连接
        if client.test_connection():
            print("✅ Plane API连接成功")

            # 获取当前用户信息
            user = client.get_current_user()
            if user:
                print(f"当前用户: {user.get('display_name', 'Unknown')}")

            # 获取项目列表
            projects = client.list_projects()
            print(f"项目数量: {len(projects)}")

        else:
            print("❌ Plane API连接失败")
    else:
        print("❌ 无法创建Plane客户端，请检查环境变量")
