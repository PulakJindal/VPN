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

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((SERVER_IP, PORT))
sock.listen(1)

conn, addr = sock.accept()
print(f"[SERVER] Client connected: {addr}")

# ---------- ENCRYPTION SETUP ----------
# ⚠️ TEMP key for lab only (32 bytes)
PSK = b'\x0b\x9f\xb9Q\x13\x1e\x8emH\xb4\x97\x98SE\xed\xc6h%M\xec]l\r\xd5\x98\xbc\xdd\xeb\xddp\x99h'
if(len(PSK)!=32):
    print("Key length is not 32 bytes")
    exit(1)
cipher = ChaCha20Poly1305(PSK)

# ---------- FORWARDING ----------
def send_packet(conn, data):
    packet_len = len(data)
    header = struct.pack("!I", packet_len)  # converts a Python integer into exactly 4 bytes, network byte order
    conn.sendall(header + data)

def tun_to_sock():
    while True:
        packet = os.read(tun, 4096)
        print("[SERVER] Read Packets from TUN:", len(packet))
        #conn.sendall(packet)
        nonce = os.urandom(12)
        encrypted = cipher.encrypt(nonce, packet, None)
        # print("[SERVER] Sending encrypted packet to client:", encrypted)
        # conn.sendall(nonce + encrypted)
        send_packet(conn, nonce + encrypted)

def recv_packet(conn):  # Receive exactly one packet from TCP using length framing.
    # Step 1: read the 4-byte length
    raw_len = b""
    while len(raw_len) < 4:
        chunk = conn.recv(4 - len(raw_len))
        if not chunk:
            return None
        raw_len += chunk

    packet_len = struct.unpack("!I", raw_len)[0]

    # Step 2: read the packet payload
    data = b""
    while len(data) < packet_len:
        chunk = conn.recv(packet_len - len(data))
        if not chunk:
            return None
        data += chunk

    return data

def sock_to_tun():
    while True:
        # packet = conn.recv(4096)
        # if not packet:
        #     break
        # print("[SERVER] Received packets from client:", len(packet))
        # os.write(tun, packet)
        # data = conn.recv(4096)
        # if not data:
        #     break
        data = recv_packet(conn)
        if data is None:
            break
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
