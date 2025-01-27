import socket
import subprocess
from concurrent.futures import ThreadPoolExecutor

# Configuration
base_ip = "192.168."  # Base IP to scan
port = 8080           # Port to check for connections
threads = 1000         # Number of threads for parallel scanning

def ping_and_check(ip):
    """Ping the host and check if the port is open."""
    try:
        # Ping the host
        ping_result = subprocess.run(
            ["ping", "-c", "1", "-W", "1", ip],  # On Windows, use ["ping", "-n", "1", ip]
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if ping_result.returncode != 0:
            return None  # Host is not reachable

        # Check if the port is open
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.5)  # Reduced timeout for faster scanning
            if sock.connect_ex((ip, port)) == 0:
                return ip  # Port is open
    except Exception:
        pass
    return None  # Port is closed or an error occurred

def find_servers(base, port):
    """Scan the subnet for available servers."""
    ip_list = [f"{base}{subnet}.{host}" for subnet in range(256) for host in range(1, 255)]
    available_servers = []

    with ThreadPoolExecutor(max_workers=threads) as executor:
        # Map all IPs to threads for scanning
        results = executor.map(ping_and_check, ip_list)
        for result in results:
            if result:
                available_servers.append(result)
                print(f"Server found: {result}:{port}")
                break

    return available_servers

if __name__ == "__main__":
    print(f"Scanning {base_ip}x.x for servers on port {port} with {threads} threads...")
    servers = find_servers(base_ip, port)
    if servers:
        print("\nAvailable servers:")
        for server in servers:
            print(f"{server}:{port}")
    else:
        print("No available servers found.")
