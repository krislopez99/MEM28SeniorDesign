#!/usr/bin/python3
from time import sleep
from serial import Serial
import struct

class LX16A_BUS:
    LED_OFF = 1
    LED_ON = 0

    LED_ERROR_NONE = 0
    LED_ERROR_OVER_TEMPERATURE=1
    LED_ERROR_OVER_VOLTAGE    =2
    LED_ERROR_OVER_TEMPERATURE_AND_VOLTAGE=3
    LED_ERROR_LOCK_ROTOR      =4
    LED_ERROR_OVER_TEMPERATE_AND_STALLED=5
    LED_ERROR_OVER_VOLTAGE_AND_STALLED=6
    LED_ERROR_OVER_ALL        = 7

    SERVO_FRAME_HEADER        =0x55
    SERVO_MOVE_TIME_WRITE     =1
    SERVO_MOVE_TIME_READ      =2
    SERVO_MOVE_TIME_WAIT_WRITE=7
    SERVO_MOVE_TIME_WAIT_READ =8
    SERVO_MOVE_START          =11
    SERVO_MOVE_STOP           =12
    SERVO_ID_WRITE            =13
    SERVO_ID_READ             =14
    SERVO_ANGLE_OFFSET_ADJUST =17
    SERVO_ANGLE_OFFSET_WRITE  =18
    SERVO_ANGLE_OFFSET_READ   =19
    SERVO_ANGLE_LIMIT_WRITE   =20
    SERVO_ANGLE_LIMIT_READ    =21
    SERVO_VIN_LIMIT_WRITE     =22
    SERVO_VIN_LIMIT_READ      =23
    SERVO_TEMP_MAX_LIMIT_WRITE=24
    SERVO_TEMP_MAX_LIMIT_READ =25
    SERVO_TEMP_READ           =26
    SERVO_VIN_READ            =27
    SERVO_POS_READ            =28
    SERVO_OR_MOTOR_MODE_WRITE =29
    SERVO_OR_MOTOR_MODE_READ  =30
    SERVO_LOAD_OR_UNLOAD_WRITE=31
    SERVO_LOAD_OR_UNLOAD_READ =32
    SERVO_LED_CTRL_WRITE      =33
    SERVO_LED_CTRL_READ       =34
    SERVO_LED_ERROR_WRITE     =35
    SERVO_LED_ERROR_READ      =36

    def __init__(self, Port="/dev/ttyUSB0", Baudrate=115200, Timeout= 0.001, debug=False):
        if not debug:
            self.serial = Serial(Port,baudrate=Baudrate,timeout=Timeout)
            self.serial.setDTR(1)
        else:
            self.serial = None
        self.TX_DELAY_TIME = 0.00002
        self.Header = struct.pack("<BB",0x55,0x55)

    def sendPacket(self,packet):
        sum = 0

        for item in packet:
            sum = sum + item
        
        fullPacket = bytearray(self.Header + packet + struct.pack("<B",(~sum) & 0xff))
        self.serial.write(fullPacket)

        sleep(self.TX_DELAY_TIME)

    def sendReceivePacket(self,packet,receiveSize):
        t_id = packet[0]
        t_command = packet[2]
        self.serial.flushInput()
        self.serial.timeout=0.1
        self.sendPacket(packet)
        r_packet = self.serial.read(receiveSize+3)
        return r_packet 

    def moveServo(self,id,position,rate=1000):
        packet = struct.pack("<BBBHH",id,7,
                            self.SERVO_MOVE_TIME_WRITE,
                            position,rate)
        self.sendPacket(packet)

    def readServoTarget(self,id):
        packet = struct.pack("<BBB",id,3,self.SERVO_MOVE_TIME_READ)
        rpacket = self.sendReceivePacket(packet,7)
        s = struct.unpack("<BBBBBHHB",rpacket)
        print(s)
        return s[5:7]

    def moveServoWait(self,id,position,rate=1000):
        packet = struct.pack("<BBBHH",id,7,
                            self.SERVO_MOVE_TIME_WAIT_WRITE,
                            position,rate)
        self.sendPacket(packet)

    def readServoTargetWait(self,id):
        packet = struct.pack("<BBB",id,3,self.SERVO_MOVE_TIME_WAIT_READ)
        rpacket = self.sendReceivePacket(packet,7)
        s = struct.unpack("<BBBBBHHB",rpacket)
        return s[5:7]

    def moveServoStart(self,id):
        packet = struct.pack("<BBB",id,3,self.SERVO_MOVE_START)
        rpacket = self.sendPacket(packet)

    def moveServoStop(self,id):
        packet = struct.pack("<BBB",id,3,self.SERVO_MOVE_STOP)
        rpacket = self.sendPacket(packet)

    def setID(self,id,newid):
        packet = struct.pack("<BBBB",id,4,
                            self.SERVO_ID_WRITE,newid)
        self.sendPacket(packet)

    def readID(self,id):
        packet = struct.pack("<BBB",id,3,self.SERVO_ID_READ)
        rpacket = self.sendReceivePacket(packet,4)
        s = struct.unpack("<BBBBBBB",rpacket)
        return s[5]

    def setAngleOffsetAdjust(self,id,angle):
        packet = struct.pack("<BBBb",id,4,
                            self.SERVO_ANGLE_OFFSET_ADJUST,angle)
        self.sendPacket(packet)

    def setAngleOffset(self,id,angle):
        packet = struct.pack("<BBBb",id,4,
                            self.SERVO_ANGLE_OFFSET_WRITE,angle)
        self.sendPacket(packet)

    def readAngleOffset(self,id):
        packet = struct.pack("<BBB",id,3,self.SERVO_ANGLE_OFFSET_READ)
        rpacket = self.sendReceivePacket(packet,4)
        s = struct.unpack("<BBBBBbB",rpacket)
        return s[5]

    def setAngleLimit(self,id,angleMin,angleMax):
        packet = struct.pack("<BBBHH",id,7,
                            self.SERVO_ANGLE_LIMIT_WRITE,angleMin,angleMax)
        self.sendPacket(packet)

    def readAngleLimit(self,id):
        packet = struct.pack("<BBB",id,3,self.SERVO_ANGLE_LIMIT_READ)
        rpacket = self.sendReceivePacket(packet,7)
        s = struct.unpack("<BBBBBHHB",rpacket)
        return s[5:7]

    def setVoltageLimit(self,id,voltageMin,voltageMax):
        packet = struct.pack("<BBBHH",id,7,self.SERVO_VIN_LIMIT_WRITE,
                            voltageMin,voltageMax)
        rpacket = self.sendPacket(packet)

    def readVoltageLimit(self,id):
        packet = struct.pack("<BBB",id,3,self.SERVO_VIN_LIMIT_READ)
        rpacket = self.sendReceivePacket(packet,7)
        s = struct.unpack("<BBBBBHHB",rpacket)
        return s[5:7]

    def setTemperatureLimit(self,id,temperatureMax):
        packet = struct.pack("<BBBB",id,4,self.SERVO_TEMP_MAX_LIMIT_WRITE,
                            temperatureMax)
        rpacket = self.sendPacket(packet)

    def readTemperatureLimit(self,id):
        packet = struct.pack("<BBB",id,3,self.SERVO_TEMP_MAX_LIMIT_READ)
        rpacket = self.sendReceivePacket(packet,4)
        s = struct.unpack("<BBBBBBB",rpacket)
        return s[5]

    def readTemperature(self,id):
        packet = struct.pack("<BBB",id,3,self.SERVO_TEMP_READ)
        rpacket = self.sendReceivePacket(packet,4)
        s = struct.unpack("<BBBBBBB",rpacket)
        return s[5]

    def readVoltage(self,id):
        packet = struct.pack("<BBB",id,3,self.SERVO_VIN_READ)
        rpacket = self.sendReceivePacket(packet,5)
        s = struct.unpack("<BBBBBHB",rpacket)
        return s[5]

    def readPosition(self,id):
        packet = struct.pack("<BBB",id,3,self.SERVO_POS_READ)
        rpacket = self.sendReceivePacket(packet,5)
        s = struct.unpack("<BBBBBhB",rpacket)
        return s[5]

    def motorOrServo(self,id,motorMode,MotorSpeed):
        packet = struct.pack("<BBBBBh",id,7,
                            self.SERVO_OR_MOTOR_MODE_WRITE,
                            motorMode,0,MotorSpeed)
        self.sendPacket(packet)

    def readMotorOrServo(self,id):
        packet = struct.pack("<BBB",id,3,self.SERVO_OR_MOTOR_MODE_READ)
        rpacket = self.sendReceivePacket(packet,7)
        s = struct.unpack("<BBBBBBBhB",rpacket)
        return [s[5],s[7]]

    def LoadUnload(self,id,mode):
        packet = struct.pack("<BBBB",id,4,
                            self.SERVO_LOAD_OR_UNLOAD_WRITE,mode)
        self.sendPacket(packet)

    def readLoadUnload(self,id):
        packet = struct.pack("<BBB",id,3,
                            self.SERVO_LOAD_OR_UNLOAD_READ)
        rpacket = self.sendReceivePacket(packet,4)
        s = struct.unpack("<BBBBBBB",rpacket)
        return s[5]

    def setLed(self,id,ledState):
        packet = struct.pack("<BBBB",id,4,
                            self.SERVO_LED_CTRL_WRITE,ledState)
        self.sendPacket(packet)

    def readLed(self,id):
        packet = struct.pack("<BBB",id,3,self.SERVO_LED_CTRL_READ)
        rpacket = self.sendReceivePacket(packet,4)
        s = struct.unpack("<BBBBBBB",rpacket)
        return s[5]

    def setLedError(self,id,ledError):
        packet = struct.pack("<BBBB",id,4,
                            self.SERVO_LED_ERROR_WRITE,ledError)
        self.sendPacket(packet)

    def readLedError(self,id):
        packet = struct.pack("<BBB",id,3,self.SERVO_LED_ERROR_READ)
        rpacket = self.sendReceivePacket(packet,4)
        s = struct.unpack("<BBBBBBB",rpacket)
        return s[5]

class LX16A_BUS_MODIFIED(LX16A_BUS):
    def moveServoBulk(self, ids, angles):
        for i in range(len(ids)):
            self.moveServo(ids[i], angles[i])

    def LoadUnloadBulk(self, ids, state):
        for id in ids:
            self.LoadUnload(id, state)
    
    def readPositionBulk(self, ids):
        out = {}
        for id in ids:
            out[id] = self.readPosition(id)

        return out


if __name__ == '__main__':
   controller = LX16A_MODIFIED()

   for id in range(1, 19):
      controller.LoadUnload(id, 1)

   while True:
      # set into flat position
      for id in [1, 4, 7, 10, 13, 16]:
         controller.moveServo(id, 500)

      for id in [2, 5, 8, 11, 14, 17]:
         controller.moveServo(id, 500)

      for id in [3, 6, 9, 12, 15, 18]:
         controller.moveServo(id, 200)
      #

      sleep(2)

      #prepare to stand
      for id in [2, 5, 8, 11, 14, 17]:
         controller.moveServo(id, 200)

      for id in [3, 6, 9, 12, 15, 18]:
         controller.moveServo(id, 800)
      #

      sleep(2)

      #stand
      for id in [2, 5, 8, 11, 14, 17]:
         controller.moveServo(id, 800)

      for id in [3, 6, 9, 12, 15, 18]:
         controller.moveServo(id, 200)

      sleep(5)