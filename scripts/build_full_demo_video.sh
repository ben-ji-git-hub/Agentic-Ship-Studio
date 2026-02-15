#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="${ROOT_DIR}/.video_output"
ASSETS_DIR="${ROOT_DIR}/.video_assets"
DEMO_REPO="${ROOT_DIR}/demo-repo-video"
PROJECT_NAME="demo-repo-video"
NARRATION_TEXT_FILE="${ROOT_DIR}/VIDEO_NARRATION_5MIN.txt"

RAW_VIDEO="${ASSETS_DIR}/walkthrough_raw.webm"
BASE_VIDEO="${ASSETS_DIR}/walkthrough_base.mp4"
NARRATION_MP3="${ASSETS_DIR}/narration_neural.mp3"
NARRATION_SRT="${ASSETS_DIR}/narration_neural.srt"
NARRATION_PADDED="${ASSETS_DIR}/narration_neural_padded.m4a"
FINAL_VIDEO="${1:-${OUT_DIR}/vibe_sentinel_demo_5min.mp4}"

mkdir -p "${OUT_DIR}" "${ASSETS_DIR}"

if [ ! -d "${ROOT_DIR}/.venv" ]; then
  echo "Error: expected virtual environment at ${ROOT_DIR}/.venv"
  exit 1
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "Error: ffmpeg not found."
  exit 1
fi

echo "Preparing fresh demo project..."
"${ROOT_DIR}/scripts/create_video_demo_repo.sh" "${DEMO_REPO}" --force

echo "Recording full click-through walkthrough (~5 minutes)..."
source "${ROOT_DIR}/.venv/bin/activate"
python "${ROOT_DIR}/scripts/record_demo_playwright.py" \
  --project-path "${PROJECT_NAME}" \
  --output "${RAW_VIDEO}" \
  --host 127.0.0.1 \
  --port 8765

echo "Generating lifelike male neural narration..."
python - "${ROOT_DIR}" "${NARRATION_MP3}" "${NARRATION_TEXT_FILE}" <<'PY'
import asyncio
import sys
from pathlib import Path

import edge_tts

root = Path(sys.argv[1])
out_path = Path(sys.argv[2])
text_path = Path(sys.argv[3])
text = text_path.read_text(encoding="utf-8").strip()
voice = "en-US-AndrewNeural"
rate = "+10%"

async def main() -> None:
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate)
    await communicate.save(str(out_path))

asyncio.run(main())
print(f"wrote narration: {out_path}")
PY

echo "Creating timed subtitles..."
python - "${ROOT_DIR}" "${NARRATION_MP3}" "${NARRATION_SRT}" "${NARRATION_TEXT_FILE}" <<'PY'
import re
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1])
audio_path = Path(sys.argv[2])
srt_path = Path(sys.argv[3])
text_path = Path(sys.argv[4])
text = text_path.read_text(encoding="utf-8").strip()
sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
if not sentences:
    raise SystemExit("narration text is empty")

duration = float(
    subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(audio_path),
        ],
        text=True,
    ).strip()
)

weights = [max(1, len(re.findall(r"\w+", s))) for s in sentences]
total = sum(weights)

def fmt(ts: float) -> str:
    ts = max(0.0, ts)
    h = int(ts // 3600)
    m = int((ts % 3600) // 60)
    s = int(ts % 60)
    ms = int(round((ts - int(ts)) * 1000))
    if ms == 1000:
        ms = 0
        s += 1
    if s == 60:
        s = 0
        m += 1
    if m == 60:
        m = 0
        h += 1
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

cursor = 0.0
blocks = []
for idx, (sentence, weight) in enumerate(zip(sentences, weights), start=1):
    seg = duration * (weight / total)
    start = cursor
    end = duration if idx == len(sentences) else min(duration, cursor + seg)
    cursor = end
    blocks.append(f"{idx}\n{fmt(start)} --> {fmt(end)}\n{sentence}\n")

srt_path.write_text("\n".join(blocks), encoding="utf-8")
print(f"wrote subtitles: {srt_path}")
PY

echo "Normalizing video container..."
ffmpeg -y -i "${RAW_VIDEO}" -an -c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p "${BASE_VIDEO}" >/dev/null 2>&1

VIDEO_DURATION="$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "${BASE_VIDEO}")"
NARRATION_DURATION="$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "${NARRATION_MP3}")"
VIDEO_FOR_MUX="${BASE_VIDEO}"

if awk "BEGIN {exit !(${NARRATION_DURATION} > ${VIDEO_DURATION})}"; then
  EXTRA_SECONDS="$(awk "BEGIN {print ${NARRATION_DURATION}-${VIDEO_DURATION}+0.25}")"
  EXTENDED_VIDEO="${ASSETS_DIR}/walkthrough_base_extended.mp4"
  echo "Narration exceeds video by ~${EXTRA_SECONDS}s; extending video tail..."
  ffmpeg -y -i "${BASE_VIDEO}" -vf "tpad=stop_mode=clone:stop_duration=${EXTRA_SECONDS}" -c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p -an "${EXTENDED_VIDEO}" >/dev/null 2>&1
  VIDEO_FOR_MUX="${EXTENDED_VIDEO}"
  VIDEO_DURATION="$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "${VIDEO_FOR_MUX}")"
fi

echo "Padding narration to full walkthrough duration (${VIDEO_DURATION}s)..."
ffmpeg -y -i "${NARRATION_MP3}" -af "apad" -t "${VIDEO_DURATION}" -c:a aac -b:a 192k "${NARRATION_PADDED}" >/dev/null 2>&1

echo "Muxing final MP4 with subtitle track..."
ffmpeg -y \
  -i "${VIDEO_FOR_MUX}" \
  -i "${NARRATION_PADDED}" \
  -i "${NARRATION_SRT}" \
  -map 0:v:0 \
  -map 1:a:0 \
  -map 2:0 \
  -c:v copy \
  -c:a copy \
  -c:s mov_text \
  "${FINAL_VIDEO}" >/dev/null 2>&1

echo "Done."
echo "Final video: ${FINAL_VIDEO}"
echo "Narration: ${NARRATION_MP3}"
echo "Subtitles: ${NARRATION_SRT}"
