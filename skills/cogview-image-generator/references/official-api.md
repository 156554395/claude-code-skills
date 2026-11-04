# 智谱图片生成 API（glm-image）

来源：<https://docs.bigmodel.cn/api-reference/%E6%A8%A1%E5%9E%8B-api/%E5%9B%BE%E7%89%87%E7%94%9F%E6%88%90>

## Endpoint

```text
POST https://open.bigmodel.cn/api/paas/v4/images/generations
```

请求头：

```text
Authorization: Bearer <ZHIPU_API_KEY>
Content-Type: application/json
```

技能直接用 `curl` 调用此 endpoint，不依赖 MCP、Python 脚本或第三方 SDK。

## 请求体

```json
{
  "model": "glm-image",
  "prompt": "图片描述",
  "quality": "standard",
  "size": "1024x1024",
  "watermark_enabled": false
}
```

字段：

- `model`：默认使用 `glm-image`；用户指定其他官方支持的图片模型时，以官方文档和账户能力为准。
- `prompt`：必填的图片文本描述。
- `quality`：通常为 `standard` 或 `hd`，以官方当前文档为准。
- `size`：默认 `1024x1024`。官方推荐尺寸包括 `1024x1024`、`768x1344`、`864x1152`、`1344x768`、`1152x864`、`1440x720`、`720x1440`。
- `watermark_enabled`：控制显式水印和隐式数字水印。本技能默认传 `false`；只有用户明确要求水印时传 `true`。关闭水印可能需要账户完成官方去水印管理和免责声明流程，参数为 `false` 不代表服务端一定批准。
- `user_id`：可选终端用户标识，长度和格式按官方当前文档执行；没有明确用户标识时不自行编造。

自定义尺寸通常要求宽高在 `512px–2048px`、均可被 `16` 整除，且总像素数不超过 `2^21`；最终以官方服务端校验为准。

## 返回体

成功响应通常包含：

```json
{
  "created": 1790000000,
  "data": [{"url": "https://..."}],
  "content_filter": [{"role": "assistant", "level": 3}]
}
```

读取 `data[0].url` 获取图片地址。该 URL 是临时资源，通常有效期约 30 天，应及时下载或转存。下载时用普通 HTTP GET，不携带生成请求的 Bearer token。

## 调用边界

`glm-image` 的官方接口支持异步任务流程；如果直接调用同步 endpoint，则按响应处理 `data[0].url`。若使用官方异步 endpoint，应按文档查询任务状态，不要把同步响应当作异步任务。

多图需求应为每张图分别调用 endpoint；不要虚构不在官方文档中的批量字段。多次请求可能产生费用，只有用户明确要求时执行，失败后默认不自动重试。
