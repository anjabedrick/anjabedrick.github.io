"""Write src/data/media-dims.json: {filename: [width, height]} for every image and video in public/media.
Pages use it to give each <img>/<video> its size up front, so nothing jumps around while loading."""
import json, os, re, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDIA = os.path.join(ROOT, "public", "media")
dims = {}
vids = []
for n in sorted(os.listdir(MEDIA)):
    p = os.path.join(MEDIA, n)
    if n.endswith(".mp4"): vids.append(p); continue
    if n.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
        out = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", p], capture_output=True, text=True).stdout
        w = int(re.search(r"pixelWidth: (\d+)", out).group(1)); h = int(re.search(r"pixelHeight: (\d+)", out).group(1))
        dims[n] = [w, h]
    elif n.endswith(".svg"):
        s = open(p).read(2000)
        m = re.search(r'width="([\d.]+)"[^>]*height="([\d.]+)"', s)
        if m: dims[n] = [round(float(m.group(1))), round(float(m.group(2)))]
if vids:
    out = subprocess.run(["swift", os.path.join(ROOT, "tools", "mediainfo.swift"), *vids], capture_output=True, text=True).stdout
    for line in out.splitlines():
        m = re.search(r"(\d+)x(\d+)\s.*\s(\S+\.mp4)$", line)
        if m: dims[m.group(3)] = [int(m.group(1)), int(m.group(2))]
os.makedirs(os.path.join(ROOT, "src", "data"), exist_ok=True)
json.dump(dims, open(os.path.join(ROOT, "src", "data", "media-dims.json"), "w"), indent=0, sort_keys=True)
print(len(dims), "files measured")
