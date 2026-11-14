-- Text coverage for menu/battle strings (scripts/textcover.py): a read breakpoint on each string's first word, logged
-- once as "TEXT <key>" when the bytes there are that string's (ST/BALLBAT/MACHINE/TTL/LVUP share 0x800D0000).
--   --debugger --script tools/lua/readlog.lua --var "LIST='<abs>/build/wataru_en.strings.tsv'"
-- LIST lines with kind 'menu': id, key (tag << 24 | RAM address), menu, first 4 bytes written (insert.strings()).
-- shortcut: the breakpoint covers the aligned word, so a memcpy that reads the previous string's last word also
-- marks this one; fine for a reached/not-reached gate, visual QA judges the drawing.
local cand, seen = {}, {}
for line in io.lines(LIST) do
  local _, key, kind, hex = line:match("^(%S+)\t(%x+)\t(%S+)\t(%x+)")
  if kind == "menu" then
    local k = tonumber(key, 16)
    local addr = 0x80000000 + k % 0x1000000
    local w = addr - addr % 4
    cand[w] = cand[w] or {}
    table.insert(cand[w], { key = k, off = addr - 0x80000000, hex = hex })
  end
end
local function matches(m, c)
  for i = 0, #c.hex / 2 - 1 do
    if m[c.off + i] ~= tonumber(c.hex:sub(2 * i + 1, 2 * i + 2), 16) then return false end
  end
  return true
end
-- One breakpoint per span of nearby words (LuaJIT runs out of FFI callbacks at ~1000 breakpoints).
local GAP = tonumber(GAP or 64)
local words = {}
for w in pairs(cand) do words[#words + 1] = w end
table.sort(words)
local raw = 0
local function hit(addr)
  addr = 0x80000000 + tonumber(addr) % 0x1000000
  local cs = cand[addr - addr % 4]
  if not cs then return end
  local m = PCSX.getMemPtr()
  if DEBUG and raw < 40 and addr >= (DLO or 0) and addr < (DHI or 0x80200000) then  -- DLO/DHI: log this range
    raw = raw + 1
    local o = addr - addr % 4 - 0x80000000
    L.log(string.format("RAW %08X pc %08X mem %02X%02X%02X%02X want %s", addr, L.pc(), m[o], m[o + 1], m[o + 2],
                        m[o + 3], cs[1].hex))
  end
  for _, c in ipairs(cs) do
    if not seen[c.key] and matches(m, c) then
      seen[c.key] = true
      L.log(string.format("TEXT %X", c.key))
    end
  end
end
local n, lo = 0, nil
for i, w in ipairs(words) do
  lo = lo or w
  if i == #words or words[i + 1] - w > GAP then
    L.on_read(lo, w + 3, hit)
    n, lo = n + 1, nil
  end
end
L.log("READLOG " .. #words .. " words, " .. n .. " breakpoints")
