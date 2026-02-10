#!/usr/bin/env python3
"""
Configuration Manager for Plane Skills System
管理全局和项目级配置的配置管理器
"""

import json
import os
import logging
import getpass
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, asdict
from copy import deepcopy


@dataclass
class PlaneConfig:
    """Plane连接配置"""
    base_url: str = ""
    api_key: str = ""
    workspace_slug: str = ""


@dataclass
class CacheConfig:
    """缓存配置"""
    enabled: bool = True
    cache_dir: str = ""
    ttl_seconds: int = 3600  # 1小时
    max_size_mb: int = 100


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: str = ""
    max_file_size_mb: int = 10
    backup_count: int = 5


@dataclass
class TemplateConfig:
    """模板配置"""
    template_dir: str = ""
    default_template: str = "default"
    auto_reload: bool = True


@dataclass
class FilterConfig:
    """任务过滤配置"""
    default_assignee: str = ""
    default_state: str = ""
    default_priority: str = ""
    exclude_completed: bool = True
    max_results: int = 100


@dataclass
class ReportConfig:
    """报告配置"""
    output_dir: str = ""
    default_format: str = "markdown"
    include_attachments: bool = False
    date_format: str = "%Y-%m-%d %H:%M:%S"


@dataclass
class UserConfig:
    """用户配置"""
    email: str = ""
    display_name: str = ""


@dataclass
class GlobalConfig:
    """全局配置结构"""
    plane: PlaneConfig
    cache: CacheConfig
    logging: LoggingConfig
    template: TemplateConfig
    filter: FilterConfig
    report: ReportConfig
    user: UserConfig

    def __post_init__(self):
        """初始化后处理，设置默认路径"""
        home_dir = Path.home()
        skills_dir = home_dir / '.plane-skills'

        if not self.cache.cache_dir:
            self.cache.cache_dir = str(skills_dir / 'cache')

        if not self.logging.file_path:
            self.logging.file_path = str(skills_dir / 'logs' / 'plane-skills.log')

        if not self.template.template_dir:
            self.template.template_dir = str(skills_dir / 'templates')

        if not self.report.output_dir:
            self.report.output_dir = str(skills_dir / 'reports')


class ConfigManager:
    """配置管理器，支持全局和项目级配置"""

    # 默认配置文件路径
    GLOBAL_CONFIG_DIR = Path.home() / '.plane-skills'
    GLOBAL_CONFIG_FILE = GLOBAL_CONFIG_DIR / 'config.json'
    PROJECT_CONFIG_FILE = '.plane-config.json'

    # 环境变量前缀
    ENV_PREFIX = 'PLANE_SKILLS_'

    def __init__(self, project_dir: Optional[Union[str, Path]] = None):
        """
        初始化配置管理器

        Args:
            project_dir: 项目目录路径，默认为当前工作目录
        """
        self.project_dir = Path(project_dir) if project_dir else Path.cwd()
        self.project_config_file = self.project_dir / self.PROJECT_CONFIG_FILE

        # 设置日志器
        self.logger = logging.getLogger(__name__)

        # 先加载环境变量文件，再加载配置
        self._load_env_file()

        # 加载配置
        self._config = self._load_config()

        # 确保必要的目录存在
        self._ensure_directories()

    def _load_config(self) -> GlobalConfig:
        """加载并合并配置"""
        # 1. 从默认配置开始
        config = GlobalConfig(
            plane=PlaneConfig(),
            cache=CacheConfig(),
            logging=LoggingConfig(),
            template=TemplateConfig(),
            filter=FilterConfig(),
            report=ReportConfig(),
            user=UserConfig(),
        )

        # 2. 加载全局配置
        global_config = self._load_global_config()
        if global_config:
            config = self._merge_config(config, global_config)

        # 3. 加载项目配置
        project_config = self._load_project_config()
        if project_config:
            config = self._merge_config(config, project_config)

        # 4. 应用环境变量
        config = self._apply_env_vars(config)

        return config

    def _load_env_file(self):
        """从项目目录加载 .env 文件（如果可用）"""
        env_file = self.project_dir / ".env"
        if not env_file.exists():
            return

        try:
            from dotenv import load_dotenv
            load_dotenv(dotenv_path=env_file, override=True)
            self.logger.debug(f"Loaded environment variables from {env_file}")
        except Exception as e:
            self.logger.warning(f"Failed to load .env file {env_file}: {e}")

    def _load_global_config(self) -> Optional[Dict[str, Any]]:
        """加载全局配置文件"""
        try:
            if self.GLOBAL_CONFIG_FILE.exists():
                with open(self.GLOBAL_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Failed to load global config: {e}")
        return None

    def _load_project_config(self) -> Optional[Dict[str, Any]]:
        """加载项目配置文件"""
        try:
            if self.project_config_file.exists():
                with open(self.project_config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Failed to load project config: {e}")
        return None

    def _merge_config(self, base_config: GlobalConfig, override_dict: Dict[str, Any]) -> GlobalConfig:
        """合并配置，override_dict中的值会覆盖base_config中的值"""
        # 转换为字典进行合并
        base_dict = asdict(base_config)
        merged_dict = self._deep_merge_dict(base_dict, override_dict)

        # 重新构造配置对象
        try:
            return GlobalConfig(
                plane=PlaneConfig(**merged_dict.get('plane', {})),
                cache=CacheConfig(**merged_dict.get('cache', {})),
                logging=LoggingConfig(**merged_dict.get('logging', {})),
                template=TemplateConfig(**merged_dict.get('template', {})),
                filter=FilterConfig(**merged_dict.get('filter', {})),
                report=ReportConfig(**merged_dict.get('report', {})),
                user=UserConfig(**merged_dict.get('user', {})),
            )
        except Exception as e:
            self.logger.error(f"Failed to merge config: {e}")
            return base_config

    def _deep_merge_dict(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并字典"""
        result = deepcopy(base)

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge_dict(result[key], value)
            else:
                result[key] = value

        return result

    def _apply_env_vars(self, config: GlobalConfig) -> GlobalConfig:
        """应用环境变量覆盖配置"""
        env_mappings = {
            # 兼容 .env 常用变量名
            'PLANE_BASE_URL': ('plane', 'base_url'),
            'PLANE_API_KEY': ('plane', 'api_key'),
            'PLANE_WORKSPACE': ('plane', 'workspace_slug'),
            'MY_EMAIL': ('user', 'email'),
            # 兼容带前缀变量名
            f'{self.ENV_PREFIX}PLANE_BASE_URL': ('plane', 'base_url'),
            f'{self.ENV_PREFIX}PLANE_API_KEY': ('plane', 'api_key'),
            f'{self.ENV_PREFIX}PLANE_WORKSPACE_SLUG': ('plane', 'workspace_slug'),
            f'{self.ENV_PREFIX}USER_EMAIL': ('user', 'email'),
            f'{self.ENV_PREFIX}CACHE_ENABLED': ('cache', 'enabled'),
            f'{self.ENV_PREFIX}CACHE_DIR': ('cache', 'cache_dir'),
            f'{self.ENV_PREFIX}CACHE_TTL_SECONDS': ('cache', 'ttl_seconds'),
            f'{self.ENV_PREFIX}LOG_LEVEL': ('logging', 'level'),
            f'{self.ENV_PREFIX}LOG_FILE': ('logging', 'file_path'),
            f'{self.ENV_PREFIX}TEMPLATE_DIR': ('template', 'template_dir'),
            f'{self.ENV_PREFIX}OUTPUT_DIR': ('report', 'output_dir'),
        }

        config_dict = asdict(config)

        for env_var, (section, key) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # 类型转换
                if key in ['enabled']:
                    value = value.lower() in ('true', '1', 'yes', 'on')
                elif key in ['ttl_seconds', 'max_size_mb', 'max_file_size_mb', 'backup_count', 'max_results']:
                    try:
                        value = int(value)
                    except ValueError:
                        self.logger.warning(f"Invalid integer value for {env_var}: {value}")
                        continue

                if section in config_dict:
                    config_dict[section][key] = value

        # 重新构造配置对象
        try:
            return GlobalConfig(
                plane=PlaneConfig(**config_dict['plane']),
                cache=CacheConfig(**config_dict['cache']),
                logging=LoggingConfig(**config_dict['logging']),
                template=TemplateConfig(**config_dict['template']),
                filter=FilterConfig(**config_dict['filter']),
                report=ReportConfig(**config_dict['report']),
                user=UserConfig(**config_dict['user']),
            )
        except Exception as e:
            self.logger.error(f"Failed to apply environment variables: {e}")
            return config

    def _ensure_directories(self):
        """确保必要的目录存在"""
        directories = [
            self.GLOBAL_CONFIG_DIR,
            Path(self._config.cache.cache_dir),
            Path(self._config.template.template_dir),
            Path(self._config.report.output_dir),
            Path(self._config.logging.file_path).parent,
        ]

        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                self.logger.warning(f"Failed to create directory {directory}: {e}")

    def get_config(self) -> GlobalConfig:
        """获取当前配置"""
        return self._config

    def get_plane_config(self) -> PlaneConfig:
        """获取Plane连接配置"""
        return self._config.plane

    def get_cache_config(self) -> CacheConfig:
        """获取缓存配置"""
        return self._config.cache

    def get_logging_config(self) -> LoggingConfig:
        """获取日志配置"""
        return self._config.logging

    def get_template_config(self) -> TemplateConfig:
        """获取模板配置"""
        return self._config.template

    def get_filter_config(self) -> FilterConfig:
        """获取过滤配置"""
        return self._config.filter

    def get_report_config(self) -> ReportConfig:
        """获取报告配置"""
        return self._config.report

    def save_global_config(self, config: Optional[GlobalConfig] = None):
        """保存全局配置到文件"""
        if config is None:
            config = self._config

        try:
            self.GLOBAL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)

            config_dict = asdict(config)
            with open(self.GLOBAL_CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Global config saved to {self.GLOBAL_CONFIG_FILE}")
        except Exception as e:
            self.logger.error(f"Failed to save global config: {e}")
            raise

    def save_project_config(self, config: Optional[Dict[str, Any]] = None):
        """保存项目配置到文件"""
        if config is None:
            # 只保存与全局配置不同的部分
            config = self._get_project_specific_config()

        try:
            with open(self.project_config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Project config saved to {self.project_config_file}")
        except Exception as e:
            self.logger.error(f"Failed to save project config: {e}")
            raise

    def _get_project_specific_config(self) -> Dict[str, Any]:
        """获取项目特定的配置（与全局配置的差异）"""
        # 这里可以实现更复杂的逻辑来确定哪些配置是项目特定的
        # 目前返回空字典，表示没有项目特定配置
        return {}

    def update_config(self, section: str, key: str, value: Any, save_global: bool = False):
        """更新配置值"""
        config_dict = asdict(self._config)

        if section in config_dict and key in config_dict[section]:
            config_dict[section][key] = value

            # 重新构造配置对象
            try:
                self._config = GlobalConfig(
                    plane=PlaneConfig(**config_dict['plane']),
                    cache=CacheConfig(**config_dict['cache']),
                    logging=LoggingConfig(**config_dict['logging']),
                    template=TemplateConfig(**config_dict['template']),
                    filter=FilterConfig(**config_dict['filter']),
                    report=ReportConfig(**config_dict['report']),
                    user=UserConfig(**config_dict['user']),
                )

                if save_global:
                    self.save_global_config()

                self.logger.info(f"Updated config: {section}.{key} = {value}")
            except Exception as e:
                self.logger.error(f"Failed to update config: {e}")
                raise
        else:
            raise ValueError(f"Invalid config section or key: {section}.{key}")

    def validate_config(self) -> List[str]:
        """验证配置，返回错误列表"""
        errors = []

        # 验证Plane配置
        if not self._config.plane.base_url:
            errors.append("Plane base_url is required")
        if not self._config.plane.api_key:
            errors.append("Plane api_key is required")
        if not self._config.plane.workspace_slug:
            errors.append("Plane workspace_slug is required")

        # 验证路径
        paths_to_check = [
            ('cache.cache_dir', self._config.cache.cache_dir),
            ('template.template_dir', self._config.template.template_dir),
            ('report.output_dir', self._config.report.output_dir),
        ]

        for path_name, path_value in paths_to_check:
            if path_value:
                path_obj = Path(path_value)
                if not path_obj.parent.exists():
                    errors.append(f"Parent directory for {path_name} does not exist: {path_obj.parent}")

        # 验证数值范围
        if self._config.cache.ttl_seconds <= 0:
            errors.append("cache.ttl_seconds must be positive")
        if self._config.cache.max_size_mb <= 0:
            errors.append("cache.max_size_mb must be positive")
        if self._config.filter.max_results <= 0:
            errors.append("filter.max_results must be positive")

        # 验证日志级别
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self._config.logging.level.upper() not in valid_log_levels:
            errors.append(f"logging.level must be one of: {valid_log_levels}")

        return errors

    def reload_config(self):
        """重新加载配置"""
        self._config = self._load_config()
        self._ensure_directories()
        self.logger.info("Configuration reloaded")

    def get_config_summary(self) -> str:
        """获取配置摘要信息"""
        summary = []
        summary.append("=== Plane Skills Configuration Summary ===")
        summary.append(f"Global config: {self.GLOBAL_CONFIG_FILE}")
        summary.append(f"Project config: {self.project_config_file}")
        summary.append(f"Project dir: {self.project_dir}")
        summary.append("")

        summary.append("Plane Configuration:")
        summary.append(f"  Base URL: {self._config.plane.base_url or 'Not set'}")
        summary.append(f"  API Key: {'Set' if self._config.plane.api_key else 'Not set'}")
        summary.append(f"  Workspace: {self._config.plane.workspace_slug or 'Not set'}")
        summary.append(f"  User Email: {self._config.user.email or 'Not set'}")
        summary.append("")

        summary.append("Cache Configuration:")
        summary.append(f"  Enabled: {self._config.cache.enabled}")
        summary.append(f"  Directory: {self._config.cache.cache_dir}")
        summary.append(f"  TTL: {self._config.cache.ttl_seconds}s")
        summary.append("")

        summary.append("Logging Configuration:")
        summary.append(f"  Level: {self._config.logging.level}")
        summary.append(f"  File: {self._config.logging.file_path}")
        summary.append("")

        # 验证配置
        errors = self.validate_config()
        if errors:
            summary.append("Configuration Errors:")
            for error in errors:
                summary.append(f"  - {error}")
        else:
            summary.append("Configuration: Valid")

        return "\n".join(summary)


# 全局配置管理器实例
_config_manager = None


def get_config_manager(project_dir: Optional[Union[str, Path]] = None) -> ConfigManager:
    """获取配置管理器单例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(project_dir)
    return _config_manager


def get_config() -> GlobalConfig:
    """获取当前配置的便捷函数"""
    return get_config_manager().get_config()


def run_interactive_auth_setup(
    project_dir: Optional[Union[str, Path]] = None,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    workspace: Optional[str] = None,
    email: Optional[str] = None,
    non_interactive: bool = False,
):
    """首次使用认证配置向导，写入项目 .env（支持交互与非交互模式）。"""
    project_path = Path(project_dir) if project_dir else Path.cwd()
    env_path = project_path / ".env"

    if not non_interactive:
        print("=== Plane Sync 首次认证向导 ===")
        print(f"项目目录: {project_path}")
        print("")
        print("请输入 Plane 连接信息（回车可保留当前值）")

    existing = {}
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            existing[key.strip()] = value.strip().strip('"').strip("'")

    def ask(
        name: str,
        prompt: str,
        supplied: Optional[str] = None,
        secret: bool = False,
        default: str = "",
        required: bool = False,
    ) -> str:
        current = existing.get(name, default)
        if supplied is not None and supplied.strip():
            return supplied.strip()

        if non_interactive:
            if required and not current:
                raise RuntimeError(
                    f"{name} is required in non-interactive mode. "
                    f"Use --{name.lower().replace('_', '-')} or set it in {env_path}."
                )
            return current

        if not sys.stdin.isatty():
            raise RuntimeError(
                "Interactive setup requires a TTY. "
                "Use --non-interactive with --base-url --api-key --workspace and optional --email."
            )

        label = f"{prompt} [{current}]:" if current else f"{prompt}:"
        try:
            if secret:
                value = getpass.getpass(label + " ")
            else:
                value = input(label + " ")
        except EOFError as e:
            raise RuntimeError(
                "Input stream closed during interactive setup. "
                "Use --non-interactive mode for AI/CI execution."
            ) from e

        value = value.strip()
        result = value if value else current
        if required and not result:
            raise RuntimeError(f"{name} is required.")
        return result

    base_url = ask("PLANE_BASE_URL", "Plane Base URL", supplied=base_url, required=True)
    api_key = ask("PLANE_API_KEY", "Plane API Key", supplied=api_key, secret=True, required=True)
    workspace = ask("PLANE_WORKSPACE", "Plane Workspace Slug", supplied=workspace, required=True)
    email = ask("MY_EMAIL", "Your Email (optional)", supplied=email)

    lines = [
        f'PLANE_BASE_URL="{base_url}"',
        f'PLANE_API_KEY="{api_key}"',
        f'PLANE_WORKSPACE="{workspace}"',
        f'MY_EMAIL="{email}"' if email else 'MY_EMAIL=""',
    ]

    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if not non_interactive:
        print("")
    print(f"✅ 已写入: {env_path}")
    print("下一步可运行: python3 verify_setup.py")
    return env_path


if __name__ == "__main__":
    # 测试代码
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Plane Skills configuration manager")
    parser.add_argument(
        "--init-auth",
        action="store_true",
        help="Run auth setup and write project .env",
    )
    parser.add_argument(
        "--project-dir",
        help="Target project directory (default: current directory)",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Do not prompt for input; require values from flags or existing .env",
    )
    parser.add_argument("--base-url", help="Plane base URL for auth setup")
    parser.add_argument("--api-key", help="Plane API key for auth setup")
    parser.add_argument("--workspace", help="Plane workspace slug for auth setup")
    parser.add_argument("--email", help="User email for --my-tasks support")
    args = parser.parse_args()

    if any([args.base_url, args.api_key, args.workspace, args.email, args.non_interactive]) and not args.init_auth:
        parser.error("--base-url/--api-key/--workspace/--email/--non-interactive require --init-auth")

    if args.init_auth:
        run_interactive_auth_setup(
            project_dir=args.project_dir,
            base_url=args.base_url,
            api_key=args.api_key,
            workspace=args.workspace,
            email=args.email,
            non_interactive=args.non_interactive,
        )
        sys.exit(0)

    if args.project_dir:
        # project-dir is only meaningful for init-auth to avoid confusion.
        parser.error("--project-dir requires --init-auth")

    # 设置日志
    logging.basicConfig(level=logging.INFO)

    # 创建配置管理器
    config_manager = ConfigManager()

    # 打印配置摘要
    print(config_manager.get_config_summary())

    # 验证配置
    errors = config_manager.validate_config()
    if errors:
        print("\nConfiguration errors found:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("\nConfiguration is valid!")
