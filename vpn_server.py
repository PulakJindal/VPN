import os
import socket
import fcntl
import struct
import threading
import ipaddress
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

print("[SERVER] UDP VPN server started")
print("[SERVER] Listening on", SERVER_IP, PORT)

# ---------- ENCRYPTION SETUP ----------
# ⚠️ TEMP key for lab only (32 bytes)
PSK = b'\x0b\x9f\xb9Q\x13\x1e\x8emH\xb4\x97\x98SE\xed\xc6h%M\xec]l\r\xd5\x98\xbc\xdd\xeb\xddp\x99h'
if(len(PSK)!=32):
    print("Key length is not 32 bytes")
    exit(1)
cipher = ChaCha20Poly1305(PSK)


#----------- CLIENT MANAGEMENT -----------
clients = {}
ip_to_client = {}

VPN_NET = ipaddress.ip_network("10.8.0.0/24")
ip_pool = iter(VPN_NET.hosts())
next(ip_pool)  # skip 10.8.0.1 (server)

# ---------- FORWARDING ----------
def tun_to_sock():
    while True:
        packet = os.read(tun, 4096)
        print("[SERVER] Read Packets from TUN:", len(packet))
        dst_ip = socket.inet_ntoa(packet[16:20])
        print("[SERVER] Packet DST IP:", dst_ip)

        if dst_ip in ip_to_client:
            addr = ip_to_client[dst_ip]
            state = clients[addr]
            cipher = state["cipher"]

            nonce = os.urandom(12)
            encrypted = cipher.encrypt(nonce, packet, None)
            sock.sendto(nonce + encrypted, addr)
        else:
            print(f"[SERVER] No client for DST IP {dst_ip}, dropping packet")

def sock_to_tun():
    while True:
        data, addr = sock.recvfrom(4096)
        print("[SERVER] Received packets from client:",addr, len(data))
        
        # Register new client if needed
        if addr not in clients:
            vip = str(next(ip_pool))
            clients[addr] = {
                "cipher": ChaCha20Poly1305(PSK),
                "vip": vip
            }
            ip_to_client[vip] = addr
            print(f"[SERVER] Client {addr} assigned {vip}")
            print("[SERVER] clients:", clients)
            print("[SERVER] ip_to_client:", ip_to_client)
        state = clients[addr]
        cipher = state["cipher"]
        client_vip = state["vip"]
        try:
            nonce = data[:12]
            encrypted = data[12:]
            packet = cipher.decrypt(nonce, encrypted, None)
            
            # 🔒 SOURCE IP OWNERSHIP CHECK
            src_ip = socket.inet_ntoa(packet[12:16])
            print(f"[SERVER DEBUG] addr={addr} src_ip={src_ip} expected_vip={client_vip}")
            if src_ip != client_vip:
                print(f"[SERVER] Spoofed packet from {addr}, SRC={src_ip}, expected {client_vip}")
                continue
            os.write(tun, packet)
        except Exception as e:
            print(f"[SERVER] Decryption failed from {addr}: {e}")

t1 = threading.Thread(target=sock_to_tun, daemon=True)
t2 = threading.Thread(target=tun_to_sock, daemon=True)

t1.start()
t2.start()
print("[SERVER] VPN forwarding started")
t1.join()
t2.join()
