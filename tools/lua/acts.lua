-- acts.lua: log the first 3 runs of each address in ADDRS (e.g. the actor-action handlers of the EXE table
-- 0x8006E840), with $ra, the actor pointer *0x8009C7AC and its action u16 +0 / state u16 +2. Needs --debugger.
-- Hooks must be registered at load time (hooks armed from on_frame never fired), so pass the list:
--   emu.py ... --debugger --script tools/lua/acts.lua --var "ADDRS='800DF76C,800DFE20'"
local m = PCSX.getMemPtr()
local function rd32(a) a = a & 0x1FFFFF; return m[a] | (m[a + 1] << 8) | (m[a + 2] << 16) | (m[a + 3] << 24) end
local seen = {}
for s in string.gmatch(assert(ADDRS, "--var ADDRS='hex,hex'"), "%x+") do
  local h = tonumber(s, 16)
  seen[h] = 0
  L.on_exec(h, function()
    if seen[h] < 3 then
      seen[h] = seen[h] + 1
      local p = rd32(0x8009C7AC) & 0x1FFFFF
      local g = PCSX.getRegisters().GPR.n
      L.log(string.format("h %08X ra %08X obj %08X +0 %04X +2 %04X", h, g.ra & 0xFFFFFFFF, p | 0x80000000,
        m[p] | (m[p + 1] << 8), m[p + 2] | (m[p + 3] << 8)))
    end
  end)
end
