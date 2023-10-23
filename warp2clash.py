import os
import re
import sys
import yaml


def read_profile_conf(filename):
    with open(filename, "r") as file:
        txt = file.read()
    data_list = re.findall(".+?= (.+)\n", txt)

    data_dict = {
        "name": re.match("\w+/(\w+)\.conf", filename).group(1),
        "type": "wireguard",
        "ip": data_list[1],
        "ipv6": data_list[2],
        "private-key": data_list[0],
        "public-key": data_list[5],
        "remote-dns-resolve": False,
        "mtu": int(data_list[4]),
        "udp": True,
    }
    return data_dict


def read_ip_csv():
    filename = "result.csv"
    print("reading", filename)
    ip_port_list = []
    with open(filename, "r") as file:
        for i, line in enumerate(file):
            if i == 4:
                # choose top3 ip-port
                break
            ip_port, _, latency = line.rstrip("\n").split(",")
            if latency.endswith("ms"):
                ip, port = ip_port.split(":")
                ip_port_list.append((ip, int(port)))
    return ip_port_list


def generate_proxies(profiles, servers):
    proxies = []
    for profile in profiles:
        name = profile["name"]
        for idx, (ip, port) in enumerate(servers):
            profile["name"] = f"{name}_{idx}"
            profile["server"] = ip
            profile["port"] = port
            proxies.append(profile.copy())
    return proxies


def generate_proxy_groups(proxy_names):
    with open("config/temp.yaml", "r", encoding="utf8") as file:
        proxy_groups_template = yaml.safe_load(file)

    proxy_groups = []
    for gp in proxy_groups_template["proxy-groups"]:
        if "☁️ CFWarp-A" in gp["proxies"]:
            gp["proxies"].remove("☁️ CFWarp-A")
            gp["proxies"] += proxy_names
        proxy_groups.append(gp)
    return proxy_groups


def prepare_new_proxies():
    profiles = [read_profile_conf(f"wireguard/{filename}") for filename in os.listdir("wireguard")]
    servers = read_ip_csv()
    proxies = generate_proxies(profiles, servers)
    proxy_names = [proxy["name"] for proxy in proxies]
    proxy_groups = generate_proxy_groups(proxy_names)
    return proxies, proxy_groups


def update_config(old_config_name, proxies, proxy_groups):
    with open(old_config_name, "r", encoding="utf8") as file:
        old_config = yaml.safe_load(file)

    old_config["proxies"] = proxies
    old_config["proxy-groups"] = proxy_groups
    with open("new_config.yaml", "w", encoding="utf8") as file:
        yaml.dump(old_config, file, allow_unicode=True)


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        old_config_name = sys.argv[1]
    else:
        print("Usage: python warp2clash.py old_config.yaml")
        exit(0)

    proxies, proxy_groups = prepare_new_proxies()
    update_config(old_config_name, proxies, proxy_groups)
