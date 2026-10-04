import time
import logging
import threading

from modules.mdns import start_mdns
from modules.routes import run_server
from modules.watering import SystemController

logging.getLogger("werkzeug").setLevel(logging.WARNING)


def main():
    system = SystemController()

    # zeroconf, mdns_info = start_mdns(
    #     hostname="mizumori.local.",
    #     service_name="MizuMori Web._http._tcp.local.",
    #     port=5000,
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
