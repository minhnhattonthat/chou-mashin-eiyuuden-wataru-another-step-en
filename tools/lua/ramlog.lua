-- Log every change of a few RAM words (PCSX-Redux via emu.py), debugger-free.
--   --script tools/lua/ramlog.lua --var "WATCH='8009C90C:2,8009C998:4'"
local m = PCSX.getMemPtr()
local list = {}
for a, n in string.gmatch(assert(WATCH, "set --var WATCH='ADDR:N,...'"), "(%x+):(%d)") do
  list[#list + 1] = { a = tonumber(a, 16) & 0x1FFFFF, n = tonumber(n), name = a }
end
local function rd(a, n)
  local v = 0
  for i = n - 1, 0, -1 do v = v * 256 + m[a + i] end
  return v
end
local last = {}
L.on_frame(function(f)
  for i, w in ipairs(list) do
    local v = rd(w.a, w.n)
    if v ~= last[i] then
      L.log(string.format("f%d %s=%X", f, w.name, v))
      last[i] = v
    end
  end
end)
