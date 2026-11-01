import time
import logging
import threading

from dotenv import load_dotenv

load_dotenv()

from modules.mdns import get_local_ip, start_mdns
from modules.routes import run_server
from modules.system import SystemController

logging.getLogger("werkzeug").setLevel(logging.WARNING)

# HOST = "127.0.0.1" # リバースプロキシ
HOST = "0.0.0.0"  # 全て
PORT = 5000


def main():
    system = SystemController()

    ip = get_local_ip()
    print(f"[Server] \033[32mhttp://{ip}:{PORT}\033[0m")

    zeroconf, mdns_info = start_mdns(
        hostname="mizumori.local.",
        service_name="MizuMori Web._http._tcp.local.",
        port=PORT,
    )

    server_thread = threading.Thread(
        target=run_server,
        args=(system, HOST, PORT),
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
    finally:
        zeroconf.unregister_service(mdns_info)
        zeroconf.close()

        system.stop_system()
        system.close()


if __name__ == "__main__":
    main()
