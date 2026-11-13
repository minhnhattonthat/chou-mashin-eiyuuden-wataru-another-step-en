-- Log reads of the EXE file table (0x80077240, 0x20-byte records; tools/filetab.py lists them). Needs --debugger.
-- One line per (record, PC) per FILE_GAP frames:  f<frame> file <index> pc=<pc>
--   --debugger --script tools/lua/fileload.lua [--var FILE_GAP=120]
local BASE, N = 0x80077240, 1037
local gap = FILE_GAP or 120
local last = {}
L.on_read(BASE, BASE + N * 0x20 - 1, function(addr)
  local i = math.floor((addr - BASE) / 0x20)
  local pc = L.pc()
  local k = i * 65536 + (pc & 0xFFFF)
  if last[k] and L.frame - last[k] < gap then return end
  last[k] = L.frame
  L.log(string.format("f%d file %d +%X pc=%08X", L.frame, i, (addr - BASE) % 0x20, pc))
end)
