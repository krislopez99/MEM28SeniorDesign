import json
from time import sleep
import threading

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

    def moveForward(self, arc, z):
        first_group = ["front_right", "rear_right", "mid_left"]
        second_group = ["front_left", "rear_left", "mid_right"]

        #lift first group legs, rotate forward, and then lower
        for leg in first_group:
            self.leg_objects[leg].raiseLowerLegParallel(z)
        sleep(0.5)
        self.leg_objects["front_right"].moveLegArc(arc)
        self.leg_objects["rear_right"].moveLegArc(arc)
        self.leg_objects["mid_left"].moveLegArc(arc * -1)
        sleep(0.5)
        for leg in first_group:
            self.leg_objects[leg].raiseLowerLegParallel(z * -1)
        sleep(0.5)

        for leg in second_group:
            self.leg_objects[leg].raiseLowerLegParallel(z)
        sleep(0.5)
        self.leg_objects["front_right"].moveLegArc(arc * -1)
        self.leg_objects["rear_right"].moveLegArc(arc * -1)
        self.leg_objects["mid_left"].moveLegArc(arc)
        sleep(0.5)
        for leg in second_group:
            self.leg_objects[leg].raiseLowerLegParallel(z * -1)
        sleep(0.5)

    def moveInDirection(self, leg_directions, arc, z):
        pass

def printHexapodErrors():
    while True:
        main_hexapod.printServoStatus()
        sleep(1)


if __name__ == "__main__":
    lx_bus= LX16A_BUS_MODIFIED(debug = True)
    with open('servo_params') as f:
        params = json.load(f)
    main_hexapod = HEXAPOD_BODY(params, lx_bus)

    status_thread = threading.Thread(target=printHexapodErrors, args=())
    status_thread.start()

    for i in range(1, 10):
        main_hexapod.changeBodyHeight(i * 10)
    sleep(1)
    for i in range(1, 10):
        main_hexapod.changeBodyHeight(i * -10)
    sleep(1)
    # for i in range(5):
    #     main_hexapod.rotateInPlace(20, 20)

    for i in range(5):
        main_hexapod.moveForward(20, 20)

