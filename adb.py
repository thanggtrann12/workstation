import os
import subprocess
from flask import Flask, render_template, request

app = Flask(__name__)

os.environ['PATH'] += ';C:/Users/rhn9hc/Desktop/TOOL/adb'

@app.route("/", methods=["GET", "POST"])
def index():
    result = ""
    if request.method == "POST":
        cmd = request.form["cmd"]
        if cmd.startswith("cd "):
            path = cmd[3:]
            os.chdir(path)
        else:
            try:
                result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
                result = result.decode()
                print("result:", result)
            except subprocess.CalledProcessError as e:
                if "adb" in cmd and "device" not in e.output.decode().lower():
                    # adb is not connected
                    result = "adb is not connected"
                else:
                    result = e.output.decode()
    return render_template("index.html", result= result+"\n\r")


if __name__ == "__main__":
    app.run(debug=True)
