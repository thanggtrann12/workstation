from enum import Enum
import serial
import time

E_OK = 0
E_NOK = 1


class Command(Enum):
    ACC = 1
    IGN = 2
    OPT2 = 3
    WD = 4


pin_mapping = {
    Command.ACC: 2,  # ACC_PIN
    Command.IGN: 3,  # IGN_PIN
    Command.OPT2: 8,  # WD_OFF_PIN
    Command.WD: 9   # OPT2_PIN
}

state_mapping = {
    E_OK: "E_OK",
    E_NOK: "E_NOT_OK"
}


class Arduino:
    def __init__(self, port, baud_rate=9600):
        self.port = port
        self.baud_rate = baud_rate
        self.ser = serial.Serial(self.port, self.baud_rate)
        time.sleep(1)  # make sure init state finish at arduino

    def send_command(self, command, state):
        try:
            if not self.ser:
                return E_NOK
            if state <= 1:
                self.ser.flush()
                self.ser.write(
                    (str(pin_mapping[command]) + str(state) + "\n").encode())
                response = self.ser.readline().strip().decode()
                if response is not None:
                    return E_OK if response == "0" else E_NOK
            else:
                return E_NOK
        except:
            return E_NOK

    def get_all_pin_state(self):
        self.ser.write(
            ("00\n").encode())
        response = self.ser.readline().strip().decode()
        return response

    def close(self):
        if self.ser:
            self.ser.close()
