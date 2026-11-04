---
name: video-transcript-txt
description: 将一个或多个本地视频转写为带每段开始和结束时间的整理版 TXT，并默认尝试用中性“说话人1/2”标签区分不同声音。当用户要求视频转文字、视频转写、提取视频文本或字幕、区分角色/说话人、批量生成带时间戳 TXT、整理视频口述内容、统计视频处理耗时时使用。通过 uv、ffmpeg/ffprobe、openai-whisper 和可选 pyannote 处理；中间文件写入系统临时目录并自动清理，永不删除源视频。
metadata:
  short-description: 视频转写为带起止时间和可选说话人标签的 TXT
---

# 视频转写为 TXT

将完整下载的本地视频转写为带逐段起止时间的纯文本文件。单视频生成一个 `.txt`；多视频时每个视频独立生成一个 `.txt`，并在全部完成后汇总总视频时长与实际处理总耗时。

默认会尝试说话人分离。这里的“角色/说话人”只表示匿名声音聚类，输出为“说话人1、说话人2……”等中性标签，不代表真实姓名、职业、身份或画面中的人物。

## 输入与输出

- 输入：一个或多个本地视频文件的绝对路径。
- 默认输出：每个视频同目录下的 `<视频文件名>_整理版.txt`。
- 普通转写段落格式：`［HH:MM:SS.mmm - HH:MM:SS.mmm］文本`
- 成功区分说话人时段落格式：`［HH:MM:SS.mmm - HH:MM:SS.mmm］说话人1：文本`
- 输出已存在时默认停止；只有用户明确允许覆盖后才传 `--force`。
- 多视频完成后不生成额外汇总文件；只在回复中汇报汇总结果。

## 硬性规则

1. 不删除、不移动、不修改源视频。
2. 拒绝处理 `.downloading`、`.part`、`.partial` 等未完成下载文件。
3. 每个视频最终只保留一个 TXT；不得在视频目录生成或保留 WAV、JSON、SRT、VTT、TSV、原始 ASR TXT。
4. 所有 Whisper、临时 WAV 和说话人分离中间输出必须进入系统临时目录，成功或失败都要清理。
5. 不编造说话人身份，不根据猜测强行修改人名、职业、角色、数字、剂量或专业术语。
6. “说话人1/2”只按声音聚类首次出现顺序生成；不能自动改成“主持人”“医生”“客户”等真实或语义角色。
7. 用户未指定语言时默认中文 `zh`；用户明确指定时使用其语言。
8. 运行前检查 `uv`、`ffmpeg`、`ffprobe` 是否可用。
9. 多视频并行必须限流；默认尝试说话人分离时最多同时处理 1 个视频，资源充足且视频较短时最多 2 个；关闭说话人分离时默认最多 2 个、最多 3 个。

## 单视频执行

```bash
uv run ~/.claude/skills/video-transcript-txt/scripts/video_transcript_txt.py \
  "/absolute/path/to/video.mp4"
```

指定输出：

```bash
uv run ~/.claude/skills/video-transcript-txt/scripts/video_transcript_txt.py \
  "/absolute/path/to/video.mp4" \
  --output "/absolute/path/to/result.txt"
```

用户已明确允许覆盖时：

```bash
uv run ~/.claude/skills/video-transcript-txt/scripts/video_transcript_txt.py \
  "/absolute/path/to/video.mp4" \
  --force
```

用户明确要求“区分角色/区分说话人”时，必须使用 required：

```bash
uv run ~/.claude/skills/video-transcript-txt/scripts/video_transcript_txt.py \
  "/absolute/path/to/video.mp4" \
  --diarization required
```

用户明确要求不区分说话人时：

```bash
uv run ~/.claude/skills/video-transcript-txt/scripts/video_transcript_txt.py \
  "/absolute/path/to/video.mp4" \
  --diarization off
```

已知就是两个人时：

```bash
uv run ~/.claude/skills/video-transcript-txt/scripts/video_transcript_txt.py \
  "/absolute/path/to/video.mp4" \
  --diarization required \
  --speaker-count 2
```

可选参数：

- `--model`：Whisper 模型，默认 `small`。
- `--language`：语言代码，默认 `zh`。
- `--model-dir`：Whisper 模型缓存目录，默认 `~/.cache/whisper`。
- `--diarization auto|required|off`：说话人分离模式，默认 `auto`。
- `--diarization-model`：pyannote 模型 ID 或本地模型路径，默认 `pyannote/speaker-diarization-community-1`。
- `--speaker-count`：已知精确说话人数。
- `--min-speakers` / `--max-speakers`：说话人数范围，不能和 `--speaker-count` 同时使用。
- `--hf-token-env`：Hugging Face token 所在环境变量名，默认 `HF_TOKEN`。不要把 token 明文写进命令。
- `--force`：覆盖已存在的最终 TXT，仅在用户明确允许时使用。

## 说话人分离依赖

默认模型 `pyannote/speaker-diarization-community-1` 通常需要：

1. Hugging Face 账号。
2. 在模型页面接受使用条款。
3. `HF_TOKEN` 环境变量或本地 Hugging Face 登录缓存具备读取权限。
4. 首次运行联网下载模型；后续使用本地缓存。

脚本不会接收命令行明文 token，也不得在日志、TXT 或 `SUMMARY_JSON` 中输出 token。

## `--diarization` 模式

- `auto`：默认。尝试说话人分离；认证、依赖、模型下载或推理失败时，明确警告并降级为普通转写。
- `required`：用户明确要求区分角色/说话人时使用。说话人分离失败则该视频失败，不生成最终 TXT。
- `off`：完全关闭说话人分离，保持普通 Whisper 转写。

自动降级时不能把所有文本伪标成“说话人1”。只有模型成功返回有效声音聚类时，才输出说话人标签。

## 单视频工作流

1. 校验输入文件、输出后缀和依赖工具。
2. 使用 `ffprobe` 获取视频时长。
3. 创建系统临时目录。
4. 用 `ffmpeg` 在临时目录提取单声道 16 kHz WAV。
5. 用 `uv run --with openai-whisper whisper` 转写临时 WAV，开启 word timestamps，所有格式输出到临时目录。
6. 在 `auto` 或 `required` 下，用 pyannote 对同一临时 WAV 做说话人分离。
7. 将 Whisper 分段/词级时间与说话人区间按时间重叠对齐。
8. 将有效分段按时间顺序写成唯一最终 TXT。
9. 原子替换最终输出并清理临时目录。
10. 汇报最终 TXT 绝对路径、有效段落数量、检测说话人数、视频时长、单视频处理耗时。
11. 读取终端中的 `SUMMARY_JSON:` 行作为机器可读摘要。

## 多视频并行工作流

当用户提供多个视频时，由主 agent 统筹，多名子 agent 分批处理：

1. 主 agent 解析并列出全部视频绝对路径。
2. 主 agent 先做批量预检查：路径存在、普通文件、未命中未完成下载后缀、默认输出路径不冲突、输出不存在或已获覆盖授权。
3. 如果输出已存在且用户未授权覆盖，先询问用户选择：跳过已有输出、允许覆盖、或停止批处理。
4. 记录批处理开始时间。
5. 按并发上限分批派发子 agent：每个子 agent 只处理一个视频，只调用单视频脚本。
6. 默认启用说话人分离时并发 1；资源充足且视频较短时最多 2。只有 `--diarization off` 时才沿用默认并发 2、最多 3。
7. 环境不支持子 agent 或并行时，降级为串行处理；仍执行同样的汇总。
8. 单个视频失败不阻塞其他视频；失败原因进入最终汇总。
9. 所有视频完成后记录结束时间，计算实际处理总耗时。
10. 汇总成功数、失败数、每个 TXT 路径、每个视频时长、每个单视频处理耗时、总视频时长和实际处理总耗时。

### 子 agent 回传字段

每个子 agent 完成后必须回传：

- 源视频绝对路径。
- 输出 TXT 绝对路径。
- `status`：`success` 或 `error`。
- 失败原因；成功时为空。
- 视频时长秒数。
- 有效段落数。
- 单视频实际处理耗时秒数。
- 使用的模型和语言。
- `diarization_requested`、`diarization_status`、`diarization_model`。
- `speaker_count`；未应用说话人分离时为空。
- `diarization_warning`；无警告时为空。

优先从脚本输出的 `SUMMARY_JSON:` 解析这些字段；解析失败时再从中文输出中提取，并说明摘要解析失败。

## 总时长汇报规范

用户说“总时长”但未明确含义时，默认同时汇报两类时长：

- **总视频时长**：所有成功处理视频的媒体时长之和，来自 `ffprobe`。
- **实际处理总耗时**：从主 agent 开始派发第一批任务到所有任务结束的墙钟时间。

多视频并行时，实际处理总耗时通常小于各单视频处理耗时之和；最终回复必须说明这一点。

## 停机条件

出现以下情况时停止对应视频，不生成误导性结果：

- 输入不存在或不是普通文件。
- 输入是未完成下载文件。
- 输出不是 `.txt`。
- 输出已存在且未明确允许覆盖。
- `uv`、`ffmpeg` 或 `ffprobe` 不可用。
- `ffmpeg` 音频提取失败。
- Whisper 失败、JSON 缺失或没有有效文本段。
- `--diarization required` 下 pyannote 认证、依赖、模型下载、推理或有效区间解析失败。

依赖缺失通常影响全部视频，应停止整批处理并提示用户修复环境。单个输入或单个转写失败只停止该视频，其余视频继续。

## 反例黑名单

不要做以下事情：

- 不要把多个视频路径一次性传给单视频脚本。
- 不要无限制启动 agent；启用说话人分离时默认并发 1。
- 不要在未获明确授权时传 `--force`。
- 不要在视频目录留下 WAV、Whisper 中间文件、pyannote JSON 或批量汇总 JSON/TXT。
- 不要把失败视频计入“成功处理的总视频时长”，除非回复中明确单独说明。
- 不要根据上下文猜测说话人、人名、职业、角色、数字、剂量或专业术语。
- 不要把“说话人1/2”改写成真实身份；即使用户说“主持人和医生”，也只能说明系统自动输出中性标签，真实角色需人工校对。
- 不要把“实际处理总耗时”说成“总视频时长”；两者必须分开标注。
