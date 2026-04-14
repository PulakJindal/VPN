#!/bin/bash

# ============================================================
# cleanup.sh — Reverses everything done by myscript.sh
#              and client2.sh, in reverse order.
# Run with: sudo bash cleanup.sh
# ============================================================


# -------------------------------------------------------
# STEP 1: Remove NAT rules on HOST
# These were added by myscript.sh to masquerade traffic
# from server_ns going out through the host's internet interface.
# We delete (-D) the same rule that was added (-A).
# -------------------------------------------------------
echo "[1] Removing NAT (MASQUERADE) rule on HOST..."
HOST_IFACE=$(ip route | grep default | awk '{print $5}')
if [ -n "$HOST_IFACE" ]; then
    sudo iptables -t nat -D POSTROUTING -s 172.30.0.0/24 -o "$HOST_IFACE" -j MASQUERADE
    echo "    Removed MASQUERADE rule for 172.30.0.0/24 on $HOST_IFACE"
else
    echo "    Warning: Could not detect default interface, skipping HOST NAT rule removal"
fi
echo ""


# -------------------------------------------------------
# STEP 2: Remove NAT rule inside server_ns
# This was added to masquerade VPN client traffic (10.8.0.0/24)
# going out through server_veth2 toward the host.
# -------------------------------------------------------
echo "[2] Removing NAT rule inside server_ns..."
sudo ip netns exec server_ns iptables -t nat -D POSTROUTING -s 10.8.0.0/24 -o server_veth2 -j MASQUERADE
echo "    Removed MASQUERADE rule inside server_ns"
echo ""


# -------------------------------------------------------
# STEP 3: Remove the host_veth interface
# This was the host-side end of the veth pair connecting
# server_ns to the host. Deleting one end of a veth pair
# automatically deletes the other end (server_veth2 inside server_ns).
# -------------------------------------------------------
echo "[3] Removing host_veth (and its peer server_veth2 inside server_ns)..."
sudo ip link del host_veth
echo "    Deleted host_veth (server_veth2 auto-deleted as it's a veth pair)"
echo ""


# -------------------------------------------------------
# STEP 4: Cleanup from client2.sh — Remove client2_ns namespace
# Deleting a namespace automatically:
#   - Destroys all interfaces inside it (client2_veth, tun0)
#   - Removes all routes and iptables rules inside it
# The peer interface server_veth3 (inside server_ns) must be
# deleted separately below.
# -------------------------------------------------------
echo "[4] Deleting client2_ns namespace..."
sudo ip netns del client2_ns
echo "    Deleted client2_ns (client2_veth and its tun0 auto-removed)"
echo ""


# -------------------------------------------------------
# STEP 5: Remove server_veth3 from server_ns
# This was the server-side end of the veth pair for client2.
# Its peer (client2_veth) was already removed in step 4
# when client2_ns was deleted, but the server side still
# exists inside server_ns and must be removed manually.
# -------------------------------------------------------
echo "[5] Removing server_veth3 from server_ns..."
sudo ip link del server_veth3 2>/dev/null || \
    sudo ip netns exec server_ns ip link del server_veth3 2>/dev/null || \
    echo "    server_veth3 already gone (may have been auto-removed)"
echo ""


# -------------------------------------------------------
# STEP 6: Delete client_ns namespace
# Deleting the namespace cleans up everything inside it:
#   - client_veth (veth interface)
#   - tun0 (TUN interface)
#   - All routes (including the 8.8.8.8 -> tun0 route)
#   - lo interface
# The peer (server_veth inside server_ns) is NOT auto-removed.
# -------------------------------------------------------
echo "[6] Deleting client_ns namespace..."
sudo ip netns del client_ns
echo "    Deleted client_ns (client_veth, tun0, routes all auto-removed)"
echo ""


# -------------------------------------------------------
# STEP 7: Delete server_ns namespace
# At this point server_ns still has:
#   - server_veth  (peer of client_veth, already gone)
#   - server_veth3 (removed in step 5, or already gone)
#   - tun0
#   - lo
#   - All routes including default via 172.30.0.1
# Deleting the namespace nukes all of them at once.
# -------------------------------------------------------
echo "[7] Deleting server_ns namespace..."
sudo ip netns del server_ns
echo "    Deleted server_ns (server_veth, tun0, all routes auto-removed)"
echo ""


# -------------------------------------------------------
# STEP 8: Verify no namespaces remain
# Should print nothing if cleanup was successful.
# -------------------------------------------------------
echo "[8] Verifying namespaces are gone..."
REMAINING=$(ip netns list)
if [ -z "$REMAINING" ]; then
    echo "    All namespaces removed successfully."
else
    echo "    Warning: Some namespaces still exist:"
    echo "    $REMAINING"
fi
echo ""


# -------------------------------------------------------
# STEP 9: Optional — disable IP forwarding on HOST
# myscript.sh enabled this. Comment out if other
# programs on your machine also need IP forwarding.
# -------------------------------------------------------
echo "[9] Disabling IP forwarding on HOST..."
sudo sysctl -w net.ipv4.ip_forward=0
echo "    IP forwarding disabled"
echo ""


echo "============================================"
echo " Cleanup complete."
echo "============================================"