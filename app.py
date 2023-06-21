from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_socketio import SocketIO
from threading import Thread
import threading
import time
import eventlet
import subprocess
import os
from InstructionSetProcess import *
from tool.ArduinoControl import Arduino, Command, E_OK, E_NOK
from tool.TTFisClient import TTFisClient
from tool.ToellnerDriver import ToellnerDriver
from config import *
import psutil
import random
from werkzeug.utils import secure_filename
eventlet.monkey_patch()
stop_event = threading.Event()

# run this in cmd: NETSH advfirewall firewall add rule name="LCM development" dir=in action=allow enable=yes protocol=TCP localport=5000 remoteip="10.0.0.0/8" localip="10.0.0.0/8" description="LCM workstation" Profile=domain

# ssh workstation@10.185.81.196
# pass: lcm

status = ""
start_time = time.time()
logged_in_users = []
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = binary_path
app.secret_key = SECRET_KEY
socketio = SocketIO(app)
admin = ""
current = ""


def update_scc_trace(trace):
    """
    Update scc trace from the ttfis client into remote view
    Args:
        trace (string): trace from ttfis
    """
    socketio.emit("ttfis_data", trace+"\n", broadcast=True)


@socketio.on("status")
def send_status(status):
    socketio.emit("status", status)


@socketio.on("submit_ttfis_cmd")
def submit_ttfis_cmd(ttfis_cmd):
    ttfis_command = str(ttfis_cmd).replace(",", " ")
    # global ttfisClient
    # ttfisClient.Cmd(ttfis_command)


@socketio.on("get_sync_data")
def get_sync_data():
    global arduino_connection
    if arduino_connection is not None:
        ret = arduino_connection.get_all_pin_state()
        socketio.emit("set_sync_data", ret)


def update_voltage_and_current_to_server():
    """
    Update voltage_returned and current_returned to server
    :return: None
    """
    global socketio,  ToellnerDriver_connection, logged_in_users
    print("assigned call back")
    while True:
        if socketio is not None:
            if logged_in_users:
                socketio.emit("list_user", logged_in_users)
        get_data_from_toellner()
        time.sleep(.1)


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


def get_data_from_toellner():
    global ToellnerDriver_connection, status
    if ToellnerDriver_connection is not None:
        try:
            voltage_returned = float(ToellnerDriver_connection.get_voltage())
            current_returned = float(ToellnerDriver_connection.get_current())
            data = {"voltage": voltage_returned,
                    "current": current_returned}
            # socketio.emit("current_power_state",
            #               ToellnerDriver_connection.get_current_power_state())
            socketio.emit("update_data_to_client", data=data)
        except Exception as e:
            print(e)
            pass
    else:
        status = "ToellnerDriver is not CONNECTED"
        socketio.emit("status", status)
    # print(status)


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


if __name__ == '__main__':
    # ttfisClient = TTFisClient()
    # ttfisClient.registerUpdateTraceCallback(update_scc_trace)
    # ttfisClient.Connect(ttfis_client_port)
    ToellnerDriver_connection = ToellnerDriver(
        ToellnerDriver_connection_port, ToellnerDriver_connection_channel)
    # if arduino_port:
    # arduino_connection = Arduino(arduino_port)
    # print("update_voltage_and_current_to_server")
    Thread(target=update_voltage_and_current_to_server).start()
    # Thread(target=callback_power_state).start()
    # print("start_socketio")
    status = "Ready"
    print("socket init")
    socketio.run(app, host='0.0.0.0', port=5000)

    ToellnerDriver_connection .__del__()
    # arduino_connection.close()
    # ttfisClient.Quit()
