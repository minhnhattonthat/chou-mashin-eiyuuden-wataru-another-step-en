-- Write RAM at one frame (PCSX-Redux via emu.py): for trying a warp variable from a savestate.
--   --script tools/lua/poke.lua --var "POKE='8009C788=9:2,8009C85A=0:2'" [--var POKE_AT=60] [--var POKE_EVERY=1]
-- ADDR=VALUE:SIZE (hex address and value, size 1/2/4 bytes). POKE_EVERY=1 repeats it every frame from POKE_AT.
local m = PCSX.getMemPtr()
local list = {}
for a, v, n in string.gmatch(assert(POKE, "set --var POKE='ADDR=VAL:N,...'"), "(%x+)=(%x+):(%d)") do
  list[#list + 1] = { a = tonumber(a, 16) & 0x1FFFFF, v = tonumber(v, 16), n = tonumber(n) }
end
local at = POKE_AT or 60
L.on_frame(function(f)
  if f == at or (POKE_EVERY and f > at) then
    for _, p in ipairs(list) do
      local v = p.v
      for i = 0, p.n - 1 do m[p.a + i] = v % 256; v = math.floor(v / 256) end
    end
    if f == at then L.log("f" .. f .. " poke " .. POKE) end
  end
end)
