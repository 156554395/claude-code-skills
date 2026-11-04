---
name: cogview-image-generator
description: 使用智谱官方图片生成 API 进行 glm-image 文生图，支持单张图片和多版本生成；当用户说生成图片、画图、文生图、智谱生图、glm-image、生成配图或批量出图时主动使用。默认关闭水印；不用于视频生成、已有图片编辑或 PPTX 文件编辑。
homepage: https://docs.bigmodel.cn/api-reference/%E6%A8%A1%E5%9E%8B-api/%E5%9B%BE%E7%89%87%E7%94%9F%E6%88%90
metadata:
  api_endpoint: https://open.bigmodel.cn/api/paas/v4/images/generations
  default_model: glm-image
---

# 智谱 glm-image 图片生成

## 概述

本技能直接使用 `curl` 调用智谱官方 API，不依赖 MCP、Python 脚本或第三方 SDK。完整参数和返回说明见 `references/official-api.md`。

## 初始化

1. 读取 `references/official-api.md`。
2. 从当前环境读取 `ZHIPU_API_KEY`；不要要求用户在聊天中粘贴密钥，也不要把密钥写入文件、命令历史、日志或回复。
3. 若未配置密钥，提示用户在本机设置 `ZHIPU_API_KEY` 后重试，并停止调用。
4. 直接使用下方官方 endpoint；不要改用 MCP 或自行创建 API 代理。

## 调用方式

### 单图

```bash
curl -X POST "https://open.bigmodel.cn/api/paas/v4/images/generations" \
  -H "Authorization: Bearer $ZHIPU_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "glm-image",
    "prompt": "雨夜上海街头，电影感摄影，湿润路面反光，蓝紫色霓虹",
    "quality": "standard",
    "size": "1024x1024",
    "watermark_enabled": false
  }'
```

请求成功后，从 `data[0].url` 读取图片临时 URL。需要本地文件时，再使用普通 `curl -L` 下载该 URL；下载图片时不要携带生成接口的 Bearer token，并使用用户指定或新建的未占用文件名，避免覆盖已有文件。

### 多张图片或多个版本

官方图片 endpoint 一次生成一张图，不要虚构 `n` 或批量字段。用户要求多张图片时，为每张图单独准备提示词并分别执行 curl；每次都显式传入 `"watermark_enabled": false`。多次调用可能产生费用，批量执行前确认用户已明确要求，失败后不要自动重试。

## 默认参数

- 模型：`glm-image`
- 尺寸：`1024x1024`
- 质量：`standard`
- 水印：`watermark_enabled: false`

支持模型：默认 `glm-image`；用户明确指定其他官方支持的图片模型时准确透传，不擅自替换。仅当用户明确要求“加水印”“保留官方水印”时，才将 `watermark_enabled` 改为 `true`。

## 需求整理

从用户请求提取主体、场景、动作、风格、材质、视角、构图、色彩、文字、尺寸和禁用元素。保留硬约束；可以补充光线、景别和材质描述，但不要凭空添加品牌、人物身份、Logo 或文字。信息足够时直接调用，只有主体、数量、比例等关键要求存在歧义才询问。

图片内文字可能出现错别字或变形；用户要求时仍尝试，并在结果中提醒这一限制。

## 错误和边界

- 未配置 `ZHIPU_API_KEY`：提示用户在本机配置后停止，不索取密钥内容。
- HTTP 401/403：提示检查 API Key、账户权限及去水印授权状态。
- HTTP 429/5xx、超时或网络失败：如实报告，默认不重试；超时请求可能已经计费。
- 参数不合法：只修正被拒绝的参数，或说明可用值；不静默切换模型。
- 安全策略拒绝：如实说明，不通过反复改写提示词规避限制。
- 图片 URL 为临时资源，应及时下载或转存，不要当作永久地址。
- 当前只支持文生图，不支持参考图编辑、局部重绘、视频生成、`.pptx` 创建或自动发布。

## 输出格式

```text
已生成图片
- 模型：<实际模型>
- 尺寸：<实际尺寸>
- 质量：<quality>
- 水印参数：关闭（或按用户要求开启）
- 图片：<临时 URL 或实际下载路径>
```

未实际下载时，不要声称图片已保存到本地；不要声称完成了像素级水印检测，水印状态仅表示请求参数。
