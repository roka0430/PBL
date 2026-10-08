from time import sleep
from gpiozero import PWMOutputDevice

MOTOR_PIN = 26
PWM_FREQUENCY = 1000
DUTY_CYCLE = 0.5

RUN_TIME = 3

motor = PWMOutputDevice(MOTOR_PIN, frequency=PWM_FREQUENCY, initial_value=0)

print("Motor OFF")
sleep(1)

print("Motor ON")
motor.value = DUTY_CYCLE
sleep(RUN_TIME)

print("Motor OFF")
motor.off()
motor.close()
