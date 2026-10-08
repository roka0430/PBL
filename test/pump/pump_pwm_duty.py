from time import sleep
from gpiozero import PWMOutputDevice

MOTOR_PIN = 26
PWM_FREQUENCY = 1000

DUTY_CYCLES = [
    0.0,
    0.2,
    0.4,
    0.6,
    0.8,
    1.0,
]

STEP_TIME = 1

motor = PWMOutputDevice(MOTOR_PIN, frequency=PWM_FREQUENCY, initial_value=0)

try:
    print("Motor PWM test started.")
    print("Press Ctrl+C to stop.")

    for duty in DUTY_CYCLES:
        print(f"Duty cycle: {duty * 100:.0f}%")
        motor.value = duty
        sleep(STEP_TIME)

    for duty in reversed(DUTY_CYCLES[:-1]):
        print(f"Duty cycle: {duty * 100:.0f}%")
        motor.value = duty
        sleep(STEP_TIME)

    print("Test finished.")

finally:
    motor.off()
    motor.close()
    print("Motor OFF")
