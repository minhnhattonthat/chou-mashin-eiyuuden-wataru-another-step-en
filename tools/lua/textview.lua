-- Dialogue viewer: play room messages as events (docs/re/debug.md "Dialogue viewer"). An event starts when the field
-- state u16 0x8009C788 = 3: the EXE (0x8003275C) copies the event start u32 0x8009C9A4 into the script pointer
-- 0x8009C998, parses the 7-word header and walks the text. Needs free walk in the episode whose overlay holds the
-- text; run with --mash 8 --mash-key circle to page on.
--   --state-in work/states/epNN.sstate --script tools/lua/textview.lua --script tools/lua/textlog.lua
--   --var "LIST='<abs path>'" --var "SNAP='<abs path>.sstate'"
--   LIST: "<hex RAM address> <kind>" per line = a page's first text word (low 24 bits) and its header kind
--   (build/wataru_en.strings.tsv columns 2-3). An 'event' page starts an event at address - 14 (its 7-word
--   header: music, actor, actor arg, face, cmd, arg, arg; 0xFFFF / 0x7FFF = none); pages the pointer already
--   passed are skipped; others are logged SKIP (next / ptr pages: reached through their event or NPC).
--   After each event (state back to 0, or the pointer stalled STALL frames: a post-text command waiting on actors)
--   the free-walk snapshot SNAP is reloaded, then WAIT frames pass before the next start (an event started right
--   after another ends at once).
--   Without LIST: PTR (default the current event start) once at frame AT (default 60).
-- Log: "SHOW<pass> <addr> f<n>", "STALL <addr> st=<state>", "NOHOST <addr>", "UNSEEN <addr>" (never passed),
-- "VIEWDONE". Coverage itself comes from tools/lua/textlog.lua's TEXT lines.
local STALL, WAIT = STALL or 600, WAIT or 40  -- the ep-1 opening holds one pointer 238 frames in state 5 (walks)
local function m() return PCSX.getMemPtr() end
local function rd16(a) local p = m(); a = a & 0x1FFFFF; return p[a] + p[a + 1] * 256 end
local function rd32(a) return rd16(a) + rd16(a + 2) * 65536 end
local function wr16(a, v) local p = m(); a = a & 0x1FFFFF; p[a] = v & 0xFF; p[a + 1] = (v >> 8) & 0xFF end
local function wr32(a, v) wr16(a, v & 0xFFFF); wr16(a + 2, (v >> 16) & 0xFFFF) end

local list, startable, i = {}, {}, 1
if LIST then
  for line in io.lines(LIST) do
    local a, kind = line:match("^(%x+)%s*(%a*)")
    if a then
      local v = tonumber(a, 16) & 0xFFFFFF  -- low 24 bits, as `seen` keys; reads mask to 0x1FFFFF
      list[#list + 1] = v
      startable[v] = kind == "event"
    end
  end
else
  list = nil
end

-- a real 7-word header: face (w4) or last word (w7) 0x7FFF, music (w1) none or a small id. `A000 n FFFF` <text>
-- pages are 'event' in rooms.py too, but their 7 words before are text: a text code as music id hung the emulator.
local function header(v)
  if not startable[v] then return false end
  local w1 = rd16(v - 14)
  return (rd16(v - 2) == 0x7FFF or rd16(v - 8) == 0x7FFF) and (w1 == 0xFFFF or w1 < 0x300)
end

local function start(rec)
  wr32(0x8009C998, 0x80000000 + rec)
  wr32(0x8009C9A4, 0x80000000 + rec)
  wr16(0x8009C788, 3)
end

-- pass 1 starts every 'event' page's own event; pass 2 shows each page still unseen (NPC talk, pages after a stall)
-- by starting the host event (the first one that walked text) and pointing 0x8009C998 at the page once its window is
-- up: the walker draws from there to the next 0x3000.
local seen, phase, calm, snapped, busy, since, last, lastp, pass = {}, "settle", 0, false, nil, 0, 0, 0, 1
local host = HOST and (HOST & 0xFFFFFF)  -- --var HOST=0x0DE4B0: an 'event' page known to open its window
L.on_frame(function(n)
  if not list then
    if n == (AT or 60) then start(PTR and (PTR & 0xFFFFFF) or (rd32(0x8009C9A4) & 0xFFFFFF)) end
    return
  end
  local st, p = rd16(0x8009C788), rd32(0x8009C998) & 0xFFFFFF
  seen[p] = true
  if phase == "settle" then  -- free walk: state 0 for WAIT frames in a row
    calm = st == 0 and calm + 1 or 0
    if calm < WAIT then return end
    if not snapped then
      local f = Support.File.open(SNAP, "TRUNCATE"); f:writeMoveSlice(PCSX.createSaveState()); f:close()
      snapped = true
    end
    if busy and not host and seen[busy] then host = busy end
    while i <= #list and (seen[list[i]] or (pass == 1 and not header(list[i]))) do i = i + 1 end
    if i > #list and pass == 1 and host then pass, i = 2, 1; return end
    if i > #list then
      for _, v in ipairs(list) do
        if not seen[v] then L.log(string.format("UNSEEN %06X", v)) end
      end
      L.log("VIEWDONE f" .. n)
      L.finish(0)
      return
    end
    busy = list[i]
    L.log(string.format("SHOW%d %06X f%d", pass, busy, n))
    start((pass == 1 and busy or host) - 14)
    i, since, last, lastp, phase = i + 1, 0, n, p, pass == 1 and "run" or "hijack"
    return
  end
  since = since + 1
  if phase == "hijack" then  -- host window open and walking its text: jump to the page
    if st == 4 and p >= host and p < host + 0x40 then
      wr32(0x8009C998, 0x80000000 + busy)
      phase = "run"
    elseif since > STALL then
      L.log(string.format("NOHOST %06X st=%d", busy, st))
      PCSX.loadSaveState(Support.File.open(SNAP))
      phase, calm = "settle", 0
    end
    return
  end
  if p ~= lastp then last, lastp = n, p end
  if (st == 0 and since > 2) or n - last > STALL or since > 8000 then  -- 8000: an event that left the field
    if st ~= 0 then L.log(string.format("STALL %06X st=%d at %06X", busy, st, p)) end
    PCSX.loadSaveState(Support.File.open(SNAP))
    phase, calm = "settle", 0
  end
end)
