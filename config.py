import json
import logging

with open('settings.json', 'rb') as settingFile:

    settings = json.loads(settingFile.read())


binary_path = settings['filePath']['binary']
trace_path = settings['filePath']['trace']
arduino_port = settings['arduino_port']
voltage_max = settings['voltage_range']['max_threshold']
voltage_min = settings['voltage_range']['min_threshold']
normal_voltage = settings['voltage_range']['operating']
shutdown_voltage = settings['voltage_range']['shutdown']
ttfis_client_port = settings['ttfis_client']['port']
log_file_path = settings['filePath']['log']
powersource_port = settings['power_source']['port']
powersource_channel = settings['power_source']['channel']

power_source_connection = None
arduino_connection = None
is_power_turn_on = False
cmd = ""
error = ""
DEFAULT_TRACE_FILE_NAME = "ccs20_cfg04_board_UNKNOWN.trc"
SECRET_KEY = "LCMAutosar"
ALLOWED_FILE = ["dnl", "trc"]
ALLOWED_USER = ["rhn9hc", 'asm1hc', "snu1hc", "nry5hc"]
