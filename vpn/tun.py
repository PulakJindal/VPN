import fcntl
import struct
import os

# ---------- TUN SETUP ----------
TUNSETIFF = 0x400454ca
IFF_TUN   = 0x0001
IFF_NO_PI = 0x1000

def create_tun_interface():
    tun = os.open("/dev/net/tun", os.O_RDWR)
    ifr = struct.pack("16sH", b"tun0", IFF_TUN | IFF_NO_PI)
    fcntl.ioctl(tun, TUNSETIFF, ifr)
    return tun

print("[SERVER] TUN attached")
