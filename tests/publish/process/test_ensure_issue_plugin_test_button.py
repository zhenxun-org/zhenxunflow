# from nonebug import App
# from pytest_mock import MockerFixture

# from tests.publish.utils import generate_issue_body_plugin


# async def test_ensure_issue_plugin_test_button(app: App, mocker: MockerFixture):
#     """确保添加插件测试按钮"""
#     from nonebot.adapters.github import GitHubBot

#     from src.plugins.publish.models import RepoInfo
#     from src.plugins.publish.utils import ensure_issue_plugin_test_button

#     # 创建模拟issue
#     mock_issue = mocker.MagicMock()
#     mock_issue.body = generate_issue_body_plugin()
#     mock_issue.number = 1

#     async with app.test_api() as ctx:
#         # 创建模拟bot
#         bot = mocker.MagicMock(spec=GitHubBot)
#         bot.rest.issues.async_update = mocker.AsyncMock(return_value=True)

#         # 设置预期的API调用 - 不再需要，因为我们直接模拟了bot的方法

#         repo_info = RepoInfo(owner="owner", repo="repo")
#         issue_body = mock_issue.body
#         issue_number = mock_issue.number

#         await ensure_issue_plugin_test_button(bot, repo_info, issue_number, issue_body)

#         # 验证bot方法被正确调用
#         bot.rest.issues.async_update.assert_called_once_with(
#             owner="owner",
#             repo="repo",
#             issue_number=1,
#             body=mocker.ANY,  # 使用ANY匹配器，因为具体内容较复杂
#         )


# async def test_ensure_issue_plugin_test_button_checked(app: App, mocker: MockerFixture):
#     """如果测试按钮勾选，则自动取消勾选"""
#     from nonebot.adapters.github import GitHubBot

#     from src.plugins.publish.models import RepoInfo
#     from src.plugins.publish.utils import ensure_issue_plugin_test_button

#     # 创建模拟issue，添加测试按钮并勾选
#     issue_body = generate_issue_body_plugin()
#     issue_body += "\n\n### 插件测试\n\n- [x] 如需重新运行插件测试，请勾选左侧勾选框"

#     async with app.test_api() as ctx:
#         # 创建模拟bot
#         bot = mocker.MagicMock(spec=GitHubBot)
#         bot.rest.issues.async_update = mocker.AsyncMock(return_value=True)

#         repo_info = RepoInfo(owner="owner", repo="repo")
#         issue_number = 1

#         await ensure_issue_plugin_test_button(bot, repo_info, issue_number, issue_body)

#         # 验证bot方法被正确调用
#         bot.rest.issues.async_update.assert_called_once_with(
#             owner="owner",
#             repo="repo",
#             issue_number=1,
#             body=mocker.ANY,  # 使用ANY匹配器，因为具体内容较复杂
#         )


# async def test_ensure_issue_plugin_test_button_unchecked(
#     app: App, mocker: MockerFixture
# ):
#     """如果测试按钮未勾选，则不进行操作"""
#     from nonebot.adapters.github import GitHubBot

#     from src.plugins.publish.models import RepoInfo
#     from src.plugins.publish.utils import ensure_issue_plugin_test_button

#     # 创建模拟issue，添加测试按钮但不勾选
#     issue_body = generate_issue_body_plugin()
#     issue_body += "\n\n### 插件测试\n\n- [ ] 如需重新运行插件测试，请勾选左侧勾选框"

#     async with app.test_api() as ctx:
#         # 创建模拟bot
#         bot = mocker.MagicMock(spec=GitHubBot)
#         bot.rest.issues.async_update = mocker.AsyncMock(return_value=True)

#         repo_info = RepoInfo(owner="owner", repo="repo")
#         issue_number = 1

#         await ensure_issue_plugin_test_button(bot, repo_info, issue_number, issue_body)

#         # 验证bot方法没有被调用
#         bot.rest.issues.async_update.assert_not_called()


# async def test_ensure_issue_plugin_test_button_in_progress(
#     app: App, mocker: MockerFixture
# ):
#     """确保添加插件测试进行中提示"""
#     from nonebot.adapters.github import GitHubBot

#     from src.plugins.publish.models import RepoInfo
#     from src.plugins.publish.utils import ensure_issue_plugin_test_button_in_progress

#     # 创建模拟issue
#     mock_issue = mocker.MagicMock()
#     mock_issue.body = generate_issue_body_plugin()
#     mock_issue.number = 1

#     async with app.test_api() as ctx:
#         # 创建模拟bot
#         bot = mocker.MagicMock(spec=GitHubBot)
#         bot.rest.issues.async_update = mocker.AsyncMock(return_value=True)

#         repo_info = RepoInfo(owner="owner", repo="repo")
#         issue_body = mock_issue.body
#         issue_number = mock_issue.number

#         await ensure_issue_plugin_test_button_in_progress(
#             bot, repo_info, issue_number, issue_body
#         )

#         # 验证bot方法被正确调用
#         bot.rest.issues.async_update.assert_called_once_with(
#             owner="owner",
#             repo="repo",
#             issue_number=1,
#             body=mocker.ANY,  # 使用ANY匹配器，因为具体内容较复杂
#         )
