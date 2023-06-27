from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_socketio import SocketIO
from threading import Thread
import threading
import time
import eventlet
import sys
import os
from InstructionSetProcess import *
from tool.ArduinoControl import Arduino
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
ADMIN = None


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


@socketio.on("request_sync_data")
def request_sync_data():
    global arduino_connection, data, ToellnerDriver_connection
    response = payload = None
    if arduino_connection is not None:
        response = arduino_connection.send_command('ALL', "")
    if ToellnerDriver_connection is not None:
        payload = {
            "arduino": response if response is not None else "1111", "power_state": True}
    socketio.emit("sync_data", payload)


@socketio.on("update_data_to_toellner")
def update_data_to_toellner(data):
    global ToellnerDriver_connection, status
    voltage = data["voltage"]
    if ToellnerDriver_connection is not None:
        if voltage_min > voltage:
            status = "Voltage must greater than " + str(voltage_min)
        elif voltage_max < voltage:
            status = "Voltage must less than " + str(voltage_max)
        else:
            ToellnerDriver_connection.set_voltage(voltage)
            status = "Updated"
    else:
        status = "ToellnerDriver is not CONNECTED"
    socketio.emit("status", status)


@app.route('/get_data', methods=['GET'])
def get_data():
    global ToellnerDriver_connection, status, isStandBy, data
    if ToellnerDriver_connection is not None:
        try:
            voltage_returned = float(ToellnerDriver_connection.get_voltage())
            current_returned = float(ToellnerDriver_connection.get_current())
            payload = {"voltage": voltage_returned,
                       "current": current_returned}
            if voltage_returned > 0 and current_returned == 0:
                isStandBy = True
                data += "\n\r[STANDBY]"
            else:
                isStandBy = False
            return jsonify(payload), 200
        except:
            return jsonify({"error": "An error occurred"}), 500
    else:
        status = "ToellnerDriver is not CONNECTED"
        socketio.emit("status", status)
        return jsonify({"error": status}), 500


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
    else:
        socketio.emit("status", "ToellnerDriver is not CONNECTED")


@app.route("/power", methods=['POST'])
def power():
    data = request.get_json()
    state = data.get('state')
    global ToellnerDriver_connection
    if state is None:
        return jsonify({"error": "Missing 'state' parameter"}), 400

    if state:
        if ToellnerDriver_connection is not None:
            ToellnerDriver_connection.set_voltage(12)
            return jsonify({"message": "Power is ON"}), 200
        return jsonify({"message": "Power is OFF"}), 200
    else:
        if ToellnerDriver_connection is not None:
            ToellnerDriver_connection.set_voltage(0)
        return jsonify({"message": "Power is OFF"}), 200


@app.route("/turn/<button_name>/<int:state>", methods=['GET'])
def request_to_arduino(button_name, state):
    global arduino_connection
    if arduino_connection:
        response = arduino_connection.send_command(button_name, state)
        return jsonify({"message": response}), 200
    else:
        return jsonify({"message": "Arduino not CONNECTED"}), 200


@ app.route('/', methods=['GET', 'POST'])
def login():
    global logged_in_users, ADMIN, current
    user_login = ""
    if request.method == 'POST':
        user_login = request.form["emp_id"]
        if user_login in ALLOWED_USER and ADMIN is None:
            logged_in_users.append(user_login)
            session["emp_id"] = user_login
            ADMIN = user_login
            print("admin: ", ADMIN)
            return redirect(url_for('index'))
        elif user_login not in logged_in_users:
            logged_in_users.append(user_login)
            session["emp_id"] = user_login
            print("New user loggin:", logged_in_users)
            return redirect(url_for('index'))
        else:
            print("User is already logged in", user_login)
            return redirect(url_for('index'))
    else:
        if user_login == "":
            return render_template('signin.html', error="")
        error = "I'm sorry but you are not allowed"
        return render_template('signin.html', error=error)


@socketio.on("lock")
def lock(locked):
    socketio.emit("lock", locked)


@ app.route('/index')
def index():
    return render_template('index.html')


@ app.route('/logout')
def logout():
    global logged_in_users
    user_remove = str(session["emp_id"])
    if user_remove is not None:
        logged_in_users.remove(user_remove)
    print("remove user: ", user_remove)
    return render_template('signin.html', error="")


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


def plug_accign():
    arduino_connection.send_command("WAKEUP", "")


def unplug_accign():
    arduino_connection.send_command("STANDBY", "")


def StandBy():
    return isStandBy


TIMEOUT_TEST_SPEC = 10*60


@app.route('/start-test/<test_name>/<int:time>', methods=['GET'])
def start_test(test_name, time):
    global subfix
    if test_name == "standby":
        subfix = "standby"
        threading.Thread(target=test_flow.execute_test(time, unplug_accign, TIMEOUT_TEST_SPEC,
                                                       StandBy, plug_accign, plug_accign, log)).start()

    if test_name == "shutdown":
        subfix = "shutdown"
        threading.Thread(test_flow.execute_test(time, unplug_accign, TIMEOUT_TEST_SPEC,
                                                StandBy, plug_accign, plug_accign, log)).start()

    return jsonify({'message': f'Test "{test_name}" started'})


@app.route('/wakeup', methods=['POST'])
def wake_up():
    print("wake up")
    socketio.emit("submit_ttfis_cmd", "SUPERVISOR_GET_ALL_DATA")
    global arduino_connection
    if arduino_connection:
        arduino_connection.send_command("WAKEUP", "")
    return "wakeup"


@app.route('/admin', methods=['GET'])
def get_admin():
    global ADMIN
    return jsonify({"admin": ADMIN}), 200


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


if __name__ == '__main__':
    test_flow = TestFlow()
    # ttfisClient = TTFisClient()
    # ttfisClient.registerUpdateTraceCallback(update_scc_trace)
    # ttfisClient.Connect(ttfis_client_port)
    # ToellnerDriver_connection = ToellnerDriver(
    #     ToellnerDriver_connection_port, ToellnerDriver_connection_channel)
    # if arduino_port:
    #     arduino_connection = Arduino(arduino_port)
    time.sleep(1)
    print("update_voltage_and_current_to_server")
    print("start_socketio")
    socketio.run(app, host='0.0.0.0', port=5000)
    ToellnerDriver_connection .__del__()
    # arduino_connection.close()
    # ttfisClient.Quit()
