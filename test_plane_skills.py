#!/usr/bin/env python3
"""Lightweight smoke tests for core plane-sync functionality."""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from textwrap import dedent

# Ensure local imports work when running as a script.
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_imports() -> bool:
    print("🧪 测试模块导入...")
    try:
        from plane_skills import plane_sync_skill, sync_my_tasks, sync_high_priority_tasks  # noqa: F401
        from plane_skills import ConfigManager, CacheManager, TaskFilter, TemplateEngine  # noqa: F401
        print("✅ 模块导入成功")
        return True
    except Exception as exc:
        print(f"❌ 模块导入失败: {exc}")
        return False


def test_argument_parsing() -> bool:
    print("\n🧪 测试参数解析...")
    try:
        from plane_skills.plane_sync_skill import parse_skill_args

        args = parse_skill_args("MOBILE --my-tasks --priority high,urgent --limit 10")
        assert args["project_id"] == "MOBILE"
        assert args["my_tasks"] is True
        assert args["priority"] == "high,urgent"
        assert args["limit"] == 10

        empty = parse_skill_args("")
        assert empty == {}
        print("✅ 参数解析通过")
        return True
    except Exception as exc:
        print(f"❌ 参数解析失败: {exc}")
        return False


def test_env_loading_from_dotenv() -> bool:
    print("\n🧪 测试 .env 自动加载...")
    try:
        from plane_skills.config_manager import ConfigManager

        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text(
                dedent(
                    """
                    PLANE_BASE_URL="https://plane.demo.com"
                    PLANE_API_KEY="plane_demo_key"
                    PLANE_WORKSPACE="demo-workspace"
                    MY_EMAIL="demo@example.com"
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            cfg = ConfigManager(project_dir=temp_dir).get_config()
            assert cfg.plane.base_url == "https://plane.demo.com"
            assert cfg.plane.api_key == "plane_demo_key"
            assert cfg.plane.workspace_slug == "demo-workspace"
            assert cfg.user.email == "demo@example.com"

        print("✅ .env 自动加载通过")
        return True
    except Exception as exc:
        print(f"❌ .env 自动加载失败: {exc}")
        return False


def test_interactive_auth_setup() -> bool:
    print("\n🧪 测试交互式认证向导...")
    try:
        from plane_skills.config_manager import run_interactive_auth_setup

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("builtins.input", side_effect=[
                "https://plane.demo.com",  # base url
                "demo-workspace",          # workspace
                "demo@example.com",        # email
            ]), patch("getpass.getpass", return_value="plane_demo_key"):
                run_interactive_auth_setup(project_dir=temp_dir)

            env_path = Path(temp_dir) / ".env"
            content = env_path.read_text(encoding="utf-8")
            assert 'PLANE_BASE_URL="https://plane.demo.com"' in content
            assert 'PLANE_API_KEY="plane_demo_key"' in content
            assert 'PLANE_WORKSPACE="demo-workspace"' in content
            assert 'MY_EMAIL="demo@example.com"' in content

        print("✅ 交互式认证向导通过")
        return True
    except Exception as exc:
        print(f"❌ 交互式认证向导失败: {exc}")
        return False


def test_template_render() -> bool:
    print("\n🧪 测试模板渲染...")
    try:
        from plane_skills.template_engine import TemplateEngine

        tasks = [
            {"name": "A", "priority": "high", "state": {"name": "Todo"}, "assignees": []},
            {"name": "B", "priority": "low", "state": {"name": "Done"}, "assignees": []},
        ]
        engine = TemplateEngine()
        output = engine.render("brief", tasks, "测试项目")
        assert "测试项目" in output
        assert "A" in output
        assert "B" in output
        print("✅ 模板渲染通过")
        return True
    except Exception as exc:
        print(f"❌ 模板渲染失败: {exc}")
        return False


def test_integration_with_mocks() -> bool:
    print("\n🧪 测试主流程（Mock）...")
    try:
        from plane_skills import plane_sync_skill

        with patch("plane_skills.plane_sync_skill.ConfigManager") as mock_config_mgr, \
             patch("plane_skills.plane_sync_skill.PlaneClient") as mock_client_cls, \
             patch("plane_skills.plane_sync_skill.get_cache_manager"):

            mock_config = Mock()
            mock_config.plane.base_url = "https://test.example.com"
            mock_config.plane.api_key = "test-key"
            mock_config.plane.workspace_slug = "workspace"
            mock_config.user.email = "test@example.com"

            mock_config_mgr.return_value.get_config.return_value = mock_config
            mock_config_mgr.return_value.validate_config.return_value = []

            mock_client = Mock()
            mock_client.list_projects.return_value = [
                {"id": "p1", "identifier": "TEST", "name": "测试项目"}
            ]
            mock_client.list_project_issues.return_value = [
                {"id": "i1", "name": "测试任务", "priority": "high", "state": {"name": "Todo"}, "assignees": []}
            ]
            mock_client_cls.return_value = mock_client

            with tempfile.TemporaryDirectory() as temp_dir:
                out = os.path.join(temp_dir, "plane.md")
                result = plane_sync_skill(project_id="TEST", template="brief", output=out)
                assert "✅ Plane任务同步完成" in result
                assert os.path.exists(out)

        print("✅ 主流程（Mock）通过")
        return True
    except Exception as exc:
        print(f"❌ 主流程（Mock）失败: {exc}")
        return False


def run_all_tests() -> bool:
    print("🚀 运行 Plane Skills 精简测试...\n")
    tests = [
        test_imports,
        test_argument_parsing,
        test_env_loading_from_dotenv,
        test_interactive_auth_setup,
        test_template_render,
        test_integration_with_mocks,
    ]

    passed = 0
    failed = 0

    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1

    print("\n📊 测试结果")
    print(f"  ✅ 通过: {passed}")
    print(f"  ❌ 失败: {failed}")

    if failed == 0:
        print("\n🎉 所有精简测试通过。")
        return True
    print("\n⚠️ 存在失败项，请检查输出。")
    return False


if __name__ == "__main__":
    ok = run_all_tests()
    sys.exit(0 if ok else 1)
