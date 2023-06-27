import json

with open('settings.json', 'rb') as settingFile:
    settings = json.loads(settingFile.read())


binary_path = settings['filePath']['binary']
trace_path = settings['filePath']['trace']
arduino_port = settings['arduino_port']

voltage_max = settings['voltage_range']['max']
voltage_min = settings['voltage_range']['min']

normal_voltage = settings['voltage_range']['thresholds']['operating']
shutdown_voltage = settings['voltage_range']['thresholds']['critical_low']
ttfis_client_port = settings['ttfis_client']['port']
ToellnerDriver_connection_port = settings['power_source']['port']
ToellnerDriver_connection_channel = settings['power_source']['channel']

ToellnerDriver_connection = None
arduino_connection = None
is_power_turn_on = False
cmd = ""
error = ""
DEFAULT_TRACE_FILE_NAME = "ccs20_cfg04_board_UNKNOWN.trc"
SECRET_KEY = "LCMAutosar"
ALLOWED_FILE = ["dnl", "trc"]
ALLOWED_USER = ["rhn9hc", 'asm1hc', "snu1hc", "nry5hc", "yey1hc"]
