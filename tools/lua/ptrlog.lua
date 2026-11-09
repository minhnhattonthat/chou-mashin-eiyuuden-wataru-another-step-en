-- Log a 32-bit RAM variable whenever it changes (frame, new value). PCSX-Redux via emu.py.
--   --script tools/lua/ptrlog.lua --var PTR=0x8009C998
local addr = assert(PTR, "set --var PTR=0x...") & 0x1FFFFF
local last = nil
local function rd32(a)
  local m = PCSX.getMemPtr()
  return m[a] + m[a + 1] * 256 + m[a + 2] * 65536 + m[a + 3] * 16777216
end
L.on_frame(function(n)
  local v = rd32(addr)
  if v ~= last then
    L.log(string.format("f%d %08X", n, v))
    last = v
  end
end)
