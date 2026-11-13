-- Debug warp (PCSX-Redux via emu.py). Cold boot -> any scene in tools/debug/scenes.txt, no save needed.
--   emu.py <cue> --out work/qa/warp/x --sav tools/debug/blank.mcd --script tools/debug/warp.lua
--          --var "SCENE='ep03'" --frames 12000 [--state-out work/states/ep03.sstate]
--   (tools/debug/warp_all.py runs every scene this way and checks the result.)
-- Opt-in globals: GOD=1 (party HP/MP pinned to max every frame), SCENES='abs/path/scenes.txt'
-- (default <repo>/tools/debug/scenes.txt), HOLD=frames (default hold after arrival).
-- Log: "f<n> step <name>", "AT <scene> f<n>" when the scene's RAM check passes, "ROOMHEAD <hex>", "DONE <scene>";
-- L.fail (exit 2) when a step times out. RAM map and the reasoning: docs/re/debug.md.
local m = PCSX.getMemPtr()
local function r8(a) return m[a & 0x1FFFFF] end
local function r16(a) a = a & 0x1FFFFF; return m[a] + m[a + 1] * 256 end
local function wr(a, v, n)
  a = a & 0x1FFFFF
  for i = 0, n - 1 do m[a + i] = v % 256; v = math.floor(v / 256) end
end
local MODE = 0x8009C7FC   -- u8 SysMode: 0x14 boot/attract, 2 title, F episode card, C/D room setup, 5 field, 6 ball
                          -- battle, 7 mashin battle, 8 IQ battle, B level-up, 10 save, 11 load, 16 credits
local EP = 0x8009C90C     -- u16 episode index: 0 prologue, 1-14 episodes (SBTTL adds 1 before the card)
local FSTATE = 0x8009C788 -- u16 field sub-state (table 0x800819DC): 0 free walk, 3 event, 4/5 message, 9 menu
local PARTY = 0x800A8D38  -- party stats, 8 bytes each: hp, hp max, mp, mp max (u16)
local BUNIT = 0x800BF924  -- battle (mode 6) party units, 0x6C each: hp, hp max (u16)

-- scenes.txt: "name key=value ... # comment"
local root = OUT:match("^(.*)/work/") or "."
local path = SCENES or (root .. "/tools/debug/scenes.txt")
local scenes = {}
local fh = assert(io.open(path, "r"), "cannot open " .. path)
for line in fh:lines() do
  line = line:gsub("#.*", "")
  local name, rest = line:match("^%s*(%S+)%s*(.*)$")
  if name then
    local s = { name = name }
    for k, v in rest:gmatch("(%w+)=(%S+)") do s[k] = tonumber(v) or v end
    scenes[name] = s
  end
end
fh:close()
local S = assert(scenes[SCENE or ""], "unknown SCENE '" .. tostring(SCENE) .. "' (see " .. path .. ")")
local ep = S.ep or 1
L.log("WARP " .. S.name)

-- press=FRAMES:BUTTONS,... (route steps, e.g. 12:triangle,40:-,12:down)
local function queue_press(spec)
  for n, b in tostring(spec):gmatch("(%d+):([%w+%-]+)") do L.press(b, tonumber(n)) end
end
-- poke=ADDR:VALUE:SIZE,... (hex), applied once when the scene's start point is reached
local function apply_pokes()
  if S.poke then
    for a, v, n in tostring(S.poke):gmatch("(%x+):(%x+):(%d)") do wr(tonumber(a, 16), tonumber(v, 16), tonumber(n)) end
  end
  if S.mode then wr(MODE, S.mode, 1) end
end
-- arrival test: atmode / atstate when given, else the step's own condition
local function arrived_ok(mode)
  if S.atmode and mode ~= S.atmode then return false end
  if S.atstate and r16(FSTATE) ~= S.atstate then return false end
  return true
end

local step, t, arrived, idle_since = "boot", 0, false, nil
local function go(n)
  step = n; t = L.frame
  L.log(string.format("f%d step %s mode=%X ep=%X state=%X", L.frame, n, r8(MODE), r16(EP), r16(FSTATE)))
end
local function start_scene()
  apply_pokes()
  if S.press then queue_press(S.press) end
  go("act")
end

L.on_frame(function(f)
  local mode = r8(MODE)
  if GOD or S.god then
    for i = 0, 5 do
      local a = PARTY + 8 * i
      local hm, mm = r16(a + 2), r16(a + 6)
      if hm > 0 and hm < 10000 then wr(a, hm, 2) end
      if mm < 10000 then wr(a + 4, mm, 2) end
    end
    if mode == 6 then -- the battle keeps its own copy: units at BUNIT, 0x6C each, hp then hp max (u16)
      for i = 0, 2 do
        local a = BUNIT + 0x6C * i
        local hm = r16(a + 2)
        if hm > 0 and hm < 10000 then wr(a, hm, 2) end
      end
    end
  end
  if step == "boot" then
    -- mode 0x14: logo, attract FMV, title art; Start (from ~f1450) opens the title (mode 2)
    if mode == 0x14 and f >= 1450 and f % 60 == 0 then L.press("start", 12) end
    if mode == 2 then go("title") end
  elseif step == "title" then
    -- the logo animates ~600 frames before PUSH START; Start opens the menu (cursor on New Game with a blank card)
    local d = f - t
    if d == 700 then L.press("start", 12) end
    if d == 860 then
      if S.stop == "title" then start_scene() else L.press("circle", 12) end
    end
    if mode == 0xF then go("card") end
    if d > 900 and d % 120 == 0 and mode == 2 and r16(EP) == 0xFFFF then L.press("start", 12) end -- skip the FMV
  elseif step == "card" then
    if f == t + 1 then wr(EP, (ep - 1) & 0xFFFF, 2) end
    if mode == 0xC or mode == 0xD then
      if S.idle then go("idle") elseif S.stop == "room" or not (S.poke or S.mode or S.press) then go("act")
      else start_scene() end
    end
  elseif step == "idle" then
    -- click through the opening dialogue until free walk (mode 5, state 0) holds for 90 frames
    if mode == 5 and r16(FSTATE) == 0 then
      idle_since = idle_since or f
      if f - idle_since >= 90 then start_scene() end
    else
      idle_since = nil
      if L.route_done() and f % 40 == 0 then L.press("circle", 6) end
    end
    if f - t > (S.idletimeout or 6000) then L.fail("warp timeout: " .. S.name .. " never reached free walk") end
  elseif step == "act" then
    local d = f - t
    -- mash=N: Circle (12 frames; 6-frame presses are dropped in battle and at the title) every N frames
    if S.mash and L.route_done() and d % S.mash == 0 then L.press("circle", 12) end
    -- pokeloop=A:V:N,...: written every frame until arrival (flags the game would clear)
    if S.pokeloop and not arrived then
      for a, v, n in tostring(S.pokeloop):gmatch("(%x+):(%x+):(%d)") do wr(tonumber(a, 16), tonumber(v, 16), tonumber(n)) end
    end
    -- late=F:A:V:N,...: written once F frames into the scene (after a battle has set up its own state)
    if S.late then
      for f0, a, v, n in tostring(S.late):gmatch("(%d+):(%x+):(%x+):(%d)") do
        if d == tonumber(f0) then wr(tonumber(a, 16), tonumber(v, 16), tonumber(n)) end
      end
    end
    if (L.route_done() or S.mash) and d >= (S.wait or 30) and (S.atmode or S.atstate or mode == 0xC or mode == 0xD or mode == 5
        or S.stop == "title") and arrived_ok(mode) and not arrived then
      arrived = f
      L.log(string.format("AT %s f%d mode=%X state=%X", S.name, f, mode, r16(FSTATE)))
    end
    if not arrived and d > (S.timeout or 3000) then
      L.fail(string.format("warp timeout: %s mode=%X state=%X", S.name, mode, r16(FSTATE)))
    end
  end
  if arrived and f == arrived + (S.hold or HOLD or 300) then
    -- room overlay head (0x800CE000): tools/debug/warp_all.py names the loaded FPRG/Rxx.BIN from it
    local h = {}
    for i = 0, 255 do h[#h + 1] = string.format("%02X", r8(0x800CE000 + i)) end
    L.log("ROOMHEAD " .. table.concat(h))
    L.shot("final.png")
    if STATE_OUT then L.save_state(STATE_OUT) end
    L.log("DONE " .. S.name .. " f" .. f)
    L.finish(0)
  end
  if step ~= "act" and step ~= "idle" and f > (S.boottimeout or 9000) then
    L.fail("warp timeout: " .. S.name .. " stuck at step " .. step)
  end
end)
