-- sprx.lua: log the actor (s0) and sprite record (s3) of each EXE sprite put (0x80024514 sh v1 = x) whose x is X.
-- Finds where a screen element's x comes from: x = actor+0x30 + record+0xA. Needs --debugger.
--   --debugger --script tools/lua/sprx.lua --var X=114 [--var FROM=2700]
local seen = {}
local mem = PCSX.getMemPtr()
local function h(a) a = a & 0x1FFFFF; return mem[a] | (mem[a + 1] << 8) end
L.on_exec(0x80024514, function()
  if L.frame < (FROM or 0) then return end
  local g = PCSX.getRegisters().GPR.n
  if (g.v1 & 0xFFFF) ~= X then return end
  local key = string.format("%08X %08X", g.s0, g.s3)
  if seen[key] then return end
  seen[key] = true
  L.log(string.format("f%d actor=%08X ax=%d rec=%08X rx=%d ry=%d", L.frame, g.s0, h(g.s0 + 0x30), g.s3,
    h(g.s3 + 0xA), h(g.s3 + 0xC)))
end)
