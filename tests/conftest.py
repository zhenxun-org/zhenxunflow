import json
from pathlib import Path
from typing import TYPE_CHECKING

import httpx
import nonebot
import pytest
from nonebot.adapters.github import Adapter
from nonebug import NONEBOT_INIT_KWARGS
from nonebug.app import App
from pytest_mock import MockerFixture
from respx import MockRouter

if TYPE_CHECKING:
    from nonebot.plugin import Plugin


def pytest_configure(config: pytest.Config) -> None:
    config.stash[NONEBOT_INIT_KWARGS] = {
        "driver": "~none",
        "input_config": {
            "base": "master",
            "plugin_path": "plugin_path",
        },
        "github_repository": "owner/repo",
        "github_run_id": "123456",
        "github_event_path": "event_path",
        "plugin_test_output": "test_output",
        "plugin_test_result": False,
        "github_apps": [],
    }


@pytest.fixture(scope="session", autouse=True)
def load_plugin(nonebug_init: None) -> set["Plugin"]:
    nonebot.get_driver().register_adapter(Adapter)
    return nonebot.load_plugins(str(Path(__file__).parent.parent / "src" / "plugins"))


@pytest.fixture()
async def app(app: App, tmp_path: Path, mocker: MockerFixture):
    from src.plugins.publish.config import plugin_config

    plugin_path = tmp_path / "plugins.json"
    with plugin_path.open("w") as f:
        json.dump(
            {
                "plugin_name": {
                    "module": "module",
                    "module_path": "module_path",
                    "description": "description",
                    "usage": "usage",
                    "author": "author",
                    "version": "0.1",
                    "plugin_type": "NORMAL",
                    "is_dir": True,
                    "github_url": "https://github.com/author/module",
                }
            },
            f,
        )

    mocker.patch.object(plugin_config.input_config, "plugin_path", plugin_path)
    mocker.patch.object(plugin_config, "skip_plugin_test", False)

    yield app

    pass


@pytest.fixture(autouse=True)
def _clear_cache(app: App):
    """每次运行前都清除 cache"""
    from src.utils.validation.utils import check_url

    check_url.cache_clear()


@pytest.fixture()
def mocked_api(respx_mock: MockRouter):
    respx_mock.get("exception", name="exception").mock(side_effect=httpx.ConnectError)
    respx_mock.get(
        "https://pypi.org/pypi/project_link/json", name="project_link"
    ).respond(
        json={
            "info": {
                "version": "0.0.1",
            },
            "urls": [
                {
                    "upload_time_iso_8601": "2023-09-01T00:00:00+00:00Z",
                }
            ],
        }
    )
    respx_mock.get(
        "https://pypi.org/pypi/nonebot-plugin-treehelp/json",
        name="project_link_treehelp",
    ).respond(
        json={
            "info": {
                "version": "0.3.1",
            },
            "urls": [
                {
                    "upload_time_iso_8601": "2021-08-01T00:00:00+00:00",
                }
            ],
        }
    )
    respx_mock.get(
        "https://pypi.org/pypi/nonebot-plugin-datastore/json",
        name="project_link_datastore",
    ).respond(
        json={
            "info": {
                "version": "1.0.0",
            }
        }
    )
    respx_mock.get(
        "https://pypi.org/pypi/nonebot-plugin-wordcloud/json",
        name="project_link_wordcloud",
    ).respond(
        json={
            "info": {
                "version": "0.5.0",
            }
        }
    )
    respx_mock.get("https://github.com/author/module", name="github_url").respond()
    respx_mock.get("https://www.baidu.com", name="github_url_failed").respond(404)
    respx_mock.get(
        "https://pypi.org/pypi/project_link1/json", name="project_link1"
    ).respond()
    respx_mock.get(
        "https://pypi.org/pypi/project_link_failed/json", name="project_link_failed"
    ).respond(404)
    return respx_mock
