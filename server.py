import socket
import threading

PORT = 5555
SERVER = socket.gethostbyname(socket.gethostname())
# print("Server IP:", SERVER)
ADDR = (SERVER, PORT)
FORMAT = "utf-8"
HEADER = 64

soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
soc.bind(ADDR)
soc.listen()

def recv_exact(conn, n):
    data = b''
    while len(data) < n:
        packet = conn.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    try:
        connected = True
        while connected:
            msg_length = recv_exact(conn, HEADER).decode()
            if not msg_length.isnumeric():
                raise ValueError("Header is not numeric")
            if int(msg_length) > 10_000:
                raise ValueError("Payload too large")
            if msg_length:
                msg_length = int(msg_length)
                msg = recv_exact(conn, msg_length).decode(FORMAT)
                if msg == "DISCONNECT":
                    connected = False
                print(f"[{addr}] {msg}")
                res_len = str(msg_length).encode(FORMAT)
                res_len += b' ' * (HEADER - len(res_len))
                conn.send(res_len)
                conn.sendall(msg.encode(FORMAT))
    except Exception as e:
        print(f"[ERROR] {addr}: {e}")
    finally:
        conn.close()
        print(f"[DISCONNECTED] {addr} disconnected.")

def start():
    print(f"[LISTENING] Server is listening on {SERVER}:{PORT}")
    while True:
        conn, addr = soc.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")
        
print("[STARTING] Server is starting...")
start()