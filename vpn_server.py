import os
import socket
import fcntl
import struct
import threading

# ---------- TUN SETUP ----------
TUNSETIFF = 0x400454ca
IFF_TUN   = 0x0001
IFF_NO_PI = 0x1000

tun = os.open("/dev/net/tun", os.O_RDWR)
ifr = struct.pack("16sH", b"tun0", IFF_TUN | IFF_NO_PI)
fcntl.ioctl(tun, TUNSETIFF, ifr)

print("[SERVER] TUN attached")

# ---------- SOCKET SETUP ----------
SERVER_IP = "0.0.0.0"
PORT = 5555

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((SERVER_IP, PORT))
sock.listen(1)

conn, addr = sock.accept()
print(f"[SERVER] Client connected: {addr}")

# ---------- FORWARDING ----------
def tun_to_sock():
    while True:
        packet = os.read(tun, 4096)
        conn.sendall(packet)

def sock_to_tun():
    while True:
        packet = conn.recv(4096)
        if not packet:
            break
        os.write(tun, packet)

threading.Thread(target=tun_to_sock, daemon=True).start()
threading.Thread(target=sock_to_tun, daemon=True).start()

print("[SERVER] VPN forwarding started")

# Keep alive
while True:
    pass
