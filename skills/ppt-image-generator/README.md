# PPT 幻灯片图片生成技能

使用豆包 Seedream AI 模型直接生成高质量 PPT 幻灯片图片。

## 功能特点

- **完全并发生成**：每张图片使用一个独立的 subAgent，最大化并发性能
- **两种专业风格**：
  - 渐变拟物玻璃卡片风格 (gradient-glass)
  - 矢量插画风格 (vector-illustration)
- **自动下载**：生成的图片自动下载到本地统一目录
- **完整记录**：生成 prompts.json 记录所有图片的生成信息

## 使用方法

在 Claude Code 中使用此技能：

```
生成3张PPT图片
```

技能将引导你完成：
1. 确认图片数量
2. 选择风格
3. 输入每张幻灯片的内容
4. 自动并发生成所有图片

## 依赖要求

### 豆包 MCP 服务器安装

此技能需要安装 `doubao-giv` MCP 服务器才能使用。

在 Claude Code 配置文件中添加：

```json
{
  "mcpServers": {
    "doubao-giv": {
      "command": "npx",
      "args": ["-y", "doubao-image-video-mcp@latest"],
      "env": {
        "DOUBAO_API_KEY": "your_api_key_here",
        "DOUBAO_IMAGE_ENDPOINT_ID": "ep-20241227-xxxxxxxxxxxxx",
        "DOUBAO_VIDEO_ENDPOINT_ID": "ep-20241227-xxxxxxxxxxxxx"
      }
    }
  }
}
```

**配置说明：**

- `DOUBAO_API_KEY`：访问 [火山引擎控制台](https://console.volcengine.com/) 获取 API 密钥
- `DOUBAO_IMAGE_ENDPOINT_ID`：图片生成推理接入点 ID（可选，推荐使用）
- `DOUBAO_VIDEO_ENDPOINT_ID`：视频生成推理接入点 ID（可选，推荐使用）

配置完成后重启 Claude Code 即可使用。

### 系统要求

- Node.js 环境（npx 会自动处理）
- 豆包 Seedream API 访问权限
- 支持 subAgent 并发调用的环境

## 输出示例

```
✅ 生成完成！
并发模式：每张图片一个Agent（3个Agent同时工作）
保存目录：ppt_images_output/20240227_120000/
- slide-01.png (Agent 1) ✅ 650KB
- slide-02.png (Agent 2) ✅ 720KB
- slide-03.png (Agent 3) ✅ 680KB
提示词记录：ppt_images_output/20240227_120000/prompts.json
总耗时：约1分钟（完全并发）
```

## 风格说明

### 渐变拟物玻璃卡片风格

融合 Apple Keynote 极简主义、现代 SaaS 产品设计和玻璃拟态风格。适合产品演示、技术分享、创意提案。

### 矢量插画风格

扁平化矢量插画，黑色轮廓线 + 复古柔和配色。适合教育演示、儿童内容、品牌展示。

## 许可证

MIT
