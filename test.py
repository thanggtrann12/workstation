from enum import Enum


class ButtonState(Enum):
    ACC_ON = 0
    ACC_OFF = 1
    IGN_ON = 2
    IGN_OFF = 3
    OPT2_ON = 4
    OPT2_OFF = 5
    WD_ON = 6
    WD_OFF = 7


for state in ButtonState:
    print(state, state.value)
