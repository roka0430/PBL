import time


class WateringController:
    def mainloop(self):
        while True:
            print("watering mainloop")
            time.sleep(5)

    def request_watering(self, amount_ml):
        try:
            amount_ml = int(amount_ml)
        except (TypeError, ValueError):
            return False

        if not 10 <= amount_ml <= 500:
            return False

        print("request:", amount_ml)
        # ここでqueue put

        return True
