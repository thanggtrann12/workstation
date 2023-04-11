from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from threading import Thread
import json
import time
import eventlet
from tool.ToellnerDriver import ToellnerDriver
# from tool.TTFisClient import TTFisClient
from tool.ArduinoControl import Arduino, Command
import logging
import subprocess
import os
import psutil

with open('settings.json', 'rb') as settingFile:
    settings = json.loads(settingFile.read())

binary_path = settings['filePath']['binary']
trace_path = settings['filePath']['trace']
arduino_port = settings['arduino_port']
volMax = settings['voltageRange']['max']
volMin = settings['voltageRange']['min']
volNormal = settings['voltageRange']['normal']

ALLOWED_FILE = ["dnl", "trc"]


logging.basicConfig(filename='log.txt', level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s')
eventlet.monkey_patch()
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = binary_path
socketio = SocketIO(app)


sourceStatus = None
sourceConnection = None
arduinoConnection = None


def broadcast_info():
    global socketio, sourceStatus, sourceConnection
    while True:
        socketio.emit("message", "assmessage")
        if sourceConnection == None:
            sourceStatus = "Power OFF"
            logging.debug("Power OFF")
        else:
            voltage = str(float(sourceConnection.GetVoltage().decode()))
            current = str(float(sourceConnection.GetCurrent().decode()))
            socketio.emit("powervalue", {
                "voltage": voltage,
                "current": current
            },
                broadcast=True)
            sourceStatus = "Power ON"
            logging.debug(
                "Power ON, voltage: {}, current: {}".format(voltage, current))
        socketio.emit("sourceStatus", data=sourceStatus, broadcast=True)
        time.sleep(1)


def update_trace(content):
    print(content)
    socketio.send(content, broadcast=True)


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
                if "Error" in line:  # in case FlashGui.exe hang
                    os.system("taskkill /f /im  FlashGui.exe")
                    socketio.emit("status", "Flashing failed!! Error occurred")
                    logging.error("Flashing failed!! Error occurred")
                    break
                elif proc.poll() is not None:
                    socketio.emit("status", "Flashing finish!!")
                    logging.info("Flashing finish!!")
                    break


def flash(file_name):
    global socketio
    socketio.emit("status", "FLashing......")
    cmd = 'FlashGUI.exe /iQuad-G3G-RS232-DebugAdapter C - FT5TMNM0,1000000,E,8,1 " /f{}/{} /b4038 /au'.format(
        binary_path, file_name)
    subprocess.Popen(cmd, stdout=subprocess.PIPE)
    socketio.emit("status", "Flashing...")
    logging.info("Start flashing...")
    get_error_FlashGui("logfile.txt")


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        file_dnl = request.files['file-dnl']
        filename_dnl = file_dnl.filename
        if ALLOWED_FILE[0] in filename_dnl:
            print("valid")
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
        else:
            logging.error("File not found: {}".format(filename_trc))
    except:
        pass
    return ""


@socketio.on('powervalue')
def powervalue(payload):
    socketio.emit("powervalue", payload, broadcast=True)


@socketio.on('sourceStatus')
def sourceStt(status):
    socketio.emit("sourceStatus", status, broadcast=True)


@socketio.on('status')
def status(status):
    socketio.emit("status", statusbroadcast=True)


@socketio.on('message')
def message_(message):
    print(message)
    socketio.emit("message", data=message, statusbroadcast=True)


@socketio.on('ACC')
def handleACC(isACCconnected):
    if arduinoConnection:
        ret = arduinoConnection.send_command(
            Command.ACC_ON if isACCconnected == True else Command.ACC_OFF)
        logging.info("Set ACC result {}".format(ret))
        socketio.emit("ret", ret, broadcast=True)


@ socketio.on('IGN')
def handleIGN(isIGNconnected):
    if arduinoConnection:
        ret = arduinoConnection.send_command(
            Command.IGN_ON if isIGNconnected == True else Command.IGN_OFF)
        logging.info("Set IGN result {}".format(ret))
        socketio.emit("ret", ret, broadcast=True)


@ socketio.on('WD')
def handleWD(isWDconnected):
    if arduinoConnection:
        ret = arduinoConnection.send_command(
            Command.WD_ON if isWDconnected == True else Command.WD_OFF)
        logging.info("Set WD_OFF result {}".format(ret))
        socketio.emit("ret", ret, broadcast=True)


@ socketio.on('OPT2')
def handleOPT2(isOPT2connected):
    if arduinoConnection:
        ret = arduinoConnection.send_command(
            Command.OPT2_ON if isOPT2connected == True else Command.OPT2_OFF)
        logging.info("Set OPT2 result {}".format(ret))
        socketio.emit("ret", ret, broadcast=True)


@ socketio.on('setVolValue')
def setVolValue(volValue):
    global sourceConnection, sourceStatus
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
    # ttfisClient.registerUpdateTraceCallback(update_trace)
    # ttfisClient.Connect("GEN3FLEX@COM7")
    # ttfisClient.Connect("GEN3FLEX@DLT")
    Thread(target=broadcast_info, args=()).start()

    # sourceConnection = ToellnerDriver("COM15", 1)

    if arduino_port:
        arduinoConnection = Arduino(arduino_port)
        logging.debug("Connect to {} : {}".format(
            arduino_port, "SUCCESS" if arduinoConnection is not None else "FAILED"))

    socketio.run(app)

    sourceConnection.__del__()
    arduinoConnection.close()
