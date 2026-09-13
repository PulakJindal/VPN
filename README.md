This is my personal project where I am trying to gain knowledge of how a VPN works.
And to learn this, I am trying to build my own VPN where you can make any device a VPN server, and when a client connects to it, it provides a secure connection over the internet.
Now, because you are choosing the server as per your choice, it only helps you to bypass the firewall restrictions of the wifi or ISP you are on.

In order to learn things, I first made a simple server-client model. Where the server accepts multiple clients, handles the error, and disconnect securly. 
When the client sends some msg to the server, the server echo back the same message to the client.

Then I learn about the TUN interfaces, which work on the IP level of the packet.
Gives a false sense to the OS that this is another NIC.
Then we can send all the packets through that interface, which will eventually transfer all the packets to the VPN server.
Then the server sends the packet to the internet and gets the response from the internet, which it redirects to the client.

Till now, I made these things on a single device, so I made two namespaces for client and server. And that's too on a Linux machine.
Then I connect them via a veth.
Then I connect the server to the Host via another veth because in the end host is the endpoint that is connected to the internet.
Then I enabled ip forwarding on the server and the host.
Then I enabled the NAT on both also.

Encryption (ChaCha20-Poly1305) and a source-IP spoofing check are already working.
The protocol is UDP now. Still using a hardcoded pre-shared key — no real key exchange yet.
Next: real key exchange, then get off Linux network namespaces so this can run on separate machines.

## Project layout

- `vpn/` — the actual VPN: `vpn_server.py`, `vpn_client.py`
- `network-lab/` — everything that sets up the test environment on one machine:
  - `myscript.sh` — creates `client_ns`/`server_ns`, wires up veths, enables NAT/forwarding, starts the server
  - `client2.sh` — adds a second client namespace, for testing multiple clients
  - `testing.sh` — ping checks across the setup
  - `reverse.sh` — tears everything down
- `learning/` — the original TCP echo server/client from before the TUN work started. Not part of the live VPN, kept for reference.

## Running it

```bash
pip install cryptography
sudo bash network-lab/myscript.sh          # sets up namespaces, starts the server
sudo ip netns exec client_ns python3 vpn/vpn_client.py   # in another terminal
sudo bash network-lab/testing.sh           # sanity-check pings
sudo bash network-lab/reverse.sh           # tear it all down
```

## Known issues

- `client2.sh` assigns the second client's veth the same IP already used by the first (`192.168.138.1/24`) — collision, not yet fixed.