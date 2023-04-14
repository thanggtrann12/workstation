import json
with open('settings.json', 'rb') as settingFile:
    settings = json.loads(settingFile.read())

binary_path = settings['filePath']['binary']
trace_path = settings['filePath']['trace']
arduino_port = settings['arduino_port']
volMax = settings['voltageRange']['max']
volMin = settings['voltageRange']['min']
volNormal = settings['voltageRange']['normal']
device_name = settings['device']
powersource_port = settings['power_source']['port']
powersource_channel = settings['power_source']['channel']

SECRET_KEY = "LCMAutosar"
