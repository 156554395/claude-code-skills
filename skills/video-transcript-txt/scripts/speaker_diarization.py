#!/usr/bin/env python3
"""Run pyannote speaker diarization and emit normalized JSON."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("audio", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--model", default="pyannote/speaker-diarization-community-1")
    parser.add_argument("--token-env", default="HF_TOKEN")
    parser.add_argument("--speaker-count", type=int)
    parser.add_argument("--min-speakers", type=int)
    parser.add_argument("--max-speakers", type=int)
    return parser.parse_args()


def redact_secret(text: str, env_name: str) -> str:
    secret = os.environ.get(env_name)
    return text.replace(secret, "[REDACTED]") if secret else text


def main() -> int:
    args = parse_args()
    token = os.environ.get(args.token_env)
    try:
        import torch
        from pyannote.audio import Pipeline

        pipeline = Pipeline.from_pretrained(args.model, token=token)
        pipeline.to(torch.device("cpu"))
        kwargs = {}
        if args.speaker_count is not None:
            kwargs["num_speakers"] = args.speaker_count
        else:
            if args.min_speakers is not None:
                kwargs["min_speakers"] = args.min_speakers
            if args.max_speakers is not None:
                kwargs["max_speakers"] = args.max_speakers
        diarization = pipeline(str(args.audio), **kwargs)
        annotation = getattr(diarization, "exclusive_speaker_diarization", diarization)
        intervals = []
        for turn, _, speaker in annotation.itertracks(yield_label=True):
            start = float(turn.start)
            end = float(turn.end)
            if end > start:
                intervals.append({"start": start, "end": end, "speaker": str(speaker)})
        args.output.write_text(json.dumps(intervals, ensure_ascii=False), encoding="utf-8")
        return 0
    except Exception as exc:
        detail = redact_secret(str(exc), args.token_env)
        print(f"说话人分离失败：{detail}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
