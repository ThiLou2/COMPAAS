import RPi.GPIO as GPIO
BTN_PIN = 16

GPIO.setmode(GPIO.BOARD) #Phys. on board vs. BCM, nb. of GPIO
GPIO.setup(BTN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) 

class Button(object):
    def SetsMotorOn(self):
        return GPIO.input(BTN_PIN)
