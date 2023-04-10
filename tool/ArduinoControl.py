from enum import Enum
import serial


class Command(Enum):
    ACC_ON = 1
    ACC_OFF = 2
    IGN_ON = 3
    IGN_OFF = 4
    OPT2_ON = 5
    OPT2_OFF = 6
    WD_ON = 7
    WD_OFF = 8


class Arduino:
    def __init__(self, port, baud_rate=9600):
        self.port = port
        self.baud_rate = baud_rate
        self.ser = serial.Serial(self.port, self.baud_rate)

    def send_command(self, command):
        print("call sendcommand")
        try:
            if not self.ser:
                print("Serial not connected.")
                return False
            print(f"command: {command.value}")
            self.ser.write((str(command.value) + "\n").encode())
            print(f"{command.name} command sent")
            response = self.ser.readline().strip()
            if str(command.value) + " executed" in response.decode():
                print(f"Response: {response.decode()}")
                return True
            if str(command.value) + " unexecuted" in response.decode():
                print(f"Response: {response.decode()}")
                return False

        except:
            return False

    def close(self):
        if self.ser:
            self.ser.close()


# arduino = Arduino(port="COM4")
# arduino.send_command(Command.ACC_ON)
# if __name__ == "__main__":
#     arduino = Arduino(port="COM4")

#     if arduino is not None:
#         print("Arduino connected.")
#         while True:
#             try:
#                 command = int(input("Enter a command (1-8): "))
#                 if command in range(1, 9):
#                     arduino.send_command(Command.ACC_ON)
#                     print(Command.ACC_ON)
#                 else:
#                     print("Invalid input.")
#             except ValueError:
#                 print("Invalid input. Please enter a number.")
#     else:
#         print("Failed to connect to Arduino.")
