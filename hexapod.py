import json
from time import sleep

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

class HEXAPOD_BODY:
    def __init__(self, servo_params, bus_link):
        self.leg_objects = {"front_right":None, "front_left":None, "mid_right":None, "mid_left":None, "rear_right":None, "rear_left":None}

        for leg in self.leg_objects.keys():
            servos = []
            for id in servo_params["leg_ids"][leg]:
                angs = servo_params["leg_angles"][str(id)]
                servos.append(SERVO(id, *angs, bus_link))
            self.leg_objects[leg] = LEG(servos)

    def changeBodyHeight(self, z):
        for leg in self.leg_objects:
            self.leg_objects[leg].raiseLowerLegParallel(z)

    def rotateInPlace(self, arc, z):
        first_group = ["front_right", "rear_right", "mid_left"]
        second_group = ["front_left", "rear_left", "mid_right"]

        #lift first group legs, rotate forward, and then lower
        for leg in first_group:
            self.leg_objects[leg].raiseLowerLegParallel(z)
        sleep(1)
        for leg in first_group:
            self.leg_objects[leg].moveLegArc(arc)
        sleep(1)
        for leg in first_group:
            self.leg_objects[leg].raiseLowerLegParallel(z * -1)
        sleep(1)

        for leg in second_group:
            self.leg_objects[leg].raiseLowerLegParallel(z)
        sleep(1)
        for leg in first_group:
            self.leg_objects[leg].moveLegArc(arc * -1)
        sleep(1)
        for leg in second_group:
            self.leg_objects[leg].raiseLowerLegParallel(z * -1)
        sleep(1)

    def moveInDirection(self, leg_directions, arc, z):
        pass


if __name__ == "__main__":
    lx_bus= LX16A_BUS_MODIFIED(debug = True)

    with open('servo_params') as f:
        params = json.load(f)
    main_hexapod = HEXAPOD_BODY(params, lx_bus)

    for i in range(10, 100, 10):
        main_hexapod.changeBodyHeight(i)
        sleep(1)
    
    sleep(2)

    for i in range(10, 100, 10):
        main_hexapod.changeBodyHeight(i * -1)
        sleep(1)

    sleep(2)
    
    for i in range(5):
        main_hexapod.rotateInPlace(20, 20)
