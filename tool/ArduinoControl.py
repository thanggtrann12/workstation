from enum import Enum
import serial
import time


class Command(Enum):
    ACC = 1
    IGN = 2
    OPT2 = 3
    WD = 4


DEVICE_OFF = 1
DEVICE_ON = 0


class Arduino:
    def __init__(self, port, baud_rate=9600):
        print("Init arduino")
        self.port = port
        self.baud_rate = baud_rate
        self.ser = serial.Serial(self.port, self.baud_rate)
        time.sleep(1)  # make sure init state finish at arduino

    def send_command(self, command, state):
        try:
            if not self.ser:
                print("Serial not connected.")
                return None
            self.ser.flush()
            response = ""
            self.ser.write((str(command.value) + str(state) + "\n").encode())
            # print(f"{command.name} command sent " +
            #       (str(command.value) + str(state)))
            response = self.ser.readline().strip().decode()
            if response is not None:
                # print(f"{command.value}  :   {response}") uncomment if debuging
                return True

        except:
            return None

    def close(self):
        if self.ser:
            self.ser.close()


# if __name__ == "__main__":
#     arduino = Arduino(port="COM23")
#     time.sleep(1)
#     if arduino is not None:
#         print("Arduino connected.")
#         while True:
#             try:
#                 cmd = int(input("1-8: "))
#                 device, resp = arduino.send_command(Command.ACC, DEVICE_OFF)
#                 print(Command.ACC, "devie ->  ",
#                       device, "resp ->  ", resp)

#             except Exception as e:
#                 print(e)
#     else:
#         print("Failed to connect to Arduino.")
