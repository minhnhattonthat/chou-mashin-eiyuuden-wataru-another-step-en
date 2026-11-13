-- vdump.lua: at frame FR dump VRAM (v.vram.bin, 1024x512 16-bit) and main RAM (ram.bin) into --out.
L.on_frame(function(n) if n == FR then L.dump_ppu("v"); L.dump_ram("ram.bin") end end)
