#!/usr/bin/env python3
"""
Plane Skills 快速验证脚本

验证核心功能是否正常工作
"""

import re
import sys
import argparse
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_dependencies():
    """检查依赖项"""
    print("🔍 检查依赖项...")

    required_modules = [
        ('requests', 'requests'),
        ('tqdm', 'tqdm'),
        ('colorama', 'colorama')
    ]
    missing = []

    for package_name, import_name in required_modules:
        try:
            __import__(import_name)
            print(f"  ✅ {package_name}")
        except ImportError:
            missing.append(package_name)
            print(f"  ❌ {package_name}")

    if missing:
        print(f"\n⚠️  缺少依赖项: {', '.join(missing)}")
        print("请运行: ./scripts/run-verify.sh（自动引导运行时环境）")
        return False

    try:
        __import__('dotenv')
        print("  ✅ python-dotenv (可选)")
    except ImportError:
        print("  ℹ️  python-dotenv 未安装（将使用内置 .env 解析器）")

    return True

def check_modules():
    """检查核心模块"""
    print("\n🧪 检查核心模块...")

    try:
        from plane_skills import plane_sync_skill
        print("  ✅ plane_sync_skill")

        from plane_skills.config_manager import ConfigManager
        print("  ✅ ConfigManager")

        from plane_skills.cache_manager import CacheManager
        print("  ✅ CacheManager")

        from plane_skills.task_filter import TaskFilter
        print("  ✅ TaskFilter")

        from plane_skills.template_engine import TemplateEngine
        print("  ✅ TemplateEngine")

        from plane_skills.plane_client import PlaneClient
        print("  ✅ PlaneClient")

        return True

    except ImportError as e:
        print(f"  ❌ 模块导入失败: {e}")
        return False

def check_config(project_dir: Path):
    """检查配置文件"""
    print("\n⚙️  检查配置...")

    env_file = project_dir / '.env'
    env_example = project_dir / '.env.example'
    fallback_env_example = project_root / '.env.example'

    if env_example.exists():
        print("  ✅ .env.example 存在")
    elif fallback_env_example.exists():
        print(f"  ✅ .env.example 存在（技能目录）: {fallback_env_example}")
    else:
        print("  ❌ .env.example 文件不存在")
        return False

    if not env_file.exists():
        print(f"  ⚠️  .env 文件不存在，请在 {project_dir} 下创建并配置")
        return False
    else:
        print(f"  ✅ .env 文件存在: {env_file}")

    # 通过 ConfigManager 统一读取（支持 python-dotenv 缺失时的兜底解析器）
    from plane_skills.config_manager import ConfigManager
    cfg = ConfigManager(project_dir=project_dir).get_config()

    missing_vars = []
    checks = [
        ("PLANE_BASE_URL", cfg.plane.base_url),
        ("PLANE_API_KEY", cfg.plane.api_key),
        ("PLANE_WORKSPACE", cfg.plane.workspace_slug),
    ]

    for key, value in checks:
        if not value:
            missing_vars.append(key)
            print(f"  ❌ {key} 未设置")
        else:
            print(f"  ✅ {key} 已设置")

    if missing_vars:
        print(f"\n⚠️  请在 .env 文件中设置: {', '.join(missing_vars)}")
        return False

    return True

def check_templates():
    """检查模板文件"""
    print("\n📄 检查模板文件...")

    template_dir = Path('plane_skills/templates')
    if not template_dir.exists():
        print("  ❌ 模板目录不存在")
        return False

    templates = ['ai-context.md', 'brief.md', 'standup.md', 'development.md']
    all_exist = True

    for template in templates:
        template_path = template_dir / template
        if template_path.exists():
            print(f"  ✅ {template}")
        else:
            print(f"  ❌ {template}")
            all_exist = False

    return all_exist

def check_skills_file():
    """检查 Skills 定义文件"""
    print("\n🎯 检查 Skills 定义...")

    skill_file = Path('SKILL.md')
    if not skill_file.exists():
        print("  ❌ SKILL.md 不存在")
        return False

    content = skill_file.read_text(encoding='utf-8')
    if not content.startswith('---'):
        print("  ❌ SKILL.md 缺少 YAML frontmatter")
        return False

    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        print("  ❌ SKILL.md frontmatter 格式无效")
        return False

    frontmatter = match.group(1)
    if "name:" not in frontmatter or "description:" not in frontmatter:
        print("  ❌ SKILL.md frontmatter 缺少 name 或 description")
        return False

    print("  ✅ SKILL.md 存在且 frontmatter 有效")
    return True

def test_basic_functionality():
    """测试基本功能"""
    print("\n🧪 测试基本功能...")

    try:
        from plane_skills.plane_sync_skill import parse_skill_args

        # 测试参数解析
        args = parse_skill_args("MOBILE --my-tasks --priority high")
        if args.get('project_id') == 'MOBILE' and args.get('my_tasks') == True:
            print("  ✅ 参数解析正常")
        else:
            print("  ❌ 参数解析异常")
            return False

        # 测试配置管理器初始化
        from plane_skills.config_manager import ConfigManager
        config_manager = ConfigManager()
        print("  ✅ 配置管理器初始化正常")

        # 测试缓存管理器初始化
        from plane_skills.cache_manager import get_cache_manager
        cache_manager = get_cache_manager()
        print("  ✅ 缓存管理器初始化正常")

        return True

    except Exception as e:
        print(f"  ❌ 功能测试失败: {e}")
        return False

def main(project_dir: Path):
    """主函数"""
    print("🚀 Plane Skills 快速验证\n")
    print(f"📂 项目目录: {project_dir}\n")

    checks = [
        ("依赖项检查", check_dependencies),
        ("模块检查", check_modules),
        ("配置检查", lambda: check_config(project_dir)),
        ("模板检查", check_templates),
        ("Skills文件检查", check_skills_file),
        ("基本功能测试", test_basic_functionality)
    ]

    passed = 0
    total = len(checks)

    for name, check_func in checks:
        try:
            if check_func():
                passed += 1
            else:
                print(f"\n❌ {name} 失败")
        except Exception as e:
            print(f"\n❌ {name} 异常: {e}")

    print(f"\n📊 验证结果: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有检查通过！Plane Skills 已准备就绪。")
        print("\n📖 使用方法:")
        print("  在 Claude Code 中运行: /plane-sync PROJECT_ID")
        print("  查看详细文档: cat USAGE.md")
        return True
    else:
        print(f"\n⚠️  有 {total - passed} 项检查失败，请修复后重试。")
        print("\n🔧 常见解决方案:")
        print("  1. 自动引导运行时: ./scripts/run-verify.sh")
        print("  2. 配置环境: cp .env.example .env && 编辑 .env")
        print("  3. 检查文件完整性")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plane Skills quick setup verification")
    parser.add_argument(
        "--project-dir",
        default=str(Path.cwd()),
        help="Target project directory for .env validation (default: current directory)",
    )
    args = parser.parse_args()

    target_dir = Path(args.project_dir).expanduser().resolve()
    success = main(target_dir)
    sys.exit(0 if success else 1)
