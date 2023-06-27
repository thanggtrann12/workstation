import serial
import time


pin_mapping = {
    'acc_button': 0,
    'ign_button': 0,
    'opt2_button': 0,
    'wd_button': 0
}


class Arduino:
    def __init__(self, port, baud_rate=9600):
        self.port = port
        self.baud_rate = baud_rate
        self.ser = None
        self.connect()

    def connect(self):
        try:
            self.ser = serial.Serial(self.port, self.baud_rate)
            # make sure initialization state finishes on the Arduino
        except serial.SerialException:
            print("Failed to connect to the Arduino.")

    def send_command(self, pin_name, state):
        if not self.ser:
            return None

        try:
            payload = ""
            self.ser.flush()
            if pin_name == "ALL":
                self.ser.write(f"ALL\n".encode())
            elif pin_name == "WAKEUP":
                self.ser.write(f"WAKEUP\n".encode())
            elif pin_name == "STANDBY":
                self.ser.write(f"STANDBY\n".encode())
            else:
                pin_mapping[pin_name] = state
                for _, val in pin_mapping.items():
                    payload += str(val)
                self.ser.write(f"{payload}\n".encode())
            response = self.ser.readline().strip().decode()
            if response is not None:
                return response
        except serial.SerialException:
            print("Failed to send command to the Arduino.")
            return None

    def close(self):
        if self.ser:
            self.ser.close()
            self.ser = None


# if __name__ == "__main__":
#     arduino = Arduino(port="COM23")
#     time.sleep(1)
#     if arduino is not None:
#         print("Arduino connected.")
#         while True:
#             try:
#                 cmd = (input("pin:  "))
#                 state = int(input("state: "))
#                 resp = arduino.send_command(cmd, state)
#                 print("COMMAND: ", cmd, "resp ->  ",
#                       resp)
#             except Exception as e:
#                 print(e)
#     else:
#         print("Failed to connect to Arduino.")
