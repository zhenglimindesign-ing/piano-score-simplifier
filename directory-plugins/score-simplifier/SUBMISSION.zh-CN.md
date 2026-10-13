# score-simplifier 提交交接

[English](SUBMISSION.md)

状态：本地已准备的审查候选包。本次没有创建官方草稿、送审或发布，也没有改动 Release 或 Tag。

## OpenAI

打开 https://platform.openai.com/plugins → Create plugin → Skills only，上传完整候选 ZIP。检查平台生成的 `.codex-plugin/plugin.json`、展示字段和 Skill 产品范围。包内已有方形图标、限长介绍、三个启动提示、依赖声明和本地数据处理说明。skills-only ZIP 的展示 URL 可选，不填写尚未公开的隐私 URL。身份验证、Apps Management 写权限、政策声明与平台安全扫描由提交者完成。平台转换与目录原生安装为 NOT VERIFIED。

本地工作区流程通过 agents/openai.yaml 限定到 CODEX。官方迁移文档要求核心价值依赖本地执行或任意本地文件访问时先联系 OpenAI partner。送审前确认这一资格；本次没有新增后端。

## Claude

打开 https://claude.ai/directory/manage → Submit new → Plugin bundle。仓库：zhenglimindesign-ing/piano-score-simplifier；插件路径：directory-plugins/score-simplifier；本地候选分支：codex/distribution-prep-20261013，尚未推送。先按项目的源码／生成分发流程审查并公开候选来源，不提交私有维护仓库。确认长期归属组织、付费计划／角色资格，以及具有仓库写权限的 GitHub 连接。

[目录政策](https://support.claude.com/en/articles/13145358-anthropic-software-directory-policy) 1.F 对查询／提取记忆、历史和用户生成／上传文件有广泛禁止，其是否适用于用户明确授权的 skills-only 材料处理，本次未得到平台澄清。本插件使用用户材料，澄清前不标为可送审。3.A 对收集用户数据或连接远端服务的软件要求可访问的隐私政策；PRIVACY.md 是可审查草稿，不是已上线 URL。填写联系邮箱、年龄范围、三个示例；执行 portal Validate，解决阻断项，由本人接受条款。登录后的隔离 Claude 模型任务为 NOT VERIFIED；本地安装和组件发现已通过。

## skills.sh

当前公开源码可经仓库 URL 发现并完整安装，测试已关闭遥测。本次公开关键词搜索／索引尚不可用。FAQ 说明索引依赖安装遥测，本次没有发送安装遥测，也未发现这一渠道的官方提交表单。不需要推送候选 wrapper 才能安装，不把 CLI 安装当作搜索收录或官方认可。
