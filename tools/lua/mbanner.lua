-- mbanner.lua: force the mashin-battle attack-name banner from a mashin-battle state (width gate, windows.md).
--   emu.py ... --state-in <mashin state> --script tools/lua/mbanner.lua [--var IDX=0] [--var ACT=1] [--var AT=30]
-- The banner actor (action 0xEA = MACHINE 0x800DF76C, found with tools/lua/acts.lua) sits at 0x800BDEE8 in state 1
-- (0x800DF880) until its u16 +0x5C turns nonzero; then it uploads up to 13 glyphs of name IDX (u32 table
-- 0x800E03E4, index u8 0x800EA160) to VRAM row y 0xC0, drawn by sprite record 0x800E6D9E (w 208).
local m = PCSX.getMemPtr()
local at = AT or 30
L.on_frame(function(f)
  if f == at then
    local p = (OBJ or 0x800BDEE8) & 0x1FFFFF
    m[0x0EA160] = IDX or 0
    local act = ACT or 1
    m[p + 0x5C] = act & 0xFF; m[p + 0x5D] = (act >> 8) & 0xFF
    L.log(string.format("obj %08X +0 %02X%02X idx %d act %d", p | 0x80000000, m[p + 1], m[p], IDX or 0, act))
  end
end)
