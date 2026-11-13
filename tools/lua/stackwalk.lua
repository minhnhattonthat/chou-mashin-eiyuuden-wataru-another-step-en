-- stackwalk.lua: on the first MAX reads of LO..HI (default) or exec of ADDR, log words on the stack that look like
-- return addresses into code (0x80018000-0x80100000): a cheap backtrace. Needs --debugger.
-- usage: emu.py ... --debugger --script tools/lua/stackwalk.lua --var LO=0x80110000 --var HI=0x80128400 [--var MAX=3]
local n = 0
local mem = PCSX.getMemPtr()
local function u32(a) a = a & 0x1FFFFF; return mem[a] | (mem[a+1] << 8) | (mem[a+2] << 16) | (mem[a+3] << 24) end
local function walk(tag)
  if n >= (MAX or 3) then return end
  n = n + 1
  local g = PCSX.getRegisters().GPR.n
  local out = {}
  for o = 0, 0x400, 4 do
    local w = u32(g.sp + o)
    if w >= 0x80018000 and w < 0x80100000 and w % 4 == 0 then out[#out + 1] = string.format("+%X:%08X", o, w) end
  end
  L.log(string.format("%s pc %08X ra %08X sp %08X | %s", tag, PCSX.getRegisters().pc, g.ra, g.sp, table.concat(out, " ")))
end
if ADDR then L.on_exec(ADDR, function() walk("exec") end) else L.on_read(LO, HI, function(a) walk(string.format("read %08X", a)) end) end
