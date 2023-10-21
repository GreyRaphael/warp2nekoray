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


def read_account_toml():
    with open("wgcf-account.toml", "r") as file:
        data_list = re.findall("\w+ = '(.+)'\n", file.read())
        return {"license_key": data_list[2], "private_key": data_list[3]}


def update_account_toml(license_key: str):
    filename = "wgcf-account.toml"
    with open(filename, "w") as file:
        line1 = "access_token = '7a6680a2-3d39-402d-ba97-9bacd92a4934'"
        line2 = "device_id = '4c169f91-e7fb-44f6-ab65-8ef29f9a10d9'"
        line3 = f"license_key = '{license_key}'"
        line4 = "private_key = 'KBoIQGCks9u41xjXV02fDamCZcYw99DId7BwvSgVYks='\n"
        file.write("\n".join([line1, line2, line3, line4]))
    run_exe_program("./wgcf update")
    data_dict = read_account_toml()
    print(f"update wgcf-account.toml: {data_dict['private_key']}")


def read_profile_conf(filename):
    with open(filename, "r") as file:
        txt = file.read()
    data_list = re.findall("\w+ = (.+)\n", txt)
    data_dict = {
        "local_address": data_list[1:3],
        "peer_public_key": data_list[5],
        "private_key": data_list[0],
        "type": "wireguard",
    }
    return data_dict


def generate_profile_conf(license_key: str):
    filename = "wgcf-profile.conf"
    run_exe_program("./wgcf generate")
    profile_dict = read_profile_conf(filename)
    print(f"generate wgcf-profile.conf: {profile_dict['private_key']}")
    return profile_dict


def read_ip_csv():
    ip_port_list = []
    with open("result.csv", "r") as file:
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
    with open(f"output/{index}.json", "w") as file:
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
    with open("config/license_keys.txt", "r") as file:
        license_keys = [line.rstrip("\n") for line in file]
    profiles = []
    for license_key in license_keys:
        update_account_toml(license_key)
        profile_dict = generate_profile_conf(license_key)
        profiles.append(profile_dict)

    run_exe_program("./warp-yxip.sh")
    ip_port_list = read_ip_csv()
    genrate_config(profiles, ip_port_list, start_index=100)
    os.remove("wgcf-account.toml")
    os.remove("wgcf-profile.conf")
