import abc
from enum import Enum
from typing import TYPE_CHECKING, Annotated, Any, TypedDict

from pydantic import (
    BaseModel,
    Field,
    StringConstraints,
    ValidationInfo,
    ValidatorFunctionWrapHandler,
    field_validator,
)
from pydantic_core import PydanticCustomError

from .constants import NAME_MAX_LENGTH
from .utils import check_url

if TYPE_CHECKING:
    from pydantic_core import ErrorDetails


class ValidationDict(TypedDict):
    valid: bool
    type: "PublishType"
    name: str
    author: str
    data: dict[str, Any]
    errors: "list[ErrorDetails]"


class PublishType(Enum):
    """发布的类型

    值为标签名
    """

    PLUGIN = "Plugin"


class PublishInfo(abc.ABC, BaseModel):
    """发布信息"""

    name: str = Field(max_length=NAME_MAX_LENGTH)
    """"发布的名字"""
    module: str
    """"模块名"""
    module_path: str
    """"模块路径"""
    is_dir: bool
    """"是否为目录"""
    author: str
    """作者"""

    github_url: Annotated[
        str,
        StringConstraints(strip_whitespace=True, pattern=r"^https?://.*$"),
    ]
    """仓库地址"""

    @field_validator("*", mode="wrap")
    @classmethod
    def collect_valid_values(
        cls, v: Any, handler: ValidatorFunctionWrapHandler, info: ValidationInfo
    ):
        """收集验证通过的数据

        NOTE: 其他所有的验证器都应该在这个验证器之前执行
        所以不能用 after 模式，只能用 before 模式
        """
        context = info.context
        if context is None:  # pragma: no cover
            raise PydanticCustomError("validation_context", "未获取到验证上下文")

        result = handler(v)
        context["valid_data"][info.field_name] = result
        return result

    @field_validator("github_url", mode="before")
    @classmethod
    def github_url_validator(cls, v: str) -> str:
        if v:
            status_code, msg = check_url(v)
            if status_code != 200:
                raise PydanticCustomError(
                    "github_url",
                    "项目主页无法访问",
                    {"status_code": status_code, "msg": msg},
                )
        return v


class PluginPublishInfo(PublishInfo):
    """发布插件所需信息"""

    description: str
    """插件描述"""

    usage: str
    """插件用法"""

    version: str
    """插件版本"""

    plugin_type: str
    """插件类型"""
