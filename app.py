import threading
import logging
import time

from modules.routes import run_server

logging.getLogger("werkzeug").setLevel(logging.WARNING)


def main():
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("終了します")


if __name__ == "__main__":
    main()
