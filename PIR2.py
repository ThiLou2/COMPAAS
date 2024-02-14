import RPi.GPIO as GPIO

PIR_PIN = 7
GPIO.setmode(GPIO.BOARD) #Phys. on board vs. BCM, nb. of GPIO
GPIO.setup(PIR_PIN,GPIO.IN)

class PIR2(object):
    def DetectsDoorOpening(self):
        #print("PIR pin:"+str(GPIO.input(PIR_PIN)))
        return GPIO.input(PIR_PIN)
