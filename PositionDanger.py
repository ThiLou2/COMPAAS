import RPi.GPIO as GPIO

PIR_PIN = 18
GPIO.setmode(GPIO.BOARD) #Phys. on board vs. BCM, nb. of GPIO
GPIO.setup(PIR_PIN,GPIO.IN)

class PositionDanger(object):
    def DetectsDanger(self,cycle):
        #print(str(cycle))
        if int(cycle) < 10:
            return 0
        else:
            return 1
    def __init__ (self):
        self.fic = open("Alarmlog.txt",'w')
        
