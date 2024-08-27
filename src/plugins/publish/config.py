from pathlib import Path

from nonebot import get_driver
from pydantic import BaseModel, ConfigDict, field_validator
from typing_extensions import TypedDict

from src.utils.plugin_test import strip_ansi


class PublishConfig(BaseModel):
    base: str
    plugin_path: Path


class PluginTestMetadata(TypedDict):
    description: str
    usage: str
    plugin_type: str
    version: str


class Config(BaseModel, extra="ignore"):
    model_config = ConfigDict(coerce_numbers_to_str=True)

    input_config: PublishConfig
    github_repository: str
    github_run_id: str
    skip_plugin_test: bool = False
    plugin_test_result: bool = False
    plugin_test_output: str = ""
    plugin_test_metadata: PluginTestMetadata | None = None

    @field_validator("plugin_test_result", mode="before")
    @classmethod
    def plugin_test_result_validator(cls, v):
        # 如果插件测试没有运行时，会得到一个空字符串
        # 这里将其转换为布尔值，不然会报错
        if v == "":
            return False
        return v

    @field_validator("plugin_test_metadata", mode="before")
    @classmethod
    def plugin_test_metadata_validator(cls, v):
        # 如果插件测试没有运行时，会得到一个空字符串
        # 这里将其转换为 None，不然会报错
        if v == "":
            return None
        return v

    @field_validator("plugin_test_output", mode="before")
    @classmethod
    def plugin_test_output_validator(cls, v):
        """移除 ANSI 转义字符"""
        return strip_ansi(v)


plugin_config = Config.model_validate(dict(get_driver().config))
