from __future__ import print_function
try:
    from ncclient import manager
    from prettytable import PrettyTable
    from netaddr import IPAddress
    import pandas as pd
    import ipaddress
    import os
    import sys
except Exception:
    print('Install all the necessary modules')
    sys.exit()

if __name__ == "__main__":
    TABLE = PrettyTable(['Router', 'Hostname', 'Loopback 99 IP', 'OSPF area', 'Advertised OSPF Networks'])
    file = 'info.csv'
    if not os.path.exists(file):
        print("File {} not found, exiting".format(file))
        sys.exit()
    if os.stat(file).st_size == 0:
        print('File {} is empty, exiting'.format(file))
        sys.exit()
    READ_FILE = pd.read_csv('info.csv')
    ROUTERS = READ_FILE['Router'].to_list()
    MGM_IP = READ_FILE['Mgmt IP'].to_list()
    UNAME = READ_FILE['Username'].to_list()
    PWD = READ_FILE['Password'].to_list()
    HOST = READ_FILE['Hostname'].to_list()
    LO_NAME = READ_FILE['Loopback Name'].to_list()
    LO_IP = READ_FILE['Loopback IP'].to_list()
    MASK = READ_FILE['Loopback Subnet'].to_list()
    WILDCARD = READ_FILE['Wildcard'].to_list()
    NETWORKS = READ_FILE['Network'].to_list()
    AREA = READ_FILE['OSPF Area'].to_list()

    cfg = '''
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
	'''

    for i in range(0, 5):
        connection = manager.connect(host=MGM_IP[i],
                                     port=22,
                                     username=UNAME[i],
                                     password=PWD[i],
                                     hostkey_verify=False,
                                     device_params={'name': 'iosxr'},
                                     allow_agent=False,
                                     look_for_keys=True)
        print('Logging into router {} and sending configurations'.format(ROUTERS[i]))
        cfg1 = cfg % (HOST[i], LO_NAME[i], LO_IP[i], MASK[i], NETWORKS[i], WILDCARD[i], AREA[i])
        edit_cfg = connection.edit_config(target='running', config=cfg1)

    print('\n------------------Configs to all routers is sent------------------\n')

    FETCH_INFO = '''
    		<filter>
    		<config-format-text-block>
    		<text-filter-spec> %s </text-filter-spec>
    		</config-format-text-block>
    		</filter>
    		'''

    for i in range(0, 5):
        connection = manager.connect(host=MGM_IP[i],
                                     port=22,
                                     username='lab',
                                     password='lab123',
                                     hostkey_verify=False,
                                     device_params={'name': 'iosxr'},
                                     allow_agent=False,
                                     look_for_keys=True)
        print('Pulling information from router {} to display'.format(ROUTERS[i]))

        fetch_hostname = FETCH_INFO % ('| i hostname')
        output1 = connection.get_config('running', fetch_hostname)
        split1 = str(output1).split()
        hostname = split1[6]

        fetch_lo_info = FETCH_INFO % ('int Loopback99')
        output2 = connection.get_config('running', fetch_lo_info)
        split2 = str(output2).split()
        lo_ip_mask = split2[9] + '/' + str(IPAddress(split2[10]).netmask_bits())

        fetch_ospf_info = FETCH_INFO % ('| s ospf')
        output3 = connection.get_config('running', fetch_ospf_info)
        split3 = str(output3).split()
        lo_ip_prefix = str(ipaddress.ip_network(split3[9] + '/' + split3[10], strict=False)
                           .prefixlen)
        mgm_ip_prefix = str(ipaddress.ip_network(split3[14] + '/' + split3[15], strict=False)
                            .prefixlen)
        ospf_area = split3[12]
        ospf_networks = split3[9] + '/' + lo_ip_prefix, split3[14] + '/' + mgm_ip_prefix

        TABLE.add_row((ROUTERS[i], hostname, lo_ip_mask, ospf_area, ospf_networks))

    print('\n------------------Displaying the fetched information------------------\n')
    print(TABLE)