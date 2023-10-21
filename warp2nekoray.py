import subprocess
import json
import re
import os


def run_exe_program(exe_path):
    try:
        output = subprocess.check_output(exe_path, shell=True, stderr=subprocess.STDOUT, universal_newlines=True, encoding="utf8")
        return output
    except subprocess.CalledProcessError as e:
        return e.output


def read_profile_conf(filename):
    with open(filename, "r") as file:
        txt = file.read()
    data_list = re.findall(".+?= (.+)\n", txt)
    data_dict = {
        "local_address": data_list[1:3],
        "peer_public_key": data_list[5],
        "private_key": data_list[0],
        "type": "wireguard",
    }
    return data_dict


def read_ip_csv():
    filename = "result.csv"
    print("generating", filename)
    ip_port_list = []
    with open(filename, "r") as file:
        for i, line in enumerate(file):
            if i == 6:
                # choose top5 ip-port
                break
            ip_port, _, latency = line.rstrip("\n").split(",")
            if latency.endswith("ms"):
                ip, port = ip_port.split(":")
                ip_port_list.append((ip, int(port)))
    return ip_port_list


def write_output_json(index: int, key_index: int, warp_dict: dict):
    with open("config/template.json", "r") as file:
        template_j = json.load(file)
    template_j["id"] = index
    template_j["bean"]["name"] = f"key-{key_index}"
    template_j["bean"]["cs"] = json.dumps(warp_dict)
    filename = f"output/{index}.json"
    with open(filename, "w") as file:
        print("writing", filename)
        json.dump(template_j, file)


def genrate_config(profiles: list[dict], ip_port_list: list, start_index: int):
    os.makedirs("output", exist_ok=True)
    for i, profile_dict in enumerate(profiles):
        for j, (ip, port) in enumerate(ip_port_list):
            profile_dict["server"] = ip
            profile_dict["server_port"] = port
            base_num = start_index * (i + 1)
            write_output_json(base_num + j, base_num, profile_dict)


if __name__ == "__main__":
    INPUT_DIR = "wireguard"
    profile_dicts = [read_profile_conf(f"{INPUT_DIR}/{file}") for file in os.listdir(INPUT_DIR)]
    run_exe_program("warp-yxip.bat")
    ip_port_list = read_ip_csv()
    genrate_config(profile_dicts, ip_port_list, start_index=100)
