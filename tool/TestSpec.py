
import time
prefix = ""


class TestFlow:
    def __init__(self):
        self.stopFlag = False
        print("init test")

    def timer(self, duration, condition, func_do_success, func_do_failed):
        global prefix
        for _ in range(duration):
            if condition():
                prefix = "PASSED"
                func_do_success()
                break
            time.sleep(1)
        else:
            prefix = "FAILED"
            func_do_failed()

    def execute_test(self, execute_time, func_do_begin, duration, condition, func_do_success, func_do_failed, func_save_log):
        self.stopFlag = False
        for _ in range(execute_time):
            func_do_begin()
            time_execute = execute_time - _
            print("Current test time:", time_execute)
            self.timer(duration, condition, func_do_success, func_do_failed)
            print("time:", _)
            func_save_log(_, prefix)

    def stop_execution(self):
        self.stopFlag = True
