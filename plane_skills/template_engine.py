"""
TemplateEngine for rendering AI-friendly task output formats.

This module provides a flexible template engine for formatting task data
into various output formats with support for variable replacement,
task grouping, and Markdown rendering.
"""

import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from html import unescape


class TemplateEngine:
    """
    A template engine for rendering AI-friendly task output formats.

    Supports multiple predefined templates and custom template variable replacement.
    """

    def __init__(self, templates_dir: Optional[str] = None):
        """
        Initialize the TemplateEngine.

        Args:
            templates_dir: Path to templates directory. If None, uses default location.
        """
        if templates_dir is None:
            # Default to templates directory relative to this file
            current_dir = Path(__file__).parent
            self.templates_dir = current_dir / "templates"
        else:
            self.templates_dir = Path(templates_dir)

        # Ensure templates directory exists
        self.templates_dir.mkdir(exist_ok=True)

        # Available template types
        self.available_templates = [
            "ai-context",
            "brief",
            "standup",
            "development"
        ]

    def load_template(self, template_name: str) -> str:
        """
        Load a template from the templates directory.

        Args:
            template_name: Name of the template to load

        Returns:
            Template content as string

        Raises:
            FileNotFoundError: If template file doesn't exist
        """
        template_path = self.templates_dir / f"{template_name}.md"

        if not template_path.exists():
            raise FileNotFoundError(f"Template '{template_name}' not found at {template_path}")

        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()

    def replace_variables(self, template: str, variables: Dict[str, Any]) -> str:
        """
        Replace template variables with actual values.

        Variables are in the format {{variable_name}} in templates.

        Args:
            template: Template string with variables
            variables: Dictionary of variable names and values

        Returns:
            Template with variables replaced
        """
        result = template

        # Replace all {{variable}} patterns
        for key, value in variables.items():
            pattern = f"{{{{{key}}}}}"
            result = result.replace(pattern, str(value))

        # Replace any remaining unreplaced variables with empty string or default message
        remaining_vars = re.findall(r'\{\{([^}]+)\}\}', result)
        for var in remaining_vars:
            pattern = f"{{{{{var}}}}}"
            if var.endswith('_tasks') or var.endswith('_count'):
                result = result.replace(pattern, "暂无数据")
            else:
                result = result.replace(pattern, "无")

        return result

    def group_tasks_by_status(self, tasks: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group tasks by their status.

        Args:
            tasks: List of task dictionaries

        Returns:
            Dictionary with status as key and list of tasks as value
        """
        grouped = {}

        for task in tasks:
            status = task.get('state', {}).get('name', 'Unknown')
            if status not in grouped:
                grouped[status] = []
            grouped[status].append(task)

        return grouped

    def group_tasks_by_priority(self, tasks: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group tasks by their priority.

        Args:
            tasks: List of task dictionaries

        Returns:
            Dictionary with priority as key and list of tasks as value
        """
        grouped = {}

        for task in tasks:
            priority = task.get('priority', 'None')
            if priority not in grouped:
                grouped[priority] = []
            grouped[priority].append(task)

        return grouped

    def group_tasks_by_assignee(self, tasks: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group tasks by their assignee.

        Args:
            tasks: List of task dictionaries

        Returns:
            Dictionary with assignee as key and list of tasks as value
        """
        grouped = {}

        for task in tasks:
            assignees = task.get('assignees', [])
            if not assignees:
                assignee_name = "Unassigned"
            else:
                # Use first assignee if multiple
                assignee_name = assignees[0].get('display_name', 'Unknown')

            if assignee_name not in grouped:
                grouped[assignee_name] = []
            grouped[assignee_name].append(task)

        return grouped

    def format_task_list(self, tasks: List[Dict[str, Any]], format_type: str = "bullet") -> str:
        """
        Format a list of tasks into a string.

        Args:
            tasks: List of task dictionaries
            format_type: Format type ("bullet", "numbered", "table")

        Returns:
            Formatted task list as string
        """
        if not tasks:
            return "暂无任务。"

        if format_type == "bullet":
            return self._format_bullet_list(tasks)
        elif format_type == "numbered":
            return self._format_numbered_list(tasks)
        elif format_type == "table":
            return self._format_table(tasks)
        elif format_type == "detailed":
            return self._format_detailed_list(tasks)
        else:
            return self._format_bullet_list(tasks)

    def _format_bullet_list(self, tasks: List[Dict[str, Any]]) -> str:
        """Format tasks as bullet list."""
        lines = []
        for task in tasks:
            name = task.get('name', 'Untitled')
            priority = self._normalize_priority(task.get('priority'))
            state = self._get_state_name(task)

            # Add priority indicator
            priority_indicator = ""
            if priority == "urgent":
                priority_indicator = "🔴 "
            elif priority == "high":
                priority_indicator = "🟠 "
            elif priority == "medium":
                priority_indicator = "🟡 "
            elif priority == "low":
                priority_indicator = "🟢 "

            lines.append(f"- {priority_indicator}**{name}** ({state})")

        return "\n".join(lines)

    def _format_numbered_list(self, tasks: List[Dict[str, Any]]) -> str:
        """Format tasks as numbered list."""
        lines = []
        for i, task in enumerate(tasks, 1):
            name = task.get('name', 'Untitled')
            priority = self._normalize_priority(task.get('priority'))
            state = self._get_state_name(task)

            lines.append(f"{i}. **{name}**（优先级: {priority}，状态: {state}）")

        return "\n".join(lines)

    def _format_table(self, tasks: List[Dict[str, Any]]) -> str:
        """Format tasks as markdown table."""
        if not tasks:
            return "暂无任务。"

        lines = [
            "| 任务 | 优先级 | 状态 | 负责人 | 描述 |",
            "|------|--------|------|--------|------|"
        ]

        for task in tasks:
            name = task.get('name', 'Untitled')
            priority = self._normalize_priority(task.get('priority'))
            state = self._get_state_name(task)

            assignees = task.get('assignees', [])
            assignee = assignees[0].get('display_name', '未分配') if assignees else '未分配'
            desc = self._extract_description(task, max_length=60).replace("\n", " ")

            lines.append(f"| {name} | {priority} | {state} | {assignee} | {desc} |")

        return "\n".join(lines)

    def _format_detailed_list(self, tasks: List[Dict[str, Any]]) -> str:
        """按详细清单格式输出任务，包含描述与时间信息。"""
        lines = []
        for idx, task in enumerate(tasks, 1):
            name = task.get("name", "未命名任务")
            task_id = task.get("id", "")
            state = self._get_state_name(task)
            priority = self._normalize_priority(task.get("priority"))
            assignees = task.get("assignees", [])
            assignee_names = ", ".join(
                a.get("display_name", "未知") for a in assignees if isinstance(a, dict)
            ) or "未分配"

            created_at = task.get("created_at") or "无"
            updated_at = task.get("updated_at") or "无"
            start_date = task.get("start_date") or "无"
            target_date = task.get("target_date") or "无"
            description = self._extract_description(task)

            lines.extend([
                f"{idx}. **{name}**",
                f"   - 任务ID: `{task_id}`",
                f"   - 状态: {state}",
                f"   - 优先级: {priority}",
                f"   - 负责人: {assignee_names}",
                f"   - 开始日期: {start_date}",
                f"   - 截止日期: {target_date}",
                f"   - 创建时间: {created_at}",
                f"   - 更新时间: {updated_at}",
                f"   - 详细描述: {description}",
            ])

        return "\n".join(lines)

    def _get_state_name(self, task: Dict[str, Any]) -> str:
        state = task.get("state", {})
        if isinstance(state, dict):
            return state.get("name", "未知")
        return str(state) if state else "未知"

    def _get_state_group(self, task: Dict[str, Any]) -> str:
        state = task.get("state", {})
        if isinstance(state, dict):
            return str(state.get("group", "")).lower()
        return ""

    def _normalize_priority(self, priority: Any) -> str:
        if isinstance(priority, dict):
            priority = priority.get("key") or priority.get("name")
        if not priority:
            return "none"
        return str(priority).lower()

    def _extract_description(self, task: Dict[str, Any], max_length: int = 300) -> str:
        description = (
            task.get("description_stripped")
            or task.get("description_text")
            or task.get("description")
            or task.get("description_html")
            or ""
        )
        if not description:
            return "无描述"

        text = self._strip_html(str(description))
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            return "无描述"
        if len(text) > max_length:
            return text[: max_length - 3] + "..."
        return text

    def _strip_html(self, value: str) -> str:
        if not value:
            return ""
        text = re.sub(r"<br\s*/?>", "\n", value, flags=re.IGNORECASE)
        text = re.sub(r"</p\s*>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"<[^>]+>", "", text)
        return unescape(text)

    def get_template_variables(self, tasks: List[Dict[str, Any]],
                             project_name: str = "",
                             additional_vars: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate common template variables from task data.

        Args:
            tasks: List of task dictionaries
            project_name: Name of the project
            additional_vars: Additional variables to include

        Returns:
            Dictionary of template variables
        """
        now = datetime.now()

        # 按状态分组（优先使用 state.group，兼容旧数据）
        done_groups = {"completed", "done"}
        in_progress_groups = {"started", "in_progress", "in-progress"}
        pending_groups = {"unstarted", "backlog", "todo", "to_do"}
        blocked_groups = {"blocked"}

        done_list = []
        in_progress_list = []
        pending_list = []
        blocked_list = []

        for task in tasks:
            group = self._get_state_group(task)
            state_name = self._get_state_name(task).lower()
            if group in done_groups or state_name in {"done", "completed"}:
                done_list.append(task)
            elif group in in_progress_groups or state_name in {"in progress", "in-progress", "started"}:
                in_progress_list.append(task)
            elif group in blocked_groups or state_name == "blocked":
                blocked_list.append(task)
            elif group in pending_groups or state_name in {"todo", "to do", "backlog", "unstarted"}:
                pending_list.append(task)
            else:
                pending_list.append(task)

        # Basic statistics
        total_tasks = len(tasks)
        completed_tasks = len(done_list)
        in_progress_tasks = len(in_progress_list)
        pending_tasks = len(pending_list)

        # Group tasks
        tasks_by_status = self.group_tasks_by_status(tasks)
        tasks_by_priority = self.group_tasks_by_priority(tasks)
        tasks_by_assignee = self.group_tasks_by_assignee(tasks)

        variables = {
            # Date and time
            'date': now.strftime('%Y-%m-%d'),
            'time': now.strftime('%H:%M:%S'),
            'datetime': now.strftime('%Y-%m-%d %H:%M:%S'),
            'timestamp': int(now.timestamp()),

            # Project info
            'project_name': project_name,

            # Task statistics
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'in_progress_count': in_progress_tasks,
            'pending_tasks': pending_tasks,
            'pending_count': pending_tasks,
            'blocked_count': len(blocked_list),
            'completion_rate': f"{(completed_tasks/total_tasks*100):.1f}%" if total_tasks > 0 else "0%",

            # Task lists (formatted)
            'all_tasks_bullet': self.format_task_list(tasks, "bullet"),
            'all_tasks_numbered': self.format_task_list(tasks, "numbered"),
            'all_tasks_table': self.format_task_list(tasks, "table"),
            'all_tasks_detailed': self.format_task_list(tasks, "detailed"),

            # Tasks by status
            'tasks_by_status': tasks_by_status,
            'tasks_by_priority': tasks_by_priority,
            'tasks_by_assignee': tasks_by_assignee,
        }

        # Add formatted lists for each status
        for status, status_tasks in tasks_by_status.items():
            safe_status = re.sub(r'[^a-zA-Z0-9_]', '_', status.lower())
            variables[f'{safe_status}_tasks'] = self.format_task_list(status_tasks, "bullet")
            variables[f'{safe_status}_count'] = len(status_tasks)

        # Add common status aliases
        variables['done_tasks'] = self.format_task_list(done_list, "detailed")
        variables['in_progress_tasks'] = self.format_task_list(in_progress_list, "detailed")
        variables['to_do_tasks'] = self.format_task_list(pending_list, "detailed")
        variables['blocked_tasks'] = self.format_task_list(blocked_list, "detailed")
        variables['review_tasks'] = '暂无评审任务'
        variables['testing_tasks'] = '暂无测试任务'
        variables['ready_tasks'] = '暂无待发布任务'
        variables['technical_debt_tasks'] = '暂无技术债任务'
        variables['unassigned_tasks'] = self.format_task_list([t for t in tasks if not t.get('assignees')], "bullet")

        # Add formatted lists for each priority
        for priority, priority_tasks in tasks_by_priority.items():
            safe_priority = re.sub(r'[^a-zA-Z0-9_]', '_', str(priority).lower())
            variables[f'{safe_priority}_priority_tasks'] = self.format_task_list(priority_tasks, "bullet")
            variables[f'{safe_priority}_priority_count'] = len(priority_tasks)

        # Add review and testing counts
        variables['review_count'] = 0
        variables['testing_count'] = 0

        # Add additional variables if provided
        if additional_vars:
            variables.update(additional_vars)

        return variables

    def render(self, template_name: str, tasks: List[Dict[str, Any]],
               project_name: str = "", additional_vars: Optional[Dict[str, Any]] = None) -> str:
        """
        Render a template with task data.

        Args:
            template_name: Name of the template to use
            tasks: List of task dictionaries
            project_name: Name of the project
            additional_vars: Additional template variables

        Returns:
            Rendered template as string

        Raises:
            FileNotFoundError: If template doesn't exist
        """
        # Load template
        template = self.load_template(template_name)

        # Get template variables
        variables = self.get_template_variables(tasks, project_name, additional_vars)

        # Replace variables and return
        return self.replace_variables(template, variables)

    def list_available_templates(self) -> List[str]:
        """
        List all available templates.

        Returns:
            List of available template names
        """
        templates = []

        # Check for predefined templates
        for template_name in self.available_templates:
            template_path = self.templates_dir / f"{template_name}.md"
            if template_path.exists():
                templates.append(template_name)

        # Check for custom templates
        for template_file in self.templates_dir.glob("*.md"):
            template_name = template_file.stem
            if template_name not in self.available_templates:
                templates.append(template_name)

        return sorted(templates)
