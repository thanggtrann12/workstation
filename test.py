import string
import random
import asyncio
from flask import Flask, jsonify
import time
import threading

app = Flask(__name__)

data = ""
isInStateRun = False
isInEnd = False
prefix = ""


class TestFlow:
    def __init__(self):
        self.stopFlag = False

    async def timer(self, duration, condition, func_do_success, func_do_failed):
        for _ in range(duration):
            if condition():
                func_do_success()
                break
            await asyncio.sleep(1)
        else:
            func_do_failed()

    async def execute_test(self, execute_time, func_do_begin, duration, condition, func_do_success, func_do_failed, func_save_log):
        self.stopFlag = False
        for _ in range(execute_time):
            func_do_begin()
            time_execute = execute_time - _
            print("Current test time:", time_execute)
            await self.timer(duration, condition, func_do_success, func_do_failed)
            print("time:", _)
            await func_save_log(_)

            await asyncio.sleep(1)

    def stop_execution(self):
        self.stopFlag = True


# Example usage

def func_do_success():
    global data, prefix
    for i in range(0, 10):
        data += str(i) + "\r\n"
        time.sleep(1)
    prefix = "PASSED"
    print("func_do_successing...")


def func_do_failed():
    print("func_do_failed...")
    global data, prefix
    prefix = "FAILED"
    data += "\r\nFAILED "


def func_do_begin():
    print("Performing action...")


def condition():
    print("isInEnd")
    global isInEnd
    return isInEnd


async def log(time):
    global data, prefix
    while True:
        if get():
            break
        await asyncio.sleep(1)
    file_path = f"C:/Users/thang/Desktop/workstation/static/uploads/test/test_{time}_{prefix}.txt"
    with open(file_path, 'a') as file:
        file.write(data)
    data = ""
    prefix = ""
    print("Data successfully written to the file.")


test_flow = TestFlow()


def get():
    global isInStateRun
    return isInStateRun


def generate_random_string(length):
    # includes both uppercase and lowercase letters, as well as digits
    letters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(letters) for _ in range(length))
    return random_string


@app.route('/start-test/<test_name>', methods=['GET'])
def start_test(test_name):
    asyncio.run(test_flow.execute_test(
        5, func_do_begin, 5, condition, func_do_success, func_do_failed, log))
    return jsonify({'message': f'Test "{test_name}" started'})


@app.route('/stop-test', methods=['GET'])
def stop_test():
    test_flow.stop_execution()
    return jsonify({'message': 'Test stopped'})


def update_trace():
    global data, isInStateRun, isInEnd
    while True:
        data += generate_random_string(10)
        test = random.randint(0, 3)
        test_ = random.randint(0, 5)
        if test == 0:
            isInStateRun = True
        if test_ == 0:
            isInEnd = False
        time.sleep(1)


if __name__ == '__main__':
    threading.Thread(target=update_trace).start()
    app.run(debug=True)
