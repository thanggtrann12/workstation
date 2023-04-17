from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_socketio import SocketIO
from threading import Thread
import time
import eventlet
import subprocess
import os
from InstructionSetProcess import *
from tool.ArduinoControl import Arduino, Command, DEVICE_OFF, DEVICE_ON
from tool.TTFisClient import TTFisClient
from tool.ToellnerDriver import ToellnerDriver
from config import *
import psutil


start_time = time.time()
logged_in_users = []
eventlet.monkey_patch()
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = binary_path
app.secret_key = 'your_secret_key'
socketio = SocketIO(app)
admin = ""
current = ""


def update_scc_trace(trace):
    """
    Update scc trace from the ttfis client into remote view
    Args:
        trace (string): trace from ttfis
    """
    socketio.emit("message", trace, broadcast=True)


def update_voltage_and_current_to_server() -> None:
    """
    Update voltage_returned and current_returned to server
    :return: None
    """
    global socketio, is_power_turn_on, power_source_connection, logged_in_users, current
    data = None
    while True:
        if logged_in_users:
            socketio.emit("list_user", logged_in_users)
        if power_source_connection == None:
            is_power_turn_on = False
            status = "Power source is not connect !!!"
        else:
            voltage_returned = str(
                float(power_source_connection .GetVoltage().decode()))
            current_returned = str(
                float(power_source_connection .GetCurrent().decode()))

            data = {"voltage_returned": voltage_returned,
                    "current_returned": current_returned}
            status = "Ready"
            update_power_source_data(data, is_power_turn_on)
            socketio.emit("status", status)
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
    while True:
        if check_process_running("FlashGUI.exe"):
            elapsed_time = time.time() - start_time
            print("waiting")
            if elapsed_time >= 120:
                socketio.emit("status", "Fashing timeout!!!")
                os.system("taskkill /f /im  FlashGUI.exe")
                break
            else:
                socketio.emit("status", "Wating for flashing...")
                time.sleep(1)  # wait for 1 second
        else:
            socketio.emit("status", "Ready")
            break


@app.route('/session_id')
def get_session_id():
    return jsonify(session_id=session["emp_id"])


def upload_trace_to_ttfis(file_name):
    """This function uses to upload trace to the ttfis client

    Args:
        file_name (string): trace file name
    """
    socketio.emit("status", "Uploading trace...")
    if ttfisClient.LoadTRCFiles([trace_path+file_name]):
        socketio.emit("status", "Restarting ttfisClient...")
        ttfisClient.Restart()
    else:
        socketio.emit("status", "Upload trace failed")
        time.sleep(1)
    socketio.emit("status", "Ready")


def handling_flash_ccs(time):
    while time > 0:
        print("haha")


def flash_ccs20_target(file_name):
    """flash ccs20 target

    Args:
        file_name (string): the dnl file name
    """
    global socketio
    print("going to flash_ccs20_target")
    socketio.emit("status", "Start FLashGui")
    cmd = 'FlashGUI.exe /iQuad-Gen5-DebugAdapter C - FT7HJJJV,1000000,E,8,1 " /f{}/{} /au'.format(
        binary_path, file_name)
    subprocess.Popen(cmd, stdout=subprocess.PIPE)
    socketio.emit("status", "Flashing...")
    handle_error_from_flash_gui()


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


@socketio.on("lock_status")
def handle_lock_status(status):
    print("lock status", status)
    if status:
        # If the first user clicks the lock button, notify all other users
        socketio.emit("lock_status", True, broadcast=True)
    else:
        # If the first user unlocks the screen, notify all other users
        socketio.emit("lock_status", False, broadcast=True)


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        _e_id = request.form["emp_id"]
        return check_login_users(_e_id)
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


@app.route('/index')
def index():
    return render_template('index.html')


@ app.route('/logout')
def logout():
    global logged_in_users
    logged_in_users.remove(session["emp_id"])
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

            upload_trace_to_ttfis(filename_trc)
        else:
            print("File not found: {}".format(filename_trc))
    except:
        pass
    return ""


@ socketio.on('is_power_turn_on')
def sourceStt(status):
    socketio.emit("is_power_turn_on", status, broadcast=True)


@ socketio.on('message')
def message_(message):
    socketio.emit("message", data=message, statusbroadcast=True)


def sync_data_from_arduino(pin, state, label):

    print("Set {} result {}".format(label, state))
    socketio.emit("return_from_arduino", data={
                  "pin": pin, "state": True if state else False, "label": label}, broadcast=True)


@ socketio.on('request_to_arduino')
def handle_request(data):
    pin_name = data['pin']
    state = data['state']
    label = data['label']
    print(data)
    time.sleep(.1)
    if arduino_connection:
        if pin_name == 'acc_button':
            arduino_connection.send_command(
                Command.ACC, DEVICE_ON if state else DEVICE_OFF)
        elif pin_name == 'ign_button':
            arduino_connection.send_command(
                Command.IGN, DEVICE_ON if state else DEVICE_OFF)
        elif pin_name == 'wd_off_button':
            arduino_connection.send_command(
                Command.WD, DEVICE_ON if state else DEVICE_OFF)
        elif pin_name == 'opt2_button':
            arduino_connection.send_command(
                Command.OPT2, DEVICE_ON if state else DEVICE_OFF)
        sync_data_from_arduino(pin_name, state, label)


def update_power_source_data(data, state):
    socketio.emit("power_source_data", data)
    socketio.emit("is_power_turn_on", state)


@ socketio.on("power_state")
def set_power_state(state):
    print("power_state", state)
    global power_source_connection, is_power_turn_on
    if power_source_connection != None:
        if state:
            is_power_turn_on = True
            power_source_connection.SetVoltage(12)
            update_power_source_data(normal_voltage, is_power_turn_on)
        else:
            print('set pwer off')
            is_power_turn_on = False
            power_source_connection.SetVoltage(0)
            update_power_source_data(shutdown_voltage, is_power_turn_on)
    else:
        status = "Power souce is not connect... It cannot turn on or off"
        socketio.emit("status", status)
        time.sleep(1)

@socketio.on("lock")
def lock(isLock):
  socketio.emit("lock", isLock)

@ socketio.on("sccCommand")
def sccCommand(cmd):
    ttfisClient.Cmd(cmd)


@ socketio.on('setvoltagValue')
def handling_voltage(voltage_value):
    global power_source_connection, is_power_turn_on
    if power_source_connection != None:
        if (int(voltage_value) > voltage_max) or (int(voltage_value) <= voltage_min):
            status = "The voltage_returned value must be in range {}-{}V".format(
                voltage_min, voltage_max)
        else:
            power_source_connection.SetVoltage(voltage_value)
            status = "Set voltage_returned successfully"
    else:
        status = "Power source not connected"
    socketio.emit("status", status)


if __name__ == '__main__':
    # ttfisClient = TTFisClient()
    # ttfisClient.registerUpdateTraceCallback(update_scc_trace)
    # ttfisClient.Connect(ttfis_client_port)
    power_source_connection = ToellnerDriver(
        powersource_port, powersource_channel)
    # if power_source_connection:
    #     power_source_connection.SetVoltage(0)
    # if arduino_port:
    #     arduino_connection = Arduino(arduino_port)
    Thread(target=update_voltage_and_current_to_server, args=()).start()
    print("start")
    socketio.run(app, host='0.0.0.0', port=5000)

    power_source_connection .__del__()
    arduino_connection.close()
    # ttfisClient.Quit()
