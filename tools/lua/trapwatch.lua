-- Free-space trap test (PCSX-Redux via emu.py). At frame FILL, fill LO..HI with 0xA5; every 600 frames and at the
-- end, log the sub-ranges that no longer hold 0xA5 (someone wrote there). Debugger-free, so it runs at full speed.
--   --script tools/lua/trapwatch.lua --var LO=0x80128072 --var HI=0x80148000 [--var FILL=60]
local lo, hi = assert(LO, "set --var LO=0x...") & 0x1FFFFF, assert(HI, "set --var HI=0x...") & 0x1FFFFF
local fill = FILL or 60
local reported = {}
local function scan(n)
  local m = PCSX.getMemPtr()
  local a = lo
  while a < hi do
    if m[a] ~= 0xA5 then
      local b = a
      while b < hi and m[b] ~= 0xA5 do b = b + 1 end
      local key = a .. ":" .. b
      if not reported[key] then
        reported[key] = true
        L.log(string.format("f%d dirty %08X-%08X (%d bytes)", n, 0x80000000 + a, 0x80000000 + b, b - a))
      end
      a = b
    else
      a = a + 1
    end
  end
end
L.on_frame(function(n)
  if n == fill then
    local m = PCSX.getMemPtr()
    for a = lo, hi - 1 do m[a] = 0xA5 end
    L.log(string.format("f%d filled %08X-%08X", n, 0x80000000 + lo, 0x80000000 + hi))
  elseif n > fill and n % 600 == 0 then
    scan(n)
  end
end)
