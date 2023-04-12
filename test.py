from tool.TTFisClient import TTFisClient
import time


def upload_scc_trace(trace):
    print(trace)
    print("\n")


ttfis = TTFisClient()
ttfis.registerUpdateTraceCallback(upload_scc_trace)
ttfis.Connect(
    "GEN3FLEX@COM4")
time.sleep(1)
while 1:
    cmd = input("cmd: ")
    ttfis.Cmd(cmd)
