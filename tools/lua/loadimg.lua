-- loadimg.lua: log LoadImage (EXE 0x80072074, a0 = RECT*, a1 = src) calls by (w, h, src range, $ra).
-- Checks the pair-compose hook's discriminator (docs/re/font.md): a 16x16 4bpp glyph is w 4 / h 16; the hook
-- composes when src is in [0x80128480, 0x80195300). Logs every distinct (ra, w, h) once with its src, and every
-- w4/h16 call whose src is in the hook range ("HIT"). Needs --debugger.
--   emu.py ... --debugger --script tools/lua/loadimg.lua      (warp_all.py --script tools/lua/loadimg.lua)
local m = PCSX.getMemPtr()
local function rd16(a) a = a & 0x1FFFFF; return m[a] | (m[a + 1] << 8) end
local seen, hits = {}, 0
L.on_exec(0x80072074, function()
  local g = PCSX.getRegisters().GPR.n
  local ra, src = g.ra & 0xFFFFFFFF, g.a1 & 0xFFFFFFFF
  local w, h = rd16(g.a0 + 4), rd16(g.a0 + 6)
  local k = string.format("%08X %d %d", ra, w, h)
  if not seen[k] then
    seen[k] = true
    L.log(string.format("call ra %08X w %d h %d src %08X", ra, w, h, src))
  end
  if w == 4 and h == 16 and src >= 0x80128480 and src < 0x80195300 and hits < 50 then
    hits = hits + 1
    L.log(string.format("HIT ra %08X src %08X", ra, src))
  end
end)
