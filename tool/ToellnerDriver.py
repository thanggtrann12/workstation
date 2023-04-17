
from serial import Serial
from time import sleep
from threading import Lock

SET_VOLTAGE_COMMAND_TEMPLATE = "INST OUT%d;:VOLT "
GET_VOLTAGE_COMMAND_TEMPLATE = "INST OUT%d;:MEAS:VOLT?\n"
GET_CURRENT_COMMAND_TEMPLATE = "INST OUT%d;:MEAS:CURR?\n"


class ToellnerDriver:
    print("init ToellnerDriver ")
    _connection = None
    _setVoltageCommand = ""
    _getVoltageCommand = b""
    _getCurrentCommand = b""
    _lock = Lock()

    def __init__(self, port_, channel_):
        self._connection = Serial(port_, baudrate=9600, timeout=1)
        sleep(1)
        self._setVoltageCommand = SET_VOLTAGE_COMMAND_TEMPLATE % (channel_)
        self._getVoltageCommand = (
            GET_VOLTAGE_COMMAND_TEMPLATE % (channel_)).encode()
        self._getCurrentCommand = (
            GET_CURRENT_COMMAND_TEMPLATE % (channel_)).encode()

    def __del__(self):
        if (None != self._connection):
            self._connection.close()

    def SetVoltage(self, value_):
        with self._lock:
            self._connection.write(
                (self._setVoltageCommand + str(value_) + "\n").encode())

    def GetVoltage(self):
        with self._lock:
            self._connection.write(self._getVoltageCommand)
            voltage = self._connection.readline()
        return voltage

    def GetCurrent(self):
        with self._lock:
            self._connection.write(self._getCurrentCommand)
            current = self._connection.readline()
        return current
