import time

import spidev

DRY = 800
WET = 300

spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1_000_000
spi.mode = 0

try:
    while True:
        response = spi.xfer2([0x68, 0x00])  # TODO CH0でなければ修正
        soil_moisture_raw = ((response[0] & 0x03) << 8) | response[1]

        soil_moisture = (soil_moisture_raw - DRY) / (WET - DRY) * 100
        print(soil_moisture)
        time.sleep(1)
finally:
    spi.close()
