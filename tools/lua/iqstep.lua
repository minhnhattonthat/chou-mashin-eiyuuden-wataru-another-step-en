-- iqstep.lua: log an IQ game's step machine and optionally jump a sub-step (text coverage of ST branches).
--   emu.py ... --script tools/lua/iqstep.lua [--var ACT=0x103] [--var TOP=3 --var FIELD=0x56 --var TO=27]
-- Actors live at 0x800BD750 + 0x6C * n; action u16 +0 indexes the EXE handler table 0x8006E840 (debug.md "IQ battle
-- steps"). Each IQ game actor keeps a top state u16 +2 (ACT 0x103 = KIO/15-puzzle, table 0x8010AEB8); some top
-- states run a sub-step at another field through their own table (0x103: top 3 -> +0x56 table 0x8010AF34, top 18
-- -> +0x5A table 0x8010B180). Logs every actor with action 0x100-0x11F once ("ACTOR"), then "STEP f top sub" on
-- every change of ACT's actor; the first time its top state is TOP (or the first frame >= ATF), u16 +FIELD is set
-- to TO (and the top state to SETTOP if given). Hit & blow = 0x112 (top 5 -> +0x56 table 0x8010B910, top 6 ->
-- 0x8010B940), whack/memory = 0x120 (top 5 -> +0x68 table 0x8010CA90).
local m = PCSX.getMemPtr()
local act, top0, field = ACT or 0x103, TOP or 3, FIELD or 0x56
local seen, last, done = {}, "", false
L.on_frame(function(f)
  for n = 0, OBJ and 0 or 95 do
    local p = OBJ and OBJ % 0x200000 or 0x0BD750 + 0x6C * n  -- OBJ: one fixed object (shop actor 0x800C0E28)
    local a = m[p] + m[p + 1] * 256
    if ((a >= 0x100 and a < 0x140) or a == act) and not seen[n * 1000 + a] then
      seen[n * 1000 + a] = true
      L.log(string.format("ACTOR %d n %d obj %08X act %X", f, n, 0x80000000 + p, a))
    end
    if a == act then
      local top = m[p + 2] + m[p + 3] * 256
      local s = m[p + field] + m[p + field + 1] * 256
      local k = n .. " " .. top .. " " .. s
      if k ~= last then
        L.log(string.format("STEP %d %d %d", f, top, s))
        last = k
      end
      if TO and not done and ((ATF and f >= ATF) or (not ATF and top == top0)) then
        done = true
        if SETTOP then m[p + 2] = SETTOP % 256; m[p + 3] = math.floor(SETTOP / 256) end
        m[p + field] = TO % 256; m[p + field + 1] = math.floor(TO / 256)
        L.log(string.format("JUMP %d top %d +%X %d -> %d", f, top, field, s, TO))
      end
    end
  end
end)
