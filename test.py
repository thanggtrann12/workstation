import asyncio
from flask import Flask, jsonify
import time

app = Flask(__name__)


class TestFlow:
    def __init__(self):
        self.stopFlag = False  # Flag to indicate if the timer should stop

        self.E_OK = True
        self.E_NOK = False

    async def timer(self, duration, condition, transition, expired, log):
        temp_dur = duration
        while temp_dur > 0 and not self.stopFlag:
            temp_dur -= 1
            if condition:
                transition()
                log()
                break
            await asyncio.sleep(1)
        if not condition:
            expired()
        log()

    async def execute_test(self, time, action, duration, condition, transition, expired, log):
        temp_time = time
        self.stopFlag = False
        action()
        while temp_time > 0 and not self.stopFlag:
            time_execute = time - temp_time
            print("Current test time:", time_execute)
            await self.timer(duration, condition, transition, expired, log)
            print("time:", temp_time)
            temp_time -= 1

    def stop_execution(self):
        self.stopFlag = True

# Example usage


def transition():
    for i in range(0, 10):
        time.sleep(1)
    print("Transitioning...")


def expired():
    print("Expired...")


def action():
    print("Performing action...")


def log():
    print("Logging...")


test_flow = TestFlow()


@app.route('/start-test/<test_name>', methods=['GET'])
def start_test(test_name):
    asyncio.run(test_flow.execute_test(
        5, action, 5, test_flow.E_OK, transition, expired, log))
    return jsonify({'message': f'Test "{test_name}" started'})


@app.route('/stop-test', methods=['GET'])
def stop_test():
    test_flow.stop_execution()
    return jsonify({'message': 'Test stopped'})


if __name__ == '__main__':
    app.run(debug=True)
