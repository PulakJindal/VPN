!#/bin/bash

echo "Making the namespaces...."
sudo ip netns add client_ns
sudo ip netns add server_ns
echo ""

echo "Namespaces created:"
echo "$(ip netns list)"
echo ""

echo "Creating veth (virtual ethernet)"
sudo ip link add client_veth type veth peer name server_veth
echo "Veth created with end names : client_veth and server_veth"
echo ""

echo "Pluging the veth ends to the namespaces..."
sudo ip link set client_veth netns client_ns
echo "Client end connected"
sudo ip link set server_veth netns server_ns
echo "Server end connected"
echo ""

echo "Giving ip address to the namespaces..."
sudo ip netns exec client_ns ip addr add 192.168.138.2/24 dev client_veth
echo "Gave ip 192.168.138.2 to client namespace $(sudo ip netns exec client_ns ip addr show)"
sudo ip netns exec server_ns ip addr add 192.168.138.1/24 dev server_veth
echo "Gave ip 192.168.138.1 to server namespace $(sudo ip netns exec server_ns ip addr show)"
echo ""

echo "Bringing interface up..."
sudo ip netns exec client_ns ip link set client_veth up
echo "Client side interface up done"
sudo ip netns exec server_ns ip link set server_veth up
echo "Server side interface up done"
echo ""

echo "Enabling loopback..."
sudo ip netns exec client_ns ip link set lo up
echo "Client side loopback up done"
sudo ip netns exec server_ns ip link set lo up
echo "Server side loopback up done"
echo ""

echo "Creating TUN interfaces for the two namespaces..."
sudo ip netns exec client_ns ip tuntap add dev tun0 mode tun
echo "Client TUN interface created"
sudo ip netns exec server_ns ip tuntap add dev tun0 mode tun
echo "Server TUN interface created"
echo ""

echo "Assigning ips to the TUN interfaces of the 2 namespaces"
sudo ip netns exec client_ns ip addr add 10.8.0.2/24 dev tun0
echo "IP assigned to the client TUN interface -> 10.8.0.2/24"
sudo ip netns exec server_ns ip addr add 10.8.0.1/24 dev tun0
echo "IP assigned to the server TUN interface -> 10.8.0.1/24"
echo ""

echo "Bringing TUN interfaces up"
sudo ip netns exec client_ns ip link set tun0 up
echo "Client TUN interface UP done $(sudo ip netns exec client_ns ip addr show tun0)"
sudo ip netns exec server_ns ip link set tun0 up
echo "Server TUN interface UP done $(sudo ip netns exec server_ns ip addr show tun0)"
echo ""

echo "Adding route in client namespace for test IP..."
sudo ip netns exec client_ns ip route add 8.8.8.8/32 dev tun0
echo "Route added: client_ns → 8.8.8.8 via tun0"
echo ""

echo "Enabling IP forwarding inside server namespace (acts as VPN router)..."
sudo ip netns exec server_ns sysctl -w net.ipv4.ip_forward=1
echo "$(sudo ip netns exec server_ns sysctl net.ipv4.ip_forward)"
echo ""

echo "Making another veth for server_ns to HOST communication..."
sudo ip link add server_veth2 type veth peer name host_veth
echo "Veth pair created: server_veth2 <-> host_veth"

echo "Assigning veth interfaces to namespaces..."
sudo ip link set server_veth2 netns server_ns
echo "Assigned server_veth2 to server_ns"
echo ""

echo "Assigning ip to server_veth2 and bringing it up..."
sudo ip netns exec server_ns ip addr add 172.30.0.2/24 dev server_veth2
sudo ip netns exec server_ns ip link set server_veth2 up
echo "server_veth2 configured ip -> 172.30.0.2/24 and up in server_ns"

echo "Assigning ip to host_veth and bringing it up..."
sudo ip addr add 172.30.0.1/24 dev host_veth
sudo ip link set host_veth up
echo "host_veth configured ip -> 172.30.0.1/24 and up on HOST"
echo ""

echo "Adding route in server_ns to route to HOST..."
sudo ip netns exec server_ns ip route add default via 172.30.0.1
echo "Route added: server_ns → default via 172.30.0.1"
echo "$(sudo ip netns exec server_ns ip route)"
echo ""

echo "Enabling IP forwarding on HOST..."
sudo sysctl -w net.ipv4.ip_forward=1
echo "$(sudo sysctl net.ipv4.ip_forward)"
echo ""

echo "Enabling NAT on server_ns for client_ns traffic to HOST..."
sudo ip netns exec server_ns iptables -t nat -A POSTROUTING -s 10.8.0.0/24 -o server_veth2 -j MASQUERADE
echo "$(sudo ip netns exec server_ns iptables -t nat -L POSTROUTING -n -v)"
echo ""

echo "Detecting HOST internet interface..."
HOST_IFACE=$(ip route | grep default | awk '{print $5}')

if [ -n "$HOST_IFACE" ]; then
    echo "Your host default interface is: $HOST_IFACE"
else
    echo "No default interface detected, exiting..."
    exit 1
fi

echo "Detected internet interface: $HOST_IFACE"
echo ""

echo "Applying NAT on HOST (CORRECT PLACE)..."
sudo iptables -t nat -A POSTROUTING -s 172.30.0.0/24 -o "$HOST_IFACE" -j MASQUERADE
sudo iptables -t nat -L POSTROUTING -n -v
echo ""
