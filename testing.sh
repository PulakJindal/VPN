#!/bin/bash

echo "-------------Testing Connectivities------------------"
echo "Testing connectivity from client_ns to server_ns..."
sudo ip netns exec client_ns ping -c 2 192.168.138.1
echo ""

echo "Testing connectivity from server_ns to host..."
sudo ip netns exec server_ns ping -c 2 172.30.0.1
echo ""

echo "Testing connectivity from server_ns to internet..."
sudo ip netns exec server_ns ping -c 2 8.8.8.8
echo ""

echo "Testing connectivity from client_ns to internet..." 
sudo ip netns exec client_ns ping -c 4 8.8.8.8