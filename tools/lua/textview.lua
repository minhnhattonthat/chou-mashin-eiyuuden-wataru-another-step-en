-- Dialogue viewer: play room messages as events by pointing the event script pointer (0x8009C998) at each record
-- and setting field state 0x8009C788 = 3 (docs/re/debug.md "Dialogue viewer"). Needs free walk in the episode
-- whose room holds the text; run with --mash N --mash-key circle to page on.
--   --state-in work/states/epNN.sstate --script tools/lua/textview.lua --var "LIST='work/qa/cover/epNN.txt'"
--   LIST: one hex RAM address per line = a page's first text word (build/wataru_en.strings.tsv, low 24 bits).
--   A page is started at address - 14 when that word is 0xFFFF (`FFFF 0000 0001 A 0100 0302 B` header); others
--   are logged SKIP (NPC / chained pages: reached through their record or not at all).
--   Without LIST: PTR (default the current bank start u32 0x8009C9A4) once at frame AT (default 60).
-- Log: "SHOW <addr> f<n>", "SKIP <addr>", "STUCK <addr>" (still in the event after LIMIT frames), "VIEWDONE".
local LIMIT = LIMIT or 3000
local function m() return PCSX.getMemPtr() end
local function rd16(a) local p = m(); a = a & 0x1FFFFF; return p[a] + p[a + 1] * 256 end
local function rd32(a) return rd16(a) + rd16(a + 2) * 65536 end
local function wr16(a, v) local p = m(); a = a & 0x1FFFFF; p[a] = v & 0xFF; p[a + 1] = (v >> 8) & 0xFF end
local function wr32(a, v) wr16(a, v & 0xFFFF); wr16(a + 2, (v >> 16) & 0xFFFF) end

local list, i, since, busy = {}, 1, 0, false
if LIST then
  for line in io.lines(LIST) do
    local v = tonumber(line:match("%x+"), 16)
    if v then list[#list + 1] = 0x80000000 | v end
  end
else
  list = nil
end

local function start(rec)
  wr32(0x8009C998, rec)
  wr16(0x8009C788, 3)
end

L.on_frame(function(n)
  if not list then
    if n == (AT or 60) then start(PTR or rd32(0x8009C9A4)) end
    return
  end
  local st = rd16(0x8009C788)
  if busy then
    since = since + 1
    if st == 0 and since > 30 then busy = false
    elseif since > LIMIT then
      L.log(string.format("STUCK %08X f%d st=%d", list[i - 1], n, st))
      wr16(0x8009C788, 0)
      busy = false
    end
    return
  end
  if st ~= 0 or n < 30 then return end
  while i <= #list and rd16(list[i] - 14) ~= 0xFFFF do
    L.log(string.format("SKIP %08X", list[i]))
    i = i + 1
  end
  if i > #list then
    L.log("VIEWDONE f" .. n)
    L.finish(0)
    return
  end
  L.log(string.format("SHOW %08X f%d", list[i], n))
  start(list[i] - 14)
  i, since, busy = i + 1, 0, true
end)
