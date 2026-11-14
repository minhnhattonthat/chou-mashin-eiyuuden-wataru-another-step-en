-- loadwin.lua: log LoadImage (EXE 0x80072074) calls whose RECT overlaps a VRAM window. Needs --debugger.
--   emu.py ... --debugger --script tools/lua/loadwin.lua --var "WIN='768,0,32,32'" [--var MAX=200]
-- Found the ST blank-cell padding writing past the IQ text buffer (704,0) into the card backs (p8 s10).
local wx, wy, ww, wh = WIN:match("(%d+),(%d+),(%d+),(%d+)")
wx, wy, ww, wh = tonumber(wx), tonumber(wy), tonumber(ww), tonumber(wh)
local n = 0
local function rd16(a) local m = PCSX.getMemPtr(); a = a & 0x1FFFFF; return m[a] + m[a + 1] * 256 end
L.on_exec(0x80072074, function()
  local g = PCSX.getRegisters().GPR.n
  local x, y, w, h = rd16(g.a0), rd16(g.a0 + 2), rd16(g.a0 + 4), rd16(g.a0 + 6)
  if x < wx + ww and x + w > wx and y < wy + wh and y + h > wy and n < (MAX or 200) then
    n = n + 1
    L.log(string.format("LI f%d rect %d,%d,%d,%d src %08X ra %08X", L.frame, x, y, w, h, g.a1, g.ra))
  end
end)
