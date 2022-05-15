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
        self.curr_default = init
        self.curr_angle = init
        self.bus_link = bus_link

    def initServoState(self):
        self.bus_link.setAngleLimit(self.id, self.min, self.max)
        self.setPosition(self.init)

    def setDefaultState(self):
        self.setPosition(self.curr_default)

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

    def setLegInit(self):
        for s in self.servos:
            s.initServoState()
            self.updateCurrAngles()

    def setLegDefault(self):
        for s in self.servos:
            s.setDefaultState()
            self.updateCurrAngles()

    def setNewLegDefault(self):
        self.servos[1].curr_default = self.curr_angs[1]
        self.servos[2].curr_default = self.curr_angs[2]

    def updateCurrAngles(self):
        self.curr_angs = [s.curr_angle for s in self.servos]

    def raiseLowerLegParallel(self, z):
        self.servos[1].setPosition(self.curr_angs[1] - z)
        self.servos[2].setPosition(self.curr_angs[2] + z)
        self.updateCurrAngles()

    def moveLegArc(self, arc):
        self.servos[0].setPosition(self.curr_angs[0] + arc)
        self.updateCurrAngles()

    def setLeg(self, arc, p1, p2): # positive value syntax: CCW, lift, lift
        self.servos[0].setPosition(self.curr_angs[0] + arc)
        self.servos[1].setPosition(self.curr_angs[1] - p1)
        self.servos[2].setPosition(self.curr_angs[2] - p2)
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

    def resetHexapod(self):
        for leg in self.leg_objects:
            self.leg_objects[leg].setLegInit()

    def changeBodyHeight(self, z):
        for leg in self.leg_objects:
            self.leg_objects[leg].raiseLowerLegParallel(z)
            self.leg_objects[leg].setNewLegDefault()

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
        
    def testSingleLeg(self, arc, z, leg_positions = {1: "front_left", 2: "front_right", 3: "mid_right", 4: "rear_right", 5: "rear_left", 6: "mid_left"}):
        first_group = [1, 3, 5]
        second_group = [2, 6, 4]

        self.leg_objects[leg_positions[2]].setLeg(0, z, z)
        sleep(2)
        self.leg_objects[leg_positions[2]].setLeg(int(z/3), z * -1, 0)
        sleep(2)
        self.leg_objects[leg_positions[2]].setLegDefault()
        sleep(2)

    def moveDirection(self, arc, z, leg_positions = {1: "front_left", 2: "front_right", 3: "mid_right", 4: "rear_right", 5: "rear_left", 6: "mid_left"}):
        first_group = [1, 3, 5]
        second_group = [2, 6, 4]

        # positive value syntax for setLeg(arc,p1,p2): CCW, lift, lift
        # stretching/pushing/propelling (WITH setLeg): -p1, +p2
        

        for leg in first_group: #initial lift
            self.leg_objects[leg_positions[leg]].raiseLowerLegParallel(z)
#            if leg == first_group[0]:
#                self.leg_objects[leg_positions[leg]].setLeg(0,0,z)
        sleep(2)

        # front_right and mid_left arc backwards
        self.leg_objects[leg_positions[second_group[0]]].setLeg(int(z / -3), z, int(z * -0.75))
        self.leg_objects[leg_positions[second_group[1]]].setLeg(arc, int(z / -2), int(z / 2))
        # rear_right pushes to propel forwards
        self.leg_objects[leg_positions[second_group[2]]].setLeg(int(z / -3), z * -1, z)
        sleep(2)

        # first group places
#        self.leg_objects[leg_positions[first_group[0]]].setLeg(0, int(z * -1.5), z)
#        self.leg_objects[leg_positions[first_group[1]]].setLeg(0, int(z * -1.5), z)
#        self.leg_objects[leg_positions[first_group[2]]].setLeg(int(z / 3), int(z * -1), z)

        for leg in first_group: #initial lift
            self.leg_objects[leg_positions[leg]].raiseLowerLegParallel(z * -1)
        sleep(2)

        # second lift
        for l in second_group: #initial lift
            self.leg_objects[leg_positions[l]].raiseLowerLegParallel(int(z * 1.5))
        sleep(2)

        # return to original stationary positions
        for leg in first_group:
            self.leg_objects[leg_positions[leg]].setLegDefault()
        sleep(2)
        
        for leg in second_group:
            self.leg_objects[leg_positions[leg]].setLegDefault()
        sleep(2)

#        # final lower
#        for l in second_group:
#            self.leg_objects[leg_positions[l]].raiseLowerLegParallel(z)
#        sleep(2)

    def moveDirectionAlt(self, arc, z, leg_positions =  {1: "front_right", 2: "mid_right", 3: "rear_right", 4: "rear_left", 5: "mid_left", 6: "front_left"}):
        first_group = [2, 4, 6]
        second_group = [1, 3, 5]
        
        # initial lift
        for leg in first_group:
            self.leg_objects[leg_positions[leg]].raiseLowerLegParallel(z)
            if leg == first_group[0]:
                self.leg_objects[leg_positions[leg]].setLeg(0,0,int(z/2))
        sleep(0.5)
        
        # propel forward
        self.leg_objects[leg_positions[second_group[0]]].setLeg(arc, int(z/1.5), int(z/-1.25))
        self.leg_objects[leg_positions[second_group[1]]].setLeg(arc * -1, int(z/1.5), int(z/-1.25))
        self.leg_objects[leg_positions[second_group[2]]].setLeg(0, z * -1, z)
        sleep(0.5)
        
        # initial place
        for leg in first_group:
            self.leg_objects[leg_positions[leg]].raiseLowerLegParallel(z * -1)
            if leg == first_group[0]:
                self.leg_objects[leg_positions[leg]].setLeg(0,0,z * -1)
        sleep(0.5)
        
        # second lift
        self.leg_objects[leg_positions[second_group[0]]].raiseLowerLegParallel(z)
        self.leg_objects[leg_positions[second_group[1]]].raiseLowerLegParallel(z)
        self.leg_objects[leg_positions[second_group[2]]].setLeg(0, z * 2, z * -1)
        sleep(0.5)
        
        # reorient second legs
        self.leg_objects[leg_positions[second_group[0]]].moveLegArc(arc * -1)
        self.leg_objects[leg_positions[second_group[1]]].moveLegArc(arc)
        self.leg_objects[leg_positions[second_group[2]]].setLeg(0, z, z * -1)
        sleep(0.5)
        
        # second place
        for leg in self.leg_objects:
            self.leg_objects[leg].setLegDefault()
        sleep(0.5)
        

if __name__ == "__main__":
    lx_bus= LX16A_BUS_MODIFIED(debug = False)
    with open('servo_params') as f:
        params = json.load(f)
    main_hexapod = HEXAPOD_BODY(params, lx_bus)

    main_hexapod.resetHexapod()
    sleep(2)

#    for i in range(1, 10):
#        main_hexapod.changeBodyHeight(i * 10)
#    sleep(1)
#    for i in range(1, 10):
#        main_hexapod.changeBodyHeight(i * -10)
#    sleep(1)

    # for i in range(5):
    #     main_hexapod.rotateInPlace(20, 20)

    for i in range(10):
        main_hexapod.moveDirectionAlt(125, 200)
