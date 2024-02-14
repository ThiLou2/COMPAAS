import RPi.GPIO as GPIO
import time, multitasking
class ServoMotor(object):
    def __init__ (self):
        GPIO.setmode(GPIO.BOARD) #Phys. on board vs. BCM, nb. of GPIO
        servoPIN = 22
        GPIO.setup(servoPIN,GPIO.OUT)
        self.p = GPIO.PWM(servoPIN,50) # 50Hz, 20ms, see DataSheet
        self.p.start(2.5)
        self.emergency = 1

    def StopsMotor(self):
        #print("ServoMotor: Signal received")
        self.emergency = 1
        #print("Cycle:"+str(self.cycle))
        return self.cycle
        

    def RunsMotor(self):
        if self.emergency == 1:
            self.emergency = 0
            self.motor_go()
        else:
            self.emergency = 0
        
    @multitasking.task
    def motor_go(self):
        print("motor running")
        while self.emergency == 0:
            for self.cycle in [5,7.5,10,12.5,10,7.5,5,2.5]:
                if self.emergency == 0:
                    self.p.ChangeDutyCycle(self.cycle)
                    time.sleep(0.5)
                else:
                    break
