#!/bin/bash

echo "Adding route in client namespace for test IP..."
sudo ip netns exec client_ns ip route add 8.8.8.8/32 dev tun0
echo "Route added: client_ns → 8.8.8.8 via tun0"
echo ""

echo "Testing traffic from client namespace (expected to reach server)..."
sudo ip netns exec client_ns ping -c 2 8.8.8.8
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

echo "Verifying connectivity between HOST and server_ns over new veth pair..."
sudo ip netns exec server_ns ping -c 2 172.30.0.1
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
    # continue with script
else
    echo "No default interface detected, exiting..."
    exit 1
fi

echo "Detected internet interface: $HOST_IFACE"
echo ""

echo "Applying NAT on HOST (CORRECT PLACE)..."
sudo iptables -t nat -A POSTROUTING -s 172.30.0.0/24 -o "$HOST_IFACE" -j MASQUERADE
echo "$(sudo iptables -t nat -L POSTROUTING -n -v)"
echo ""

echo "Testing connectivity from server_ns to internet..."
sudo ip netns exec server_ns ping -c 2 8.8.8.8
echo ""

echo "--------------------------------------------"
echo "FINAL TEST: VPN client to internet"
echo "--------------------------------------------"

sudo ip netns exec client_ns ping -c 4 8.8.8.8