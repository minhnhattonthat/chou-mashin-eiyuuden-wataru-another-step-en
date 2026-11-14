-- Text coverage hook (scripts/textcover.py): log each distinct room-text position the event pointer visits, as
-- "TEXT <episode << 24 | ptr & 0xFFFFFF>", the key build/wataru_en.strings.tsv lists per page (insert.strings()).
--   --script tools/lua/textlog.lua   (with warp.lua or textview.lua; sampled once a frame: a page's first word
--   holds the pointer while its window opens)
local seen = {}
L.on_frame(function(n)
  local m = PCSX.getMemPtr()
  local a = 0x9C998
  local p = m[a] + m[a + 1] * 256 + m[a + 2] * 65536 + m[a + 3] * 16777216
  if p < 0x800CE000 or p >= 0x800F7000 then return end
  local key = ((m[0x9C90C] + m[0x9C90D] * 256) << 24) | (p & 0xFFFFFF)
  if not seen[key] then
    seen[key] = true
    L.log(string.format("TEXT %X f%d", key, n))
  end
end)
