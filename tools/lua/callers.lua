-- callers.lua: log each distinct $ra (and a0..a3 the first time) when ADDR executes. Needs --debugger.
-- usage: emu.py ... --debugger --script tools/lua/callers.lua --var ADDR=0x80073880 [--var MAX=40]
local seen, n = {}, 0
L.on_exec(ADDR, function()
  local g = PCSX.getRegisters().GPR.n
  if not seen[g.ra] and n < (MAX or 40) then
    seen[g.ra] = true; n = n + 1
    L.log(string.format("ra %08X a0 %08X a1 %08X a2 %08X a3 %08X sp %08X", g.ra, g.a0, g.a1, g.a2, g.a3, g.sp))
  end
end)
