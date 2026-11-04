# Agent Skills

通用 Agent 技能集合，可供支持 Agent Skills 标准的 AI Agent 使用。

## 安装

### 推荐：使用 skills CLI

```bash
npx skills add 156554395/claude-code-skills
```

### Claude Code 插件市场（兼容安装）

```text
/plugin marketplace add 156554395/claude-code-skills
/plugin install novel-writer@claude-code-skills-market
```

将 `novel-writer` 替换为其他技能名称，即可安装对应技能。

### 手动安装

```bash
git clone https://github.com/156554395/claude-code-skills.git
cp -r claude-code-skills/skills/* ~/.claude/skills/
```

## 技能

| 技能 | 介绍 |
| --- | --- |
| [novel-writer](./skills/novel-writer/) | 小说写作助手，支持网络小说大纲生成与逐章创作。 |
| [ppt-image-generator](./skills/ppt-image-generator/) | 使用豆包 Seedream 生成 PPT 幻灯片图片。 |
| [wechat-sticker-creator](./skills/wechat-sticker-creator/) | 制作、检查并发布微信表情包。 |
| [gpt-image-generator](./skills/gpt-image-generator/) | 使用 GPT Image 模型生成图片。 |
| [video-transcript-txt](./skills/video-transcript-txt/) | 将本地视频转写为带时间戳和说话人标签的 TXT。 |
| [novel-writer-team](./skills/novel-writer-team/) | 由多个 Agent 协作完成小说创作。 |
| [dingtalk-shanji](./skills/dingtalk-shanji/) | 提取钉钉闪记的听记、转写、摘要和待办。 |
| [dedao-thinking-skills](./skills/dedao-thinking-skills/) | 提供润色、点评、拷问、回顾、创作、发芽六种思考模式。 |
| [amoeba-management-analysis](./skills/amoeba-management-analysis/) | 提供阿米巴经营和单位时间核算分析。 |
| [cogview-image-generator](./skills/cogview-image-generator/) | 使用智谱 glm-image API 进行文生图。 |

## 许可

MIT License - 详见 [LICENSE](./LICENSE)
