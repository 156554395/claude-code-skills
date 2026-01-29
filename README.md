# Claude Code Skills

这是一个 Claude Code 技能集合，用于扩展 Claude 的功能。

## 简介

Claude Code 技能是一系列可复用的功能模块，可以通过特定触发词激活，帮助完成特定的任务。

## 当前技能列表

### [novel-writer](./novel-writer/) - 小说写作助手

一个帮助新手作者快速生成网络小说的 AI 技能。支持多种主流网文类型，自动生成大纲并逐章创作完整小说。

**支持类型：** 玄幻、仙侠、都市、科幻、历史、武侠、网游、灵异、军事、竞技

**触发方式：**
- `写小说`
- `创作小说`
- `生成小说`
- `帮我写个小说`

**功能特点：**
- 交互式需求收集（类型/风格/字数）
- AI 自动生成大纲（世界观/人物/剧情/章节规划）
- 用户确认后逐章生成
- 分章节文件保存

详细文档请查看：[novel-writer/README.md](./novel-writer/README.md)

## 如何使用

### 1. 安装技能

将技能目录复制到 Claude Code 的技能目录：

```bash
# 技能目录位置（macOS/Linux）
~/.claude/skills/

# 复制技能示例
cp -r novel-writer ~/.claude/skills/
```

**技能目录结构：**
```
~/.claude/skills/
├── novel-writer/
│   ├── SKILL.md
│   └── README.md
├── your-skill/
│   ├── SKILL.md
│   └── README.md
└── ...
```

### 2. 激活技能

在 Claude Code 对话中使用触发词激活技能：

```bash
# 例如激活 novel-writer 技能
写小说
```

### 3. 交互使用

根据技能提示进行交互，完成相应任务。

## 技能开发

如果你想创建自己的技能，可以参考现有技能的结构：

```
skill-name/
├── SKILL.md      # 技能定义和逻辑
└── README.md     # 用户文档
```

### SKILL.md 模板

```yaml
---
name: your-skill-name
description: 简短描述触发条件和使用场景
---

# 技能名称

## 技能触发条件
- 触发词1
- 触发词2

## 核心工作流
...
```

## 贡献

欢迎贡献新的技能！请确保：
- 提供清晰的 SKILL.md 定义
- 编写详细的 README.md 用户文档
- 遵循现有技能的代码风格

## 许可

请根据各自技能的许可声明使用。
