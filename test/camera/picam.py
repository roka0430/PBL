import time
from pathlib import Path
from picamera2 import Picamera2

BASE_DIR = Path(__file__).resolve().parent
IMAGE_PATH = BASE_DIR / "test.jpg"

picam2 = Picamera2()

config = picam2.create_still_configuration(main={"size": (1280, 720)})
picam2.configure(config)

picam2.start()
time.sleep(2)
picam2.capture_file(str(IMAGE_PATH))
picam2.stop()

print(f"saved: {IMAGE_PATH}")
