from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_socketio import SocketIO
from threading import Thread
import threading
import time
import eventlet
import sys
import os
from InstructionSetProcess import *
from tool.ArduinoControl import Arduino, Command, E_OK, E_NOK
from tool.TTFisClient import TTFisClient
from tool.ToellnerDriver import ToellnerDriver
from tool.TestSpec import TestFlow
from config import *
from werkzeug.utils import secure_filename
eventlet.monkey_patch()
# run this in cmd: NETSH advfirewall firewall add rule name="LCM development" dir=in action=allow enable=yes protocol=TCP localport=5000 remoteip="10.0.0.0/8" localip="10.0.0.0/8" description="LCM workstation" Profile=domain

# ssh workstation@10.185.81.196
# pass: lcm

status = ""
logged_in_users = []
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = binary_path
app.secret_key = SECRET_KEY
socketio = SocketIO(app)
admin = ""
current = ""
isStateRun = True
isStandBy = False
data = ""
subfix = ""


def update_scc_trace(trace):
    global isStandBy, isStateRun, data
    """
    Update scc trace from the ttfis client into remote view
    Args:
        trace (string): trace from ttfis
    """
    if "Current state after transition [ST_Supervisor_States_Run]" in trace:
        isStateRun = True
        socketio.emit("status", "State: ST_Supervisor_States_Run")
    if "Current state after transition " in trace:
        data_within_brackets = trace[trace.rfind('[')+1:trace.rfind(']')]
        # print(data_within_brackets)
        socketio.emit("status", "State: "+data_within_brackets)
    data += "\r\n"+trace
    socketio.emit("ttfis_data", trace+"\n", broadcast=True)


@socketio.on("status")
def send_status(status):
    socketio.emit("status", status)


@socketio.on("submit_ttfis_cmd")
def submit_ttfis_cmd(ttfis_cmd):
    print("cmd")
    ttfis_command = str(ttfis_cmd).replace(",", " ")
    global ttfisClient
    ttfisClient.Cmd(ttfis_command)


@socketio.on("get_sync_data")
def get_sync_data():
    global arduino_connection, data
    if arduino_connection is not None:
        ret = arduino_connection.get_all_pin_state()
        socketio.emit("set_sync_data", {"arduino": ret, "trace": data})


def update_voltage_and_current_to_server():
    """
    Update voltage_returned and current_returned to server
    :return: None
    """
    global socketio,  ToellnerDriver_connection, logged_in_users
    # while True:
    # if socketio is not None:
    #     if logged_in_users:
    #         socketio.emit("list_user", logged_in_users)
    get_data_from_toellner()


@socketio.on("update_data_to_toellner")
def update_data_to_toellner(data):
    global ToellnerDriver_connection, status
    voltage = data["voltage"]
    if ToellnerDriver_connection is not None:
        ToellnerDriver_connection.set_voltage(voltage)
        status = "Updated"
    else:
        status = "ToellnerDriver is not CONNECTED"
    socketio.emit("status", status)


def get_data_from_toellner():
    global ToellnerDriver_connection, status, isStandBy, socketio, data
    while True:
        time.sleep(1)
        if ToellnerDriver_connection is not None:
            try:
                voltage_returned = float(
                    ToellnerDriver_connection.get_voltage())
                current_returned = float(
                    ToellnerDriver_connection.get_current())
                paload = {"voltage": voltage_returned,
                          "current": current_returned}
                if voltage_returned > 0 and current_returned == 0:
                    isStandBy = True
                    data += "\n\r[STANDBY]"
                else:
                    isStandBy = False
                if socketio is not None:
                    socketio.emit("update_data_to_client", data=paload)
            except:
                pass
        else:
            if socketio is not None:
                status = "ToellnerDriver is not CONNECTED"
                socketio.emit("status", status)
    # print(status)


@socketio.on('set_power_to_on')
@socketio.on('set_power_to_off')
def set_power_to_on():
    event_name = request.event['message']
    global ToellnerDriver_connection
    if ToellnerDriver_connection is not None:
        if event_name == "set_power_to_on":
            ToellnerDriver_connection.set_voltage(12)
        if event_name == "set_power_to_off":
            ToellnerDriver_connection.set_voltage(0)

    # Handle the event logic for turning power on or off


@socketio.on("remove_accign")
def remove_accign():
    print("remove_accign")
    socketio.emit("submit_ttfis_cmd", "SUPERVISOR_GET_ALL_DATA")
    global data, isStateRun
    isStateRun = False
    data += '\n [UNPLUG ACC + IGN] \n'
    arduino_connection.send_command(Command.ACC, E_NOK)
    arduino_connection.send_command(Command.IGN, E_NOK)


@socketio.on("reconnect_accign")
def reconnect_accign():
    print("reconnect_accign")
    global data
    data += '\n [PLUG ACC + IGN] \n'
    arduino_connection.send_command(Command.ACC, E_OK)
    socketio.emit("response_from_arduino", data={
                  "button": "acc", "response": True})
    arduino_connection.send_command(Command.IGN, E_OK)
    socketio.emit("response_from_arduino", data={
                  "button": "ign", "response": True})


@socketio.on("request_to_arduino")
def request_to_arduino(payload):
    global arduino_connection
    button_name = payload["button"]
    button_state = E_OK if payload["state"] == True else E_NOK
    response = E_NOK
    if button_name == "acc_button":
        response = arduino_connection.send_command(Command.ACC, button_state)
    if button_name == "ign_button":
        response = arduino_connection.send_command(Command.IGN, button_state)
    if button_name == "wd_button":
        response = arduino_connection.send_command(Command.WD, button_state)
    if button_name == "opt2_button":
        response = arduino_connection.send_command(Command.OPT2, button_state)

    socketio.emit("response_from_arduino", data={
                  "button": button_name.split('_')[0], "response": response})


@app.route("/")
def index():
    return render_template("index.html")


@app.route('/result', methods=['POST'])
def upload_file():
    file = request.files['file']
    if file:
        filename = secure_filename(file.filename)
        save_path = os.path.join(
            app.root_path, 'static', 'uploads/test/', filename)
        file.save(save_path)
        return 'File uploaded successfully'
    else:
        return 'No file uploaded'


@ app.route("/getTTFisCmd/", methods=["GET"])
def get_command_set():
    global trace_path
    if (os.listdir(trace_path)) is None:
        print("No trace file, using default file name")
        trace_file_name = DEFAULT_TRACE_FILE_NAME
    else:
        trace_file_name = os.listdir(trace_path)[0]
    traceFilePath = trace_path + trace_file_name
    return process_instruction_file(traceFilePath)


def StandBy():
    return isStandBy


TIMEOUT_TEST_SPEC = 10*60


@app.route('/start-test/<test_name>/<int:time>', methods=['GET'])
def start_test(test_name, time):
    global subfix
    if test_name == "standby":
        subfix = "standby"
        threading.Thread(target=test_flow.execute_test(time, remove_accign, TIMEOUT_TEST_SPEC,
                                                       StandBy, reconnect_accign, reconnect_accign, log)).start()

    if test_name == "shutdown":
        subfix = "shutdown"
        threading.Thread(test_flow.execute_test(time, remove_accign, TIMEOUT_TEST_SPEC,
                                                StandBy, reconnect_accign, reconnect_accign, log)).start()

    return jsonify({'message': f'Test "{test_name}" started'})


@app.route("/wakeup", methods=['GET'])
def wake_up():
    print("wake up")
    reconnect_accign()
    return "wakeup"


def log(time_, prefix):
    global data, subfix
    time.sleep(3)
    socketio.emit("submit_ttfis_cmd", "SUPERVISOR_GET_ALL_DATA")
    file_path = os.path.join(
        app.root_path, 'static', 'uploads/test/', f"test_{subfix}_{time_}_{prefix}.pro")
    data += "\n" + prefix
    while os.path.exists(file_path):
        time_ += 1
        file_path = os.path.join(
            app.root_path, 'static', 'uploads/test/', f"test_{subfix}_{time_}_{prefix}.pro")

    with open(file_path, 'w', encoding='utf-8', errors='ignore') as file:
        file.write(data)

    data = ""
    print("Data successfully written to the file.")


# Existing code...

if __name__ == '__main__':
    test_flow = TestFlow()
    ttfisClient = TTFisClient()
    ttfisClient.registerUpdateTraceCallback(update_scc_trace)
    ttfisClient.Connect(ttfis_client_port)
    ToellnerDriver_connection = ToellnerDriver(
        ToellnerDriver_connection_port, ToellnerDriver_connection_channel)
    if arduino_port:
        arduino_connection = Arduino(arduino_port)
    print("update_voltage_and_current_to_server")
    Thread(target=update_voltage_and_current_to_server).start()
    print("start_socketio")
    socketio.run(app, host='0.0.0.0', port=5000)
    ToellnerDriver_connection .__del__()
    arduino_connection.close()
    ttfisClient.Quit()
