import socket

FORMAT = "utf-8"
HEADER = 64
PORT = 5555
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)

def recv_exact(conn, n):
    data = b''
    while len(data) < n:
        packet = conn.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data

def send_message(soc, message):
    message = message.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    soc.send(send_length)
    soc.sendall(message)
    
def main():
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    soc.connect(ADDR)

    print(f"Connected to server at {SERVER}:{PORT}")

    while True:
        message = input("Enter message to send (type 'DISCONNECT' to exit): ")
        send_message(soc, message)
        response_len = recv_exact(soc, HEADER).decode(FORMAT)
        response = recv_exact(soc, int(response_len)).decode(FORMAT)
        if response == "DISCONNECT":
            break
        print(f"Server response: {response}")
    soc.close()
    print("Disconnected from server.")

if __name__ == "__main__":
    main()