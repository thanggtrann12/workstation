from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, emit
from threading import Thread
import time
import eventlet
import logging
import subprocess
import os
from InstructionSetProcess import *
from tool.ArduinoControl import Arduino, Command, DEVICE_OFF, DEVICE_ON
from tool.TTFisClient import TTFisClient
from tool.ToellnerDriver import ToellnerDriver
from config import *
ALLOWED_FILE = ["dnl", "trc"]

user_name = ""
logined = False
logging.basicConfig(filename='log.pro', level=logging.DEBUG,
                    format=('%(filename)s: '
                            '%(levelname)s: '
                            '%(funcName)s(): '
                            '%(lineno)d:\t'
                            '%(message)s')
                    )
eventlet.monkey_patch()
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = binary_path
app.secret_key = 'your_secret_key'
socketio = SocketIO(app)

powersourceStatus = False
sourceConnection = None
arduinoConnection = None
cmd = ""
status = "Ready"
mess = ""
e_name = ""
e_id = ""
isSetPwr = False
trace_file_name = ""


def upload_scc_trace(trace):
    socketio.emit("message", trace+"\n\r", broadcast=True)


def broadcast_info():
    global socketio, powersourceStatus, sourceConnection, status
    while True:
        # socketio.emit("message", "assmessage")
        if sourceConnection == None:
            powersourceStatus = False
            status = "Power OFF"
            logging.debug("Power OFF")
        else:
            voltage = str(float(sourceConnection.GetVoltage().decode()))
            current = str(float(sourceConnection.GetCurrent().decode()))
            socketio.emit("powervalue", {
                "voltage": voltage,
                "current": current
            },
                broadcast=True)
            if isSetPwr == False:
                powersourceStatus = True
            status = "Power ON"
            logging.debug(
                "Power ON, voltage: {}, current: {}".format(voltage, current))
        socketio.emit("powersourceStatus",
                      data=powersourceStatus, broadcast=True)
        time.sleep(1)


def get_error_FlashGui(filename):
    proc = subprocess.Popen(["FlashGui.exe"])
    with open(filename, 'r') as f:
        last_pos = f.tell()
        while True:
            time.sleep(0.1)
            line = f.readline()
            if not line:
                f.seek(last_pos)
            else:
                last_pos = f.tell()
                if "Error: No valid Com Port selected -> Error !!" in line:  # in case FlashGui.exe hang
                    os.system("taskkill /f /im  FlashGui.exe")
                    socketio.emit("status", line)
                    logging.error("Flashing failed!! Error occurred")
                    break
                elif proc.poll() is not None:
                    socketio.emit("status", "Flashing finish!!")
                    logging.info("Flashing finish!!")
                    break


def upload_trace(file_name):
    socketio.emit("status", "Uploading trace...")
    if ttfisClient.LoadTRCFiles([trace_path+file_name]):
        socketio.emit("status", "Restarting ttfisClient...")
        ttfisClient.Restart()
        logging.info("trace upload success")
    else:
        logging.info("trace upload fail")
    ttfisClient.Restart()


def flash(file_name):
    global socketio
    print("going to flash")
    socketio.emit("status", "Start FLashGui")
    cmd = 'FlashGUI.exe /i Quad-G3G-RS232-DebugAdapter C - FT5W10RX,1000000,E,8,1 " /f{}/{} /b4038 /au'.format(
        binary_path, file_name)
    subprocess.Popen(cmd, stdout=subprocess.PIPE)
    socketio.emit("status", "Flashing...")
    logging.info("Start flashing...")
    get_error_FlashGui("logfile.txt")


def process_instruction_file(file_path):
    cmd, extra_cmd = read_cmd_list(file_path)
    lkup_table = dict()
    lkup_table["root"] = extract_cmd(cmd)
    lkup_table["enum"] = extract_enum(extra_cmd)
    return lkup_table


# @app.route('/', methods=['GET', 'POST'])
# def login():
#     global e_name, logined, e_id
#     if request.method == 'POST':
#         _e_id = request.form['e_id']
#         _e_name = request.form['e_name']
#         if logined and _e_id != e_id:
#             return render_template('login.html', error=f"Server is current log-in by {e_name}")
#         # Kiểm tra thông tin đăng nhập của người dùng và thiết lập session nếu đăng nhập thành công
#         if _e_id == e_id:
#             return redirect(url_for('index'))
#         elif _e_id == 'admin' and e_id == "":
#             session['e_id'] = _e_id
#             e_id = _e_id
#             e_name = _e_name
#             logined = True
#             return redirect(url_for('index'))
#         else:
#             return render_template('login.html', error='Invalid e_name')
#     else:
#         return render_template('login.html')


# @socketio.on("usr_name")
# def usrname(user):
#     print("user name :", user)


# @app.route('/index')
# def index():
#     global e_name, e_id
#     if session['e_id'] == e_id:
#         return render_template('index.html', username=e_name)
#     else:

#         return redirect(url_for('login'))

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/logout')
def logout():
    global logined, e_name, e_id
    logined = False
    e_name = ""
    e_id = ""
    session['e_name'] = None
    session['e_id'] = None
    return redirect(url_for('login'))


@app.route("/GetCommandSet/", methods=["GET"])
def GetCommandSet():
    global trace_path, trace_file_name
    trace_file_name = os.listdir(trace_path)
    traceFilePath = trace_path + trace_file_name[0]
    print(traceFilePath)
    return process_instruction_file(traceFilePath)


@app.route('/upload', methods=['POST'])
def upload_file():
    global trace_file_name
    try:
        file_dnl = request.files['file-dnl']
        filename_dnl = file_dnl.filename
        if ALLOWED_FILE[0] in filename_dnl:
            file_dnl.save(os.path.join(binary_path, filename_dnl))
            flash(filename_dnl)
            logging.info("Flashing with file: {}".format(filename_dnl))
        else:
            logging.error("File not found: {}".format(filename_dnl))
    except:
        pass
    try:
        file_trc = request.files['file-trc']
        filename_trc = file_trc.filename
        if ALLOWED_FILE[1] in filename_trc:
            file_trc.save(os.path.join(trace_path, filename_trc))
            logging.info("Upload Trace with file: {}".format(filename_trc))
            trace_file_name = filename_trc

            upload_trace(filename_trc)
        else:
            logging.error("File not found: {}".format(filename_trc))
    except:
        pass
    return ""


@socketio.on("user")
def user_require(user):
    user_name = user
    print(user_name)


@socketio.on("app_input")
def app_input(data):
    socketio.emit("appContent",  data, broadcast=True)


@socketio.on('powervalue')
def powervalue(payload):
    socketio.emit("powervalue", payload, broadcast=True)


@socketio.on('status')
def send_status(status):
    socketio.emit("status", status, broadcast=True)


@socketio.on('powersourceStatus')
def sourceStt(status):
    socketio.emit("powersourceStatus", status, broadcast=True)


@socketio.on('message')
def message_(message):
    socketio.emit("message", data=message, statusbroadcast=True)


def sync_data_from_arduino(pin, state, label):
    logging.info("Set {} result {}".format(label, state))
    print("Set {} result {}".format(label, state))
    socketio.emit("return_from_arduino", data={
                  "pin": pin, "state": True if state else False, "label": label}, broadcast=True)


@socketio.on("chat_message")
def chat(message):
    global mess
    print(message)
    mess = message


@socketio.on('request_to_arduino')
def handle_request(data):
    pin = data['pin']
    state = data['state']
    label = data['label']
    time.sleep(.1)
    if arduinoConnection:
        if pin == 'acc_button':
            _ = arduinoConnection.send_command(
                Command.ACC, DEVICE_ON if state else DEVICE_OFF)
        elif pin == 'ign_button':
            _ = arduinoConnection.send_command(
                Command.IGN, DEVICE_ON if state else DEVICE_OFF)
        elif pin == 'wd_off_button':
            _ = arduinoConnection.send_command(
                Command.WD, DEVICE_ON if state else DEVICE_OFF)
        elif pin == 'opt2_button':
            _ = arduinoConnection.send_command(
                Command.OPT2, DEVICE_ON if state else DEVICE_OFF)
        sync_data_from_arduino(pin, state, label)


@socketio.on("set_pin")
def set_hardware_pin(data):
    print(data)


@socketio.on("power_state")
def onpowerstate(state):

    print("power_state", state)
    global sourceConnection, isSetPwr
    isSetPwr = False
    if sourceConnection != None:
        if state:
            socketio.emit("powervalue", {
                "voltage": "12",
                "current": "0"
            },
                broadcast=True)
            socketio.emit("powersourceStatus", state)
        else:
            print('set pwer off')
            isSetPwr = True
            socketio.emit("powervalue", {
                "voltage": "0",
                "current": "0"
            },
                broadcast=True)
            socketio.emit("powersourceStatus", state)


@socketio.on("sccCommand")
def sccCommand(cmd):
    ttfisClient.Cmd(cmd)


@socketio.on("powervalue")
def powervalue(value):
    socketio.emit("powervalue", value)


@ socketio.on('setvoltagValue')
def setVolValue(volValue):
    global sourceConnection, powersourceStatus
    if sourceConnection != None:
        if (int(volValue) > volMax) or (int(volValue) <= volMin):
            status = "The voltage value must be in range 0-{}V".format(
                volMax)
        else:
            sourceConnection.SetVoltage(volValue)
            status = "Set voltage successfully"
    else:
        status = "Power source not connected"
    logging.debug(status)
    socketio.emit("status", status, broadcast=True)


if __name__ == '__main__':

    # ttfisClient = TTFisClient()
    # ttfisClient.registerUpdateTraceCallback(upload_scc_trace)
    # ttfisClient.Connect(device_name)
    Thread(target=broadcast_info, args=()).start()
    # sourceConnection = ToellnerDriver(powersource_port, powersource_channel)

    # if arduino_port:
    #     arduinoConnection = Arduino(arduino_port)
    #     logging.debug("Connect to {} : {}".format(
    #         arduino_port, "SUCCESS" if arduinoConnection is not None else "FAILED"))
    logging.info("Server start!!!")
    socketio.run(app, host='0.0.0.0', port=5000)

    # sourceConnection.__del__()
    # arduinoConnection.close()
    # ttfisClient.Quit()
    logging.info("Server stop!!!")
