"""Turn a dumpsxiso 2336-byte-sector STR (subheader+data+EDC) into raw 2352-byte sectors ffmpeg's psxstr demuxer reads.
usage: python tools/str2raw.py IN.STR OUT.raw"""
import sys

SYNC = b'\x00' + b'\xff' * 10 + b'\x00'


def bcd(n): return ((n // 10) << 4) | (n % 10)


def to_raw(data, lba0=150):
    assert len(data) % 2336 == 0, 'not 2336-byte sectors'
    out = bytearray()
    for i in range(len(data) // 2336):
        a = lba0 + i
        out += SYNC + bytes([bcd(a // 4500), bcd(a // 75 % 60), bcd(a % 75), 2]) + data[i * 2336:(i + 1) * 2336]
    return bytes(out)


if __name__ == '__main__':
    assert len(to_raw(b'\0' * 2336 * 2)) == 2352 * 2
    open(sys.argv[2], 'wb').write(to_raw(open(sys.argv[1], 'rb').read()))
