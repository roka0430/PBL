import socket
import time

from zeroconf import Zeroconf, ServiceInfo


def get_local_ip():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    finally:
        sock.close()


def start_mdns(hostname, service_name, port):
    ip = get_local_ip()

    info = ServiceInfo(
        "_http._tcp.local.",
        service_name,
        addresses=[socket.inet_aton(ip)],
        port=port,
        server=hostname,
    )

    zeroconf = Zeroconf()
    zeroconf.register_service(info)

    return zeroconf, info
