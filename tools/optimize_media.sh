#!/bin/bash
# Re-encode videos and convert GIFs to MP4 from the untouched originals.
# Originals: ~/Documents/anjabedrick-site-originals/media   Output: public/media
set -e
cd "$(dirname "$0")/.."
B=~/Documents/anjabedrick-site-originals/media
BIN=/tmp/anja-optv
swiftc -O tools/optimize_video.swift -o $BIN
for f in $B/*.mp4; do
  n=$(basename "$f"); $BIN video "$f" /tmp/anja-opt-$n >/dev/null
  old=$(stat -f%z "$f"); new=$(stat -f%z /tmp/anja-opt-$n)
  if [ $new -lt $((old * 9 / 10)) ]; then mv /tmp/anja-opt-$n public/media/$n; echo "video $n: $((old/1048576))MB -> $((new/1048576))MB"
  else rm /tmp/anja-opt-$n; cp "$f" public/media/$n; echo "video $n: kept original"; fi
done
for f in $B/*.gif; do
  n=$(basename "$f" .gif); $BIN gif "$f" public/media/$n.mp4 >/dev/null
  echo "gif $n: $(( $(stat -f%z "$f")/1024 ))KB -> $(( $(stat -f%z public/media/$n.mp4)/1024 ))KB mp4"
done
