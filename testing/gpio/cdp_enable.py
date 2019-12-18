import time
try:
    import RPi.GPIO as GPIO
except RuntimeError:
    print("error GPIO - might need sudo")

GPIO.setmode(GPIO.BOARD)

print(f'mode = {GPIO.getmode()}')
ch = 31
GPIO.setup(ch, GPIO.OUT, initial=GPIO.LOW)

for i in range(0, 1):
    GPIO.output(ch, GPIO.LOW)
    time.sleep(1)
    GPIO.output(ch, GPIO.HIGH)
    time.sleep(60)

GPIO.output(ch, GPIO.LOW)
GPIO.cleanup(ch)
