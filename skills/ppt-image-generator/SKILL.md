---
name: ppt-image-generator
description: PPT幻灯片图片生成技能。使用豆包Seedream模型直接生成高质量PPT幻灯片图片。当用户需要生成PPT图片、创建幻灯片视觉内容时使用此技能。
---

# PPT幻灯片图片生成技能

## 技能概述

使用豆包 Seedream AI 模型直接生成高质量 PPT 幻灯片图片，并自动下载到本地。

**完全并发**：每张图片使用一个独立的 subAgent，最大化并发性能！

## 前置检查

**在开始工作流程之前，必须先检查 MCP 工具是否可用：**

```javascript
// 检查豆包 MCP 工具是否安装
const hasDoubaoMCP = availableTools.includes('mcp__doubao-giv__generate_image');

if (!hasDoubaoMCP) {
  console.log(`
╔════════════════════════════════════════════════════════════╗
║  ⚠️  豆包 MCP 工具未安装                                  ║
╠════════════════════════════════════════════════════════════╣
║  PPT 图片生成功能需要安装 doubao-giv MCP 服务器          ║
║                                                           ║
║  在 Claude Code 配置文件中添加：                          ║
║                                                           ║
║  {                                                        ║
║    "mcpServers": {                                        ║
║      "doubao-giv": {                                      ║
║        "command": "npx",                                  ║
║        "args": ["-y", "doubao-image-video-mcp@latest"],  ║
║        "env": {                                           ║
║          "DOUBAO_API_KEY": "your_api_key_here",          ║
║          "DOUBAO_IMAGE_ENDPOINT_ID": "ep-20241227-xxxx", ║
║          "DOUBAO_VIDEO_ENDPOINT_ID": "ep-20241227-xxxx"  ║
║        }                                                  ║
║      }                                                    ║
║    }                                                      ║
║  }                                                        ║
║                                                           ║
║  配置完成后重启 Claude Code                               ║
╚════════════════════════════════════════════════════════════╝
  `);
  return; // 结束技能执行
}
```

**只有确认 MCP 工具可用后，才继续执行以下工作流程。**

## 工作流程

### 第1步：确认图片数量

首先询问用户：
```
需要生成几张PPT图片？
```

用户输入数量后，继续下一步。

### 第2步：选择风格

展示风格选项让用户选择：

```
请选择PPT风格：

【1】渐变拟物玻璃卡片风格 (gradient-glass)
   特点：融合Apple Keynote极简主义、现代SaaS设计和玻璃拟态
   - 高端、沉浸、洁净有呼吸感
   - 3D玻璃物体 + 磨砂玻璃容器
   - 极光渐变色背景（霓虹紫、电光蓝、柔和珊瑚橙、青色）
   - 适合：产品演示、技术分享、创意提案

【2】矢量插画风格 (vector-illustration)
   特点：扁平化矢量插画，黑色轮廓线 + 复古柔和配色
   - 清晰的黑色单线描边，填色书风格
   - 几何化简化，玩具模型般的可爱感
   - 米色纸张纹理 + 复古色调（珊瑚红、薄荷绿、芥末黄）
   - 适合：教育演示、儿童内容、品牌展示

请输入 1 或 2 选择风格：
```

### 第3步：收集每张幻灯片内容

逐张询问每张幻灯片的信息：

```
第 1 张幻灯片：
1. 类型（封面/内容/数据）？
2. 内容文字？

第 2 张幻灯片：
1. 类型（封面/内容/数据）？
2. 内容文字？

...（重复直到收集完所有幻灯片）
```

### 第4步：创建统一输出目录

在启动 subAgent 之前，先创建统一的输出目录：

```bash
OUTPUT_DIR="ppt_images_output/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUTPUT_DIR"
```

### 第5步：为每张图片启动一个 subAgent

**每张图片使用一个独立的 subAgent**

所有 subAgent 同时启动，实现完全并发：

```
# 第1张图片的Agent
Task(subagent_type="general-purpose",
     prompt="生成第1张幻灯片...\n输出目录: $OUTPUT_DIR",
     run_in_background=true)

# 第2张图片的Agent
Task(subagent_type="general-purpose",
     prompt="生成第2张幻灯片...\n输出目录: $OUTPUT_DIR",
     run_in_background=true)

# 第3张图片的Agent
Task(subagent_type="general-purpose",
     prompt="生成第3张幻灯片...\n输出目录: $OUTPUT_DIR",
     run_in_background=true)

# ...继续为每张图片启动Agent
```

### 第6步：等待所有 subAgent 完成

等待所有后台任务完成，然后收集结果。

### 第7步：完成反馈

所有 subAgent 完成后：
1. 检查输出目录中的所有图片
2. 合并所有结果到统一的 `prompts.json`
3. 输出：
   - 保存的图片路径
   - prompts.json 路径
   - 每张图片的生成状态
   - 总耗时

---

## 风格1：渐变拟物玻璃卡片风格 (gradient-glass)

### 基础提示词

```
你是一位专家级UI UX演示设计师，请生成高保真、未来科技感的16比9演示文稿幻灯片。

全局视觉语言：融合Apple Keynote的极简主义、现代SaaS产品设计和玻璃拟态风格。整体氛围高端、沉浸、洁净且有呼吸感。光照采用电影级体积光、柔和的光线追踪反射和环境光遮蔽。配色方案选择深邃的虚空黑或纯净的陶瓷白作为基底，并以流动的极光渐变色（霓虹紫、电光蓝、柔和珊瑚橙、青色）作为背景和UI高光点缀。

排版引擎采用Bento便当盒网格系统，将内容组织在模块化的圆角矩形容器中。容器材质必须是带有模糊效果的磨砂玻璃，具有精致的白色边缘和柔和的投影，并强制保留巨大的内部留白。

字体使用干净的无衬线字体，建立高对比度。
```

### 封面页提示词模板

```
{基础提示词}

请根据视觉平衡美学，生成封面页。在中心放置一个巨大的复杂3D玻璃物体，并覆盖粗体大字：

{内容}

背景有延伸的极光波浪。
```

### 内容页提示词模板

```
{基础提示词}

请生成内容页。使用Bento网格布局，将以下内容组织在模块化的圆角矩形容器中，容器材质必须是带有模糊效果的磨砂玻璃：

{内容}

保留巨大的内部留白，避免拥挤。
```

### 数据页提示词模板

```
{基础提示词}

请生成数据页或总结页。使用分屏设计，左侧排版以下文字，右侧悬浮巨大的发光3D数据可视化图表（使用发光的3D甜甜圈图、胶囊状进度条或悬浮数字）：

{内容}

图表应看起来像发光的霓虹灯玩具。
```

---

## 风格2：矢量插画风格 (vector-illustration)

### 基础提示词

```
你是一位专家级插画设计师，请生成16比9的矢量插画风格演示文稿幻灯片。

**视觉风格与美术指导**

插画风格：扁平化矢量插画（Flat Vector Illustration）。必须包含清晰、统一粗细的黑色轮廓线（Monoline/Stroke）。色彩填涂需简洁，仅使用少量阴影，严禁使用渐变色或3D渲染效果。

构图形式：横向全景式构图，占据版面顶部 1/3 的空间。

线条风格：必须使用统一粗细的黑色单线描边。所有物体都必须有封闭的黑色轮廓，类似填色书的线稿风格。线条末端圆润。

几何化处理：将复杂的物体简化为基本几何形状。树木简化为棒棒糖形状，建筑物简化为矩形块面。追求"玩具模型"般的可爱感。

空间与透视：采用平视或稍微俯视的 2.5D 视角。通过图层的前后遮挡来表现纵深。

装饰元素：在空白处添加装饰性的几何元素，如放射状的线条、药丸形状的云朵、小圆点和星星。

**配色方案**

背景：米色/奶油色纸张纹理感底色。

强调色：珊瑚红、薄荷绿、芥末黄、赭石色和岩石蓝。复古且柔和的色调。

**字体排版**

主标题：巨大的、加粗的复古衬线体，体现权威感与优雅感。

副标题：位于矩形色块内的全大写无衬线体。

正文：清晰易读的几何感无衬线体。
```

### 封面页提示词模板

```
{基础提示词}

请生成封面页。在顶部1/3区域绘制横向全景式的矢量插画场景，包含几何化简化的建筑、树木和装饰元素。

主标题使用巨大的复古衬线体，内容为：

{内容}

背景使用米色/奶油色纸张纹理。
```

### 内容页提示词模板

```
{基础提示词}

请生成内容页。顶部绘制横向插画装饰带。

内容区域展示以下要点，每个要点配合简洁的矢量图标，所有元素都有统一的黑色轮廓线：

{内容}

使用彩色矩形块（珊瑚红、薄荷绿、芥末黄）分隔不同要点。
```

### 数据页提示词模板

```
{基础提示词}

请生成数据页。使用几何化的矢量图表形式展示以下数据，所有图表元素都有清晰的黑色轮廓：

{内容}

配色使用复古柔和色调，添加装饰性的几何元素（小圆点、星星、放射线）平衡画面。
```

---

## 单图片 subAgent 任务格式

每个 subAgent 只负责生成一张图片：

```
你是PPT图片生成助手。请完成以下任务：

【任务信息】
- 输出目录：{OUTPUT_DIR}
- 幻灯片编号：{slide_number}
- 幻灯片类型：{type}（cover/content/data）
- 幻灯片内容：{content}
- 风格：{style}

【操作步骤】
1. 根据类型和内容生成完整的图片生成提示词
2. 调用 mcp__doubao-giv__generate_image 生成图片
   - prompt: 生成的完整提示词
   - size: "2560x1440"
   - watermark: false
3. 将返回的图片URL下载到 {OUTPUT_DIR}/slide-{slide_number:02d}.png
4. 返回结果：{slide_number, success, local_path, file_size}

【{style}风格的提示词模板】
{完整的风格提示词模板内容}
```

---

## 并发生成实现

### 完全并发策略

**每张图片一个 subAgent**：

| 幻灯片数量 | subAgent 数量 | 并发策略 |
|-----------|---------------|----------|
| 1张 | 1个 | 单独处理 |
| 2张 | 2个 | 同时处理 |
| 3张 | 3个 | 同时处理 |
| 4张 | 4个 | 同时处理 |
| 5张 | 5个 | 同时处理 |
| ... | ... | ... |
| 8张 | 8个 | 同时处理 |

### 调用示例

```
# 先创建统一目录
OUTPUT_DIR=ppt_images_output/$(date +%Y%m%d_%H%M%S)
mkdir -p $OUTPUT_DIR

# 为每张图片启动一个独立的Agent
for i in {1..8}; do
  Task(subagent_type="general-purpose",
       prompt="生成第${i}张幻灯片\n输出目录: $OUTPUT_DIR\n...",
       run_in_background=true)
done

# 等待所有Agent完成
```

### 性能优势

```
顺序生成：8张 × ~1分钟 = 8分钟
每张一个Agent：8张同时进行 × ~1分钟 = 1分钟

速度提升：约8倍！
```

---

## 豆包MCP参数说明

- **prompt**: 图片描述文本（使用上面对应风格的提示词模板）
- **size**: "2560x1440" (16:9，推荐)
- **model**: "doubao-seedream-4-5"
- **watermark**: false
- **endpoint_id**: （可选）推荐在火山引擎控制台创建推理接入点后使用

## 图片下载实现

豆包 MCP 返回图片URL后，使用以下方式下载到本地：

```bash
# 下载图片到统一目录
curl -o {OUTPUT_DIR}/slide-{slide_number:02d}.png "图片URL"
```

或者使用 Python：

```python
import urllib.request
import os

# 确保目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 下载到统一目录
urllib.request.urlretrieve(url, f"{OUTPUT_DIR}/slide-{slide_number:02d}.png")
```

## 输出结构

```
ppt_images_output/
└── 20240227_120000/          # 统一输出目录
    ├── slide-01.png          # Agent 1 生成
    ├── slide-02.png          # Agent 2 生成
    ├── slide-03.png          # Agent 3 生成
    ├── slide-04.png          # Agent 4 生成
    ├── slide-05.png          # Agent 5 生成
    ├── slide-06.png          # Agent 6 生成
    ├── slide-07.png          # Agent 7 生成
    ├── slide-08.png          # Agent 8 生成
    └── prompts.json          # 统一的结果记录
```

## prompts.json 格式

```json
{
  "style": "gradient-glass",
  "total_slides": 8,
  "output_dir": "ppt_images_output/20240227_120000",
  "generated_at": "2024-02-27T12:00:00",
  "parallel_mode": "per-slide",
  "agents_count": 8,
  "slides": [
    {
      "slide_number": 1,
      "type": "cover",
      "content": "标题内容",
      "prompt": "完整提示词...",
      "image_url": "豆包返回的URL",
      "local_path": "slide-01.png",
      "status": "success",
      "file_size": "650KB",
      "agent": "Agent 1"
    }
  ]
}
```

## 使用示例

**用户输入**:
```
生成3张PPT图片
```

**技能交互流程**:
1. 确认：需要生成3张图片
2. 选择风格：用户选择 1
3. 逐张收集内容：
   - 第1张（封面）：标题文字
   - 第2张（内容）：正文内容
   - 第3张（数据）：总结内容
4. 创建统一输出目录：`ppt_images_output/20240227_120000/`
5. **启动3个 subAgent，每个处理一张图片**
6. 等待所有图片生成完成
7. 输出结果：
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
