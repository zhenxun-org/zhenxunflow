import re

NONEFLOW_MARKER = "<!-- ZHENXUNFLOW -->"

BOT_MARKER = "[bot]"
"""机器人的名字结尾都会带有这个"""

SKIP_PLUGIN_TEST_COMMENT = "/skip"

COMMIT_MESSAGE_PREFIX = ":beers: publish"

BRANCH_NAME_PREFIX = "publish/issue"

TITLE_MAX_LENGTH = 50
"""标题最大长度"""

# 匹配信息的正则表达式
# 格式：### {标题}\n\n{内容}
ISSUE_PATTERN = r"### {}\s+([^\s#].*?)(?=(?:\s+###|$))"
ISSUE_FIELD_TEMPLATE = "### {}"
ISSUE_FIELD_PATTERN = r"### {}\s+"

# 基本信息
TAGS_PATTERN = re.compile(ISSUE_PATTERN.format("标签"))
# 插件
PLUGIN_NAME_STRING = "插件名称"
PLUGIN_NAME_PATTERN = re.compile(ISSUE_PATTERN.format(PLUGIN_NAME_STRING))
PLUGIN_MODULE_NAME_STRING = "模块名称"
PLUGIN_MODULE_NAME_PATTERN = re.compile(ISSUE_PATTERN.format(PLUGIN_MODULE_NAME_STRING))
PLUGIN_MODULE_PATH_STRING = "模块路径"
PLUGIN_MODULE_PATH_PATTERN = re.compile(ISSUE_PATTERN.format(PLUGIN_MODULE_PATH_STRING))
PLUGIN_GITHUB_URL_STRING = "仓库地址"
PLUGIN_GITHUB_URL_PATTERN = re.compile(ISSUE_PATTERN.format(PLUGIN_GITHUB_URL_STRING))
PLUGIN_IS_DIR_STRING = "是否为目录"
PLUGIN_IS_DIR_PATTERN = re.compile(ISSUE_PATTERN.format(PLUGIN_IS_DIR_STRING))
PLUGIN_CONFIG_PATTERN = re.compile(r"### 插件配置项\s+```(?:\w+)?\s?([\s\S]*?)```")
PLUGIN_STRING_LIST = [
    PLUGIN_NAME_STRING,
    PLUGIN_MODULE_PATH_STRING,
    PLUGIN_GITHUB_URL_STRING,
    PLUGIN_IS_DIR_STRING,
]

# 发布信息项对应的中文名
LOC_NAME_MAP = {
    "name": "名称",
    "module": "模块名称",
    "module_path": "模块路径",
    "description": "描述",
    "github_url": "仓库地址",
    "author": "作者",
    "version": "版本",
}
