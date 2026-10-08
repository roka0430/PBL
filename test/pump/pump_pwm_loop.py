from time import sleep
from gpiozero import PWMOutputDevice

MOTOR_PIN = 26
PWM_FREQUENCY = 1000
DUTY_CYCLE = 0.5

ON_TIME = 2
OFF_TIME = 2


motor = PWMOutputDevice(MOTOR_PIN, frequency=PWM_FREQUENCY, initial_value=0)

try:
    print("Motor test started.")
    print("Press Ctrl+C to stop.")

    while True:
        print("ON")
        motor.value = DUTY_CYCLE
        sleep(ON_TIME)

        print("OFF")
        motor.off()
        sleep(OFF_TIME)

except KeyboardInterrupt:
    print("\nStopping...")

finally:
    motor.off()
    motor.close()
    print("Motor OFF")
    print("Motor test finished.")
