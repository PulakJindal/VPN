This is my personal project where I am trying to gain knowledge of how a VPN works.
And to learn this, I am trying to build my own VPN where you can make any device a VPN server, and when a client connects to it, it provides a secure connection over the internet.
Now, because you are choosing the server as per your choice, it only helps you to bypass the firewall restrictions of the wifi or ISP you are on.

In order to learn things, I first made a simple server-client model. Where the server accepts multiple clients, handles the error, and disconnect securly. 
When the client sends some msg to the server, the server echo back the same message to the client.

Then I learn about the TUN interfaces. Which works on the IP level of the packet.
Gives a false sense to the OS that this is another NIC.
Then we can send all the packets through that interface, which will eventually transfer all the packets to the VPN server.
Then the server sends the packet to the internet and gets the response from the internet, which it redirects to the client.

Till now, I made these things on a single device, so I made two namespaces for client and server. And that's too on a Linux machine.
Then I connect them via a veth.
Then I connect the server to the Host via another veth because in the end host is the endpoint that is connected to the internet.
Then I enabled ip forwarding on the server and the host.
Then I enabled the NAT on both also.

Right now, I am working on the encryption and the authentication.
Then I will try to switch the protocol from TCP to UDP to make it faster.
Then I will try to make the server that can work on different OSes like windows or android.
