import time

import board
import adafruit_ahtx0

sensor = adafruit_ahtx0.AHTx0(board.I2C())

while True:
    temperature = sensor.temperature
    humidity = sensor.relative_humidity

    print(temperature, humidity)
    time.sleep(1)
