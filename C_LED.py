import RPi.GPIO as GPIO

LED_PIN = 29
GPIO.setmode(GPIO.BOARD) 
GPIO.setup(LED_PIN,GPIO.OUT)

class C_LED(object):
    def SetAlarm(self):
        GPIO.output(LED_PIN,GPIO.HIGH)
