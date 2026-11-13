"""Compose each G9 list (new records over gfx/en/PRG/MEM_atlas.png) on a dark panel: offline check of every message."""
import struct, sys
sys.path.insert(0, 'tools')
import gfx
from PIL import Image
d = gfx.load(gfx.MEM)
new = {o: n for _, o, _, _, n, _ in gfx.mem_recs(d)}
atlas = Image.open('gfx/en/PRG/MEM_atlas.png').convert('RGBA')
px = atlas.load()
for j in range(atlas.size[1]):
    for i in range(atlas.size[0]):
        if px[i, j][:3] == (255, 0, 255):
            px[i, j] = (0, 0, 0, 0)
lists = gfx.mem_lists(d)
keys = list(gfx.MEM_EN) + [0x5068, 0x3C78]
W, H = 300, 64
out = Image.new('RGB', (W * 3, H * ((len(keys) + 2) // 3)), (40, 40, 90))
for k, lo in enumerate(keys):
    ox, oy = (k % 3) * W + 150, (k // 3) * H + 32
    for o, r in lists[lo]:
        tp, cl, u, v, w, h, x, y = new.get(o, r)
        if cl != gfx.MEM_TEXT or not w:
            continue
        out.paste(atlas.crop((256 * (tp - 10) + u, v, 256 * (tp - 10) + u + w, v + h)), (ox + x, oy + y),
                  atlas.crop((256 * (tp - 10) + u, v, 256 * (tp - 10) + u + w, v + h)))
out.resize((out.size[0] * 2, out.size[1] * 2), Image.NEAREST).save(sys.argv[1] if len(sys.argv) > 1 else 'work/g9/preview.png')
