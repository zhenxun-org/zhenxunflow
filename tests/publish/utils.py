def generate_issue_body_plugin(
    plugin_name: str = "plugin_name",
    module: str = "module",
    module_path: str = "module_path",
    is_dir: bool = True,
    github_url: str = "https://github.com/author/module",
    config: str = "log_level=DEBUG",
):
    return f"""### 插件名称\n\n{plugin_name}\n\n### 模块名称\n\n{module}\n\n### 模块路径\n\n{module_path}\n\n### 仓库地址\n\n{github_url}\n\n### 是否为目录\n\n{'是' if is_dir else '否'}\n\n### 插件配置项\n\n```dotenv\n{config}\n```"""
