import os
import socket
import fcntl
import struct
import threading
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

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

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((SERVER_IP, PORT))
client_addr = None
# print(f"[SERVER] Client connected: {client_addr}")

# ---------- ENCRYPTION SETUP ----------
# ⚠️ TEMP key for lab only (32 bytes)
PSK = b'\x0b\x9f\xb9Q\x13\x1e\x8emH\xb4\x97\x98SE\xed\xc6h%M\xec]l\r\xd5\x98\xbc\xdd\xeb\xddp\x99h'
if(len(PSK)!=32):
    print("Key length is not 32 bytes")
    exit(1)
cipher = ChaCha20Poly1305(PSK)

# ---------- FORWARDING ----------
def tun_to_sock():
    while True:
        packet = os.read(tun, 4096)
        print("[SERVER] Read Packets from TUN:", len(packet))
        if client_addr is None:
            continue  # no client yet
        #conn.sendall(packet)
        nonce = os.urandom(12)
        encrypted = cipher.encrypt(nonce, packet, None)
        # print("[SERVER] Sending encrypted packet to client:", encrypted)
        # conn.sendall(nonce + encrypted)
        sock.sendto(nonce + encrypted, client_addr)

def sock_to_tun():
    while True:
        data, addr = sock.recvfrom(4096)
        global client_addr
        client_addr = addr  # remember who sent it
        print("[SERVER] Received packets from client:", len(data))
        nonce = data[:12]
        encrypted = data[12:]
        packet = cipher.decrypt(nonce, encrypted, None)
        # print("[SERVER] Writing packet to TUN:", packet)
        os.write(tun, packet)

threading.Thread(target=tun_to_sock, daemon=True).start()
threading.Thread(target=sock_to_tun, daemon=True).start()

print("[SERVER] VPN forwarding started")

# Keep alive
while True:
    pass
