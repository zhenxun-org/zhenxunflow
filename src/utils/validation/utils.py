from functools import cache
from typing import TYPE_CHECKING

import httpx

from .constants import MESSAGE_TRANSLATIONS

if TYPE_CHECKING:
    from pydantic_core import ErrorDetails


@cache
def check_url(url: str) -> tuple[int, str]:
    """检查网址是否可以访问

    返回状态码，如果报错则返回 -1
    """
    try:
        r = httpx.get(url, follow_redirects=True)
        return r.status_code, ""
    except Exception as e:
        return -1, str(e)


def translate_errors(errors: list["ErrorDetails"]) -> list["ErrorDetails"]:
    """翻译 Pydantic 错误信息"""
    new_errors: list["ErrorDetails"] = []
    for error in errors:
        translation = MESSAGE_TRANSLATIONS.get(error["type"])
        if translation:
            ctx = error.get("ctx")
            error["msg"] = translation.format(**ctx) if ctx else translation
        new_errors.append(error)
    return new_errors
