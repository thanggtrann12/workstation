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
eventlet.monkey_patch()
stop_event = threading.Event()
# run this in cmd: NETSH advfirewall firewall add rule name="LCM development" dir=in action=allow enable=yes protocol=TCP localport=5000 remoteip="10.0.0.0/8" localip="10.0.0.0/8" description="LCM workstation" Profile=domain

# ssh workstation@10.185.81.196
# pass: lcm


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
    global is_power_turn_on, is_start_up_msg_recv
    if "SPM_SPMS_R_STARTUP_FINISHED transmission completed" in trace:
        is_start_up_msg_recv = True
        socketio.emit("status", "Start Up success")
        print("Start Up success")
    if "SPM_SPMS_R_SHUTDOWN_IN_PROGRESS transmission completed" in trace:
        socketio.emit("status", "Receive SPM_SPMS_R_SHUTDOWN_IN_PROGRES")
        print("Receive Up success")
    if is_power_turn_on:
        socketio.emit("message", trace+"\n", broadcast=True)


def update_voltage_and_current_to_server():
    """
    Update voltage_returned and current_returned to server
    :return: None
    """
    global socketio, is_power_turn_on, power_source_connection, logged_in_users

    while True:
        if socketio is not None:
            if logged_in_users:
                socketio.emit("list_user", logged_in_users)
        if power_source_connection == None:
            if socketio is not None:
                socketio.emit("update_power_data", data={"voltage_returned": 0,
                                                         "current_returned": 0})
            status = "Power source is not connect !!!"
        else:
            try:
                voltage_returned = str(
                    float(power_source_connection .GetVoltage().decode()))
                current_returned = str(
                    float(power_source_connection .GetCurrent().decode()))
                data = {"voltage_returned": voltage_returned,
                        "current_returned": current_returned}
                socketio.emit("update_power_data", data)
                socketio.emit("status", status)
            except:
                pass

        time.sleep(1)


def check_process_running(process_name):
    """
    Check if a process with the given name is running or not
    """
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.name() == process_name:
            return True
    return False


def handle_error_from_flash_gui():
    elapsed_time = 0
    while True:
        if check_process_running("FlashGUI.exe"):
            elapsed_time += 1
            print("waiting")
            if elapsed_time >= 120:
                socketio.emit("status", "Fashing timeout!!!")
                os.system("taskkill /f /im  FlashGUI.exe")
                break
            else:
                elapsed_time += 1
                socketio.emit("status", "Wating for flashing...")
                time.sleep(1)  # wait for 1 second
        else:
            print("done")
            elapsed_time = 0
            socketio.emit("status", "Ready")
            break


@ app.route('/session_id')
def get_session_id():
    return jsonify(session_id=session["emp_id"])


def upload_trace_to_ttfis(file_name):
    """This function uses to upload trace to the ttfis client

    Args:
        file_name (string): trace file name
    """
    socketio.emit("status", "Uploading trace...")
    time.sleep(1)
    if ttfisClient.LoadTRCFiles([trace_path+file_name]):
        socketio.emit("status", "Restarting ttfisClient...")
        print("Success")
        ttfisClient.Disconnect(ttfis_client_port)
        ttfisClient.Connect(ttfis_client_port)
        ttfisClient.Restart()
    else:
        print("failed")
        socketio.emit("status", "Upload trace failed")
        time.sleep(1)
    socketio.emit("status", "Ready")


def flash_ccs20_target(file_name):
    """flash ccs20 target

    Args:
        file_name (string): the dnl file name
    """
    global socketio
    # print("going to flash_ccs20_target")
    # socketio.emit("status", "Start FLashGui")
    # cmd = 'FlashGUI.exe /iQuad-Gen5-DebugAdapter C - FT7HJJJV,1000000,E,8,1 " /f{}/{} /au'.format(
    #     binary_path, file_name)
    # subprocess.Popen(cmd, stdout=subprocess.PIPE)
    # socketio.emit("status", "Flashing...")
    # handle_error_from_flash_gui()


def process_instruction_file(file_path):
    """
    Process instruction file
    Args:
        file_path (string): instruction file path
    Returns:
        lkup_table (dict): lkup table
    """
    cmd, extra_cmd = read_cmd_list(file_path)
    lkup_table = dict()
    lkup_table["root"] = extract_cmd(cmd)
    lkup_table["enum"] = extract_enum(extra_cmd)
    return lkup_table


@ socketio.on("lock_status")
def handle_lock_status(status):
    print("lock status", status)
    if status:
        socketio.emit("lock_status", True, broadcast=True)
    else:
        socketio.emit("lock_status", False, broadcast=True)


@ app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        _e_id = request.form["emp_id"]
        return check_login_users(_e_id.lower())
    else:
        error = ''
        return render_template('signin.html', error=error)


def check_login_users(user):
    global logged_in_users, admin, current
    error = ''
    if user in ALLOWED_USER:
        if len(logged_in_users) == 0:
            logged_in_users.append(user)
            print("admin user loggin:", user)
            session["emp_id"] = user
            return redirect(url_for('index'))
        elif user not in logged_in_users:
            logged_in_users.append(user)
            session["emp_id"] = user
            print("New user loggin:", logged_in_users)
            socketio.emit("list_user", logged_in_users)
            return redirect(url_for('index'))
        else:
            print("User is already logged in", session["emp_id"])
            return redirect(url_for('index'))
    else:
        error = "I'm sorry but you are not allowed"
        if user == "":
            return render_template('signin.html', error="")
        else:
            return render_template('signin.html', error=error)


@ app.route('/index')
def index():
    if request.method == 'GET':
        if 'Referer' in request.headers and request.headers['Referer'] + "index" == request.url:
            refresh_detected = True
            print(f"Refresh detected: {refresh_detected}")
            return render_template('index.html')
        else:
            refresh_detected = False
            print(f"No refresh: {refresh_detected}")
            return render_template('index.html')
    else:
        return render_template('index.html')


@ app.route('/logout')
def logout():
    global logged_in_users
    print(session["emp_id"])
    user_remove = str(session["emp_id"])
    logged_in_users.remove(user_remove)
    return redirect(url_for('login'))


@ app.route("/GetCommandSet/", methods=["GET"])
def get_command_set():
    global trace_path
    if (os.listdir(trace_path)) is None:
        print("No trace file, using default file name")
        trace_file_name = DEFAULT_TRACE_FILE_NAME
    else:
        trace_file_name = os.listdir(trace_path)[0]
    traceFilePath = trace_path + trace_file_name
    return process_instruction_file(traceFilePath)


@ app.route('/upload', methods=['POST'])
def handling_file_upload_from_server():
    global trace_file_name
    try:
        file_dnl = request.files['file-dnl']
        filename_dnl = file_dnl.filename
        if ALLOWED_FILE[0] in filename_dnl:
            file_dnl.save(os.path.join(binary_path, filename_dnl))
            flash_ccs20_target(filename_dnl)
        else:
            print("File not found: {}".format(filename_dnl))
    except:
        pass
    try:
        file_trc = request.files['file-trc']
        filename_trc = file_trc.filename
        if ALLOWED_FILE[1] in filename_trc:
            file_trc.save(os.path.join(trace_path, filename_trc))

            trace_file_name = filename_trc
            print(trace_file_name)
            upload_trace_to_ttfis(trace_file_name)
            socketio.emit("status", "Ready")
        else:
            print("File not found: {}".format(filename_trc))
    except:
        pass
    return ""


@ socketio.on('message')
def message_(message):
    socketio.emit("message", data=message, statusbroadcast=True)


@ socketio.on('chat_box')
def forward_message(message):
    socketio.emit("chat_box", message, statusbroadcast=True)


@ socketio.on("get_all_data")
def get_all_data():
    ret = arduino_connection.get_all_pin_state()
    socketio.emit("sync_data_from_arduino", ret)


@ socketio.on('request_to_arduino')
def request_to_arduino(data):
    time.sleep(.1)
    if arduino_connection:
        ret = ""
        if data['pin'] == 'acc':
            ret = arduino_connection.send_command(
                Command.ACC, int(data['state']))
        elif data['pin'] == 'ign':
            ret = arduino_connection.send_command(
                Command.IGN, int(data['state']))
        elif data['pin'] == 'wd':
            ret = arduino_connection.send_command(
                Command.WD, int(data['state']))
        elif data['pin'] == 'opt2':
            ret = arduino_connection.send_command(
                Command.OPT2, int(data['state']))
        print("pin  ", data['pin'], "ret  ",
              ret, "state  ", int(data['state']))
        socketio.emit("return_from_arduino", data={
            "pin": data['pin'], "ret": ret}, broadcast=True)


@ socketio.on("power_state")
def set_power_state(state):
    global power_source_connection, is_power_turn_on
    if power_source_connection != None:
        if state:
            status = "Set ToellnerDriver ON"
            socketio.emit("update_power_data", json.dumps(normal_voltage))
        else:
            print('set pwer off')
            status = "Set ToellnerDriver OFF"
            socketio.emit("update_power_data", json.dumps(shutdown_voltage))
        is_power_turn_on = state
    else:
        status = "ToellnerDriver is not connect... Cannot turn on or off"
        print(status)
        socketio.emit("status", status)
        time.sleep(1)


@ socketio.on("lock")
def lock(isLock):
    socketio.emit("lock", isLock)


@ socketio.on("force_ul")
def force_unlock():
    socketio.emit("force_ul")


@ socketio.on("sccCommand")
def sccCommand(cmd):
    ttfisClient.Cmd(cmd)


@ socketio.on('setVoltage')
def handling_voltage(voltage_value):
    print(voltage_value)
    global power_source_connection, is_power_turn_on
    if power_source_connection != None:
        if (int(voltage_value) > voltage_max) or (int(voltage_value) <= voltage_min):
            status = "The voltage must in range {}V - {}V".format(
                voltage_min, voltage_max)
        else:
            power_source_connection.SetVoltage(voltage_value)
            status = "Set voltage successfully"
    else:
        status = "Power source not connected"
    socketio.emit("status", status)


@ socketio.on("shortToGround")
def shortToGround(periDevices):
    print("shortToGround ", periDevices)


@ socketio.on("shortToBat")
def shortToBat(periDevices):
    print("shortToBat ", periDevices)


@ socketio.on("shut_down")
def shut_down_target():
    unplug_acc_ign()


@ socketio.on("stand_by")
def stand_by_target():
    unplug_acc_ign()


@socketio.on("wake_up")
def wake_up_target():
    plug_acc_ign()


def unplug_acc_ign():
    request_to_arduino({"pin": "acc", "state": E_NOK})
    request_to_arduino({"pin": "ign", "state": E_NOK})


def plug_acc_ign():
    request_to_arduino({"pin": "acc", "state": E_OK})
    request_to_arduino({"pin": "ign", "state": E_OK})


if __name__ == '__main__':
    # ttfisClient = TTFisClient()
    # ttfisClient.registerUpdateTraceCallback(update_scc_trace)
    # ttfisClient.Connect(ttfis_client_port)
    # power_source_connection = ToellnerDriver(
    #     powersource_port, powersource_channel)
    # if power_source_connection:
    #     power_source_connection.SetVoltage(12)
    if arduino_port:
        arduino_connection = Arduino(arduino_port)
    # print("update_voltage_and_current_to_server")
    Thread(target=update_voltage_and_current_to_server).start()
    print("start_socketio")
    socketio.run(app, host='0.0.0.0', port=5000)

    # power_source_connection .__del__()
    arduino_connection.close()
    # ttfisClient.Quit()
