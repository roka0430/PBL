import time
import socket
import logging
import threading

from modules.mdns import get_local_ip, start_mdns
from modules.routes import run_server, PORT
from modules.watering import SystemController

logging.getLogger("werkzeug").setLevel(logging.WARNING)


def main():
    system = SystemController()

    ip = get_local_ip()
    print(f"[Server] \033[32mhttp://{ip}:{PORT}\033[0m")

    # zeroconf, mdns_info = start_mdns(
    #     hostname="mizumori.local.",
    #     service_name="MizuMori Web._http._tcp.local.",
    #     port=PORT,
    # )

    server_thread = threading.Thread(
        target=run_server,
        args=(system,),
        daemon=True,
    )

    watering_thread = threading.Thread(
        target=system.mainloop,
        daemon=True,
    )

    server_thread.start()
    watering_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("終了します")
    # finally:
    #     zeroconf.unregister_service(mdns_info)
    #     zeroconf.close()


if __name__ == "__main__":
    main()
