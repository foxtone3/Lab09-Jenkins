#!/usr/bin/env python3
"""Lab 9 corrected working version of the provided NETCONF script."""

from __future__ import print_function

import ipaddress
import os
import sys

import pandas as pd
from ncclient import manager
from netaddr import IPAddress
from prettytable import PrettyTable


def main():
    """Read router data, push config, then pull and display verification data."""
    table = PrettyTable(
        ["Router", "Hostname", "Loopback 99 IP", "OSPF area", "Advertised OSPF Networks"]
    )

    file_name = "info.csv"
    if not os.path.exists(file_name):
        print(f"File {file_name} not found, exiting")
        sys.exit()

    if os.stat(file_name).st_size == 0:
        print(f"File {file_name} is empty, exiting")
        sys.exit()

    read_file = pd.read_csv(file_name)
    routers = read_file["Router"].to_list()
    mgmt_ip = read_file["Mgmt IP"].to_list()
    usernames = read_file["Username"].to_list()
    passwords = read_file["Password"].to_list()
    hostnames = read_file["Hostname"].to_list()
    loopback_names = read_file["Loopback Name"].to_list()
    loopback_ips = read_file["Loopback IP"].to_list()
    masks = read_file["Loopback Subnet"].to_list()
    wildcards = read_file["Wildcard"].to_list()
    networks = read_file["Network"].to_list()
    areas = read_file["OSPF Area"].to_list()

    cfg = """
    <config>
        <cli-config-data>
            <cmd> hostname %s </cmd>
            <cmd> int %s </cmd>
            <cmd> ip address %s %s </cmd>
            <cmd> router ospf 1 </cmd>
            <cmd> network %s %s area %s </cmd>
            <cmd> network 198.51.100.0 0.0.0.255 area 0 </cmd>
        </cli-config-data>
    </config>
    """

    for i in range(0, 5):
        connection = manager.connect(
            host=mgmt_ip[i],
            port=22,
            username=usernames[i],
            password=passwords[i],
            hostkey_verify=False,
            device_params={"name": "iosxr"},
            allow_agent=False,
            look_for_keys=True,
        )
        print(f"Logging into router {routers[i]} and sending configurations")
        cfg_payload = cfg % (
            hostnames[i],
            loopback_names[i],
            loopback_ips[i],
            masks[i],
            networks[i],
            wildcards[i],
            areas[i],
        )
        connection.edit_config(target="running", config=cfg_payload)

    print("\n------------------Configs to all routers were sent------------------\n")

    fetch_info = """
    <filter>
        <config-format-text-block>
            <text-filter-spec> %s </text-filter-spec>
        </config-format-text-block>
    </filter>
    """

    for i in range(0, 5):
        connection = manager.connect(
            host=mgmt_ip[i],
            port=22,
            username=usernames[i],
            password=passwords[i],
            hostkey_verify=False,
            device_params={"name": "iosxr"},
            allow_agent=False,
            look_for_keys=True,
        )
        print(f"Pulling information from router {routers[i]} to display")

        fetch_hostname = fetch_info % ("| i hostname")
        output1 = connection.get_config("running", fetch_hostname)
        split1 = str(output1).split()
        hostname = split1[6]

        fetch_loopback = fetch_info % ("int Loopback99")
        output2 = connection.get_config("running", fetch_loopback)
        split2 = str(output2).split()
        loopback_ip_mask = f"{split2[9]}/{IPAddress(split2[10]).netmask_bits()}"

        fetch_ospf = fetch_info % ("| s ospf")
        output3 = connection.get_config("running", fetch_ospf)
        split3 = str(output3).split()

        loopback_prefix = str(
            ipaddress.ip_network(f"{split3[9]}/{split3[10]}", strict=False).prefixlen
        )
        mgmt_prefix = str(
            ipaddress.ip_network(f"{split3[14]}/{split3[15]}", strict=False).prefixlen
        )

        ospf_area = split3[12]
        ospf_networks = (
            f"{split3[9]}/{loopback_prefix}",
            f"{split3[14]}/{mgmt_prefix}",
        )

        table.add_row((routers[i], hostname, loopback_ip_mask, ospf_area, ospf_networks))

    print("\n------------------Displaying the fetched information------------------\n")
    print(table)


if __name__ == "__main__":
    try:
        main()
    except ImportError:
        print("Install all the necessary modules")
        sys.exit()
    except KeyboardInterrupt:
        print("\nExecution interrupted by user.")
        sys.exit()
