#!/usr/bin/env python3

'''
READ ME:
This python file is designed to...

'''

#Imports at the top

from loguru import logger
from netmiko import ConnectHandler
import unittest, re
import pandas as pd

#All functions that organize code go here:

class NetmanTest(unittest.TestCase):

    @classmethod

    def setUpClass(cls):
        """Loading router data."""
        cls.df = pd.read_csv("info.csv")
    
    def getRtrRow(self, router_name):
        f"""Retrieving {router_name}'s router data"""
        row = self.df[self.df["Router"] == router_name]
        self.assertFalse(row.empty,f"{router_name} not found in 'info.csv'.")
        return row.iloc[0]
    
    def cnctRtr(self, router_name):
        row = self.getRtrRow(router_name)
        return ConnectHandler(
            device_type = 'cisco_ios',
            host = str(row["Mgmt IP"]).strip(),
            username = str(row["Username"]).strip(),
            password = str(row["Password"]).strip(),
            fast_cli = False
        )
        
    def test_r3_loopback(self):
        """Verify R3 Loopback99"""
        with self.cnctRtr("R3") as conn:
            output = conn.send_command("show running-config interface Loopback99")
            self.assertIn("ip address 10.1.3.1 255.255.255.0", output)
    
    def test_r1_OSPF_Area(self):
        """Verify R1 OSPF Area"""
        with self.cnctRtr("R1") as conn:
            output = conn.send_command("show running-config | section router ospf")
            areaMatches = re.findall(r"area\s+(\d+)", output)
            uniqueAreas = set(areaMatches)
            self.assertGreater(len(areaMatches),0, "No OSPF area statements found on the device.")
            self.assertEqual(len(uniqueAreas), 1, f"The device has multiple OSPF areas: {uniqueAreas}")
    
    def test_r2_r5_Ping(self):
        """Verify ICMP ping between R2/R5 Loopbacks"""
        with self.cnctRtr("R2") as conn:
            output = conn.send_command("ping 10.1.5.1 source Loopback99",read_timeout=20)

            successRate = re.search(r"Success +rate +is +(\d+) +percent",  output)
            self.assertIsNotNone(successRate, f"Could not determine the ping's success rate.")

            successMatch = int(successRate.group(1))
            self.assertEqual(successMatch, 100, f'Ping did not fully succeed.\n{output}')

#At the end, the main function encapsulates the core logic
def main():
    unittest.main(verbosity=2)
    

#The code concludes with the namespace check.
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.error("Keyboard interrupt detected. Exiting gracefully.")