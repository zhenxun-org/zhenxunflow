"""验证数据是否符合规范"""

from typing import Any

from pydantic import ValidationError

from .models import PluginPublishInfo, PublishInfo
from .models import PublishType as PublishType
from .models import ValidationDict as ValidationDict
from .utils import translate_errors

validation_model_map: dict[PublishType, type[PublishInfo]] = {
    PublishType.PLUGIN: PluginPublishInfo,
}


def validate_info(
    publish_type: PublishType, raw_data: dict[str, Any]
) -> ValidationDict:
    """验证信息是否符合规范"""
    if publish_type not in validation_model_map:
        raise ValueError("⚠️ 未知的发布类型。")  # pragma: no cover

    # https://docs.pydantic.dev/latest/usage/validators/#validation-context
    validation_context = {
        "previous_data": raw_data.get("previous_data"),
        "skip_plugin_test": raw_data.get("skip_plugin_test"),
        "valid_data": {},
    }

    try:
        data = dict(
            validation_model_map[publish_type].model_validate(
                raw_data, context=validation_context
            )
        )
        errors = []
    except ValidationError as exc:
        errors = exc.errors()
        data: dict[str, Any] = validation_context["valid_data"]

    # 翻译错误
    errors = translate_errors(errors)

    # 如果是插件，还需要额外验证插件加载测试结果
    if publish_type == PublishType.PLUGIN:
        skip_plugin_test = raw_data.get("skip_plugin_test")
        plugin_test_result = raw_data.get("plugin_test_result")
        plugin_test_output = raw_data.get("plugin_test_output")
        plugin_test_metadata = raw_data.get("plugin_test_metadata")
        if previous_data := raw_data.get("previous_data"):
            if old_data := previous_data.get(raw_data["name"]):
                for old_key, old_value in old_data.items():
                    if data[old_key] != old_value:
                        break
                else:
                    errors.append(
                        {
                            "loc": ("previous_data",),
                            "msg": "与上次发布的数据相同。",
                            "type": "previous_data",
                            "ctx": {"previous_data": previous_data, "data": data},
                            "input": None,
                        }
                    )

        if plugin_test_metadata is None and not skip_plugin_test:
            errors.append(
                {
                    "loc": ("metadata",),
                    "msg": "无法获取到插件元数据。",
                    "type": "metadata",
                    "ctx": {"plugin_test_result": plugin_test_result},
                    "input": None,
                }
            )
            # 如果没有跳过测试且缺少插件元数据，则跳过元数据相关的错误
            # 因为这个时候这些项都会报错，错误在此时没有意义
            metadata_keys = [
                "usage",
                "description",
                "plugin_type",
                "version",
            ]
            errors = [error for error in errors if error["loc"][0] not in metadata_keys]
            # 元数据缺失时，需要删除元数据相关的字段
            for key in metadata_keys:
                data.pop(key, None)

        if not skip_plugin_test and not plugin_test_result:
            errors.append(
                {
                    "loc": ("plugin_test",),
                    "msg": "插件无法正常加载",
                    "type": "plugin_test",
                    "ctx": {"output": plugin_test_output},
                    "input": None,
                }
            )

    return {
        "valid": not errors,
        "data": data,
        "errors": errors,
        # 方便插件使用的数据
        "type": publish_type,
        "name": data.get("name") or raw_data.get("name", ""),
        "author": data.get("author", ""),
    }
