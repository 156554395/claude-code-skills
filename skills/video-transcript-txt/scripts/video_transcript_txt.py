#!/usr/bin/env python3
"""Transcribe one local video into one timestamped, speaker-aware TXT file."""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


BLOCKED_SUFFIXES = (".downloading", ".part", ".partial")
DEFAULT_DIARIZATION_MODEL = "pyannote/speaker-diarization-community-1"
PYANNOTE_VERSION = "4.0.7"
UNKNOWN_SPEAKER = "说话人未知"


def run_checked(command: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, text=True, capture_output=capture)


def require_command(name: str) -> None:
    if shutil.which(name) is None:
        raise RuntimeError(f"找不到必要命令：{name}")


def format_timestamp(seconds: float) -> str:
    total_ms = max(0, int(round(seconds * 1000)))
    hours, remainder = divmod(total_ms, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def get_duration(video: Path) -> float | None:
    result = run_checked(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(video),
        ],
        capture=True,
    )
    try:
        return float(result.stdout.strip())
    except ValueError:
        return None


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("说话人数必须大于或等于 1")
    return parsed


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="将本地视频转写为带时间戳和说话人标签的 TXT")
    parser.add_argument("video", type=Path, help="本地视频路径")
    parser.add_argument("--output", type=Path, help="最终 TXT 路径")
    parser.add_argument("--model", default="small", help="Whisper 模型，默认 small")
    parser.add_argument("--language", default="zh", help="语言代码，默认 zh")
    parser.add_argument(
        "--model-dir",
        type=Path,
        default=Path.home() / ".cache" / "whisper",
        help="Whisper 模型缓存目录",
    )
    parser.add_argument(
        "--diarization",
        choices=("auto", "required", "off"),
        default="auto",
        help="说话人分离模式，默认 auto",
    )
    parser.add_argument(
        "--diarization-model",
        default=DEFAULT_DIARIZATION_MODEL,
        help="pyannote 模型 ID 或本地模型路径",
    )
    parser.add_argument("--speaker-count", type=positive_int, help="已知的说话人数")
    parser.add_argument("--min-speakers", type=positive_int, help="最少说话人数")
    parser.add_argument("--max-speakers", type=positive_int, help="最多说话人数")
    parser.add_argument(
        "--hf-token-env",
        default="HF_TOKEN",
        help="Hugging Face token 所在的环境变量名，默认 HF_TOKEN",
    )
    parser.add_argument("--force", action="store_true", help="覆盖已有输出")
    args = parser.parse_args(argv)
    validate_diarization_args(parser, args)
    return args


def validate_diarization_args(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    has_range = args.min_speakers is not None or args.max_speakers is not None
    if args.speaker_count is not None and has_range:
        parser.error("--speaker-count 不能与 --min-speakers/--max-speakers 同时使用")
    if (
        args.min_speakers is not None
        and args.max_speakers is not None
        and args.max_speakers < args.min_speakers
    ):
        parser.error("--max-speakers 不能小于 --min-speakers")
    if args.diarization == "off" and (args.speaker_count is not None or has_range):
        parser.error("--diarization off 不能与说话人数参数同时使用")


def validate_paths(video: Path, output: Path, force: bool) -> None:
    if not video.exists() or not video.is_file():
        raise RuntimeError(f"输入视频不存在或不是普通文件：{video}")
    if video.name.lower().endswith(BLOCKED_SUFFIXES):
        raise RuntimeError(f"拒绝处理未完成下载文件：{video}")
    if video == output:
        raise RuntimeError("输出路径不能覆盖源视频")
    if output.suffix.lower() != ".txt":
        raise RuntimeError("最终输出必须是 .txt 文件")
    if output.exists() and not force:
        raise RuntimeError(f"输出已存在；如需覆盖请明确传入 --force：{output}")
    output.parent.mkdir(parents=True, exist_ok=True)


def find_json(directory: Path, stem: str) -> Path:
    expected = directory / f"{stem}.json"
    if expected.exists():
        return expected
    candidates = list(directory.glob("*.json"))
    if len(candidates) != 1:
        raise RuntimeError("Whisper 没有生成唯一的 JSON 转写结果")
    return candidates[0]


def normalize_intervals(raw: object) -> list[dict]:
    if not isinstance(raw, list):
        raise RuntimeError("说话人分离 JSON 根节点不是列表")
    intervals = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        speaker = str(item.get("speaker", "")).strip()
        try:
            start = float(item["start"])
            end = float(item["end"])
        except (KeyError, TypeError, ValueError):
            continue
        if speaker and math.isfinite(start) and math.isfinite(end) and end > start:
            intervals.append({"start": start, "end": end, "speaker": speaker})
    intervals.sort(key=lambda item: (item["start"], item["end"]))
    return intervals


def build_speaker_labels(intervals: list[dict]) -> dict[str, str]:
    labels = {}
    for interval in intervals:
        speaker = interval["speaker"]
        if speaker not in labels:
            labels[speaker] = f"说话人{len(labels) + 1}"
    return labels


def assign_speaker(start: float, end: float, intervals: list[dict]) -> str | None:
    overlaps = []
    for interval in intervals:
        overlap = max(0.0, min(end, interval["end"]) - max(start, interval["start"]))
        if overlap > 0:
            overlaps.append((overlap, interval["speaker"]))
    if overlaps:
        return max(overlaps, key=lambda item: item[0])[1]
    midpoint = (start + end) / 2
    for interval in intervals:
        if interval["start"] <= midpoint <= interval["end"]:
            return interval["speaker"]
    return None


def parse_segment(segment: object) -> tuple[float, float, str] | None:
    if not isinstance(segment, dict):
        return None
    text = str(segment.get("text", "")).strip()
    try:
        start = float(segment["start"])
        end = float(segment["end"])
    except (KeyError, TypeError, ValueError):
        return None
    if not text or not math.isfinite(start) or not math.isfinite(end) or end < start:
        return None
    return start, end, text


def speaker_rows(segments: object, intervals: list[dict]) -> list[dict]:
    if not isinstance(segments, list):
        raise RuntimeError("Whisper JSON 中的 segments 不是列表")
    labels = build_speaker_labels(intervals)
    rows = []
    for segment in segments:
        parsed = parse_segment(segment)
        if parsed is None:
            continue
        segment_start, segment_end, segment_text = parsed
        words = segment.get("words") if isinstance(segment, dict) else None
        valid_words = []
        if isinstance(words, list):
            for word in words:
                if not isinstance(word, dict):
                    continue
                text = str(word.get("word", ""))
                try:
                    start = float(word["start"])
                    end = float(word["end"])
                except (KeyError, TypeError, ValueError):
                    continue
                if text and math.isfinite(start) and math.isfinite(end) and end >= start:
                    valid_words.append((start, end, text, assign_speaker(start, end, intervals)))
        if not valid_words:
            speaker = assign_speaker(segment_start, segment_end, intervals)
            rows.append({
                "start": segment_start,
                "end": segment_end,
                "text": segment_text,
                "speaker": labels.get(speaker, UNKNOWN_SPEAKER),
            })
            continue
        group = None
        for start, end, text, speaker in valid_words:
            label = labels.get(speaker, UNKNOWN_SPEAKER)
            if group is None or group["speaker"] != label:
                if group is not None:
                    group["text"] = group["text"].strip()
                    if group["text"]:
                        rows.append(group)
                group = {"start": start, "end": end, "text": text, "speaker": label}
            else:
                group["end"] = end
                group["text"] += text
        if group is not None:
            group["text"] = group["text"].strip()
            if group["text"]:
                rows.append(group)
    return rows


def plain_rows(segments: object) -> list[dict]:
    if not isinstance(segments, list):
        raise RuntimeError("Whisper JSON 中的 segments 不是列表")
    rows = []
    for segment in segments:
        parsed = parse_segment(segment)
        if parsed is not None:
            start, end, text = parsed
            rows.append({"start": start, "end": end, "text": text})
    return rows


def build_text(
    video: Path,
    duration: float | None,
    language: str,
    segments: object,
    *,
    diarization_status: str,
    diarization_model: str,
    intervals: list[dict] | None = None,
    diarization_warning: str | None = None,
) -> tuple[str, int, int | None]:
    applied = diarization_status == "applied"
    rows = speaker_rows(segments, intervals or []) if applied else plain_rows(segments)
    if not rows:
        raise RuntimeError("转写结果没有有效文本段")
    speaker_count = len(build_speaker_labels(intervals or [])) if applied else None
    status_text = {
        "applied": "已应用",
        "fallback": "未应用，已降级为普通转写",
        "off": "已关闭",
    }[diarization_status]
    lines = [
        f"{video.stem} 视频转写整理版",
        "",
        "基本信息",
        "",
        f"源视频：{video.name}",
        f"视频时长：约 {duration:.2f} 秒" if duration is not None else "视频时长：未知",
        "转写模型：Whisper",
        f"语言：{language}",
        f"说话人分离：{status_text}",
    ]
    if applied:
        lines.extend([
            "说话人标签：按首次出现顺序生成的中性标签，不代表真实身份",
            f"检测说话人数：{speaker_count}",
            f"说话人分离模型：{diarization_model}",
        ])
    elif diarization_warning:
        lines.append(f"降级原因：{diarization_warning}")
    lines.extend(["时间格式：［开始时间 - 结束时间］", "", "整理后内容", ""])
    for row in rows:
        prefix = f"［{format_timestamp(row['start'])} - {format_timestamp(row['end'])}］"
        speaker = f"{row['speaker']}：" if applied else ""
        lines.append(f"{prefix}{speaker}{row['text']}")
    lines.extend([
        "",
        (
            "说明：以上为自动转写和自动说话人聚类结果；“说话人1/2”等仅区分声音聚类，"
            "不代表真实身份；专业术语、数字、重叠发言和说话人边界请结合原视频复核。"
            if applied
            else "说明：以上为自动转写整理结果；专业术语、数字和说话人如需正式使用，请结合原视频复核。"
        ),
        "",
    ])
    return "\n".join(lines), len(rows), speaker_count


def extract_audio(video: Path, audio: Path) -> None:
    run_checked([
        "ffmpeg",
        "-v",
        "error",
        "-y",
        "-i",
        str(video),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "pcm_s16le",
        str(audio),
    ])


def redact_secret(text: str, env_name: str) -> str:
    secret = os.environ.get(env_name)
    return text.replace(secret, "[REDACTED]") if secret else text


def run_diarization(args: argparse.Namespace, audio: Path, output: Path) -> list[dict]:
    helper = Path(__file__).with_name("speaker_diarization.py")
    command = [
        "uv",
        "run",
        "--python",
        "3.11",
        "--with",
        f"pyannote.audio=={PYANNOTE_VERSION}",
        str(helper),
        str(audio),
        str(output),
        "--model",
        args.diarization_model,
        "--token-env",
        args.hf_token_env,
    ]
    for name, value in (
        ("--speaker-count", args.speaker_count),
        ("--min-speakers", args.min_speakers),
        ("--max-speakers", args.max_speakers),
    ):
        if value is not None:
            command.extend([name, str(value)])
    try:
        run_checked(command, capture=True)
    except subprocess.CalledProcessError as exc:
        detail = redact_secret((exc.stderr or exc.stdout or "未知错误").strip(), args.hf_token_env)
        raise RuntimeError(f"说话人分离执行失败：{detail}") from exc
    intervals = normalize_intervals(json.loads(output.read_text(encoding="utf-8")))
    if not intervals:
        raise RuntimeError("说话人分离没有返回有效区间")
    return intervals


def write_atomic(output: Path, content: str) -> None:
    fd, temporary_output = tempfile.mkstemp(
        prefix=f".{output.stem}-", suffix=".tmp", dir=output.parent, text=True
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        os.replace(temporary_output, output)
    except Exception:
        Path(temporary_output).unlink(missing_ok=True)
        raise


def print_summary(summary: dict, *, error: bool = False) -> None:
    stream = sys.stderr if error else sys.stdout
    print(f"SUMMARY_JSON: {json.dumps(summary, ensure_ascii=False)}", file=stream)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    video = args.video.expanduser().resolve()
    output = (args.output or video.with_name(f"{video.stem}_整理版.txt")).expanduser().resolve()
    started = time.perf_counter()
    duration = None
    diarization_status = "off" if args.diarization == "off" else "error"
    diarization_warning = None
    speaker_count = None
    try:
        validate_paths(video, output, args.force)
        for command in ("uv", "ffmpeg", "ffprobe"):
            require_command(command)
        duration = get_duration(video)
        with tempfile.TemporaryDirectory(prefix="video-transcript-txt-") as temp_name:
            temp_dir = Path(temp_name)
            audio = temp_dir / "audio.wav"
            whisper_dir = temp_dir / "whisper"
            whisper_dir.mkdir()
            extract_audio(video, audio)
            run_checked([
                "uv",
                "run",
                "--with",
                "openai-whisper",
                "whisper",
                str(audio),
                "--model",
                args.model,
                "--model_dir",
                str(args.model_dir.expanduser()),
                "--language",
                args.language,
                "--task",
                "transcribe",
                "--device",
                "cpu",
                "--fp16",
                "False",
                "--word_timestamps",
                "True",
                "--output_dir",
                str(whisper_dir),
                "--output_format",
                "all",
            ])
            result_path = find_json(whisper_dir, audio.stem)
            data = json.loads(result_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise RuntimeError("Whisper JSON 根节点不是对象")
            intervals = None
            if args.diarization != "off":
                try:
                    intervals = run_diarization(args, audio, temp_dir / "diarization.json")
                    diarization_status = "applied"
                except (OSError, RuntimeError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
                    if args.diarization == "required":
                        raise RuntimeError(f"必须完成说话人分离，但处理失败：{exc}") from exc
                    diarization_status = "fallback"
                    diarization_warning = str(exc)
                    print(f"警告：{diarization_warning}；已降级为普通转写。", file=sys.stderr)
            content, segment_count, speaker_count = build_text(
                video,
                duration,
                args.language,
                data.get("segments", []),
                diarization_status=diarization_status,
                diarization_model=args.diarization_model,
                intervals=intervals,
                diarization_warning=diarization_warning,
            )
            write_atomic(output, content)
        processing_duration = time.perf_counter() - started
        print(f"已生成：{output}")
        print(f"段落数：{segment_count}")
        if speaker_count is not None:
            print(f"检测说话人数：{speaker_count}")
        print(f"视频时长：{duration:.2f} 秒" if duration is not None else "视频时长：未知")
        print(f"处理耗时：{processing_duration:.2f} 秒")
        print_summary({
            "status": "success",
            "video": str(video),
            "output": str(output),
            "segments": segment_count,
            "video_duration_seconds": duration,
            "processing_duration_seconds": processing_duration,
            "model": args.model,
            "language": args.language,
            "diarization_requested": args.diarization,
            "diarization_status": diarization_status,
            "diarization_model": args.diarization_model,
            "speaker_count": speaker_count,
            "diarization_warning": diarization_warning,
        })
        return 0
    except (OSError, RuntimeError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        processing_duration = time.perf_counter() - started
        error_message = redact_secret(str(exc), args.hf_token_env)
        print(f"错误：{error_message}", file=sys.stderr)
        print_summary({
            "status": "error",
            "video": str(video),
            "output": str(output),
            "video_duration_seconds": duration,
            "processing_duration_seconds": processing_duration,
            "model": args.model,
            "language": args.language,
            "diarization_requested": args.diarization,
            "diarization_status": "error",
            "diarization_model": args.diarization_model,
            "speaker_count": None,
            "diarization_warning": None,
            "error": error_message,
        }, error=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
