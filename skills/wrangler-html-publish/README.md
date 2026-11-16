# Wrangler HTML Publish

给支持本地终端操作的 AI Agent 使用的技能：HTML 生成完成后主动归档，并在获得公开授权后发布到 Cloudflare Pages。

## 安装

使用 skills CLI 安装到当前项目：

```bash
npx skills add 156554395/claude-code-skills --skill wrangler-html-publish
```

如需在多个项目中使用，安装到用户级全局目录：

```bash
npx skills add 156554395/claude-code-skills --skill wrangler-html-publish -g
```

按 CLI 提示选择目标 Agent。安装前检查同名技能，避免覆盖已有修改；不要默认加 `-y` 跳过确认。运行 npx 需要 Node.js/npm 和网络。技能不包含作者电脑路径、账号、认证信息或运行记录。

安装后保留 `SKILL.md`、`scripts/`、`references/` 和 `tests/` 的完整结构；多 Agent 的安装路径和链接由 skills CLI 管理。

重新加载技能或新建会话后，可明确输入：

> 使用 wrangler-html-publish，把这份 HTML 保存到固定目录并发布，给我地址。

## 默认行为

- 存放目录：当前用户主目录的 `Documents/published-html/<slug>/index.html`，可自行指定其他目录。
- 仅本地：说“生成 HTML，先不要上传”；不会登录或部署。
- 首次发布：检查 Node.js/npm/Wrangler、引导登录、确认项目/分支与公开范围，保存非敏感配置。
- 后续发布：复用配置，按白名单保留旧站点页面，不把私人草稿混入快照。
- Pages 内容通常公开，不适合直接分享客户隐私或内部原文；随机 URL 不提供访问控制。

“生成 HTML 后自动触发”是 Agent 的行为指引，不是文件监听服务，不能保证每个 Agent 必然调用。本技能不会擅自安装 hooks 或修改全局 settings。

## 依赖与测试

本地脚本只用 Node.js 内置模块，无 npm 依赖，不执行 Cloudflare 请求。部署需要可用的 Node.js、npm、Wrangler 和 Cloudflare 账号；登录凭证由 Wrangler 自行管理。

```sh
node --test "<技能目录>/tests/files.test.mjs"
```

离线测试验证路径与文件整理，不证明真实 Cloudflare 部署已成功。技能安装和升级不应包含运行态 config、plan、manifest、快照或缓存。
