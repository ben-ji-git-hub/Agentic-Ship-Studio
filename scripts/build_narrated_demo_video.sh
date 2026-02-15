#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRAMES_DIR="${ROOT_DIR}/.video_frames/raw"
ASSETS_DIR="${ROOT_DIR}/.video_assets"
OUT_DIR="${ROOT_DIR}/.video_output"
NARRATION_TEXT="${ROOT_DIR}/VIDEO_NARRATION.txt"

OUT_MP4="${1:-${OUT_DIR}/vibe_sentinel_demo_final.mp4}"
VOICE_NAME="${2:-Daniel}"
VOICE_RATE="${3:-175}"

mkdir -p "${ASSETS_DIR}" "${OUT_DIR}"

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "Error: ffmpeg is required but not found on PATH."
  exit 1
fi

if ! command -v say >/dev/null 2>&1; then
  echo "Error: macOS 'say' command is required but not found."
  exit 1
fi

if [ ! -f "${NARRATION_TEXT}" ]; then
  echo "Error: narration text file missing at ${NARRATION_TEXT}"
  exit 1
fi

frames=(
  "${FRAMES_DIR}/01_tutorial_hero.png"
  "${FRAMES_DIR}/02_dashboard_ready.png"
  "${FRAMES_DIR}/03_after_audit.png"
  "${FRAMES_DIR}/04_after_ship.png"
  "${FRAMES_DIR}/05_demo_tour.png"
  "${FRAMES_DIR}/06_artifacts.png"
  "${FRAMES_DIR}/07_openclaw.png"
  "${FRAMES_DIR}/08_tutorial_close.png"
)

for frame in "${frames[@]}"; do
  if [ ! -f "${frame}" ]; then
    echo "Error: missing frame ${frame}"
    exit 1
  fi
done

AUDIO_AIFF="${ASSETS_DIR}/narration.aiff"
AUDIO_WAV="${ASSETS_DIR}/narration.wav"
SUB_SRT="${ASSETS_DIR}/narration.srt"
BASE_VIDEO="${ASSETS_DIR}/base_slideshow.mp4"
FINAL_VIDEO="${OUT_MP4}"

say -v "${VOICE_NAME}" -r "${VOICE_RATE}" -f "${NARRATION_TEXT}" -o "${AUDIO_AIFF}"
ffmpeg -y -i "${AUDIO_AIFF}" -ar 48000 -ac 1 "${AUDIO_WAV}" >/dev/null 2>&1

python3 - "${NARRATION_TEXT}" "${AUDIO_WAV}" "${SUB_SRT}" <<'PY'
import re
import sys
import wave
from pathlib import Path

text_path = Path(sys.argv[1])
audio_path = Path(sys.argv[2])
srt_path = Path(sys.argv[3])

text = text_path.read_text(encoding="utf-8").strip()
if not text:
    raise SystemExit("Narration text is empty")

with wave.open(str(audio_path), "rb") as wav:
    frames = wav.getnframes()
    rate = wav.getframerate()
    duration = frames / float(rate)

sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
if not sentences:
    sentences = [text]

weights = [max(1, len(re.findall(r"\w+", s))) for s in sentences]
total = sum(weights)

def fmt(ts: float) -> str:
    ts = max(0.0, ts)
    hours = int(ts // 3600)
    mins = int((ts % 3600) // 60)
    secs = int(ts % 60)
    millis = int(round((ts - int(ts)) * 1000))
    if millis == 1000:
        millis = 0
        secs += 1
    if secs == 60:
        secs = 0
        mins += 1
    if mins == 60:
        mins = 0
        hours += 1
    return f"{hours:02d}:{mins:02d}:{secs:02d},{millis:03d}"

cursor = 0.0
lines = []
for idx, (sentence, weight) in enumerate(zip(sentences, weights), start=1):
    seg = duration * (weight / total)
    start = cursor
    end = duration if idx == len(sentences) else min(duration, cursor + seg)
    cursor = end
    lines.append(f"{idx}\n{fmt(start)} --> {fmt(end)}\n{sentence}\n")

srt_path.write_text("\n".join(lines), encoding="utf-8")
PY

FRAME_SEC=12
FPS=30

input_args=()
filter_graph=""
concat_inputs=""

for idx in "${!frames[@]}"; do
  input_args+=(-framerate "${FPS}" -loop 1 -t "${FRAME_SEC}" -i "${frames[$idx]}")
  filter_graph+="[${idx}:v]setpts=PTS-STARTPTS,scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,format=yuv420p[v${idx}];"
  concat_inputs+="[v${idx}]"
done
filter_graph+="${concat_inputs}concat=n=${#frames[@]}:v=1:a=0[vout]"

ffmpeg -y "${input_args[@]}" \
  -filter_complex "${filter_graph}" \
  -map "[vout]" \
  -r "${FPS}" \
  -pix_fmt yuv420p \
  -c:v libx264 \
  -preset medium \
  -crf 20 \
  "${BASE_VIDEO}"

pushd "${ROOT_DIR}" >/dev/null
ffmpeg -y \
  -i "${BASE_VIDEO}" \
  -i "${AUDIO_WAV}" \
  -i "${SUB_SRT}" \
  -map 0:v:0 \
  -map 1:a:0 \
  -map 2:0 \
  -c:v copy \
  -c:a aac \
  -b:a 192k \
  -c:s mov_text \
  -shortest \
  "${FINAL_VIDEO}"
popd >/dev/null

echo "Created narrated demo video: ${FINAL_VIDEO}"
echo "Subtitles: ${SUB_SRT}"
echo "Narration audio: ${AUDIO_WAV}"
