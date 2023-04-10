import readline
import keyboard
import json


def read_cmd_list(file_path):
    base = list()
    enum = list()

    with open(file_path, "r") as f:
        for line in f.readlines():
            type = line.strip().split(maxsplit=1)
            if len(type) > 0:
                if type[0] == "ARRAY":
                    enum.append(type[1])
                elif type[0] == "CMD":
                    base.append(parse_cmd(type[1]))
    return (base, enum)


def parse_cmd(cmd: str):
    return cmd.split("::")[0]


def extract_cmd(cmd):
    result = dict()
    for c in cmd:
        try:
            base, option = c.strip().split(maxsplit=1)
            option = extract_option(option)
        except ValueError:
            base = c.strip()
            option = None
        assert (" " not in base)
        result[base] = option
    return result


def extract_option(op: str):
    lBound = op.find("(")
    result = list()
    while lBound != -1:
        lBound += 1
        enum_name = op[lBound: op.find(")", lBound)]
        lBound = op.find("(", lBound)

        # Hack to filter number option
        try:
            int(enum_name)
            enum_name = None
        except ValueError:
            pass

        # Filter out option like (100, Enum)
        try:
            enum_name = enum_name.split(",")[1].strip()
        except (IndexError, AttributeError):
            pass

        if enum_name:
            assert (" " not in enum_name)
            result.append(enum_name)
        else:
            result.append(None)
    return result


def extract_enum(enum_list):
    enum_table = dict()
    enum_table["APP_AND_CNTXT"] = list()
    enum_table["APP_AND_CNTXT"].append("SUPVISOR")
    enum_table["APP_AND_CNTXT"].append("SuplMgmt")
    enum_table["APP_AND_CNTXT"].append("SySMPrj_")
    enum_table["APP_AND_CNTXT"].append("TMPrPrj_")
    enum_table["APP_AND_CNTXT"].append("APP_WDG_")
    enum_table["APP_AND_CNTXT"].append("WRD_MAIN")
    enum_table["APP_AND_CNTXT"].append("VOLTMGMT")
    enum_table["APP_AND_CNTXT"].append("SYSTINFO")
    enum_table["APP_AND_CNTXT"].append("WRD_MAIN")
    for enum in enum_list:
        if "=" not in enum:
            continue
        try:
            name, value = enum.split(": ")
            name = name.split("=")[0].strip()
            value = value.strip()

            if " " in value:
                value = value.split()[1]

            assert (" " not in value)
            assert (" " not in name)

            try:
                enum_table[name].append(value)
            except KeyError:
                enum_table[name] = list()
                enum_table[name].append(value)
        except:
            pass
    return enum_table


def process_instruction_file(file_path):
    cmd, extra_cmd = read_cmd_list(file_path)
    lkup_table = dict()
    lkup_table["root"] = extract_cmd(cmd)
    lkup_table["enum"] = extract_enum(extra_cmd)

    return lkup_table


data = process_instruction_file("static/trace.txt")


current_command = ''  # biến để lưu trữ command đang được nhập


def get_matching_values(text):
    # Trả về danh sách các giá trị phù hợp với text
    matching_values = []
    for value in my_list:
        if value.startswith(text):
            matching_values.append(value)
    return matching_values


def auto_complete(text, state):
    # Hàm được gọi bởi readline để hiển thị danh sách các giá trị phù hợp với text
    if state == 0:
        # Đầu tiên, lấy danh sách các giá trị phù hợp với text
        global matching_values
        matching_values = get_matching_values(text)
    if state < len(matching_values):
        # Hiển thị giá trị phù hợp thứ state
        return matching_values[state]
    else:
        # Không còn giá trị nào phù hợp
        return None


# Cấu hình readline để sử dụng hàm auto_complete
readline.parse_and_bind("tab: complete")
readline.set_completer(auto_complete)

# Đọc dữ liệu vào danh sách
my_list = data['root']

# Bắt đầu nhập từ khóa và sử dụng auto-complete
while True:
    keyword = input("Nhập từ khóa: ")
    print(get_matching_values(keyword))
