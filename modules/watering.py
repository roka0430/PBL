import time


class WateringController:
    def mainloop(self):
        while True:
            print("watering mainloop")
            time.sleep(5)

    def request_watering(self, n):
        print("request: ", n)
