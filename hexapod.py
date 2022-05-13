import json
from time import sleep
import threading

from pip import main

from lx16a_controller import LX16A_BUS_MODIFIED

class SERVO:
    def __init__(self, id, min, max, init, bus_link):
        self.id = id
        self.min = min
        self.max = max
        self.init = init
        self.curr_angle = init
        self.bus_link = bus_link

    def initServoState(self):
        self.bus_link.setAngleLimit(self.id, self.min, self.max)
        self.setPosition(self.init)

    def getPosition(self):
        return self.bus_link.readPosition(self.id)

    def setPosition(self, pos):
        if pos > self.max:
            pos = self.max
        elif pos < self.min:
            pos = self.min

        self.bus_link.moveServo(self.id, pos)
        self.curr_angle = pos

    def getServoStatus(self):
        return self.bus_link.readLedError(self.id)

class LEG:
    def __init__(self, servo_objects):
        self.servos = servo_objects
        self.clean_ids = [s.id for s in self.servos]
        self.curr_angs = [s.curr_angle for s in self.servos]

    def updateCurrAngles(self):
        self.curr_angs = [s.curr_angle for s in self.servos]

    def raiseLowerLegParallel(self, z):
        self.servos[1].setPosition(self.curr_angs[1] - z)
        self.servos[2].setPosition(self.curr_angs[2] + z)
        self.updateCurrAngles()

    def moveLegArc(self, arc):
        self.servos[0].setPosition(self.curr_angs[0] + arc)
        self.updateCurrAngles()

    def stretchLeg(self, z):
        self.servos[1].setPosition(self.curr_angs[1] + z)
        self.servos[2].setPosition(self.curr_angs[2] - abs(z * 2))
        self.updateCurrAngles()

    def retractLeg(self, z):
        self.servos[1].setPosition(self.curr_angs[1] - z)
        self.servos[2].setPosition(self.curr_angs[2] + (z * 2))
        self.updateCurrAngles()

    def getLegStatus(self):
        errors = {s.id: s.getServoStatus() for s in self.servos}
        return errors

class HEXAPOD_BODY:
    def __init__(self, servo_params, bus_link):
        self.leg_objects = {"front_right":None, "front_left":None, "mid_right":None, "mid_left":None, "rear_right":None, "rear_left":None}

        for leg in self.leg_objects.keys():
            servos = []
            for id in servo_params["leg_ids"][leg]:
                angs = servo_params["leg_angles"][str(id)]
                servos.append(SERVO(id, *angs, bus_link))
            self.leg_objects[leg] = LEG(servos)

    def printServoStatus(self):
        for leg in self.leg_objects.keys():
            print(leg)
            error = self.leg_objects[leg].getLegStatus()
            for id in error.keys():
                print(id, error[id], "\n")

    def changeBodyHeight(self, z):
        for leg in self.leg_objects:
            self.leg_objects[leg].raiseLowerLegParallel(z)

    def reorientYaw(self):
        for leg in self.leg_objects:
            self.leg_objects[leg].servos[0].setPosition(500)
            self.leg_objects[leg].updateCurrAngles()

    def rotateInPlace(self, arc, z):
        first_group = ["front_right", "rear_right", "mid_left"]
        second_group = ["front_left", "rear_left", "mid_right"]

        #lift first group legs, rotate forward, and then lower
        for leg in first_group:
            self.leg_objects[leg].raiseLowerLegParallel(z)
        sleep(0.5)
        for leg in first_group:
            self.leg_objects[leg].moveLegArc(arc)
        sleep(0.5)
        for leg in first_group:
            self.leg_objects[leg].raiseLowerLegParallel(z * -1)
        sleep(0.5)

        for leg in second_group:
            self.leg_objects[leg].raiseLowerLegParallel(z)
        sleep(0.5)
        for leg in first_group:
            self.leg_objects[leg].moveLegArc(arc * -1)
        sleep(0.5)
        for leg in second_group:
            self.leg_objects[leg].raiseLowerLegParallel(z * -1)
        sleep(0.5)

    def liftLegs(self, arc, z, group): #Expected group notation: [front, rear, mid]
        #front leg: stretch forward, move arc slightly inwards
        self.leg_objects[group[0]].stretchLeg(z)
        self.leg_objects[group[0]].moveLegArc(arc//2)

        #rear leg: lift and retract, move arc slightly outwards
        # self.leg_objects[group[1]].raiseLowerLegParallel(z)
        # self.leg_objects[group[1]].moveLegArc(arc//2)

        #middle leg: lift and rotate it forward
        # self.leg_objects[group[2]].raiseLowerLegParallel(z)
        # self.leg_objects[group[2]].moveLegArc(arc * -1)
        sleep(1)

    def pushLegs(self, arc, z, group):
        #front leg: retract and rotate slightly outwards
        self.leg_objects[group[0]].moveLegArc(arc//2)
        self.leg_objects[group[0]].retractLeg(z)

        #rear leg: stretch outwards, move arc slightly inwards?
        # self.leg_objects[group[1]].stretchLeg(z)

        #middle leg: rotate it backward
        # self.leg_objects[group[2]].moveLegArc(arc * -1)
        sleep(1)

    def moveForward(self, arc, z):
        first_group = ["front_right", "rear_right", "mid_left"]
        second_group = ["front_left", "rear_left", "mid_right"]

        arc_half = int(arc/2)

        self.leg_objects["front_right"].raiseLowerLegParallel(z)
        self.leg_objects["front_right"].moveLegArc(int(arc_half/2))
        self.leg_objects["front_right"].stretchLeg(z)
        sleep(1)

        self.leg_objects["front_right"].retractLeg(z)
        self.leg_objects["front_right"].moveLegArc(int(arc_half/2))
        sleep(1)

        # # First group initial lift motion
#        self.liftLegs(arc_half, z, first_group)
#        self.pushLegs(arc_half, z, second_group)
        # # Second group place motion
#        self.liftLegs(arc_half, z * -1, first_group)
#        self.pushLegs(arc_half, z, second_group)

        # # Second group initial lift motion
#        self.liftLegs(arc_half * -1, z, second_group)
#        self.pushLegs(arc_half * -1, z, first_group)
        # # Second group place motion
#        self.liftLegs(arc_half * -1, z * -1, second_group)
#        self.pushLegs(arc_half * -1, z, first_group)

    def moveInDirection(self, leg_directions, arc, z):
        pass

def printHexapodErrors():
    while True:
        main_hexapod.printServoStatus()
        sleep(1)


if __name__ == "__main__":
    lx_bus= LX16A_BUS_MODIFIED(debug = False)
    with open('servo_params') as f:
        params = json.load(f)
    main_hexapod = HEXAPOD_BODY(params, lx_bus)

    # status_thread = threading.Thread(target=printHexapodErrors, args=())
    # status_thread.start()

    main_hexapod.reorientYaw()

    for i in range(1, 10):
        main_hexapod.changeBodyHeight(i * 10)
    sleep(1)
    for i in range(1, 10):
        main_hexapod.changeBodyHeight(i * -10)
    sleep(1)

    # for i in range(5):
    #     main_hexapod.rotateInPlace(20, 20)

    for i in range(5):
        main_hexapod.moveForward(75, 200)
