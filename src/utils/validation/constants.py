NAME_MAX_LENGTH = 50
"""名称最大长度"""

PLUGIN_VALID_TYPE = [
    "NORMAL",
    "ADMIN",
    "SUPERUSER",
    "ADMIN_SUPERUSER",
    "DEPENDANT",
    "HIDDEN",
]
"""插件类型"""

# Pydantic 错误信息翻译
MESSAGE_TRANSLATIONS = {
    "model_type": "值不是合法的字典",
    "list_type": "值不是合法的列表",
    "set_type": "值不是合法的集合",
    "json_type": "JSON 格式不合法",
    "missing": "字段不存在",
    "color_error": "颜色格式不正确",
    "string_too_long": "字符串长度不能超过 {max_length} 个字符",
    "too_long": "列表长度不能超过 {max_length} 个元素",
    "string_pattern_mismatch": "字符串应满足格式 '{pattern}'",
}
