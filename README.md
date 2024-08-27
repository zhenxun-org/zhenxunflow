<!-- markdownlint-disable -->
<p align="center">
  <a href="https://nonebot.dev/"><img src="https://raw.githubusercontent.com/zhenxun-org/zhenxunflow/main/assets/logo.png" width="200" alt="zhenxunflow"></a>
</p>

<div align="center">

# zhenxunflow

_✨ zhenxun-bot 工作流管理机器人 ✨_

[![codecov](https://codecov.io/gh/nonebot/noneflow/branch/main/graph/badge.svg?token=BOIBTOCWCH)](https://codecov.io/gh/nonebot/noneflow)
[![Powered by NoneBot](https://img.shields.io/badge/Powered%20%20by-NoneBot-red)](https://github.com/nonebot/nonebot2)

</div>
<!-- markdownlint-enable-->

## 来源

修改自[noneflow](https://github.com/nonebot/noneflow)

## 主要功能

根据 插件 发布(带 Plugin)议题，自动修改对应文件，并创建拉取请求。

## 自动处理

- 商店发布议题创建后，自动根据议题内容创建拉取请求
- 相关议题修改时，自动修改已创建的拉取请求，如果没有创建则重新创建
- 拉取请求关闭时，自动关闭对应议题，并删除对应分支
- 已经创建的拉取请求在其他拉取请求合并后，自动解决冲突
- 自动检查是否符合发布要求
- 审查通过后自动合并

### 发布要求

- 仓库能够访问
- 插件能够正常加载
