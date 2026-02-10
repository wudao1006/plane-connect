"""
Plane Sync Skills - 主入口函数

这个模块提供了plane_sync_skill函数，整合了所有组件来实现完整的Plane任务同步功能。
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import argparse
import traceback

# 导入所有组件
from .config_manager import ConfigManager, get_config
from .cache_manager import CacheManager, get_cache_manager, CacheType
from .task_filter import TaskFilter, PriorityLevel
from .template_engine import TemplateEngine
from .plane_client import PlaneClient


class PlaneSkillsError(Exception):
    """Plane Skills自定义异常"""
    pass


def parse_skill_args(args_string: str = "") -> Dict[str, Any]:
    """解析Skills参数字符串"""
    if not args_string.strip():
        return {}

    parser = argparse.ArgumentParser(description='Plane Sync Skills')
    parser.add_argument('project_id', nargs='?', help='项目ID')
    parser.add_argument('--my-tasks', action='store_true', help='只同步我的任务')
    parser.add_argument('--assignee', help='按负责人筛选')
    parser.add_argument('--priority', help='按优先级筛选 (urgent,high,medium,low)')
    parser.add_argument('--status', help='按状态筛选')
    parser.add_argument('--limit', type=int, default=20, help='限制任务数量')
    parser.add_argument('--template', default='ai-context', help='模板类型')
    parser.add_argument('--output', default='plane.md', help='输出文件名')
    parser.add_argument('--refresh-users', action='store_true', help='刷新用户缓存')

    try:
        # 分割参数字符串
        args_list = []
        if args_string.strip():
            import shlex
            args_list = shlex.split(args_string)

        parsed_args = parser.parse_args(args_list)
        return vars(parsed_args)
    except SystemExit:
        # argparse调用sys.exit，我们捕获并返回空字典
        return {}
    except Exception as e:
        print(f"参数解析错误: {e}")
        return {}


def validate_project_id(project_id: str, available_projects: List[Dict]) -> Optional[str]:
    """验证项目ID并返回有效的项目ID"""
    if not project_id:
        return None

    # 直接匹配项目ID
    for project in available_projects:
        if project.get('identifier', '').upper() == project_id.upper():
            return project.get('identifier')
        if project.get('name', '').lower() == project_id.lower():
            return project.get('identifier')

    return None


def format_error_message(error: Exception, verbose: bool = False) -> str:
    """格式化错误信息"""
    error_msg = f"❌ 错误: {str(error)}"

    if isinstance(error, PlaneSkillsError):
        return error_msg
    elif "API" in str(error) or "HTTP" in str(error):
        return f"{error_msg}\n💡 请检查网络连接和API配置"
    elif "permission" in str(error).lower() or "401" in str(error):
        return f"{error_msg}\n💡 请检查API密钥权限"
    elif "not found" in str(error).lower() or "404" in str(error):
        return f"{error_msg}\n💡 请检查项目ID是否正确"
    else:
        if verbose:
            return f"{error_msg}\n\n详细错误信息:\n{traceback.format_exc()}"
        return error_msg


def plane_sync_skill(
    project_id: Optional[str] = None,
    my_tasks: bool = False,
    assignee: Optional[str] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20,
    template: str = "ai-context",
    output: str = "plane.md",
    refresh_users: bool = False,
    args_string: str = "",
    **kwargs
) -> str:
    """
    Plane任务同步Skills主入口函数

    Args:
        project_id: 项目ID
        my_tasks: 是否只同步我的任务
        assignee: 按负责人筛选
        priority: 按优先级筛选
        status: 按状态筛选
        limit: 限制任务数量
        template: 模板类型
        output: 输出文件名
        refresh_users: 是否刷新用户缓存
        args_string: 参数字符串（用于Skills调用）
        **kwargs: 其他参数

    Returns:
        执行结果摘要
    """

    start_time = datetime.now()

    try:
        # 如果提供了args_string，解析参数
        if args_string:
            parsed_args = parse_skill_args(args_string)
            # 合并参数，args_string中的参数优先
            project_id = parsed_args.get('project_id') or project_id
            my_tasks = parsed_args.get('my_tasks', my_tasks)
            assignee = parsed_args.get('assignee') or assignee
            priority = parsed_args.get('priority') or priority
            status = parsed_args.get('status') or status
            limit = parsed_args.get('limit', limit)
            template = parsed_args.get('template', template)
            output = parsed_args.get('output', output)
            refresh_users = parsed_args.get('refresh_users', refresh_users)

        # 1. 初始化配置管理器
        print("🔧 初始化配置...")
        config_manager = ConfigManager()
        config = config_manager.get_config()

        # 验证配置
        config_errors = config_manager.validate_config()
        if config_errors:
            error_msg = "配置验证失败:\n" + "\n".join(f"  - {error}" for error in config_errors)
            raise PlaneSkillsError(error_msg)

        # 2. 初始化缓存管理器
        cache_manager = get_cache_manager()

        # 3. 初始化Plane客户端
        print("🌐 连接Plane平台...")
        plane_client = PlaneClient(
            base_url=config.plane.base_url,
            api_key=config.plane.api_key,
            workspace_slug=config.plane.workspace_slug,
            cache_manager=cache_manager
        )

        # 4. 获取项目列表
        print("📋 获取项目列表...")
        projects = plane_client.list_projects()
        if not projects:
            raise PlaneSkillsError("未找到任何项目，请检查工作空间配置")

        # 5. 验证项目ID
        if not project_id:
            # 如果没有指定项目ID，列出可用项目
            project_list = "\n".join([f"  - {p.get('name', '未知')} ({p.get('identifier', '未知')})"
                                    for p in projects[:10]])  # 只显示前10个
            raise PlaneSkillsError(f"请指定项目ID。可用项目:\n{project_list}")

        valid_project_id = validate_project_id(project_id, projects)
        if not valid_project_id:
            available = ", ".join([p.get('identifier', '未知') for p in projects[:5]])
            raise PlaneSkillsError(f"项目 '{project_id}' 不存在。可用项目: {available}")

        # 获取项目信息
        project_info = next((p for p in projects if p.get('identifier') == valid_project_id), None)
        project_name = project_info.get('name', valid_project_id) if project_info else valid_project_id

        print(f"🎯 同步项目: {project_name} ({valid_project_id})")

        # 6. 刷新用户缓存（如果需要）
        if refresh_users:
            print("👥 刷新用户缓存...")
            cache_manager.cleanup_expired()  # 清理过期缓存

        # 7. 获取任务数据
        print("📥 获取任务数据...")
        tasks = plane_client.list_project_issues(project_info.get('id'))

        if not tasks:
            return f"✅ 项目 '{project_name}' 没有任务数据"

        # 8. 设置任务筛选器
        task_filter = TaskFilter()

        # 处理我的任务筛选
        if my_tasks:
            user_email = config.user.email if hasattr(config, 'user') and config.user else None
            if not user_email:
                raise PlaneSkillsError("使用 --my-tasks 需要在配置中设置用户邮箱")
            assignee = user_email

        # 应用筛选条件
        if assignee:
            # 查找用户ID
            user_id = plane_client.find_user_by_email_or_name(assignee)
            if user_id:
                task_filter.set_assignee_filter(user_id)
            else:
                print(f"⚠️  未找到用户 '{assignee}', 将按邮箱/姓名模糊匹配")

        if priority:
            priority_list = [p.strip().lower() for p in priority.split(',')]
            task_filter.set_priority_filter(priority_list)

        if status:
            status_list = [s.strip() for s in status.split(',')]
            task_filter.set_state_filter(status_list)

        # 设置排序和限制
        task_filter.set_sorting(by_priority=True, by_updated=True)
        task_filter.set_limit(limit)

        # 9. 筛选任务
        print("🔍 筛选任务...")
        filtered_tasks = task_filter.filter_tasks(tasks)

        # 10. 生成报告
        print(f"📝 生成 {template} 格式报告...")
        template_engine = TemplateEngine()

        # 准备自定义变量
        custom_vars = {
            'project_id': valid_project_id,
            'filter_summary': task_filter.get_filter_summary(),
            'sync_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_available_tasks': len(tasks),
            'filtered_task_count': len(filtered_tasks)
        }

        report_content = template_engine.render(template, filtered_tasks, project_name, custom_vars)

        # 11. 保存文件
        output_path = Path(output)
        output_path.write_text(report_content, encoding='utf-8')

        # 12. 生成执行摘要
        duration = (datetime.now() - start_time).total_seconds()

        summary = f"""✅ Plane任务同步完成!

📊 执行摘要:
  - 项目: {project_name} ({valid_project_id})
  - 总任务数: {len(tasks)}
  - 筛选后任务数: {len(filtered_tasks)}
  - 输出文件: {output_path.absolute()}
  - 模板: {template}
  - 执行时间: {duration:.1f}秒

📋 筛选条件:
{task_filter.get_filter_summary()}

📁 输出文件已保存到: {output_path.absolute()}

💡 现在AI可以基于 {output} 文件了解项目任务状态和优先级!"""

        print(summary)
        return summary

    except PlaneSkillsError as e:
        error_msg = format_error_message(e)
        print(error_msg)
        return error_msg

    except Exception as e:
        error_msg = format_error_message(e, verbose=True)
        print(error_msg)
        return error_msg


# 便捷函数
def sync_my_tasks(project_id: str, template: str = "ai-context", output: str = "plane.md") -> str:
    """同步我的任务的便捷函数"""
    return plane_sync_skill(
        project_id=project_id,
        my_tasks=True,
        template=template,
        output=output
    )


def sync_high_priority_tasks(project_id: str, template: str = "brief", output: str = "plane.md") -> str:
    """同步高优先级任务的便捷函数"""
    return plane_sync_skill(
        project_id=project_id,
        priority="urgent,high",
        template=template,
        output=output
    )


if __name__ == "__main__":
    # 命令行测试
    import sys
    if len(sys.argv) > 1:
        args_str = " ".join(sys.argv[1:])
        result = plane_sync_skill(args_string=args_str)
        print(result)
    else:
        print("用法: python plane_sync_skill.py PROJECT_ID [选项]")
        print("示例: python plane_sync_skill.py MOBILE --my-tasks --template brief")
