#!/usr/bin/env bash
set -euo pipefail

mkdir -p video /tmp/rukna-nahi
FONT="/usr/share/fonts/truetype/noto/NotoSansGurmukhi-Regular.ttf"
if [[ ! -f "$FONT" ]]; then
  FONT="$(find /usr/share/fonts -iname '*Gurmukhi*Regular*.ttf' -o -iname '*Gurmukhi*.otf' | head -n 1)"
fi
if [[ -z "${FONT:-}" || ! -f "$FONT" ]]; then
  echo "Punjabi/Gurmukhi font was not found." >&2
  exit 1
fi

scenes=(
  "scenes/01-the-dream.svg"
  "scenes/02-knocking-on-doors.svg"
  "scenes/03-the-fall.svg"
  "scenes/04-rising-again.svg"
  "scenes/05-hard-work.svg"
  "scenes/06-victory.svg"
)
captions=(
  "captions/01.txt"
  "captions/02.txt"
  "captions/03.txt"
  "captions/04.txt"
  "captions/05.txt"
  "captions/06.txt"
)

for i in ${!scenes[@]}; do
  out="/tmp/rukna-nahi/scene-$((i+1)).mp4"
  ffmpeg -y -loglevel error \
    -loop 1 -framerate 30 -t 5 -i "${scenes[$i]}" \
    -vf "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,format=yuv420p,drawtext=fontfile=${FONT}:textfile=${captions[$i]}:fontcolor=white:fontsize=48:line_spacing=14:x=(w-text_w)/2:y=h*0.73:box=1:boxcolor=black@0.52:boxborderw=26" \
    -an -c:v libx264 -preset veryfast -crf 21 -pix_fmt yuv420p -t 5 "$out"
done

printf "file '%s'\n" /tmp/rukna-nahi/scene-1.mp4 /tmp/rukna-nahi/scene-2.mp4 /tmp/rukna-nahi/scene-3.mp4 /tmp/rukna-nahi/scene-4.mp4 /tmp/rukna-nahi/scene-5.mp4 /tmp/rukna-nahi/scene-6.mp4 > /tmp/rukna-nahi/concat.txt
ffmpeg -y -loglevel error -f concat -safe 0 -i /tmp/rukna-nahi/concat.txt -c copy /tmp/rukna-nahi/muted.mp4

# Soft synthesized instrumental bed (not a vocal recording).
ffmpeg -y -loglevel error -i /tmp/rukna-nahi/muted.mp4 \
  -f lavfi -i "aevalsrc=0.10*sin(2*PI*220*t)+0.07*sin(2*PI*277.18*t)+0.06*sin(2*PI*329.63*t)+0.04*sin(2*PI*440*t):s=44100:d=30" \
  -filter_complex "[1:a]afade=t=in:st=0:d=2,afade=t=out:st=27:d=3,volume=0.45[music]" \
  -map 0:v:0 -map "[music]" -t 30 -c:v copy -c:a aac -b:a 128k -shortest -movflags +faststart video/rukna-nahi-30s.mp4

ffprobe -v error -show_entries format=duration,size -of default=noprint_wrappers=1 video/rukna-nahi-30s.mp4
