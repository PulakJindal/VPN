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

print("[CLIENT] TUN attached")

# ---------- SOCKET SETUP ----------
SERVER_IP = "192.168.138.1"
PORT = 5555
print(f"Connecting to {SERVER_IP}:{PORT}")

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((SERVER_IP, PORT))
print("[CLIENT] Connected to VPN server")

# ---------- ENCRYPTION SETUP ----------
# ⚠️ TEMP key for lab only (32 bytes)
PSK = b'\x0b\x9f\xb9Q\x13\x1e\x8emH\xb4\x97\x98SE\xed\xc6h%M\xec]l\r\xd5\x98\xbc\xdd\xeb\xddp\x99h'
if(len(PSK)!=32):
    print("Key length is not 32 bytes")
    exit(1)
cipher = ChaCha20Poly1305(PSK)

# ---------- FORWARDING ----------
def send_packet(sock, data):
    packet_len = len(data)
    header = struct.pack("!I", packet_len)   # converts a Python integer into exactly 4 bytes, network byte order
    sock.sendall(header + data)

def tun_to_sock():
    while True:
        packet = os.read(tun, 4096)
        print("[CLIENT] Read packet from TUN:", len(packet))
        #sock.sendall(packet)
        nonce = os.urandom(12)
        encrypted = cipher.encrypt(nonce, packet, None)
        # print("[CLIENT] Sending encrypted packet to server:", encrypted)
        # sock.sendall(nonce + encrypted)
        send_packet(sock, nonce + encrypted)
        
def recv_packet(sock):     # Receive exactly one packet from TCP using length framing.
    # Step 1: read the 4-byte length
    raw_len = b""
    while len(raw_len) < 4:
        chunk = sock.recv(4 - len(raw_len))
        if not chunk:
            return None
        raw_len += chunk

    packet_len = struct.unpack("!I", raw_len)[0]  

    # Step 2: read the packet payload
    data = b""
    while len(data) < packet_len:
        chunk = sock.recv(packet_len - len(data))
        if not chunk:
            return None
        data += chunk

    return data

def sock_to_tun():
    while True:
        # packet = sock.recv(4096)
        # if not packet:
        #     break
        # print("[CLIENT] Received packet from server:", len(packet))
        # os.write(tun, packet)
        # data = sock.recv(4096)
        # if not data:
        #     break
        data = recv_packet(sock)
        if data is None:
            break
        print("[CLIENT] Received packet from server:", len(data))
        nonce = data[:12]
        encrypted = data[12:]
        packet = cipher.decrypt(nonce, encrypted, None)
        # print("[CLIENT] Writing packet to TUN:", packet)
        os.write(tun, packet)

threading.Thread(target=tun_to_sock, daemon=True).start()
threading.Thread(target=sock_to_tun, daemon=True).start()

print("[CLIENT] VPN forwarding started")

while True:
    pass
