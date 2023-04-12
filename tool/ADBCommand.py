from adbutils import adb
import os


class AdbCommand:
    def __init__(self):
        try:
            self.device = adb.device()
        except:
            raise RuntimeError("No divice connected")

    def runCommandWithAdbShell(self, cmd):
        resp = " ".join(self.device.shell(cmd).split())
        device = self.device.serial

        return device, resp

    def uploadFileWithAdbShell(self, path):
        if os.path.exists(path):
            resp = self.device.sync.push(path)
            return resp
        return "Empty path file"

    def getFileWithAdbShell(self, from_dest, to_dest):
        resp = self.device.sync.pull(from_dest, to_dest)
        return resp


adb = AdbCommand()

_, res = adb.runCommandWithAdbShell("ls")
print(res)
