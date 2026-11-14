-- mbanall.lua: force every mashin-battle banner name in turn (text coverage of MACHINE names, mbanner.lua's trigger).
--   emu.py ... --state-in work/states/mashin_attack.sstate --script tools/lua/mbanall.lua [--var N=34] [--var STEP=120]
-- From frame AT, every STEP frames: index u8 0x800EA160 = i, banner actor 0x800BDEE8 +0x5C = 1 (i = 0 .. N-1).
local m = PCSX.getMemPtr()
local at, step, n = AT or 30, STEP or 120, N or 34
L.on_frame(function(f)
  if f < at or (f - at) % step ~= 0 then return end
  local i = math.floor((f - at) / step)
  if i >= n then return end
  local p = (OBJ or 0x800BDEE8) & 0x1FFFFF
  m[0x0EA160] = i
  m[p + 0x5C] = 1; m[p + 0x5D] = 0
  L.log(string.format("f%d banner idx %d state %02X%02X", f, i, m[p + 1], m[p]))
end)
