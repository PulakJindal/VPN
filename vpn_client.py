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

print("[CLIENT] TUN attached")

# ---------- SOCKET SETUP ----------
SERVER_IP = "192.168.138.1"
PORT = 5555
print(f"Connecting to {SERVER_IP}:{PORT}")

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((SERVER_IP, PORT))
print("[CLIENT] Connected to VPN server")

# ---------- FORWARDING ----------
def tun_to_sock():
    while True:
        packet = os.read(tun, 4096)
        print("[CLIENT] Read packet from TUN:", len(packet))
        sock.sendall(packet)

def sock_to_tun():
    while True:
        packet = sock.recv(4096)
        if not packet:
            break
        print("[CLIENT] Received packet from server:", len(packet))
        os.write(tun, packet)

threading.Thread(target=tun_to_sock, daemon=True).start()
threading.Thread(target=sock_to_tun, daemon=True).start()

print("[CLIENT] VPN forwarding started")

while True:
    pass
