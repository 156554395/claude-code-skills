# Claude Code Skills

Claude Code 中文技能集合

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 简介

这是一个 Claude Code 技能集合，包含实用的中文技能，可以通过 Claude Code 插件市场直接安装。

## 安装

### 方法一：插件市场安装（推荐）

在 Claude Code 中运行：

```bash
# 1. 启动 Claude Code
claude

# 2. 添加市场插件
/plugin marketplace add 156554395/claude-code-skills
# 3. 安装小说技能插件
/plugin install claude-code-skills@156554395
```

### 方法二：手动安装

```bash
# 克隆仓库
git clone https://github.com/156554395/claude-code-skills.git

# 复制到 Claude Code 技能目录
cp -r claude-code-skills/skills/* ~/.claude/skills/
```

## 当前技能列表

### [novel-writer](./skills/novel-writer/) - 小说写作助手

帮助新手作者快速生成网络小说，支持多种主流网文类型，自动生成大纲并逐章创作。

**支持类型：** 玄幻、仙侠、都市、科幻、历史、武侠、网游、灵异、军事、竞技

**触发方式：**
- `写小说`
- `创作小说`
- `生成小说`

**功能特点：**
- 交互式需求收集
- AI 自动生成大纲
- 逐章生成完整小说

详细文档：[novel-writer README](./skills/novel-writer/README.md)

## 使用方法

安装后，在 Claude Code 对话中使用触发词即可激活技能：

```bash
# 激活小说写作助手
写小说
```

## 技能开发

创建自己的技能，参考以下结构：

```
skills/
└── your-skill/
    ├── SKILL.md    # 技能定义（触发条件、工作流）
    └── README.md   # 用户文档
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
- 遵循现有技能的风格

## 许可

MIT License - 详见 [LICENSE](./LICENSE)
