import time

from gpiozero import PWMOutputDevice


class Pump:
    MOTOR_PIN = 26

    PWM_FREQUENCY = 5000
    DUTY_CYCLE = 0.6

    def __init__(self):
        self._motor = PWMOutputDevice(
            self.MOTOR_PIN, frequency=self.PWM_FREQUENCY, initial_value=0
        )

    def start(self):
        self._motor.value = self.DUTY_CYCLE

    def stop(self):
        self._motor.off()

    def close(self):
        self._motor.off()
        self._motor.close()


pump = Pump()

try:
    pump.start()
    time.sleep(3)  # ポンプ駆動時間
finally:
    pump.close()
