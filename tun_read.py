import os
import fcntl  #call ioctl() (input/output control) & configure kernel devices
import struct  #pack binary data & exactly match kernel C structures

TUNSETIFF = 0x400454ca  #ioctl command number
IFF_TUN   = 0x0001  # TUN device
IFF_NO_PI = 0x1000  # Dont add anything extra to the packet (without this add 4 bytes)

# Open TUN device
tun = os.open("/dev/net/tun", os.O_RDWR) # os.open() -> low-level os interfaces, os.O_RDWR -> read & write both

# Attach to existing tun0
ifr = struct.pack("16sH", b"tun0", IFF_TUN | IFF_NO_PI)  #creates a binary structure that the kernel expects.
fcntl.ioctl(tun, TUNSETIFF, ifr) # Attach the TUN device to tun0 interface (ioctl() -> input/output control system call)

print("[+] Attached to tun0")

while True:
    packet = os.read(tun, 4096)
    print(f"[IN ] {len(packet)} bytes")

    # TEMPORARY: write the same packet back
    os.write(tun, packet)
    print(f"[OUT] {len(packet)} bytes")
