from flask import Flask, render_template
from flask_socketio import SocketIO
from threading import Thread
import json
import time
import eventlet
from tool.ToellnerDriver import ToellnerDriver
# from tool.TTFisClient import TTFisClient
from tool.ArduinoControl import Arduino, Command
import logging

logging.basicConfig(filename='log.txt', level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s')
eventlet.monkey_patch()
app = Flask(__name__)
socketio = SocketIO(app)
with open('settings.json', 'rb') as settingFile:
    settings = json.loads(settingFile.read())

binary_path = settings['filePath']['binary']
trace_path = settings['filePath']['trace']
arduino_port = settings['arduino_port']
volMax = settings['voltageRange']['max']
volMin = settings['voltageRange']['min']
volNormal = settings['voltageRange']['normal']

sourceStatus = None
sourceConnection = None
arduinoConnection = None


def broadcast_info():
    global socketio, sourceStatus, sourceConnection

    while True:
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
        socketio.emit("sourceStatus", data=sourceStatus)
        time.sleep(1)


def update_trace(content):
    socketio.send(content, broadcast=True)


@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('powervalue')
def powervalue(payload):
    socketio.emit("powervalue", payload)


@socketio.on('sourceStatus')
def sourceStt(status):
    socketio.emit("sourceStatus", status)


@socketio.on('status')
def status(status):
    socketio.emit("status", status)


@socketio.on('ACC')
def handleACC(isACCconnected):
    if arduinoConnection:
        ret = arduinoConnection.send_command(
            Command.ACC_ON if isACCconnected == True else Command.ACC_OFF)
        logging.info("Set ACC result {}".format(ret))
        socketio.emit("ret", ret)


@ socketio.on('IGN')
def handleIGN(isIGNconnected):
    if arduinoConnection:
        ret = arduinoConnection.send_command(
            Command.IGN_ON if isIGNconnected == True else Command.IGN_OFF)
        logging.info("Set IGN result {}".format(ret))
        socketio.emit("ret", ret)


@ socketio.on('WD')
def handleWD(isWDconnected):
    if arduinoConnection:
        ret = arduinoConnection.send_command(
            Command.WD_ON if isWDconnected == True else Command.WD_OFF)
        logging.info("Set WD_OFF result {}".format(ret))
        socketio.emit("ret", ret)


@ socketio.on('OPT2')
def handleOPT2(isOPT2connected):
    if arduinoConnection:
        ret = arduinoConnection.send_command(
            Command.OPT2_ON if isOPT2connected == True else Command.OPT2_OFF)
        logging.info("Set OPT2 result {}".format(ret))
        socketio.emit("ret", ret)


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
    socketio.emit("status", status)


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
