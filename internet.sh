sudo ip addr add 192.168.233.194/24 dev wlan0
sleep 2
sudo iptables -A INPUT -p tcp --dport 8080 -j ACCEPT
sleep 2
sudo iptables-save
sleep 2
