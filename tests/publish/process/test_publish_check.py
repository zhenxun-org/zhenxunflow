# ruff: noqa: ASYNC101

import json
from pathlib import Path
from typing import Any, cast

import httpx
from githubkit import Response
from githubkit.exception import RequestFailed
from nonebot import get_adapter
from nonebot.adapters.github import (
    Adapter,
    GitHubBot,
    IssueCommentCreated,
    IssuesOpened,
)
from nonebot.adapters.github.config import GitHubApp
from nonebug import App
from pytest_mock import MockerFixture
from respx import MockRouter

from tests.publish.utils import generate_issue_body_plugin


def check_json_data(file: Path, data: Any) -> None:
    with open(file) as f:
        assert json.load(f) == data


async def test_process_publish_check(
    app: App, mocker: MockerFixture, mocked_api: MockRouter, tmp_path: Path
) -> None:
    """测试一个正常的发布流程"""
    from src.plugins.publish import publish_check_matcher
    from src.plugins.publish.config import PluginTestMetadata, plugin_config

    mock_subprocess_run = mocker.patch(
        "subprocess.run", side_effect=lambda *args, **kwargs: mocker.MagicMock()
    )

    mock_installation = mocker.MagicMock()
    mock_installation.id = 123
    mock_installation_resp = mocker.MagicMock()
    mock_installation_resp.parsed_data = mock_installation

    mock_issue = mocker.MagicMock()
    mock_issue.pull_request = None
    mock_issue.title = "Plugin: test"
    mock_issue.number = 80
    mock_issue.state = "open"
    mock_issue.body = generate_issue_body_plugin(plugin_name="test")
    mock_issue.user.login = "test"

    mock_event = mocker.MagicMock()
    mock_event.issue = mock_issue

    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    mock_comment = mocker.MagicMock()
    mock_comment.body = "Plugin: test"
    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    mock_pull = mocker.MagicMock()
    mock_pull.number = 2
    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = mock_pull
    plugin_config.plugin_test_metadata = PluginTestMetadata(
        description="description",
        usage="usage",
        plugin_type="NORMAL",
        version="0.1",
    )
    plugin_config.plugin_test_result = True

    with open(tmp_path / "plugins.json", "w") as f:
        json.dump({}, f)

    check_json_data(plugin_config.input_config.plugin_path, {})

    async with app.test_matcher(publish_check_matcher) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=GitHubBot,
            adapter=adapter,
            self_id=GitHubApp(app_id="1", private_key="1"),  # type: ignore
        )
        bot = cast(GitHubBot, bot)
        event_path = Path(__file__).parent.parent / "events" / "issue-open.json"
        event = Adapter.payload_to_event("1", "issues", event_path.read_bytes())
        assert isinstance(event, IssuesOpened)

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            {"owner": "AkashiCoin", "repo": "action-test"},
            mock_installation_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_get",
            {"owner": "AkashiCoin", "repo": "action-test", "issue_number": 80},
            mock_issues_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "AkashiCoin", "repo": "action-test", "issue_number": 80},
            mock_list_comments_resp,
        )
        ctx.should_call_api(
            "rest.pulls.async_create",
            {
                "owner": "AkashiCoin",
                "repo": "action-test",
                "title": "Plugin: test",
                "body": "resolve #80",
                "base": "master",
                "head": "publish/issue80",
            },
            mock_pulls_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_add_labels",
            {
                "owner": "AkashiCoin",
                "repo": "action-test",
                "issue_number": 2,
                "labels": ["Plugin"],
            },
            True,
        )
        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "AkashiCoin", "repo": "action-test", "issue_number": 80},
            mock_list_comments_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_create_comment",
            {
                "owner": "AkashiCoin",
                "repo": "action-test",
                "issue_number": 80,
                "body": """# 📃 商店发布检查结果\n\n> Plugin: test\n\n**✅ 所有测试通过，一切准备就绪！**\n\n\n<details>\n<summary>详情</summary>\n<pre><code><li>✅ 项目 <a href="https://github.com/author/module/">https://github.com/author/module</a> GitHub仓库存在。</li><li>✅ version: 0.1。</li><li>✅ 插件类型: 普通插件。</li><li>✅ 插件 <a href="https://github.com/owner/repo/actions/runs/123456">加载测试</a> 通过。</li></code></pre>\n</details>\n\n---\n\n💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。\n💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。\n\n\n💪 Powered by [ZHENXUNFLOW](https://github.com/zhenxun-org/zhenxunflow)\n<!-- ZHENXUNFLOW -->\n""",
            },
            True,
        )

        ctx.receive_event(bot, event)

    # 测试 git 命令
    mock_subprocess_run.assert_has_calls(
        [
            mocker.call(
                ["git", "config", "--global", "safe.directory", "*"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                ["pre-commit", "install", "--install-hooks"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                ["git", "switch", "-C", "publish/issue80"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                ["git", "config", "--global", "user.name", "test"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                [
                    "git",
                    "config",
                    "--global",
                    "user.email",
                    "test@users.noreply.github.com",
                ],
                check=True,
                capture_output=True,
            ),
            mocker.call(["git", "add", "-A"], check=True, capture_output=True),
            mocker.call(
                ["git", "commit", "-m", ":beers: publish plugin test (#80)"],
                check=True,
                capture_output=True,
            ),
            mocker.call(["git", "fetch", "origin"], check=True, capture_output=True),
            mocker.call(
                ["git", "diff", "origin/publish/issue80", "publish/issue80"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                ["git", "push", "origin", "publish/issue80", "-f"],
                check=True,
                capture_output=True,
            ),
        ]  # type: ignore
    )

    # 检查文件是否正确
    check_json_data(
        plugin_config.input_config.plugin_path,
        {
            "test": {
                "module": "module",
                "module_path": "module_path",
                "description": "description",
                "usage": "usage",
                "author": "test",
                "version": "0.1",
                "plugin_type": "NORMAL",
                "is_dir": True,
                "github_url": "https://github.com/author/module",
            }
        },
    )

    assert mocked_api["github_url"].called


async def test_edit_title(
    app: App, mocker: MockerFixture, mocked_api: MockRouter, tmp_path: Path
) -> None:
    """测试编辑标题"""
    from src.plugins.publish import publish_check_matcher
    from src.plugins.publish.config import PluginTestMetadata, plugin_config

    mock_subprocess_run = mocker.patch(
        "subprocess.run", side_effect=lambda *args, **kwargs: mocker.MagicMock()
    )

    mock_installation = mocker.MagicMock()
    mock_installation.id = 123
    mock_installation_resp = mocker.MagicMock()
    mock_installation_resp.parsed_data = mock_installation

    mock_issue = mocker.MagicMock()
    mock_issue.pull_request = None
    mock_issue.title = "Plugin: test"
    mock_issue.number = 80
    mock_issue.state = "open"
    mock_issue.body = generate_issue_body_plugin(plugin_name="test1")
    mock_issue.user.login = "test"

    mock_event = mocker.MagicMock()
    mock_event.issue = mock_issue

    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    mock_comment = mocker.MagicMock()
    mock_comment.body = "Plugin: test"
    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    mock_pull = mocker.MagicMock()
    mock_pull.number = 2
    mock_pull.draft = False
    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = [mock_pull]
    plugin_config.plugin_test_metadata = PluginTestMetadata(
        description="description",
        usage="usage",
        plugin_type="NORMAL",
        version="0.1",
    )
    plugin_config.plugin_test_result = True

    with open(tmp_path / "plugins.json", "w") as f:
        json.dump({}, f)

    check_json_data(plugin_config.input_config.plugin_path, {})

    async with app.test_matcher(publish_check_matcher) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=GitHubBot,
            adapter=adapter,
            self_id=GitHubApp(app_id="1", private_key="1"),  # type: ignore
        )
        bot = cast(GitHubBot, bot)
        event_path = Path(__file__).parent.parent / "events" / "issue-open.json"
        event = Adapter.payload_to_event("1", "issues", event_path.read_bytes())
        assert isinstance(event, IssuesOpened)

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            {"owner": "AkashiCoin", "repo": "action-test"},
            mock_installation_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_get",
            {"owner": "AkashiCoin", "repo": "action-test", "issue_number": 80},
            mock_issues_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "AkashiCoin", "repo": "action-test", "issue_number": 80},
            mock_list_comments_resp,
        )
        ctx.should_call_api(
            "rest.pulls.async_create",
            {
                "owner": "AkashiCoin",
                "repo": "action-test",
                "title": "Plugin: test1",
                "body": "resolve #80",
                "base": "master",
                "head": "publish/issue80",
            },
            exception=RequestFailed(
                Response(
                    httpx.Response(422, request=httpx.Request("test", "test")), None
                )
            ),
        )
        ctx.should_call_api(
            "rest.pulls.async_list",
            {
                "owner": "AkashiCoin",
                "repo": "action-test",
                "head": "AkashiCoin:publish/issue80",
            },
            mock_pulls_resp,
        )
        # 修改标题
        ctx.should_call_api(
            "rest.pulls.async_update",
            {
                "owner": "AkashiCoin",
                "repo": "action-test",
                "pull_number": 2,
                "title": "Plugin: test1",
            },
            True,
        )
        ctx.should_call_api(
            "rest.issues.async_update",
            {
                "owner": "AkashiCoin",
                "repo": "action-test",
                "issue_number": 80,
                "title": "Plugin: test1",
            },
            True,
        )
        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "AkashiCoin", "repo": "action-test", "issue_number": 80},
            mock_list_comments_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_create_comment",
            {
                "owner": "AkashiCoin",
                "repo": "action-test",
                "issue_number": 80,
                "body": """# 📃 商店发布检查结果\n\n> Plugin: test1\n\n**✅ 所有测试通过，一切准备就绪！**\n\n\n<details>\n<summary>详情</summary>\n<pre><code><li>✅ 项目 <a href="https://github.com/author/module/">https://github.com/author/module</a> GitHub仓库存在。</li><li>✅ version: 0.1。</li><li>✅ 插件类型: 普通插件。</li><li>✅ 插件 <a href="https://github.com/owner/repo/actions/runs/123456">加载测试</a> 通过。</li></code></pre>\n</details>\n\n---\n\n💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。\n💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。\n\n\n💪 Powered by [ZHENXUNFLOW](https://github.com/zhenxun-org/zhenxunflow)\n<!-- ZHENXUNFLOW -->\n""",
            },
            True,
        )

        ctx.receive_event(bot, event)

    # 测试 git 命令
    mock_subprocess_run.assert_has_calls(
        [
            mocker.call(
                ["git", "config", "--global", "safe.directory", "*"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                ["pre-commit", "install", "--install-hooks"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                ["git", "switch", "-C", "publish/issue80"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                ["git", "config", "--global", "user.name", "test"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                [
                    "git",
                    "config",
                    "--global",
                    "user.email",
                    "test@users.noreply.github.com",
                ],
                check=True,
                capture_output=True,
            ),
            mocker.call(["git", "add", "-A"], check=True, capture_output=True),
            mocker.call(
                ["git", "commit", "-m", ":beers: publish plugin test1 (#80)"],
                check=True,
                capture_output=True,
            ),
            mocker.call(["git", "fetch", "origin"], check=True, capture_output=True),
            mocker.call(
                ["git", "diff", "origin/publish/issue80", "publish/issue80"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                ["git", "push", "origin", "publish/issue80", "-f"],
                check=True,
                capture_output=True,
            ),
        ]  # type: ignore
    )

    # 检查文件是否正确
    check_json_data(
        plugin_config.input_config.plugin_path,
        {
            "test1": {
                "module": "module",
                "module_path": "module_path",
                "description": "description",
                "usage": "usage",
                "author": "test",
                "version": "0.1",
                "plugin_type": "NORMAL",
                "is_dir": True,
                "github_url": "https://github.com/author/module",
            }
        },
    )

    assert mocked_api["github_url"].called


async def test_edit_title_too_long(
    app: App, mocker: MockerFixture, mocked_api: MockRouter, tmp_path: Path
) -> None:
    """测试标题过长的情况"""
    from src.plugins.publish import publish_check_matcher
    from src.plugins.publish.config import PluginTestMetadata, plugin_config

    mock_subprocess_run = mocker.patch(
        "subprocess.run", side_effect=lambda *args, **kwargs: mocker.MagicMock()
    )

    mock_installation = mocker.MagicMock()
    mock_installation.id = 123
    mock_installation_resp = mocker.MagicMock()
    mock_installation_resp.parsed_data = mock_installation

    mock_issue = mocker.MagicMock()
    mock_issue.pull_request = None
    mock_issue.title = "Plugin: test"
    mock_issue.number = 80
    mock_issue.state = "open"
    mock_issue.body = generate_issue_body_plugin(
        plugin_name="looooooooooooooooooooooooooooooooooooooooooooooooooooooong"
    )
    mock_issue.user.login = "test"

    mock_event = mocker.MagicMock()
    mock_event.issue = mock_issue

    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    mock_comment = mocker.MagicMock()
    mock_comment.body = "Plugin: test"
    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = []
    plugin_config.plugin_test_metadata = PluginTestMetadata(
        description="description",
        usage="usage",
        plugin_type="NORMAL",
        version="0.1",
    )
    plugin_config.plugin_test_result = True

    with open(tmp_path / "plugins.json", "w") as f:
        json.dump({}, f)

    check_json_data(plugin_config.input_config.plugin_path, {})

    async with app.test_matcher(publish_check_matcher) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=GitHubBot,
            adapter=adapter,
            self_id=GitHubApp(app_id="1", private_key="1"),  # type: ignore
        )
        bot = cast(GitHubBot, bot)
        event_path = Path(__file__).parent.parent / "events" / "issue-open.json"
        event = Adapter.payload_to_event("1", "issues", event_path.read_bytes())
        assert isinstance(event, IssuesOpened)

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            {"owner": "AkashiCoin", "repo": "action-test"},
            mock_installation_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_get",
            {"owner": "AkashiCoin", "repo": "action-test", "issue_number": 80},
            mock_issues_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "AkashiCoin", "repo": "action-test", "issue_number": 80},
            mock_list_comments_resp,
        )
        ctx.should_call_api(
            "rest.pulls.async_list",
            {
                "owner": "AkashiCoin",
                "repo": "action-test",
                "head": "AkashiCoin:publish/issue80",
            },
            mock_pulls_resp,
        )
        # 修改标题
        ctx.should_call_api(
            "rest.issues.async_update",
            {
                "owner": "AkashiCoin",
                "repo": "action-test",
                "issue_number": 80,
                "title": "Plugin: looooooooooooooooooooooooooooooooooooooooooooooooo",
            },
            True,
        )
        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "AkashiCoin", "repo": "action-test", "issue_number": 80},
            mock_list_comments_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_create_comment",
            {
                "owner": "AkashiCoin",
                "repo": "action-test",
                "issue_number": 80,
                "body": """# 📃 商店发布检查结果\n\n> Plugin: looooooooooooooooooooooooooooooooooooooooooooooooooooooong\n\n**⚠️ 在发布检查过程中，我们发现以下问题：**\n\n<pre><code><li>⚠️ 名称: 字符过多。<dt>请确保其不超过 50 个字符。</dt></li></code></pre>\n\n<details>\n<summary>详情</summary>\n<pre><code><li>✅ 项目 <a href="https://github.com/author/module/">https://github.com/author/module</a> GitHub仓库存在。</li><li>✅ version: 0.1。</li><li>✅ 插件类型: 普通插件。</li><li>✅ 插件 <a href="https://github.com/owner/repo/actions/runs/123456">加载测试</a> 通过。</li></code></pre>\n</details>\n\n---\n\n💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。\n💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。\n\n\n💪 Powered by [ZHENXUNFLOW](https://github.com/zhenxun-org/zhenxunflow)\n<!-- ZHENXUNFLOW -->\n""",
            },
            True,
        )

        ctx.receive_event(bot, event)

    # 测试 git 命令
    mock_subprocess_run.assert_has_calls(
        [
            mocker.call(
                ["git", "config", "--global", "safe.directory", "*"],
                check=True,
                capture_output=True,
            )  # type: ignore
        ]
    )

    # 检查文件是否正确
    check_json_data(
        plugin_config.input_config.plugin_path,
        {},
    )

    assert mocked_api["github_url"].called


async def test_process_publish_check_not_pass(
    app: App, mocker: MockerFixture, mocked_api: MockRouter, tmp_path: Path
) -> None:
    """测试发布检查不通过的情况"""
    from src.plugins.publish import publish_check_matcher
    from src.plugins.publish.config import PluginTestMetadata, plugin_config

    mock_subprocess_run = mocker.patch(
        "subprocess.run", side_effect=lambda *args, **kwargs: mocker.MagicMock()
    )

    mock_installation = mocker.MagicMock()
    mock_installation.id = 123
    mock_installation_resp = mocker.MagicMock()
    mock_installation_resp.parsed_data = mock_installation

    mock_issue = mocker.MagicMock()
    mock_issue.pull_request = None
    mock_issue.title = "Plugin: test"
    mock_issue.number = 80
    mock_issue.state = "open"
    mock_issue.body = generate_issue_body_plugin(
        plugin_name="test", github_url="https://www.baidu.com"
    )
    mock_issue.user.login = "test"

    mock_event = mocker.MagicMock()
    mock_event.issue = mock_issue

    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = []

    mock_comment = mocker.MagicMock()
    mock_comment.body = "Plugin: test"
    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    plugin_config.plugin_test_metadata = PluginTestMetadata(
        description="description",
        usage="usage",
        plugin_type="NORMAL",
        version="0.1",
    )
    plugin_config.plugin_test_result = True

    with open(tmp_path / "plugins.json", "w") as f:
        json.dump({}, f)

    check_json_data(plugin_config.input_config.plugin_path, {})

    async with app.test_matcher(publish_check_matcher) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=GitHubBot,
            adapter=adapter,
            self_id=GitHubApp(app_id="1", private_key="1"),  # type: ignore
        )
        bot = cast(GitHubBot, bot)
        event_path = Path(__file__).parent.parent / "events" / "issue-open.json"
        event = Adapter.payload_to_event("1", "issues", event_path.read_bytes())
        assert isinstance(event, IssuesOpened)

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            {"owner": "AkashiCoin", "repo": "action-test"},
            mock_installation_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_get",
            {"owner": "AkashiCoin", "repo": "action-test", "issue_number": 80},
            mock_issues_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "AkashiCoin", "repo": "action-test", "issue_number": 80},
            mock_list_comments_resp,
        )
        ctx.should_call_api(
            "rest.pulls.async_list",
            {
                "owner": "AkashiCoin",
                "repo": "action-test",
                "head": "AkashiCoin:publish/issue80",
            },
            mock_pulls_resp,
        )
        # 检查是否可以复用评论
        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "AkashiCoin", "repo": "action-test", "issue_number": 80},
            mock_list_comments_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_create_comment",
            {
                "owner": "AkashiCoin",
                "repo": "action-test",
                "issue_number": 80,
                "body": """# 📃 商店发布检查结果\n\n> Plugin: test\n\n**⚠️ 在发布检查过程中，我们发现以下问题：**\n\n<pre><code><li>⚠️ 仓库地址: 项目主页无法访问</li></code></pre>\n\n<details>\n<summary>详情</summary>\n<pre><code><li>✅ version: 0.1。</li><li>✅ 插件类型: 普通插件。</li><li>✅ 插件 <a href="https://github.com/owner/repo/actions/runs/123456">加载测试</a> 通过。</li></code></pre>\n</details>\n\n---\n\n💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。\n💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。\n\n\n💪 Powered by [ZHENXUNFLOW](https://github.com/zhenxun-org/zhenxunflow)\n<!-- ZHENXUNFLOW -->\n""",
            },
            True,
        )

        ctx.receive_event(bot, event)

    # 测试 git 命令
    mock_subprocess_run.assert_has_calls(
        [
            mocker.call(
                ["git", "config", "--global", "safe.directory", "*"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                ["pre-commit", "install", "--install-hooks"],
                check=True,
                capture_output=True,
            ),
        ]  # type: ignore
    )

    # 检查文件是否正确
    check_json_data(
        plugin_config.input_config.plugin_path,
        {},
    )

    assert mocked_api["github_url_failed"].called


async def test_comment_at_pull_request(
    app: App, mocker: MockerFixture, mocked_api: MockRouter
) -> None:
    """测试在拉取请求下评论

    event.issue.pull_request 不为空
    """
    from src.plugins.publish import publish_check_matcher

    mock_subprocess_run = mocker.patch(
        "subprocess.run", side_effect=lambda *args, **kwargs: mocker.MagicMock()
    )

    async with app.test_matcher(publish_check_matcher) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=GitHubBot,
            adapter=adapter,
            self_id=GitHubApp(app_id="1", private_key="1"),  # type: ignore
        )
        bot = cast(GitHubBot, bot)
        event_path = Path(__file__).parent.parent / "events" / "pr-comment.json"
        event = Adapter.payload_to_event("1", "issue_comment", event_path.read_bytes())
        assert isinstance(event, IssueCommentCreated)

        ctx.receive_event(bot, event)

    assert mocked_api.calls == []
    mock_subprocess_run.assert_not_called()


async def test_issue_state_closed(
    app: App, mocker: MockerFixture, mocked_api: MockRouter
) -> None:
    """测试议题已关闭

    event.issue.state = "closed"
    """
    from src.plugins.publish import publish_check_matcher

    mock_subprocess_run = mocker.patch(
        "subprocess.run", side_effect=lambda *args, **kwargs: mocker.MagicMock()
    )

    mock_installation = mocker.MagicMock()
    mock_installation.id = 123
    mock_installation_resp = mocker.MagicMock()
    mock_installation_resp.parsed_data = mock_installation

    mock_issue = mocker.MagicMock()
    mock_issue.pull_request = None
    mock_issue.state = "closed"
    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    async with app.test_matcher(publish_check_matcher) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=GitHubBot,
            adapter=adapter,
            self_id=GitHubApp(app_id="1", private_key="1"),  # type: ignore
        )
        bot = cast(GitHubBot, bot)
        event_path = Path(__file__).parent.parent / "events" / "issue-open.json"
        event = Adapter.payload_to_event("1", "issues", event_path.read_bytes())
        assert isinstance(event, IssuesOpened)

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            {"owner": "AkashiCoin", "repo": "action-test"},
            mock_installation_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_get",
            {"owner": "AkashiCoin", "repo": "action-test", "issue_number": 80},
            mock_issues_resp,
        )

        ctx.receive_event(bot, event)

    assert mocked_api.calls == []
    mock_subprocess_run.assert_has_calls(
        [
            mocker.call(
                ["git", "config", "--global", "safe.directory", "*"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                ["pre-commit", "install", "--install-hooks"],
                check=True,
                capture_output=True,
            ),
        ]  # type: ignore
    )


async def test_not_publish_issue(
    app: App, mocker: MockerFixture, mocked_api: MockRouter
) -> None:
    """测试议题与发布无关

    议题的标签不是 "Bot/Adapter/Plugin"
    """
    from src.plugins.publish import publish_check_matcher

    mock_subprocess_run = mocker.patch(
        "subprocess.run", side_effect=lambda *args, **kwargs: mocker.MagicMock()
    )

    async with app.test_matcher(publish_check_matcher) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=GitHubBot,
            adapter=adapter,
            self_id=GitHubApp(app_id="1", private_key="1"),  # type: ignore
        )
        bot = cast(GitHubBot, bot)
        event_path = Path(__file__).parent.parent / "events" / "issue-open.json"
        event = Adapter.payload_to_event("1", "issues", event_path.read_bytes())
        assert isinstance(event, IssuesOpened)
        event.payload.issue.labels = []

        ctx.receive_event(bot, event)

    mock_subprocess_run.assert_not_called()


async def test_comment_by_self(
    app: App, mocker: MockerFixture, mocked_api: MockRouter
) -> None:
    """测试自己评论触发的情况"""
    from src.plugins.publish import publish_check_matcher

    mock_subprocess_run = mocker.patch(
        "subprocess.run", side_effect=lambda *args, **kwargs: mocker.MagicMock()
    )

    async with app.test_matcher(publish_check_matcher) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=GitHubBot,
            adapter=adapter,
            self_id=GitHubApp(app_id="1", private_key="1"),  # type: ignore
        )
        bot = cast(GitHubBot, bot)
        event_path = Path(__file__).parent.parent / "events" / "issue-comment-bot.json"
        event = Adapter.payload_to_event("1", "issue_comment", event_path.read_bytes())
        assert isinstance(event, IssueCommentCreated)

        ctx.receive_event(bot, event)

    mock_subprocess_run.assert_not_called()


async def test_convert_pull_request_to_draft(
    app: App, mocker: MockerFixture, mocked_api: MockRouter, tmp_path: Path
) -> None:
    """未通过时将拉取请求转换为草稿"""
    from src.plugins.publish import publish_check_matcher
    from src.plugins.publish.config import PluginTestMetadata, plugin_config

    mock_subprocess_run = mocker.patch(
        "subprocess.run", side_effect=lambda *args, **kwargs: mocker.MagicMock()
    )

    mock_installation = mocker.MagicMock()
    mock_installation.id = 123
    mock_installation_resp = mocker.MagicMock()
    mock_installation_resp.parsed_data = mock_installation

    mock_issue = mocker.MagicMock()
    mock_issue.pull_request = None
    mock_issue.title = "Plugin: test"
    mock_issue.number = 80
    mock_issue.state = "open"
    mock_issue.body = generate_issue_body_plugin(
        plugin_name="test", github_url="https://www.baidu.com"
    )
    mock_issue.user.login = "test"

    mock_event = mocker.MagicMock()
    mock_event.issue = mock_issue

    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    mock_pull = mocker.MagicMock()
    mock_pull.number = 2
    mock_pull.title = "Plugin: test"
    mock_pull.draft = False
    mock_pull.node_id = "123"
    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = [mock_pull]

    mock_comment = mocker.MagicMock()
    mock_comment.body = "Plugin: test"
    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    plugin_config.plugin_test_metadata = PluginTestMetadata(
        description="description",
        usage="usage",
        plugin_type="NORMAL",
        version="0.1",
    )
    plugin_config.plugin_test_result = True

    with open(tmp_path / "plugins.json", "w") as f:
        json.dump({}, f)

    check_json_data(plugin_config.input_config.plugin_path, {})

    async with app.test_matcher(publish_check_matcher) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=GitHubBot,
            adapter=adapter,
            self_id=GitHubApp(app_id="1", private_key="1"),  # type: ignore
        )
        bot = cast(GitHubBot, bot)
        event_path = Path(__file__).parent.parent / "events" / "issue-open.json"
        event = Adapter.payload_to_event("1", "issues", event_path.read_bytes())
        assert isinstance(event, IssuesOpened)

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            {"owner": "AkashiCoin", "repo": "action-test"},
            mock_installation_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_get",
            {"owner": "AkashiCoin", "repo": "action-test", "issue_number": 80},
            mock_issues_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "AkashiCoin", "repo": "action-test", "issue_number": 80},
            mock_list_comments_resp,
        )
        ctx.should_call_api(
            "rest.pulls.async_list",
            {
                "owner": "AkashiCoin",
                "repo": "action-test",
                "head": "AkashiCoin:publish/issue80",
            },
            mock_pulls_resp,
        )
        # 将拉取请求转换为草稿
        ctx.should_call_api(
            "async_graphql",
            {
                "query": "mutation convertPullRequestToDraft($pullRequestId: ID!) {\n                        convertPullRequestToDraft(input: {pullRequestId: $pullRequestId}) {\n                            clientMutationId\n                        }\n                    }",
                "variables": {"pullRequestId": "123"},
            },
            True,
        )
        # 检查是否可以复用评论
        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "AkashiCoin", "repo": "action-test", "issue_number": 80},
            mock_list_comments_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_create_comment",
            {
                "owner": "AkashiCoin",
                "repo": "action-test",
                "issue_number": 80,
                "body": """# 📃 商店发布检查结果\n\n> Plugin: test\n\n**⚠️ 在发布检查过程中，我们发现以下问题：**\n\n<pre><code><li>⚠️ 仓库地址: 项目主页无法访问</li></code></pre>\n\n<details>\n<summary>详情</summary>\n<pre><code><li>✅ version: 0.1。</li><li>✅ 插件类型: 普通插件。</li><li>✅ 插件 <a href="https://github.com/owner/repo/actions/runs/123456">加载测试</a> 通过。</li></code></pre>\n</details>\n\n---\n\n💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。\n💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。\n\n\n💪 Powered by [ZHENXUNFLOW](https://github.com/zhenxun-org/zhenxunflow)\n<!-- ZHENXUNFLOW -->\n""",
            },
            True,
        )

        ctx.receive_event(bot, event)

    # 测试 git 命令
    mock_subprocess_run.assert_has_calls(
        [
            mocker.call(
                ["git", "config", "--global", "safe.directory", "*"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                ["pre-commit", "install", "--install-hooks"],
                check=True,
                capture_output=True,
            ),
        ]  # type: ignore
    )

    # 检查文件是否正确
    check_json_data(
        plugin_config.input_config.plugin_path,
        {},
    )

    assert mocked_api["github_url_failed"].called


async def test_process_publish_check_ready_for_review(
    app: App, mocker: MockerFixture, mocked_api: MockRouter, tmp_path: Path
) -> None:
    """当之前失败后再次通过测试时，应该将拉取请求标记为 ready for review"""
    from src.plugins.publish import publish_check_matcher
    from src.plugins.publish.config import PluginTestMetadata, plugin_config

    mock_subprocess_run = mocker.patch(
        "subprocess.run", side_effect=lambda *args, **kwargs: mocker.MagicMock()
    )

    mock_installation = mocker.MagicMock()
    mock_installation.id = 123
    mock_installation_resp = mocker.MagicMock()
    mock_installation_resp.parsed_data = mock_installation

    mock_issue = mocker.MagicMock()
    mock_issue.pull_request = None
    mock_issue.title = "Plugin: test"
    mock_issue.number = 80
    mock_issue.state = "open"
    mock_issue.body = generate_issue_body_plugin(plugin_name="test")
    mock_issue.user.login = "test"

    mock_event = mocker.MagicMock()
    mock_event.issue = mock_issue

    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    mock_comment = mocker.MagicMock()
    mock_comment.body = "Plugin: test"
    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    mock_pull = mocker.MagicMock()
    mock_pull.number = 2
    mock_pull.title = "Plugin: test"
    mock_pull.draft = True
    mock_pull.node_id = "123"
    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = [mock_pull]
    plugin_config.plugin_test_metadata = PluginTestMetadata(
        description="description",
        usage="usage",
        plugin_type="NORMAL",
        version="0.1",
    )
    plugin_config.plugin_test_result = True

    with open(tmp_path / "plugins.json", "w") as f:
        json.dump({}, f)

    check_json_data(plugin_config.input_config.plugin_path, {})

    async with app.test_matcher(publish_check_matcher) as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=GitHubBot,
            adapter=adapter,
            self_id=GitHubApp(app_id="1", private_key="1"),  # type: ignore
        )
        bot = cast(GitHubBot, bot)
        event_path = Path(__file__).parent.parent / "events" / "issue-open.json"
        event = Adapter.payload_to_event("1", "issues", event_path.read_bytes())
        assert isinstance(event, IssuesOpened)

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            {"owner": "AkashiCoin", "repo": "action-test"},
            mock_installation_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_get",
            {"owner": "AkashiCoin", "repo": "action-test", "issue_number": 80},
            mock_issues_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "AkashiCoin", "repo": "action-test", "issue_number": 80},
            mock_list_comments_resp,
        )
        ctx.should_call_api(
            "rest.pulls.async_create",
            {
                "owner": "AkashiCoin",
                "repo": "action-test",
                "title": "Plugin: test",
                "body": "resolve #80",
                "base": "master",
                "head": "publish/issue80",
            },
            exception=RequestFailed(
                Response(
                    httpx.Response(422, request=httpx.Request("test", "test")), None
                )
            ),
        )
        ctx.should_call_api(
            "rest.pulls.async_list",
            {
                "owner": "AkashiCoin",
                "repo": "action-test",
                "head": "AkashiCoin:publish/issue80",
            },
            mock_pulls_resp,
        )
        # 将拉取请求标记为可供审阅
        ctx.should_call_api(
            "async_graphql",
            {
                "query": "mutation markPullRequestReadyForReview($pullRequestId: ID!) {\n                    markPullRequestReadyForReview(input: {pullRequestId: $pullRequestId}) {\n                        clientMutationId\n                    }\n                }",
                "variables": {"pullRequestId": "123"},
            },
            True,
        )
        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "AkashiCoin", "repo": "action-test", "issue_number": 80},
            mock_list_comments_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_create_comment",
            {
                "owner": "AkashiCoin",
                "repo": "action-test",
                "issue_number": 80,
                "body": """# 📃 商店发布检查结果\n\n> Plugin: test\n\n**✅ 所有测试通过，一切准备就绪！**\n\n\n<details>\n<summary>详情</summary>\n<pre><code><li>✅ 项目 <a href="https://github.com/author/module/">https://github.com/author/module</a> GitHub仓库存在。</li><li>✅ version: 0.1。</li><li>✅ 插件类型: 普通插件。</li><li>✅ 插件 <a href="https://github.com/owner/repo/actions/runs/123456">加载测试</a> 通过。</li></code></pre>\n</details>\n\n---\n\n💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。\n💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。\n\n\n💪 Powered by [ZHENXUNFLOW](https://github.com/zhenxun-org/zhenxunflow)\n<!-- ZHENXUNFLOW -->\n""",
            },
            True,
        )

        ctx.receive_event(bot, event)

    # 测试 git 命令
    mock_subprocess_run.assert_has_calls(
        [
            mocker.call(
                ["git", "config", "--global", "safe.directory", "*"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                ["pre-commit", "install", "--install-hooks"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                ["git", "switch", "-C", "publish/issue80"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                ["git", "config", "--global", "user.name", "test"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                [
                    "git",
                    "config",
                    "--global",
                    "user.email",
                    "test@users.noreply.github.com",
                ],
                check=True,
                capture_output=True,
            ),
            mocker.call(["git", "add", "-A"], check=True, capture_output=True),
            mocker.call(
                ["git", "commit", "-m", ":beers: publish plugin test (#80)"],
                check=True,
                capture_output=True,
            ),
            mocker.call(["git", "fetch", "origin"], check=True, capture_output=True),
            mocker.call(
                ["git", "diff", "origin/publish/issue80", "publish/issue80"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                ["git", "push", "origin", "publish/issue80", "-f"],
                check=True,
                capture_output=True,
            ),
        ]  # type: ignore
    )

    # 检查文件是否正确
    check_json_data(
        plugin_config.input_config.plugin_path,
        {
            "test": {
                "module": "module",
                "module_path": "module_path",
                "description": "description",
                "usage": "usage",
                "author": "test",
                "version": "0.1",
                "plugin_type": "NORMAL",
                "is_dir": True,
                "github_url": "https://github.com/author/module",
            }
        },
    )

    assert mocked_api["github_url"].called
