#!/usr/bin/env python3
"""
TaskFilter - 智能任务筛选和排序类
用于对Plane任务进行高级筛选、排序和限制
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Callable, Union
from enum import Enum


class PriorityLevel(Enum):
    """任务优先级枚举"""
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class SortOrder(Enum):
    """排序顺序枚举"""
    ASC = "asc"
    DESC = "desc"


class TaskFilter:
    """智能任务筛选和排序类"""

    # 优先级权重映射（数值越高优先级越高）
    PRIORITY_WEIGHTS = {
        PriorityLevel.URGENT.value: 4,
        PriorityLevel.HIGH.value: 3,
        PriorityLevel.MEDIUM.value: 2,
        PriorityLevel.LOW.value: 1,
        PriorityLevel.NONE.value: 0,
        None: 0
    }

    def __init__(self):
        """初始化TaskFilter"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # 筛选条件
        self.assignee_filter: Optional[Union[str, List[str]]] = None
        self.state_filter: Optional[Union[str, List[str]]] = None
        self.priority_filter: Optional[Union[str, List[str]]] = None
        self.project_filter: Optional[Union[str, List[str]]] = None
        self.label_filter: Optional[Union[str, List[str]]] = None

        # 时间筛选
        self.updated_after: Optional[datetime] = None
        self.updated_before: Optional[datetime] = None
        self.created_after: Optional[datetime] = None
        self.created_before: Optional[datetime] = None

        # 排序设置
        self.sort_by_priority: bool = True
        self.sort_by_updated: bool = False
        self.sort_by_created: bool = False
        self.sort_order: SortOrder = SortOrder.DESC

        # 限制设置
        self.limit: Optional[int] = None
        self.offset: int = 0

        # 自定义筛选函数
        self.custom_filters: List[Callable[[Dict], bool]] = []

    def set_assignee_filter(self, assignees: Union[str, List[str]]) -> 'TaskFilter':
        """
        设置负责人筛选

        Args:
            assignees: 负责人ID或ID列表

        Returns:
            TaskFilter实例（支持链式调用）
        """
        self.assignee_filter = assignees
        return self

    def set_state_filter(self, states: Union[str, List[str]]) -> 'TaskFilter':
        """
        设置状态筛选

        Args:
            states: 状态ID或ID列表

        Returns:
            TaskFilter实例（支持链式调用）
        """
        self.state_filter = states
        return self

    def set_priority_filter(self, priorities: Union[str, List[str]]) -> 'TaskFilter':
        """
        设置优先级筛选

        Args:
            priorities: 优先级或优先级列表

        Returns:
            TaskFilter实例（支持链式调用）
        """
        self.priority_filter = priorities
        return self

    def set_project_filter(self, projects: Union[str, List[str]]) -> 'TaskFilter':
        """
        设置项目筛选

        Args:
            projects: 项目ID或ID列表

        Returns:
            TaskFilter实例（支持链式调用）
        """
        self.project_filter = projects
        return self

    def set_label_filter(self, labels: Union[str, List[str]]) -> 'TaskFilter':
        """
        设置标签筛选

        Args:
            labels: 标签ID或ID列表

        Returns:
            TaskFilter实例（支持链式调用）
        """
        self.label_filter = labels
        return self

    def set_updated_time_range(self, after: Optional[datetime] = None,
                              before: Optional[datetime] = None) -> 'TaskFilter':
        """
        设置更新时间范围筛选

        Args:
            after: 更新时间晚于此时间
            before: 更新时间早于此时间

        Returns:
            TaskFilter实例（支持链式调用）
        """
        self.updated_after = after
        self.updated_before = before
        return self

    def set_created_time_range(self, after: Optional[datetime] = None,
                              before: Optional[datetime] = None) -> 'TaskFilter':
        """
        设置创建时间范围筛选

        Args:
            after: 创建时间晚于此时间
            before: 创建时间早于此时间

        Returns:
            TaskFilter实例（支持链式调用）
        """
        self.created_after = after
        self.created_before = before
        return self

    def set_sorting(self, by_priority: bool = True, by_updated: bool = False,
                   by_created: bool = False, order: SortOrder = SortOrder.DESC) -> 'TaskFilter':
        """
        设置排序规则

        Args:
            by_priority: 是否按优先级排序
            by_updated: 是否按更新时间排序
            by_created: 是否按创建时间排序
            order: 排序顺序

        Returns:
            TaskFilter实例（支持链式调用）
        """
        self.sort_by_priority = by_priority
        self.sort_by_updated = by_updated
        self.sort_by_created = by_created
        self.sort_order = order
        return self

    def set_limit(self, limit: Optional[int], offset: int = 0) -> 'TaskFilter':
        """
        设置结果数量限制

        Args:
            limit: 最大返回数量
            offset: 偏移量

        Returns:
            TaskFilter实例（支持链式调用）
        """
        self.limit = limit
        self.offset = offset
        return self

    def add_custom_filter(self, filter_func: Callable[[Dict], bool]) -> 'TaskFilter':
        """
        添加自定义筛选函数

        Args:
            filter_func: 接受任务字典，返回布尔值的筛选函数

        Returns:
            TaskFilter实例（支持链式调用）
        """
        self.custom_filters.append(filter_func)
        return self

    def _parse_datetime(self, date_str: str) -> Optional[datetime]:
        """
        解析日期时间字符串

        Args:
            date_str: 日期时间字符串

        Returns:
            datetime对象或None
        """
        if not date_str:
            return None

        try:
            # 尝试多种日期格式
            formats = [
                "%Y-%m-%dT%H:%M:%S.%f%z",
                "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%S.%fZ",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d"
            ]

            for fmt in formats:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    # 如果没有时区信息，假设为UTC
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    return dt
                except ValueError:
                    continue

            self.logger.warning(f"无法解析日期时间: {date_str}")
            return None

        except Exception as e:
            self.logger.error(f"解析日期时间失败 {date_str}: {e}")
            return None

    def _get_priority_weight(self, task: Dict) -> int:
        """
        获取任务优先级权重

        Args:
            task: 任务字典

        Returns:
            优先级权重
        """
        priority = task.get('priority')
        if isinstance(priority, dict):
            priority = priority.get('key') or priority.get('name')

        return self.PRIORITY_WEIGHTS.get(priority, 0)

    def _matches_filter(self, task: Dict, filter_value: Union[str, List[str]],
                       task_field: str, task_subfield: str = None) -> bool:
        """
        检查任务是否匹配筛选条件

        Args:
            task: 任务字典
            filter_value: 筛选值
            task_field: 任务字段名
            task_subfield: 任务子字段名（可选）

        Returns:
            是否匹配
        """
        if filter_value is None:
            return True

        # 获取任务字段值
        field_value = task.get(task_field)
        if field_value is None:
            return False

        # 如果有子字段，获取子字段值
        if task_subfield:
            if isinstance(field_value, dict):
                field_value = field_value.get(task_subfield)
            elif isinstance(field_value, list):
                field_value = [item.get(task_subfield) if isinstance(item, dict) else item
                              for item in field_value]
            else:
                return False

        # 转换为列表进行比较
        if not isinstance(filter_value, list):
            filter_value = [filter_value]

        if isinstance(field_value, list):
            # 字段值是列表，检查是否有交集
            return any(val in filter_value for val in field_value if val is not None)
        else:
            # 字段值是单个值
            return field_value in filter_value

    def _matches_assignee_filter(self, task: Dict) -> bool:
        """检查任务是否匹配负责人筛选"""
        if self.assignee_filter is None:
            return True

        assignees = task.get('assignees', [])
        if not assignees:
            return False

        assignee_ids = [assignee.get('id') for assignee in assignees if isinstance(assignee, dict)]

        filter_list = self.assignee_filter if isinstance(self.assignee_filter, list) else [self.assignee_filter]
        return any(assignee_id in filter_list for assignee_id in assignee_ids if assignee_id)

    def _matches_state_filter(self, task: Dict) -> bool:
        """检查任务是否匹配状态筛选"""
        return self._matches_filter(task, self.state_filter, 'state', 'id')

    def _matches_priority_filter(self, task: Dict) -> bool:
        """检查任务是否匹配优先级筛选"""
        return self._matches_filter(task, self.priority_filter, 'priority', 'key')

    def _matches_project_filter(self, task: Dict) -> bool:
        """检查任务是否匹配项目筛选"""
        return self._matches_filter(task, self.project_filter, 'project', 'id')

    def _matches_label_filter(self, task: Dict) -> bool:
        """检查任务是否匹配标签筛选"""
        if self.label_filter is None:
            return True

        labels = task.get('labels', [])
        if not labels:
            return False

        label_ids = [label.get('id') for label in labels if isinstance(label, dict)]

        filter_list = self.label_filter if isinstance(self.label_filter, list) else [self.label_filter]
        return any(label_id in filter_list for label_id in label_ids if label_id)

    def _matches_time_filter(self, task: Dict) -> bool:
        """检查任务是否匹配时间筛选"""
        # 检查更新时间
        if self.updated_after or self.updated_before:
            updated_at = self._parse_datetime(task.get('updated_at'))
            if updated_at:
                if self.updated_after and updated_at < self.updated_after:
                    return False
                if self.updated_before and updated_at > self.updated_before:
                    return False
            elif self.updated_after or self.updated_before:
                return False

        # 检查创建时间
        if self.created_after or self.created_before:
            created_at = self._parse_datetime(task.get('created_at'))
            if created_at:
                if self.created_after and created_at < self.created_after:
                    return False
                if self.created_before and created_at > self.created_before:
                    return False
            elif self.created_after or self.created_before:
                return False

        return True

    def _matches_custom_filters(self, task: Dict) -> bool:
        """检查任务是否匹配自定义筛选"""
        return all(filter_func(task) for filter_func in self.custom_filters)

    def _sort_tasks(self, tasks: List[Dict]) -> List[Dict]:
        """
        对任务进行排序

        Args:
            tasks: 任务列表

        Returns:
            排序后的任务列表
        """
        def sort_key(task: Dict) -> tuple:
            keys = []

            # 优先级排序
            if self.sort_by_priority:
                priority_weight = self._get_priority_weight(task)
                keys.append(-priority_weight if self.sort_order == SortOrder.DESC else priority_weight)

            # 更新时间排序
            if self.sort_by_updated:
                updated_at = self._parse_datetime(task.get('updated_at'))
                if updated_at:
                    timestamp = updated_at.timestamp()
                    keys.append(-timestamp if self.sort_order == SortOrder.DESC else timestamp)
                else:
                    keys.append(0)

            # 创建时间排序
            if self.sort_by_created:
                created_at = self._parse_datetime(task.get('created_at'))
                if created_at:
                    timestamp = created_at.timestamp()
                    keys.append(-timestamp if self.sort_order == SortOrder.DESC else timestamp)
                else:
                    keys.append(0)

            return tuple(keys) if keys else (0,)

        return sorted(tasks, key=sort_key)

    def filter_tasks(self, tasks: List[Dict]) -> List[Dict]:
        """
        对任务列表进行筛选和排序

        Args:
            tasks: 原始任务列表

        Returns:
            筛选和排序后的任务列表
        """
        if not tasks:
            return []

        self.logger.debug(f"开始筛选任务，原始数量: {len(tasks)}")

        # 应用筛选条件
        filtered_tasks = []
        for task in tasks:
            if (self._matches_assignee_filter(task) and
                self._matches_state_filter(task) and
                self._matches_priority_filter(task) and
                self._matches_project_filter(task) and
                self._matches_label_filter(task) and
                self._matches_time_filter(task) and
                self._matches_custom_filters(task)):
                filtered_tasks.append(task)

        self.logger.debug(f"筛选后任务数量: {len(filtered_tasks)}")

        # 排序
        if self.sort_by_priority or self.sort_by_updated or self.sort_by_created:
            filtered_tasks = self._sort_tasks(filtered_tasks)
            self.logger.debug("任务排序完成")

        # 应用偏移和限制
        if self.offset > 0:
            filtered_tasks = filtered_tasks[self.offset:]

        if self.limit is not None and self.limit > 0:
            filtered_tasks = filtered_tasks[:self.limit]

        self.logger.info(f"最终返回任务数量: {len(filtered_tasks)}")
        return filtered_tasks

    def get_filter_summary(self) -> Dict[str, Any]:
        """
        获取当前筛选条件摘要

        Returns:
            筛选条件摘要字典
        """
        return {
            'assignee_filter': self.assignee_filter,
            'state_filter': self.state_filter,
            'priority_filter': self.priority_filter,
            'project_filter': self.project_filter,
            'label_filter': self.label_filter,
            'updated_after': self.updated_after.isoformat() if self.updated_after else None,
            'updated_before': self.updated_before.isoformat() if self.updated_before else None,
            'created_after': self.created_after.isoformat() if self.created_after else None,
            'created_before': self.created_before.isoformat() if self.created_before else None,
            'sort_by_priority': self.sort_by_priority,
            'sort_by_updated': self.sort_by_updated,
            'sort_by_created': self.sort_by_created,
            'sort_order': self.sort_order.value,
            'limit': self.limit,
            'offset': self.offset,
            'custom_filters_count': len(self.custom_filters)
        }

    def reset(self) -> 'TaskFilter':
        """
        重置所有筛选条件

        Returns:
            TaskFilter实例（支持链式调用）
        """
        self.assignee_filter = None
        self.state_filter = None
        self.priority_filter = None
        self.project_filter = None
        self.label_filter = None
        self.updated_after = None
        self.updated_before = None
        self.created_after = None
        self.created_before = None
        self.sort_by_priority = True
        self.sort_by_updated = False
        self.sort_by_created = False
        self.sort_order = SortOrder.DESC
        self.limit = None
        self.offset = 0
        self.custom_filters = []
        return self


# 便捷函数
def create_priority_filter(priorities: Union[str, List[str]], limit: int = None) -> TaskFilter:
    """
    创建按优先级筛选的TaskFilter

    Args:
        priorities: 优先级或优先级列表
        limit: 结果数量限制

    Returns:
        配置好的TaskFilter实例
    """
    return TaskFilter().set_priority_filter(priorities).set_limit(limit)


def create_assignee_filter(assignees: Union[str, List[str]], limit: int = None) -> TaskFilter:
    """
    创建按负责人筛选的TaskFilter

    Args:
        assignees: 负责人ID或ID列表
        limit: 结果数量限制

    Returns:
        配置好的TaskFilter实例
    """
    return TaskFilter().set_assignee_filter(assignees).set_limit(limit)


def create_recent_tasks_filter(days: int = 7, limit: int = 20) -> TaskFilter:
    """
    创建最近任务筛选器

    Args:
        days: 最近天数
        limit: 结果数量限制

    Returns:
        配置好的TaskFilter实例
    """
    from datetime import timedelta

    after_date = datetime.now(timezone.utc) - timedelta(days=days)
    return (TaskFilter()
            .set_updated_time_range(after=after_date)
            .set_sorting(by_priority=True, by_updated=True)
            .set_limit(limit))


def create_high_priority_filter(limit: int = 10) -> TaskFilter:
    """
    创建高优先级任务筛选器

    Args:
        limit: 结果数量限制

    Returns:
        配置好的TaskFilter实例
    """
    return (TaskFilter()
            .set_priority_filter([PriorityLevel.URGENT.value, PriorityLevel.HIGH.value])
            .set_sorting(by_priority=True)
            .set_limit(limit))
