-- readpcs.lua: log reads (or writes, MODE='Write') of RAM LO..HI: each distinct PC once, or with ALL=1 the first
-- MAX hits (pc, ra, addr, width).
-- usage: emu.py ... --debugger --script tools/lua/readpcs.lua --var LO=0x80110000 --var HI=0x80128400 [--var ALL=1]
local seen, n = {}, 0
local f = (MODE == "Write") and L.on_write or L.on_read
f(LO, HI, function(addr, width)
  local r = PCSX.getRegisters()
  local pc = r.pc
  if ALL and n < (MAX or 200) or (not ALL and not seen[pc]) then
    seen[pc] = true; n = n + 1
    L.log(string.format("pc %08X ra %08X addr %08X w%d", pc, r.GPR.n.ra, addr, width))
  end
end)
