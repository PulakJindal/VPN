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

echo "Checking connectivity by ping from client to server ip"
count=0
while [ $count -lt 3 ]; do
	echo "Attempt $((count+1))"
	if sudo ip netns exec client_ns ping -c 1 192.168.138.1; then
		echo "Ping sucessful, continuing script..."
		break
	else 
		echo "Ping failed!"
		count=$((count+1))
		if [ $count -eq 3 ]; then
			echo "Failed 3 times. Exiting script"
			exit 1
		fi
		echo "Retrying..."
		sleep 2
	fi
done

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

echo "Now you can run the client and server scripts"
echo "You can also route an ip to the namespace TUN interface and then generate traffic to check if it's working or not"