import json

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
        self.bus_link.moveServo(self.id, pos)
        self.curr_angle = pos

    def setOffsetPosition(self, offset):
        self.setPosition(self.curr_angle - offset)

class LEG:
    def __init__(self, servo_objects):
        self.servos = servo_objects
        self.clean_ids = [s.id for s in self.servos]

    def positionLeg(self, angs):
        for i in range(len(servo_objects)):
            if angs[i] is not None:
                self.servo_objects[i].setPosition(angs[i])

    def positionLegOffset(self, offsets):
        for i in range(len(servo_objects)):
            if offsets[i] is not None:
                self.servo_objects[i].setOffsetPosition(offsets[i])

class HEXAPOD_BODY:
    def __init__(self, servo_params, bus_link):
        self.leg_objects = {"front_right":None, "front_left":None, "mid_right":None, "mid_left":None, "rear_right":None, "rear_left":None}

        for leg in self.leg_objects.keys():
            servos = []
            for id in servo_params["leg_ids"][leg]:
                angs = servo_params["leg_angles"][str(id)]
                servos.append(SERVO(id, *angs, bus_link))
            self.leg_objects[leg] = LEG(servos)

if __name__ == "__main__":
    lx_bus= LX16A_BUS_MODIFIED(debug = True)

    with open('servo_params') as f:
        params = json.load(f)
    main_hexapod = HEXAPOD_BODY(params, lx_bus)