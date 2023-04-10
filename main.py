from flask import Flask, render_template
from flask_socketio import SocketIO
from threading import Thread
import json
import time
import eventlet
from tool.ToellnerDriver import ToellnerDriver
from tool.TTFisClient import TTFisClient
eventlet.monkey_patch()

app = Flask(__name__)
socketio = SocketIO(app)

with open('settings.json', 'rb') as settingFile:
    settings = json.loads(settingFile.read())

binary_path = settings['filePath']['binary']
trace_path = settings['filePath']['trace']

volMax = settings['voltageRange']['max']
volMin = settings['voltageRange']['min']
volNormal = settings['voltageRange']['normal']

sourceStatus = None
sourceConnection = None


def broadcast_info():
    global socketio, sourceStatus, sourceConnection

    while True:
        if sourceConnection == None:
            sourceStatus = "Power OFF"
        else:
            voltage = str(float(sourceConnection.GetVoltage().decode()))
            current = str(float(sourceConnection.GetCurrent().decode()))
            socketio.emit("powervalue", {
                "voltage": voltage,
                "current": current
            },
                broadcast=True)
            sourceStatus = "Power ON"
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


@socketio.on('setVolValue')
def setVolValue(volValue):
    print(volValue)
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
    socketio.emit("status", status)


if __name__ == '__main__':
    # ttfisClient = TTFisClient()
    # ttfisClient.registerUpdateTraceCallback(update_trace)
    # ttfisClient.Connect("GEN3FLEX@COM7")
    # ttfisClient.Connect("GEN3FLEX@DLT")
    Thread(target=broadcast_info, args=()).start()
    # sourceConnection = ToellnerDriver("COM15", 1)
    socketio.run(app)
    sourceConnection.__del__()
