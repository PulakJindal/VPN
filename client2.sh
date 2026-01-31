echo "Creating second client namespace and connecting to server namespace"
sudo ip netns add client2_ns
echo "Namespace created: client2_ns"
echo ""

echo "Creating veth pair for client2_ns and server_ns"
sudo ip link add client2_veth type veth peer name server_veth3
echo "Veth pair created with end names : client2_veth and server_veth3"
echo ""

echo "Plugging the veth ends to the namespaces..."
sudo ip link set client2_veth netns client2_ns
echo "Client2 end connected to client2_ns"
sudo ip link set server_veth3 netns server_ns
echo "Server end connected to server_ns"
echo ""

echo "Giving ip address to the client2_ns namespace and bringing it up..."
sudo ip netns exec client2_ns ip addr add 192.168.138.3/24 dev client2_veth
sudo ip netns exec client2_ns ip link set client2_veth up
echo "Gave ip address to client2_ns" $(sudo ip netns exec client2_ns ip addr show)
echo ""

echo "Bringing server_veth3 up and lo up for client2_ns..."
sudo ip netns exec server_ns ip link set server_veth3 up
sudo ip netns exec client2_ns ip link set lo up
echo "Server side interface up done"
echo ""

echo "Creating TUN interface for client2_ns namespace and bringing it up..."
sudo ip netns exec client2_ns ip tuntap add dev tun0 mode tun
sudo ip netns exec client2_ns ip addr add 10.8.0.3/24 dev tun0
sudo ip netns exec client2_ns ip link set tun0 up
sudo ip netns exec client2_ns ip route add 8.8.8.8/32 dev tun0
echo "Client2 TUN interface created and brought up with IP 10.8.0.3/24"
echo ""

echo "Setting up bridge in server_ns to connect both clients"
sudo ip netns exec server_ns ip link add br0 type bridge
sudo ip netns exec server_ns ip addr add 192.168.138.1/24 dev br0
sudo ip netns exec server_ns ip link set br0 up
sudo ip netns exec server_ns ip link set server_veth master br0
sudo ip netns exec server_ns ip link set server_veth3 master br0
sudo ip netns exec server_ns ip link set br0 type bridge stp_state 0
echo "Bridge br0 set up in server_ns connecting both clients"
echo ""echo "Setup complete. Client2 namespace is ready to communicate with server_ns."
echo ""
