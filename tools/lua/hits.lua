-- hits.lua: log every execution of ADDR (frame, ra, a0..a2), up to MAX lines. Needs --debugger.
-- usage: emu.py ... --debugger --script tools/lua/hits.lua --var ADDR=0x80062E98 [--var MAX=200]
local n = 0
L.on_exec(ADDR, function()
  if n >= (MAX or 200) then return end
  n = n + 1
  local g = PCSX.getRegisters().GPR.n
  L.log(string.format("HIT f%d ra %08X a0 %08X a1 %08X a2 %08X", L.frame, g.ra, g.a0, g.a1, g.a2))
end)
