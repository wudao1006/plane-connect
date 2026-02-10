#!/usr/bin/env python3
"""
Cache Manager for Plane Skills System
用于管理用户信息和项目元数据的缓存系统
"""

import json
import os
import time
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from enum import Enum
import hashlib


class CacheType(Enum):
    """缓存类型枚举"""
    USER_INFO = "user_info"           # 用户信息 - 永久缓存
    PROJECT_METADATA = "project_meta" # 项目元数据 - 1小时缓存
    PROJECT_ISSUES = "project_issues" # 项目任务 - 30分钟缓存
    WORKSPACE_DATA = "workspace_data" # 工作空间数据 - 2小时缓存


class CacheEntry:
    """缓存条目类"""

    def __init__(self, data: Any, cache_type: CacheType, ttl: Optional[int] = None):
        """
        初始化缓存条目

        Args:
            data: 缓存的数据
            cache_type: 缓存类型
            ttl: 生存时间（秒），None表示永久缓存
        """
        self.data = data
        self.cache_type = cache_type
        self.created_at = time.time()
        self.updated_at = time.time()
        self.access_count = 0
        self.last_accessed = time.time()

        # 设置TTL
        if ttl is not None:
            self.ttl = ttl
        else:
            # 根据缓存类型设置默认TTL
            self.ttl = self._get_default_ttl(cache_type)

    def _get_default_ttl(self, cache_type: CacheType) -> Optional[int]:
        """根据缓存类型获取默认TTL"""
        ttl_map = {
            CacheType.USER_INFO: None,        # 永久缓存
            CacheType.PROJECT_METADATA: 3600, # 1小时
            CacheType.PROJECT_ISSUES: 1800,   # 30分钟
            CacheType.WORKSPACE_DATA: 7200,   # 2小时
        }
        return ttl_map.get(cache_type, 3600)  # 默认1小时

    def is_expired(self) -> bool:
        """检查缓存是否过期"""
        if self.ttl is None:
            return False  # 永久缓存不过期
        return (time.time() - self.updated_at) > self.ttl

    def update_data(self, data: Any):
        """更新缓存数据"""
        self.data = data
        self.updated_at = time.time()

    def access(self) -> Any:
        """访问缓存数据，更新访问统计"""
        self.access_count += 1
        self.last_accessed = time.time()
        return self.data

    def to_dict(self) -> Dict:
        """转换为字典格式用于序列化"""
        return {
            'data': self.data,
            'cache_type': self.cache_type.value,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'access_count': self.access_count,
            'last_accessed': self.last_accessed,
            'ttl': self.ttl
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'CacheEntry':
        """从字典创建缓存条目"""
        cache_type = CacheType(data['cache_type'])
        entry = cls(data['data'], cache_type, data.get('ttl'))
        entry.created_at = data.get('created_at', time.time())
        entry.updated_at = data.get('updated_at', time.time())
        entry.access_count = data.get('access_count', 0)
        entry.last_accessed = data.get('last_accessed', time.time())
        return entry


class CacheManager:
    """缓存管理器"""

    def __init__(self, cache_dir: str = None):
        """
        初始化缓存管理器

        Args:
            cache_dir: 缓存目录路径
        """
        # 设置缓存目录
        self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / '.plane_skills_cache'
        self.cache_dir.mkdir(exist_ok=True)

        # 缓存文件路径
        self.cache_files = {
            CacheType.USER_INFO: self.cache_dir / 'user_info.json',
            CacheType.PROJECT_METADATA: self.cache_dir / 'project_metadata.json',
            CacheType.PROJECT_ISSUES: self.cache_dir / 'project_issues.json',
            CacheType.WORKSPACE_DATA: self.cache_dir / 'workspace_data.json',
        }

        # 内存缓存
        self._memory_cache: Dict[str, CacheEntry] = {}

        # 设置日志器
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # 加载所有缓存
        self._load_all_caches()

    def _generate_cache_key(self, cache_type: CacheType, identifier: str) -> str:
        """生成缓存键"""
        return f"{cache_type.value}:{identifier}"

    def _load_all_caches(self):
        """加载所有缓存文件到内存"""
        for cache_type, cache_file in self.cache_files.items():
            self._load_cache_file(cache_type, cache_file)

    def _load_cache_file(self, cache_type: CacheType, cache_file: Path):
        """加载单个缓存文件"""
        try:
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)

                loaded_count = 0
                for identifier, entry_data in cache_data.items():
                    try:
                        cache_key = self._generate_cache_key(cache_type, identifier)
                        entry = CacheEntry.from_dict(entry_data)

                        # 检查是否过期，过期的不加载到内存
                        if not entry.is_expired():
                            self._memory_cache[cache_key] = entry
                            loaded_count += 1
                        else:
                            self.logger.debug(f"跳过过期缓存: {cache_key}")
                    except Exception as e:
                        self.logger.warning(f"加载缓存条目失败 {identifier}: {e}")

                self.logger.debug(f"已加载 {cache_type.value} 缓存: {loaded_count} 个条目")
        except Exception as e:
            self.logger.warning(f"加载缓存文件失败 {cache_file}: {e}")

    def _save_cache_file(self, cache_type: CacheType):
        """保存指定类型的缓存到文件"""
        try:
            cache_file = self.cache_files[cache_type]
            cache_data = {}

            # 收集该类型的所有缓存条目
            prefix = f"{cache_type.value}:"
            for cache_key, entry in self._memory_cache.items():
                if cache_key.startswith(prefix) and not entry.is_expired():
                    identifier = cache_key[len(prefix):]
                    cache_data[identifier] = entry.to_dict()

            # 写入文件
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)

            self.logger.debug(f"已保存 {cache_type.value} 缓存: {len(cache_data)} 个条目")
        except Exception as e:
            self.logger.error(f"保存缓存文件失败 {cache_type.value}: {e}")

    def get(self, cache_type: CacheType, identifier: str, default: Any = None) -> Any:
        """
        获取缓存数据

        Args:
            cache_type: 缓存类型
            identifier: 缓存标识符
            default: 默认值

        Returns:
            缓存的数据或默认值
        """
        cache_key = self._generate_cache_key(cache_type, identifier)

        if cache_key in self._memory_cache:
            entry = self._memory_cache[cache_key]

            # 检查是否过期
            if entry.is_expired():
                self.logger.debug(f"缓存已过期，删除: {cache_key}")
                del self._memory_cache[cache_key]
                return default

            # 返回数据并更新访问统计
            return entry.access()

        return default

    def set(self, cache_type: CacheType, identifier: str, data: Any, ttl: Optional[int] = None):
        """
        设置缓存数据

        Args:
            cache_type: 缓存类型
            identifier: 缓存标识符
            data: 要缓存的数据
            ttl: 生存时间（秒），None使用默认值
        """
        cache_key = self._generate_cache_key(cache_type, identifier)

        if cache_key in self._memory_cache:
            # 更新现有缓存
            self._memory_cache[cache_key].update_data(data)
            self.logger.debug(f"更新缓存: {cache_key}")
        else:
            # 创建新缓存
            entry = CacheEntry(data, cache_type, ttl)
            self._memory_cache[cache_key] = entry
            self.logger.debug(f"创建缓存: {cache_key}")

        # 异步保存到文件
        self._save_cache_file(cache_type)

    def delete(self, cache_type: CacheType, identifier: str) -> bool:
        """
        删除缓存数据

        Args:
            cache_type: 缓存类型
            identifier: 缓存标识符

        Returns:
            是否成功删除
        """
        cache_key = self._generate_cache_key(cache_type, identifier)

        if cache_key in self._memory_cache:
            del self._memory_cache[cache_key]
            self.logger.debug(f"删除缓存: {cache_key}")
            self._save_cache_file(cache_type)
            return True

        return False

    def exists(self, cache_type: CacheType, identifier: str) -> bool:
        """
        检查缓存是否存在且未过期

        Args:
            cache_type: 缓存类型
            identifier: 缓存标识符

        Returns:
            缓存是否存在且有效
        """
        cache_key = self._generate_cache_key(cache_type, identifier)

        if cache_key in self._memory_cache:
            entry = self._memory_cache[cache_key]
            if entry.is_expired():
                del self._memory_cache[cache_key]
                return False
            return True

        return False

    def clear_cache_type(self, cache_type: CacheType):
        """
        清空指定类型的所有缓存

        Args:
            cache_type: 要清空的缓存类型
        """
        prefix = f"{cache_type.value}:"
        keys_to_delete = [key for key in self._memory_cache.keys() if key.startswith(prefix)]

        for key in keys_to_delete:
            del self._memory_cache[key]

        # 删除缓存文件
        cache_file = self.cache_files[cache_type]
        if cache_file.exists():
            cache_file.unlink()

        self.logger.info(f"已清空 {cache_type.value} 缓存: {len(keys_to_delete)} 个条目")

    def clear_all(self):
        """清空所有缓存"""
        self._memory_cache.clear()

        # 删除所有缓存文件
        for cache_file in self.cache_files.values():
            if cache_file.exists():
                cache_file.unlink()

        self.logger.info("已清空所有缓存")

    def cleanup_expired(self):
        """清理过期的缓存条目"""
        expired_keys = []

        for cache_key, entry in self._memory_cache.items():
            if entry.is_expired():
                expired_keys.append(cache_key)

        for key in expired_keys:
            cache_type_str = key.split(':')[0]
            cache_type = CacheType(cache_type_str)
            del self._memory_cache[key]
            self._save_cache_file(cache_type)

        if expired_keys:
            self.logger.info(f"清理过期缓存: {len(expired_keys)} 个条目")

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            缓存统计数据
        """
        stats = {
            'total_entries': len(self._memory_cache),
            'by_type': {},
            'memory_usage_mb': 0,  # 简化实现，实际可以计算内存使用
        }

        # 按类型统计
        for cache_key, entry in self._memory_cache.items():
            cache_type_str = cache_key.split(':')[0]
            if cache_type_str not in stats['by_type']:
                stats['by_type'][cache_type_str] = {
                    'count': 0,
                    'expired_count': 0,
                    'total_access_count': 0,
                }

            stats['by_type'][cache_type_str]['count'] += 1
            stats['by_type'][cache_type_str]['total_access_count'] += entry.access_count

            if entry.is_expired():
                stats['by_type'][cache_type_str]['expired_count'] += 1

        return stats

    def refresh_user_cache(self, user_id: str, force: bool = False) -> bool:
        """
        刷新用户缓存（用户信息是永久缓存，需要手动刷新）

        Args:
            user_id: 用户ID
            force: 是否强制刷新

        Returns:
            是否需要刷新
        """
        if not force and self.exists(CacheType.USER_INFO, user_id):
            return False

        # 删除现有缓存，强制重新获取
        self.delete(CacheType.USER_INFO, user_id)
        self.logger.info(f"已标记用户缓存需要刷新: {user_id}")
        return True

    def update_project_metadata(self, project_id: str, metadata: Dict, merge: bool = True):
        """
        更新项目元数据缓存（支持增量更新）

        Args:
            project_id: 项目ID
            metadata: 元数据
            merge: 是否与现有数据合并
        """
        if merge and self.exists(CacheType.PROJECT_METADATA, project_id):
            existing_data = self.get(CacheType.PROJECT_METADATA, project_id, {})
            if isinstance(existing_data, dict) and isinstance(metadata, dict):
                existing_data.update(metadata)
                metadata = existing_data

        self.set(CacheType.PROJECT_METADATA, project_id, metadata)
        self.logger.debug(f"更新项目元数据缓存: {project_id}")

    def batch_set(self, cache_type: CacheType, data_dict: Dict[str, Any], ttl: Optional[int] = None):
        """
        批量设置缓存数据

        Args:
            cache_type: 缓存类型
            data_dict: 数据字典 {identifier: data}
            ttl: 生存时间
        """
        for identifier, data in data_dict.items():
            self.set(cache_type, identifier, data, ttl)

        self.logger.info(f"批量设置 {cache_type.value} 缓存: {len(data_dict)} 个条目")

    def get_cache_info(self, cache_type: CacheType, identifier: str) -> Optional[Dict]:
        """
        获取缓存条目的详细信息

        Args:
            cache_type: 缓存类型
            identifier: 缓存标识符

        Returns:
            缓存条目信息
        """
        cache_key = self._generate_cache_key(cache_type, identifier)

        if cache_key in self._memory_cache:
            entry = self._memory_cache[cache_key]
            return {
                'identifier': identifier,
                'cache_type': cache_type.value,
                'created_at': datetime.fromtimestamp(entry.created_at).isoformat(),
                'updated_at': datetime.fromtimestamp(entry.updated_at).isoformat(),
                'last_accessed': datetime.fromtimestamp(entry.last_accessed).isoformat(),
                'access_count': entry.access_count,
                'ttl': entry.ttl,
                'is_expired': entry.is_expired(),
                'age_seconds': time.time() - entry.created_at,
                'time_since_update': time.time() - entry.updated_at,
            }

        return None


# 全局缓存管理器实例
_global_cache_manager: Optional[CacheManager] = None


def get_cache_manager(cache_dir: str = None) -> CacheManager:
    """
    获取全局缓存管理器实例

    Args:
        cache_dir: 缓存目录路径

    Returns:
        缓存管理器实例
    """
    global _global_cache_manager

    if _global_cache_manager is None:
        _global_cache_manager = CacheManager(cache_dir)

    return _global_cache_manager


def reset_cache_manager():
    """重置全局缓存管理器"""
    global _global_cache_manager
    _global_cache_manager = None


if __name__ == "__main__":
    # 示例用法
    import logging

    # 设置日志
    logging.basicConfig(level=logging.DEBUG)

    # 创建缓存管理器
    cache_manager = CacheManager()

    # 测试用户信息缓存（永久缓存）
    user_data = {"id": "user123", "name": "张三", "email": "zhangsan@example.com"}
    cache_manager.set(CacheType.USER_INFO, "user123", user_data)

    # 测试项目元数据缓存（1小时）
    project_data = {"id": "proj456", "name": "测试项目", "status": "active"}
    cache_manager.set(CacheType.PROJECT_METADATA, "proj456", project_data)

    # 获取缓存数据
    cached_user = cache_manager.get(CacheType.USER_INFO, "user123")
    cached_project = cache_manager.get(CacheType.PROJECT_METADATA, "proj456")

    print("缓存的用户数据:", cached_user)
    print("缓存的项目数据:", cached_project)

    # 获取缓存统计
    stats = cache_manager.get_cache_stats()
    print("缓存统计:", json.dumps(stats, indent=2, ensure_ascii=False))

    # 增量更新项目元数据
    cache_manager.update_project_metadata("proj456", {"last_updated": "2026-02-10"})
    updated_project = cache_manager.get(CacheType.PROJECT_METADATA, "proj456")
    print("更新后的项目数据:", updated_project)