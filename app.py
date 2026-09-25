import time
import logging
import threading

from modules.routes import run_server
from modules.watering import WateringController

# logging.getLogger("werkzeug").setLevel(logging.WARNING)


def main():
    watering = WateringController()

    server_thread = threading.Thread(
        target=run_server,
        args=(watering,),
        daemon=True,
    )

    watering_thread = threading.Thread(
        target=watering.mainloop,
        daemon=True,
    )

    server_thread.start()
    watering_thread.start()

    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("終了します")


if __name__ == "__main__":
    main()
