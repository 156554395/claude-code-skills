---
name: gpt-image-generator
description: 使用 gpt-image-2、gpt-image-2.5-flare 或 gpt-image-2.5-sunburst 生成图片，支持自定义 OpenAI Images API baseurl。用户指定这些模型画图、文生图、生成配图，或要求通过自定义图片接口生成图片时使用。默认模型 gpt-image-2.5-flare；不用于参考图编辑、聊天接口出图或视频生成。
compatibility: Python 3.10+；推荐通过 uv run --no-project python 执行，无第三方 Python 依赖。
---

# GPT 图片生成

## 工作流

1. 确定提示词和输出路径。保留用户指定的文字、主题、风格与构图；不凭空添加品牌或人物。仅在缺少核心主题时追问。
2. 用户未指定模型时使用 `gpt-image-2.5-flare`，另支持 `gpt-image-2` 和 `gpt-image-2.5-sunburst`。不替换模型，不根据模型名称猜测价格或能力。
3. 使用下述脚本。`{baseDir}` 是当前 SKILL.md 所在目录，可以是任意 Agent 的软链接入口；真实共享目录是 `~/.agents/skills/gpt-image-generator/`。
4. 缺配置时提示用户在本机设置，不让用户在聊天中粘贴密钥，不读取其他技能的凭证。更换服务域名时先确认用户信任该服务，因为提示词和 API Key 会发送给该服务。
5. 成功后用可用的图片查看工具打开输出文件，报告实际模型与绝对路径。脚本仅校验文件标识，不等同于完整图片解码或视觉效果验证。若无法查看，明确说明。

## 配置

配置文件默认路径：`~/.config/gpt-image-generator/config.json`。模板见同目录的 `config.example.json`。不要覆盖现有配置；让用户在本机编辑密钥；含密钥时执行 `chmod 600`。

优先级：命令行参数 > 环境变量 > JSON 配置 > 默认值。

| JSON 字段 | 环境变量 | 默认值 |
|---|---|---|
| base_url | OPENAI_BASE_URL | 无，必须设置 |
| api_key | OPENAI_API_KEY | 无，必须设置；不接受命令行密钥 |
| model | OPENAI_IMAGE_MODEL | gpt-image-2.5-flare |
| size | GPT_IMAGE_SIZE | 1024x1024 |
| quality | GPT_IMAGE_QUALITY | 不发送 |

`base_url` 是完整 API 前缀，例如 `https://example.com/v1` 或 `https://example.com/custom/v1`。脚本仅追加 `/images/generations`，不自动追加 `/v1`。不支持 query、fragment、URL 内嵌凭证或完整 generations endpoint。远程仅 HTTPS，本机测试允许 loopback HTTP。

不自动创建含真实密钥的配置，不把密钥写入 SKILL.md、共享目录、Git、命令行或日志。

## 调用

```bash
uv run --no-project python "{baseDir}/scripts/generate.py" \
  --prompt '雨后山林中的木屋，水彩风格，柔和晨光' \
  --output '/绝对路径/woodland.png'

uv run --no-project python "{baseDir}/scripts/generate.py" \
  --model gpt-image-2.5-sunburst \
  --base-url 'https://example.com/custom/v1' \
  --prompt '复古太空旅行海报，标题为「向星辰出发」' \
  --size 1024x1536 --quality high \
  --output '/绝对路径/space-poster.png'
```

先确保输出父目录存在，选择未使用的文件名。没有 uv 时可使用系统 `python3`，不要为此创建项目或安装 SDK。

- `--config /path/config.json`：指定其它配置文件。
- `--size`：`auto` 或 `宽x高`；显式尺寸为16的倍数，最长边≤3840，长宽比≤3:1，总像素655360–8294400。服务端可能有更严格约束。
- `--quality`：`auto/low/medium/high`，未指定则使用服务端默认值。
- 每次单图，读取 `data[0].b64_json` 或 `data[0].url`。默认使用 `.png`；返回 JPEG/WebP 时要求扩展名匹配，不把其它格式伪装成 PNG。

## 失败和边界

- 不自动重试生成请求：超时仍可能计费。未经用户同意，不重跑、不切换模型或服务。
- 不覆盖任何已有文件，包括悬空链接；不写知识库 Raw。
- 不跟随 HTTP 重定向；下载响应 URL 时不携带生成接口 Bearer。
- 错误只报告脱敏说明和 HTTP 状态码，不打印完整服务响应、密钥或带签名 URL。
- 无真实接口测试时只能说本地模拟测试通过，不能声称模型已成功出图。
- 当前仅文生图，不支持参考图、图片编辑、Chat Completions、批处理或自动发布。

## 验证

```bash
uv run --no-project python -m unittest discover -s "{baseDir}/tests" -v
```

测试使用假密钥和本机模拟响应，不消耗真实服务额度。三组技能行为用例见 `evals/evals.json`；视觉效果需用户授权真实出图后评估。
